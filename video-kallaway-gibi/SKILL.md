---
name: video-kallaway-gibi
description: Kendi dikey konuşma klibini kendi Claude Code'unla "Kallaway gibi" kurgular (üstte siyah panelde başlık ve çizim, altta konuşan sen, ortada kelime kelime kalın altyazı, arada film kesitleri). "Kallaway gibi", "eğitim reeli", "üstte grafik altta ben" dendiğinde kullan.
---

# Kallaway gibi

## Ne yapar
Kendi konuşma klibinden Kallaway tarzı bir eğitim reeli: ekranın üst yarısında siyah zeminde kısa başlık (küçük sans satır, altında büyük italik serif) ve konuyu gösteren bir çizim, altta konuşan sen, ikisinin arasında kelime kelime kalın beyaz altyazı, ara sıra tam ekran bir kesit. Kurguyu senin Claude'un yapar: videoyu kod olarak kurar, kendi karelerine bakar, sen kareye not bıraktıkça düzeltir.

## Kimin tarzı, hangi reellerden
Tarz: Kallaway (@kallawaymarketing). En çok izlenen 5 reeli ölçüldü, bağlantılar ve sayılar `reference/kaynaklar.md` içinde. Üslubun referansı herkese açık reellerden kare kare ölçüldü; o başkasının işidir: ondan öğren, kendi videonda kendi klibini kullan, onu ya da karelerini yeniden paylaşma. Bu pakette yalnız bağlantılar ve bizim ölçtüğümüz sayılar var; kimsenin videosu, karesi, kapağı ya da konuşma yazısı yok.

## Çekim notu
Kallaway kendini kameraya yarım boy, masa başında çeker ve üst yarıyı grafiğe verir. Sen de kafanın ekranın alt yarısına denk geleceği bir kadrajla çek: telefonu biraz geri al, kafa kadrajın altta ve ortada olsun, üstte boşluk kalsın. Üst panel siyah bir şeritle örtülür; kafan oraya girerse kesilir.

## Ne gerekir
- Kendi Claude Code'un (herhangi bir plan). Claude.ai sohbetinde değil, Claude Code'da çalışır.
- Dikey çektiğin kendi konuşma klibin (5 ile 45 saniye iyi başlangıçtır; telefonun HDR çekimi de olur). Kimsenin videosunu ya da yüzünü kullanma.
- Ücretsiz araçlar: `ffmpeg` (tam sürüm: zscale, tonemap, lut3d, loudnorm filtreleriyle) ve `python3` (numpy, opencv-contrib-python, Pillow, scipy, faster-whisper, onnxruntime). GPU şart değil; NVIDIA kartın varsa kurgu ve yazıya dökme 5-20 kat hızlanır.
- Hesap, anahtar ya da ücretli servis gerekmez; her şey bu klasörün içinde, kendi bilgisayarında çalışır.

## Kurulum kontrolü (bir kez)
Klasörde şunu çalıştır:

    python3 scripts/setup_check.py

Eksik olanı ve nasıl kurulacağını düz cümleyle yazar; her şey tamsa `ready` der. İlk çalıştırmada küçük modeller `models/` klasörüne iner (yüz bulucu YuNet, kişi kesici MODNet ve RVM, toplam yaklaşık 41 MB). Model dosyaları pakete konmaz, ilk çalıştırmada kendi sayfalarından indirilir. Not: RVM (RobustVideoMatting) GPL-3.0 lisanslıdır, kaynağı https://github.com/PeterL1n/RobustVideoMatting; kendi bilgisayarına indirip kendi kurgunda kullanırsın, bu paketin parçası değildir. Konuşma modeli (faster-whisper) da ilk yazıya dökmede iner; Claude indirmeden önce süreyi söyler.

## Nasıl başlarsın
1. Bu klasörü Claude Code'da aç (ya da `~/.claude/skills/` altına koy), klibini yanına bırak.
2. Claude'a şunu yaz: "Videomu Kallaway gibi kurgula". Gerisini Claude yapar: kurulumu kontrol eder, ne dediğini yazıya döker ve yanlış duyduğu kelimeleri sana sorar, kesimi kurar, kısa bir kanıt render'ı alır, kendi karelerine bakar, sonra tamamını verir.
3. İlk kurgu taslaktır. Hangi saniyede neyin yanlış olduğunu bir editöre söylediğin gibi söyle ("şu saniyede başlık geç giriyor"); Claude yalnız onu değiştirip yeniden render eder.

