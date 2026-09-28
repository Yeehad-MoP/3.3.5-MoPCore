#!/usr/bin/env python3
from pathlib import Path

AURA = Path("src/server/game/Spells/Auras/SpellAuraDefines.h")
SPELL = Path("src/server/game/Spells/Spell.cpp")
UNIT = Path("src/server/game/Entities/Unit/Unit.cpp")


def replace_once(text, old, new, label):
    if new in text:
        print(f"{label}: already applied")
        return text
    if text.count(old) != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {text.count(old)}")
    print(f"{label}: patched")
    return text.replace(old, new, 1)


def main():
    aura = AURA.read_text(encoding="utf-8")
    aura = replace_once(
        aura,
        "    SPELL_AURA_MASTERY                                      = 318,\n    TOTAL_AURAS                                             = 438",
        "    SPELL_AURA_MASTERY                                      = 318,\n    SPELL_AURA_CAST_WHILE_WALKING                           = 330,\n    TOTAL_AURAS                                             = 438",
        "Aura 330 enum",
    )
    AURA.write_text(aura, encoding="utf-8", newline="\n")

    spell = SPELL.read_text(encoding="utf-8")

    old_start = """    if ((m_spellInfo->IsChanneled() || m_casttime) && m_caster->IsPlayer() && m_caster->isMoving() && m_spellInfo->InterruptFlags & SPELL_INTERRUPT_FLAG_MOVEMENT && !IsTriggered())\n"""
    new_start = """    if ((m_spellInfo->IsChanneled() || m_casttime) && m_caster->IsPlayer() && m_caster->isMoving() && m_spellInfo->InterruptFlags & SPELL_INTERRUPT_FLAG_MOVEMENT && !IsTriggered()\n        && !m_caster->HasAuraTypeWithAffectMask(SPELL_AURA_CAST_WHILE_WALKING, m_spellInfo))\n"""
    spell = replace_once(spell, old_start, new_start, "Moving cast start check")

    old_update = """    if ((m_caster->IsPlayer() && m_timer != 0) &&\n            m_caster->isMoving() && (m_spellInfo->InterruptFlags & SPELL_INTERRUPT_FLAG_MOVEMENT) && m_spellState == SPELL_STATE_PREPARING &&\n            (m_spellInfo->Effects[0].Effect != SPELL_EFFECT_STUCK || !m_caster->HasUnitMovementFlag(MOVEMENTFLAG_FALLING_FAR)))\n"""
    new_update = """    if ((m_caster->IsPlayer() && m_timer != 0) &&\n            m_caster->isMoving() && (m_spellInfo->InterruptFlags & SPELL_INTERRUPT_FLAG_MOVEMENT) && m_spellState == SPELL_STATE_PREPARING &&\n            (m_spellInfo->Effects[0].Effect != SPELL_EFFECT_STUCK || !m_caster->HasUnitMovementFlag(MOVEMENTFLAG_FALLING_FAR)) &&\n            !m_caster->HasAuraTypeWithAffectMask(SPELL_AURA_CAST_WHILE_WALKING, m_spellInfo))\n"""
    spell = replace_once(spell, old_update, new_update, "Moving cast update check")

    SPELL.write_text(spell, encoding="utf-8", newline="\n")

    unit = UNIT.read_text(encoding="utf-8")

    old_aura_interrupt = """        if ((aura->GetSpellInfo()->AuraInterruptFlags & flag) && (!except || aura->GetId() != except))\n        {\n"""
    new_aura_interrupt = """        if ((aura->GetSpellInfo()->AuraInterruptFlags & flag) && (!except || aura->GetId() != except) &&\n            !(flag & AURA_INTERRUPT_FLAG_MOVE && HasAuraTypeWithAffectMask(SPELL_AURA_CAST_WHILE_WALKING, aura->GetSpellInfo())))\n        {\n"""
    unit = replace_once(unit, old_aura_interrupt, new_aura_interrupt, "Movement aura interrupt exemption")

    old_channel_interrupt = """        if (spell->getState() == SPELL_STATE_CASTING && (spell->m_spellInfo->ChannelInterruptFlags & flag) && spell->m_spellInfo->Id != except)\n        {\n"""
    new_channel_interrupt = """        if (spell->getState() == SPELL_STATE_CASTING && (spell->m_spellInfo->ChannelInterruptFlags & flag) && spell->m_spellInfo->Id != except &&\n            !(flag & AURA_INTERRUPT_FLAG_MOVE && HasAuraTypeWithAffectMask(SPELL_AURA_CAST_WHILE_WALKING, spell->GetSpellInfo())))\n        {\n"""
    unit = replace_once(unit, old_channel_interrupt, new_channel_interrupt, "Movement channel interrupt exemption")

    UNIT.write_text(unit, encoding="utf-8", newline="\n")

    print("Aura 330 cast-while-moving support applied, including movement-start preservation.")


if __name__ == "__main__":
    main()
