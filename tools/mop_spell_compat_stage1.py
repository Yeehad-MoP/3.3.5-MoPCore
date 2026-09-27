#!/usr/bin/env python3
"""
MoP 5.4.8 spell compatibility bootstrap patch for Yeehad-MoP/3.3.5-MoPCore.

Purpose
-------
Expand the WotLK/AzerothCore spell subsystem so MoP Spell.dbc-derived data can
be loaded safely without:
  * TOTAL_SPELL_TARGETS assertions
  * TOTAL_SPELL_EFFECTS assertions / null effect dispatch
  * TOTAL_AURAS assertions / null aura dispatch

This is intentionally a *compatibility bootstrap*, not a claim that every
5.4.8 effect/aura/target now has full MoP gameplay semantics.

MoP reference ranges (SkyFire 5.4.8):
  TOTAL_SPELL_TARGETS = 144   (IDs 0..143)
  TOTAL_SPELL_EFFECTS = 214   (IDs 0..213)
  TOTAL_AURAS         = 438   (IDs 0..437)

This branch already contains the custom Mastery aura IDs 317/318, so the new
MoP aura fallback range begins at 319 and preserves those handlers.
"""

from pathlib import Path
import re
import shutil

ROOT = Path.cwd()

SHARED = ROOT / "src/server/shared/SharedDefines.h"
AURA_DEFINES = ROOT / "src/server/game/Spells/Auras/SpellAuraDefines.h"
SPELL_EFFECTS = ROOT / "src/server/game/Spells/SpellEffects.cpp"
AURA_EFFECTS = ROOT / "src/server/game/Spells/Auras/SpellAuraEffects.cpp"
SPELL_INFO = ROOT / "src/server/game/Spells/SpellInfo.cpp"

TARGET_TOTAL = 144
EFFECT_TOTAL = 214
AURA_TOTAL = 438

OLD_EFFECT_TOTAL = 165
OLD_AURA_TOTAL = 319

MARK_EFFECTS = "MOP_COMPAT_EFFECT_HANDLERS_BEGIN"
MARK_AURAS = "MOP_COMPAT_AURA_HANDLERS_BEGIN"
MARK_TARGETS = "MOP_COMPAT_TARGET_METADATA_BEGIN"


def require(path: Path):
    if not path.is_file():
        raise SystemExit(f"Missing expected source file: {path}")


def backup(path: Path):
    dst = path.with_name(path.name + ".mopcompat.bak")
    if not dst.exists():
        shutil.copy2(path, dst)
        print(f"Backup: {dst}")


def replace_one(text: str, pattern: str, repl: str, label: str) -> str:
    out, count = re.subn(pattern, repl, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"Could not uniquely patch {label} (matches={count})")
    return out


def patch_shared(path: Path):
    text = path.read_text(encoding="utf-8")

    if f"TOTAL_SPELL_TARGETS = {TARGET_TOTAL}" not in text:
        text = replace_one(
            text,
            r"(?m)^(\s*)TOTAL_SPELL_TARGETS\s*$",
            rf"\1TOTAL_SPELL_TARGETS = {TARGET_TOTAL}",
            "TOTAL_SPELL_TARGETS",
        )

    if f"TOTAL_SPELL_EFFECTS                             = {EFFECT_TOTAL}" not in text and \
       f"TOTAL_SPELL_EFFECTS = {EFFECT_TOTAL}" not in text:
        text = replace_one(
            text,
            r"(?m)^(\s*)TOTAL_SPELL_EFFECTS\s*=\s*165\s*$",
            rf"\1TOTAL_SPELL_EFFECTS                             = {EFFECT_TOTAL}",
            "TOTAL_SPELL_EFFECTS",
        )

    path.write_text(text, encoding="utf-8", newline="\n")


def patch_aura_defines(path: Path):
    text = path.read_text(encoding="utf-8")
    if f"TOTAL_AURAS                                             = {AURA_TOTAL}" not in text and \
       f"TOTAL_AURAS = {AURA_TOTAL}" not in text:
        text = replace_one(
            text,
            r"(?m)^(\s*)TOTAL_AURAS\s*=\s*319\s*$",
            rf"\1TOTAL_AURAS                                             = {AURA_TOTAL}",
            "TOTAL_AURAS",
        )
    path.write_text(text, encoding="utf-8", newline="\n")


def find_initializer_end(text: str, declaration: str) -> tuple[int, int]:
    start = text.find(declaration)
    if start < 0:
        raise RuntimeError(f"Could not find declaration: {declaration}")

    brace = text.find("{", start)
    if brace < 0:
        raise RuntimeError(f"Could not find initializer opening brace for: {declaration}")

    depth = 0
    i = brace
    in_string = False
    in_char = False
    escape = False
    line_comment = False
    block_comment = False
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""

        if line_comment:
            if c == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if c == "*" and n == "/":
                block_comment = False
                i += 2
            else:
                i += 1
            continue
        if in_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_string = False
            i += 1
            continue
        if in_char:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == "'":
                in_char = False
            i += 1
            continue

        if c == "/" and n == "/":
            line_comment = True
            i += 2
            continue
        if c == "/" and n == "*":
            block_comment = True
            i += 2
            continue
        if c == '"':
            in_string = True
            i += 1
            continue
        if c == "'":
            in_char = True
            i += 1
            continue

        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return brace, i
        i += 1

    raise RuntimeError(f"Could not find initializer closing brace for: {declaration}")


