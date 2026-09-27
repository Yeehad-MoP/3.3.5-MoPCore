from pathlib import Path

# Runtime correctness fixes found by the full Mastery audit.

# ---------------------------------------------------------------------------
# spell_mastery.cpp
# ---------------------------------------------------------------------------
path = Path('src/server/scripts/Spells/spell_mastery.cpp')
text = path.read_text()

# Make no-PCH dependencies explicit.
if '#include "SpellInfo.h"\n' not in text:
    text = text.replace('#include "SpellAuraEffects.h"\n', '#include "SpellAuraEffects.h"\n#include "SpellInfo.h"\n', 1)
if '#include <algorithm>\n' not in text:
    text = text.replace('#include "SpellScriptLoader.h"\n', '#include "SpellScriptLoader.h"\n#include <algorithm>\n', 1)


def class_section(source: str, class_name: str):
    start = source.find(f'    class {class_name} ')
    if start < 0:
        raise SystemExit(f'class not found: {class_name}')
    end = source.find('\n    };', start)
    if end < 0:
        raise SystemExit(f'class end not found: {class_name}')
    end += len('\n    };')
    return start, end, source[start:end]


def replace_in_class(source: str, class_name: str, old: str, new: str):
    start, end, section = class_section(source, class_name)
    if old not in section:
        raise SystemExit(f'anchor not found in {class_name}: {old[:80]!r}')
    section = section.replace(old, new, 1)
    return source[:start] + section + source[end:]

# Extra-attack Masteries must never trigger from their own triggered attack.
for cls, trigger_id in (
    ('spell_mastery_strikes_of_opportunity', 'SPELL_MASTERY_OPPORTUNITY_STRIKE'),
    ('spell_mastery_wild_quiver', 'SPELL_MASTERY_WILD_QUIVER'),
    ('spell_mastery_main_gauche', 'SPELL_MASTERY_MAIN_GAUCHE'),
):
    old = '''        bool CheckProc(ProcEventInfo& eventInfo)\n        {\n            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;\n'''
    new = f'''        bool CheckProc(ProcEventInfo& eventInfo)\n        {{\n            if (SpellInfo const* trigger = eventInfo.GetSpellInfo())\n                if (trigger->Id == {trigger_id})\n                    return false;\n\n            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;\n'''
    text = replace_in_class(text, cls, old, new)

# The converted client DBC has Enrage 12880's MOD_DAMAGE_PERCENT_DONE at
# effect 0. SkyFire used effect 1 in its native MoP spell layout.
text = replace_in_class(
    text,
    'spell_mastery_unshackled_fury',
    'DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_unshackled_fury::CalculateAmount, EFFECT_1, SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);',
    'DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_unshackled_fury::CalculateAmount, EFFECT_0, SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);'
)

# Ignite is a rolling reservoir in MoP. Preserve the remaining damage from the
# old Ignite before refreshing it, matching the SkyFire 5.4 behavior.
old_ignite = '''            int32 tickAmount = int32(float(damage) * (Acore::Mastery::GetMastery(player) * 1.50f / 100.0f) / 2.0f);\n            if (tickAmount > 0)\n                player->CastCustomSpell(target, SPELL_MASTERY_IGNITE, &tickAmount, nullptr, nullptr, true);\n'''
new_ignite = '''            int32 tickAmount = int32(float(damage) * (Acore::Mastery::GetMastery(player) * 1.50f / 100.0f) / 2.0f);\n\n            if (AuraEffect* existing = target->GetAuraEffect(SPELL_MASTERY_IGNITE, EFFECT_0, player->GetGUID()))\n            {\n                uint32 amplitude = std::max<int32>(existing->GetAmplitude(), 1);\n                int32 duration = std::max<int32>(existing->GetBase()->GetDuration(), 0);\n                uint32 remainingTicks = uint32((duration + int32(amplitude) - 1) / int32(amplitude));\n                tickAmount += existing->GetAmount() * int32(remainingTicks);\n                tickAmount = int32(float(tickAmount) * 0.66f);\n            }\n\n            if (tickAmount > 0)\n                player->CastCustomSpell(target, SPELL_MASTERY_IGNITE, &tickAmount, nullptr, nullptr, true);\n'''
text = replace_in_class(text, 'spell_mastery_ignite', old_ignite, new_ignite)
path.write_text(text)

