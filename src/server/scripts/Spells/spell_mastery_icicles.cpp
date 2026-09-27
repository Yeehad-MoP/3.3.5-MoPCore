/*
 * MoP Frost Mage Mastery: Icicles for the 3.3.5 core.
 * Uses the actual MoP storage/projectile/launcher spells present in the
 * converted client Spell.dbc.
 */

#include "Mastery.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuras.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include <algorithm>
#include <array>
#include <deque>
#include <map>
#include <mutex>
#include <utility>
#include <vector>

namespace
{
    constexpr std::array<uint32, 5> IcicleStorageSpells =
    {
        148012, 148013, 148014, 148015, 148016
    };

    constexpr std::array<uint32, 5> IcicleProjectileSpells =
    {
        148017, 148018, 148019, 148020, 148021
    };

    enum IcicleSpells : uint32
    {
        SPELL_MASTERY_ICICLES = 76613,
        SPELL_ICICLE_DAMAGE   = 148022,
        SPELL_ICICLE_LAUNCHER = 148023
    };

    // The five real storage auras carry the actual stored damage and client
    // state. This small server-side queue only preserves FIFO ordering because
    // Aura::GetApplyTime() has second resolution and cannot reliably order
    // several Icicles generated inside the same second.
    std::map<ObjectGuid, std::deque<uint8>> IcicleQueues;
    std::map<ObjectGuid, ObjectGuid> IcicleLaunchTargets;
    std::recursive_mutex IcicleStateMutex;

    Aura* GetStoredIcicle(Player* player, uint8 slot)
    {
        if (!player || slot >= IcicleStorageSpells.size())
            return nullptr;

        return player->GetAura(IcicleStorageSpells[slot]);
    }

    void ReconcileIcicleQueue(Player* player)
    {
        if (!player)
            return;

        std::lock_guard<std::recursive_mutex> lock(IcicleStateMutex);
        std::deque<uint8>& queue = IcicleQueues[player->GetGUID()];

        // Drop queue entries whose storage aura expired or was otherwise
        // removed before it could launch.
        queue.erase(std::remove_if(queue.begin(), queue.end(), [player](uint8 slot)
        {
            return !GetStoredIcicle(player, slot);
        }), queue.end());

        // Normally every active storage aura is already in the queue. Rebuild
        // missing entries defensively (for example after script reload) using
        // apply time, then slot number as a deterministic tie breaker.
        std::vector<std::pair<time_t, uint8>> missing;
        for (uint8 slot = 0; slot < IcicleStorageSpells.size(); ++slot)
        {
            Aura* aura = GetStoredIcicle(player, slot);
            if (!aura || std::find(queue.begin(), queue.end(), slot) != queue.end())
                continue;

            missing.emplace_back(aura->GetApplyTime(), slot);
        }

        std::sort(missing.begin(), missing.end(), [](auto const& left, auto const& right)
        {
            if (left.first != right.first)
                return left.first < right.first;
            return left.second < right.second;
        });

        for (auto const& entry : missing)
            queue.push_back(entry.second);
    }

    bool HasStoredIcicles(Player* player)
    {
        if (!player)
            return false;

        for (uint32 spellId : IcicleStorageSpells)
            if (player->HasAura(spellId))
                return true;

        return false;
    }

    void ClearIcicles(Player* player)
    {
        if (!player)
            return;

        std::lock_guard<std::recursive_mutex> lock(IcicleStateMutex);
        ObjectGuid guid = player->GetGUID();
        IcicleQueues.erase(guid);
        IcicleLaunchTargets.erase(guid);

        player->RemoveAurasDueToSpell(SPELL_ICICLE_LAUNCHER);
        for (uint32 spellId : IcicleStorageSpells)
            player->RemoveAurasDueToSpell(spellId);
    }

