# Critic round 10 (verification): "Block Space", draft 19

## 1. Previous top changes and signature moments

| # | Change | Status | Proof |
|---|---|---|---|
| 1 | Truncate subsidies | **FIXED** | **t21.3:** block 2,823,202 is in era 13. The readout shows 0.00610351 BTC, which is 5,000,000,000 >> 13 = 610,351 sat. **t21.5:** block 3,490,440 is in era 16. It shows 0.00076293 BTC, which is >> 16 = 76,293 sat. **t22.5 and t22.8:** blocks 6,834,052 and 6,854,399 are in era 32. They show 0.00000001, which is 1 sat. **t6.6:** block 210,299 shows 25 BTC; it is past the 210,000 boundary, so that is correct. **t18.3:** block 970,440 shows 3.125 BTC. I checked all of these by hand. The facts gate passes with 18 of 18 tokens. |
| 2 | Ladder bleeding into the headline | **FIXED** | **cut-s08:** the ladder is gone by 26.85 s. The 27.00 s frame shows only the fading headline and the bracket. 27.05–27.15 s are clean. **t27.1** has no spine and no rungs. **t28.8** is clean. |
| 3 | Bracket pinned to the top edge | **FIXED** | The bracket sits about 55 px from the top at t22.5, about 68 px at t22.8, and is well clear at t23.5 and t24.5. All are above the 40 px floor. |
| 4 | Gate threshold | **PARTLY** | I asked for a 0.2 s limit with the NOW stop whitelisted. The builder set a global 0.3 s instead. A 0.25 s freeze in the crane would now pass. The crane still has a 0.2 s still at 21.1–21.3 s. The normalised total is 1.00 s per 30 s against a 1.0 limit, so it passes with no margin. Last round it was 0.89. |

**Signature moments**
1. **The first gate halves the street: HOLDS.** At t6.6 the orange gate reads at block 210,299 with the plate "HALVING 1 · 25 BTC". The kick lifts 15.0 dB and lands 0.05 s after the cue.
2. **The camera stops at NOW: HOLDS.** At t18.3 the gate is centred. "NOW · BLOCK 970,440 · OCT 2026" sits clear above the top bar, and "20,095,128 COINS ISSUED SO FAR." is in the caption. The arrive-now cue lifts 28.7 dB.
3. **Crane up to a hairline that ends: HOLDS.** The crane moves continuously from t20.8 to t24.5, and the line ends in the bracket. It reads on a phone (t24.5-phone). The ladder now fades from 26.5 to 26.85 s, so the line dissolves just before the headline instead of being cut by it. The 26.9–26.95 s frames hold only the bracket, which sits inside the designed 25–27 s silence. It reads as a breath, not a dead frame.

## 2. Regressions

- **The still-time total crept up from 0.89 to 1.00 s per 30 s.** The new 0.1 s stretch at 26.6–26.7 s comes from the ladder fade. The gate now passes exactly at its limit.
- **The readout plate touches the horizon at t22.5.** The plate's top is at y≈72 and the horizon line at y≈62. They do not collide, but the plate looks as if it hangs off the horizon. This is cosmetic.
- **No new colour outside the rule.** Orange appears only on the gates, the NOW gate, the bracket, the small orange markers on the hairline, and 21,000,000. The hairline markers sit at halving positions and read as tiny gates.
- **No new collisions.**
- **Other measurements are steady:**
  - The luma floor is 52.04 at 21.3 s, against a limit of 35. There are 0 dark seconds.
  - There are 0 pops and 0 flashes. The same 2 single shimmer frames remain, at 10.12 s and 14.98 s.
  - All 15 sound cues are audible and none is late. The silence window holds.
  - Loudness is −14.1 LUFS and true peak −2.3 dBTP.
  - All 8 cuts land with 0 frames of beat error.

## 3. Sound-off comprehension

On mute, a viewer gets the whole argument:
- one building per 2,016 blocks, with height equal to the new coins;
- each orange gate halves the street;
- NOW is block 970,440 in October 2026, with 20,095,128 issued;
- the future is wireframe, and 28 more halvings still pay out;
- the subsidy shrinks to 1 satoshi, and the last block is 6,929,999, around 2140;
- 21,000,000, never more, with the exact 20,999,999.9769 BTC underneath.

A Bitcoiner who pauses the crane now finds subsidy figures that match Bitcoin Core to the satoshi.

## 4. Remaining problems, ranked

1. **The scheduled years use an unclear model.** At t21.3, block 2,823,202 reads "≈ 2061". A flat 10-minute projection from block 970,440 in October 2026 gives early 2062. At t21.5, block 3,490,440 reads "≈ 2074", which the same projection matches. The "≈" covers it and I do not call it wrong, but the model should be stated and tested. Use one function, for example `year = 2026.77 + (h − 970440) / 52560`, floored. Have sweep.mjs assert that every displayed year equals that function.
2. **Restore a separate hold limit for the crane.** Set `hold_max_s` to 0.2 for every stretch except an explicit whitelist entry for 17.8–18.0 s. Shorten the ladder fade's tail so that 26.6–26.7 s is not counted as still, which gives the per-30 s total some margin below 1.0.
3. **Readout plate against the horizon, 22.3–23.0 s.** Either move the plate down about 20 px while the horizon is above y≈90, or let it ride 16 px below the horizon line.
4. **Two shimmer frames, at 10.12 s and 14.98 s.** These are single-frame thin-line crawls on the wireframe. Raise the line width by 0.25 px or lift the minimum alpha on distant wireframe edges. This is low priority and invisible at speed.

None of these breaks the client's rules. Every number checked is correct. The luma never drops below 52. Orange stays on the gates, the bracket and the number, and all three signature moments land.

VERDICT: SHIP
