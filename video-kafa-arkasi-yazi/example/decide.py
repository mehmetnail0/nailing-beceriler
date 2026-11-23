"""video-kafa-arkasi-yazi worked example: a sample clip (164 s, locked phone framing, light wall, face upper-middle).
Sources: C = reference/card.json (the reference reel, measured), H = reference/hareket.json, S = my look at work/src.jpg and the proof frames."""
import json, os, sys
from PIL import ImageFont
K = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W_ = os.path.join(K, 'work')
sys.path.insert(0, os.path.join(K, 'scripts'))
from timeline import TL, pages_from_words
C = json.load(open(os.path.join(K, 'reference', 'card.json'))); D = C['document']; PAL = C['palette']
W, H = 1080, 1920
# takes: start = silence end - 0.06 s, end = last word + ~0.06 s (work/sil.json; ASR puts the first word after a pause ~0.4 s early)
tl = TL([(6.45, 10.44),                # hook: the result first (8.000 subscribers, 120.000 views)
         (2.04, 3.74),                 # “Saatlerce yoğurup durmadan.”
         (17.11, 21.10),               # “Yarın sabah … tam olarak şunu yapardım.”
         (30.92, 35.88),               # step 1
         (37.45, 40.44),               # step 2 (said twice in the source; the first, cleaner one)
         (54.74, 59.46),               # step 3
         (64.71, 66.98),               # step 4
         (85.68, 90.62),               # step 5
         (109.22, 111.02), (117.01, 118.78),   # step 6, two takes
         (143.96, 144.76), (145.06, 145.84),   # recap line; one “yavaş” of “yavaş yavaş” out: twice in a 40 s cut reads as a stutter
         (156.80, 160.85)])            # CTA: the second, cleaner take, which ends on a breath (the first runs straight into the next sentence at 151.97)
T = tl.T
WJ = os.path.join(W_, 'words.json')
caps = pages_from_words(tl, WJ, max_words=3, max_chars=22, fix={'8': '8.000', '120': "120.000'e", '.000': '', "'e": '', '30': '30-40', '-40': ''})   # C.caption.words_per_page [1, 3]
seg_t = [o for (a, b, o, x) in tl.segs]


def wt(word, seg, nth=0):
    """output time of a spoken word inside take seg (ASR word start)."""
    a, b, o, _ = tl.segs[seg]; d = json.load(open(WJ)); hits = []
    for s in d['segments']:
        for w in s['words']:
            if word.lower() in w['w'].lower() and w['e'] > a + 0.05 and w['s'] < b: hits.append(max(w['s'], a))
    return T(hits[nth], seg)


LH = round(D['scroll_dist_h'] * H)              # C: one scroll = 0.068 H = one document line
SLOT = 0.235 * H                                # S: the newest line sits on his hairline (hair top ~0.22-0.25 H), so his curls cover its end like the ref's head covers its bars
X0 = D['doc_box'][0] * W                        # C: document column starts at 0.05 W
RISE = {'d': D['letter_fade_s'], 'stagger': D['stagger_s'], 'dy': D['letter_rise_h'] * H, 'bez': [0.16, 1, 0.3, 1]}   # C: 0.2 s fade, 0.02 s stagger, 0.015 H rise
SCROLL_BEZ = [0.16, 1, 0.3, 1]                  # S: the ref scroll leaves fast and settles (expo-out look); C gives its length, 0.7 s
DRIFT = D['drift_h_per_s'] * H                  # C: 0.8 % H per second, so something moves every frame
ACC = [PAL[c] for c in D['accents']]
F_TITLE = os.path.join(K, 'fonts', 'Inter.ttf')
sections = [  # (take, start time, text, kind, bar key word)
    (0, seg_t[0], '8.000 abone', 'num', 'abonem'),
    (0, wt('Son', 0), '120.000 izlenme', 'num', '120'),
    (1, seg_t[1], 'saatlerce durmadan', 'script', None),
    (2, seg_t[2], 'yarın sabah yapacağım şey', 'script', None),
    (3, seg_t[3], '1. Yeni bir tarif bul', 'title', 'tarif'),
    (4, seg_t[4], '2. Kendi tadını ekle', 'title', 'tad'),
    (5, seg_t[5], '3. Formatı platformdan seç', 'title', 'Formatı'),
    (6, seg_t[6], '4. Tutan tarifi bul', 'title', 'tutan'),
    (7, seg_t[7], '5. Formülü al, kopyalama', 'title', 'Formülü'),
    (8, seg_t[8], '6. Deftere yaz, oranı bul', 'title', 'deftere'),
]
REC, CTA = seg_t[10], seg_t[12]
starts = [s[1] for s in sections] + [REC]
# document motion: scroll k starts scroll_lead before section k; between scrolls a slow drift; scroll + drift = one line per section
moves = []
for k in range(1, len(sections)):
    prev = starts[k - 1]; span = starts[k] - D['scroll_lead_s'] - (prev + 0.5)
    drift = min(DRIFT * max(span, 0), 0.5 * LH)
    moves.append((k, [{'t': round(prev + 0.5, 3), 'd': round(max(span, 0.05), 3), 'dy': -drift, 'ease': 'linear'},
                      {'t': round(starts[k] - D['scroll_lead_s'], 3), 'd': D['scroll_s'], 'dy': -(LH - drift), 'bez': SCROLL_BEZ}]))