    // Returns the storage slot that was freed, or -1 when nothing could launch.
    int8 LaunchOldestIcicle(Player* player, Unit* target)
    {
        if (!player || !target || !target->IsAlive())
            return -1;

        std::lock_guard<std::recursive_mutex> lock(IcicleStateMutex);
        ReconcileIcicleQueue(player);
        std::deque<uint8>& queue = IcicleQueues[player->GetGUID()];

        while (!queue.empty())
        {
            uint8 slot = queue.front();
            queue.pop_front();

            Aura* aura = GetStoredIcicle(player, slot);
            if (!aura)
                continue;

            AuraEffect* stored = aura->GetEffect(EFFECT_0);
            int32 damage = stored ? stored->GetAmount() : 0;

            // Removing the storage aura before casting the projectile makes
            // the slot immediately reusable by an Icicle generated while a
            // launch sequence is already in progress.
            player->RemoveAurasDueToSpell(IcicleStorageSpells[slot]);

            if (damage > 0)
                player->CastCustomSpell(target, IcicleProjectileSpells[slot], &damage, nullptr, nullptr, true);

            return int8(slot);
        }

        return -1;
    }

    void StoreIcicle(Player* player, Unit* target, int32 damage)
    {
        if (!player || !target || damage <= 0)
            return;

        std::lock_guard<std::recursive_mutex> lock(IcicleStateMutex);
        ReconcileIcicleQueue(player);
        std::deque<uint8>& queue = IcicleQueues[player->GetGUID()];

        int8 freeSlot = -1;
        for (uint8 slot = 0; slot < IcicleStorageSpells.size(); ++slot)
        {
            if (!GetStoredIcicle(player, slot))
            {
                freeSlot = int8(slot);
                break;
            }
        }

        // A sixth Icicle immediately fires the oldest one at the spell target.
        if (freeSlot < 0)
            freeSlot = LaunchOldestIcicle(player, target);

        if (freeSlot < 0)
            return;

        uint8 slot = uint8(freeSlot);
        player->CastCustomSpell(player, IcicleStorageSpells[slot], &damage, nullptr, nullptr, true);
        queue.push_back(slot);

        // If Ice Lance already started the barrage, keep its DBC-driven
        // periodic launcher alive long enough to consume newly generated
        // Icicles as well.
        if (Aura* launcher = player->GetAura(SPELL_ICICLE_LAUNCHER))
            launcher->RefreshDuration();
    }

    class spell_mastery_icicles_store : public SpellScript
    {
        PrepareSpellScript(spell_mastery_icicles_store);

        bool Validate(SpellInfo const* /*spellInfo*/) override
        {
            return ValidateSpellInfo({ SPELL_MASTERY_ICICLES, 148012, 148013, 148014, 148015, 148016,
                148017, 148018, 148019, 148020, 148021, SPELL_ICICLE_DAMAGE, SPELL_ICICLE_LAUNCHER });
        }

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

            // MoP 5.4 Icicles store 2% of Frostbolt/Frostfire Bolt damage per
            // Mastery point. The project's Mastery total already includes the
            // base 8 Mastery, giving the expected 16% baseline storage.
            int32 storedDamage = int32(float(hitDamage) * Acore::Mastery::GetMastery(player) * 2.0f / 100.0f);
            StoreIcicle(player, target, storedDamage);
        }

