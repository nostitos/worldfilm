# BRIEF — __PROJECT_SLUG__

Fill every line; "unknown" is allowed and the director decides. Read first by the worldfilm director (stage 0).

## The film
- Format: length, primary size, fps (written to shotspec.json project.duration / sizes[0] / fps)
- Extra sizes: none | list them — each delivered size is its own film at the gates (own render, own pops / luma /
  run_gates, own PROGRESS.md row); say which moments must survive the reframe
- Deadline and what "done" means (which of master, poster, SRT, music-only version are delivered)

## The world
- What is simulated or filmed, and at what scale (world units)
- What stays constant and what changes over the film
- Data: files in data/, with the source, unit, precision and rounding of every value (into facts.json; nothing else
  reaches the screen)
- Footage: file in footage/, what the subject is, what may sit behind the subject

## The camera (set once; a branding decision)
- Camera dial 1-5: 1 Locked, 2 Anchored, 3 Motivated, 4 Flowing, 5 Perpetual
- Signature moves allowed to repeat
- Rests: still, or drifting (rest drift, see MOTION.md)
- Framing targets (what must sit where on screen at a given moment), if any

## Look
- Motion personality in one word, and the materials of the world
- References: videos or stills in references/ (measured, never copied); which one is the benchmark
- Palette / type if they exist (hex, font files); otherwise derived from the measured reference

## Sound
- Route: synthesized (audio.cue_sheet) | supplied track (project.music.src, with rights) | none
- Voiceover: none | lines in narration.txt
- Silence windows, music-only export: only if wanted
- Who reviews the sound before it ships (the gates measure; they do not listen)

## Facts and rights
- facts.json holds every number, name, date and claim that may appear on screen, with its source
- Image/footage rights; generated imagery is allowed only as a labelled concept layer

## Must / must not
- Moments the viewer should remember
- Must-nots
- What would be most costly to get wrong