# ---------------------------------------------------------------------------
# Unit.cpp - limit owner Mastery scaling to the units it actually belongs to.
# ---------------------------------------------------------------------------
path = Path('src/server/game/Entities/Unit/Unit.cpp')
text = path.read_text()

old_spell_pet = '''        if (Player* ownerPlayer = ownerUnit->ToPlayer())\n        {\n            if (Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::HUNTER_BEAST_MASTERY))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer) * 2.0f);\n            else if (Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::WARLOCK_DEMONOLOGY))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer));\n            else if (Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::MAGE_FROST) &&\n                     (spellProto->Id == 31707 || spellProto->Id == 131581))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer) * 2.0f);\n        }\n'''
new_spell_pet = '''        if (Player* ownerPlayer = ownerUnit->ToPlayer())\n        {\n            // Master of Beasts modifies the hunter's real tamed pet, represented\n            // by Tamed Pet Passive 01 (DND), not every temporary owned summon.\n            bool const isHunterPet = HasAura(8875);\n\n            // Master Demonologist's servant bonus belongs to demon creatures,\n            // not arbitrary guardians or temporary objects owned by the Warlock.\n            Creature* creature = ToCreature();\n            bool const isWarlockDemon = creature && creature->GetCreatureTemplate() &&\n                creature->GetCreatureTemplate()->type == CREATURE_TYPE_DEMON;\n\n            if (isHunterPet && Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::HUNTER_BEAST_MASTERY))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer) * 2.0f);\n            else if (isWarlockDemon && Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::WARLOCK_DEMONOLOGY))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer));\n            else if (Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::MAGE_FROST) &&\n                     (spellProto->Id == 31707 || spellProto->Id == 131581))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer) * 2.0f);\n        }\n'''
if old_spell_pet not in text:
    raise SystemExit('Unit.cpp spell pet Mastery block not found')
text = text.replace(old_spell_pet, new_spell_pet, 1)

old_melee_pet = '''    if (Unit* ownerUnit = GetOwner())\n    {\n        if (Player* owner = ownerUnit->ToPlayer())\n        {\n            if (Acore::Mastery::HasMasterySpecialization(owner, Acore::Mastery::HUNTER_BEAST_MASTERY))\n                AddPct(pdamage, Acore::Mastery::GetMastery(owner) * 2.0f);\n            else if (Acore::Mastery::HasMasterySpecialization(owner, Acore::Mastery::WARLOCK_DEMONOLOGY))\n                AddPct(pdamage, Acore::Mastery::GetMastery(owner));\n        }\n    }\n'''
new_melee_pet = '''    if (Unit* ownerUnit = GetOwner())\n    {\n        if (Player* owner = ownerUnit->ToPlayer())\n        {\n            bool const isHunterPet = HasAura(8875);\n            Creature* creature = ToCreature();\n            bool const isWarlockDemon = creature && creature->GetCreatureTemplate() &&\n                creature->GetCreatureTemplate()->type == CREATURE_TYPE_DEMON;\n\n            if (isHunterPet && Acore::Mastery::HasMasterySpecialization(owner, Acore::Mastery::HUNTER_BEAST_MASTERY))\n                AddPct(pdamage, Acore::Mastery::GetMastery(owner) * 2.0f);\n            else if (isWarlockDemon && Acore::Mastery::HasMasterySpecialization(owner, Acore::Mastery::WARLOCK_DEMONOLOGY))\n                AddPct(pdamage, Acore::Mastery::GetMastery(owner));\n        }\n    }\n'''
if old_melee_pet not in text:
    raise SystemExit('Unit.cpp melee pet Mastery block not found')
text = text.replace(old_melee_pet, new_melee_pet, 1)
path.write_text(text)

# ---------------------------------------------------------------------------
# World SQL - Wild Mushroom: Bloom (heal spell 102792) is a direct Harmony heal.
# ---------------------------------------------------------------------------
path = Path('data/sql/updates/db_world/2026_09_27_00.sql')
text = path.read_text()
old_sql = "(50464,  'spell_mastery_harmony_trigger');"
new_sql = "(50464,  'spell_mastery_harmony_trigger'),\n(102792, 'spell_mastery_harmony_trigger');"
if old_sql not in text:
    raise SystemExit('Harmony SQL anchor not found')
text = text.replace(old_sql, new_sql, 1)
path.write_text(text)
