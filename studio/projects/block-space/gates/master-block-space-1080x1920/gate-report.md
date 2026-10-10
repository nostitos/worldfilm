# Gate report — Block Space

- generated: 2026-10-10T01:46:13+00:00 by run_gates.py 0.1.0
- video: `studio/projects/block-space/renders/block-space-1080x1920.mp4` (sha256 6e67e34f9730b27a…, 1080x1920 @ 60.000 fps, 30.00s, audio: yes)
- spec: `studio/projects/block-space/shotspec.json` (sha256 6aa73ca1b4037d38…)
- ffmpeg: ffmpeg version 8.0.1 Copyright (c) 2000-2025 the FFmpeg developers
- out dir: `studio/projects/block-space/gates/master-block-space-1080x1920`
- summary: **PASS** — 8 PASS, 0 FAIL, 0 WARN, 2 SKIP (exit code 0)

| gate | status | measured | threshold | evidence |
|---|---|---|---|---|
| frozen_time | PASS | hold 0.10s; 0.11s/30s (0.1s of 27.0s) | hold <= 0.3s; <= 1.0s/30s | `frame-diff.csv` |
| loudness | PASS | I -14.0 LUFS; TP -2.5 dBTP; LRA 7.2 LU | -14 +-1.5 LUFS; TP <= -1 dBTP | `loudness.csv` |
| handoff | SKIP | - | mean |RGB diff| <= 6 | - |
| facts | PASS | 0 unmatched of 18 tokens; 0 texts without fact_ids | 0 unmatched; digit text needs fact_ids | - |
| beats | PASS | worst 0.00 frames over 8 cuts | <= 2 frames (0.0333s) | - |
| swatch | SKIP | - | RGB distance <= 40 | - |
| read_time | PASS | 0 failed, 0 without min_hold_s, of 14 texts | max(1.5, cjk/4.5 + other/15.0 + 1.5)s | - |
| motion_shape | PASS | 0 of 9 shots look constant-speed | WARN if CV < 0.15 and mean > 1.0 | `motion-s01.csv`, `motion-s02.csv`, `motion-s03.csv`, `motion-s04.csv` … |
| contrast | PASS | 0 contrast, 0 overlap, 0 clipped | WCAG AA (spec contrast_min 4.5); 0 overlap/clipped errors | `hyperframes-check.json` |
| contact_sheet | PASS | 150 frames, 1 sheet(s), 9 cut strips | evidence only | `contact-sheet.jpg`, `cut-s01.jpg`, `cut-s02.jpg`, `cut-s03.jpg` … |

## Details

- **frozen_time** (PASS): 1 near-frozen samples of 270 in the first 27.0s (YAVG < 0.35) = 0.1s, normalised 0.11s per 30s; longest still stretch 0.1s at 26.6-26.7s; final 3.0s excluded as the CTA end card (2.7s frozen there). stretches: 26.6-26.7s (0.1s)
- **loudness** (PASS): integrated -14.0 LUFS (target -14 +-1.5), true peak -2.5 dBTP LRA 7.2 LU.
- **handoff** (SKIP): no shot declares a carry object
- **facts** (PASS): 18 numeric tokens all trace to facts.json values (173 values; 0 tokens from the composition)
- **beats** (PASS): s01 beat 6: 0.00 frames (PASS); s02 beat 14: 0.00 frames (PASS); s03 beat 20: 0.00 frames (PASS); s04 beat 26: 0.00 frames (PASS); s05 beat 31: 0.00 frames (PASS); s06 beat 39: 0.00 frames (PASS); s07 beat 46: 0.00 frames (PASS); s08 beat 54: 0.00 frames (PASS)
- **swatch** (SKIP): no shot declares swatch_points
- **read_time** (PASS): s01/C1: 62 chars need 5.63s, min_hold 6.2, on screen 6.20s (PASS); s02/L-h1: 14 chars need 2.43s, min_hold 3.3, on screen 3.30s (PASS); s03/L-h2: 16 chars need 2.57s, min_hold 2.9, on screen 2.90s (PASS); s04/L-h3: 16 chars need 2.57s, min_hold 2.9, on screen 2.90s (PASS); s05/L-h4: 17 chars need 2.63s, min_hold 2.65, on screen 2.65s (PASS); s06/L-now: 24 chars need 3.10s, min_hold 3.5, on screen 3.50s (PASS); s06/C2: 27 chars need 3.30s, min_hold 3.3, on screen 3.30s (PASS); s07/C3: 26 chars need 3.23s, min_hold 3.6, on screen 3.60s (PASS); s07/L-h5: 18 chars need 2.70s, min_hold 3.0, on screen 3.00s (PASS); s08/C4: 15 chars need 2.50s, min_hold 2.85, on screen 2.85s (PASS); s08/L-last: 19 chars need 2.77s, min_hold 3.1, on screen 3.10s (PASS); s09/H-cap: 10 chars need 2.17s, min_hold 3.0, on screen 3.00s (PASS); s09/K-cap: 10 chars need 2.17s, min_hold 2.7, on screen 2.70s (PASS); s09/X-cap: 18 chars need 2.70s, min_hold 2.9, on screen 2.90s (PASS). Static check on the spec; the live readcheck.mjs sweep (window.TEXTS) still applies to the rendered page.
- **motion_shape** (PASS): s01: mean 7.34 cv 0.20 (PASS); s02: mean 7.39 cv 0.54 (PASS); s03: mean 9.02 cv 0.29 (PASS); s04: mean 6.85 cv 0.21 (PASS); s05: mean 4.58 cv 0.23 (PASS); s06: mean 2.71 cv 0.83 (PASS); s07: mean 3.33 cv 1.03 (PASS); s08: mean 1.04 cv 0.37 (PASS); s09: mean 0.14 cv 1.66 (PASS). Experimental: a frame-difference series is a proxy for speed, so static shots with a tiny moving element or constant-speed camera moves can both trigger it; judge with the contact sheet.
- **contrast** (PASS): contrast 23/23 text checks pass WCAG AA at 5 samples; 0 contrast, 0 overlap, 0 clipped-text findings (0 errors, 0 warnings); lint errors 0, runtime errors 0, other layout findings 0
- **contact_sheet** (PASS): 150 frames every 0.2s on 1 sheet(s) (8 columns, 320x568 tiles, timestamps burned in); 9 dense strips of +-0.5s at 20 fps around each transition_out (orange border = first frame at/after the cut)

## Spec vs render notes

- spec sizes[0] 1920x1080 but the video is 1080x1920 (pixel coordinates were scaled)

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
- Gate 'handoff' was skipped (no shot declares a carry object); cover it by hand or supply the missing input.
- Gate 'swatch' was skipped (no shot declares swatch_points); cover it by hand or supply the missing input.
