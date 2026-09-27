from pathlib import Path


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'anchor not found: {label}')
    return text.replace(old, new, 1)


def class_section(source, class_name):
    start = source.find(f'    class {class_name} ')
    if start < 0:
        raise SystemExit(f'class not found: {class_name}')
    end = source.find('\n    };', start)
    if end < 0:
        raise SystemExit(f'class end not found: {class_name}')
    end += len('\n    };')
    return start, end, source[start:end]


def replace_in_class(source, class_name, old, new):
    start, end, section = class_section(source, class_name)
    if new in section:
        return source
    if old not in section:
        raise SystemExit(f'anchor not found in {class_name}: {old[:100]!r}')
    section = section.replace(old, new, 1)
    return source[:start] + section + source[end:]


def function_section(source, signature):
    start = source.find(signature)
    if start < 0:
        raise SystemExit(f'function not found: {signature}')
    brace = source.find('{', start)
    if brace < 0:
        raise SystemExit(f'opening brace not found: {signature}')
    depth = 0
    for i in range(brace, len(source)):
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                return start, i + 1, source[start:i + 1]
    raise SystemExit(f'closing brace not found: {signature}')


def insert_before_function_end(source, signature, code, marker):
    start, end, section = function_section(source, signature)
    if marker in section:
        return source
    section = section[:-1] + code + '\n}'
    return source[:start] + section + source[end:]


# ---------------------------------------------------------------------------
# spell_mastery.cpp: runtime fixes and 5.4.8 coefficient corrections.
# ---------------------------------------------------------------------------
path = Path('src/server/scripts/Spells/spell_mastery.cpp')
text = path.read_text()
if '#include "SpellInfo.h"\n' not in text:
    text = text.replace('#include "SpellAuraEffects.h"\n', '#include "SpellAuraEffects.h"\n#include "SpellInfo.h"\n', 1)
if '#include <algorithm>\n' not in text:
    text = text.replace('#include "SpellScriptLoader.h"\n', '#include "SpellScriptLoader.h"\n#include <algorithm>\n', 1)

for cls, trigger_id in (
    ('spell_mastery_strikes_of_opportunity', 'SPELL_MASTERY_OPPORTUNITY_STRIKE'),
    ('spell_mastery_wild_quiver', 'SPELL_MASTERY_WILD_QUIVER'),
    ('spell_mastery_main_gauche', 'SPELL_MASTERY_MAIN_GAUCHE'),
):
    start, end, section = class_section(text, cls)
    guard = f'if (trigger->Id == {trigger_id})'
    if guard not in section:
        old = '''        bool CheckProc(ProcEventInfo& eventInfo)\n        {\n            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;\n'''
        new = f'''        bool CheckProc(ProcEventInfo& eventInfo)\n        {{\n            if (SpellInfo const* trigger = eventInfo.GetSpellInfo())\n                if (trigger->Id == {trigger_id})\n                    return false;\n\n            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;\n'''
        text = replace_in_class(text, cls, old, new)

text = replace_in_class(
    text, 'spell_mastery_unshackled_fury',
    'DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_unshackled_fury::CalculateAmount, EFFECT_1, SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);',
    'DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_unshackled_fury::CalculateAmount, EFFECT_0, SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);')

old_ignite = '''            int32 tickAmount = int32(float(damage) * (Acore::Mastery::GetMastery(player) * 1.50f / 100.0f) / 2.0f);\n            if (tickAmount > 0)\n                player->CastCustomSpell(target, SPELL_MASTERY_IGNITE, &tickAmount, nullptr, nullptr, true);\n'''
new_ignite = '''            int32 tickAmount = int32(float(damage) * (Acore::Mastery::GetMastery(player) * 1.50f / 100.0f) / 2.0f);\n\n            if (AuraEffect* existing = target->GetAuraEffect(SPELL_MASTERY_IGNITE, EFFECT_0, player->GetGUID()))\n            {\n                uint32 amplitude = std::max<int32>(existing->GetAmplitude(), 1);\n                int32 duration = std::max<int32>(existing->GetBase()->GetDuration(), 0);\n                uint32 remainingTicks = uint32((duration + int32(amplitude) - 1) / int32(amplitude));\n                tickAmount += existing->GetAmount() * int32(remainingTicks);\n                tickAmount = int32(float(tickAmount) * 0.66f);\n            }\n\n            if (tickAmount > 0)\n                player->CastCustomSpell(target, SPELL_MASTERY_IGNITE, &tickAmount, nullptr, nullptr, true);\n'''
text = replace_in_class(text, 'spell_mastery_ignite', old_ignite, new_ignite)

