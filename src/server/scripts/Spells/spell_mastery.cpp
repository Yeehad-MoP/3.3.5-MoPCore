/*
 * Initial MoP Mastery spell effects for the 3.3.5 core.
 * Based on ProjectSkyfire/SkyFire_548 spell_mastery.cpp and adapted to the
 * server-side Mastery implementation in Entities/Player/Mastery.h.
 */

#include "Mastery.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellScript.h"

namespace
{
    enum MasteryTriggeredSpells : uint32
    {
        SPELL_MASTERY_LIGHTNING_BOLT_OVERLOAD = 45284,
        SPELL_MASTERY_CHAIN_LIGHTNING_OVERLOAD = 45297,
        SPELL_MASTERY_LAVA_BURST_OVERLOAD = 77451,
        SPELL_MASTERY_ELEMENTAL_BLAST_OVERLOAD = 120588,
        SPELL_MASTERY_HAND_OF_LIGHT = 96172,
        SPELL_MASTERY_IGNITE = 12654,
        SPELL_MASTERY_BLOOD_SHIELD = 77535,
        SPELL_DK_BLOOD_PRESENCE = 48263
    };

    class spell_mastery_unshackled_fury : public AuraScript
    {
        PrepareAuraScript(spell_mastery_unshackled_fury);

        void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::WARRIOR_FURY))
                    amount = int32(Acore::Mastery::GetMastery(player));
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_unshackled_fury::CalculateAmount, EFFECT_1, SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);
        }
    };

    class spell_mastery_shield_discipline : public AuraScript
    {
        PrepareAuraScript(spell_mastery_shield_discipline);

        void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::PRIEST_DISCIPLINE))
                    amount = int32(float(amount) * (1.0f + Acore::Mastery::GetMastery(player) * 2.5f / 100.0f));
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_shield_discipline::CalculateAmount, EFFECT_0, SPELL_AURA_SCHOOL_ABSORB);
        }
    };

    class spell_mastery_blood_shield : public SpellScript
    {
        PrepareSpellScript(spell_mastery_blood_shield);

        void HandleAfterHit()
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            Unit* target = GetHitUnit();
            if (!player || !target)
                return;

            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::DEATH_KNIGHT_BLOOD) || !player->HasAura(SPELL_DK_BLOOD_PRESENCE))
                return;

            float multiplier = Acore::Mastery::GetMastery(player) * 6.25f / 100.0f;
            int32 baseHeal = GetHitHeal();
            if (baseHeal <= 0)
                baseHeal = GetHitDamage();

            int32 absorb = int32(float(baseHeal) * multiplier);
            if (absorb <= 0)
                return;

            if (AuraEffect* existing = target->GetAuraEffect(SPELL_MASTERY_BLOOD_SHIELD, EFFECT_0, player->GetGUID()))
                absorb += existing->GetAmount();

            absorb = std::min<int32>(absorb, int32(target->GetMaxHealth()));
            player->CastCustomSpell(target, SPELL_MASTERY_BLOOD_SHIELD, &absorb, nullptr, nullptr, true);
        }

        void Register() override
        {
            AfterHit += SpellHitFn(spell_mastery_blood_shield::HandleAfterHit);
        }
    };

    class spell_mastery_ignite : public SpellScript
    {
        PrepareSpellScript(spell_mastery_ignite);

        void HandleAfterHit()
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            Unit* target = GetHitUnit();
            if (!player || !target || GetSpellInfo()->Id == SPELL_MASTERY_IGNITE)
                return;

            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::MAGE_FIRE))
                return;

            int32 damage = GetHitDamage();
            if (damage <= 0)
                return;

            int32 tickAmount = int32(float(damage) * (Acore::Mastery::GetMastery(player) * 1.5f / 100.0f) / 2.0f);
            if (tickAmount > 0)
                player->CastCustomSpell(target, SPELL_MASTERY_IGNITE, &tickAmount, nullptr, nullptr, true);
        }

        void Register() override
        {
            AfterHit += SpellHitFn(spell_mastery_ignite::HandleAfterHit);
        }
    };

    class spell_mastery_hand_of_light : public SpellScript
    {
        PrepareSpellScript(spell_mastery_hand_of_light);

        void HandleAfterHit()
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            Unit* target = GetHitUnit();
            if (!player || !target || GetSpellInfo()->Id == SPELL_MASTERY_HAND_OF_LIGHT)
                return;

            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::PALADIN_RETRIBUTION))
                return;

            int32 damage = GetHitDamage();
            if (damage <= 0)
                return;

            int32 bonus = int32(float(damage) * Acore::Mastery::GetMastery(player) * 1.85f / 100.0f);
            if (bonus > 0)
                player->CastCustomSpell(target, SPELL_MASTERY_HAND_OF_LIGHT, &bonus, nullptr, nullptr, true);
        }

        void Register() override
        {
            AfterHit += SpellHitFn(spell_mastery_hand_of_light::HandleAfterHit);
        }
    };

    class spell_mastery_elemental_overload : public SpellScript
    {
        PrepareSpellScript(spell_mastery_elemental_overload);

        void HandleOnHit()
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            Unit* target = GetHitUnit();
            if (!player || !target)
                return;

            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::SHAMAN_ELEMENTAL))
                return;

            if (!roll_chance_f(Acore::Mastery::GetMastery(player) * 2.0f))
                return;

            switch (GetSpellInfo()->Id)
            {
                case 403:
                    player->CastSpell(target, SPELL_MASTERY_LIGHTNING_BOLT_OVERLOAD, true);
                    break;
                case 421:
                    player->CastSpell(target, SPELL_MASTERY_CHAIN_LIGHTNING_OVERLOAD, true);
                    break;
                case 51505:
                    player->CastSpell(target, SPELL_MASTERY_LAVA_BURST_OVERLOAD, true);
                    break;
                case 117014:
                    player->CastSpell(target, SPELL_MASTERY_ELEMENTAL_BLAST_OVERLOAD, true);
                    player->CastSpell(target, 118517, true);
                    player->CastSpell(target, 118515, true);
                    break;
                default:
                    break;
            }
        }

        void Register() override
        {
            OnHit += SpellHitFn(spell_mastery_elemental_overload::HandleOnHit);
        }
    };
}

void AddSC_mastery_spell_scripts()
{
    RegisterSpellScript(spell_mastery_unshackled_fury);
    RegisterSpellScript(spell_mastery_shield_discipline);
    RegisterSpellScript(spell_mastery_blood_shield);
    RegisterSpellScript(spell_mastery_ignite);
    RegisterSpellScript(spell_mastery_hand_of_light);
    RegisterSpellScript(spell_mastery_elemental_overload);
}
