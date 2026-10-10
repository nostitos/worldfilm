# Third-party notices

worldfilm's own code carries no licence grant yet. The components below are included or adapted under their own
licences, reproduced here as those licences require.

## Code adapted into worldfilm scripts

workflow/scripts/synth_sfx.py (sound generators, mastering, BS.1770 loudness) and workflow/scripts/beats_drop.py (beat
tracking) contain code adapted from software under the MIT License:

~~~
MIT License

Copyright (c) 2026 whaleyxbt

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
~~~

workflow/scripts/sam_separate.py (the SAM 2.1 separation flow: machine scan, model choice, chunked propagation)
contains code adapted from software under the MIT License:

~~~
MIT License

Copyright (c) 2026 Bart

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
~~~

## Bundled with the Block Space project

- studio/projects/block-space/vendor/three.module.js, three.core.js: three.js r186, MIT License (vendor/LICENSE-three.txt).
- studio/projects/block-space/vendor/gsap.min.js: GSAP 3.14.2 under the GSAP standard licence (vendor/GSAP-NOTICE.txt).
- studio/projects/block-space/fonts/: IBM Plex Mono and Newsreader, SIL Open Font License 1.1 (fonts/OFL-*.txt).
- studio/projects/block-space/references/sources/bitcoin_validation.cpp and bitcoin_chainparams.cpp: copies of Bitcoin
  Core source files (commit in bitcoin_commit.txt), MIT License, headers retained; kept as the source for the subsidy facts.

## Used at runtime, not redistributed

HyperFrames (npm), Playwright and Chromium, three (npm), ffmpeg, the Python packages in studio/requirements*.txt,
the SAM 2.1 weights (downloaded by transformers on first use), and the stock test footage described in
workflow/tests/footage/LICENSE.txt (download it; it is not in this repository).

<details><summary>three.js licence text</summary>

~~~
The MIT License

Copyright © 2010-2026 three.js authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
~~~

</details>

<details><summary>GSAP notice</summary>

~~~
gsap.min.js is GSAP 3.14.2 (https://gsap.com), copied unmodified from https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js.
Copyright 2025 GreenSock. Used under the GSAP Standard "No Charge" License: https://gsap.com/standard-license
~~~

</details>
