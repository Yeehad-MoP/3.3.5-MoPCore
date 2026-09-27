from pathlib import Path

path = Path('src/server/game/Entities/Unit/Unit.cpp')
text = path.read_text()

# Pet melee: Beast Mastery pets gain 2% damage per Mastery point; Demonology
# demons gain 1% per Mastery point. Apply to owned combat units before the
# existing melee bonus pipeline.
melee_anchor = '''uint32 Unit::MeleeDamageBonusDone(Unit* victim, uint32 pdamage, WeaponAttackType attType, SpellInfo const* spellProto, SpellSchoolMask damageSchoolMask /*= SPELL_SCHOOL_MASK_NORMAL*/)\n{\n    if (!victim || pdamage == 0)\n        return 0;\n\n'''
melee_insert = melee_anchor + '''    if (Unit* ownerUnit = GetOwner())\n    {\n        if (Player* owner = ownerUnit->ToPlayer())\n        {\n            if (Acore::Mastery::HasMasterySpecialization(owner, Acore::Mastery::HUNTER_BEAST_MASTERY))\n                AddPct(pdamage, Acore::Mastery::GetMastery(owner) * 2.0f);\n            else if (Acore::Mastery::HasMasterySpecialization(owner, Acore::Mastery::WARLOCK_DEMONOLOGY))\n                AddPct(pdamage, Acore::Mastery::GetMastery(owner));\n        }\n    }\n\n'''
if 'HUNTER_BEAST_MASTERY' not in text[text.find('uint32 Unit::MeleeDamageBonusDone'):text.find('uint32 Unit::MeleeDamageBonusTaken')]:
    if melee_anchor not in text:
        raise SystemExit('MeleeDamageBonusDone anchor not found')
    text = text.replace(melee_anchor, melee_insert, 1)

# Shared spell-damage additions. Insert immediately after the existing Mana
# Adept block so all Mastery multipliers compose with the normal aura system.
damage_marker = '''    // done scripted mod (take it from owner)\n    Unit* owner = GetOwner() ? GetOwner() : this;\n'''
mastery_damage = '''    // MoP pet/caster Masteries that cannot be represented by the converted\n    // Spell.dbc's zeroed EffectBonusMultiplier fields.\n    if (Player* player = ToPlayer())\n    {\n        if (spellProto->SpellFamilyName == SPELLFAMILY_WARLOCK)\n        {\n            if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::WARLOCK_DEMONOLOGY))\n            {\n                // Master Demonologist: 1% per Mastery in caster form, 3% in\n                // Metamorphosis (103958).\n                float coefficient = player->HasAura(103958) ? 3.0f : 1.0f;\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(player) * coefficient);\n            }\n            else if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::WARLOCK_DESTRUCTION))\n            {\n                switch (spellProto->Id)\n                {\n                    // Immolate, Incinerate, Fel Flame, Conflagrate and their\n                    // Fire-and-Brimstone variants: 1% per Mastery point.\n                    case 348:\n                    case 29722:\n                    case 77799:\n                    case 17962:\n                    case 108685:\n                    case 108686:\n                    case 114654:\n                        AddPct(DoneTotalMod, Acore::Mastery::GetMastery(player));\n                        break;\n                    // Burning Ember consumers: 3% per Mastery point.\n                    case 116858: // Chaos Bolt\n                    case 17877:  // Shadowburn\n                    case 125882: // MoP Shadowburn alias\n                        AddPct(DoneTotalMod, Acore::Mastery::GetMastery(player) * 3.0f);\n                        break;\n                    default:\n                        break;\n                }\n            }\n        }\n        else if (spellProto->SpellFamilyName == SPELLFAMILY_HUNTER &&\n                 Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::HUNTER_BEAST_MASTERY))\n        {\n            // A Murder of Crows is explicitly modified by Master of Beasts.\n            if (spellProto->Id == 131900)\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(player) * 2.0f);\n        }\n    }\n    else if (Unit* ownerUnit = GetOwner())\n    {\n        if (Player* ownerPlayer = ownerUnit->ToPlayer())\n        {\n            if (Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::HUNTER_BEAST_MASTERY))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer) * 2.0f);\n            else if (Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::WARLOCK_DEMONOLOGY))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer));\n            else if (Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::MAGE_FROST) &&\n                     (spellProto->Id == 31707 || spellProto->Id == 131581))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer) * 2.0f);\n        }\n    }\n\n'''
# Only patch the first damage function occurrence, before SpellDamageBonusDone.
section_start = text.find('float Unit::SpellPctDamageModsDone')
section_end = text.find('uint32 Unit::SpellDamageBonusDone', section_start)
section = text[section_start:section_end]
if 'MoP pet/caster Masteries' not in section:
    pos = section.find(damage_marker)
    if pos < 0:
        raise SystemExit('SpellPctDamageModsDone scripted-mod anchor not found')
    absolute = section_start + pos
    text = text[:absolute] + mastery_damage + text[absolute:]

# Ember Tap is a Burning Ember consumer and gets the 3%/Mastery effectiveness
# multiplier on its healing side as well.
heal_marker = '''    // Healing done percent\n    if (includeHealingDonePct)\n        DoneTotalMod *= GetTotalAuraMultiplier(SPELL_AURA_MOD_HEALING_DONE_PERCENT);\n'''
heal_insert = '''    // Mastery: Emberstorm - Ember Tap consumes Burning Embers and its healing\n    // effectiveness scales by 3% per Mastery point.\n    if (Player* player = ToPlayer())\n        if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::WARLOCK_DESTRUCTION) && spellProto->Id == 114635)\n            AddPct(DoneTotalMod, Acore::Mastery::GetMastery(player) * 3.0f);\n\n''' + heal_marker
heal_start = text.find('float Unit::SpellPctHealingModsDone')
heal_end = text.find('uint32 Unit::SpellHealingBonusDone', heal_start)
heal_section = text[heal_start:heal_end]
if 'Mastery: Emberstorm - Ember Tap' not in heal_section:
    if heal_marker not in heal_section:
        raise SystemExit('SpellPctHealingModsDone marker not found')
    absolute = heal_start + heal_section.find(heal_marker)
    text = text[:absolute] + heal_insert + text[absolute + len(heal_marker):]

path.write_text(text)
