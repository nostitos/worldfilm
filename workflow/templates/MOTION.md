# MOTION.md — __PROJECT_SLUG__

The motion system, set once at stage 0. Numbers, not adjectives. Builders import these as motion-tokens.js; the
camera and the HUD implement the rules below, and tools/sweep.mjs asserts the ones that can be measured per frame.
Every number here also lives in shotspec.json (project.motion_tokens, project.camera, shots[].world_anchors).

## Personality
- Archetype: (calm | precise | urgent | playful | monumental | other)
- Base duration:    ·  entrance ease:    ·  exit ease:    ·  overshoot:    ·  stagger between siblings:
- Reading hold: (e.g. max(1.5 s, chars/15 + 1.5 s))
- Linear motion: (allowed where | avoided; the motion_shape gate warns on it)

## Camera dial: __DIAL__ (1 Locked · 2 Anchored · 3 Motivated · 4 Flowing · 5 Perpetual)
- Set once; it governs the camera only. Elements may keep moving at every setting. A per-shot exception
  (shots[].camera.dial) is named here with its reason.
- 1-2: the camera holds or makes small, deliberate adjustments; rests stay still unless rest drift is configured
  for that dial (rest_drift.min_dial).
- 3: the camera moves when the action motivates it and settles after.
- 4: the camera is usually moving between named poses; settles are brief.
- 5: the camera is always moving.
- Distance and zoom keyed in log space (project.camera.log_space); monotone cubic interpolation unless a pose names an ease.
- Signature moves allowed to repeat:
- Exceptions (shot, dial, reason):

## Rest drift (optional; for moving rests only)
Configure in shotspec.json project.camera.rest_drift, or set its shape to "none" so rests stay still. It applies to
shots whose effective dial is at least min_dial. When it applies, drift on an ellipse so the velocity never passes
through zero (a one-axis sine stops at each turning point, every pi/omega seconds, and the frozen-time gate reads
those instants as frozen):

    lateral  = A(t)  * (L * sin(w * t) + Ls * sin(ws * t + 1))
    vertical = Av(t) * V * cos(w * t)                     height in quadrature with the lateral sway
    A(t)  = 1 + the sine-windowed boost factors active at t
    Av(t) = the same without boosts whose axes are "lateral" (so a framing target can settle in one direction)

Scale L, V, Ls and the rates to this scene: a starting point is L about 0.2-1 % of the camera-to-subject distance,
V at 0.5-1x L, and w giving a period of a few seconds. Tune by eye and by the frozen-time margin. This project:
- min_dial:    L:    V:    w:    Ls:    ws:    boosts (from, to, factor, axes):

## Framing targets
A shot whose composition is a place on screen (e.g. a horizon held at a fixed fraction of the frame) is solved
rather than keyed by hand: name the world point, key its screen position densely (shots[].camera.framing_target),
derive the pose from it, and assert the projected quantity in tools/sweep.mjs (settles in one direction, then holds).

## Labels (film/place_label.js implements the rule; the sweep asserts it)
- A plate sits above its anchor. When that would overlap the object it names and the world supplies side
  candidates (<a>-right / <a>-right-outer / <a>-left / <a>-left-outer from anchors(cam)), it moves beside the object
  instead. Side candidates are optional; provide them only for objects that need them.
- Then: clamped to the safe area, out of the caption zone and any reserved readout box, held at the hold line, and
  pushed up deterministically on collision. Safe margin:    caption zone:    readout box: (or none)
- Hold line: __HOLD_FRAC__ of the frame height (place_label.js default 0.76).
- No plate touches the object it names in any frame it is up (sweep_lib labelsClear). Labels of one family never
  overlap in time.

## Displayed values
- Preserve each source's precision, units, rounding and provenance (facts.json records them).
- Where a value is computed for display, recompute it independently in the sweep every frame with an appropriate
  type: integers (BigInt if large) for discrete units, exact decimals for exact decimal quantities, and a stated
  tolerance for measured values. Display rounding is declared once and applied once.

## Aspect variants (optional; each delivered one is its own film at the gates)
- Variant: __VARIANT__ (compositions/<id>.html) — deliver: yes/no; label hold line:    fov_scale: (optional)
  world options only this variant uses: (keys defined by world.js)
- Adding a variant option must leave the primary render unchanged (frame_hash on a primary draft proves it).
- A delivered variant is rendered, muxed and gated on its own and has its own PROGRESS.md row.

## Safe areas and composition
- Margins per size:    caption zone:    subject fill range:
- Layout repetition rule:

## Transitions
- Allowed transitions:    hard-cut times (also project.gates.hard_cuts_s, so the shutter never crosses them):
- Object carries across cuts (handoffs), if any:

## Sound locks (when the film has sound)
- Which events carry cues; motion cues on camera velocity peaks; cue density limits:
- Silence windows, if any (shotspec.json audio.silence is the one source; synth_sfx.py carves them as exact zeros):
- Music-only export, if any: the score stem mastered on its own (synth_sfx.py --master-stem via audio.music_only)
