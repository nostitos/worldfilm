Checked: all the evidence has been read, and the report follows.

# Critic round 5 (verification): "Block Space", draft 13

## 1. Previous top changes and signature moments

| # | Change | Status | Proof |
|---|---|---|---|
| 1 | End composition: roll, horizon, black sky | **PARTLY** | **Roll is fixed:** at t25.0, t26.5 and t28.8 the horizon is level. **Horizon is not fixed.** At t23.5 the ground edge sits at y≈425 (39 % from the top), not 21 %. The top 39 % is a near-black gradient that reads as flat dark sky. It does not leave the top fifth until about 24.5 s. At t25.0 it is at 14.5 % and at t26.5 at about 9.5 %. |
| 2 | Hairline that ends | **PARTLY** | The apron is gone. The hairline itself only exists at t20.8. From 23.0 s the street is a wide lit trapezoid with scattered ink rungs on both sides (t25.0, t26.5). It reads as a runway with lane markings, not as a line thinning to nothing. The rungs sit off the road, so they read as decoration, not as the "footprint" of the schedule. |
| 3 | Gate 1 as a gate in profile | **PARTLY** | At t5.8 and t6.6 it is still **one orange blade**, about 20–30 px wide and tapering like a wedge. There is no second post and no top bar. It now rises above the 50-coin roofs (y≈220 against roofs at about 180–280), so it is no longer hidden. But a "portal" never shows during the 5.8–7.0 s hold. The step down to half is clear. |
| 4 | Shimmer | **STILL** (in this file) | pops.json: WARN, 21 shimmer frames from 3.87 s. The fix is said to come from the delivered master's shutter. Nothing I was given shows that. |
| 5 | Labels above crossbars; BLOCK 0 | **PARTLY** | BLOCK 0 is gone (t1.5 is clean): FIXED. **Gate 3 still collides:** at t11.4 the "HALVING 3 · 6.25 BTC" plate sits across the portal's top bar, with orange showing behind the plate at x≈945–1040. It only clears at close range (t12.9). |
| 6 | 2140 in one place | **FIXED** | t25.0: the label reads "LAST BLOCK · 6,929,999". "≈ 2140" appears only in the readout and the caption. |

**Signature moments**
1. **The first gate halves the street: PARTLY.** The step reads (t5.8: 50-coin roofs at about y 180–280, 25-coin roofs at about y 380–420). The gate still reads as an orange sliver, not a gate. kick-h1 at 7.00 s, lift 15 dB.
2. **Camera stops at NOW: FIXED.** At t18.3 the portal, label, readout (970,440 / 3.125 / 2026) and caption (20,095,128) agree. arrive-now lifts 28.7 dB at 17.40 s. This is still the best frame in the film.
3. **Crane up to a hairline that ends: PARTLY.** t20.8 delivers it. From 23.0 s the picture turns back into a wide grey road under a dark sky, and the "end" is a 160 px orange bracket.

## 2. Regressions

- **The end label sits on the end gate.** At t26.5 the "LAST BLOCK · 6,929,999" plate covers the gate. Two orange post tips poke out behind it at x≈855 and x≈1060. At t25.0 they barely clear.
- **The end card cuts through the gate.** At t28.8 the frame's top edge slices the orange bracket in half. It does not "rise out of frame"; it stays parked on the edge for 2 s, as a tangent.
- **Rungs strike through the hero number.** At t28.8 ink rungs run behind "21,000,000": one at y≈345 under the "2", one at y≈405 through the zeros.
- **Two years on screen at once.** At t23.5 the readout says "≈ 2139" while the caption says "AROUND 2140". Both are defensible, but a mute viewer sees a contradiction 1.5 s before the payoff.
- **Faint blotches on the street.** At t25.0 and t26.5 the end street shows faint bluish and reddish patches (y≈580–760). This looks like dither or fog banding on a large flat area.
- **One cue may be late.** audible.json schedules sub-h4 at 15.52 s, but its measured peak is 16.01 s (peak_t 16.26), and it is still marked "late: false" against a 0.03 s tolerance. Either the gate is wrong or the cue lands half a second late.

**Passes:**
- Luma floor is 50.05 at 23.7 s.
- The silence from 25 to 27 s is clean.
- Frozen time is 0.63 s per 30 s.
- I found no wrong number and no orange outside the gates and the hero number.

## 3. Sound-off comprehension

A mute viewer gets:
- one building per 2,016 blocks, with height equal to the new coins;
- the street drops to half at the first orange mark, and again at each later mark;
- you are at block 970,440 in Oct 2026, with 20,095,128 issued;
- the future is wireframe, and 28 halvings remain;
- the last block is 6,929,999, around 2140;
- 21,000,000, never more, exactly 20,999,999.9769 BTC.

They miss that gate 1 is a gate (it reads as a tick). At the end they see a road meeting a dark sky, not a line running out.

## 4. Remaining problems, ranked

1. **Fix the end framing between 23.0 and 24.5 s.**
   - Pitch down harder, so the ground edge is at y ≤ 0.2·H by 23.0 s, as claimed. It is currently 0.39·H at 23.5 s.
   - Or lift the sky gradient's top stop toward #1B1F26 so the sky never reads as a flat black band.
2. **Make the end read as a hairline.**
   - Narrow the lit street to the slab footprint width, or fade its emissive and fog lift to zero beyond NOW.
   - Draw the rungs centred on the street axis, spanning it, not beside it, so the eye follows one shrinking line to the bracket.
3. **Make gate 1 a gate.**
   - During 5.8–7.0 s, yaw the camera 15–20° off pure profile so both posts and the top bar separate on screen.
   - Or draw the far post and bar with `depthTest:false` at reduced opacity.
4. **Fix the label collisions.**
   - Offset each label anchor to at least 40 px above the projected top bar, computed per frame (not from the roof line): gate 3 at about 11.4 s and LAST BLOCK at 26.5 s.
   - At the end card, either push the camera until the bracket is fully out of frame by 27.0 s, or stop it with the bracket fully inside the frame.
5. **Clear the hero number.** From 27.0 s, fade the rungs to 0 inside the number's bounding box plus 40 px (or put a 60 % ground plate behind the number).
6. **Close the open checks.**
   - Prove the shimmer is gone on the delivered master: rerun pops.json on that file.
   - Re-time sub-h4 to peak within 0.03 s of 15.52 s, or fix the audible gate's late check.
   - Hold the readout's year at "≈ 2140" once the caption is up.

VERDICT: ONE MORE PASS
