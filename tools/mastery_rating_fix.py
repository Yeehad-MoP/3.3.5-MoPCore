from pathlib import Path

# Patch Mastery.h
path = Path('src/server/game/Entities/Player/Mastery.h')
text = path.read_text()
start = text.index('    /**\n     * Converts raw Mastery Rating to Mastery points using gtCombatRatings block')
end = text.index('    inline float GetMasteryAuraBonus', start)
replacement = r'''    inline uint32 GetMasteryRatingLookupIndex(Player const* player)
    {
        if (!player || !player->GetLevel())
            return 0;

        uint8 level = std::min<uint8>(player->GetLevel(), GT_MAX_LEVEL);
        return COMBAT_RATING_INDEX * GT_MAX_LEVEL + level - 1;
    }

    inline uint32 GetMasteryClassScalarLookupIndex(Player const* player)
    {
        if (!player || !player->getClass())
            return 0;

        return (player->getClass() - 1) * GT_MAX_RATING + CLASS_SCALAR_INDEX;
    }

    inline float GetMasteryRatingRatioFromDBC(Player const* player)
    {
        if (!player)
            return 0.0f;

        if (GtCombatRatingsEntry const* rating = sGtCombatRatingsStore.LookupEntry(GetMasteryRatingLookupIndex(player)))
            return rating->ratio;

        return 0.0f;
    }

    inline float GetMasteryClassScalarFromDBC(Player const* player)
    {
        if (!player)
            return 0.0f;

        if (GtOCTClassCombatRatingScalarEntry const* scalar =
            sGtOCTClassCombatRatingScalarStore.LookupEntry(GetMasteryClassScalarLookupIndex(player)))
            return scalar->ratio;

        return 0.0f;
    }

    /**
     * Canonical MoP 5.4.8 Mastery rating curve for the supported 80-90 range.
     *
     * gtCombatRatings in a stock 3.3.5 client predates Mastery. Even when a
     * Mastery block is appended/ported, the legacy DBC storage/indexing path is
     * not guaranteed to expose that post-WotLK block under the same key layout.
     * Keep the exact 5.4.8 values server-side for the levels this port supports.
     */
    inline float GetMasteryRatingRatio(Player const* player)
    {
        if (!player)
            return 0.0f;

        switch (player->GetLevel())
        {
            case 80: return 45.905987f;
            case 81: return 60.278423f;
            case 82: return 79.155647f;
            case 83: return 103.985641f;
            case 84: return 136.538132f;
            case 85: return 179.280045f;
            case 86: return 228.0f;
            case 87: return 290.0f;
            case 88: return 370.0f;
            case 89: return 470.0f;
            case 90: return 600.0f;
            default:
                return GetMasteryRatingRatioFromDBC(player);
        }
    }

    inline float GetMasteryClassScalar(Player const* player)
    {
        if (!player)
            return 0.0f;

        float scalar = GetMasteryClassScalarFromDBC(player);
        if (scalar > 0.0f)
            return scalar;

        // Every non-Monk WotLK class uses a 1.0 Mastery scalar in the supplied
        // MoP gtOCTClassCombatRatingScalar data. Class 10 is intentionally not
        // enabled in this 3.3.5 port.
        uint8 classId = player->getClass();
        if (classId >= 1 && classId <= 11 && classId != 10)
            return 1.0f;

        return 0.0f;
    }

    /**
     * Converts raw Mastery Rating to Mastery points without touching the
     * WotLK PLAYER_FIELD_COMBAT_RATING array.
     */
    inline float GetMasteryRatingBonus(Player const* player)
    {
        if (!player)
            return 0.0f;

        float ratingRatio = GetMasteryRatingRatio(player);
        float classScalar = GetMasteryClassScalar(player);
        if (ratingRatio <= 0.0f || classScalar <= 0.0f)
            return 0.0f;

        return float(GetMasteryRating(player)) * classScalar / ratingRatio;
    }

'''
text = text[:start] + replacement + text[end:]
path.write_text(text)

# Patch .mastery diagnostics
path = Path('src/server/scripts/Commands/cs_mastery.cpp')
text = path.read_text()
old = '''        float ratingBonus = Acore::Mastery::GetMasteryRatingBonus(player);\n        float auraBonus = Acore::Mastery::GetMasteryAuraBonus(player);\n'''
new = '''        float dbcRatingRatio = Acore::Mastery::GetMasteryRatingRatioFromDBC(player);\n        float effectiveRatingRatio = Acore::Mastery::GetMasteryRatingRatio(player);\n        float dbcClassScalar = Acore::Mastery::GetMasteryClassScalarFromDBC(player);\n        float effectiveClassScalar = Acore::Mastery::GetMasteryClassScalar(player);\n        float ratingBonus = Acore::Mastery::GetMasteryRatingBonus(player);\n        float auraBonus = Acore::Mastery::GetMasteryAuraBonus(player);\n'''
if old not in text:
    raise SystemExit('cs_mastery variable anchor not found')
text = text.replace(old, new, 1)
old = '''        handler->PSendSysMessage("Mastery Rating: {}", rating);\n        handler->PSendSysMessage("Base Mastery: {:.3f}", available ? Acore::Mastery::BASE_MASTERY : 0.0f);\n        handler->PSendSysMessage("Rating bonus: {:.3f}", ratingBonus);\n'''
new = '''        handler->PSendSysMessage("Mastery Rating: {}", rating);\n        handler->PSendSysMessage("Rating DBC key: {} | DBC ratio: {:.6f} | Effective ratio: {:.6f}",\n            Acore::Mastery::GetMasteryRatingLookupIndex(player), dbcRatingRatio, effectiveRatingRatio);\n        handler->PSendSysMessage("Class scalar DBC key: {} | DBC scalar: {:.6f} | Effective scalar: {:.6f}",\n            Acore::Mastery::GetMasteryClassScalarLookupIndex(player), dbcClassScalar, effectiveClassScalar);\n        handler->PSendSysMessage("Base Mastery: {:.3f}", available ? Acore::Mastery::BASE_MASTERY : 0.0f);\n        handler->PSendSysMessage("Rating bonus: {:.3f}", ratingBonus);\n'''
if old not in text:
    raise SystemExit('cs_mastery output anchor not found')
text = text.replace(old, new, 1)
path.write_text(text)
