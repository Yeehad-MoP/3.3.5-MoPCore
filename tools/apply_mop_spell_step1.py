#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path.cwd()

def load(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit(f"Missing expected file: {rel}")
    return p, p.read_text(encoding="utf-8")

def save(p, text):
    p.write_text(text, encoding="utf-8")

def once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected one anchor, found {n}")
    return text.replace(old, new, 1)

# ------------------------------------------------------------------
# SharedDefines.h: make every MoP effect ID 165..213 addressable.
# ------------------------------------------------------------------
p, text = load("src/server/shared/SharedDefines.h")
old = "    SPELL_EFFECT_REMOVE_AURA                        = 164,\n    TOTAL_SPELL_EFFECTS                             = 214\n"
known_effects = {
    165:"SPELL_EFFECT_DAMAGE_FROM_MAX_HEALTH_PCT", 166:"SPELL_EFFECT_GIVE_CURRENCY",
    169:"SPELL_EFFECT_DESTROY_ITEM", 172:"SPELL_EFFECT_RESURRECT_WITH_AURA",
    173:"SPELL_EFFECT_UNLOCK_GUILD_VAULT_TAB", 179:"SPELL_EFFECT_CREATE_AREATRIGGER",
    181:"SPELL_EFFECT_REMOVE_TALENT", 184:"SPELL_EFFECT_REPUTATION_2",
    200:"SPELL_EFFECT_HEAL_BATTLEPET_PCT", 201:"SPELL_EFFECT_BATTLE_PET_UNLOCK",
    208:"SPELL_EFFECT_REPUTATION_3", 213:"SPELL_EFFECT_JUMP_DEST_2",
}
lines = ["    SPELL_EFFECT_REMOVE_AURA                        = 164,"]
for i in range(165, 214):
    name = known_effects.get(i, f"SPELL_EFFECT_{i}")
    lines.append(f"    {name:<48}= {i},")
lines[-1] = lines[-1].rstrip(',') + ','
lines.append("    TOTAL_SPELL_EFFECTS                             = 214")
text = once(text, old, "\n".join(lines) + "\n", "SpellEffects enum")
save(p, text)

# ------------------------------------------------------------------
# SpellAuraDefines.h: explicitly define every aura ID 319..437.
# ------------------------------------------------------------------
p, text = load("src/server/game/Spells/Auras/SpellAuraDefines.h")
old = ("    SPELL_AURA_MASTERY                                      = 318,\n"
       "    SPELL_AURA_CAST_WHILE_WALKING                           = 330,\n"
       "    TOTAL_AURAS                                             = 438\n")
known_auras = {
319:"SPELL_AURA_MOD_MELEE_HASTE_3",320:"SPELL_AURA_MOD_RANGED_HASTE_2",322:"SPELL_AURA_INTERFERE_TARGETTING",
326:"SPELL_AURA_PHASE_GROUP",328:"SPELL_AURA_PROC_ON_POWER_AMOUNT",329:"SPELL_AURA_MOD_RUNE_REGEN_SPEED",
330:"SPELL_AURA_CAST_WHILE_WALKING",331:"SPELL_AURA_FORCE_WEATHER",332:"SPELL_AURA_OVERRIDE_ACTIONBAR_SPELLS",
333:"SPELL_AURA_OVERRIDE_ACTIONBAR_SPELLS_2",334:"SPELL_AURA_MOD_BLIND",336:"SPELL_AURA_MOD_FLYING_RESTRICTIONS",
337:"SPELL_AURA_MOD_VENDOR_ITEMS_PRICES",338:"SPELL_AURA_MOD_DURABILITY_LOSS",339:"SPELL_AURA_INCREASE_SKILL_GAIN_CHANCE",
340:"SPELL_AURA_MOD_RESURRECTED_HEALTH_BY_GUILD_MEMBER",341:"SPELL_AURA_MOD_SPELL_CATEGORY_COOLDOWN",
342:"SPELL_AURA_MOD_MELEE_RANGED_HASTE_2",344:"SPELL_AURA_MOD_AUTOATTACK_DAMAGE",345:"SPELL_AURA_BYPASS_ARMOR_FOR_CASTER",
346:"SPELL_AURA_ENABLE_ALT_POWER",347:"SPELL_AURA_MOD_SPELL_COOLDOWN_BY_HASTE",
348:"SPELL_AURA_DEPOSIT_BONUS_MONEY_IN_GUILD_BANK_ON_LOOT",349:"SPELL_AURA_MOD_CURRENCY_GAIN",
350:"SPELL_AURA_MOD_GATHERING_ITEMS_GAINED_PERCENT",352:"SPELL_AURA_ENABLE_WORGER_ALTERED_FORM",
353:"SPELL_AURA_MOD_CAMOUFLAGE",357:"SPELL_AURA_ENABLE_BOSS1_UNIT_FRAME",358:"SPELL_AURA_WORGEN_ALTERED_FORM",
360:"SPELL_AURA_PROC_TRIGGER_SPELL_COPY",361:"SPELL_AURA_PROC_TRIGGER_SPELL_2",363:"SPELL_AURA_MOD_NEXT_SPELL",
365:"SPELL_AURA_MAX_FAR_CLIP_PLANE",366:"SPELL_AURA_OVERRIDE_SPELL_POWER_BY_AP_PCT",
367:"SPELL_AURA_OVERRIDE_AUTOATTACK_WITH_SPELL",369:"SPELL_AURA_ENABLE_POWER_BAR_TIMER",370:"SPELL_AURA_SET_FAIR_FAR_CLIP",
374:"SPELL_AURA_MODIFY_FALL_DAMAGE_PCT",376:"SPELL_AURA_MOD_CURRENCY_GAIN2",377:"SPELL_AURA_CAST_WHILE_WALKING2",
383:"SPELL_AURA_IGNORE_SPELL_COOLDOWN",400:"SPELL_AURA_MOD_SKILL_2",404:"SPELL_AURA_OVERRIDE_AP_BY_SPELL_POWER_PCT",
407:"SPELL_AURA_MOD_FEAR_2",411:"SPELL_AURA_MOD_CHARGES",420:"SPELL_AURA_MOD_PET_XP_PCT",
}
lines = ["    SPELL_AURA_MASTERY                                      = 318,"]
for i in range(319, 438):
    name = known_auras.get(i, f"SPELL_AURA_{i}")
    lines.append(f"    {name:<58}= {i},")
lines.append("    TOTAL_AURAS                                             = 438")
text = once(text, old, "\n".join(lines) + "\n", "Aura enum 319..437")
save(p, text)

# ------------------------------------------------------------------
# SpellInfo.cpp: target/object metadata through Effect 213.
# ------------------------------------------------------------------
p, text = load("src/server/game/Spells/SpellInfo.cpp")
old = ("    {EFFECT_IMPLICIT_TARGET_EXPLICIT, TARGET_OBJECT_TYPE_UNIT}, // 163 SPELL_EFFECT_163\n"
       "    {EFFECT_IMPLICIT_TARGET_EXPLICIT, TARGET_OBJECT_TYPE_UNIT}, // 164 SPELL_EFFECT_REMOVE_AURA\n"
       "} };\n")
reference = {
165:("EXPLICIT","UNIT","SPELL_EFFECT_DAMAGE_FROM_MAX_HEALTH_PCT"),166:("CASTER","UNIT","SPELL_EFFECT_GIVE_CURRENCY"),
167:("EXPLICIT","UNIT","SPELL_EFFECT_167"),168:("EXPLICIT","UNIT","SPELL_EFFECT_168"),169:("NONE","ITEM","SPELL_EFFECT_DESTROY_ITEM"),
170:("EXPLICIT","UNIT","SPELL_EFFECT_170"),171:("NONE","DEST","SPELL_EFFECT_171"),172:("EXPLICIT","UNIT","SPELL_EFFECT_RESURRECT_WITH_AURA"),
173:("NONE","NONE","SPELL_EFFECT_UNLOCK_GUILD_VAULT_TAB"),174:("EXPLICIT","UNIT","SPELL_EFFECT_174"),175:("NONE","NONE","SPELL_EFFECT_175"),
176:("EXPLICIT","UNIT","SPELL_EFFECT_176"),177:("EXPLICIT","UNIT","SPELL_EFFECT_177"),178:("NONE","NONE","SPELL_EFFECT_178"),
179:("NONE","DEST","SPELL_EFFECT_CREATE_AREATRIGGER"),180:("NONE","NONE","SPELL_EFFECT_180"),181:("NONE","NONE","SPELL_EFFECT_REMOVE_TALENT"),
182:("NONE","UNIT","SPELL_EFFECT_182"),184:("EXPLICIT","UNIT","SPELL_EFFECT_REPUTATION_2"),
200:("EXPLICIT","UNIT","SPELL_EFFECT_HEAL_BATTLEPET_PCT"),208:("EXPLICIT","UNIT","SPELL_EFFECT_REPUTATION_3"),
213:("NONE","DEST","SPELL_EFFECT_JUMP_DEST_2"),
}
meta = ["    {EFFECT_IMPLICIT_TARGET_EXPLICIT, TARGET_OBJECT_TYPE_UNIT}, // 163 SPELL_EFFECT_163",
        "    {EFFECT_IMPLICIT_TARGET_EXPLICIT, TARGET_OBJECT_TYPE_UNIT}, // 164 SPELL_EFFECT_REMOVE_AURA"]
for i in range(165,214):
    imp,obj,name = reference.get(i,("NONE","NONE",f"SPELL_EFFECT_{i}"))
    meta.append(f"    {{EFFECT_IMPLICIT_TARGET_{imp}, TARGET_OBJECT_TYPE_{obj}}}, // {i} {name}")
text = once(text, old, "\n".join(meta) + "\n} };\n", "SpellEffectInfo metadata")
save(p, text)

# ------------------------------------------------------------------
# Spell.h + SpellEffects.cpp: generic effect handler + safe reuse.
# ------------------------------------------------------------------
p, text = load("src/server/game/Spells/Spell.h")
anchor = "    void EffectRemoveAura(SpellEffIndex effIndex);\n"
if "void EffectDamageFromMaxHealthPCT(SpellEffIndex effIndex);" not in text:
    text = once(text, anchor, anchor + "    void EffectDamageFromMaxHealthPCT(SpellEffIndex effIndex);\n", "Effect165 declaration")
save(p, text)

p, text = load("src/server/game/Spells/SpellEffects.cpp")
handlers = {
165:("EffectDamageFromMaxHealthPCT","SPELL_EFFECT_DAMAGE_FROM_MAX_HEALTH_PCT"),
171:("EffectSummonObject","SPELL_EFFECT_171 gameobject summon"),
176:("EffectSanctuary","SPELL_EFFECT_176 sanctuary/Vanish"),
184:("EffectReputation","SPELL_EFFECT_REPUTATION_2"),208:("EffectReputation","SPELL_EFFECT_REPUTATION_3"),
213:("EffectJumpDest","SPELL_EFFECT_JUMP_DEST_2"),
}
for i,(handler,comment) in handlers.items():
    comma = "," if i != 213 else ""
    pat = rf"&Spell::EffectUnused{',' if i != 213 else ''}\\s*//\\s*{i}\\s+MoP compatibility fallback"
    repl = f"&Spell::{handler}{comma}".ljust(60) + f"// {i} {comment}"
    text2,n = re.subn(pat,repl,text,count=1)
    if n != 1:
        raise SystemExit(f"Effect handler {i}: expected one fallback, found {n}")
    text = text2
if "void Spell::EffectDamageFromMaxHealthPCT(SpellEffIndex" not in text:
    text += """

// MoP 5.4.8 effect 165: damage equal to effect value % of target max health.
void Spell::EffectDamageFromMaxHealthPCT(SpellEffIndex /*effIndex*/)
{
    if (effectHandleMode != SPELL_EFFECT_HANDLE_HIT_TARGET)
        return;
    if (!unitTarget || damage <= 0)
        return;
    m_damage += unitTarget->CountPctFromMaxHealth(damage);
}
"""
save(p, text)

# ------------------------------------------------------------------
# AuraEffectHandler: only direct semantic equivalents.
# ------------------------------------------------------------------
p, text = load("src/server/game/Spells/Auras/SpellAuraEffects.cpp")
aura_handlers = {
319:("HandleModMeleeSpeedPct","SPELL_AURA_MOD_MELEE_HASTE_3"),
320:("HandleAuraModRangedHaste","SPELL_AURA_MOD_RANGED_HASTE_2"),
342:("HandleModMeleeRangedSpeedPct","SPELL_AURA_MOD_MELEE_RANGED_HASTE_2"),
400:("HandleAuraModSkill","SPELL_AURA_MOD_SKILL_2"),407:("HandleModFear","SPELL_AURA_MOD_FEAR_2"),
}
for i,(handler,name) in aura_handlers.items():
    pat = rf"&AuraEffect::HandleNoImmediateEffect,\\s*//\\s*{i}\\s+MoP compatibility fallback"
    repl = f"&AuraEffect::{handler},".ljust(65) + f"// {i} {name}"
    text2,n = re.subn(pat,repl,text,count=1)
    if n != 1:
        raise SystemExit(f"Aura handler {i}: expected one fallback, found {n}")
    text = text2
pat = r"&AuraEffect::HandleNoImmediateEffect,\\s*//\\s*330\\s+MoP compatibility fallback"
repl = "&AuraEffect::HandleNoImmediateEffect,".ljust(65) + "// 330 SPELL_AURA_CAST_WHILE_WALKING (handled by casting checks)"
text2,n = re.subn(pat,repl,text,count=1)
if n != 1:
    raise SystemExit(f"Aura 330: expected one fallback, found {n}")
save(p, text2)

print("MoP spell Step 1 patch applied. Rebuild worldserver and run docs/mop-spell-step1-coverage.md tests.")
