> Earlier look pack (v4, 11-15): captions, inserts, layout and audio measured with OCR and face boxes. Kept as reference data for SKILL.md. For zoom, easing and cut timing `hareket.json` is the measured source; the zoom ease counts below had no fitted curve behind them. Any `uret.py` step named here is retired .

# Sinematik sade
This grammar comes from three public reels (ref-b, ref-a, ref-c), analysed on 2026-09-29. ref-a is the user's pick (the owner's own words), so it sets the defaults. Every value below is data, not law: read the user's own reference first and let it override. There are only two laws. (1) Captions stay readable: they must contrast with the plate behind them. (2) Captions never cover the eyes and mouth unless the user's reference does.

## Grammar
- Plate: one beautiful, mostly locked shot of the speaker (a stage or keynote, warm wood or tungsten light) that holds for long stretches. About half of all frames are still. The footage carries the reel.
- Captions: one quiet style. A small warm-gold italic serif, centred low, one short phrase at a time, hard-cut on and off, with no box and no animation. B-roll carries the same captions.
- Life b-roll: cinematic single shots (shallow depth, slow drift), each cut in on the sentence it illustrates. No graphics or cards on them.
- Bursts: fast runs only on a repeated or stressed phrase. Sound transients sit on burst cuts and nowhere else.
- Illustrations: rare, and always over a blurred, dimmed copy of the same plate, so the reel never leaves its world. They enter with a short cross-dissolve. Screenshots and cards come in staggered, labelled in the same serif, and a line or arrows draw between them.
- Statement beat: once per reel, one word or phrase in a big white bold grotesk over a dimmed black-and-white grid of clips.
- Opening: either a rack focus from blur to sharp on shot 1 (ref-c) or a settle zoom (ref-a). A short white bold grotesk phrase beside the head is optional.
- Variant seen in ref-b only: no running captions. Key-phrase titles sit top-left in a heavy grotesk, with bold against light italic. Each word goes from blur to sharp on its spoken word and is gone at the next cut. Use this only if the user's reference looks like it.
- Mapping to vertical: the references are 16:9 and 4:3 and ours is 9:16. The analysis did not cover this, so everything in this bullet is by eye. Crop a 9:16 window around the speaker; at equal height it keeps 42 % of a 4:3 width (simple arithmetic). Centre the speaker so the one-point symmetry and depth survive. Caption % H values were measured on horizontal frames, so in vertical set the caption's position and size from the user's reference: below the mouth and above the platform UI. Cards that sat on the left third stack above or below the speaker instead.

## Params (default first; brackets = other reels)
| param | value | source reel / field |
|---|---|---|
| caption colour | #DECA5D [#D7CD65] | ref-a [ref-c], caption crop |
| caption cap height | 3.2 % H [3.3 % H], horizontal frame | ref-a [ref-c] |
| caption centre | 85–88 % H [78–81 % H], horizontal frame | ref-a [ref-c] |
| caption length | 2–6 words [2–5 words] | ref-a [ref-c] |
| plate hold | 8–21 s [5–17 s; 5–15 s] | ref-a [ref-c; ref-b] |
| life b-roll shot | 1.2–3 s | ref-c only |
| burst | 6 cuts ≈0.2–0.3 s apart [4–9 clips at 0.3–0.5 s each] | ref-a [ref-b] |
| illustrations | 5 in 54.2 s | ref-a only |
| illustration dissolve | 0.3 s | ref-a, ref-b |
| card stagger | ≈0.25 s | ref-a only |
| plate blur radius / dim | not measured (blur window 2.25–2.5 s) | ref-a |
| statement word | ≈6 % H, fade-in 0.1 s | ref-a only |
| opening | rack focus 0.375 s, phrase ≈2.5 % H [settle zoom 0–0.25 s] | ref-c [ref-a] |
| titles variant | ≈8 % H cap, blur-in 0.1–0.2 s, hold ≈0.8 s | ref-b only |
| hard cuts | 0.277 /s [0.316; 0.526] | video.hard_cuts_per_s |
| median shot | 0.73 s [1.7 s; 0.93 s] | video.median_shot_s |
| still frames | 49.0 % [56.7 %; 47.5 %] | video.still_frames_pct |
| speech rate | 3.65 words/s [3.26; 2.65] | post.words_per_s |
| grade luma / contrast / sat | 44.0 / 33.2 / 0.303 | ref-a video.grade |
| grade a / b / p98 / p2 | +4.24 / −0.26 / 95.7 / 2.0 | ref-a video.grade |
| loudness | −14.3 LUFS I, −0.8 dBFS true peak | ref-a audio.loudness |
| voice / bed | voice −21.1 dB median; bed ≈8 dB under [≈9; ≈5] | ref-a [ref-c; ref-b] |
| cut transients | 4, burst cuts only [3; 5] | post.cuts_with_transient |

Bracket order is always [ref-c; ref-b].

## Build
This pack is look data only. Build the edit with the workflow in ../SKILL.md (ffmpeg + python plain path), not with a browser-based kit.

## Check
- Re-measure our render with the same measure script (cuts/s, median shot, still %, grade, LUFS, true peak, voice and bed, cut transients). Each value must fall inside `tolerance` in params.json, which holds the min–max seen across the references. The user's own reference replaces those ranges.
- Captions: sample the colour and cap height on a frame and compare them with the params. The references give no contrast number, so check readability on the hardest frame. Using face boxes, assert that no caption overlaps the eyes or mouth on any frame.
- Look at a 1 fps sheet of ours beside the ref-a sheet before showing it.

## Limits
- This rests on 3 horizontal reels from one creator. The vertical mapping is by eye; it was not measured.
- Some values come from a single reel: illustrations, card stagger, statement word and settle zoom (ref-a); b-roll length and rack focus (ref-c); burst clip count and the titles variant (ref-b).
- Fonts were named by eye (Times/Garamond italic). Blur radius, dim amount and caption tracking were not measured. Bed levels are estimates (≈).
- Tempo (121–134 bpm across the refs) was not shown to drive the cuts, so do not cut to the beat by default.
