# Block Space — a worldfilm prototype

Thirty seconds, 1920x1080 at 60 fps (and a 1080x1920 cut): the Bitcoin issuance schedule as a night boulevard of
concrete slabs, one per difficulty period, flown through once. Built with the worldfilm skill on top of shotspec-film.

Rebuild: `bash build.sh` (full: Docker masters twice, framemd5 compare, blur master) or `DRAFT=1 bash build.sh`.
Source of truth: tools/build.py -> data/periods.csv, facts.json, shotspec.json, film/data.js. World: world.js.
Camera + HUD + timeline: film/main.js. Sound: audio/make_cues.py -> audio/cues.json -> assets/mix.wav + stems.
Evidence: gates/ (every measured report), GAUNTLET.jsonl (critic rounds), PROGRESS.md (resumable state).

Delivered files (renders/): block-space-1080p60.mp4 (blur master + full mix), block-space-1080p60-music-only.mp4
(blur master + assets/music-only.wav, the score stem mastered on its own), block-space-1080p60-docker.mp4 (the sharp
Docker picture + mix; picture-a/picture-b are frame-identical), block-space-1080x1920.mp4 (portrait, Docker),
poster.png, block-space.srt. Gate reports per delivered file in gates/master-*; the critic ledger in GAUNTLET.jsonl.

Known state (2026-10-09): the shipped 16:9 masters predate the elliptical-drift change in film/camera.js and fail
frozen_time at 1.11 s/30 s on the blur master (limit 1.0; the Docker master reads 1.00, the portrait master 0.11).
`bash build.sh` regenerates the 16:9 masters with the fix. Nobody has listened to the audio; the blur master is a
host Playwright capture (the installed HyperFrames CLI has no motion-blur option). Details: PROGRESS.md.
