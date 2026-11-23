"""video-soowei-gibi worked example: my decisions for a sample clip (190 s talking head, desk behind, face fills the upper half).
Every number names its source: H = reference/hareket.json, F = SKILL.md finished-edit values, M = SKILL.md measured grammar, S = my look at work/src.jpg."""
import json, os, subprocess, sys
K = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W_ = os.path.join(K, 'work')
sys.path.insert(0, os.path.join(K, 'scripts'))
from timeline import TL, pages_from_words
PUSH = [0.36, 0.34, 0.61, 0.82]        # M: ref-a push, median 1.4 % over 1.0 s
SETTLE = [0.0, 0.0, 0.2, 1.0]          # M: layer entries settle over ~3 frames
OUT = [0.4, 0, 1, 1]
# story order, cut at the silence edges of work/sil.json (speech starts ~0.06 s before a silence ends, ends ~0.08 s after the last word)
tl = TL([(0.38, 4.02),                 # hook: the contrarian line, first frame (F: hook = strongest line, no warm-up)
         (5.40, 10.22, 4),             # “Marka gibi…” + the claim “yüz binlerce izlenen videolarımın çoğunu evde, tek başıma çektim”
         (58.09, 68.46, 4),            # why it matters: “artık sadece… yarışmıyorsun… fiyatı tahminle yazıyor”
         (69.64, 73.03, 4),            # the turn: “Ben ölçüyorum. Tek bir videom 4.8 milyon izlendi.”
         (44.56, 48.72, 4),            # proof: “9 bin takipçide… 40 katı”
         (128.62, 132.27, 4),          # “acele etmiyorsun, sabrı alıp kendi hikayene uygulayabiliyorsun” (the word before it runs into the previous one with no gap, so it stays out)
         (148.82, 152.65, 4),          # “sıfırdan başlamıyorsun, dönüp devam edebiliyorsun”
         (179.95, 181.90, 4)])         # CTA
fix = {'4': '4.8', '.8': ''}
caps = pages_from_words(tl, os.path.join(W_, 'words.json'), max_words=4, max_chars=24, fix=fix)   # F: 2-4 words per page
T = tl.T


def behind(txt, a, b, seg, size=200, y=0.17, extra=None):
    L = {'t': T(a, seg), 'e': T(b, seg), 'kind': 'text', 'behind': True, 'x': 0.5, 'y': y, 'opacity': 0.95,
         'text': {'text': txt, 'font': 'Inter.ttf', 'weight': 850, 'size': size, 'color': '#1C1915', 'tracking': -4, 'shadow': [16, 0.10]},
         'in': {'d': 0.13, 'scale': 1.08, 'blur': 6, 'bez': SETTLE}, 'out': {'d': 0.2, 'blur': 6, 'bez': OUT}}   # F: big word Inter 850 ~210, settle + blur_in 6
    L.update(extra or {}); return L


# screens: the speaker's own videos and boards, screen-recorded (work/screens/*.png), made into cards by scripts/card.py.
# The reference shows a screen the moment he names it, never later: the card comes out from behind his head, blurred and a little small, and settles
# beside it, half off the frame edge so most of it clears his curls; a white halo on a dark screen, a dark one on a light page. Three land one after another inside the hook, so the reel opens on pictures.
SC = os.path.join(W_, 'screens'); CD = os.path.join(W_, 'cards'); os.makedirs(CD, exist_ok=True)
def card(name, src, crop, w, halo='#FFFFFF', op=0.55):
    out = os.path.join(CD, name + '.png')
    subprocess.run([sys.executable, os.path.join(K, 'scripts', 'card.py'), os.path.join(SC, src), out, '--crop', crop, '--w', str(w), '--sharpen', '0.5',
                    '--halo-color', halo, '--halo-opacity', str(op)], check=True, capture_output=True)
    return out
K_REEL = card('reel', 'c84_8.png', '260,320,880,1340', 520)          # a video, open in the app
K_PLAY = card('play', 'c84_6.png', '280,0,960,900', 520)             # the same video playing
K_PROF = card('profile', 'c84_1.png', '260,560,660,1480', 420)       # his profile page: 9,1K followers, views on every video
K_GRID = card('grid', 's55_170.png', '0,600,920,1240', 760, '#000000', 0.35)   # a grid of videos on a light board
K_DECK = card('deck', 's55_217.png', '320,400,820,1080', 520)        # a carousel made in the app
REVEAL = [0.16, 1, 0.3, 1]


def shot(f, a, b, seg, x, y, w, side, delay=0.0):
    """a card that slides out from behind the head to x, blur 18 -> 0, 0.86 -> 1, then floats up a little while it is on."""
    t0, t1 = T(a, seg) + delay, T(b, seg)
    return {'t': round(t0, 3), 'e': round(t1, 3), 'kind': 'image', 'behind': True, 'x': x, 'y': y, 'file': f, 'w': w,
            'in': {'d': 0.5, 'dx': -side * 300, 'scale': 0.86, 'blur': 18, 'bez': REVEAL}, 'out': {'d': 0.28, 'blur': 12, 'scale': 0.96, 'bez': OUT},
            'move': [{'t': round(t0, 3), 'd': round(t1 - t0, 3), 'dy': -24, 'ease': 'linear'}]}


