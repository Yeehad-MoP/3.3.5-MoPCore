from pathlib import Path

# One-shot patch script for Mana Adept and Deep Healing.
path = Path('src/server/game/Entities/Unit/Unit.cpp')
text = path.read_text()

include_anchor = '#include "MapMgr.h"\n'
if '#include "Mastery.h"\n' not in text:
    if include_anchor not in text:
        raise SystemExit('Unit.cpp include anchor not found')
    text = text.replace(include_anchor, include_anchor + '#include "Mastery.h"\n', 1)

# Arcane Mage: Mana Adept. In MoP the level-90 rating relationship represented by
# this project is +1% full-mana damage per 300 rating. Since this port's
# gtCombatRatings gives 600 rating per Mastery point at 90, that is 2% damage
# per Mastery point at full mana, scaled linearly by current mana percentage.
damage_anchor = '''    // Done total percent damage auras\n    float DoneTotalMod = 1.0f;\n\n'''
damage_insert = '''    // Done total percent damage auras\n    float DoneTotalMod = 1.0f;\n\n    // MoP Mastery: Mana Adept (Arcane Mage). Damage bonus scales linearly\n    // with current mana and reaches 2% per Mastery point at full mana.\n    if (Player* player = ToPlayer())\n    {\n        if (spellProto->SpellFamilyName == SPELLFAMILY_MAGE &&\n            Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::MAGE_ARCANE))\n        {\n            uint32 maxMana = player->GetMaxPower(POWER_MANA);\n            if (maxMana)\n            {\n                float manaFraction = float(player->GetPower(POWER_MANA)) / float(maxMana);\n                AddPct(DoneTotalMod, Acore::Mastery::GetMastery(player) * 2.0f * manaFraction);\n            }\n        }\n    }\n\n'''
if 'MoP Mastery: Mana Adept' not in text:
    if damage_anchor not in text:
        raise SystemExit('SpellPctDamageModsDone anchor not found')
    text = text.replace(damage_anchor, damage_insert, 1)

# Restoration Shaman: Deep Healing. Patch 4.1+ behavior applies to all healing,
# including periodic/totem healing. The maximum bonus is 3% per Mastery point
# at 0% target health and falls linearly to 0 at 100% health.
heal_anchor = '''    float DoneTotalMod = 1.0f;\n\n    // Healing done percent\n'''
heal_insert = '''    float DoneTotalMod = 1.0f;\n\n    // MoP Mastery: Deep Healing (Restoration Shaman). All healing gains up to\n    // 3% per Mastery point, proportional to the target's missing health.\n    if (Player* player = ToPlayer())\n    {\n        if (spellProto->SpellFamilyName == SPELLFAMILY_SHAMAN &&\n            Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::SHAMAN_RESTORATION))\n        {\n            float missingHealthPct = 100.0f - victim->GetHealthPct();\n            AddPct(DoneTotalMod, Acore::Mastery::GetMastery(player) * 3.0f * missingHealthPct / 100.0f);\n        }\n    }\n\n    // Healing done percent\n'''
if 'MoP Mastery: Deep Healing' not in text:
    if heal_anchor not in text:
        raise SystemExit('SpellPctHealingModsDone anchor not found')
    text = text.replace(heal_anchor, heal_insert, 1)

path.write_text(text)
