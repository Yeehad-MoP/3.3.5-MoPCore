/*
 * MoP Mastery spell effects for the 3.3.5 core.
 * Based on ProjectSkyfire/SkyFire_548 behavior and the converted client Spell.dbc.
 */

#include "Mastery.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"

namespace
{
    enum MasteryTriggeredSpells : uint32
    {
        SPELL_MASTERY_OPPORTUNITY_STRIKE = 76858,
        SPELL_MASTERY_WILD_QUIVER = 76663,
        SPELL_MASTERY_MAIN_GAUCHE = 86392,
        SPELL_MASTERY_LIGHTNING_BOLT_OVERLOAD = 45284,
        SPELL_MASTERY_CHAIN_LIGHTNING_OVERLOAD = 45297,
        SPELL_MASTERY_LAVA_BURST_OVERLOAD = 77451,
        SPELL_MASTERY_ELEMENTAL_BLAST_OVERLOAD = 120588,
        SPELL_MASTERY_HAND_OF_LIGHT = 96172,
        SPELL_MASTERY_IGNITE = 12654,
        SPELL_MASTERY_BLOOD_SHIELD = 77535,
        SPELL_DK_BLOOD_PRESENCE = 48263
    };

    class spell_mastery_strikes_of_opportunity : public AuraScript
    {
        PrepareAuraScript(spell_mastery_strikes_of_opportunity);