Çıktı: kendi klibinin kurgulanmış hali, H.264 mp4 (dikey 1080x1920, 30 kare) ve bir kontrol karesi.

## Octi ile (isteğe bağlı)
Octi kullanıyorsan Claude, kurgudan önce beğendiğin yaratıcıların videolarına bakıp üslubu onlardan öğrenebilir. Düz modda da her şey Octi olmadan çalışır.
1. Octi MCP'yi bir kez bağla: `claude mcp add --transport http --scope user octi https://app.getocti.si/api/mcp`, sonra Claude Code'da `/mcp` ile Octi hesabınla giriş yap.
2. Beğendiğin videoları bulmak için Claude `search_library` ile arar (ücretsiz), ya da senin verdiğin bağlantıları `add_links` ile bir panoya ekler (günlük video kotasından düşer, kredi harcamaz). Panodaki yazıya dökümler hazır olunca `read_board` ile okunur.
3. Claude bu videolardan kesim ritmini, altyazının yerini ve boyunu, tempoyu ve konuşma hızını çıkarır; paketteki `reference/` verisi yalnız başlangıçtır, senin seçtiklerin onun üstündedir.
Octi videoyu yazıya dökümü ve sayılarıyla verir; kareleri gözle incelemek için beğendiğin videonun ekran kaydını da klasöre bırakıp "bunu da ölç" demen yeter.



