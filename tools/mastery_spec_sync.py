from pathlib import Path


def function_section(source: str, signature: str):
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

# ---------------------------------------------------------------------------
# Mastery.h - map WotLK talent trees to MoP Mastery passives and keep exactly
# one active specialization Mastery aura at level 80+.
# ---------------------------------------------------------------------------
path = Path('src/server/game/Entities/Player/Mastery.h')
text = path.read_text()
anchor = '''    inline bool HasMasterySpecialization(Player const* player, uint32 masterySpell)\n    {\n        return GetMasterySpecializationSpell(player) == masterySpell;\n    }\n\n'''
if anchor not in text:
    raise SystemExit('Mastery.h specialization anchor not found')
insert = anchor + '''    inline uint32 GetExpectedMasterySpecializationSpell(Player* player)\n    {\n        if (!IsMasteryAvailable(player))\n            return 0;\n\n        switch (player->GetSpec())\n        {\n            case TALENT_TREE_WARRIOR_ARMS: return WARRIOR_ARMS;\n            case TALENT_TREE_WARRIOR_FURY: return WARRIOR_FURY;\n            case TALENT_TREE_WARRIOR_PROTECTION: return WARRIOR_PROTECTION;\n            case TALENT_TREE_PALADIN_HOLY: return PALADIN_HOLY;\n            case TALENT_TREE_PALADIN_PROTECTION: return PALADIN_PROTECTION;\n            case TALENT_TREE_PALADIN_RETRIBUTION: return PALADIN_RETRIBUTION;\n            case TALENT_TREE_HUNTER_BEAST_MASTERY: return HUNTER_BEAST_MASTERY;\n            case TALENT_TREE_HUNTER_MARKSMANSHIP: return HUNTER_MARKSMANSHIP;\n            case TALENT_TREE_HUNTER_SURVIVAL: return HUNTER_SURVIVAL;\n            case TALENT_TREE_ROGUE_ASSASSINATION: return ROGUE_ASSASSINATION;\n            case TALENT_TREE_ROGUE_COMBAT: return ROGUE_COMBAT;\n            case TALENT_TREE_ROGUE_SUBTLETY: return ROGUE_SUBTLETY;\n            case TALENT_TREE_PRIEST_DISCIPLINE: return PRIEST_DISCIPLINE;\n            case TALENT_TREE_PRIEST_HOLY: return PRIEST_HOLY;\n            case TALENT_TREE_PRIEST_SHADOW: return PRIEST_SHADOW;\n            case TALENT_TREE_DEATH_KNIGHT_BLOOD: return DEATH_KNIGHT_BLOOD;\n            case TALENT_TREE_DEATH_KNIGHT_FROST: return DEATH_KNIGHT_FROST;\n            case TALENT_TREE_DEATH_KNIGHT_UNHOLY: return DEATH_KNIGHT_UNHOLY;\n            case TALENT_TREE_SHAMAN_ELEMENTAL: return SHAMAN_ELEMENTAL;\n            case TALENT_TREE_SHAMAN_ENHANCEMENT: return SHAMAN_ENHANCEMENT;\n            case TALENT_TREE_SHAMAN_RESTORATION: return SHAMAN_RESTORATION;\n            case TALENT_TREE_MAGE_ARCANE: return MAGE_ARCANE;\n            case TALENT_TREE_MAGE_FIRE: return MAGE_FIRE;\n            case TALENT_TREE_MAGE_FROST: return MAGE_FROST;\n            case TALENT_TREE_WARLOCK_AFFLICTION: return WARLOCK_AFFLICTION;\n            case TALENT_TREE_WARLOCK_DEMONOLOGY: return WARLOCK_DEMONOLOGY;\n            case TALENT_TREE_WARLOCK_DESTRUCTION: return WARLOCK_DESTRUCTION;\n            case TALENT_TREE_DRUID_BALANCE: return DRUID_BALANCE;\n            case TALENT_TREE_DRUID_RESTORATION: return DRUID_RESTORATION;\n            case TALENT_TREE_DRUID_FERAL_COMBAT:\n                // WotLK has one Feral Combat tree, while MoP splits Feral and\n                // Guardian. Preserve an explicitly learned/cast Guardian\n                // passive as the stable selector; otherwise default to Feral.\n                if (player->HasSpell(DRUID_GUARDIAN) || player->HasAura(DRUID_GUARDIAN))\n                    return DRUID_GUARDIAN;\n                return DRUID_FERAL;\n            default:\n                return 0;\n        }\n    }\n\n    inline void SyncMasterySpecialization(Player* player)\n    {\n        if (!player)\n            return;\n\n        uint32 expected = GetExpectedMasterySpecializationSpell(player);\n        static constexpr uint32 masterySpells[] =\n        {\n            WARRIOR_ARMS, WARRIOR_FURY, WARRIOR_PROTECTION,\n            PALADIN_HOLY, PALADIN_PROTECTION, PALADIN_RETRIBUTION,\n            HUNTER_BEAST_MASTERY, HUNTER_MARKSMANSHIP, HUNTER_SURVIVAL,\n            ROGUE_ASSASSINATION, ROGUE_COMBAT, ROGUE_SUBTLETY,\n            PRIEST_DISCIPLINE, PRIEST_HOLY, PRIEST_SHADOW,\n            DEATH_KNIGHT_BLOOD, DEATH_KNIGHT_FROST, DEATH_KNIGHT_UNHOLY,\n            SHAMAN_ELEMENTAL, SHAMAN_ENHANCEMENT, SHAMAN_RESTORATION,\n            MAGE_ARCANE, MAGE_FIRE, MAGE_FROST,\n            WARLOCK_AFFLICTION, WARLOCK_DEMONOLOGY, WARLOCK_DESTRUCTION,\n            DRUID_BALANCE, DRUID_FERAL, DRUID_GUARDIAN, DRUID_RESTORATION\n        };\n\n        for (uint32 spellId : masterySpells)\n            if (spellId != expected && player->HasAura(spellId))\n                player->RemoveAurasDueToSpell(spellId);\n\n        if (expected && !player->HasAura(expected))\n            player->CastSpell(player, expected, true);\n    }\n\n'''
text = text.replace(anchor, insert, 1)
path.write_text(text)

