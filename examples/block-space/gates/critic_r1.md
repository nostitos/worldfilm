# Critic round 1: "Block Space", draft 4

## 1. Per shot

**s01 (0–3 s).** The genesis canyon seen from above, with the camera diving in. About 45% of the frame is empty grey ground. It can't lose any time.
- Frame 0 is a finished composition, which is good.
- At 1.5 s the caption (two lines, uppercase serif) runs across the slab edges, so the text has no clear ground behind it.

**s02 (3–7.5 s).** Inside the 50-coin canyon, with walls filling the frame. About 20% empty. It could lose **1.5 s**.
- From 3.2 to 6.4 s the frames on the contact sheet are almost identical. The camera moves, but the walls repeat, so it reads as standing still. This is the biggest waste in the film.
- At 7.0–7.4 s the HALVING 2 label is already on screen while HALVING 1 is still approaching, so two labels are stacked.

**s03 (7.5–11 s).** The street at 25. About 25% empty. It could lose 0.5 s.
- At 11.0 s HALVING 2 and HALVING 3 labels are on screen together again.
- The slab outlines cut through the top-right readout ("SUBSIDY").

**s04 (11–14 s).** 12.5. About 35% empty. It could lose 1.0 s. It is visually the same as s05 apart from the slab height, and the beat repeats.

**s05 (14–16.5 s).** 6.25. About 45% empty, mostly sky. It can't lose time.

**s06 (16.5–19.5 s).** NOW. About 40% empty. It can't lose time, but it needs restructuring.
- The camera never stops. The gate keeps growing from 17.6 to 19.8 s and the camera passes through it at 20.0 s.
- The readout shows block 949,536 while the label says 970,440, so the camera stops short of NOW and never reaches it.

**s07 (19.5–23.5 s).** The crane up over the future. 80–95% empty. It could lose **0.8 s**.
- At 22.8–23.4 s the frame is nearly blank.
- At 21.0 s the caption "20,095,128 coins issued so far" is still on screen while the readout says SCHEDULED ≈ 2029, so the caption is out of sync with the readout.

**s08 (23.5–27.5 s).** Overhead view of the end. About 85% empty.
- **The grey street continues past the BLOCK 6,929,999 marker to the top of the frame** (t26.5). The street does not end.
- At t24.5 a faint ghost label sits under the caption around x 860–975.
- The caption runs into the wireframe boxes (t24.5, t26.5).

**s09 (27.5–30 s).** 21,000,000. About 75% empty.
- Frames from 27.6 s to the end are almost identical (the gate report shows 1.3 s frozen at the end). That breaks dial 4.
- The s08 caption stays on screen under the headline, and a box outline runs through "6,929,999".

## 2. Legibility at phone size

All sizes are cap heights from the native 1920-wide stills; "phone" assumes a frame about 390 px wide (×0.2).

| element | cap height (native) | on a phone | verdict |
|---|---|---|---|
| Readout labels (BLOCK / SUBSIDY / MINED) | ≈8 px, faint, letter-spaced | ≈1.6 px | invisible |
| Readout values | ≈17 px | ≈3.5 px | barely legible |
| Gate labels | ≈16 px, 33–39 characters, moving | ≈3.3 px | unreadable at that length |
| Captions | ≈30 px | ≈6 px | the minimum acceptable |
| "NEVER MORE." | ≈17 px, letter-spaced orange | ≈3.5 px | too small for the payoff line |

- Gate labels are the worst problem: four fields at once while they move, and they arrive two at a time.
- The read_time gate passed on paper, but stacked labels halve the effective reading time.

## 3. Signature moments

1. **First halving stepping the street down to half: it fails.** The camera is inside a canyon whose walls are taller than the frame, and a cut at 7.5 s hides the step itself. No single frame shows a 50-tall slab next to a 25-tall slab.
2. **Camera stopping at NOW: it fails.** The camera creeps toward the gate, never settles and never reaches it, then flies through it.
3. **Crane up as the schedule thins to a hairline that ends: half.** The hairline at 21–22.6 s is good. Then the camera goes overhead, where height can't be seen at all, so "thinning" disappears. The end isn't drawn either, because the street keeps going.

