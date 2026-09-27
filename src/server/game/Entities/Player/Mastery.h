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
    constexpr uint8 MIN_MASTERY_LEVEL = 80;

    enum MasterySpell : uint32
    {
        WARRIOR_ARMS            = 76838,
        WARRIOR_FURY            = 76856,
        WARRIOR_PROTECTION      = 76857,

        PALADIN_HOLY            = 76669,
        PALADIN_PROTECTION      = 76671,
        PALADIN_RETRIBUTION     = 76672,

        HUNTER_BEAST_MASTERY    = 76657,
        HUNTER_MARKSMANSHIP     = 76659,
        HUNTER_SURVIVAL         = 76658,

        ROGUE_ASSASSINATION     = 76803,
        ROGUE_COMBAT            = 76806,
        ROGUE_SUBTLETY          = 76808,

        PRIEST_DISCIPLINE       = 77484,
        PRIEST_HOLY             = 77485,
        PRIEST_SHADOW           = 77486,

        DEATH_KNIGHT_BLOOD      = 77513,
        DEATH_KNIGHT_FROST      = 77514,
        DEATH_KNIGHT_UNHOLY     = 77515,

        SHAMAN_ELEMENTAL        = 77222,
        SHAMAN_ENHANCEMENT      = 77223,
        SHAMAN_RESTORATION      = 77226,

        MAGE_ARCANE             = 76547,
        MAGE_FIRE               = 12846,
        MAGE_FROST              = 76613,

        WARLOCK_AFFLICTION      = 77215,
        WARLOCK_DEMONOLOGY      = 77219,
        WARLOCK_DESTRUCTION     = 77220,

        DRUID_BALANCE           = 77492,
        DRUID_FERAL             = 77493,
        DRUID_GUARDIAN          = 77494,
        DRUID_RESTORATION       = 77495
    };

    inline bool IsMasteryAvailable(Player const* player)
    {
        return player && player->GetLevel() >= MIN_MASTERY_LEVEL;
    }

    inline uint32 GetMasterySpecializationSpell(Player const* player)
    {
        if (!IsMasteryAvailable(player))
            return 0;

        switch (player->getClass())
        {
            case CLASS_WARRIOR:
                if (player->HasAura(WARRIOR_ARMS)) return WARRIOR_ARMS;
                if (player->HasAura(WARRIOR_FURY)) return WARRIOR_FURY;
                if (player->HasAura(WARRIOR_PROTECTION)) return WARRIOR_PROTECTION;
                break;
            case CLASS_PALADIN:
                if (player->HasAura(PALADIN_HOLY)) return PALADIN_HOLY;
                if (player->HasAura(PALADIN_PROTECTION)) return PALADIN_PROTECTION;
                if (player->HasAura(PALADIN_RETRIBUTION)) return PALADIN_RETRIBUTION;
                break;
            case CLASS_HUNTER:
                if (player->HasAura(HUNTER_BEAST_MASTERY)) return HUNTER_BEAST_MASTERY;
                if (player->HasAura(HUNTER_MARKSMANSHIP)) return HUNTER_MARKSMANSHIP;
                if (player->HasAura(HUNTER_SURVIVAL)) return HUNTER_SURVIVAL;
                break;
            case CLASS_ROGUE:
                if (player->HasAura(ROGUE_ASSASSINATION)) return ROGUE_ASSASSINATION;
                if (player->HasAura(ROGUE_COMBAT)) return ROGUE_COMBAT;
                if (player->HasAura(ROGUE_SUBTLETY)) return ROGUE_SUBTLETY;
                break;
            case CLASS_PRIEST:
                if (player->HasAura(PRIEST_DISCIPLINE)) return PRIEST_DISCIPLINE;
                if (player->HasAura(PRIEST_HOLY)) return PRIEST_HOLY;
                if (player->HasAura(PRIEST_SHADOW)) return PRIEST_SHADOW;
                break;
            case CLASS_DEATH_KNIGHT:
                if (player->HasAura(DEATH_KNIGHT_BLOOD)) return DEATH_KNIGHT_BLOOD;
                if (player->HasAura(DEATH_KNIGHT_FROST)) return DEATH_KNIGHT_FROST;
                if (player->HasAura(DEATH_KNIGHT_UNHOLY)) return DEATH_KNIGHT_UNHOLY;
                break;
            case CLASS_SHAMAN:
                if (player->HasAura(SHAMAN_ELEMENTAL)) return SHAMAN_ELEMENTAL;
                if (player->HasAura(SHAMAN_ENHANCEMENT)) return SHAMAN_ENHANCEMENT;
                if (player->HasAura(SHAMAN_RESTORATION)) return SHAMAN_RESTORATION;
                break;
            case CLASS_MAGE:
                if (player->HasAura(MAGE_ARCANE)) return MAGE_ARCANE;
                if (player->HasAura(MAGE_FIRE)) return MAGE_FIRE;
                if (player->HasAura(MAGE_FROST)) return MAGE_FROST;
                break;
            case CLASS_WARLOCK:
                if (player->HasAura(WARLOCK_AFFLICTION)) return WARLOCK_AFFLICTION;
                if (player->HasAura(WARLOCK_DEMONOLOGY)) return WARLOCK_DEMONOLOGY;
                if (player->HasAura(WARLOCK_DESTRUCTION)) return WARLOCK_DESTRUCTION;
                break;
            case CLASS_DRUID:
                if (player->HasAura(DRUID_BALANCE)) return DRUID_BALANCE;
                if (player->HasAura(DRUID_FERAL)) return DRUID_FERAL;
                if (player->HasAura(DRUID_GUARDIAN)) return DRUID_GUARDIAN;
                if (player->HasAura(DRUID_RESTORATION)) return DRUID_RESTORATION;
                break;
            default:
                break;
        }

        return 0;
    }

    inline bool HasMasterySpecialization(Player const* player, uint32 masterySpell)
    {
        return GetMasterySpecializationSpell(player) == masterySpell;
    }

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

    inline float GetMasteryAuraBonus(Player const* player)
    {
        if (!player)
            return 0.0f;

        return float(player->GetTotalAuraModifier(SPELL_AURA_MASTERY));
    }

    /**
     * Current total Mastery points. MoP uses 8 base Mastery plus Mastery Rating
     * and SPELL_AURA_MASTERY (318) modifiers.
     */
    inline float GetMastery(Player const* player)
    {
        if (!IsMasteryAvailable(player))
            return 0.0f;

        return BASE_MASTERY + GetMasteryRatingBonus(player) + GetMasteryAuraBonus(player);
    }
}

#endif // ACORE_MASTERY_H
