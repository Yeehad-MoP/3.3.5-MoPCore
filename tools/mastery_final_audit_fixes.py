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
    return source[:start] + section.replace(old, new, 1) + source[end:]


def function_section(source, signature):
    start = source.find(signature)
    if start < 0:
        raise SystemExit(f'function not found: {signature}')
    brace = source.find('{', start)
    depth = 0
    for i in range(brace, len(source)):
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                return start, i + 1, source[start:i + 1]
    raise SystemExit(f'function end not found: {signature}')


# ---------------------------------------------------------------------------
# Correct remaining 5.4.8 coefficients and Blood Shield targeting.
# ---------------------------------------------------------------------------
path = Path('src/server/scripts/Spells/spell_mastery.cpp')
text = path.read_text()
text = replace_in_class(text, 'spell_mastery_hand_of_light', '* 2.10f / 100.0f', '* 1.85f / 100.0f')
text = replace_in_class(text, 'spell_mastery_executioner', '* 2.50f);', '* 3.00f);')
text = replace_in_class(text, 'spell_mastery_enhanced_elements', '* 2.50f);', '* 2.00f);')
text = replace_in_class(text, 'spell_mastery_total_eclipse', '* 1.87f);', '* 1.875f);')

start, end, blood = class_section(text, 'spell_mastery_blood_shield')
old = '''            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;\n            Unit* target = GetHitUnit();\n            if (!player || !target)\n                return;\n\n            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::DEATH_KNIGHT_BLOOD) || !player->HasAura(SPELL_DK_BLOOD_PRESENCE))\n                return;\n\n            float multiplier = Acore::Mastery::GetMastery(player) * 6.25f / 100.0f;\n            int32 baseHeal = GetHitHeal();\n            if (baseHeal <= 0)\n                baseHeal = GetHitDamage();\n\n            int32 absorb = int32(float(baseHeal) * multiplier);\n            if (absorb <= 0)\n                return;\n\n            if (AuraEffect* existing = target->GetAuraEffect(SPELL_MASTERY_BLOOD_SHIELD, EFFECT_0, player->GetGUID()))\n                absorb += existing->GetAmount();\n\n            absorb = std::min<int32>(absorb, int32(target->GetMaxHealth()));\n            player->CastCustomSpell(target, SPELL_MASTERY_BLOOD_SHIELD, &absorb, nullptr, nullptr, true);\n'''
new = '''            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;\n            if (!player)\n                return;\n\n            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::DEATH_KNIGHT_BLOOD) || !player->HasAura(SPELL_DK_BLOOD_PRESENCE))\n                return;\n\n            // 45470 is Death Strike's self-heal component. Blood Shield is based\n            // only on that heal and is always applied to the Death Knight.\n            int32 baseHeal = GetHitHeal();\n            if (baseHeal <= 0)\n                return;\n\n            float multiplier = Acore::Mastery::GetMastery(player) * 6.25f / 100.0f;\n            int32 absorb = int32(float(baseHeal) * multiplier);\n            if (absorb <= 0)\n                return;\n\n            if (AuraEffect* existing = player->GetAuraEffect(SPELL_MASTERY_BLOOD_SHIELD, EFFECT_0, player->GetGUID()))\n                absorb += existing->GetAmount();\n\n            absorb = std::min<int32>(absorb, int32(player->GetMaxHealth()));\n            player->CastCustomSpell(player, SPELL_MASTERY_BLOOD_SHIELD, &absorb, nullptr, nullptr, true);\n'''
if new not in blood:
    if old not in blood:
        raise SystemExit('Blood Shield anchor not found')
    blood = blood.replace(old, new, 1)
    text = text[:start] + blood + text[end:]
path.write_text(text)


# ---------------------------------------------------------------------------
# Automatic specialization-passive synchronization.
# ---------------------------------------------------------------------------
path = Path('src/server/game/Entities/Player/Mastery.h')
text = path.read_text()
if 'inline void SynchronizeMasterySpecialization(Player* player)' not in text:
    start = text.find('    inline uint32 GetMasterySpecializationSpell(Player const* player)')
    end = text.find('    inline void RecalculateMasterySpecialization(Player* player)', start)
    if start < 0 or end < 0:
        raise SystemExit('Mastery specialization helper block not found')
    helpers = r'''    constexpr uint32 MASTERY_SPECIALIZATION_SPELLS[] =
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
                // Feral and Guardian. Keep an explicit choice but never infer
                // specialization from a temporary cat/bear shapeshift form.
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
    text = text[:start] + helpers + text[end:]
path.write_text(text)


# ---------------------------------------------------------------------------
# Synchronize on level changes, talent learning/reset, dual-spec switch, login.
# ---------------------------------------------------------------------------
path = Path('src/server/game/Entities/Player/Player.cpp')
text = path.read_text()
anchor = '    sScriptMgr->OnPlayerLevelChanged(this, oldLevel);'
new_anchor = '    Acore::Mastery::SynchronizeMasterySpecialization(this);\n\n' + anchor
text = replace_once(text, anchor, new_anchor, 'level-change sync')

anchor = '    sScriptMgr->OnPlayerAfterSpecSlotChanged(this, GetActiveSpec());'
new_anchor = '    Acore::Mastery::SynchronizeMasterySpecialization(this);\n\n' + anchor
text = replace_once(text, anchor, new_anchor, 'spec-switch sync')

start, end, section = function_section(text, 'void Player::LearnTalent(uint32 talentId, uint32 talentRank, bool command')
if 'SynchronizeMasterySpecialization' not in section:
    section = section[:-1] + '    Acore::Mastery::SynchronizeMasterySpecialization(this);\n}'
    text = text[:start] + section + text[end:]

start, end, section = function_section(text, 'bool Player::resetTalents(bool noResetCost)')
if 'SynchronizeMasterySpecialization' not in section:
    pos = section.rfind('    return true;')
    if pos < 0:
        raise SystemExit('resetTalents successful return not found')
    section = section[:pos] + '    Acore::Mastery::SynchronizeMasterySpecialization(this);\n\n' + section[pos:]
    text = text[:start] + section + text[end:]
path.write_text(text)

path = Path('src/server/game/Entities/Player/PlayerStorage.cpp')
text = path.read_text()
if '#include "Mastery.h"\n' not in text:
    text = text.replace('#include "MapMgr.h"\n', '#include "MapMgr.h"\n#include "Mastery.h"\n', 1)
anchor = '    UpdateAllStats();\n\n    // restore remembered power/health values'
new_anchor = '    UpdateAllStats();\n    Acore::Mastery::SynchronizeMasterySpecialization(this);\n\n    // restore remembered power/health values'
text = replace_once(text, anchor, new_anchor, 'login sync')
path.write_text(text)

print('final Mastery audit corrections applied')