def patch_spell_effect_handlers(path: Path):
    text = path.read_text(encoding="utf-8")
    if MARK_EFFECTS in text:
        print("Spell effect fallback handlers already present.")
        return

    _, end = find_initializer_end(text, "pEffect SpellEffects[TOTAL_SPELL_EFFECTS]")

    lines = [
        "",
        f"    // {MARK_EFFECTS}",
        "    // MoP 5.4.8 effect IDs not yet implemented by the 3.3.5 core.",
        "    // Keep them safe and explicit instead of leaving null function pointers.",
    ]
    for effect_id in range(OLD_EFFECT_TOTAL, EFFECT_TOTAL):
        comma = "," if effect_id != EFFECT_TOTAL - 1 else ""
        lines.append(
            f"    &Spell::EffectUnused{comma:<2}                                 // {effect_id:3d} MoP compatibility fallback"
        )
    lines.append("    // MOP_COMPAT_EFFECT_HANDLERS_END")
    insertion = "\n".join(lines) + "\n"

    before = text[:end]
    after = text[end:]
    stripped = before.rstrip()
    if not stripped.endswith(","):
        before = stripped + ",\n"
    text = before + insertion + after
    path.write_text(text, encoding="utf-8", newline="\n")


def patch_aura_effect_handlers(path: Path):
    text = path.read_text(encoding="utf-8")
    if MARK_AURAS in text:
        print("Aura fallback handlers already present.")
        return

    _, end = find_initializer_end(text, "pAuraEffectHandler AuraEffectHandler[TOTAL_AURAS]")

    lines = [
        "",
        f"    // {MARK_AURAS}",
        "    // MoP 5.4.8 aura IDs not yet implemented by the 3.3.5 core.",
        "    // Preserve the existing custom Mastery aura IDs 317/318 above.",
        "    // New IDs are inert rather than null so unsupported mechanics cannot",
        "    // crash solely by dispatching through a null function pointer.",
    ]
    for aura_id in range(OLD_AURA_TOTAL, AURA_TOTAL):
        comma = "," if aura_id != AURA_TOTAL - 1 else ""
        lines.append(
            f"    &AuraEffect::HandleNoImmediateEffect{comma:<2}                 // {aura_id:3d} MoP compatibility fallback"
        )
    lines.append("    // MOP_COMPAT_AURA_HANDLERS_END")
    insertion = "\n".join(lines) + "\n"

    before = text[:end]
    after = text[end:]
    stripped = before.rstrip()
    if not stripped.endswith(","):
        before = stripped + ",\n"
    text = before + insertion + after
    path.write_text(text, encoding="utf-8", newline="\n")


def patch_target_metadata(path: Path):
    text = path.read_text(encoding="utf-8")
    if MARK_TARGETS in text:
        print("MoP target metadata already present.")
        return

    anchor = (
        "    {TARGET_OBJECT_TYPE_DEST, TARGET_REFERENCE_TYPE_NONE,   "
        "TARGET_SELECT_CATEGORY_NYI,     TARGET_CHECK_DEFAULT,  "
        "TARGET_DIR_NONE},        // 110 TARGET_DEST_UNK_110"
    )
    pos = text.find(anchor)
    if pos < 0:
        raise RuntimeError("Could not find target metadata row 110 in SpellInfo.cpp")
    eol = text.find("\n", pos)
    if eol < 0:
        raise RuntimeError("Malformed SpellInfo.cpp around target row 110")

    none = "    {TARGET_OBJECT_TYPE_NONE, TARGET_REFERENCE_TYPE_NONE,   TARGET_SELECT_CATEGORY_NYI,     TARGET_CHECK_DEFAULT,  TARGET_DIR_NONE},"
    rows = [
        f"    // {MARK_TARGETS}",
        f"{none}        // 111",
        "    {TARGET_OBJECT_TYPE_DEST, TARGET_REFERENCE_TYPE_CASTER, TARGET_SELECT_CATEGORY_DEFAULT, TARGET_CHECK_DEFAULT,  TARGET_DIR_NONE},        // 112",
        f"{none}        // 113",
        f"{none}        // 114",
        f"{none}        // 115",
        f"{none}        // 116",
        f"{none}        // 117",
        "    // Raid buffs (Fortitude, Mark of the Wild, Blessing of Kings, Arcane Brilliance, ...).",
        "    {TARGET_OBJECT_TYPE_UNIT, TARGET_REFERENCE_TYPE_CASTER, TARGET_SELECT_CATEGORY_AREA,    TARGET_CHECK_RAID,     TARGET_DIR_NONE},        // 118",
        "    {TARGET_OBJECT_TYPE_UNIT, TARGET_REFERENCE_TYPE_CASTER, TARGET_SELECT_CATEGORY_AREA,    TARGET_CHECK_RAID,     TARGET_DIR_NONE},        // 119",
    ]
    for target_id in range(120, 144):
        rows.append(f"{none}        // {target_id}")
    rows.append("    // MOP_COMPAT_TARGET_METADATA_END")

    text = text[:eol+1] + "\n".join(rows) + "\n" + text[eol+1:]
    path.write_text(text, encoding="utf-8", newline="\n")


def main():
    for p in (SHARED, AURA_DEFINES, SPELL_EFFECTS, AURA_EFFECTS, SPELL_INFO):
        require(p)
    for p in (SHARED, AURA_DEFINES, SPELL_EFFECTS, AURA_EFFECTS, SPELL_INFO):
        backup(p)

    patch_shared(SHARED)
    patch_aura_defines(AURA_DEFINES)
    patch_spell_effect_handlers(SPELL_EFFECTS)
    patch_aura_effect_handlers(AURA_EFFECTS)
    patch_target_metadata(SPELL_INFO)

    print("MoP spell compatibility bootstrap applied.")
    print(f"TOTAL_SPELL_TARGETS={TARGET_TOTAL}, TOTAL_SPELL_EFFECTS={EFFECT_TOTAL}, TOTAL_AURAS={AURA_TOTAL}")


if __name__ == "__main__":
    main()