last_span = REC - 0.25 - (starts[-2] + 0.5)
tail = [{'t': round(starts[-2] + 0.5, 3), 'd': round(last_span, 3), 'dy': -min(DRIFT * last_span, 0.5 * LH), 'ease': 'linear'}]

lay = []
for k, (seg, t0, txt, kind, key) in enumerate(sections):
    mv = [m for kk, ms in moves if kk > k for m in ms] + tail
    if kind == 'script':
        size = 80; fnt = os.path.join(K, 'fonts', 'InstrumentSerif-Italic.ttf')
        L = {'t': round(t0, 3), 'e': round(REC, 3), 'kind': 'text', 'behind': True, 'x': X0 / W, 'y': SLOT / H, 'align': 'left',
             'text': {'text': txt, 'font': 'InstrumentSerif-Italic.ttf', 'size': size, 'color': PAL['script'], 'shadow': [8, 0.35]},
             'in': {'d': D['write_on_s'], 'wipe': True, 'ease': 'linear'}, 'out': {'d': 0.2, 'dy': -20}, 'move': mv}   # C: hand script written on in 0.5 s
        lay.append(L); continue
    size = 74 if kind == 'num' else 60
    L = {'t': round(t0, 3), 'e': round(REC, 3), 'kind': 'text', 'behind': True, 'x': X0 / W, 'y': SLOT / H, 'align': 'left',
         'text': {'text': txt, 'font': 'Inter.ttf', 'weight': 800, 'size': size, 'color': '#FFFFFF', 'tracking': -1, 'shadow': [10, 0.4]},
         'in': RISE, 'out': {'d': 0.2, 'dy': -20}, 'move': mv}
    lay.append(L)
    tw = ImageFont.truetype(F_TITLE, size).getlength(txt) + (-1) * (len(txt) - 1)
    tb = wt(key, seg) if key else t0 + 0.3
    color = ACC[(k) % len(ACC)]
    lay.insert(len(lay) - 1, {'t': round(max(tb, t0 + 0.15), 3), 'e': round(REC, 3), 'kind': 'bar', 'behind': True, 'align': 'left',
                              'x': X0 / W, 'y': (SLOT + D['bar_gap'] * H) / H,
                              'bar': {'w': int(tw), 'h': round(D['bar_h'] * H), 'color': color, 'opacity': D['bar_opacity'], 'radius': 4},
                              'in': {'d': D['bar_wipe_s'], 'wipe': True, 'ease': 'linear'}, 'out': {'d': 0.2, 'dy': -20}, 'move': mv})   # C: bar wipes in 0.1 s on its clause
