/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * Extends the WotLK aura handler table with the first MoP-era aura slots needed
 * by the Mastery port without rewriting the existing 0..316 table.
 */

#include "SpellAuraEffects.h"

extern pAuraEffectHandler AuraEffectHandler[TOTAL_AURAS];

namespace
{
    struct MasteryAuraHandlerRegistration
    {
        MasteryAuraHandlerRegistration()
        {
            // 317 SPELL_AURA_MOD_SPELL_POWER_PCT is not implemented yet.
            AuraEffectHandler[317] = &AuraEffect::HandleNoImmediateEffect;

            // 318 SPELL_AURA_MASTERY has no immediate side effect. Mastery is
            // evaluated on demand through Unit::GetTotalAuraModifier().
            AuraEffectHandler[SPELL_AURA_MASTERY] = &AuraEffect::HandleNoImmediateEffect;
        }
    } masteryAuraHandlerRegistration;
}
