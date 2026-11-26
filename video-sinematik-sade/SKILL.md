---
name: video-sinematik-sade
description: Kendi dikey konuşma klibini kendi Claude Code'unla "Sinematik sade" tarzında kurgular (sakin tek plan, küçük altın italik altyazı, cümleye denk gelen ara görüntüler, seyrek kesim patlamaları). "sinematik sade" ya da "sakin sinematik konuşma" dendiğinde kullan.
---

# Sinematik sade

## Kimin tarzı
Tarz: Nik'in sinematik sade üslubu (kendi referans videosundan kare kare ölçüldü). Bu klasör bu reellerden öğrenir, onları yeniden paylaşmaz: pakette yalnız bağlantılar ve bizim ölçtüğümüz sayılar var; kimsenin videosu, karesi, kapağı ya da konuşma yazısı yok.

## Ne yapar
Kendi konuşma klibinden sakin, sinematik bir konuşma reeli: tek sahne planı, küçük altın italik serif altyazı, cümlesine denk gelen hayat görüntüleri, seyrek kesim patlamaları. Kurguyu senin Claude'un yapar: videoyu kod olarak kurar, kendi karelerine bakar, sen kareye not bıraktıkça düzeltir.

Üslubun referansı herkese açık bir videodan kare kare ölçüldü; o başkasının işidir: ondan öğren, kendi videonda kendi klibini kullan, onu ya da karelerini yeniden paylaşma.

## Ne gerekir
- Kendi Claude Code'un (herhangi bir plan). Claude.ai sohbetinde değil, Claude Code'da çalışır.
- Dikey çektiğin kendi konuşma klibin (5 ile 45 saniye iyi başlangıçtır; telefonun HDR çekimi de olur). Kimsenin videosunu ya da yüzünü kullanma.
- Ücretsiz araçlar: `ffmpeg` (Mac'te `brew install ffmpeg` yeter; telefonun HDR çekimini zscale olmadan da SDR'ye çevirir) ve `python3` (numpy, opencv-contrib-python, Pillow, scipy, faster-whisper, onnxruntime, soundfile). Eksik paketleri kurulum kontrolü tek satırlık bir `pip install` komutu olarak yazar. GPU şart değil; NVIDIA kartın varsa kurgu ve yazıya dökme 5-20 kat hızlanır.
- Hesap, anahtar ya da ücretli servis gerekmez; her şey bu klasörün içinde, kendi bilgisayarında çalışır.

## Kurulum kontrolü (bir kez)
Klasörde şunu çalıştır:

    python3 scripts/setup_check.py

Eksik olanı ve nasıl kurulacağını düz cümleyle yazar; her şey tamsa `ready` der. İlk çalıştırmada küçük modeller `models/` klasörüne iner (yüz bulucu YuNet, kişi kesici MODNet ve RVM, toplam yaklaşık 41 MB). Model dosyaları pakete konmaz, ilk çalıştırmada kendi sayfalarından indirilir. Not: RVM (RobustVideoMatting) GPL-3.0 lisanslıdır, kaynağı https://github.com/PeterL1n/RobustVideoMatting; kendi bilgisayarına indirip kendi kurgunda kullanırsın, bu paketin parçası değildir. Konuşma modeli (faster-whisper) da ilk yazıya dökmede iner; Claude indirmeden önce süreyi söyler.

## Nasıl başlarsın
1. Bu klasörü `~/.claude/skills/` altına koy. Klibini kendi proje klasörüne bırak ve Claude Code'u o klasörde aç. Claude kurguyu klibin yanında `kurgu-1/` klasöründe yapar; beceri klasörüne bir şey yazmaz.
2. Claude'a şunu yaz: "Videomu Sinematik sade tarzında kurgula". Gerisini Claude yapar: kurulumu kontrol eder, ne dediğini yazıya döker ve yanlış duyduğu kelimeleri sana sorar, kesimi kurar, kısa bir kanıt render'ı alır, kendi karelerine bakar, sonra tamamını verir.
3. İlk kurgu taslaktır. Hangi saniyede neyin yanlış olduğunu bir editöre söylediğin gibi söyle ("şu saniyede başlık geç giriyor"); Claude yalnız onu değiştirip yeniden render eder.

Çıktı: kendi klibinin kurgulanmış hali, H.264 mp4 (dikey 1080x1920, 30 kare) ve bir kontrol karesi.

