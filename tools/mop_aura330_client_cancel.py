#!/usr/bin/env python3
from pathlib import Path

SPELL_HANDLER = Path("src/server/game/Handlers/SpellHandler.cpp")


def replace_once(text, old, new, label):
    if new in text:
        print(f"{label}: already applied")
        return text
    if text.count(old) != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {text.count(old)}")
    print(f"{label}: patched")
    return text.replace(old, new, 1)


def main():
    text = SPELL_HANDLER.read_text(encoding="utf-8")

    old = """    recvPacket >> spellId;\n\n    _player->SpellQueue.clear();\n"""
    new = """    recvPacket >> spellId;\n\n    // The 3.3.5 client does not understand MoP SPELL_AURA_CAST_WHILE_WALKING\n    // and can send CMSG_CANCEL_CAST as soon as movement begins. The server is\n    // authoritative for Aura 330, so ignore that movement-generated cancel\n    // only when the active spell is actually affected by the aura.\n    if (_player->isMoving())\n        if (Spell* currentSpell = _player->FindCurrentSpellBySpellId(spellId))\n            if (_player->HasAuraTypeWithAffectMask(SPELL_AURA_CAST_WHILE_WALKING, currentSpell->m_spellInfo))\n                return;\n\n    _player->SpellQueue.clear();\n"""

    text = replace_once(text, old, new, "Aura 330 client cancel suppression")
    SPELL_HANDLER.write_text(text, encoding="utf-8", newline="\n")
    print("Aura 330 client-side movement cancel suppression applied.")


if __name__ == "__main__":
    main()
