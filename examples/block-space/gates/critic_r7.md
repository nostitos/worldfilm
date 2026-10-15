# Critic round 7 (verification): "Block Space", draft 15

## 1. Previous top changes and signature moments

| # | Change | Status | Proof |
|---|---|---|---|
| 1 | Gate 3 label collision | **FIXED, with a weaker link to its gate** | At t11.4 the gate is at x 945–1040, y 48–125, and the "HALVING 3 · 6.25 BTC" plate is at x 1058–1475, y 330–380. They no longer overlap. But the right post the plate is meant to sit beside is hidden behind the slabs, so the plate floats about 200 px below the gate over the right-hand row, and its leader bar points at a slab. At t12.9 the plate sits cleanly above the bar, as it should. |
| 2 | One hairline | **FIXED in structure, weak on a phone** | t20.8 is the best transition yet: the two foreground rows feed into the halving-6 gate, and one bright ladder runs from it to the horizon. From t22.9 to t26.5 there is a single centred dashed column, with no jitter and even spacing. But the rungs are 8–45 px long and about 1 px thick, grey on grey. At phone scale (about ⅓) the far half falls below a pixel. The thinning you see in the end shot is perspective only, because every rung there is already the minimum (1 sat). |
| 3 | Dead frames at the cut | **MOSTLY FIXED** | cut-s07: the bracket is visible at the top edge from 22.85 s on, and the ladder stays present. About 0.1 s is left at 22.70–22.80 s where the horizon runs along the top edge with no marker. |
| 4 | Edge settles in one direction | **STILL** | The claim was 9 % → 16 % → 20 %. The stills show the edge at y 67 (6 %) at t22.9, y 88 (8 %) at t23.5, **y 265 (24.5 %)** at t24.5, then **y 225 (21 %)** at t26.5. It overshoots the target, then climbs back about 40 px. The bump is smaller than draft 14's 75 px, but the edge still reverses. |
| 5 | Shimmer | **STILL** | pops.json is the same as round 6: 23 shimmer frames (3.85–4.32 s, 10.12 s, 14.98 s), measured on draft15.mp4. The blur master's pops report is named in the change list but is not in the evidence. A promise again. |
| 6 | Audibility gate | **FIXED, with one caveat** | The riser is now 15 ms early (24.935 s against 24.95 s) and early cues are now checked. Its `bed_db: -80` is a clamp, so the 67.8 dB lift is a made-up number. The −12.2 dB level is plainly audible, so I accept the cue, not the number. The kicks are all exactly 50 ms late (3 frames), which passes BT.1359. |

**Signature moments**
1. **The first gate halves the street: HOLDS.** At t6.6 the gate is an open orange portal, the readout says block 210,299 · 25 BTC · 2012, and kick-h1 lifts 15 dB.
2. **The camera stops at NOW: HOLDS, with a new defect** (see Regressions). t18.3 shows block 970,440 · 3.125 BTC · OCT 2026, and arrive-now lifts 28.7 dB.
3. **Crane up to a hairline that ends: PARTLY → close.** The crane at 20.0–22.4 s and the single line now read. The ending is undercut by the edge reversal and by rungs too faint for a phone.

## 2. Regressions

- **The NOW plate sits on its gate.** At t18.3 the right post runs x ≈ 1190–1250, y 130–560, and the "NOW · BLOCK 970,440 · OCT 2026" plate starts at x 1212, y 330–380. The plate's leader bar is on the orange post and the plate covers about 40 px of it. This is the new "beside the right post" anchor sitting on the post instead of past it, and it lands on the film's best frame.
- **The stillness thresholds were moved to fit the measurement.** The longest hold went from 0.2 s (draft 14) to 0.6 s (25.4–26.0 s), and the new `hold_max_s` is exactly 0.6. There is also a 0.4 s hold at 21.1–21.5 s, in the middle of the crane, which is a signature moment. The 25.4 s hold sits inside the designed silence and I accept it. The crane hold is not designed.
- The t6.6 readout ("25 BTC", "2012") sits over slab edges at the top right. It is legible but busy. Minor.

**Passes:** no wrong number (I checked t6.6, t9.9, t11.4, t12.9, t18.3, t20.8 at 0.390625 BTC / ≈2038, t22.9, t23.5, t26.5 at 6,929,999 / ≈2140, and 20,999,999.9769). No orange outside the gates, the end marker and the number. Luma floor 51.9. The silence from 25 to 27 s is clean. Serious tone.

## 3. Sound-off comprehension

A mute viewer gets:
- one building per 2,016 blocks, with height equal to the new coins;
- each orange gate halves the street (25 → 12.5 → 6.25 → 3.125);
- NOW is block 970,440 in October 2026, with 20,095,128 issued;
- the future is wireframe, and 28 halvings remain;
- one line runs out to a bracket at block 6,929,999, around 2140;
- 21,000,000, never more, exactly 20,999,999.9769.

On a phone, 23–27 s becomes a near-empty grey field with an orange tick at the top. The line is mostly lost.

## 4. Remaining problems, ranked

1. **Ground edge reverses at 24.5 → 26.5 s.** Sample the projected edge y every frame from 23.0 to 27.0 s and assert it never decreases. Re-key the look point so the 24.0 s and 24.5 s keys sit below 20 %, or solve the camera pitch directly from the target edge-y curve (smoothstep 9 % → 21 %).
2. **NOW plate on the post (t18.3).** Set plate x to at least the post's outer projected x + 24 px, using the bounding box of the post's outer face, not its centreline. Then assert no plate rectangle intersects any projected gate geometry, every frame.
3. **Hairline too faint for a phone.** From 22.6 s, set rung stroke to at least 2 px and ink opacity to at least 0.85. Add a 1–2 px centre spine joining the rungs, so it reads as a line that thins out, not a dotted road marking. Check a 640×360 downscale.
4. **Supply the blur-master pops.json.** Until it exists, shimmer is unproven: 23 frames.
5. **Crane hold at 21.1–21.5 s.** Keep a small ease (at least 3 % speed) through the crane so it doesn't freeze.
6. **Gate 3 plate anchor.** When the right post is occluded, anchor the plate to the top-bar's right end and draw a short leader to it, so the plate visibly belongs to the gate.

VERDICT: ONE MORE PASS