# Verified 5.4.8 per-Mastery-point coefficients.
text = replace_in_class(text, 'spell_mastery_hand_of_light', '* 2.10f / 100.0f', '* 1.85f / 100.0f')
text = replace_in_class(text, 'spell_mastery_executioner', '* 2.50f);', '* 3.00f);')
text = replace_in_class(text, 'spell_mastery_enhanced_elements', '* 2.50f);', '* 2.00f);')
text = replace_in_class(text, 'spell_mastery_total_eclipse', '* 1.87f);', '* 1.875f);')

old_blood = '''            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;\n            Unit* target = GetHitUnit();\n            if (!player || !target)\n                return;\n\n            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::DEATH_KNIGHT_BLOOD) || !player->HasAura(SPELL_DK_BLOOD_PRESENCE))\n                return;\n\n            float multiplier = Acore::Mastery::GetMastery(player) * 6.25f / 100.0f;\n            int32 baseHeal = GetHitHeal();\n            if (baseHeal <= 0)\n                baseHeal = GetHitDamage();\n\n            int32 absorb = int32(float(baseHeal) * multiplier);\n            if (absorb <= 0)\n                return;\n\n            if (AuraEffect* existing = target->GetAuraEffect(SPELL_MASTERY_BLOOD_SHIELD, EFFECT_0, player->GetGUID()))\n                absorb += existing->GetAmount();\n\n            absorb = std::min<int32>(absorb, int32(target->GetMaxHealth()));\n            player->CastCustomSpell(target, SPELL_MASTERY_BLOOD_SHIELD, &absorb, nullptr, nullptr, true);\n'''
new_blood = '''            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;\n            if (!player)\n                return;\n\n            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::DEATH_KNIGHT_BLOOD) || !player->HasAura(SPELL_DK_BLOOD_PRESENCE))\n                return;\n\n            // 45470 is Death Strike's self-heal component. Blood Shield is based\n            // only on that heal and is always applied to the Death Knight.\n            int32 baseHeal = GetHitHeal();\n            if (baseHeal <= 0)\n                return;\n\n            float multiplier = Acore::Mastery::GetMastery(player) * 6.25f / 100.0f;\n            int32 absorb = int32(float(baseHeal) * multiplier);\n            if (absorb <= 0)\n                return;\n\n            if (AuraEffect* existing = player->GetAuraEffect(SPELL_MASTERY_BLOOD_SHIELD, EFFECT_0, player->GetGUID()))\n                absorb += existing->GetAmount();\n\n            absorb = std::min<int32>(absorb, int32(player->GetMaxHealth()));\n            player->CastCustomSpell(player, SPELL_MASTERY_BLOOD_SHIELD, &absorb, nullptr, nullptr, true);\n'''
text = replace_in_class(text, 'spell_mastery_blood_shield', old_blood, new_blood)
path.write_text(text)


# ---------------------------------------------------------------------------
# Mastery.h: derive specialization from the active WotLK talent tree and keep
# the correct MoP Mastery passive synchronized automatically.
# ---------------------------------------------------------------------------
path = Path('src/server/game/Entities/Player/Mastery.h')
text = path.read_text()
start = text.find('    inline uint32 GetMasterySpecializationSpell(Player const* player)')
end = text.find('    inline void RecalculateMasterySpecialization(Player* player)', start)
if start < 0 or end < 0:
    raise SystemExit('Mastery specialization helper block not found')