lay = [shot(K_REEL, 0.40, 2.50, 0, 0.14, 0.33, 540, -1),            # hook: “El yapımı mumla” - one video
       shot(K_PLAY, 0.95, 2.50, 0, 0.86, 0.31, 540, 1),             # “internette satış” - a second
       shot(K_GRID, 1.55, 2.50, 0, 0.50, 0.125, 640, 0),            # “olmaz” - the wall of them above his head
       shot(K_PROF, 7.11, 10.22, 1, 0.86, 0.36, 500, 1),            # “yüz binlerce izlenen videolarımın”
       shot(K_GRID, 59.60, 61.60, 2, 0.50, 0.125, 660, 0),           # “diğer satıcılarla yarışmıyorsun”
       shot(K_PLAY, 70.44, 73.03, 3, 0.14, 0.37, 520, -1),          # “Tek bir videom” - then 4.8M lands over it
       shot(K_PROF, 44.60, 46.80, 4, 0.86, 0.36, 500, 1),           # “Hesabım 9 bin takipçide”
       shot(K_DECK, 149.26, 152.65, 6, 0.85, 0.34, 540, 1),         # “Aklına bir fikir geldiğinde … dönüp devam”
       behind('4.8M', 71.58, 73.03, 3, 230, y=0.13),   # S: at 0.17 a curl hides the decimal point and it reads “48M”
                                         # the number he says, behind his head
       behind('×40', 46.94, 48.72, 4, 210),
       behind('acele', 128.62, 129.80, 5, 190)]
# small drawn motion: a strike that writes itself across “acele” as he says “acele etmiyorsun”, then “sabır” rises in its place
lay.append({'t': T(129.05, 5), 'e': T(129.80, 5), 'kind': 'path', 'behind': True, 'x': 0.5, 'y': 0.17,
            'path': {'pts': [[-300, 10], [-100, -4], [120, 6], [310, -8]], 'width': 16, 'color': '#E8563F', 'opacity': 0.95},
            'in': {'d': 0.35, 'bez': [0.16, 1, 0.3, 1]}, 'out': {'d': 0.2, 'bez': OUT}})
lay.append(behind('sabır', 129.88, 132.27, 5, 190, extra={'in': {'d': 0.3, 'dy': 40, 'blur': 6, 'bez': [0.16, 1, 0.3, 1]}}))
# a hand-drawn ring that circles “×40” once it has landed
import math
ring = [[300 * math.cos(a / 40 * 2 * math.pi - 2.6) , 130 * math.sin(a / 40 * 2 * math.pi - 2.6)] for a in range(0, 43)]
lay.append({'t': T(47.25, 4), 'e': T(48.72, 4), 'kind': 'path', 'behind': True, 'x': 0.5, 'y': 0.17,
            'path': {'pts': ring, 'width': 10, 'color': '#1C1915', 'opacity': 0.9}, 'in': {'d': 0.5, 'bez': [0.37, 0, 0.63, 1]}, 'out': {'d': 0.2, 'bez': OUT}})

segs = tl.segs
cam = [{'t': 0, 'd': 0, 'to': 1.0}]
for i, (a, b, o, x) in enumerate(segs):                     # F: one slow eased push per take, 1.5-3 % over the take
    d = b - a
    if d < 1.0: continue
    cam.append({'t': round(o, 3), 'd': 0, 'to': 1.0})
    cam.append({'t': round(o + 0.05, 3), 'd': round(d - 0.1, 3), 'to': 1.0 + min(0.03, 0.015 + 0.0015 * d), 'bez': PUSH})
cam = [k for k in cam if not (T(69.64, 3) <= k['t'] < T(73.03, 3))]
cam += [{'t': T(69.64, 3), 'd': 0, 'to': 1.0}, {'t': T(69.70, 3), 'd': 1.2, 'to': 1.05, 'bez': PUSH}]   # F: +5 % over 1.2 s only on the key line
cam.sort(key=lambda k: k['t'])
E = dict(fps=30, mezz=os.path.join(W_, 'mezz.mp4'), audio=os.path.join(W_, 'a48.wav'), lut=os.path.join(W_, 'look.cube'), fonts=os.path.join(K, 'fonts'),
         style='otantik', segments=tl.seg_json(), joint_bez=[0.42, 0, 0.58, 1],                  # F: 4-frame eased dissolves
         follow=dict(face=os.path.join(W_, 'face.json'), sigma=14, size_sigma=30, base=1.07, max=1.30, size_k=0.6,
                     eye_y=0.43, follow_x=0.85, hair_k=0.42, head_margin=0.035),               # F: crop values (S); the face size is this clip's median by default
         matte=dict(model=os.path.join(K, 'models', 'modnet.onnx'), size=[384, 672], ema=0.25, guided=[8, 1e-4], choke=0.1, fill=True, median=5),   # matte_probe (5 takes of a talking head): lower-band sway 56 -> 18 x1000; the cards sit behind his shoulders, so the torso edge must hold
         caption=dict(font='Inter.ttf', weight=600, size=54, y=0.66, maxw=900, color='#F8F6F3', shadow=[10, 0.55], fade=0.1, rise=8,
                      bez=[0.25, 0.1, 0.25, 1], below_face=0.025, y_max=0.86),                 # F: Inter 600, soft shadow, 100 ms fade, 8 px rise; seat under the chin
         captions=caps, layers=lay, camera=cam)
json.dump(E, open(os.path.join(W_, 'edit.json'), 'w'), ensure_ascii=False, indent=1)
print('dur', tl.dur, 'cuts', tl.cuts, 'pages', len(caps))