## Octi ile (isteğe bağlı)
Octi kullanıyorsan Claude, kurgudan önce beğendiğin yaratıcıların videolarına bakıp üslubu onlardan öğrenebilir. Düz modda da her şey Octi olmadan çalışır.
1. Octi MCP'yi bir kez bağla: `claude mcp add --transport http --scope user octi https://app.getocti.si/api/mcp`, sonra Claude Code'da `/mcp` ile Octi hesabınla giriş yap.
2. Beğendiğin videoları bulmak için Claude `search_library` ile arar (ücretsiz), ya da senin verdiğin bağlantıları `add_links` ile bir panoya ekler (günlük video kotasından düşer, kredi harcamaz). Panodaki yazıya dökümler hazır olunca `read_board` ile okunur.
3. Claude bu videolardan kesim ritmini, altyazının yerini ve boyunu, tempoyu ve konuşma hızını çıkarır; paketteki `reference/` verisi yalnız başlangıçtır, senin seçtiklerin onun üstündedir.
Octi videoyu yazıya dökümü ve sayılarıyla verir; kareleri gözle incelemek için beğendiğin videonun ekran kaydını da klasöre bırakıp "bunu da ölç" demen yeter.


## Engine notes: what the reference does (measured)
Measured by a frame-by-frame motion tracker on every frame (not shipped here). Full event list with per-event curves is in `reference/hareket.json`.

| ref | length | cuts /10 s | median shot | zooms /10 s | median zoom | median zoom length | typical curve (cubic-bezier) | time in motion | flashes | rebuild error: median / p90 scale % (moves checked) |
|---|---|---|---|---|---|---|---|---|---|---|
| ref-a | 54.19 s | 3.69 | 0.2 s | 2.03 | 5.12% | 0.901 s | out [0.192, 0.365, 0.094, 0.889] | 0.38 | 0 | 0.077 / 0.359 (8) |

How to read the error column: each move was rebuilt from its fitted curve alone and laid over the real reference frames; the number is the scale difference left. Per-frame scale noise and the share of frames where tracking was weak are in `reference/hareket.json` under `olcum_hatasi`. Zoom length is the time between 1% and 99% of the move. Caption type, fonts and placement are in `reference/gramer.md` (measured earlier with OCR).

- `reference/gramer.md`: the look pack read from the reference frames (caption type, colours, placement, layer kinds).
- `reference/params.json`: the finished-edit numbers measured on the reference (cuts, zoom, caption seat, inserts).

## Finished-edit values (from a real edit in this style)
Taken from the finished edit of this style (the numbers go into `edit.json`; the measured table above stays the rule for timing).

- **Captions:** Instrument Serif Italic, size 80, y 0.79, max width 900, colour #DECA5D, key words #F6E39A at 1.18x size, soft black shadow (blur 7). Appears in one frame.
- **Big word or number:** Archivo Black 150, white, y 0.47, fade 0.1 s, hide_caps true; the statement beat also dims the speaker to black and white (fx.bw dim 0.42).
- **Inserts:** card width 960, y 0.40, radius 26, ins_dissolve 0.3, ins_dim 0.5.
- **Grade:** lut.py --strength 0.9 --warm 0.4.
- **Camera:** Opens on a settle 1.188 to 1.0 over 0.9 s (bezier 0.192,0.365,0.094,0.925); long drift +11 % over 8.1 s (0.12,0.007,0.85,0.929) on a calm passage; overshoot push over 0.53 s (0.189,1.145,0.963,0.968) on the key moment; hard punch 1.0 / 1.06 on every cut.
- Set `"style": "sade"` in `edit.json`.

## Kendi referansını ölç (isteğe bağlı, ama en iyisi)
Beğendiğin bir reeli klasöre bırak (ekran kaydı ya da kendi indirdiğin dosya, `ref.mp4`). Sonra:

    python3 scripts/tarz_cikar.py olc ref.mp4 --out work/ref

`work/ref/hareket.json` çıkar: kesim ritmi, her zoomun başlangıcı, süresi, yüzdesi ve eğrisi, parlamalar, katman girişleri, renk ve ses. Kendi kurgunu o sayılara göre kur; `reference/hareket*.json` yalnız başlangıç verisidir, seninkinin altında kalır. Kurgun bitince `python3 scripts/tarz_cikar.py olc work/out.mp4 --out work/own` ile kendi çıktını ölç, `python3 scripts/tarz_cikar.py karsilastir work/ref/hareket.json work/own/hareket.json` ile alan alan karşılaştır. Gerekenler `setup_check.py` içinde (opencv, scipy). Videoyu karelerine de bak: `bash scripts/sheet.sh ref.mp4 work/ref.jpg 1`.

