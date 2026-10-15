# brand.md — Block Space

## Identity
- Name / mark: Block Space (no logo; the number 21,000,000 is the mark)
- Voice: cold, measured, monumental; a civic film about a rule, not a pitch
- Audience: people who have heard "there will only be 21 million" and never seen the schedule as a place

## Colours
| token | hex | role |
|---|---|---|
| ground | #0B0D10 | spec ground token (the rendered ground reads #171B22 under light) |
| concrete | #1B1F26 | spec concrete token (the lit slabs read #3A424D) |
| ink | #E9E4D8 | every edge, every label, the captions |
| accent | #F7931A | halving gates, the NOW gate, the last-block marker, projections, the kicker; nothing else |
| fog | #0E1116 | the far end of the street |

## Type
- Display: Newsreader 700 (the number), 400 (captions)
- Data: IBM Plex Mono 500 (labels, corner readout)
- Minimum cap height: labels 22 px, corner readout 22 px at 1080p; the vertical cut scales to 26 px

## Materials and light
- Surfaces: matte concrete (roughness 0.78), bone-ink edges at 0.9 opacity on the past, 0.6 on the scheduled future
- Light: one warm key from the past side (-40, 60, 30), a cool rim from the future side, a blue-grey hemisphere; no shadows
- Fog: exponential, density falls with camera height so the overhead shots read the whole street
- Measured: styleframe luma mean 41-46 (reference lock); grain index target < 0.03

## Interpolation rule
- Colour transitions happen in OKLCH; in this film colours never transition, so the rule is honoured by having no gradients
