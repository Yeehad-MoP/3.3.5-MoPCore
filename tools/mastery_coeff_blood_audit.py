from pathlib import Path


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
        raise SystemExit(f'anchor not found in {class_name}: {old!r}')
    section = section.replace(old, new, 1)
    return source[:start] + section + source[end:]


path = Path('src/server/scripts/Spells/spell_mastery.cpp')
text = path.read_text()
text = replace_in_class(text, 'spell_mastery_hand_of_light', '* 2.10f / 100.0f', '* 1.85f / 100.0f')
text = replace_in_class(text, 'spell_mastery_executioner', '* 2.50f);', '* 3.00f);')
text = replace_in_class(text, 'spell_mastery_enhanced_elements', '* 2.50f);', '* 2.00f);')
text = replace_in_class(text, 'spell_mastery_total_eclipse', '* 1.87f);', '* 1.875f);')

start, end, section = class_section(text, 'spell_mastery_blood_shield')
old = '''            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;\n            Unit* target = GetHitUnit();\n            if (!player || !target)\n                return;\n\n            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::DEATH_KNIGHT_BLOOD) || !player->HasAura(SPELL_DK_BLOOD_PRESENCE))\n                return;\n\n            float multiplier = Acore::Mastery::GetMastery(player) * 6.25f / 100.0f;\n            int32 baseHeal = GetHitHeal();\n            if (baseHeal <= 0)\n                baseHeal = GetHitDamage();\n\n            int32 absorb = int32(float(baseHeal) * multiplier);\n            if (absorb <= 0)\n                return;\n\n            if (AuraEffect* existing = target->GetAuraEffect(SPELL_MASTERY_BLOOD_SHIELD, EFFECT_0, player->GetGUID()))\n                absorb += existing->GetAmount();\n\n            absorb = std::min<int32>(absorb, int32(target->GetMaxHealth()));\n            player->CastCustomSpell(target, SPELL_MASTERY_BLOOD_SHIELD, &absorb, nullptr, nullptr, true);\n'''
new = '''            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;\n            if (!player)\n                return;\n\n            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::DEATH_KNIGHT_BLOOD) || !player->HasAura(SPELL_DK_BLOOD_PRESENCE))\n                return;\n\n            // 45470 is Death Strike's self-heal component. Blood Shield is based\n            // only on that heal and is always applied to the Death Knight.\n            int32 baseHeal = GetHitHeal();\n            if (baseHeal <= 0)\n                return;\n\n            float multiplier = Acore::Mastery::GetMastery(player) * 6.25f / 100.0f;\n            int32 absorb = int32(float(baseHeal) * multiplier);\n            if (absorb <= 0)\n                return;\n\n            if (AuraEffect* existing = player->GetAuraEffect(SPELL_MASTERY_BLOOD_SHIELD, EFFECT_0, player->GetGUID()))\n                absorb += existing->GetAmount();\n\n            absorb = std::min<int32>(absorb, int32(player->GetMaxHealth()));\n            player->CastCustomSpell(player, SPELL_MASTERY_BLOOD_SHIELD, &absorb, nullptr, nullptr, true);\n'''
if new not in section:
    if old not in section:
        raise SystemExit('Blood Shield anchor not found')
    section = section.replace(old, new, 1)
    text = text[:start] + section + text[end:]

path.write_text(text)
print('final coefficient/Blood corrections applied')
