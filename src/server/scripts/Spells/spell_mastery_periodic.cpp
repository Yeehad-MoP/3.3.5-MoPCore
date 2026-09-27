/*
 * MoP periodic/proc Masteries for the 3.3.5 core.
 */

#include "Mastery.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"

namespace
{
    // Mastery: Shadowy Recall - 77486
    // Each periodic Shadow damage tick has a 1.8% chance per Mastery point to
    // deal that tick's post-mitigation damage a second time.
    class spell_mastery_shadowy_recall : public AuraScript
    {
        PrepareAuraScript(spell_mastery_shadowy_recall);

        bool CheckProc(ProcEventInfo& eventInfo)
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            DamageInfo* damageInfo = eventInfo.GetDamageInfo();
            if (!player || !damageInfo || !damageInfo->GetVictim() || !damageInfo->GetSpellInfo())
                return false;

            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::PRIEST_SHADOW))
                return false;

            if (damageInfo->GetDamageType() != DOT || !(damageInfo->GetSchoolMask() & SPELL_SCHOOL_MASK_SHADOW))
                return false;

            if (damageInfo->GetSpellInfo()->SpellFamilyName != SPELLFAMILY_PRIEST || !damageInfo->GetDamage())
                return false;

            return roll_chance_f(Acore::Mastery::GetMastery(player) * 1.80f);
        }

        void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
        {
            PreventDefaultAction();

            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            DamageInfo* damageInfo = eventInfo.GetDamageInfo();
            Unit* target = damageInfo ? damageInfo->GetVictim() : nullptr;
            if (!player || !damageInfo || !target)
                return;

            uint32 duplicateDamage = damageInfo->GetDamage();
            if (!duplicateDamage)
                return;

            // Deal the already-mitigated tick amount a second time. DealDamage
            // itself does not run the spell proc pipeline again, preventing this
            // duplicate from recursively triggering Shadowy Recall.
            Unit::DealDamage(player, target, duplicateDamage, nullptr, DOT,
                damageInfo->GetSchoolMask(), damageInfo->GetSpellInfo(), false);
        }

        void Register() override
        {
            DoCheckProc += AuraCheckProcFn(spell_mastery_shadowy_recall::CheckProc);
            OnEffectProc += AuraEffectProcFn(spell_mastery_shadowy_recall::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
        }
    };
}

void AddSC_mastery_periodic_spell_scripts()
{
    RegisterSpellScript(spell_mastery_shadowy_recall);
}
