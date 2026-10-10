# MOTION.md — Block Space

## Personality archetype
- Archetype: monumental
- Base duration 0.5 s · entrance ease expo.out · exit ease expo.in (half the entrance time) · overshoot 0
- Label fades 0.3 s; captions hold max(1.5 s, chars/15 + 1.5 s) (read_time gate)
- No linear motion: the camera is a monotone cubic through its poses (motion_shape gate warns on constant speed)

## Camera dial: 4 (Flowing)
- The camera is in motion in every frame; consecutive shots share their boundary pose so momentum is handed on (C1)
- Height and look-ahead distance are keyed in log space; x and lateral offset in linear space
- Rests (NOW, the end) carry micro-drift on an ellipse: 0.05 units lateral, 0.04 vertical in quadrature at 1.7 rad/s
  (plus a slow 0.61 rad/s lateral component), so the drift's velocity never passes through zero; x4 at the NOW stop,
  the ending's x10 sway is lateral only so the end edge settles in one direction
- The portrait cut dissolves each portal over the last 14 units of the approach and holds anchored labels at 60 % of
  the frame; the 16:9 picture does neither (its frames are unchanged by the portrait code path)
- Signature moves that may repeat: dolly, crane. Everything else varies: the first move is a crane-down, the present is
  a settle with drift, the future is a crane-race, the end is an overhead drift
- Focus discipline: labels are projected from world anchors at a fixed screen size and clamped to the safe area;
  colliding labels are pushed up deterministically (film/main.js)
- Velocity peaks (whoosh and blur cues): 1.3 s, 22.4 s, 24.3 s

## Safe areas and composition
- 1920x1080: 96 px margins; captions in the lower zone at y >= 940; labels never below y = 820
- 1080x1920: 64 px margins; captions above the lower 300 px; labels never below y = 1500
- Subject fill 0.6-0.85; layouts: wide, close x4 (the street), wide (NOW), overhead x2, full-frame type

## Transitions
- No hard cuts: every shot boundary is a camera phrase (type "continuous"); the one declared carry (s08 -> s09)
  measures 0.00 at the boundary because the world keeps drifting under the final card
- The shutter never crosses a cut (none here); the master is captured with a 180 degree shutter, 4 samples

## Sound locks
- Kicks on the four halvings (7.5, 11.0, 14.0, 16.5 s); accelerating ticks for the 28 scheduled halvings
- Whooshes on the three velocity peaks; a blip when the camera settles at NOW
- Silence 25.5-27.5 s; the loudest moment at 27.5 s (impact + sub + chime) on 21,000,000