        void Register() override
        {
            AfterHit += SpellHitFn(spell_mastery_icicles_store::HandleAfterHit);
        }
    };

    // The five 148017-148021 spells carry the matching client projectile
    // visuals. Their DUMMY amount is replaced with the stored Icicle damage;
    // on impact they cast the real Frost damage spell 148022.
    class spell_mastery_icicle_projectile : public SpellScript
    {
        PrepareSpellScript(spell_mastery_icicle_projectile);

        bool Validate(SpellInfo const* /*spellInfo*/) override
        {
            return ValidateSpellInfo({ SPELL_ICICLE_DAMAGE });
        }

        void HandleDummy(SpellEffIndex /*effIndex*/)
        {
            Unit* caster = GetCaster();
            Unit* target = GetHitUnit();
            if (!caster || !target)
                return;

            int32 damage = GetEffectValue();
            if (damage > 0)
                caster->CastCustomSpell(target, SPELL_ICICLE_DAMAGE, &damage, nullptr, nullptr, true);
        }

        void Register() override
        {
            OnEffectHitTarget += SpellEffectFn(spell_mastery_icicle_projectile::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
        }
    };

    class spell_mastery_icicles_launch : public SpellScript
    {
        PrepareSpellScript(spell_mastery_icicles_launch);

        bool Validate(SpellInfo const* /*spellInfo*/) override
        {
            return ValidateSpellInfo({ SPELL_ICICLE_LAUNCHER });
        }

        void HandleAfterHit()
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            Unit* target = GetHitUnit();
            if (!player || !target || !target->IsAlive())
                return;

            if (!Acore::Mastery::HasMasterySpecialization(player, Acore::Mastery::MAGE_FROST) || !HasStoredIcicles(player))
                return;

            {
                std::lock_guard<std::recursive_mutex> lock(IcicleStateMutex);
                IcicleLaunchTargets[player->GetGUID()] = target->GetGUID();
            }

            if (Aura* launcher = player->GetAura(SPELL_ICICLE_LAUNCHER))
                launcher->RefreshDuration();
            else
                player->CastSpell(player, SPELL_ICICLE_LAUNCHER, true);
        }

        void Register() override
        {
            AfterHit += SpellHitFn(spell_mastery_icicles_launch::HandleAfterHit);
        }
    };

    // Spell 148023 is a 750 ms periodic dummy aura in the supplied MoP DBC.
    // Letting that aura drive the sequence preserves the client spell data and
    // avoids firing all five Icicles in the same server tick.
    class spell_mastery_icicle_launcher : public AuraScript
    {
        PrepareAuraScript(spell_mastery_icicle_launcher);

        void HandlePeriodic(AuraEffect const* /*aurEff*/)
        {
            Player* player = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr;
            if (!player)
                return;

            std::lock_guard<std::recursive_mutex> lock(IcicleStateMutex);
            auto itr = IcicleLaunchTargets.find(player->GetGUID());
            if (itr == IcicleLaunchTargets.end())
            {
                Remove();
                return;
            }

            Unit* target = ObjectAccessor::GetUnit(*player, itr->second);
            if (!target || !target->IsAlive())
            {
                // Keep unlaunched Icicles stored if the Ice Lance target is no
                // longer valid; only stop the current barrage.
                IcicleLaunchTargets.erase(itr);
                Remove();
                return;
            }

            LaunchOldestIcicle(player, target);

            if (!HasStoredIcicles(player))
            {
                IcicleLaunchTargets.erase(player->GetGUID());
                Remove();
            }
        }

        void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
        {
            if (Player* player = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr)
            {
                std::lock_guard<std::recursive_mutex> lock(IcicleStateMutex);
                IcicleLaunchTargets.erase(player->GetGUID());
            }
        }

        void Register() override
        {
            OnEffectPeriodic += AuraEffectPeriodicFn(spell_mastery_icicle_launcher::HandlePeriodic, EFFECT_0, SPELL_AURA_PERIODIC_DUMMY);
            AfterEffectRemove += AuraEffectRemoveFn(spell_mastery_icicle_launcher::HandleRemove, EFFECT_0, SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
        }
    };

    // Removing the Frost Mastery passive (for example on a spec change) also
    // removes all transient Icicle state.
    class spell_mastery_icicles_passive : public AuraScript
    {
        PrepareAuraScript(spell_mastery_icicles_passive);

        void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
        {
            if (Player* player = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr)
                ClearIcicles(player);
        }

        void Register() override
        {
            AfterEffectRemove += AuraEffectRemoveFn(spell_mastery_icicles_passive::HandleRemove, EFFECT_0, SPELL_AURA_ADD_PCT_MODIFIER, AURA_EFFECT_HANDLE_REAL);
        }
    };

    class mastery_icicles_player_cleanup : public PlayerScript
    {
    public:
        mastery_icicles_player_cleanup() : PlayerScript("mastery_icicles_player_cleanup",
            { PLAYERHOOK_ON_PLAYER_JUST_DIED, PLAYERHOOK_ON_AFTER_SPEC_SLOT_CHANGED, PLAYERHOOK_ON_BEFORE_LOGOUT }) { }

        void OnPlayerJustDied(Player* player) override
        {
            ClearIcicles(player);
        }

        void OnPlayerAfterSpecSlotChanged(Player* player, uint8 /*newSlot*/) override
        {
            ClearIcicles(player);
        }

        void OnPlayerBeforeLogout(Player* player) override
        {
            ClearIcicles(player);
        }
    };
}

void AddSC_mastery_icicles_spell_scripts()
{
    RegisterSpellScript(spell_mastery_icicles_store);
    RegisterSpellScript(spell_mastery_icicle_projectile);
    RegisterSpellScript(spell_mastery_icicles_launch);
    RegisterSpellScript(spell_mastery_icicle_launcher);
    RegisterSpellScript(spell_mastery_icicles_passive);
    new mastery_icicles_player_cleanup();
}
