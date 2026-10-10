# Critic round 8 (verification): "Block Space", draft 17

## 1. Previous top changes and signature moments

| # | Change | Status | Proof |
|---|---|---|---|
| 1 | Ground edge reverses | **FIXED** | Edge y measured on the stills: t23.5 at 87 (8 %), t24.5 at 185 (17 %), t26.5 at 220 (20.4 %), t28.8 at 230 (21.3 %). It only moves down, with no overshoot. The 40 px climb-back is gone. |
| 2 | NOW plate on the post | **FIXED** | At t18.3 the plate spans x 655–1265, y 72–122, and the gate's top bar starts at y ≈ 128. The plate sits above the bar, clear of both posts, and nothing orange is covered. |
| 3 | Hairline too faint for a phone | **FIXED** | At t24.5-phone (640 px) the spine and every rung read as one line down to the bracket. At t26.5 the rungs taper from about 40 px to about 18 px with a continuous spine. This is the first time the end reads as a line that ends, not a dotted road marking. |
| 4 | Blur-master pops | **FIXED (by evidence)** | blur-draft14/pops.json admits 20 shimmer frames at 3.85 s and later, so the earlier claim was false and the builder now says so. s02-blur-pops.json and s02-sharp-pops.json both measure 0. draft17/pops.json: 0 pops, 2 single shimmer frames (10.12 s, 14.98 s). That is down from 23. |
| 5 | Crane hold | **STILL** | The builder claims "longest hold now 0.2 s". gate-report.md says the opposite: **longest still stretch 0.5 s at 21.3–21.8 s**, mid-crane. The new 21.8 s key landed at the end of the freeze instead of breaking it. The hold limit is still 0.6 s, the loosened value I flagged last round. |
| 6 | Gate 3 plate anchor | **STILL** | At t11.4 the gate is at x 945–1040, y 48–125, and the "HALVING 3 · 6.25 BTC" plate is still at y 330–380, about 205 px below it. Its 24 px leader points left at slabs, not at the bar's end. The flip rule only fires when the plate would land on the top bar, and here it lands beside a hidden post, so this case is never handled. At t12.9 it is correct. |

**Signature moments**
1. **The first gate halves the street: HOLDS.** At t6.6 the gate is orange at block 210,299, 25 BTC, 2012, and kick-h1 lifts 15 dB.
2. **The camera stops at NOW: HOLDS, and is now clean.** At t18.3 there is no collision. arrive-now lifts 28.7 dB.
3. **Crane up to a hairline that ends: HOLDS, with one blemish.** t20.8 → t21.3 → t24.5 → t26.5 is a continuous thinning line into the bracket, and it reads on a phone. The 0.5 s freeze at 21.3–21.8 s still sits inside it.

## 2. Regressions

- **The ladder runs through the end card.** At t28.8 the spine and rungs pass behind "21,000,000". One rung lands in the gap of "NEVER MORE.", and the spine cuts "20,999,999.9769" at the decimal point. It is dimmed, but on the film's last and most important text it reads as a strike-through. The sweep checks that the edge stays still under the number. It does not check that the ladder stays out of the type.
- **0.25 s of empty frame before s08.** In cut-s07, 22.70–22.95 s, the horizon sits on the top edge with no bracket. t22.9 shows the edge at y ≈ 0. The solved curve starts at 23.0 s, and the frames just before it were never brought into it.
- **The riser's bed is still −80 / lift 67.8 dB** in audible.json, and nothing marks it as a floor. The claim that it is "reported as a floor, not null" is not in the file. This is cosmetic: −12.2 dB is plainly audible.

**Passes:** no wrong number. I checked t6.6, t11.4 (549,024 at 12.5 BTC is mid-era, correct), t12.9 (636,178, 6.25, 2020), t18.3, t20.8 (0.390625, ≈2038), t21.3 (0.00610352, ≈2061), t23.5 (6,881,489, 1 sat, ≈2139), t24.5 and t26.5 (6,929,999, ≈2140), and the card. No orange outside the gates, the bracket and the number. Luma floor is 51.55 at 21.6 s, against the 35 minimum. Silence holds from 25 to 27 s. Loudness is −14.1 LUFS. The tone is serious throughout.

## 3. Sound-off comprehension

A mute viewer now gets the whole argument:
- one building per period, with height equal to the new coins;
- each orange gate halves the street;
- NOW is block 970,440 in October 2026, with 20,095,128 issued;
- the future is wireframe, and 28 halvings remain;
- a single line runs out and ends at block 6,929,999, around 2140;
- 21,000,000, never more.

The end stretch no longer goes grey on a phone.

## 4. Remaining problems, ranked

1. **Crane freeze at 21.3–21.8 s (0.5 s).** Re-time the mid key to 21.5 s, or enforce a minimum crane speed of at least 3 % of peak from 20.0 to 22.6 s. Then set `hold_max_s` back to 0.2 for non-designed holds, so the gate catches this case.
2. **Ladder under the end-card type.** From 26.8 s, either fade the ladder to 0 inside the text block's padded box, or mask it with the card's ground colour behind the type. Add a sweep check that no ladder pixel falls inside any text box.
3. **Gate 3 plate floats 205 px off its gate (t11.4).** Extend the flip rule: if the right post is occluded (sample depth at the post's projected midpoint), anchor the plate to the top bar's right end plus 24 px, at the bar's y, with the leader touching the bar. Assert that the plate's distance to the gate's bounding box is at most 40 px.
4. **Dead top edge, 22.70–22.95 s.** Extend the edge-y target curve back to 22.6 s (from 2 % to 6 %), so the bracket is always on screen after the cut.
5. **Readout over slabs at t6.6.** Add a 0.6-opacity #0B0D10 backing plate behind the top-right readout.
6. **Riser bed.** Write `bed_db: null, bed_floor: true` and drop the 67.8 dB lift from the report.

VERDICT: ONE MORE PASS