## Workflow (you, the model, decide every look value from the refs; the scripts only execute)
Never write inside this skill's folder (it may sit in `~/.claude/skills`); the one exception is `setup_check.py`, which downloads the models into its `models/` once, as part of installing. `K` = the folder this SKILL.md is in.
0. **Setup, once:** `python3 $K/scripts/setup_check.py` must print `ready` (it prints the one install line for anything missing).
   **Run folder:** `bash $K/scripts/hizli.sh prep <the clip's folder>/kurgu-1 <clip> [other files: b-roll, logo]` copies the scripts, fonts and refs there and prepares the media (steps 1-3 below: `work/mezz.mp4`, `work/a48.wav`, `work/words.json`, `work/sil.json`, `work/face.json`, `work/src.jpg`, `work/brief.md`). `cd` into the run folder and run everything below from there; `S=scripts`. Read `work/brief.md` and look at `work/src.jpg`; redo steps 1-3 by hand only when something in them looks wrong.
   After `work/decide.py` exists, `bash scripts/hizli.sh go .` runs decide, edges, placement (`yerlesim.py --fix`), check, render, cut gate and loudness in one line (`HIZLI_FG=1` keeps it in the foreground); `bash scripts/hizli.sh quick .` after a small note. Steps 6-7 are what it runs; you still LOOK at the frames.
   **When go ends FAILED** (`work/FAILED` says why): `check` = fix `work/decide.py` as the message says; `cut gate exit 2` = the gate wants your judgement on a word said twice (`work/cutqc/judge.json`, each with its sentence in `context`): read the sentence (or listen to the cut wav), then write the source span into `work/cut_fixes.json` as `"keep": [[a, b]]` when it is meant (Turkish: "bir lisansla lisanslanmıştır") or `"drop": [[a, b]]` when it is a stumble, and run `go` again; the gate never flags a kept span again. `quick` before the first finished render runs `go`. A render on a CPU takes minutes per 10 s of video; say so before you start.
1. **Look at the source.** `bash $S/mezz.sh clip.mov work` (SDR 1440x2560 30 fps mezz + 48 kHz wav; HLG/HDR is tone-mapped).
   `bash $S/sheet.sh work/mezz.mp4 work/src.jpg 2` and open the image: where is the face, how much room above the head, what is behind, b-roll or screen shots. Note every stretch that is not the speaker (a title card, a logo, a wipe, a screen): `work/brief.md` lists the ones where no face was found, `timeline.noface()` returns them, `check_edit.py` refuses a take that runs through one (set `"allow_noface": true` to show one on purpose) and the edge tools never move a cut into one. Also check what is behind the caption seat (a white shirt under white captions needs a stroke or a plate). A horizontal clip is centre-cropped (mezz.sh says so); `follow` keeps the speaker in frame.
2. **Hear it.** `python3 $S/transcribe.py work/a48.wav work/words.json [--gpu] [--lang xx]` (word times), `python3 $S/silences.py work/a48.wav work/sil.json`.
   `words.json` = `{language, segments: [{words: [{w, s, e, p}]}]}` (word, start, end in source seconds, confidence); `timeline.py` has `words_between()` and `pages_from_words()` to build caption pages from it. On a CPU transcription takes minutes (measured on a shared server at 3 threads, 30 s of Turkish with `medium`: 9.5-16 min; a recent Mac is faster); `--model small` is quicker and makes more mistakes, so tell the user the choice before you start. Whisper stretches a word across a pause: snap every cut to the silence edges in `sil.json`, never inside a word. Ask the user for names you are unsure of.
3. **Track the face** (crop, captions that never sit on the face, graphics behind the head): `python3 $S/facetrack.py work/mezz.mp4 models/yunet.onnx work/face.json`.
4. **Read the refs.** `reference/hareket.json` = every measured zoom (start, length, %, cubic-bezier, GSAP name), cut rhythm, layer entries; the other files in `reference/` add the look. These are DATA, not rules: pick which move lands on which word for THIS clip. If the user gave own refs, measure them the same way you look at frames (sheet.sh at 1 fps and at the beats) and weigh them above the bundled ref.
5. **Write the story.** Hook = the strongest line, said in the first second (no warm-up). Keep only what serves it, in story order (takes may come from anywhere in the clip). Write the edit in SOURCE seconds with `scripts/timeline.py` (see its header) in a small `work/decide.py` (start from `cp scripts/decide_iskelet.py work/decide.py`: the shape only, every look value is yours), which writes `work/edit.json`. Put a one-line reason next to every number you chose and where it came from (`hareket.json` event, card field, a frame you looked at).
6. **Check, prove, look.** `python3 $S/lut.py work/look.cube [--strength --warm --pink]` (neutral grade; tune from the ref frames),
   `python3 $S/yerlesim.py work/edit.json --fix` (safe zone of the phone app, text on its card, `reserved` corners such as a logo; it moves or shrinks what it can and lists the rest; when your refs write outside the default area, set edit.json `safe: [x0, y0, x1, y1]` in 0..1 from what you measured), `python3 $S/check_edit.py work/edit.json` (must print `ok`), then a 4-6 s proof: `python3 $S/render.py work/edit.json work/proof.mp4 --slice 0,6 [--encoder h264_nvenc]`.
   `bash $S/sheet.sh work/proof.mp4 work/proof.jpg at "0.1 0.8 1.5 2.5 4"` and LOOK: hook frame, caption off the face, layer behind the head with hair on top, zoom eased (no jump), joints clean. Fix and repeat.
