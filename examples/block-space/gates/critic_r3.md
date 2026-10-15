# Critic round 3 (verification): "Block Space", draft 9

## 1. Previous top changes and signature moments

| # | Change | Status | Proof |
|---|---|---|---|
| 1 | Readout tied to the picture, no drift at the end | **PARTLY** | The "IN VIEW · BLOCK" label makes the early subsidy flips defensible: 430,084 / 12.5 at t9.9, 635,528 / 6.25 at t12.9, 845,700 / 3.125 at t15.4. It climbs steadily to 6,929,999 by 22.95 s (cut-s07) and is gone by 27.4 s. **But t5.6 reads BLOCK 210,000 · SUBSIDY 50 BTC. Block 210,000 pays 25 BTC.** The same frame carries the label "HALVING 1 · 25 BTC". A wrong number on screen is the client's stated deal-breaker. |
| 2 | Halving visible at gate 1 | **PARTLY** | There is a raised oblique view from about 6.0 to 7.0 s (t6.9, cut-s02). The 50-coin slabs are still nearer the camera than the 25-coin slabs, so perspective blurs the step down again. The gate shows as two thin orange slivers, and the HALVING 1 label sits on top of its crossbar. The kick lands at 7.00 s, on the cut. The camera passes the gate at about 7.2–7.3 s, so the hit lands about 0.2–0.3 s before the gate it marks. |
| 3 | One label at a time; HALVING 5 has two fields | **FIXED** | t12.9 shows HALVING 3 alone. NOW is gone by 19.8 s and HALVING 5 starts at 20.0 s with "· 1.5625 BTC". |
| 4 | No void at 22.8–24.3 s | **FIXED** | The crane is continuous through the cut (cut-s07). The end gate is a speck at about 23.4 s and readable at 24.4 s. |
| 5 | End-card layout | **PARTLY** | The headline is clear of the gate (t28.8). The exact figure is legible ink, but it has no unit: "20,999,999.9769" with nothing after it. |
| 6 | Genesis label | **PARTLY** | At t2.5 it is still fully opaque, pinned to a near slab while the readout says 94,129. It is gone by 2.60 s (cut-s01), so the label and readout disagree for about 1.5 s. |

**Signature moments**
1. **First gate steps the street down to half: PARTLY.** This is better than draft 7, but the label still carries the idea, not the picture. The gate is barely visible in its own moment.
2. **Camera stops at NOW: FIXED.** At t18.3 the label, readout and caption agree, and the arrive-now cue gives a 28.8 dB lift at 17.40 s. It is still the best beat.
3. **Crane up to a hairline that ends: FIXED.** The move from 20.0 to 26.5 s reads as one move. The hairline resolves into the clipped end gate.

## 2. Regressions

- **Luma margin collapsed.** The lowest 0.5 s window is now 36.37 at 27.25 s, against 42.4 in draft 7 and a floor of 35. One encoder pass or a phone brightness curve could take it under.
- **Dead sky.** From 22.8 to 27.4 s, 55–75% of the frame is flat #0B0D10 above the horizon (t23.0, t26.5). Luma passes, but on a phone this is the "black tunnel" the client fears, turned on its side.
- **6,929,999 appears three times at once** from 24.4 to 27.2 s: in the readout, the 3D label and the caption (t24.5, t26.5). Each copy weakens the others.
- **Crowded bottom quarter at t26.5.** The label sits 36 px above the caption, and wireframe slab outlines show through the caption plate.
- **The post-swoop pass is mechanical.** motion_shape flags s04 (12–15 s) as constant speed (CV 0.15), and the contact sheet frames from 13.2 to 14.8 s are nearly identical. Shimmer and pops measure 0, which is good.
- **Colour, strict reading.** Every label, including the non-gate "BLOCK 0 · 50 BTC", has an orange tick bar. The brief allows orange only on gates and the number.

## 3. Sound-off comprehension

A mute viewer gets:
- one building per period, with height equal to the new coins;
- orange gates are halvings;
- "you are here: block 970,440, 20,095,128 issued";
- the future is wireframe and thins out;
- 28 more halvings;
- the last coin comes at block 6,929,999, around 2140;
- 21,000,000, never more.

They still learn "halves at each gate" mostly from the labels. A careful viewer who pauses at 5.6 s sees 50 BTC printed next to "HALVING 1 · 25 BTC" and stops trusting the numbers. The unlabelled 20,999,999.9769 reads as a stray figure.

## 4. Remaining problems, ranked

1. **Fix the boundary subsidy.** Derive subsidy and year from the same rounded integer that is displayed: `sub = 50 / 2**floor(shown / 210000)`. Add a per-frame assertion `subsidy(shownBlock) === shownSubsidy` across all 1,800 frames, so 420,000, 630,000 and 840,000 can't repeat this.
2. **Make gate 1 legible.**
   - Move the HALVING 1 label up so it sits above the roof line, offset to one side of the gate.
   - Thicken the gate posts while the camera is in profile.
   - Place the camera so the last 50-coin slab and the first 25-coin slab are at equal distance from it.
   - Hold the profile for at least 1.2 s.
   - Put kick-h1 on the frame where the camera crosses the gate plane, about 7.25 s, not on the 7.00 s cut.
3. **Recompose the end stretch.**
   - From 22.8 to 27.4 s, pitch the camera down about 8–10° so the horizon sits in the upper third.
   - Lift the ground's lightness near the end gate so the minimum luma window gets back above 42.
4. **De-duplicate 6,929,999.** Drop the number from the caption ("LAST NEW COIN ≈ 2140.") or hide the 3D label while the caption is up. Keep at least 60 px between the label and the caption plate.
5. **Give the exact figure its unit:** "20,999,999.9769 BTC".
6. **Change the label tick bars from orange to ink**, or use orange only on the gate labels and never on BLOCK 0. While in s04, add ease or a slight speed swell to 12–15 s so it isn't a constant-speed dolly.

VERDICT: ONE MORE PASS
