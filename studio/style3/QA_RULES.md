# Style 3 — persistent QA and correction rules

These checks apply to Style 3 only. They do not import Style A/B or Type 1/2/3/4 creative behavior.

## Before every full render

1. Build song-first. Use one continuous section of a real produced track; never synthesize music.
2. Validate every cut against the saved song beat grid. Maximum planned cut error for the Maverick project: 31 ms.
3. Render a local storyboard and inspect every layout before sending the cloud master.
4. Check vertical/square crops at the segment midpoint and near both ends. A subject-aware crop must contain the intended face, cockpit, aircraft or moving subject — not empty background.
5. Reject source title cards, actor/movie credit cards and logo-only portions. Added lyric/type treatments must not contain movie, actor, studio or copyright credits.
6. The closing shot needs a visible moving subject. Do not end on an empty landscape merely because its color looks good.
7. Keep real footage moving. Hard cuts and layout changes land on beats; no freeze-frame creative treatment.

## Cloud master QA

- Exact 1080x1920, 30 fps, planned frame count and duration.
- One H.264 video stream and one AAC audio stream; no movie-audio/dialogue stream mixed underneath the song.
- Inspect the 24-frame final contact sheet after artifact download.
- Review per-segment active-picture and motion measurements.
- Measure integrated loudness and true peak on the encoded master.
- Run ASR/earshot on the encoded song section and save its transcript; waveform/loudness graphs alone are not audio verification.

## Correction reuse

- Keep source movie footage and the song in the GitHub Actions Style 3 cache namespace.
- For a text, crop or shot-level correction, change the plan and reuse cached sources; do not unnecessarily rebuild another style or download assets again.
- Save confirmed corrections as a plan constraint or validator/check so the next Style 3 video inherits the fix.
