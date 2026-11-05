# SOUND GRAMMAR (Style A) — "music answers the line"

Rule set distilled after TDK v1: the bed stayed in ONE state for 12.7 s (level flat within
2 dB, centroid 3789→3774 Hz) while 7 cuts happened on screen. Music was *correct*, but it was
not *responding*. Everything below is measurable at QA time.

## 1. Shaant / suspense bed is a tool, not a default
A quiet drone is only allowed as a **held breath before something**. It must be resolved by a
change — impact, lift, or silence — within one musical phrase. Never let it be the whole edit.

## 2. Every intense line gets a 3-part response
    BEFORE   music pulls back      (-6 dB or more, or strip an element)  -> gives the line room
    ON LINE  music thins           (voice owns 250 Hz-4 kHz; bed keeps only sub + one texture)
    AFTER    music pays off        (hit/lift lands on the FIRST beat after the last syllable)

If the line is a *promise* ("the night is darkest before the dawn") the payoff is a rise.
If the line is a *threat* ("people will die", "I don't want to kill you") the payoff is a
strike — and it should land on the cut, not between cuts.

## 3. The most intimate threat gets the LEAST music, not the most
"I don't want to kill you" is whispered. So: near-silence under it, and the loud answer comes
one beat later (cut + hit together). Loudness is not intensity — **contrast** is intensity.
Same reason the 8 s gap before a cluster is worth more than 8 s of full bed.

## 4. Dips are where dialogue lives; clusters are where the montage lives
Map the track's own hit density first, then place dialogue into the sparse stretches and cuts
into the dense ones. This way one song, played continuously, still has shape — because the
song's own contour is doing the work.

## 5. Acceptance criteria (QA must print these numbers)
- No 8-second window inside the edit with 0 audible onsets unless a line is playing in it.
- After every dialogue line: level change ≥ 6 dB OR centroid shift ≥ 800 Hz within 1 beat.
- Music level must move at least twice: low -> high, and it must not still be climbing when
  the video ends (end on a strike or on silence, never mid-crescendo).
- Cut times must sit on detected onsets (list cut-vs-onset delta per cut, ms).
- Zero frames from credit rolls / title cards: hard stop at the last picture frame
  (TDK: 8665.95 s). Verify with frame luma, not by eye.

## 6. Never fix a flat edit by changing the song
User rule: one song, played once. Fix it with section choice + level contour + dialogue
placement + measure of onsets. Not with a second track, not with a re-arranged "remix".