        bool CheckProc(ProcEventInfo& eventInfo)
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            return player && eventInfo.GetActionTarget() &&
                Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::WARRIOR_ARMS) &&
                roll_chance_f(Acore::Mastery::GetMastery(player) * 2.20f);
        }

        void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
        {
            PreventDefaultAction();
            if (Unit* target = eventInfo.GetActionTarget())
                if (Unit* actor = eventInfo.GetActor())
                    actor->CastSpell(target, SPELL_MASTERY_OPPORTUNITY_STRIKE, true);
        }

        void Register() override
        {
            DoCheckProc += AuraCheckProcFn(spell_mastery_strikes_of_opportunity::CheckProc);
            OnEffectProc += AuraEffectProcFn(spell_mastery_strikes_of_opportunity::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
        }
    };

    class spell_mastery_wild_quiver : public AuraScript
    {
        PrepareAuraScript(spell_mastery_wild_quiver);

        bool CheckProc(ProcEventInfo& eventInfo)
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            return player && eventInfo.GetActionTarget() &&
                Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::HUNTER_MARKSMANSHIP) &&
                roll_chance_f(Acore::Mastery::GetMastery(player) * 2.00f);
        }

        void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
        {
            PreventDefaultAction();
            if (Unit* target = eventInfo.GetActionTarget())
                if (Unit* actor = eventInfo.GetActor())
                    actor->CastSpell(target, SPELL_MASTERY_WILD_QUIVER, true);
        }

        void Register() override
        {
            DoCheckProc += AuraCheckProcFn(spell_mastery_wild_quiver::CheckProc);
            OnEffectProc += AuraEffectProcFn(spell_mastery_wild_quiver::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
        }
    };

    class spell_mastery_main_gauche : public AuraScript
    {
        PrepareAuraScript(spell_mastery_main_gauche);

        bool CheckProc(ProcEventInfo& eventInfo)
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            return player && eventInfo.GetActionTarget() &&
                Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::ROGUE_COMBAT) &&
                roll_chance_f(Acore::Mastery::GetMastery(player) * 2.00f);
        }

        void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
        {
            PreventDefaultAction();
            if (Unit* target = eventInfo.GetActionTarget())
                if (Unit* actor = eventInfo.GetActor())
                    actor->CastSpell(target, SPELL_MASTERY_MAIN_GAUCHE, true);
        }

        void Register() override
        {
            DoCheckProc += AuraCheckProcFn(spell_mastery_main_gauche::CheckProc);
            OnEffectProc += AuraEffectProcFn(spell_mastery_main_gauche::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
        }
    };

    class spell_mastery_critical_block : public AuraScript
    {
        PrepareAuraScript(spell_mastery_critical_block);

        void CalculateAmount(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::WARRIOR_PROTECTION))
                    amount = int32(Acore::Mastery::GetMastery(player) * 1.50f);
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_critical_block::CalculateAmount, EFFECT_1, SPELL_AURA_MOD_BLOCK_CRIT_CHANCE);
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_critical_block::CalculateAmount, EFFECT_2, SPELL_AURA_MOD_BLOCK_PERCENT);
        }
    };

    class spell_mastery_divine_bulwark : public AuraScript
    {
        PrepareAuraScript(spell_mastery_divine_bulwark);

        void CalculateAmount(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::PALADIN_PROTECTION))
                    amount = int32(Acore::Mastery::GetMastery(player));
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_divine_bulwark::CalculateAmount, EFFECT_0, SPELL_AURA_ADD_FLAT_MODIFIER);
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_divine_bulwark::CalculateAmount, EFFECT_1, SPELL_AURA_MOD_BLOCK_PERCENT);
        }
    };

    class spell_mastery_essence_of_the_viper : public AuraScript
    {
        PrepareAuraScript(spell_mastery_essence_of_the_viper);

        void CalculateAmount(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::HUNTER_SURVIVAL))
                    amount = int32(Acore::Mastery::GetMastery(player));
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_essence_of_the_viper::CalculateAmount, EFFECT_0, SPELL_AURA_ADD_PCT_MODIFIER);
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_essence_of_the_viper::CalculateAmount, EFFECT_1, SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);
        }
    };

    class spell_mastery_potent_poisons : public AuraScript
    {
        PrepareAuraScript(spell_mastery_potent_poisons);

        void CalculateAmount(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::ROGUE_ASSASSINATION))
                    amount = int32(Acore::Mastery::GetMastery(player) * 3.50f);
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_potent_poisons::CalculateAmount, EFFECT_1, SPELL_AURA_ADD_PCT_MODIFIER);
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_potent_poisons::CalculateAmount, EFFECT_2, SPELL_AURA_ADD_PCT_MODIFIER);
        }
    };

    class spell_mastery_executioner : public AuraScript
    {
        PrepareAuraScript(spell_mastery_executioner);

        void CalculateAmount(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::ROGUE_SUBTLETY))
                    amount = int32(Acore::Mastery::GetMastery(player) * 2.50f);
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_executioner::CalculateAmount, EFFECT_0, SPELL_AURA_ADD_PCT_MODIFIER);
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_executioner::CalculateAmount, EFFECT_1, SPELL_AURA_ADD_PCT_MODIFIER);
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_executioner::CalculateAmount, EFFECT_2, SPELL_AURA_ADD_PCT_MODIFIER);
        }
    };

    class spell_mastery_shield_discipline_passive : public AuraScript
    {
        PrepareAuraScript(spell_mastery_shield_discipline_passive);

        void CalculateHealing(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::PRIEST_DISCIPLINE))
                    amount = int32(Acore::Mastery::GetMastery(player) * 0.80f);
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_shield_discipline_passive::CalculateHealing, EFFECT_0, SPELL_AURA_MOD_HEALING_DONE_PERCENT);
        }
    };

    class spell_mastery_frozen_heart : public AuraScript
    {
        PrepareAuraScript(spell_mastery_frozen_heart);

        void CalculateAmount(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::DEATH_KNIGHT_FROST))
                    amount = int32(Acore::Mastery::GetMastery(player) * 2.00f);
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_frozen_heart::CalculateAmount, EFFECT_1, SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);
        }
    };

    class spell_mastery_dreadblade : public AuraScript
    {
        PrepareAuraScript(spell_mastery_dreadblade);

        void CalculateAmount(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::DEATH_KNIGHT_UNHOLY))
                    amount = int32(Acore::Mastery::GetMastery(player) * 2.50f);
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_dreadblade::CalculateAmount, EFFECT_1, SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);
        }
    };

    class spell_mastery_enhanced_elements : public AuraScript
    {
        PrepareAuraScript(spell_mastery_enhanced_elements);

        void CalculateAmount(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::SHAMAN_ENHANCEMENT))
                    amount = int32(Acore::Mastery::GetMastery(player) * 2.50f);
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_enhanced_elements::CalculateAmount, EFFECT_1, SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);
        }
    };

    class spell_mastery_potent_afflictions : public AuraScript
    {
        PrepareAuraScript(spell_mastery_potent_afflictions);

        void CalculateAmount(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::WARLOCK_AFFLICTION))
                    amount = int32(Acore::Mastery::GetMastery(player) * 3.10f);
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_potent_afflictions::CalculateAmount, EFFECT_0, SPELL_AURA_ADD_PCT_MODIFIER);
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_potent_afflictions::CalculateAmount, EFFECT_1, SPELL_AURA_ADD_PCT_MODIFIER);
        }
    };

    class spell_mastery_total_eclipse : public AuraScript
    {
        PrepareAuraScript(spell_mastery_total_eclipse);

        void CalculateAmount(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::DRUID_BALANCE))
                    amount = int32(Acore::Mastery::GetMastery(player) * 1.87f);
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_total_eclipse::CalculateAmount, EFFECT_1, SPELL_AURA_ADD_FLAT_MODIFIER);
        }
    };

    class spell_mastery_razor_claws : public AuraScript
    {
        PrepareAuraScript(spell_mastery_razor_claws);

        void CalculateAmount(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::DRUID_FERAL))
                    amount = int32(Acore::Mastery::GetMastery(player) * 3.13f);
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_razor_claws::CalculateAmount, EFFECT_1, SPELL_AURA_ADD_PCT_MODIFIER);
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_razor_claws::CalculateAmount, EFFECT_2, SPELL_AURA_ADD_PCT_MODIFIER);
        }
    };

    class spell_mastery_natures_guardian : public AuraScript
    {
        PrepareAuraScript(spell_mastery_natures_guardian);

        void CalculateAmount(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::DRUID_GUARDIAN))
                    amount = int32(Acore::Mastery::GetMastery(player) * 2.00f);
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_natures_guardian::CalculateAmount, EFFECT_1, SPELL_AURA_MOD_RESISTANCE_PCT);
        }
    };

    class spell_mastery_unshackled_fury : public AuraScript
    {
        PrepareAuraScript(spell_mastery_unshackled_fury);

        void CalculateAmount(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::WARRIOR_FURY))
                    amount = int32(Acore::Mastery::GetMastery(player) * 1.40f);
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_unshackled_fury::CalculateAmount, EFFECT_1, SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);
        }
    };

    class spell_mastery_shield_discipline : public AuraScript
    {
        PrepareAuraScript(spell_mastery_shield_discipline);

        void CalculateAmount(AuraEffect const*, int32& amount, bool&)
        {
            if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
                if (Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::PRIEST_DISCIPLINE))
                    amount = int32(float(amount) * (1.0f + Acore::Mastery::GetMastery(player) * 1.60f / 100.0f));
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

            int32 tickAmount = int32(float(damage) * (Acore::Mastery::GetMastery(player) * 1.50f / 100.0f) / 2.0f);
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

            int32 bonus = int32(float(damage) * Acore::Mastery::GetMastery(player) * 2.10f / 100.0f);
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
    RegisterSpellScript(spell_mastery_strikes_of_opportunity);
    RegisterSpellScript(spell_mastery_wild_quiver);
    RegisterSpellScript(spell_mastery_main_gauche);
    RegisterSpellScript(spell_mastery_critical_block);
    RegisterSpellScript(spell_mastery_divine_bulwark);
    RegisterSpellScript(spell_mastery_essence_of_the_viper);
    RegisterSpellScript(spell_mastery_potent_poisons);
    RegisterSpellScript(spell_mastery_executioner);
    RegisterSpellScript(spell_mastery_shield_discipline_passive);
    RegisterSpellScript(spell_mastery_frozen_heart);
    RegisterSpellScript(spell_mastery_dreadblade);
    RegisterSpellScript(spell_mastery_enhanced_elements);
    RegisterSpellScript(spell_mastery_potent_afflictions);
    RegisterSpellScript(spell_mastery_total_eclipse);
    RegisterSpellScript(spell_mastery_razor_claws);
    RegisterSpellScript(spell_mastery_natures_guardian);
    RegisterSpellScript(spell_mastery_unshackled_fury);
    RegisterSpellScript(spell_mastery_shield_discipline);
    RegisterSpellScript(spell_mastery_blood_shield);
    RegisterSpellScript(spell_mastery_ignite);
    RegisterSpellScript(spell_mastery_hand_of_light);
    RegisterSpellScript(spell_mastery_elemental_overload);
}