new_helpers = r'''    constexpr uint32 MASTERY_SPECIALIZATION_SPELLS[] =
    {
        WARRIOR_ARMS, WARRIOR_FURY, WARRIOR_PROTECTION,
        PALADIN_HOLY, PALADIN_PROTECTION, PALADIN_RETRIBUTION,
        HUNTER_BEAST_MASTERY, HUNTER_MARKSMANSHIP, HUNTER_SURVIVAL,
        ROGUE_ASSASSINATION, ROGUE_COMBAT, ROGUE_SUBTLETY,
        PRIEST_DISCIPLINE, PRIEST_HOLY, PRIEST_SHADOW,
        DEATH_KNIGHT_BLOOD, DEATH_KNIGHT_FROST, DEATH_KNIGHT_UNHOLY,
        SHAMAN_ELEMENTAL, SHAMAN_ENHANCEMENT, SHAMAN_RESTORATION,
        MAGE_ARCANE, MAGE_FIRE, MAGE_FROST,
        WARLOCK_AFFLICTION, WARLOCK_DEMONOLOGY, WARLOCK_DESTRUCTION,
        DRUID_BALANCE, DRUID_FERAL, DRUID_GUARDIAN, DRUID_RESTORATION
    };

    inline uint32 GetExpectedMasterySpecializationSpell(Player const* player)
    {
        if (!IsMasteryAvailable(player))
            return 0;

        uint32 talentTree = const_cast<Player*>(player)->GetSpec();
        switch (talentTree)
        {
            case TALENT_TREE_WARRIOR_ARMS: return WARRIOR_ARMS;
            case TALENT_TREE_WARRIOR_FURY: return WARRIOR_FURY;
            case TALENT_TREE_WARRIOR_PROTECTION: return WARRIOR_PROTECTION;
            case TALENT_TREE_PALADIN_HOLY: return PALADIN_HOLY;
            case TALENT_TREE_PALADIN_PROTECTION: return PALADIN_PROTECTION;
            case TALENT_TREE_PALADIN_RETRIBUTION: return PALADIN_RETRIBUTION;
            case TALENT_TREE_HUNTER_BEAST_MASTERY: return HUNTER_BEAST_MASTERY;
            case TALENT_TREE_HUNTER_MARKSMANSHIP: return HUNTER_MARKSMANSHIP;
            case TALENT_TREE_HUNTER_SURVIVAL: return HUNTER_SURVIVAL;
            case TALENT_TREE_ROGUE_ASSASSINATION: return ROGUE_ASSASSINATION;
            case TALENT_TREE_ROGUE_COMBAT: return ROGUE_COMBAT;
            case TALENT_TREE_ROGUE_SUBTLETY: return ROGUE_SUBTLETY;
            case TALENT_TREE_PRIEST_DISCIPLINE: return PRIEST_DISCIPLINE;
            case TALENT_TREE_PRIEST_HOLY: return PRIEST_HOLY;
            case TALENT_TREE_PRIEST_SHADOW: return PRIEST_SHADOW;
            case TALENT_TREE_DEATH_KNIGHT_BLOOD: return DEATH_KNIGHT_BLOOD;
            case TALENT_TREE_DEATH_KNIGHT_FROST: return DEATH_KNIGHT_FROST;
            case TALENT_TREE_DEATH_KNIGHT_UNHOLY: return DEATH_KNIGHT_UNHOLY;
            case TALENT_TREE_SHAMAN_ELEMENTAL: return SHAMAN_ELEMENTAL;
            case TALENT_TREE_SHAMAN_ENHANCEMENT: return SHAMAN_ENHANCEMENT;
            case TALENT_TREE_SHAMAN_RESTORATION: return SHAMAN_RESTORATION;
            case TALENT_TREE_MAGE_ARCANE: return MAGE_ARCANE;
            case TALENT_TREE_MAGE_FIRE: return MAGE_FIRE;
            case TALENT_TREE_MAGE_FROST: return MAGE_FROST;
            case TALENT_TREE_WARLOCK_AFFLICTION: return WARLOCK_AFFLICTION;
            case TALENT_TREE_WARLOCK_DEMONOLOGY: return WARLOCK_DEMONOLOGY;
            case TALENT_TREE_WARLOCK_DESTRUCTION: return WARLOCK_DESTRUCTION;
            case TALENT_TREE_DRUID_BALANCE: return DRUID_BALANCE;
            case TALENT_TREE_DRUID_RESTORATION: return DRUID_RESTORATION;
            case TALENT_TREE_DRUID_FERAL_COMBAT:
                // WotLK has one Feral Combat tree whereas MoP split it into
                // Feral and Guardian. Preserve an explicit aura/spell choice,
                // but never guess between the two from temporary shapeshift form.
                if (player->HasAura(DRUID_GUARDIAN)) return DRUID_GUARDIAN;
                if (player->HasAura(DRUID_FERAL)) return DRUID_FERAL;
                if (player->HasSpell(DRUID_GUARDIAN) && !player->HasSpell(DRUID_FERAL)) return DRUID_GUARDIAN;
                if (player->HasSpell(DRUID_FERAL) && !player->HasSpell(DRUID_GUARDIAN)) return DRUID_FERAL;
                return 0;
            default:
                return 0;
        }
    }

    inline uint32 GetMasterySpecializationSpell(Player const* player)
    {
        return GetExpectedMasterySpecializationSpell(player);
    }

    inline bool HasMasterySpecialization(Player const* player, uint32 masterySpell)
    {
        return GetExpectedMasterySpecializationSpell(player) == masterySpell;
    }

    inline void SynchronizeMasterySpecialization(Player* player)
    {
        if (!player)
            return;

        uint32 expected = GetExpectedMasterySpecializationSpell(player);
        for (uint32 masterySpell : MASTERY_SPECIALIZATION_SPELLS)
            if (masterySpell != expected && player->HasAura(masterySpell))
                player->RemoveAurasDueToSpell(masterySpell);

        if (expected && !player->HasAura(expected))
            player->CastSpell(player, expected, true);
    }

'''
# Idempotent replacement whether old or already partially patched.
if 'inline void SynchronizeMasterySpecialization(Player* player)' not in text:
    text = text[:start] + new_helpers + text[end:]
