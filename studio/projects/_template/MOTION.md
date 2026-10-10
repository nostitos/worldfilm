# MOTION.md — __PROJECT_SLUG__

The motion system, set once at stage 0. Numbers, not adjectives. Builders import these as motion-tokens.js; the
camera and the HUD implement the rules below and tools/sweep.mjs asserts them every frame.

## Personality archetype
- Archetype: (calm | precise | urgent | playful | monumental)
- Base duration: 0.5 s  ·  entrance ease: expo.out  ·  exit ease: expo.in (exits take half the entrance time)
- Overshoot: 0  ·  stagger between siblings: 0.09 s  ·  reading hold: max(1.5 s, chars/15 + 1.5 s)
- No linear motion anywhere (motion_shape gate warns)

## Camera dial: __DIAL__ (1 Locked · 2 Anchored · 3 Motivated · 4 Flowing · 5 Perpetual)
- Set once; it governs the camera only. Elements keep moving at every setting (zero-static law). A per-shot
  exception (shots[].camera.dial) is named here with its reason, or it does not exist.
- Dial 3: the camera moves when the action motivates it (push on a reveal, settle after) and rests with micro-drift.
- Dial 4: the camera is usually in motion between named poses; brief settles decay into residual drift; momentum hands shot to shot.
- Dial 5: no frame where the camera is still; every move pairs zoom with at least one rotation axis.
- Pose keys live in log space for distance/zoom; interpolation is a monotone cubic (no overshoot) unless a pose names an ease.
- Signature moves (allowed to repeat): 
- Every other move varies scene to scene (no copy-pasted camera).
- Focus discipline: the focal plane sits on the words; shutter blur only where velocity peaks.

## Rest drift (the rule, with the formula)
Every rest drifts on an ELLIPSE so the camera's velocity never passes through zero (a one-axis sine is still at
every turning point, every pi/omega seconds, and the frozen_time gate reads those instants as frozen):

    dz = A * (L * sin(w * t) + Ls * sin(ws * t + 1))      lateral
    dy = As * V * cos(w * t)                              height, in quadrature with the lateral sway
    L = 0.05  V = 0.04  w = 1.7 rad/s  Ls = 0.03  ws = 0.61 rad/s   (world units; scale to the world)
    A = 1 + sum of sine-windowed boosts (x4 at a designed stop); As = the same without the boosts whose axes are
    "lateral" (an ending that must settle a framing target in one direction keeps its big sway lateral only)

Written in shotspec.json project.camera.rest_drift; the values here and there are the same numbers.

## Framing targets
A shot whose composition is a place on screen (the horizon in the top fifth, the edge of a plane at 4.5 %) is not
keyed by hand: name the world point, key its screen position every 0.1 s (shots[].camera.framing_target), derive
the pose from it, and assert the projected quantity in tools/sweep.mjs (settles in one direction, then holds).

## Labels (the placement rule; film/main.js implements it, the sweep asserts it)
- A plate sits ABOVE its anchor. If that puts it on the object (a gate's top bar), it moves BESIDE the right post,
  past the post's outer face, with a leader to the bar's end. If that side belongs to the corner readout, beside the
  LEFT post. Then: clamped to the safe area; never over the corner readout; never in the caption zone; a later label
  that collides is pushed up (deterministic). The world's anchors(cam) returns <a>-right, <a>-right-outer, <a>-left,
  <a>-left-outer for every anchor that names an object with posts.
- Hold line: a plate stops following its anchor below __HOLD_FRAC__ of the frame height (16:9: 0.76) and holds, so
  it never races a passing object out of the frame (that reads as a one-frame pop).
- No plate touches the object it names, any frame it is up (sweep_lib labelsClear). Labels of one family never
  overlap in time.
- Money is integers: every number on screen is computed in the unit the source uses and recomputed independently
  (BigInt, a different formula) in the sweep every frame; the facts gate alone cannot see a rounding that facts.json shares.

## Aspect variants (each one is its own film at the gates)
- Variant: __VARIANT__ (compositions/<id>.html): fov_scale __FOV_SCALE__ (tan(fov/2) multiplier), label hold line
  __VARIANT_HOLD_FRAC__ (portrait: 0.60), world options only this variant turns on (e.g. portalFade: objects the
  camera passes through dissolve over the last N units of the approach, because a wider vertical field keeps near
  geometry on screen until the camera is over it).
- The 16:9 code path stays byte-identical when a variant option is added (frame_hash on the 16:9 draft proves it).
- The variant is rendered, muxed and gated on its own (pops, luma, run_gates + check_gate_report) and has its own
  PROGRESS.md row. It never inherits the 16:9 pass.

## Safe areas and composition
- 1920x1080: 96 px margins; captions inside the lower 20 %; nothing touches the edge at 1080x1920 except full-bleed worlds
- Subject fill 0.6-0.85 of the frame; one layout never repeats in consecutive shots

## Transitions
- Morph carry: one object survives every cut at exact pixels (handoffs.json); cross-fades are banned
- Hard cuts only on beats; the shutter never crosses a cut (capture_subframes.mjs --cuts)

## Sound locks
- Every whoosh sits on a camera velocity peak; every click on a real on-screen action; one riser, one impact per film
- The silence window precedes the loudest moment; the loudest moment follows the silence; the window is exact zeros
  in every output (audio/cues.json, shotspec.json audio.silence, build.sh SILENCE are the same numbers)
- The music-only export is the score stem mastered on its own (synth_sfx.py --master-stem): a stem carries the mix's gain

