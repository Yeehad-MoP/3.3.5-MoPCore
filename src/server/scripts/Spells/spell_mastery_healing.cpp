/*
 * MoP healing Masteries for the 3.3.5 core.
 * Values are based on the converted MoP Spell.dbc used by this project.
 */

#include "Mastery.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"

namespace
{
    enum MasteryHealingSpells : uint32
    {
        SPELL_PALADIN_ILLUMINATED_HEALING_ABSORB = 86273,
        SPELL_PALADIN_BEACON_OF_LIGHT_HEAL       = 53652,
        SPELL_PRIEST_ECHO_OF_LIGHT               = 77489
    };

    // Mastery: Illuminated Healing - 76669
    // 1.25% of the triggering direct heal per Mastery point.
    class spell_mastery_illuminated_healing : public AuraScript
    {
        PrepareAuraScript(spell_mastery_illuminated_healing);

        bool CheckProc(ProcEventInfo& eventInfo)
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            HealInfo* healInfo = eventInfo.GetHealInfo();
            if (!player || !healInfo || !healInfo->GetTarget() || !healInfo->GetSpellInfo())
                return false;

            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::PALADIN_HOLY))
                return false;

            // Illuminated Healing explicitly does not trigger from Beacon heals.
            if (healInfo->GetSpellInfo()->Id == SPELL_PALADIN_BEACON_OF_LIGHT_HEAL)
                return false;

            // The passive's proc flags select healing events; reject empty heals.
            return healInfo->GetHeal() > 0;
        }

        void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
        {
            PreventDefaultAction();

            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            HealInfo* healInfo = eventInfo.GetHealInfo();
            Unit* target = healInfo ? healInfo->GetTarget() : nullptr;
            if (!player || !healInfo || !target)
                return;

            int32 absorb = int32(float(healInfo->GetHeal()) * Acore::Mastery::GetMastery(player) * 1.25f / 100.0f);
            if (absorb <= 0)
                return;

            // MoP Illuminated Healing rolls into the existing shield. Cap the
            // total absorb at one third of the Paladin's maximum health.
            if (AuraEffect* existing = target->GetAuraEffect(SPELL_PALADIN_ILLUMINATED_HEALING_ABSORB, EFFECT_0, player->GetGUID()))
                absorb += existing->GetAmount();

            int32 cap = int32(player->GetMaxHealth() / 3);
            absorb = std::min(absorb, cap);
            player->CastCustomSpell(target, SPELL_PALADIN_ILLUMINATED_HEALING_ABSORB, &absorb, nullptr, nullptr, true);
        }

        void Register() override
        {
            DoCheckProc += AuraCheckProcFn(spell_mastery_illuminated_healing::CheckProc);
            OnEffectProc += AuraEffectProcFn(spell_mastery_illuminated_healing::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
        }
    };

    // Mastery: Echo of Light - 77485
    // 1.30% of the triggering direct heal per Mastery point, delivered as a
    // rolling periodic heal through spell 77489.
    class spell_mastery_echo_of_light : public AuraScript
    {
        PrepareAuraScript(spell_mastery_echo_of_light);

        bool Validate(SpellInfo const* /*spellInfo*/) override
        {
            return ValidateSpellInfo({ SPELL_PRIEST_ECHO_OF_LIGHT });
        }

        bool CheckProc(ProcEventInfo& eventInfo)
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            HealInfo* healInfo = eventInfo.GetHealInfo();
            if (!player || !healInfo || !healInfo->GetTarget() || !healInfo->GetSpellInfo())
                return false;

            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::PRIEST_HOLY))
                return false;

            // Never allow Echo of Light to feed itself.
            if (healInfo->GetSpellInfo()->Id == SPELL_PRIEST_ECHO_OF_LIGHT)
                return false;

            return healInfo->GetHeal() > 0;
        }

        void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
        {
            PreventDefaultAction();

            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            HealInfo* healInfo = eventInfo.GetHealInfo();
            Unit* target = healInfo ? healInfo->GetTarget() : nullptr;
            if (!player || !healInfo || !target)
                return;

            SpellInfo const* echoInfo = sSpellMgr->GetSpellInfo(SPELL_PRIEST_ECHO_OF_LIGHT);
            if (!echoInfo)
                return;

            uint32 totalTicks = echoInfo->GetMaxTicks();
            if (!totalTicks)
                totalTicks = 6;

            float reservoir = float(healInfo->GetHeal()) * Acore::Mastery::GetMastery(player) * 1.30f / 100.0f;

            // Rolling HoT: preserve the unconsumed healing from an existing
            // Echo and redistribute the full reservoir over a refreshed aura.
            if (AuraEffect* existing = target->GetAuraEffect(SPELL_PRIEST_ECHO_OF_LIGHT, EFFECT_0, player->GetGUID()))
            {
                uint32 amplitude = std::max<int32>(existing->GetAmplitude(), 1);
                int32 duration = std::max<int32>(existing->GetBase()->GetDuration(), 0);
                uint32 remainingTicks = uint32((duration + int32(amplitude) - 1) / int32(amplitude));
                reservoir += float(existing->GetAmount()) * float(remainingTicks);
            }

            int32 tickAmount = int32(reservoir / float(totalTicks));
            if (tickAmount > 0)
                player->CastCustomSpell(target, SPELL_PRIEST_ECHO_OF_LIGHT, &tickAmount, nullptr, nullptr, true);
        }

        void Register() override
        {
            DoCheckProc += AuraCheckProcFn(spell_mastery_echo_of_light::CheckProc);
            OnEffectProc += AuraEffectProcFn(spell_mastery_echo_of_light::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
        }
    };
}

void AddSC_mastery_healing_spell_scripts()
{
    RegisterSpellScript(spell_mastery_illuminated_healing);
    RegisterSpellScript(spell_mastery_echo_of_light);
}