path.write_text(text)


# ---------------------------------------------------------------------------
# Player.cpp: synchronize passives on level, talent learning/reset, and spec swap.
# ---------------------------------------------------------------------------
path = Path('src/server/game/Entities/Player/Player.cpp')
text = path.read_text()

# Level changes: before the public level-changed hook.
anchor = '    sScriptMgr->OnPlayerLevelChanged(this, oldLevel);'
if 'Acore::Mastery::SynchronizeMasterySpecialization(this);\n\n    sScriptMgr->OnPlayerLevelChanged(this, oldLevel);' not in text:
    if anchor not in text:
        raise SystemExit('GiveLevel end anchor not found')
    text = text.replace(anchor, '    Acore::Mastery::SynchronizeMasterySpecialization(this);\n\n' + anchor, 1)

# Dual-spec switching: synchronize immediately before the post-switch hook.
anchor = '    sScriptMgr->OnPlayerAfterSpecSlotChanged(this, GetActiveSpec());'
if 'Acore::Mastery::SynchronizeMasterySpecialization(this);\n\n    sScriptMgr->OnPlayerAfterSpecSlotChanged(this, GetActiveSpec());' not in text:
    if anchor not in text:
        raise SystemExit('ActivateSpec end anchor not found')
    text = text.replace(anchor, '    Acore::Mastery::SynchronizeMasterySpecialization(this);\n\n' + anchor, 1)

# Successful talent learning can change the dominant tree on custom setups.
start, end, section = function_section(text, 'void Player::LearnTalent(uint32 talentId, uint32 talentRank, bool command')
if 'SynchronizeMasterySpecialization' not in section:
    section = section[:-1] + '    Acore::Mastery::SynchronizeMasterySpecialization(this);\n}'
    text = text[:start] + section + text[end:]

# A talent reset must immediately remove a stale specialization passive. Insert
# before each successful return from resetTalents, not after the final return.
start, end, section = function_section(text, 'bool Player::resetTalents(bool noResetCost)')
if 'SynchronizeMasterySpecialization' not in section:
    pos = section.rfind('    return true;')
    if pos < 0:
        raise SystemExit('resetTalents success return not found')
    section = section[:pos] + '    Acore::Mastery::SynchronizeMasterySpecialization(this);\n\n' + section[pos:]
    text = text[:start] + section + text[end:]
path.write_text(text)


# ---------------------------------------------------------------------------
# PlayerStorage.cpp: login synchronization and Mastery from stat-type enchants/
# gems (SpellItemEnchantment type STAT, stat 49).
# ---------------------------------------------------------------------------
path = Path('src/server/game/Entities/Player/PlayerStorage.cpp')
text = path.read_text()

old = '''                        case ITEM_MOD_BLOCK_VALUE:\n                            HandleBaseModFlatValue(SHIELD_BLOCK_VALUE, float(enchant_amount), apply);\n                            LOG_DEBUG("entities.player.items", "+ {} BLOCK_VALUE", enchant_amount);\n                            break;\n'''
new = old + '''                        case ITEM_MOD_MASTERY_RATING:\n                            ApplyMasteryRatingBonus(enchant_amount, apply);\n                            LOG_DEBUG("entities.player.items", "+ {} MASTERY_RATING", enchant_amount);\n                            break;\n'''
text = replace_once(text, old, new, 'Mastery enchant stat 49')

anchor = '    UpdateAllStats();\n\n    // restore remembered power/health values'
new_anchor = '    UpdateAllStats();\n    Acore::Mastery::SynchronizeMasterySpecialization(this);\n\n    // restore remembered power/health values'
text = replace_once(text, anchor, new_anchor, 'login Mastery synchronization')