**With the sound off,** a viewer understands: buildings, numbers counting up, "issued so far", "28 more halvings", 21,000,000. They would not see that height halves at each gate, or where "now" is. The captions carry the meaning, not the pictures.

## 4. Honesty and colour

- **The gates render yellow** (about #F5C24A), not #F7931A. It is probably tone mapping. As rendered, this breaks the one-orange rule.
- **Navy/blue side faces on the concrete** (t7.4, t11.0, t16.4) and a blue-tinted sky are colours outside the palette.
- **Orange is on the wrong things.** "NEVER MORE." and the last-block label text are orange, while the number (21,000,000) is ink. The brief says orange goes on gates and the number. The orange rule on every label also stretches that rule.
- **"28 more halvings" is open to challenge.** Halvings 5 to 32 is 28, but the 33rd (at block 6,930,000, where the subsidy goes to zero) is also a halving in the code. Change the wording to "28 more halvings still pay out", or count 29.
- **21,000,000 is a rounded figure.** The schedule actually issues 20,999,999.9769 BTC. "Never more" stays true, but add a small Plex line under it with the exact figure, as the house film would.
- **Luma is not measured by any gate.** From 23 s to the end the background is about #1C1C1E, roughly luma 28, which looks below the client's floor of 35. The sky in s02–s07 is about luma 19 over 30–50% of the frame. This is the "black tunnel on a phone" the client said they would be unhappy with.
- **The digital silence at 25.5–27.5 s is not verified** by the gate report.

## 5. Camera

- **s02–s04:** constant forward speed down a repeating corridor. It reads as drifting with an "AI camera" feel: no settle and no reason for the speed.
- **The cut at 7.5 s** jumps height and angle rather than handing momentum over to the next shot.
- **s06** never stops, though stopping there is the whole point of the beat.
- **s09** goes fully static, which breaks dial 4.
- **The best move** is the dive in s01 and the pull into the hairline at 20.4–22.6 s.

## 6. Top changes, ranked by impact

1. **Rebuild the first-halving move.** Raise the camera to about 0.8× the 50-coin slab height by 6 s. Remove the 7.5 s cut and pass the gate in one continuous shot. Ease to near-stop (about 0.6 s) with the H1 gate in profile so the 50 and 25 tops share the frame. Put the kick on that frame.
2. **Make NOW a real stop.** The camera reaches block 970,440, so the readout equals the label. Decelerate with an ease-out to about 3% speed and hold for 1.2 s with micro-drift only. Then the crane departs.
3. **End the street.** Clip the ground mesh and the street strip at the z of block 6,929,999. Keep the camera at a 35–45° pitch instead of straight overhead, so the hairline height stays visible and the void beyond the end reads.
4. **Fix the colour.** Use a linear or no-tone-mapping (unlit) material for the gates so the output measures #F7931A ±10. Remove the blue component from the concrete side faces and the sky (neutral #1B1F26 / #0B0D10). Make 21,000,000 the orange element and put "NEVER MORE." in ink.
5. **Lift luma and measure it.** Raise the ground and fog to keep the mean above 40 in every frame. Add a per-frame YAVG ≥ 35 gate. s08–s09 is the most at risk.
6. **One label at a time.** Show the next gate's label only after the previous one has left. Cut each label to two fields ("HALVING 1 · 25 BTC") and raise the gate labels to 30 px font. Raise the readout labels to 14 px at full ink and the values to 26 px.
7. **Tighten the timing.** Take 1.5 s from s02, 1 s from s04 and 0.8 s from s07. Spend it on the NOW hold and a 0.5 s profile hold on H1.
8. **Clean the end card.** Fade the s08 caption out before 27.5 s and remove the ghost label. Add a slow push (about 2%) through s09. Add "20,999,999.9769 BTC, by the schedule" in Plex under the headline, and change the halving count wording.

VERDICT: ONE MORE PASS
