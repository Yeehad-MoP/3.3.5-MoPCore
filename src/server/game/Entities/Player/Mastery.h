/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * Server-side Mastery support for the 3.3.5 client.
 *
 * Mastery deliberately does not use PLAYER_FIELD_COMBAT_RATING_1 + 25 because
 * the WotLK client only has 25 combat-rating update fields (0..24). Treating
 * Mastery as a native update-field rating would overlap the following player
 * field and corrupt the client-visible object layout.
 */

#ifndef ACORE_MASTERY_H
#define ACORE_MASTERY_H

#include "DBCStores.h"
#include "Player.h"
#include <algorithm>

namespace Acore::Mastery
{
    // Cataclysm/MoP combat-rating index. Kept separate from MAX_COMBAT_RATING
    // until the 3.3.5 client update-field layout is extended or replaced.
    constexpr uint8 COMBAT_RATING_INDEX = 25;
    constexpr uint8 CLASS_SCALAR_INDEX = COMBAT_RATING_INDEX + 1; // gtOCT is 1-based per class
    constexpr float BASE_MASTERY = 8.0f;

    /**
     * Returns raw Mastery Rating supplied by currently equipped item_template
     * stats (ITEM_MOD_MASTERY_RATING / stat type 49).
     *
     * This intentionally reads the equipped items on demand instead of using
     * PLAYER_FIELD_COMBAT_RATING_1. It therefore stays synchronized across
     * equip/unequip operations without adding a client update field.
     */
    inline int32 GetMasteryRating(Player const* player)
    {
        if (!player)
            return 0;

        int32 rating = 0;

        for (uint8 slot = EQUIPMENT_SLOT_START; slot < EQUIPMENT_SLOT_END; ++slot)
        {
            Item* item = player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot);
            if (!item || item->IsBroken())
                continue;

            ItemTemplate const* itemTemplate = item->GetTemplate();
            if (!itemTemplate)
                continue;

            uint32 statCount = std::min<uint32>(itemTemplate->StatsCount, MAX_ITEM_PROTO_STATS);
            for (uint32 stat = 0; stat < statCount; ++stat)
            {
                if (itemTemplate->ItemStat[stat].ItemStatType == ITEM_MOD_MASTERY_RATING)
                    rating += itemTemplate->ItemStat[stat].ItemStatValue;
            }
        }

        return std::max<int32>(rating, 0);
    }

    /**
     * Converts raw Mastery Rating to Mastery points using gtCombatRatings block
     * 25 and the existing gtOCTClassCombatRatingScalar class scalar.
     *
     * Formula mirrors Player::GetRatingMultiplier(), but never indexes the
     * WotLK PLAYER_FIELD_COMBAT_RATING array.
     */
    inline float GetMasteryRatingBonus(Player const* player)
    {
        if (!player)
            return 0.0f;

        uint8 level = player->GetLevel();
        if (!level)
            return 0.0f;
        if (level > GT_MAX_LEVEL)
            level = GT_MAX_LEVEL;

        GtCombatRatingsEntry const* rating =
            sGtCombatRatingsStore.LookupEntry(COMBAT_RATING_INDEX * GT_MAX_LEVEL + level - 1);

        GtOCTClassCombatRatingScalarEntry const* classRating =
            sGtOCTClassCombatRatingScalarStore.LookupEntry(
                (player->getClass() - 1) * GT_MAX_RATING + CLASS_SCALAR_INDEX);

        if (!rating || !classRating || rating->ratio <= 0.0f || classRating->ratio <= 0.0f)
            return 0.0f;

        return float(GetMasteryRating(player)) * classRating->ratio / rating->ratio;
    }

    /**
     * Returns flat Mastery points granted by SPELL_AURA_MASTERY (318).
     * Multiple active effects stack through the core's normal aura-modifier
     * aggregation rules.
     */
    inline float GetMasteryAuraBonus(Player const* player)
    {
        if (!player)
            return 0.0f;

        return float(player->GetTotalAuraModifier(SPELL_AURA_MASTERY));
    }

    /**
     * Current total Mastery points.
     *
     * MoP model:
     *   8 base Mastery + Mastery from rating + SPELL_AURA_MASTERY modifiers.
     */
    inline float GetMastery(Player const* player)
    {
        return BASE_MASTERY + GetMasteryRatingBonus(player) + GetMasteryAuraBonus(player);
    }
}

#endif // ACORE_MASTERY_H
