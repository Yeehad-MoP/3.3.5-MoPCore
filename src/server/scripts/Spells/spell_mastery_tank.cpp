/*
 * MoP tank Mastery mechanics that live on secondary class auras rather than
 * directly on the Mastery passive spell.
 */

#include "Mastery.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"

namespace
{
    // Bastion of Glory - 114637.
    // Its normal per-stack value is preserved by the converted DBC; Divine
    // Bulwark adds 1 percentage point per Mastery point to that value.
    class spell_mastery_divine_bulwark_bastion : public AuraScript
    {
        PrepareAuraScript(spell_mastery_divine_bulwark_bastion);

        void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            if (!player || !Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::PALADIN_PROTECTION))
                return;

            amount += int32(Acore::Mastery::GetMastery(player));
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_divine_bulwark_bastion::CalculateAmount, EFFECT_0, SPELL_AURA_DUMMY);
        }
    };

    // Shield of the Righteous mitigation aura - 132403.
    // The aura amount is negative damage-taken percentage, therefore greater
    // Mastery makes it more negative (more mitigation).
    class spell_mastery_divine_bulwark_sotr : public AuraScript
    {
        PrepareAuraScript(spell_mastery_divine_bulwark_sotr);

        void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            if (!player || !Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::PALADIN_PROTECTION))
                return;

            amount -= int32(Acore::Mastery::GetMastery(player));
        }

        void Register() override
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mastery_divine_bulwark_sotr::CalculateAmount, EFFECT_0, SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN);
        }
    };
}

void AddSC_mastery_tank_spell_scripts()
{
    RegisterSpellScript(spell_mastery_divine_bulwark_bastion);
    RegisterSpellScript(spell_mastery_divine_bulwark_sotr);
}
