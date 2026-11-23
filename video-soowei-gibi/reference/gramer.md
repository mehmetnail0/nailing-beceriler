> Earlier look pack (v4, 11-15): captions, inserts, layout and audio measured with OCR and face boxes. Kept as reference data for SKILL.md. For zoom, easing and cut timing `hareket.json` is the measured source; the zoom ease counts below had no fitted curve behind them. Any `uret.py` step named here is retired .

# Otantik

This is for people who sell with a personal brand and film themselves (“faceless üretmiyorum, ben gibi”). The person is the picture, and nothing here is faceless.
There are two sources of ground truth, one reel each. **ref** is the reference reel ref-a by a public creator account (49.18 s, 30 fps, measured 11-14). **film-b** is our finished film (117.92 s, 1920x1080, measured with referans_olc.py). No soowei1–3 reel is in hand.
Taste is data, not law: every value is a default, and the user's own reference overrides it. There are only two hard laws. The caption must be readable. The caption never covers eyes and mouth unless the user's reference does.

## Grammar
- Opening montage with no speaker, 0–9.23 s: 11 shots of 0.10–1.64 s each. Flashes of 0.10–0.17 s fall at 0.63–1.07 s, and the rest run 1.1–1.6 s each (ref).
- After the opening, the edit alternates: speaker 1–5 s, then one cutaway 1.2–2.6 s. Over the whole reel the speaker holds 51 % of the time and cutaways 49 % (ref).
- Position: the speaker sits at a desk, side angle, in a 16:9 picture (ref puts it in rows 651–1268 of a 1080×1920 file). Face band: seen, not measured. The prep face box decides where captions go.
- Cutaways are his own life footage that shows what he says (other rooms, the city, a dashboard screen, a to-do app). Never a literal pun, never stock.
- A cut back to the speaker goes soft to sharp in 6 frames with a small front-loaded zoom-out (zoom amount not measured).
- Caption: inside the picture, centred, white, sentence case, no box, thin stroke. One word per page (1–3), and each word fades in over ~4 frames on its spoken word. Key words are one weight heavier.
- Accent words: a few big on-screen words (the largest in film-b is 404 px tall at y 0.44, held 2.36 s, on the 1920 scale).
- Card pieces fade, deblur and settle ×1.08 to 1.0 over 8–10 frames, staggered by 3 frames (ref).
- Moves are few and slight (ref): +2.3 % in 0.30 s · −4.4 % · −1.5 / −2.5 % · +10 % over 1.4 s · +1.7 %.
- Entry push (from a second reference that is not in hand): not measured. It is kept as move data (bulge k, push %, secs, curve) until that reference can be fitted.

## Params
| param | value | source |
|---|---|---|
| output | 1920x1080, 16:9 | film-b |
| cuts | 26 per 49.18 s; 22 shots per 117.92 s (14 hard cuts, 7 transitions) | ref scdet; film-b |
| shot length | median 1.43 s, mean 1.82 s; film-b median 2.44 s (0.96–24.96 s) | ref shots.py; film-b |
| speaker share | 51 % (8 shots, 0.90–5.20 s) | ref refcls.py |
| caption y | 0.64 of picture H; ref 52 % of file H ≈ 0.56 of picture (derived) | film-b; ref |
| caption size | 120 px on the 1920 scale (OCR ±10 %); ref 4.9 % H (H basis not stated) | film-b; ref |
| caption width | 0.161 of W (median) | film-b |
| words per page | median 1, max 2 (film-b); 1–3 (ref) | both |
| page on screen | 0.59 s median | film-b |
| caption colour | 252/248/250 (ref); #F4F2F6, stroke #A4A2A7 seen on 100 % of pages | both |
| stroke weight | 0.09 (unit not stated) | ref earlier measurement |
| uppercase share | 0.02 | film-b |
| grade | r/g/b 85/77/76; luma sd 71.6, p1 1 / p99 234 (8-bit levels); sat 0.44; no vignette | ref earlier measurement |
| palette | #100C0F 32.6 %, #302927 17.9 %, #AFB0B0 15.5 % | film-b |
| soft zoom | 1.1 per 10 s, depth 0.084 (fraction of frame), 0.79 s | film-b |
| slide | 1.2 per 10 s | film-b |
| shake p95 | zoom 0.0166, slide 0.0199 (fraction of frame) | film-b |
| speech | 139 words/min; 0 silences > 0.3 s | film-b |
| loudness | -14 LUFS, true peak ≤ -1.5 dBFS | ours |

## Check
After your own render, measure it with the same kind of measurement (cuts per 10 s, median shot, caption y and size, colours, loudness) and compare it with `tolerance` in params.json: the numbers are a band, not a law, and the user's own reference replaces them.

## Limits
- Every number comes from one reel per source. The grade, caption style and move numbers come from an earlier measurement and were not re-measured on 11-14.
- The command takes one clip, but cutaways (49 % of ref) need his own footage. Without it the reel is speaker-only, and Check flags the cutaway share.
- Font: not measured. Read it from the reference frames.
- The two sources disagree on caption y and size. The defaults follow film-b, and the user's reference decides.
- ref has a true peak of +0.4 dBFS, which clips. Ours does not copy that.
