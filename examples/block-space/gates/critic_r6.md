I've read all the evidence. The report follows.

# Critic round 6 (verification): "Block Space", draft 14

## 1. Previous top changes and signature moments

| # | Change | Status | Proof |
|---|---|---|---|
| 1 | End framing | **FIXED, with a wobble** | At t23.5 the ground edge is at y≈225 (21 %). At t26.5 it is at y≈227 (21 %). The black sky band is gone. But the camera doesn't settle: at t24.5 the edge has dropped to y≈300 (28 %), then it climbs back. The claimed 18 % is not what the frames show. |
| 2 | Hairline that ends | **PARTLY** | The road now ends at NOW, and t20.8 is bare ground with two converging rows: good. From 23.0 s, though, the "hairline" is two loose columns of ink dashes of random length. They spread apart toward the camera and are offset from each other (t24.5, t26.5). It reads as scattered tick marks on a grey field, not one line thinning to a point. About 75 % of the frame is empty concrete. |
| 3 | Gate 1 as a gate | **FIXED, barely** | At t6.6 the left post, the top bar and the right post all separate, with about a 70 px gap at the top. It reads as a narrow upside-down U. The lower posts are still partly hidden by the slabs in front. |
| 4 | Shimmer | **STILL** (in this file) | pops.json: WARN, 23 shimmer frames (3.85–4.32 s, 10.12 s, 14.98 s). No measurement of the delivered master was supplied. "Checked at delivery" is a promise, not evidence. |
| 5 | Label collisions | **PARTLY** | LAST BLOCK is fixed. At t24.5 the plate bottom is at y 242 and the bracket starts at y 280. At t26.5 the plate bottom is at 155 and the bracket at 195. **Gate 3 still collides:** at t11.4 the "HALVING 3 · 6.25 BTC" plate (y 72–122) sits on the gate frame (x 945–1040, y 48–125), with orange showing above and below it. Third round running. |
| 6 | Open checks | **PARTLY** | The years are fixed: at t23.5 the readout says ≈ 2139 with no caption on screen, and by t24.5 it says ≈ 2140 under "THE LAST NEW COIN." sub-h4 is now timed by onset (15.505 s against a 15.52 s cue): accepted. Shimmer: see #4. |
| — | Hero number clear | **FIXED** | At t28.8 the rungs are faded to 20 %, only faint traces near y 330 / 410 / 515 under the "2". The bracket is fully inside the frame (y 155–200), about 130 px above the number, and not tangent to the edge. |

**Signature moments**
1. **The first gate halves the street: FIXED.** It is now a portal, and the 50-coin to 25-coin step reads at t5.8 and t6.6. kick-h1 lands at 7.001 s with a 15 dB lift.
2. **The camera stops at NOW: FIXED.** t18.3 is unchanged and still the best frame. arrive-now lands at 17.40 s with a 28.7 dB lift.
3. **Crane up to a hairline that ends: PARTLY.** The crane and convergence at 20.0–22.4 s work. After the cut at 23.0 s the line breaks into dashes, and the "end" is a small bracket sitting on a horizon.

## 2. Regressions

- **A new empty stretch at 22.85–23.10 s** (cut-s07). The frame is wall-to-wall flat grey: no horizon, no end marker, no landmark, only faint rungs and a fading caption. About 0.3 s of nothing, right before the payoff.
- **The edge drifts after "settling".** It goes 21 % (23.5 s), then 28 % (24.5 s), then 21 % (25+ s). The camera moves away from the frame it promised and comes back, which reads as hunting.
- **The riser's audibility number is meaningless.** `bed_db: null` gives `lift_db: Infinity`. The measured peak is 24.70 s against a 24.95 s cue, 0.25 s early. The gate only flags cues that are late, so this passes.

**Passes:**
- No wrong number. I checked the readouts at t9.9, t11.4, t12.9, t15.4, t18.3, t23.5 and t26.5, and the 20,999,999.9769 total.
- No orange outside the gates, the end marker and the number.
- Luma floor is 51.9 at 21.38 s.
- The silence from 25 to 27 s is clean.
- The longest frozen hold outside the end card is 0.2 s.
- The tone is serious, with no jokes.

## 3. Sound-off comprehension

A mute viewer gets:
- one building per 2,016 blocks, with height equal to the new coins;
- the street steps down at each orange gate, and the readout halves 25 → 12.5 → 6.25 → 3.125;
- you are at block 970,440 in Oct 2026, with 20,095,128 issued;
- the future is wireframe, and 28 halvings remain;
- the last block is 6,929,999, around 2140;
- 21,000,000, never more, exactly 20,999,999.9769 BTC.

What they miss: the end of the schedule reads as a sparse dashed pattern on an empty plane, not a line running out. At 11.4 s the gate 3 label hides the gate it names.

## 4. Remaining problems, ranked

1. **Gate 3 label collision (about 9.9–11.6 s).** Every frame, compute the gate's top-bar y on screen and clamp the plate bottom to at most that y minus 24 px. If it hits the safe-area top, flip the plate below the bar, or put it beside the right post.
2. **Make the end hairline one line.** From 23.0 s, draw the future schedule as rungs centred on the street axis. Their length should scale with subsidy (so they shrink toward the end), their spacing should be even, and there should be no random length jitter. Or collapse the two rows into one centreline ending at the bracket. That way the eye follows a single thinning line.
3. **Kill the dead frames at 22.85–23.10 s.** Keep the end marker or the horizon on screen through the cut: start the look-down 0.3 s earlier, or keep the rows at the 22.6 s brightness.
4. **Settle the ground edge without moving away.** Ease the look-point path so the edge moves in one direction to 20 % and stays there. The bump to 28 % at 24.5 s has to go.
5. **Prove the shimmer is gone.** Run pops.json on the delivered master. If it still fails, fade line opacity by projected line width over 3.8–4.4 s, or enable MSAA or supersampling for the slab edges.
6. **Fix the audibility gate.** Measure the riser's bed from the score stem, not as null. Flag cues that arrive early as well as late (the riser is 0.25 s early).

VERDICT: ONE MORE PASS
