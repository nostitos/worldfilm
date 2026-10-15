# Gate report — Block Space

- generated: 2026-10-10T01:04:23+00:00 by run_gates.py 0.1.0
- video: none (static mode; spec declares 1920x1080 @ 60.000 fps, 30.00s)
- spec: `studio/projects/block-space/shotspec.json` (sha256 6aa73ca1b4037d38…)
- ffmpeg: ffmpeg version 8.0.1 Copyright (c) 2000-2025 the FFmpeg developers
- out dir: `studio/projects/block-space/gates/static`
- summary: **PASS** — 3 PASS, 0 FAIL, 0 WARN, 7 SKIP (exit code 0)

| gate | status | measured | threshold | evidence |
|---|---|---|---|---|
| frozen_time | SKIP | - | - | - |
| loudness | SKIP | - | - | - |
| handoff | SKIP | - | - | - |
| facts | PASS | 0 unmatched of 18 tokens; 0 texts without fact_ids | 0 unmatched; digit text needs fact_ids | - |
| beats | PASS | worst 0.00 frames over 8 cuts | <= 2 frames (0.0333s) | - |
| swatch | SKIP | - | - | - |
| read_time | PASS | 0 failed, 0 without min_hold_s, of 14 texts | max(1.5, cjk/4.5 + other/15.0 + 1.5)s | - |
| motion_shape | SKIP | - | - | - |
| contrast | SKIP | - | WCAG AA (spec contrast_min 4.5); 0 overlap/clipped errors | - |
| contact_sheet | SKIP | - | - | - |

## Details

- **frozen_time** (SKIP): static mode: needs a rendered video
- **loudness** (SKIP): static mode: needs a rendered video
- **handoff** (SKIP): static mode: needs a rendered video
- **facts** (PASS): 18 numeric tokens all trace to facts.json values (173 values; 0 tokens from the composition)
- **beats** (PASS): s01 beat 6: 0.00 frames (PASS); s02 beat 14: 0.00 frames (PASS); s03 beat 20: 0.00 frames (PASS); s04 beat 26: 0.00 frames (PASS); s05 beat 31: 0.00 frames (PASS); s06 beat 39: 0.00 frames (PASS); s07 beat 46: 0.00 frames (PASS); s08 beat 54: 0.00 frames (PASS)
- **swatch** (SKIP): static mode: needs a rendered video
- **read_time** (PASS): s01/C1: 62 chars need 5.63s, min_hold 6.2, on screen 6.20s (PASS); s02/L-h1: 14 chars need 2.43s, min_hold 3.3, on screen 3.30s (PASS); s03/L-h2: 16 chars need 2.57s, min_hold 2.9, on screen 2.90s (PASS); s04/L-h3: 16 chars need 2.57s, min_hold 2.9, on screen 2.90s (PASS); s05/L-h4: 17 chars need 2.63s, min_hold 2.65, on screen 2.65s (PASS); s06/L-now: 24 chars need 3.10s, min_hold 3.5, on screen 3.50s (PASS); s06/C2: 27 chars need 3.30s, min_hold 3.3, on screen 3.30s (PASS); s07/C3: 26 chars need 3.23s, min_hold 3.6, on screen 3.60s (PASS); s07/L-h5: 18 chars need 2.70s, min_hold 3.0, on screen 3.00s (PASS); s08/C4: 15 chars need 2.50s, min_hold 2.85, on screen 2.85s (PASS); s08/L-last: 19 chars need 2.77s, min_hold 3.1, on screen 3.10s (PASS); s09/H-cap: 10 chars need 2.17s, min_hold 3.0, on screen 3.00s (PASS); s09/K-cap: 10 chars need 2.17s, min_hold 2.7, on screen 2.70s (PASS); s09/X-cap: 18 chars need 2.70s, min_hold 2.9, on screen 2.90s (PASS). Static check on the spec; the live readcheck.mjs sweep (window.TEXTS) still applies to the rendered page.
- **motion_shape** (SKIP): static mode: needs a rendered video
- **contrast** (SKIP): no --composition-dir given; contrast/overlap/clipped-text need the HTML composition
- **contact_sheet** (SKIP): static mode: needs a rendered video

## Needs a human

- Aesthetics against the references: does it sit beside premium SaaS launch films (launch-film-notes.md benchmark) or read as 'image, then video, then text'?
- Sound-off comprehension: can a first-time viewer, on mute, say what the business does and the one next action by the end?
- Frame 0 is a finished composition; no empty frames, wasted space or lingering beats (per-scene % empty frame and seconds to lose).
- Text collisions mid-transition, equal spacing in lists/rows, aligned left edges across headline, image and supporting rows.
- Transitions keep a carried object or matched direction (handoff only measures pixels inside carry.box, not whether the cut reads).
- Lead subject fills 60-85% of the frame in feature beats (fill_ratio is declared in the spec, not measured).
- Every claim is true or clearly labelled as a concept; the facts gate only traces numbers, not wording or implication.
- Music matches the buyer and brand tone; SFX land on visual events and feel professional (~+4 dB in-band lift is not measured here).
- Brightness and mood: consumer and home-services buyers rejected dark openers unless the brand demands it.
- Taste: the 3 signature moments should be describable without effect names (spec marks 4 shot(s) as signature).
- Gate 'frozen_time' was skipped (static mode: needs a rendered video); cover it by hand or supply the missing input.
- Gate 'loudness' was skipped (static mode: needs a rendered video); cover it by hand or supply the missing input.
- Gate 'handoff' was skipped (static mode: needs a rendered video); cover it by hand or supply the missing input.
- Gate 'swatch' was skipped (static mode: needs a rendered video); cover it by hand or supply the missing input.
- Gate 'motion_shape' was skipped (static mode: needs a rendered video); cover it by hand or supply the missing input.
- Gate 'contrast' was skipped (no --composition-dir given; contrast/overlap/clipped-text need the HTML composition); cover it by hand or supply the missing input.
- Gate 'contact_sheet' was skipped (static mode: needs a rendered video); cover it by hand or supply the missing input.