7. **Full render + self-review.** Render the whole edit, `bash $S/sheet.sh work/out.mp4 work/out.jpg 1` plus strips at ±0.2 s around every cut and every layer entry. Loudness lands at -15 LUFS (render does it). Hand over `out.mp4` and a `notes.md`: what you measured, what you decided, timestamps.
8. **Notes rounds.** The user says what is wrong at which second; change only that, re-render, look again.

## edit.json (the whole contract; render.py executes it, check_edit.py refuses what would break)
- `fps`, `mezz`, `audio`, `lut`, `fonts` (= this folder's `fonts/`), `style` (caption fallback: `sade|kutulu|otantik`).
- `segments: [{in, out, x}]` source seconds in story order; `x` = dissolve frames into that take (0 = hard cut); `joint_bez` dissolve curve. Output length = sum of takes.
- `camera: [{t, d, to, from?, cx?, cy?, bez | ease}]` output seconds; `to` = zoom factor (with `follow` it multiplies the face crop). `ease`: `expoInOut sineInOut backOut linear`, or `bez: [x1,y1,x2,y2]` straight from `hareket.json`.
- `follow: {face, sigma, size_sigma, base, max, io_ref, size_k, eye_y, follow_x, hair_k, head_margin}` face-following crop: eyes held at `eye_y` of the frame, face size steady across takes (at `io_ref`, by default the clip's own median face size; never copy a number from another clip), hair kept inside.
- `captions: [{t, e, text, key: [words]}]` + `caption: {font, weight, size, color, key_color, key_font, key_scale, stroke: [px, colour], shadow: [blur, opacity], y, maxw, fade, rise, bez, pop, below_face, face, y_max}`. `below_face: 0.02` moves a page under the chin's lowest point over its own span (never on the face); it reads the face track from `follow.face`, or from `caption.face` on a locked frame without follow; the render report lists `caps_on_face` (page starts that `y_max` held up on the chin): move them in the edit (a larger `y_max` lets the page go lower, or a smaller size, or another seat) until it is empty; `y` is the seat you read from the ref.
- A card from a screen, a post or a frame (a notification, a screenshot): `python3 $S/card.py src.png work/card1.png --crop x0,y0,x1,y1 --w 620 --radius 28` makes the PNG with rounded corners and a halo; use it as an `image` layer. Only the user's own screens or material they have the right to show.
- `layers: [{t, e, kind: text|image|bar|path, behind, x, y, align, opacity, hide_caps, text|image|bar|path: {...}; path = {pts: [[x,y],..] px around the anchor, width, color, opacity, head (arrowhead px), shadow}, drawn on over in.d, in: {d, bez|ease, dy, dx, scale, blur, opacity0, stagger, wipe}, out: {d, bez|ease, dy, scale, blur, track_open}, move: [{t, d, dx, dy, scale, bez|ease}]}]` alpha motion graphics. `behind: true` draws it behind the speaker (needs `matte`), `over_caps: true` draws it over the captions (a strike or circle on a caption word), `stagger` animates letter by letter, `wipe` reveals left to right, `move` moves the layer later (a document scroll = the same `move` on every layer of the document).
- `matte: {model: models/rvm.onnx, downsample: 0.4, fill}` person cut-out, only computed on frames that need it. RVM is a video model: it carries its state from frame to frame inside a take (reset on every cut), so the edge holds still; measured on 8 takes (flow-compensated temporal error ×1000 top/mid/low): MODNet + median 5 + ema 1.82/3.82/12.77, soft edge 15.0 px, 74.5 ms/frame; RVM 1.64/2.89/11.62, 9.2 px, 17.7 ms/frame. The older form `{model: models/modnet.onnx, size: [384, 672], ema, guided: [r, eps], choke}` still works (`choke` 0.05-0.15 pulls a glowing edge in). Behind layers and `bgplate` only replace pixels they actually change, so a matte error away from a graphic never shows.
- A text layer's `shadow: [blur, opacity, color]`: the colour defaults to black; a light one is a glow (white type with a soft white glow on a dark wall). Pick ink and glow from the refs and the wall you see, not by habit.
- `fx: {bgplate: [{t, d, dim, sat, ramp}], soften: [{t, d, r}], bw: [{t, d, dim}], flash: [{t, d, invert}], camblur_ds}`: `bgplate` dims/desaturates the room behind the speaker (needs `matte`).
- Fast toolkit (every value is the edit's call from the refs and the ask; none is a default look):
  - `fx.soft: [{t, d, blur, fade, color, zoom: [from, to], at: head, ramp, bez|ease}]` soft look: blur and a slight fade toward `color`, ramped in and out over `ramp` s, on a smooth zoom of the whole picture (about the head with `at: head`).
  - `fx.blurcol: [{t, d, w, x|head, blur, dim, line, line_color, ramp}]` one sharp column (share `w` of the width, centred on the head by default) over the same frame blurred and dimmed; it opens from full width over `ramp`.
  - `fx.columns: [{t, d, items: [{file, in, focus} | {speaker: true, dx}], gap, gap_color, stagger, in, slide}]` the frame split into 2-4 columns; a file is cover-cropped at `focus`, the speaker column is cut round the head; columns slide in one after another and leave the same way.
  - `inserts: [{file, full: true, t, d, zoom: [from, to], soft, dissolve, focus, grade}]` a stock or b-roll shot over the whole frame (cover-cropped; stills get the `zoom` push); `soft` blurs the frame it leaves while the shot settles. Captions stay on top. Stock comes from the user's own files, or from a free-licence library the user picks (Pexels, Pixabay, Wikimedia Commons): note the author, link and licence of every shot in `work/kaynak.json`. `grade` defaults to off for a full shot (the clip's tone-map is for the clip).
  - `layers[].track: head` (+ `track_k`, 1 = locked, below 1 = parallax): the layer keeps its x, y at its start and then moves with the head; with `behind: true` it is a word or a graphic behind the head that follows it. Needs a face track.
- `legible` (edit or layer) and `with: <id>`: `render.py --fit` measures how much of each behind word stays clear of the speaker (4 samples over its span) and moves it (dx, dy, size) until that share holds; a strike or ring with `with` moves with its word. `overlays[].clear` and `ui: [[x0, y0, x1, y1]]` do the same for a pinned still (a logo). The engine measures and moves; how much hides behind the head is the edit's call. `hizli.sh` runs it before every render; the report lands in `edit.json` `fit`.
- `cut: {tail, head}` seconds kept past the voice at a take edge (default: half the speaker's median pause between two words of a phrase). `scripts/edges.py` runs after `decide.py` in `hizli.sh`: a word an edge cuts with most of it outside goes (a retake's first word at a take end), a clipped word end opens, room past the voice and the word's stamp goes. An edge the cut QC set stays.
- Sound (`music`, `sfx`; this package ships no sound files, every one is the user's own or from a free library whose licence allows it: Pixabay Sound Effects / Music under the Pixabay Content License, Freesound files marked CC0; note author, link and licence in `work/kaynak.json`):
  `music: {file, db, start, duck, fade}` a bed under the voice, looped and ducked by it: starting value about 20-22 dB under the voice (`db: -20`, `duck: 8`), up a little in pauses and at the end, eased in and out over `fade`.
  `sfx: [{t, file, db, lp, fade}]` output seconds; starting values from measured edits: at most about one sound every 2.5 s (0.4 per second), each 12-19 dB under the voice (`db: -16`), on a move a deep slow sound (low-pass `lp: 2000`, soft start `fade: 0.14`), never on top of a key word. Your refs decide the real density and levels; `check_edit.py` refuses a missing file or a time outside the video.
- Motion values: `scripts/hareket.py` gives the measured starting curves as edit.json numbers (`AE` = bezier 0.5,0,0.2,1.08; `move_d(px)`: a move of 300 px or more takes at least 0.75 s; `snap()`: 1.18x in 0.32 s on an emphasis line; `drift()` on a long hold). The refs you read win over them.
- `inserts`, `accents`: b-roll windows and big words (see `scripts/check_edit.py` for the fields it accepts).
