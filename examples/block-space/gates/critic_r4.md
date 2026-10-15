I've read all the evidence. Here is the report.

# Critic round 4 (verification): "Block Space", draft 10

## 1. Previous top changes and signature moments

| # | Change | Status | Proof |
|---|---|---|---|
| 1 | Boundary subsidy | **FIXED** | t5.8 reads 210,000 / 25 BTC / 2012. Every readout I checked matches its block: t11.4 549,024 / 12.5 / 2018; t18.3 970,440 / 3.125; t20.8 1,595,400 / 0.390625 / ≈2038; t25.0 6,929,999 / 0.00000001 / ≈2140. 20,095,128 checks against blocks 0–970,440 inclusive. I found no wrong number. |
| 2 | Gate 1 legible | **PARTLY** | The step down now reads in the picture. In the profile at t5.8–t6.6, the 50-coin roofs sit at about y 80–110 and the 25-coin roofs at about y 300–330, so you see roughly half. The label is above the roofs and off to the right. **But the gate itself is a 10×90 px orange stub** at x≈955, cut off by the last 50-coin slab. It reads as a tick mark, not a gate. kick-h1 lands at 7.00 s (lift 15 dB), at the end of the hold. That is defensible. |
| 3 | End stretch recomposed | **STILL** | The claim that "the horizon leaves the frame from 23.0 s" is false. At t23.5 the top 49% of the frame is flat #0B0D10. At t25.0 and t26.5 it is 35–45%, with a diagonal horizon across the frame. Luma passes (min window 44.6 at 29.98 s), but the dead sky the last report flagged is still there. |
| 4 | De-duplicate 6,929,999 | **FIXED, with a new duplicate** | 6,929,999 now appears only in the label and the readout. **"≈ 2140" now appears three times at once** (readout, label, caption) at t25.0 and t26.5. The label clears the caption by more than 400 px. |
| 5 | Unit on the exact figure | **FIXED** | t28.8: "20,999,999.9769 BTC". |
| 6 | Ink tick bars; s04 ease | **FIXED** | Tick bars are ink at t5.8, t18.3 and t25.0. s04 measures CV 0.32 (PASS), although frames 13.2–14.8 on the contact sheet still look nearly identical. |

**Signature moments**
1. **First gate halves the street: PARTLY.** The halving now shows in the picture, which it did not before. The gate is still the weakest object in its own moment.
2. **Camera stops at NOW: FIXED.** At t18.3 the label, readout and caption agree. arrive-now lifts 28.7 dB at 17.40 s. This is still the best frame in the film.
3. **Crane up to a hairline that ends: PARTLY (regressed from FIXED).** At t20.8 there is a real hairline. From 23.0 s the lit apron turns the end into a broad grey plaza with flat outlines that read as parking bays (t23.5). The "hairline that ends" becomes a wide road meeting a wall of black.

## 2. Regressions

- **Unmotivated Dutch tilt.** From about 24.4 s through the end card, the horizon rolls about 10° (t25.0, t26.5, t28.8). In a "serious tone" film this reads as a mistake, and the end card sits on a crooked world.
- **Shimmer came back.** pops.json is now WARN with 21 shimmer frames, starting at 3.82 s, against 0 in draft 9. The thin wireframe edges are crawling.
- **The gate 3 label sits on its crossbar.** At t11.4 the orange crossbar shows as a strip under "HALVING 3 · 6.25 BTC". Only gate 1 was moved above the roof line.
- **The genesis label and readout still disagree.** At t1.5, "BLOCK 0" is pinned to a near slab while the readout says 54,400. The window is shorter but still there.
- **Caption plate overlap.** At t20.8, wireframe slabs run under the right edge of "28 MORE HALVINGS STILL PAY OUT."

## 3. Sound-off comprehension

A mute viewer gets:
- one building per period, with height equal to the new coins;
- **at the first orange mark, the buildings drop to about half** (they now see this, not just read it);
- the later gates repeat it;
- you are at block 970,440, with 20,095,128 issued;
- the future is wireframe and thins out;
- 28 more halvings still pay out;
- the last coin comes around 2140;
- 21,000,000, never more, exactly 20,999,999.9769 BTC.

No number on screen contradicts another. What they will miss is gate 1 as a *gate*: they see a step and an orange tick. What they will feel at the end is a tilted plaza under a black sky, not a street narrowing to nothing.

## 4. Remaining problems, ranked

1. **Fix the end composition.**
   - Remove the roll: set camera `up = (0,1,0)` and zero the roll term from 23.0 s.
   - Actually pitch down, so the horizon sits at or above y = 0 by 23.5 s, or keep it within the top 15%.
   - If the horizon must stay, lift the far ground and fog toward ink-grey so the sky is no longer flat #0B0D10 across a third of the frame.
2. **Bring back the hairline at the end.**
   - Shrink the apron to a soft radial pool about 2× the street width around the end gate, not the whole ground plane.
   - Draw the zero-height future slabs as a single ink line, not rectangle outlines.
3. **Make gate 1 a gate in profile.**
   - Draw both posts and the crossbar, or at minimum a full-height post above the occluding roof.
   - Render it on top with `depthTest:false` during 5.8–7.0 s, or move the camera half a slab toward the 25-coin side so the post isn't hidden.
   - Post width ≥ 0.35 units while in profile.
4. **Kill the shimmer.** From 3.8 s, fade wireframe and edge opacity with distance, or raise line width plus temporal supersampling on edges under 1 px.
5. **Lift the gate-3, 4 and 5 labels above their crossbars** with the same roof-line rule as gate 1. Hide BLOCK 0 by 1.0 s, or anchor it to the slab under the readout's look point.
6. **Keep 2140 in one place.** At the end, drop "≈ 2140" from either the 3D label (make it "LAST BLOCK · 6,929,999") or the readout.

VERDICT: ONE MORE PASS