## Ölçülen sayılar (5 reel, ortanca)
| reel | izlenme (okunma 2026-11-24) | süre | kesim /10 sn | ortanca plan | zoom /10 sn | ortanca zoom | zoom süresi | tipik eğri (cubic-bezier) |
|---|---|---|---|---|---|---|---|---|
| [DaiCxAkOpNb](https://www.instagram.com/reel/DaiCxAkOpNb/) | 1.245.571 | 107.52 s | 2.23 | 2.419 s | 3.81 | 4.01% | 0.501 s | linear  |
| [DZU1D_8OI62](https://www.instagram.com/reel/DZU1D_8OI62/) | 854.779 | 62.54 s | 2.56 | 3.417 s | 4.8 | 4.035% | 0.25 s | in [0.99, 0.165, 0.356, 0.108] |
| [DbI9NOTOIFi](https://www.instagram.com/reel/DbI9NOTOIFi/) | 554.233 | 69.99 s | 2.57 | 3.504 s | 4.86 | 3.655% | 0.417 s | out [0.563, 0.819, 0.409, 0.622] |
| [DcqiQesO_R9](https://www.instagram.com/reel/DcqiQesO_R9/) | 538.502 | 38.8 s | 1.8 | 3.9 s | 5.41 | 3.15% | 0.56 s | in [0.315, 0.471, 0.742, -0.237] |
| [DdEPZQSOsx2](https://www.instagram.com/reel/DdEPZQSOsx2/) | 416.919 | 91.21 s | 1.21 | 4.146 s | 3.62 | 3.48% | 0.417 s | in [0.733, 0.069, 0.516, -0.463] |

Ortancalar: kesim 2.23 /10 sn, ortanca plan 3.504 s, zoom 4.8 /10 sn, ortanca zoom 3.655%, zoom süresi 0.417 s, parlaklık 0.171, doygunluk 0.162. Zoomlar küçük ve sık: her 2 saniyede bir yüzde 3-4'lük kısa bir itiş. Kesim seyrek; ritmi zoom ve kelime kelime akan altyazı taşır. Tek reelde (DaiCxAkOpNb) 3 beyaz parlama ölçüldü, diğerlerinde yok: parlama bu tarzın kuralı değildir. Ölçüm 360 piksel genişlikte, her karede yapıldı; kare başına ölçek gürültüsü `reference/hareket-*.json` içinde `olcum_hatasi` altında.

## Bu tarzın değerleri (uydurma bir test klibinde kurulup izlendi)
- **Yerleşim:** tam genişlik siyah panel (`bar`, #08080A, opaklık 1, 1080x980 px, y 0.255), kafa altta. Panelin üstünde iki katman: küçük sans satır (Inter 700, 46 px, #E9E9EE, y 0.085) ve altında büyük italik serif (Instrument Serif Italic, 92 px, #F4F1E6, y 0.155); her cümlede değişir, 0.3 sn içinde 26-34 px aşağıdan, 8 px bulanıklıkla girer, 0.18 sn'de çıkar.
- **Çizim:** konuyu gösteren bir şekil (`image` katmanı, 700 px, y 0.34), 0.45 sn'de 0.88 ölçekten ve bulanıklıktan oturur; ilgili cümle bitince çıkar.
- **Altyazı:** kelime kelime, her kelime kendi süresince; Inter 800, 74 px, beyaz, yumuşak gölge, y 0.565, panelin hemen altında, yüze binmez. Kelime değişimi sert (fade 0.05 sn, kayma yok).
- **Kesit:** tam ekran bir kesit (`inserts` ile `full: true`), 1.5 sn, 0.15 sn çözülme, yavaş 1.0'dan 1.06'ya itiş; bir reelde en çok 2-3 kez.
- **Kamera:** her planın başında sert ayar (1.0, sonra 1.10, sonra yine 1.0...), arada her 2.1 sn'de 3.655% itiş, 0.417 s, eğri (0.28, 0.67, 0.38, 0.27).
- **Renk:** doğal; Kallaway'in zemini siyah, görüntü soğuk-yeşilimsi bir ışıkta.
- `edit.json` içinde `"style": "sade"` kalsın ve altyazı biçimini `caption` ile açıkça yaz (yazı tipi, boyut, renk); `sade` yalnız yedek ön ayardır.

## Kendi referansını ölç (isteğe bağlı, ama en iyisi)
Beğendiğin bir reeli klasöre bırak (ekran kaydı ya da kendi indirdiğin dosya, `ref.mp4`). Sonra:

    python3 scripts/tarz_cikar.py olc ref.mp4 --out work/ref

`work/ref/hareket.json` çıkar: kesim ritmi, her zoomun başlangıcı, süresi, yüzdesi ve eğrisi, parlamalar, katman girişleri, renk ve ses. Kendi kurgunu o sayılara göre kur; `reference/hareket-*.json` yalnız başlangıç verisidir, seninkinin altında kalır. Kurgun bitince `python3 scripts/tarz_cikar.py olc work/out.mp4 --out work/own` ile kendi çıktını ölç, `python3 scripts/tarz_cikar.py karsilastir work/ref/hareket.json work/own/hareket.json` ile alan alan karşılaştır. Gerekenler `setup_check.py` içinde (opencv, scipy). Videoyu karelerine de bak: `bash scripts/sheet.sh ref.mp4 work/ref.jpg 1`.

## Workflow (you, the model, decide every look value from the refs; the scripts only execute)
Work in a new folder `work/` next to this file. `S=scripts`.
1. **Look at the source.** `bash $S/mezz.sh clip.mov work` (SDR 1440x2560 30 fps mezz + 48 kHz wav; HLG/HDR is tone-mapped).
   `bash $S/sheet.sh work/mezz.mp4 work/src.jpg 2` and open the image: where is the face, how much room above the head, what is behind, b-roll or screen shots.
2. **Hear it.** `python3 $S/transcribe.py work/a48.wav work/words.json [--gpu] [--lang xx]` (word times), `python3 $S/silences.py work/a48.wav work/sil.json`.
   Whisper stretches a word across a pause: snap every cut to the silence edges in `sil.json`, never inside a word. Ask the user for names you are unsure of.
3. **Track the face** (crop, captions that never sit on the face, graphics behind the head): `python3 $S/facetrack.py work/mezz.mp4 models/yunet.onnx work/face.json`.
4. **Read the refs.** `reference/hareket.json` = every measured zoom (start, length, %, cubic-bezier, GSAP name), cut rhythm, layer entries; the other files in `reference/` add the look. These are DATA, not rules: pick which move lands on which word for THIS clip. If the user gave own refs, measure them the same way you look at frames (sheet.sh at 1 fps and at the beats) and weigh them above the bundled ref.
5. **Write the story.** Hook = the strongest line, said in the first second (no warm-up). Keep only what serves it, in story order (takes may come from anywhere in the clip). Write the edit in SOURCE seconds with `scripts/timeline.py` (see its header) in a small `work/decide.py`, which writes `work/edit.json`. Put a one-line reason next to every number you chose and where it came from (`hareket.json` event, card field, a frame you looked at).
6. **Check, prove, look.** `python3 $S/lut.py work/look.cube [--strength --warm --pink]` (neutral grade; tune from the ref frames),
   `python3 $S/check_edit.py work/edit.json` (must print `ok`), then a 4-6 s proof: `python3 $S/render.py work/edit.json work/proof.mp4 --slice 0,6 [--encoder h264_nvenc]`.
   `bash $S/sheet.sh work/proof.mp4 work/proof.jpg at "0.1 0.8 1.5 2.5 4"` and LOOK: hook frame, caption off the face, layer behind the head with hair on top, zoom eased (no jump), joints clean. Fix and repeat.
7. **Full render + self-review.** Render the whole edit, `bash $S/sheet.sh work/out.mp4 work/out.jpg 1` plus strips at ±0.2 s around every cut and every layer entry. Loudness lands at -15 LUFS (render does it). Hand over `out.mp4` and a `notes.md`: what you measured, what you decided, timestamps.
8. **Notes rounds.** The user says what is wrong at which second; change only that, re-render, look again.

## edit.json (the whole contract; render.py executes it, check_edit.py refuses what would break)
- `fps`, `mezz`, `audio`, `lut`, `fonts` (= this folder's `fonts/`), `style` (caption fallback: `sade|kutulu|otantik`).
- `segments: [{in, out, x}]` source seconds in story order; `x` = dissolve frames into that take (0 = hard cut); `joint_bez` dissolve curve. Output length = sum of takes.
- `camera: [{t, d, to, from?, cx?, cy?, bez | ease}]` output seconds; `to` = zoom factor (with `follow` it multiplies the face crop). `ease`: `expoInOut sineInOut backOut linear`, or `bez: [x1,y1,x2,y2]` straight from `hareket.json`.
- `follow: {face, sigma, size_sigma, base, max, io_ref, size_k, eye_y, follow_x, hair_k, head_margin}` face-following crop: eyes held at `eye_y` of the frame, face size steady across takes (at `io_ref`, by default the clip's own median face size; never copy a number from another clip), hair kept inside.
- `captions: [{t, e, text, key: [words]}]` + `caption: {font, weight, size, color, key_color, key_font, key_scale, stroke: [px, colour], shadow: [blur, opacity], y, maxw, fade, rise, bez, pop, below_face, face, y_max}`. `below_face: 0.02` moves a page under the chin's lowest point over its own span (never on the face); it reads the face track from `follow.face`, or from `caption.face` on a locked frame without follow; the render report lists `caps_on_face` (page starts that `y_max` held up on the chin): move them in the edit (a larger `y_max` lets the page go lower, or a smaller size, or another seat) until it is empty; `y` is the seat you read from the ref.
- `layers: [{t, e, kind: text|image|bar|path, behind, x, y, align, opacity, hide_caps, text|image|bar|path: {...}; path = {pts: [[x,y],..] px around the anchor, width, color, opacity, head (arrowhead px), shadow}, drawn on over in.d, in: {d, bez|ease, dy, dx, scale, blur, opacity0, stagger, wipe}, out: {d, bez|ease, dy, scale, blur, track_open}, move: [{t, d, dx, dy, scale, bez|ease}]}]` alpha motion graphics. `behind: true` draws it behind the speaker (needs `matte`), `over_caps: true` draws it over the captions (a strike or circle on a caption word), `stagger` animates letter by letter, `wipe` reveals left to right, `move` moves the layer later (a document scroll = the same `move` on every layer of the document).
- `matte: {model: models/rvm.onnx, downsample: 0.4, fill}` person cut-out, only computed on frames that need it. RVM is a video model: it carries its state from frame to frame inside a take (reset on every cut), so the edge holds still; measured on 8 takes (flow-compensated temporal error ×1000 top/mid/low): MODNet + median 5 + ema 1.82/3.82/12.77, soft edge 15.0 px, 74.5 ms/frame; RVM 1.64/2.89/11.62, 9.2 px, 17.7 ms/frame. The older form `{model: models/modnet.onnx, size: [384, 672], ema, guided: [r, eps], choke}` still works (`choke` 0.05-0.15 pulls a glowing edge in). Behind layers and `bgplate` only replace pixels they actually change, so a matte error away from a graphic never shows.
- A text layer's `shadow: [blur, opacity, color]`: the colour defaults to black; a light one is a glow (white type with a soft white glow on a dark wall). Pick ink and glow from the refs and the wall you see, not by habit.
- `fx: {bgplate: [{t, d, dim, sat, ramp}], soften: [{t, d, r}], bw: [{t, d, dim}], camblur_ds}`: `bgplate` dims/desaturates the room behind the speaker (needs `matte`).
- Fast toolkit (every value is the edit's call from the refs and the ask; none is a default look):
  - `fx.soft: [{t, d, blur, fade, color, zoom: [from, to], at: head, ramp, bez|ease}]` soft look: blur and a slight fade toward `color`, ramped in and out over `ramp` s, on a smooth zoom of the whole picture (about the head with `at: head`).
  - `fx.blurcol: [{t, d, w, x|head, blur, dim, line, line_color, ramp}]` one sharp column (share `w` of the width, centred on the head by default) over the same frame blurred and dimmed; it opens from full width over `ramp`.
  - `fx.columns: [{t, d, items: [{file, in, focus} | {speaker: true, dx}], gap, gap_color, stagger, in, slide}]` the frame split into 2-4 columns; a file is cover-cropped at `focus`, the speaker column is cut round the head; columns slide in one after another and leave the same way.
  - `inserts: [{file, full: true, t, d, zoom: [from, to], soft, dissolve, focus, grade}]` a stock or b-roll shot over the whole frame (cover-cropped; stills get the `zoom` push); `soft` blurs the frame it leaves while the shot settles. Captions stay on top. Stock comes from the user's files or `malzeme-bul` (`malzeme.py ara` / `indir`, open licence, author and licence in `kaynak.json`). `grade` defaults to off for a full shot (the clip's tone-map is for the clip).
  - `layers[].track: head` (+ `track_k`, 1 = locked, below 1 = parallax): the layer keeps its x, y at its start and then moves with the head; with `behind: true` it is a word or a graphic behind the head that follows it. Needs a face track.
- `legible` (edit or layer) and `with: <id>`: `render.py --fit` measures how much of each behind word stays clear of the speaker (4 samples over its span) and moves it (dx, dy, size) until that share holds; a strike or ring with `with` moves with its word. `overlays[].clear` and `ui: [[x0, y0, x1, y1]]` do the same for a pinned still (a logo). The engine measures and moves; how much hides behind the head is the edit's call. `hizli.sh` runs it before every render; the report lands in `edit.json` `fit`.
- `cut: {tail, head}` seconds kept past the voice at a take edge (default: half the speaker's median pause between two words of a phrase). `scripts/edges.py` runs after `decide.py` in `hizli.sh`: a word an edge cuts with most of it outside goes (a retake's first word at a take end), a clipped word end opens, room past the voice and the word's stamp goes. An edge the cut QC set stays.
- `inserts`, `accents`: b-roll windows and big words (see `scripts/check_edit.py` for the fields it accepts).

## Worked example
`example/edit.json` and `example/notes.md` are the exact edit that was drawn once on an invented test clip (a cartoon speaker and a synthetic voice, no real person) to prove this folder; `example/kanit-kontak.jpg` is its contact sheet. Read them once before your first edit; do not copy the choices, the user's clip and refs decide.