# step 6 second clause gets its own bar on “oran”
k6 = len(sections) - 1; tw6 = ImageFont.truetype(F_TITLE, 60).getlength('6. Deftere yaz, ') - 14
tw6b = ImageFont.truetype(F_TITLE, 60).getlength('oranı bul')
lay.append({'t': round(wt('oran', 9), 3), 'e': round(REC, 3), 'kind': 'bar', 'behind': True, 'align': 'left', 'x': (X0 + tw6) / W,
            'y': (SLOT + D['bar_gap'] * H) / H, 'bar': {'w': int(tw6b), 'h': round(D['bar_h'] * H), 'color': PAL['blue'], 'opacity': D['bar_opacity'], 'radius': 4},
            'in': {'d': D['bar_wipe_s'], 'wipe': True, 'ease': 'linear'}, 'out': {'d': 0.2, 'dy': -20}, 'move': tail})
# recap: the whole step list returns at once, smaller, letter by letter (C.recap), and drifts on; the head hides the lower lines (C.head)
steps = [s for s in sections if s[3] == 'title']
RLH = 0.042 * H
for i, (seg, t0, txt, kind, key) in enumerate(steps):
    y = 0.075 * H + i * RLH; ti = REC + 0.06 * i
    dr = [{'t': round(ti, 3), 'd': round(CTA - ti, 3), 'dy': -DRIFT * (CTA - ti), 'ease': 'linear'}]
    lay.append({'t': round(ti, 3), 'e': round(CTA + 0.25, 3), 'kind': 'text', 'behind': True, 'x': X0 / W, 'y': y / H, 'align': 'left',
                'text': {'text': txt, 'font': 'Inter.ttf', 'weight': 800, 'size': 40, 'color': '#FFFFFF', 'shadow': [8, 0.4]},
                'in': dict(RISE, stagger=0.012), 'out': {'d': 0.25, 'dy': -30}, 'move': dr})
    tw = ImageFont.truetype(F_TITLE, 40).getlength(txt)
    lay.append({'t': round(ti + 0.3, 3), 'e': round(CTA + 0.25, 3), 'kind': 'bar', 'behind': True, 'align': 'left', 'x': X0 / W, 'y': (y + 0.016 * H) / H,
                'bar': {'w': int(tw), 'h': 14, 'color': ACC[(i + 4) % len(ACC)], 'opacity': D['bar_opacity'], 'radius': 3},
                'in': {'d': D['bar_wipe_s'], 'wipe': True, 'ease': 'linear'}, 'out': {'d': 0.25, 'dy': -30}, 'move': dr})
# CTA: hand script written on, a bar under the keyword, and a drawn arrow down toward the caption
ctaw = ImageFont.truetype(os.path.join(K, 'fonts', 'InstrumentSerif-Italic.ttf'), 86).getlength('yorumlara: kurgu')
lay.append({'t': round(CTA + 0.2, 3), 'e': round(tl.dur, 3), 'kind': 'text', 'behind': True, 'x': X0 / W, 'y': 0.12, 'align': 'left',
            'text': {'text': 'yorumlara: kurgu', 'font': 'InstrumentSerif-Italic.ttf', 'size': 86, 'color': PAL['script'], 'shadow': [8, 0.35]},
            'in': {'d': D['write_on_s'], 'wipe': True, 'ease': 'linear'}, 'move': [{'t': round(CTA + 0.2, 3), 'd': round(tl.dur - CTA, 3), 'dy': -DRIFT * (tl.dur - CTA), 'ease': 'linear'}]})
nw = ImageFont.truetype(os.path.join(K, 'fonts', 'InstrumentSerif-Italic.ttf'), 86).getlength('kurgu')
lay.append({'t': round(wt('kurgu', 12), 3), 'e': round(tl.dur, 3), 'kind': 'bar', 'behind': True, 'align': 'left', 'x': (X0 + ctaw - nw) / W, 'y': 0.12 + 0.03,
            'bar': {'w': int(nw), 'h': round(D['bar_h'] * H), 'color': PAL['yellow'], 'opacity': D['bar_opacity'], 'radius': 4},
            'in': {'d': D['bar_wipe_s'], 'wipe': True, 'ease': 'linear'}, 'move': [{'t': round(CTA + 0.2, 3), 'd': round(tl.dur - CTA, 3), 'dy': -DRIFT * (tl.dur - CTA), 'ease': 'linear'}]})
