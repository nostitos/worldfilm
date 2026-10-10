I've finished checking the stills, the cut strips and the gate JSONs, and I'm writing the report now.

# Critic round 9 (verification): "Block Space", draft 18

## 1. Previous top changes and signature moments

| # | Change | Status | Proof |
|---|---|---|---|
| 1 | Crane freeze | **FIXED** | gate-report.md: the longest still stretch is 0.2 s, at 17.8–18.0 s. That is the designed stop at NOW, not the crane. Inside the crane the stretches are 21.2–21.4 s (0.2 s) and 22.3–22.4 s (0.1 s). The total is 0.89 s per 30 s. The contact sheet from 20.8 to 22.2 s keeps moving. However, `hold_max` is still 0.6 s. I asked for 0.2 s and the gate was never tightened. |
| 2 | Ladder under the end card | **PARTLY** | t28.8 is clean: no spine and no rungs in the type. But cut-s08 at 27.00–27.15 s still shows a faint spine and rungs through "21,000,000" and through "20,999,999.9769 BTC" while the headline is already up. That contradicts the claim that the sweep asserts "invisible whenever the headline is up". Either the sweep samples too coarsely or its threshold forgives low alpha. It lasts about 9 frames and is faint, but it falls on the impact cue. |
| 3 | Gate 3 plate anchor | **FIXED** | At t11.4 the plate spans x 498–918, y 72–122. Its leader meets the gate's top bar at about x 945 at the bar's own height, about 27 px from the gate. At t12.9 the plate is still correct. |
| 4 | Dead top edge, 22.70–22.95 s | **FIXED, tight** | cut-s07 22.5–23.5 s: the bracket is on screen in every frame. But the horizon sits only about 5–45 px from the top edge (t22.8: about 45 px), so for a few tenths of a second the bracket is squeezed against the frame edge. It is legal, not comfortable. |
| 5 | Readout backing plate | **FIXED** | At t6.6 the readout reads cleanly over the slabs on the right. |
| 6 | Riser bed | **FIXED** | audible.json for the riser: `bed_db: null`, `bed_floor: true`, `lift_db: null`, level −12.2 dB. |

**Signature moments**
1. **The first gate halves the street: HOLDS.** At t6.6 the gate is orange at block 210,299, 25 BTC, 2012. kick-h1 lifts 15.0 dB.
2. **The camera stops at NOW: HOLDS.** At t18.3 the plate sits clear above the bar and shows block 970,440 in October 2026, with 20,095,128 issued. arrive-now lifts 28.7 dB.
3. **Crane up to a hairline that ends: HOLDS, and the blemish is gone.** t20.8 → t21.5 → t22.8 → t24.5 → t26.5 is continuous motion, and the line ends in the bracket. It reads on a phone (t24.5-phone).

## 2. Regressions and new findings

- **A wrong number is on screen, and the previous round (my own) missed it.** At t21.5 the readout shows `SUBSIDY 0.00076294 BTC` for block 3,490,440. Block 3,490,440 is in era 16. The protocol subsidy is `5,000,000,000 >> 16 = 76,293 sat` = **0.00076293 BTC**. The film rounds where Bitcoin truncates. The 21.3 s value from last round has the same bug: era 13 is `>> 13 = 610,351 sat` = 0.00610351, not 0.00610352. Exact eras (0.390625, 6.25, 3.125, 1 sat) are unaffected. The facts gate passes only because facts.json holds the same rounded values. This breaks the client's mandatory "a number on screen is wrong" rule.
- The ladder still shows through the headline for the first ~0.15 s after the cut (see item 2 above).
- No new colour outside the rule: the orange is only on gates, the bracket and 21,000,000. No collisions: t11.4 plate against the readout is clear, as is t18.3. Luma floor is 52.05 at 21.3 s. pops.json: 0 pops, 2 single shimmer frames at 10.12 s and 14.98 s, unchanged. Loudness is −14.1 LUFS. Silence holds from 25 to 27 s. All beats land with 0 frames of error.

## 3. Sound-off comprehension

The full argument lands on mute:
- one slab per 2,016 blocks, with height equal to the new coins;
- each orange gate halves the street;
- NOW is block 970,440 in October 2026, with 20,095,128 issued;
- the future is wireframe, and 28 more halvings still pay out;
- one line thins to block 6,929,999, around 2140;
- 21,000,000, never more, with the exact 20,999,999.9769 underneath.

A sharp-eyed Bitcoiner pausing the crane will catch the rounded subsidy figures.

## 4. Remaining problems, ranked

1. **Truncate subsidies; don't round them.** Wherever the readout and facts.json get their subsidy, compute it as `subsidySat = 5_000_000_000n >> BigInt(era)` (BigInt or integer shift), and format it as `(subsidySat / 1e8).toFixed(8)` on the integer sats. Regenerate facts.json from the same function. Add a facts-gate assertion that every displayed subsidy equals `floor(5e9 / 2^era) / 1e8` for the era of the block shown beside it.
2. **The ladder bleeds into the headline from 27.00 to 27.15 s.** Move `ladderOpacityAt` so it reaches 0 at or before the headline's first non-zero opacity (end the fade at 27.0 s, or start the headline at 27.4 s). Make tools/sweep.mjs sample every frame (1/60 s) from 26.8 to 27.6 s, and fail on any ladder alpha above 0.01 inside the padded text boxes.
3. **Bracket pinned to the top edge, 22.5–23.0 s.** Lift the edge-y target to at least 4 % (about 43 px) from 22.3 s, so the bracket never sits within 40 px of the frame edge.
4. **Gate threshold.** Set `hold_max_s` to 0.2 for non-designed holds, and whitelist the 17.8–18.0 s NOW stop explicitly, so the gate catches future crane freezes.

VERDICT: ONE MORE PASS
