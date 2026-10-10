# Critic round 2 (verification): "Block Space", draft 7

## 1. Previous top changes and signature moments

| # | Change | Status | Proof |
|---|---|---|---|
| 1 | First-halving move | **PARTLY** | The camera is above the roofs and eases from 5.2 to 6.9 s (t6.9). The cut is still there, at 7.00 s in cut-s02, just after the gate is passed. The tall slabs nearest the camera are 50-era and fill the left and right thirds, so perspective makes them look 3–4× taller than the 25-era slabs past the gate. A viewer can't read "half". There is also no audio cue on the gate: audible.json has no halving cue, so the requested kick on that frame never landed. |
| 2 | NOW is a real stop | **FIXED** | The camera holds from 17.4 to 19.2 s, the readout and the label both say 970,440 (t18.3), and the arrive-now cue lands at 17.40 with a 28.7 dB lift. |
| 3 | The street ends | **FIXED** | At t24.5 and t26.5 the ground is clipped at the gate and there is void beyond it, seen from a pitched view. |
| 4 | Colour | **FIXED** | The gates measure about #F39317. Faces and sky are neutral. 21,000,000 is orange and NEVER MORE is ink. |
| 5 | Luma | **FIXED** | The lowest 0.5 s window is 42.4 (at 24.08 s), with 0 dark seconds. |
| 6 | One label at a time, two fields, 30 px | **PARTLY** | The text is 30 px. Two labels share the screen twice: HALVING 3 and HALVING 4 at t12.9, and NOW and HALVING 5 overlapping from 19.4 to 19.8 s. HALVING 5 has three fields ("· 2028 ·"). |
| 7 | Timing | **PARTLY** | s02 no longer drags. But 22.8–24.3 s is about 1.5 s of frame that is 70% black with a grey sliver (cut-s07). It is the new dead stretch. |
| 8 | End card | **PARTLY** | The s08 caption is gone and the exact sum is there. But the headline sits on top of the end-gate geometry: the orange bar and its post run through "0,000" (t28.8). The exact figure is about 14 px mid-grey with no unit, which will be illegible on a phone. |

**Signature moments**
1. **First gate steps the street down to half: PARTLY.** The gate and the slow-down are there. The halving is not visible (see change 1).
2. **Camera stops at NOW: FIXED.** It is the best beat in the film.
3. **Crane up to a hairline that ends: PARTLY.** The hairline from 20.4 to 22.6 s works, and the end is real. Between them, 22.8–24.3 s is a dark void with the end not yet in view, so "thins to a hairline" and "ends" don't connect into one move.

## 2. Regressions

- **The readout runs ahead of the picture.** At t12.9 it shows 6.25 BTC at block 635,450 while the HALVING 3 gate is still ahead of the camera. The same happens at t6.9 (25 BTC before the gate) and t15.4 (3.125 BTC before the HALVING 4 gate). On screen, the subsidy halves before the gate, which contradicts the gate.
- **The readout counts backwards at the end.** It reads 6,929,999 at 22.95 s, before the end is even visible, and 6,929,214 at t26.5 while the label says 6,929,999. This is the client's "a number on screen is wrong" trigger.
- **Stale genesis label.** At t2.5 "BLOCK 0 · 50 BTC" is pinned to a slab in the foreground while the readout says 94,686.
- **Headline collision** with the end-gate geometry at t28.8 (see change 8).
- **The 28.4–29.8 s push is barely visible** on the contact sheet. It is close to static again.

## 3. Sound-off comprehension

A mute viewer now understands:
- one building per period, with height equal to the new coins;
- each orange gate is a halving, and the label says so;
- "you are here", which is clear and lands;
- after NOW, the future is drawn in wireframe and fades to nothing;
- there is a last coin around 2140, and the cap is 21 million.

They still get "height halves at each gate" from the labels, not from the picture. The readout changing before the gate actively confuses that.

## 4. Remaining problems, ranked

1. **Tie the readout to the gate crossing, not the look target.** Compute the block from the camera's z (or the gate plane), so the subsidy changes on the frame the camera passes each gate. At the end, clamp the block to be non-decreasing and to stop at 6,929,999. Fade the readout out at 27.4 s, under the headline.
2. **Make the halving visible at gate 1.** During the 5.8–6.9 s near-stop, yaw the camera about 60° so the gate is seen in profile, with the last 50 slab and the first 25 slab side by side at equal distance. Add an orange 1 px tick at the 50 height and at the 25 height. Put a low "step" cue (+6 dB) on the gate frame. Move the 7.00 s cut to after the profile hold.
3. **Enforce one label at a time in code.** Before a label fades in, require the previous one to be at opacity 0. Hide HALVING 4 until HALVING 3 has left, and hold HALVING 5 until 19.9 s. Drop "2028" from HALVING 5 (two fields).
4. **Remove the 22.8–24.3 s void.** Keep the s07 crane continuous into s08 and start the pitched end view by 23.0 s, so the end gate is in frame within 0.3 s of the cut. Alternatively, cut 1.0 s and give it to the end card.
5. **End-card layout.** Raise 21,000,000 by about 120 px, or fade the end gate's geometry out by 27.4 s, so nothing crosses the glyphs. Set the exact line to 22 px ink at 80% opacity: "20,999,999.9769 BTC by the schedule".
6. **Genesis label:** fade "BLOCK 0" out by 1.8 s, or keep it attached to the genesis slab and cull it when that slab leaves the frame.

VERDICT: ONE MORE PASS