lay.append({'t': round(wt('Linki', 12), 3), 'e': round(tl.dur, 3), 'kind': 'path', 'behind': False, 'x': 0.86, 'y': 0.25,
            'path': {'pts': [[0, -70], [18, -20], [10, 30], [-14, 70]], 'width': 7, 'color': PAL['script'], 'opacity': 0.95, 'head': 26, 'shadow': [6, 0.35]},
            'in': {'d': D['arrow_draw_s'], 'bez': [0.37, 0, 0.63, 1]}})   # C: arrow drawn on in 0.5 s

# camera: locked framing (C.camera); measured moves from H only
OPEN = [0.219, 0.779, 0.495, 0.66]; TYP = [0.468, 0.741, 0.495, 0.777]
cam = [{'t': 0, 'd': 0, 'to': 1.256, 'cx': 0.5, 'cy': 0.45}, {'t': 0.0, 'd': 0.667, 'to': 1.0, 'bez': OPEN}]   # H: opening -25.6 % over 0.667 s
lvl = 1.0
for i, o in enumerate(seg_t):                   # H: ~3 moves per 10 s, median 3.06 % over 0.667 s, every take starts where the last one ended
    if i == 0: continue
    a, b, oo, _ = tl.segs[i]
    if b - a < 1.4: continue
    lvl = 1.03 if lvl == 1.0 else 1.0
    cam.append({'t': round(o + 0.35, 3), 'd': 0.667, 'to': lvl, 'bez': TYP})
k5 = wt('Formülü', 7)
cam = [c for c in cam if not (seg_t[7] <= c['t'] < seg_t[8])]
cam += [{'t': round(k5, 3), 'd': 0.667, 'to': 1.102, 'bez': TYP}, {'t': round(seg_t[8], 3), 'd': 0, 'to': 1.0}]   # H: the one +10.2 % push, on the key line
lvl = 1.0
cam.sort(key=lambda c: c['t'])
E = dict(fps=30, mezz=os.path.join(W_, 'mezz.mp4'), audio=os.path.join(W_, 'a48.wav'), lut=os.path.join(W_, 'look.cube'), fonts=os.path.join(K, 'fonts'),
         style='sade', segments=tl.seg_json(),
         matte=dict(model=os.path.join(K, 'models', 'rvm.onnx'), downsample=0.4, fill=True),   # probe3, 8 takes of this clip (flow-compensated temporal error x1000 top/mid/low, soft edge px per outline px): MODNet+median5+ema 1.82/3.82/12.77, 15.0 px, 74.5 ms/f -> RVM 1.64/2.89/11.62, 9.15 px, 17.7 ms/f; on the finished reel the ring 2-12 px outside him vs the room 14-34 px out: 1.160 -> 1.068 brighter
         fx=dict(bgplate=[{'t': 0, 'd': tl.dur, 'dim': 0.42, 'sat': 0.45}]),          # S: light wall; the neon document only reads on a darker room
         caption=dict(font='Inter.ttf', weight=600, size=round(C['caption']['size_h'] * H), y=C['caption']['centre_y'], maxw=round(C['document']['caption_w'] * W),
                      color='#FFFFFF', shadow=[6, 0.6], fade=0, rise=0, below_face=0.02, face=os.path.join(W_, 'face.json'), y_max=0.86),   # C: small white, hard cut, never moves
         captions=caps, layers=lay, camera=cam)
json.dump(E, open(os.path.join(W_, 'edit.json'), 'w'), ensure_ascii=False, indent=1)
print('dur', round(tl.dur, 2), 'cuts', len(tl.cuts), 'pages', len(caps), 'layers', len(lay))
