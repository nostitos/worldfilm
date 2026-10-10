# BRIEF — Block Space

## The film
- Format: 30 s, 1920x1080 at 60 fps (camera work and motion graphics), plus a 1080x1920 vertical cut from the same world
- Deadline / done: master MP4 (full mix), music-only master, poster, SRT, gate report, GAUNTLET ledger, one-command build

## The world
- Simulated: a boulevard of 3,438 concrete slabs, one per 2,016-block difficulty period from block 0 to block 6,929,999 (the last
  block with a subsidy). Height = the block subsidy. The past (482 periods, through the chain tip at retrieval) is solid concrete;
  the scheduled future is wireframe. Halvings are orange gates across the street; NOW is a taller gate; the last block is a marker.
- The one constant: the rule (50 coins, halved every 210,000 blocks). The one variable: how much is left to issue.
- Data: data/schedule.csv (heights, subsidies, header-time years, coins issued) retained from the "21,000,000" project and
  re-derived here in integer satoshi arithmetic (tools/build.py); sources in references/sources/ (Bitcoin Core commit
  db0bde16, Blockstream block header times). Every number on screen is in facts.json.
- Footage: none (the pipeline's footage layer is exercised by workflow/tests/footage, not by this film)

## The camera (set once)
- Dial 4, Flowing: the camera is in motion in every shot; momentum is handed shot to shot; rests carry micro-drift
- Signature moves allowed to repeat: dolly (down the street), crane (up to the schedule)

## Look
- Personality: monumental. Materials: concrete, bone ink, one orange
- References (measured, never copied): a third-party `engine` simulation (a 3D world filmed by a camera with labels on
  anchors) and the "21,000,000" master (data honesty, one accent, serious tone); benchmark = the engine sim's camera
- Palette / type: ground #0B0D10, concrete #1B1F26, ink #E9E4D8, accent #F7931A, fog #0E1116; IBM Plex Mono (data), Newsreader (captions)

## Sound
- Voiceover: none
- Music: original synthesized score (audio/make_cues.py -> audio/cues.json -> worldfilm synth_sfx.py): a thinning A-minor
  drone, a kick on each past halving, accelerating ticks for the 28 written halvings, a riser into the end
- The silence: 25.5-27.5 s, exact digital zero, before the loudest moment (27.5 s, the cap)

## Facts and rights
- facts.json holds the 12 facts; the only projections are future dates (ten-minute block assumption) and they carry "≈"
- Fonts under OFL (fonts/OFL-*.txt); three.js MIT (vendor/LICENSE-three.txt); GSAP under its standard licence (vendor/GSAP-NOTICE.txt)

## Must / must not
- Signature moments: the first halving gate stepping the street down to half; the camera stopping at NOW; the crane
  up as the schedule thins to a hairline that ends
- Must not: jokes, invented numbers, colour other than the one orange on anything but gates and the number
- Unhappy if: the film is a black tunnel on a phone (measured luma must stay above 35), or a number on screen is wrong