# PlayerStorage.cpp needs Mastery helpers explicitly in no-PCH builds.
if '#include "Mastery.h"\n' not in text:
    text = text.replace('#include "MapMgr.h"\n', '#include "MapMgr.h"\n#include "Mastery.h"\n', 1)
path.write_text(text)


# ---------------------------------------------------------------------------
# Unit.cpp: restrict owner-based Mastery to valid pets/demons.
# ---------------------------------------------------------------------------
path = Path('src/server/game/Entities/Unit/Unit.cpp')
text = path.read_text()
old_spell_pet = '''        if (Player* ownerPlayer = ownerUnit->ToPlayer())\n        {\n            if (Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::HUNTER_BEAST_MASTERY))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer) * 2.0f);\n            else if (Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::WARLOCK_DEMONOLOGY))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer));\n            else if (Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::MAGE_FROST) &&\n                     (spellProto->Id == 31707 || spellProto->Id == 131581))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer) * 2.0f);\n        }\n'''
new_spell_pet = '''        if (Player* ownerPlayer = ownerUnit->ToPlayer())\n        {\n            bool const isHunterPet = HasAura(8875);\n            Creature* creature = ToCreature();\n            bool const isWarlockDemon = creature && creature->GetCreatureTemplate() &&\n                creature->GetCreatureTemplate()->type == CREATURE_TYPE_DEMON;\n\n            if (isHunterPet && Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::HUNTER_BEAST_MASTERY))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer) * 2.0f);\n            else if (isWarlockDemon && Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::WARLOCK_DEMONOLOGY))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer));\n            else if (Acore::Mastery::HasMasterySpecialization(ownerPlayer, Acore::Mastery::MAGE_FROST) &&\n                     (spellProto->Id == 31707 || spellProto->Id == 131581))\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(ownerPlayer) * 2.0f);\n        }\n'''
text = replace_once(text, old_spell_pet, new_spell_pet, 'spell pet Mastery gating')

old_melee_pet = '''    if (Unit* ownerUnit = GetOwner())\n    {\n        if (Player* owner = ownerUnit->ToPlayer())\n        {\n            if (Acore::Mastery::HasMasterySpecialization(owner, Acore::Mastery::HUNTER_BEAST_MASTERY))\n                AddPct(pdamage, Acore::Mastery::GetMastery(owner) * 2.0f);\n            else if (Acore::Mastery::HasMasterySpecialization(owner, Acore::Mastery::WARLOCK_DEMONOLOGY))\n                AddPct(pdamage, Acore::Mastery::GetMastery(owner));\n        }\n    }\n'''
new_melee_pet = '''    if (Unit* ownerUnit = GetOwner())\n    {\n        if (Player* owner = ownerUnit->ToPlayer())\n        {\n            bool const isHunterPet = HasAura(8875);\n            Creature* creature = ToCreature();\n            bool const isWarlockDemon = creature && creature->GetCreatureTemplate() &&\n                creature->GetCreatureTemplate()->type == CREATURE_TYPE_DEMON;\n\n            if (isHunterPet && Acore::Mastery::HasMasterySpecialization(owner, Acore::Mastery::HUNTER_BEAST_MASTERY))\n                AddPct(pdamage, Acore::Mastery::GetMastery(owner) * 2.0f);\n            else if (isWarlockDemon && Acore::Mastery::HasMasterySpecialization(owner, Acore::Mastery::WARLOCK_DEMONOLOGY))\n                AddPct(pdamage, Acore::Mastery::GetMastery(owner));\n        }\n    }\n'''
text = replace_once(text, old_melee_pet, new_melee_pet, 'melee pet Mastery gating')
path.write_text(text)


# ---------------------------------------------------------------------------
# SQL: Harmony must trigger from Wild Mushroom: Bloom direct healing.
# ---------------------------------------------------------------------------
path = Path('data/sql/updates/db_world/2026_09_27_00.sql')
text = path.read_text()
if "(102792, 'spell_mastery_harmony_trigger')" not in text:
    old = "(50464,  'spell_mastery_harmony_trigger');"
    new = "(50464,  'spell_mastery_harmony_trigger'),\n(102792, 'spell_mastery_harmony_trigger');"
    if old not in text:
        raise SystemExit('Harmony SQL anchor not found')
    text = text.replace(old, new, 1)
path.write_text(text)

print('full Mastery audit fixes applied')
