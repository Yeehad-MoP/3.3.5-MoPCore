/*
 * MoP Frost Mage Mastery: Icicles for the 3.3.5 core.
 * Uses the actual MoP storage/damage spells present in the converted Spell.dbc.
 */

#include "Mastery.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuras.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include <array>

namespace
{
    constexpr std::array<uint32, 5> IcicleStorageSpells =
    {
        148012, 148013, 148014, 148015, 148016
    };

    enum IcicleSpells : uint32
    {
        SPELL_ICICLE_DAMAGE = 148017
    };

    void LaunchIcicle(Player* player, Unit* target, uint32 storageSpell)
    {
        if (!player || !target)
            return;

        AuraEffect* stored = player->GetAuraEffect(storageSpell, EFFECT_0, player->GetGUID());
        if (!stored)
            stored = player->GetAuraEffect(storageSpell, EFFECT_0);
        if (!stored)
            return;

        int32 damage = stored->GetAmount();
        player->RemoveAurasDueToSpell(storageSpell);

        if (damage > 0)
            player->CastCustomSpell(target, SPELL_ICICLE_DAMAGE, &damage, nullptr, nullptr, true);
    }

    void StoreIcicle(Player* player, Unit* target, int32 damage)
    {
        if (!player || !target || damage <= 0)
            return;

        // Prefer an empty storage aura.
        for (uint32 storageSpell : IcicleStorageSpells)
        {
            if (!player->HasAura(storageSpell))
            {
                player->CastCustomSpell(player, storageSpell, &damage, nullptr, nullptr, true);
                return;
            }
        }

        // Five Icicles are already stored. Retail launches the oldest Icicle
        // when another is generated, then stores the new one. Use Aura apply
        // time to preserve that FIFO behavior.
        uint32 oldestSpell = IcicleStorageSpells.front();
        time_t oldestApplyTime = std::numeric_limits<time_t>::max();

        for (uint32 storageSpell : IcicleStorageSpells)
        {
            if (Aura* aura = player->GetAura(storageSpell))
            {
                if (aura->GetApplyTime() < oldestApplyTime)
                {
                    oldestApplyTime = aura->GetApplyTime();
                    oldestSpell = storageSpell;
                }
            }
        }

        LaunchIcicle(player, target, oldestSpell);
        player->CastCustomSpell(player, oldestSpell, &damage, nullptr, nullptr, true);
    }

    // Frostbolt / Frostfire Bolt generate Icicles worth 2% of post-hit damage
    // per Mastery point. Eight base Mastery therefore stores 16%, matching 5.4.
    class spell_mastery_icicles_store : public SpellScript
    {
        PrepareSpellScript(spell_mastery_icicles_store);

        void HandleAfterHit()
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            Unit* target = GetHitUnit();
            if (!player || !target)
                return;

            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::MAGE_FROST))
                return;

            int32 hitDamage = GetHitDamage();
            if (hitDamage <= 0)
                return;

            int32 storedDamage = int32(float(hitDamage) * Acore::Mastery::GetMastery(player) * 2.0f / 100.0f);
            StoreIcicle(player, target, storedDamage);
        }

        void Register() override
        {
            AfterHit += SpellHitFn(spell_mastery_icicles_store::HandleAfterHit);
        }
    };

    // Ice Lance releases every stored Icicle at its current target.
    class spell_mastery_icicles_launch : public SpellScript
    {
        PrepareSpellScript(spell_mastery_icicles_launch);

        void HandleAfterHit()
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            Unit* target = GetHitUnit();
            if (!player || !target)
                return;

            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::MAGE_FROST))
                return;

            for (uint32 storageSpell : IcicleStorageSpells)
                LaunchIcicle(player, target, storageSpell);
        }

        void Register() override
        {
            AfterHit += SpellHitFn(spell_mastery_icicles_launch::HandleAfterHit);
        }
    };
}

void AddSC_mastery_icicles_spell_scripts()
{
    RegisterSpellScript(spell_mastery_icicles_store);
    RegisterSpellScript(spell_mastery_icicles_launch);
}