# ---------------------------------------------------------------------------
# StatSystem.cpp - login/level/stat rebuild safety net.
# ---------------------------------------------------------------------------
path = Path('src/server/game/Entities/Unit/StatSystem.cpp')
text = path.read_text()
if '#include "Mastery.h"\n' not in text:
    text = text.replace('#include "Creature.h"\n', '#include "Creature.h"\n#include "Mastery.h"\n', 1)
start, end, section = function_section(text, 'bool Player::UpdateAllStats()')
old = '    UpdateAllResistances();\n\n    return true;'
new = '    UpdateAllResistances();\n\n    Acore::Mastery::SyncMasterySpecialization(this);\n    return true;'
if old not in section:
    raise SystemExit('UpdateAllStats tail anchor not found')
section = section.replace(old, new, 1)
text = text[:start] + section + text[end:]
path.write_text(text)

# ---------------------------------------------------------------------------
# Player.cpp - make talent/spec transitions immediate rather than waiting for
# the next full stat rebuild.
# ---------------------------------------------------------------------------
path = Path('src/server/game/Entities/Player/Player.cpp')
text = path.read_text()

start, end, section = function_section(text, 'void Player::ActivateSpec(uint8 spec)')
old = '    sScriptMgr->OnPlayerAfterSpecSlotChanged(this, GetActiveSpec());'
new = '    Acore::Mastery::SyncMasterySpecialization(this);\n    sScriptMgr->OnPlayerAfterSpecSlotChanged(this, GetActiveSpec());'
if old not in section:
    raise SystemExit('ActivateSpec tail anchor not found')
section = section.replace(old, new, 1)
text = text[:start] + section + text[end:]

start, end, section = function_section(text, 'void Player::LearnTalent(uint32 talentId, uint32 talentRank, bool command')
close = section.rfind('\n}')
if close < 0:
    raise SystemExit('LearnTalent closing brace not found')
section = section[:close] + '\n    Acore::Mastery::SyncMasterySpecialization(this);' + section[close:]
text = text[:start] + section + text[end:]

start, end, section = function_section(text, 'bool Player::resetTalents(bool noResetCost)')
pos = section.rfind('    return true;')
if pos < 0:
    raise SystemExit('resetTalents final return not found')
section = section[:pos] + '    Acore::Mastery::SyncMasterySpecialization(this);\n' + section[pos:]
text = text[:start] + section + text[end:]
path.write_text(text)
