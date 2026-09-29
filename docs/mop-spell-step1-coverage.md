# MoP Spell Port — Step 1 coverage

Base: `mop-spell-compat-stage1`. Reference: `ProjectSkyfire/SkyFire_548`.

## Effects 165–213

The current branch reserves 165–213 in `TOTAL_SPELL_EFFECTS`, but all of them dispatch to `EffectUnused` and `SpellEffectInfo::_data` stops at 164. Step 1 fixes the structural gap first, then wires only mechanics that are directly compatible with existing 3.3.5 handlers.

Implemented / directly mapped:

- 165 `DAMAGE_FROM_MAX_HEALTH_PCT` — generic max-health-percent damage handler.
- 171 — gameobject summon via existing `EffectSummonObject`.
- 176 — sanctuary/Vanish behavior via existing `EffectSanctuary`.
- 184 `REPUTATION_2` — existing `EffectReputation`.
- 208 `REPUTATION_3` — existing `EffectReputation`.
- 213 `JUMP_DEST_2` — existing `EffectJumpDest`.

Recognized but intentionally deferred:

- 166 currency.
- 169 destroy-item exact MoP semantics.
- 172 resurrect-with-aura.
- 173 guild-vault unlock.
- 179 AreaTrigger creation (Step 3).
- 181 MoP talent removal.
- 200/201 battle pets.
- Unknown/unused IDs remain explicit safe no-ops.

The patch also adds explicit target/object metadata through effect 213, so 165–213 no longer silently rely on zero-initialized metadata.

## Auras 319–437

All IDs 319–437 are explicitly defined in `SpellAuraDefines.h`. Direct legacy-equivalent handlers wired in Step 1:

- 319 `MOD_MELEE_HASTE_3` -> `HandleModMeleeSpeedPct`
- 320 `MOD_RANGED_HASTE_2` -> `HandleAuraModRangedHaste`
- 330 `CAST_WHILE_WALKING` -> existing stage-1 behavior retained unchanged
- 342 `MOD_MELEE_RANGED_HASTE_2` -> `HandleModMeleeRangedSpeedPct`
- 400 `MOD_SKILL_2` -> `HandleAuraModSkill`
- 407 `MOD_FEAR_2` -> `HandleModFear`

The rest stay inert until their real server-side dependencies are ported. This avoids silently mapping MoP mechanics to merely similar WotLK behavior.

## Regression tests

1. Spell 1459 — ordinary compatible spell behavior unchanged.
2. Spell 49575 — destination/jump behavior remains valid.
3. Spell 79206 — server continues casting while moving; the known 3.3.5 castbar visual interruption may remain.
4. Spell 115460 — Effect 179 is recognized with destination metadata but remains gameplay-NYI until AreaTriggers are implemented.
5. Test imported aura types 319 and 320 if present in the imported `SpellEffect.dbc`.
6. Confirm startup produces no out-of-range dispatch errors for effects <=213 or auras <=437.
