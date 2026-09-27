/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * Server-side Mastery diagnostics for the MoP-on-3.3.5 port.
 */

#include "Chat.h"
#include "CommandScript.h"
#include "Mastery.h"
#include "Player.h"
#include "RBAC.h"

using namespace Acore::ChatCommands;

namespace
{
    char const* GetMasterySpecializationName(uint32 spellId)
    {
        using namespace Acore::Mastery;

        switch (spellId)
        {
            case WARRIOR_ARMS: return "Warrior - Arms";
            case WARRIOR_FURY: return "Warrior - Fury";
            case WARRIOR_PROTECTION: return "Warrior - Protection";
            case PALADIN_HOLY: return "Paladin - Holy";
            case PALADIN_PROTECTION: return "Paladin - Protection";
            case PALADIN_RETRIBUTION: return "Paladin - Retribution";
            case HUNTER_BEAST_MASTERY: return "Hunter - Beast Mastery";
            case HUNTER_MARKSMANSHIP: return "Hunter - Marksmanship";
            case HUNTER_SURVIVAL: return "Hunter - Survival";
            case ROGUE_ASSASSINATION: return "Rogue - Assassination";
            case ROGUE_COMBAT: return "Rogue - Combat";
            case ROGUE_SUBTLETY: return "Rogue - Subtlety";
            case PRIEST_DISCIPLINE: return "Priest - Discipline";
            case PRIEST_HOLY: return "Priest - Holy";
            case PRIEST_SHADOW: return "Priest - Shadow";
            case DEATH_KNIGHT_BLOOD: return "Death Knight - Blood";
            case DEATH_KNIGHT_FROST: return "Death Knight - Frost";
            case DEATH_KNIGHT_UNHOLY: return "Death Knight - Unholy";
            case SHAMAN_ELEMENTAL: return "Shaman - Elemental";
            case SHAMAN_ENHANCEMENT: return "Shaman - Enhancement";
            case SHAMAN_RESTORATION: return "Shaman - Restoration";
            case MAGE_ARCANE: return "Mage - Arcane";
            case MAGE_FIRE: return "Mage - Fire";
            case MAGE_FROST: return "Mage - Frost";
            case WARLOCK_AFFLICTION: return "Warlock - Affliction";
            case WARLOCK_DEMONOLOGY: return "Warlock - Demonology";
            case WARLOCK_DESTRUCTION: return "Warlock - Destruction";
            case DRUID_BALANCE: return "Druid - Balance";
            case DRUID_FERAL: return "Druid - Feral";
            case DRUID_GUARDIAN: return "Druid - Guardian";
            case DRUID_RESTORATION: return "Druid - Restoration";
            default: return "None";
        }
    }
}

class mastery_commandscript : public CommandScript
{
public:
    mastery_commandscript() : CommandScript("mastery_commandscript") { }

    ChatCommandTable GetCommands() const override
    {
        static ChatCommandTable commandTable =
        {
            { "mastery", HandleMasteryCommand, rbac::RBAC_PERM_COMMAND_DEBUG_INFO, Console::No }
        };
        return commandTable;
    }

    static bool HandleMasteryCommand(ChatHandler* handler)
    {
        Player* player = handler->GetPlayer();
        if (!player)
            return false;

        uint32 activeMastery = Acore::Mastery::GetMasterySpecializationSpell(player);
        uint32 expectedMastery = Acore::Mastery::GetExpectedMasterySpecializationSpell(player);
        int32 rating = Acore::Mastery::GetMasteryRating(player);
        float dbcRatingRatio = Acore::Mastery::GetMasteryRatingRatioFromDBC(player);
        float effectiveRatingRatio = Acore::Mastery::GetMasteryRatingRatio(player);
        float dbcClassScalar = Acore::Mastery::GetMasteryClassScalarFromDBC(player);
        float effectiveClassScalar = Acore::Mastery::GetMasteryClassScalar(player);
        float ratingBonus = Acore::Mastery::GetMasteryRatingBonus(player);
        float auraBonus = Acore::Mastery::GetMasteryAuraBonus(player);
        float totalMastery = Acore::Mastery::GetMastery(player);
        bool available = Acore::Mastery::IsMasteryAvailable(player);
        bool synchronized = activeMastery == expectedMastery;

        handler->PSendSysMessage("=== Mastery diagnostic: {} ===", player->GetName());
        handler->PSendSysMessage("Level: {} | Talent tree ID: {} | Mastery available: {}",
            player->GetLevel(), player->GetSpec(), available ? "Yes" : "No");
        handler->PSendSysMessage("Expected specialization: {} ({})",
            GetMasterySpecializationName(expectedMastery), expectedMastery);
        handler->PSendSysMessage("Active Mastery aura: {} ({}) | Synchronized: {}",
            GetMasterySpecializationName(activeMastery), activeMastery, synchronized ? "Yes" : "NO");
        handler->PSendSysMessage("Mastery Rating: {}", rating);
        handler->PSendSysMessage("Rating DBC key: {} | DBC ratio: {:.6f} | Effective ratio: {:.6f}",
            Acore::Mastery::GetMasteryRatingLookupIndex(player), dbcRatingRatio, effectiveRatingRatio);
        handler->PSendSysMessage("Class scalar DBC key: {} | DBC scalar: {:.6f} | Effective scalar: {:.6f}",
            Acore::Mastery::GetMasteryClassScalarLookupIndex(player), dbcClassScalar, effectiveClassScalar);
        handler->PSendSysMessage("Base Mastery: {:.3f}", available ? Acore::Mastery::BASE_MASTERY : 0.0f);
        handler->PSendSysMessage("Rating bonus: {:.3f}", ratingBonus);
        handler->PSendSysMessage("Aura 318 bonus: {:.3f}", auraBonus);
        handler->PSendSysMessage("Total Mastery: {:.3f}", totalMastery);

        if (activeMastery == Acore::Mastery::MAGE_FROST)
        {
            static constexpr uint32 icicleStorageAuras[] = { 148012, 148013, 148014, 148015, 148016 };
            uint32 storedIcicles = 0;
            for (uint32 spellId : icicleStorageAuras)
                if (player->HasAura(spellId))
                    ++storedIcicles;

            handler->PSendSysMessage("Stored Icicles: {}/5", storedIcicles);
        }

        if (!synchronized)
            handler->PSendSysMessage("WARNING: active Mastery passive does not match the expected specialization.");

        return true;
    }
};

void AddSC_mastery_commandscript()
{
    new mastery_commandscript();
}
