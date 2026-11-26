#!/usr/bin/env python3
"""Plain compositor: edit.json (decided by the model) -> finished 1080x1920 mp4.
Code only executes: cut (hard or dissolve), grade (lut3d), camera curves (optionally riding a face track), inserts, captions,
alpha motion layers (in front of or behind the speaker), audio, encode. No taste lives here: every look number comes from edit.json.
usage: render.py edit.json out.mp4 [--slice a,b] [--encoder libx264|h264_nvenc] [--cuda] [--reuse-video frames.mp4] [--jobs n]
The composited frames stay next to the output as <out>.video.mp4 (no sound, no overlays): quick.py splices changed spans into it
and --reuse-video skips the frame loop, so an overlays- or music-only change re-mixes in seconds.
Defaults run on a plain laptop (CPU): libx264, no hardware decode. --encoder h264_nvenc --cuda only on an NVIDIA box.
edit.json is documented in SKILL.md ("edit.json")."""
import argparse, json, math, os, subprocess, sys, time
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument('edit'); ap.add_argument('out')
ap.add_argument('--encoder', default='libx264'); ap.add_argument('--cuda', action='store_true')
ap.add_argument('--slice', default='')  # "a,b" output-time seconds for a proof slice
ap.add_argument('--reuse-video', default='')
ap.add_argument('--jobs', type=int, default=1)  # a full render split at take starts into this many slices drawn at once
ap.add_argument('--fit', action='store_true')  # measure behind words and pinned stills against the speaker, move them where the edit asks, write edit.json, exit
a = ap.parse_args()
E = json.load(open(a.edit))
FF = os.environ.get('FF', 'ffmpeg')
FPS, W, H = E.get('fps', 30), 1080, 1920
try:      # the mezzanine's real size wins over a number copied into edit.json
    SW, SH = map(int, subprocess.run([FF.replace('ffmpeg', 'ffprobe'), '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                                      '-of', 'csv=p=0', E['mezz']], capture_output=True, text=True, check=True).stdout.strip().split(',')[:2])
except Exception:
    SW, SH = E.get('mezz_w', 1440), E.get('mezz_h', 2560)
FONTS = E.get('fonts', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts'))
ST = E['style']
T0 = time.time()

# ---------- timeline ----------
# segments: [{in, out, x}] source seconds in story order; x = dissolve frames into this segment (0 or missing = hard cut).
# A dissolve borrows x/2 frames of handle on each side of the joint, so the output length stays the sum of the segments.
segs = []
o = 0
for i, x in enumerate(E['segments']):
    fi, fo = int(round(x['in'] * FPS)), int(round(x['out'] * FPS))
    segs.append({'fi': fi, 'fo': fo, 'len': fo - fi, 'o': o, 'x': int(x.get('x', E.get('joint_frames', 0))) if i else 0,
                 'in': fi / FPS, 'out': fo / FPS, 'cover': [(int(round(a * FPS)), int(round(b * FPS))) for a, b in x.get('cover', [])]})
    o += fo - fi
for i, s in enumerate(segs):
    s['hp'] = s['x'] // 2
    s['hn'] = (segs[i + 1]['x'] - segs[i + 1]['x'] // 2) if i + 1 < len(segs) else 0
    s['s0'], s['s1'] = s['o'] - s['hp'], s['o'] + s['len'] + s['hn']
    s['o_s'] = s['o'] / FPS
NF = o; DUR = NF / FPS
sl = [float(x) for x in a.slice.split(',')] if a.slice else [0, DUR]
cut_times = [s['o_s'] for s in segs[1:]]

if a.jobs > 1 and not a.slice and not a.reuse_video and not a.fit:
    # even slices, each moved onto a take start within a second of it; a slice that opens inside a take decodes from a few frames
    # before its first one and runs the matte over them, so its recurrent state matches one long render
    def _seat(f):
        near = min((s['o'] for s in segs), key=lambda o_: abs(o_ - f))
        return near if abs(near - f) <= FPS else int(f)
    bounds = sorted({0, NF} | {_seat(k * NF / a.jobs) for k in range(1, a.jobs)})
    base = os.path.splitext(a.out)[0]; parts = [f'{base}.part{k}.mp4' for k in range(len(bounds) - 1)]
    extra = ['--encoder', a.encoder] + (['--cuda'] if a.cuda else [])
    ps = [subprocess.Popen([sys.executable, os.path.abspath(__file__), a.edit, p, '--slice', f'{b0 / FPS:.6f},{b1 / FPS:.6f}'] + extra,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE) for p, b0, b1 in zip(parts, bounds, bounds[1:])]
    errs = [p.communicate()[1] for p in ps]
    if any(p.returncode for p in ps): sys.exit(b''.join(errs).decode()[-1500:])
    lst = base + '.parts.txt'
    with open(lst, 'w') as f_: f_.write(''.join(f"file '{os.path.abspath(os.path.splitext(p)[0])}.video.mp4'\n" for p in parts))
    subprocess.run([FF, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', base + '.video.mp4'], check=True)
    for p in parts: os.remove(p); os.remove(os.path.splitext(p)[0] + '.video.mp4')
    os.remove(lst)
    r = subprocess.run([sys.executable, os.path.abspath(__file__), a.edit, a.out, '--reuse-video', base + '.video.mp4'] + extra, capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr[-1500:])
    j = json.loads(r.stdout.strip().splitlines()[-1]); j.update(jobs=len(parts), total_s=round(time.time() - T0, 1))
    print(json.dumps(j)); sys.exit(0)


def bez(p, t):
    """cubic-bezier(x1,y1,x2,y2) like CSS: solve x(u)=t, return y(u)."""
    t = min(1.0, max(0.0, t))
    x1, y1, x2, y2 = p
    u = t
    for _ in range(14):
        x = 3 * (1 - u) ** 2 * u * x1 + 3 * (1 - u) * u ** 2 * x2 + u ** 3 - t
        dx = 3 * (1 - u) ** 2 * x1 + 6 * (1 - u) * u * (x2 - x1) + 3 * u ** 2 * (1 - x2)
        if abs(dx) < 1e-6: break
        u = min(1, max(0, u - x / dx))
    return 3 * (1 - u) ** 2 * u * y1 + 3 * (1 - u) * u ** 2 * y2 + u ** 3


EASE = {'expoInOut': lambda t: (2 ** (20 * t - 10)) / 2 if t < .5 else (2 - 2 ** (-20 * t + 10)) / 2,
        'sineInOut': lambda t: -(math.cos(math.pi * t) - 1) / 2,
        'backOut': lambda t: 1 + 2.2 * (t - 1) ** 3 + 1.2 * (t - 1) ** 2,
        'linear': lambda t: t}


def ease(k, u, default='sineInOut'):
    u = min(1.0, max(0.0, u))
    return bez(k['bez'], u) if 'bez' in k else EASE[k.get('ease', default)](u)


cam = sorted(E['camera'], key=lambda k: k['t'])


def cam_at(t):
    """camera state (scale, cx, cy) at output time t. Keys: {t,d,to,from,cx,cy,bez|ease}; d=0 = hard set (on a cut).
    With a face track ("follow"), scale is a factor on the follow base and cx/cy are ignored (the face drives them)."""
    s, cx, cy = cam[0].get('from', cam[0]['to']), cam[0].get('cx', .5), cam[0].get('cy', .4)
    for k in cam:
        if t < k['t']: break
        s0, cx0, cy0 = s, cx, cy
        s1, cx1, cy1 = k['to'], k.get('cx', cx), k.get('cy', cy)
        if 'from' in k: s0 = k['from']
        d = k.get('d', 0)
        if d <= 0 or t >= k['t'] + d:
            s, cx, cy = s1, cx1, cy1
        else:
            f = ease(k, (t - k['t']) / d)
            s, cx, cy = s0 + (s1 - s0) * f, cx0 + (cx1 - cx0) * f, cy0 + (cy1 - cy0) * f
    return s, cx, cy


# ---------- face-following crop (optional) ----------
# follow: {face, sigma, size_sigma, base, max, io_ref, size_k, eye_y, follow_x, hair_k, head_margin, room_top}  (minimal: {face: 'work/face.json'})
# face = facetrack.py output (per source frame: eye-centre x, y, inter-ocular distance, face box). The crop keeps the eyes at eye_y,
# the face size near io_ref (default: the clip's median) across takes (so a joint does not jump in size) and the hair top inside the frame.
FOL = E.get('follow')
FACE = (FOL or {}).get('face') or E['caption'].get('face')   # caption.face: the face track for a locked frame (no follow), so below_face still works
FSM = None
if FACE:
    from scipy.ndimage import gaussian_filter1d
    FO = FOL or {}
    _F = json.load(open(FACE))['f']
    for x in E['segments']:               # a covered card holds the speaker's frame, so it holds that frame's face too
        fi_ = int(round(x['in'] * FPS))
        for a_, b_ in x.get('cover', []):
            a_, b_ = int(round(a_ * FPS)), int(round(b_ * FPS)); src_ = a_ - 1 if a_ - 1 >= fi_ else b_
            for k_ in range(a_, min(b_, len(_F))): _F[k_] = _F[src_] if src_ < len(_F) else _F[k_]
    _idx = np.array([i for i, x in enumerate(_F) if x])
    _arr = np.array([[_F[i][0], _F[i][1], _F[i][2], _F[i][4], _F[i][6]] for i in _idx], float)
    _full = np.stack([np.interp(np.arange(len(_F)), _idx, _arr[:, k]) for k in range(5)], 1)
    FSM = gaussian_filter1d(_full, FO.get('sigma', 14), axis=0, mode='nearest')
    FSM[:, 2] = gaussian_filter1d(_full[:, 2], FO.get('size_sigma', 30), mode='nearest')
    _has = np.array([1.0 if x else 0.0 for x in _F])        # face present? smoothed, so a take that turns to a screen hands over to a plain crop softly
    HAS = gaussian_filter1d(_has, FO.get('sigma', 14), mode='nearest')
    IO_REF = FO.get('io_ref') or float(np.median(_arr[:, 2]))   # the face size every take is brought to: this clip's own median unless the edit names one


def panel_b(t):
    """bottom (0..1) of the opaque full-width panels across the top of the frame at t (0 when none)."""
    b = 0.0
    for L in E.get('layers', []):
        if L.get('behind') or not (L['t'] <= t < L['e']) or L.get('opacity', 1) < 0.9: continue
        if L['kind'] == 'bar' and L['bar'].get('opacity', 1) >= 0.9 and L['bar']['w'] >= 0.9 * W:
            top = L.get('y', 0.5) * H - L['bar']['h'] / 2
            if top <= 0.02 * H: b = max(b, (top + L['bar']['h']) / H)
    return b


def view(seg, n, t):
    """crop window (x0, y0, ww) in mezz pixels for output frame n drawn from segment seg."""
    s, cx, cy = cam_at(t)
    if not FOL:
        ww, wh = SW / s, SH / s
        return min(max(cx * SW - ww / 2, 0), SW - ww), min(max(cy * SH - wh / 2, 0), SH - wh), ww
    sf = min(max(seg['fi'] + (n - seg['o']), 0), len(FSM) - 1)
    ex, ey, io, by, bh = FSM[sf]
    norm = (IO_REF / io) ** FOL.get('size_k', 1.0)
    sc = min(FOL.get('max', 1.35), max(1.0, FOL.get('base', 1.07) * norm * s))
    h = HAS[sf]
    if h < 0.999:                                    # no face (screen, b-roll): plain centred crop at the camera zoom, blended by face presence
        sc = h * sc + (1 - h) * max(1.0, s)
    ww, wh = SW / sc, SH / sc
    fx_ = SW / 2 + (ex - SW / 2) * FOL.get('follow_x', 1.0)
    hair = by - FOL.get('hair_k', 0.35) * bh
    x0 = min(max(fx_ - ww / 2, 0), SW - ww)
    pb = panel_b(t)                           # an opaque panel across the top: the head fits under it, the crop may start above the clip
    ytop = -max(FOL.get('room_top', 0), pb) * wh   # room_top: the crop may start this much (of the frame) above the clip (a head shot too high)
    y0 = min(max(min(ey - FOL.get('eye_y', 0.43) * wh, hair - (pb + FOL.get('head_margin', 0.035)) * wh), ytop), SH - wh)
    if h < 0.999:
        x0 = h * x0 + (1 - h) * (cx * SW - ww / 2); y0 = h * y0 + (1 - h) * (cy * SH - wh / 2)
        x0 = min(max(x0, 0), SW - ww); y0 = min(max(y0, ytop), SH - wh)
    return x0, y0, ww


def warp(img, x0, y0, ww):
    k = W / ww
    return cv2.warpAffine(img, np.float32([[k, 0, -x0 * k], [0, k, -y0 * k]]), (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


HEAD_C = {}


def head_at(n):
    """the eye centre of the speaker in output pixels at output frame n (None with no face): what a layer with track 'head' follows."""
    if FSM is None: return None
    if n not in HEAD_C:
        act = [s for s in segs if s['o'] <= n < s['o'] + s['len']] or [s for s in segs if s['s0'] <= n < s['s1']]
        r = None
        if act:
            sg = act[-1]; x0, y0, ww = view(sg, n, n / FPS); sf = min(max(sg['fi'] + (n - sg['o']), 0), len(FSM) - 1)
            if HAS[sf] >= 0.5: r = ((FSM[sf][0] - x0) * W / ww, (FSM[sf][1] - y0) * W / ww)
        HEAD_C[n] = r
    return HEAD_C[n]


def head_off(L, t):
    """layer.track 'head': the layer keeps its x, y at its start and then moves with the head (track_k 1 = locked, 0.5 = half, a parallax)."""
    if L.get('track') != 'head': return 0.0, 0.0
    h0, h1 = head_at(int(round(L['t'] * FPS))), head_at(int(round(t * FPS)))
    if not h0 or not h1: return 0.0, 0.0
    k = L.get('track_k', 1.0); return k * (h1[0] - h0[0]), k * (h1[1] - h0[1])


# ---------- fonts / captions ----------
def font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if weight:
        try:
            axes = f.get_variation_axes(); vals = []
            for ax in axes:
                nm = ax.get('name', b'')
                nm = nm.decode() if isinstance(nm, bytes) else str(nm)
                vals.append(weight if 'eight' in nm or nm == 'wght' else (min(max(size / 2, ax['minimum']), ax['maximum']) if 'ptical' in nm or nm == 'opsz' else ax['default']))
            f.set_variation_by_axes(vals)
        except Exception:
            if name not in _NOVAR: _NOVAR.add(name); print(f'{name} has no weight axis (not a variable font): "weight" is ignored for it', file=sys.stderr)
    return f


_NOVAR = set()


def low(s):
    """Turkish-safe lower(): 'İ'.lower() would leave a combining dot and a key word would never match."""
    return s.replace('İ', 'i').replace('I', 'ı').lower()


def hexrgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


CAP_CACHE = {}


def layout_words(words, keyset, fn_norm, fn_key, maxw, gap):
    """greedy wrap into lines of (word, font, w)."""
    lines, cur, cw = [], [], 0
    for w in words:
        fn = fn_key if low(w.strip('.,!?…“”')) in keyset else fn_norm
        ww = fn.getlength(w)
        if cur and cw + gap + ww > maxw:
            lines.append(cur); cur, cw = [], 0
        cur.append((w, fn, ww)); cw += (gap if cw else 0) + ww
    if cur: lines.append(cur)
    return lines


def render_caption(c):
    """RGBA image + (x, y) top-left on the 1080x1920 canvas, per style. Cached per caption."""
    key = id(c)
    if key in CAP_CACHE: return CAP_CACHE[key]
    words = c['text'].split()
    keyset = {low(k.strip('.,!?…“”')) for k in c.get('key', [])}
    cs = E['caption']
    if 'font' in cs:      # explicit look from edit.json wins over the style preset
        fn = font(cs['font'], cs.get('size', 70), cs.get('weight'))
        fk = font(cs.get('key_font', cs['font']), int(cs.get('size', 70) * cs.get('key_scale', 1.0)), cs.get('key_weight', cs.get('weight')))
        col, kcol = hexrgb(cs.get('color', '#F6F4F7')), hexrgb(cs.get('key_color', cs.get('color', '#FFFFFF')))
    elif ST == 'sade':
        fn = font('InstrumentSerif-Italic.ttf', cs.get('size', 66))
        fk = font('InstrumentSerif-Italic.ttf', int(cs.get('size', 66) * 1.18))
        col, kcol = hexrgb(cs.get('color', '#DECA5D')), hexrgb(cs.get('key_color', '#F3DF8E'))
    elif ST == 'kutulu':
        fn = font('Inter.ttf', cs.get('size', 70), 760)
        fk = font('Inter.ttf', cs.get('size', 70), 900)
        col, kcol = hexrgb('#F4DCC6'), hexrgb('#FFF3E6')
    else:
        fn = font('Inter.ttf', cs.get('size', 76), 560)
        fk = font('Inter.ttf', int(cs.get('size', 76) * 1.06), 820)
        col, kcol = (246, 244, 247), (255, 255, 255)
    gap = fn.getlength(' ')
    lines = layout_words(words, keyset, fn, fk, cs.get('maxw', 880), gap)
    asc, desc = fk.getmetrics()
    lh = int((asc + desc) * cs.get('lh', 1.08))
    padx, pady = (30, 14) if ST == 'kutulu' else (24, 20)
    lw = [sum(x[2] for x in ln) + gap * (len(ln) - 1) for ln in lines]
    bw, bh = int(max(lw) + 2 * padx + 20), int(lh * len(lines) + 2 * pady + 20)
    im = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if ST == 'kutulu':   # rust box per line, outline, measured colours
        for i, ln in enumerate(lines):
            x0 = (bw - lw[i]) / 2 - padx; y0 = 10 + i * lh
            d.rounded_rectangle([x0, y0, x0 + lw[i] + 2 * padx, y0 + lh + pady * 0.6], radius=18, fill=hexrgb('#9F5C35') + (245,), outline=hexrgb('#B88A6A') + (255,), width=3)
    shadow = Image.new('RGBA', (bw, bh), (0, 0, 0, 0)); sd = ImageDraw.Draw(shadow)
    for i, ln in enumerate(lines):
        x = (bw - lw[i]) / 2; y = 10 + pady * (0.3 if ST == 'kutulu' else 1) + i * lh
        for w, f, ww in ln:
            iskey = f is fk
            fill = (kcol if iskey else col) + (255,)
            if 'stroke' in cs:
                sw_, sc_ = cs['stroke']
                d.text((x, y + (asc - f.getmetrics()[0])), w, font=f, fill=fill, stroke_width=int(sw_), stroke_fill=hexrgb(sc_) + (255,))
            elif ST == 'otantik':
                d.text((x, y + (asc - f.getmetrics()[0])), w, font=f, fill=fill, stroke_width=2, stroke_fill=(164, 162, 167, 200))
            else:
                if ST == 'sade': sd.text((x + 2, y + 3 + (asc - f.getmetrics()[0])), w, font=f, fill=(0, 0, 0, 215), stroke_width=3, stroke_fill=(0, 0, 0, 150))
                d.text((x, y + (asc - f.getmetrics()[0])), w, font=f, fill=fill)
            x += ww + gap
    if ST == 'sade':
        shadow = shadow.filter(ImageFilter.GaussianBlur(7)); shadow.alpha_composite(im); im = shadow
    if 'shadow' in cs:    # [blur px, opacity 0..1]
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel('A').filter(ImageFilter.GaussianBlur(cs['shadow'][0])).point(lambda v: int(v * cs['shadow'][1])))
        sh.alpha_composite(im); im = sh
    elif ST == 'otantik':
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel('A').filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.45)))
        sh.alpha_composite(im); im = sh
    arr = np.array(im)
    x = int(W / 2 - bw / 2); y = int(cs.get('y', 0.74) * H - bh / 2)
    CAP_CACHE[key] = (arr, x, y)
    return CAP_CACHE[key]


def render_accent(c):
    key = ('acc', id(c))
    if key in CAP_CACHE: return CAP_CACHE[key]
    acc = E.get('accent_style', {})
    txt = c['text']
    size = acc.get('size', 150)
    fn = font(acc.get('font', 'ArchivoBlack-Regular.ttf'), size, acc.get('weight'))
    maxw = int(W * acc.get('maxw', 0.9)) - 80          # a big number never leaves the frame: shrink until it fits
    while fn.getlength(txt) > maxw and size > 40:
        size = int(size * 0.94); fn = font(acc.get('font', 'ArchivoBlack-Regular.ttf'), size, acc.get('weight'))
    tw = fn.getlength(txt); asc, desc = fn.getmetrics()
    im = Image.new('RGBA', (int(tw + 80), asc + desc + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((40, 46), txt, font=fn, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    d.text((40, 40), txt, font=fn, fill=hexrgb(acc.get('color', '#FFFFFF')) + (255,))
    sh.alpha_composite(im)
    arr = np.array(sh)
    x = int(W / 2 - arr.shape[1] / 2); y = int(c.get('y', acc.get('y', 0.5)) * H - arr.shape[0] / 2)
    CAP_CACHE[key] = (arr, x, y)
    return CAP_CACHE[key]


def blend(frame, rgba, x, y, alpha=1.0, scale=1.0, blur=0):
    """composite an RGBA sprite at a sub-pixel position and scale (scale about its centre), premultiplied so edges never darken;
    whole-pixel snapping is what makes slow drifts and eased scales step visibly."""
    h0, w0 = rgba.shape[:2]
    if blur > 0.3:
        k = int(blur * 2) * 2 + 1; pad = k
        rgba = cv2.copyMakeBorder(rgba, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0); x -= pad; y -= pad; h0 += 2 * pad; w0 += 2 * pad
    w, h = w0 * scale, h0 * scale
    left, top = x + (w0 - w) / 2, y + (h0 - h) / 2
    X0, Y0 = max(int(np.floor(left)), 0), max(int(np.floor(top)), 0)
    X1, Y1 = min(int(np.ceil(left + w)) + 1, W), min(int(np.ceil(top + h)) + 1, H)
    if X1 <= X0 or Y1 <= Y0: return
    src = rgba.astype(np.float32); src[..., :3] *= src[..., 3:4] / 255.0
    if blur > 0.3: src = cv2.GaussianBlur(src, (k, k), blur)
    M = np.float32([[scale, 0, left - X0 + 0.5 * scale - 0.5], [0, scale, top - Y0 + 0.5 * scale - 0.5]])
    sub = cv2.warpAffine(src, M, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    al = sub[..., 3:4] / 255.0 * alpha
    roi = frame[Y0:Y1, X0:X1].astype(np.float32)
    frame[Y0:Y1, X0:X1] = np.clip(roi * (1 - al) + sub[..., :3] * alpha, 0, 255).astype(np.uint8)


# ---------- inserts ----------
INS = []
def cover_crop(f, aspect, fx_=0.5, fy_=0.5):
    """the largest crop of file f with this w/h aspect, centred on (fx_, fy_) of the source"""
    sw, sh = map(int, subprocess.run([FF.replace('ffmpeg', 'ffprobe'), '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                                      '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.split(',')[:2])
    cw_, ch_ = (sw, int(sw / aspect)) if sw / sh < aspect else (int(sh * aspect), sh)
    cw_, ch_ = cw_ // 2 * 2, ch_ // 2 * 2
    return [int(min(max(fx_ * sw - cw_ / 2, 0), sw - cw_)), int(min(max(fy_ * sh - ch_ / 2, 0), sh - ch_)), cw_, ch_]


for ins in E.get('inserts', []):
    if ins.get('full'):                           # a stock or b-roll shot over the whole frame: cover-cropped, no card
        ins = dict(ins, w=W, radius=0, crop=ins.get('crop') or cover_crop(ins['file'], W / H, *ins.get('focus', [0.5, 0.5])))
    cw = ins.get('w', 1000)
    x, y, w, h = ins.get('crop', [0, 0, 1920, 1080])
    ch = H if ins.get('full') else int(round(cw * h / w / 2) * 2)
    still = ins['file'].lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))   # a screenshot or photo: held for the whole insert, 'in' is ignored
    src_in = ['-loop', '1', '-t', str(ins['d'] + 0.1), '-i', ins['file']] if still else ['-ss', str(ins['in']), '-t', str(ins['d'] + 0.1), '-i', ins['file']]
    cmd = [FF, '-v', 'error'] + src_in + ['-vf',
           f'crop={w}:{h}:{x}:{y},scale={cw}:{ch}:flags=lanczos,fps={FPS}' + (f",lut3d={E['lut']}:interp=tetrahedral" if ins.get('grade', not ins.get('full')) else ''),
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    if not raw:
        sys.exit(f"insert {ins['file']}: ffmpeg gave no frames; check the path and that 'in' ({ins.get('in')}) is inside the clip.")
    fr = np.frombuffer(raw, np.uint8).reshape(-1, ch, cw, 3)
    r = ins.get('radius', 28)
    if r == 0: INS.append(dict(ins, frames=fr, mask=np.full((ch, cw), 255, np.uint8), cw=cw, ch=ch)); print('insert', ins['file'], fr.shape, file=sys.stderr); continue
    mask = np.zeros((ch, cw), np.uint8); cv2.rectangle(mask, (r, 0), (cw - r, ch), 255, -1); cv2.rectangle(mask, (0, r), (cw, ch - r), 255, -1)
    for cx_, cy_ in ((r, r), (cw - r, r), (r, ch - r), (cw - r, ch - r)): cv2.circle(mask, (cx_, cy_), r, 255, -1, cv2.LINE_AA)
    INS.append(dict(ins, frames=fr, mask=mask, cw=cw, ch=ch))
    print('insert', ins['file'], fr.shape, file=sys.stderr)


def active_insert(t):
    for i in INS:
        if i['t'] <= t < i['t'] + i['d']: return i
    return None


def plate_bg(img):
    sm = cv2.resize(img, (W // 6, H // 6), interpolation=cv2.INTER_AREA)
    sm = cv2.GaussianBlur(sm, (0, 0), 6)
    bg = cv2.resize(sm, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) * E.get('ins_dim', 0.55)
    return bg.astype(np.uint8)


def draw_insert(frame, plate, ins, t):
    u = t - ins['t']; out_u = ins['t'] + ins['d'] - t
    fi = min(int(u * FPS), len(ins['frames']) - 1)
    card = ins['frames'][fi]
    dis = ins.get('dissolve', E.get('ins_dissolve', 0.3))
    if ins.get('full'):                           # whole-frame shot: dissolve, and with soft r the frame it leaves blurs out while the shot settles in
        a = ease({'ease': 'sineInOut'}, min(1, u / dis, out_u / dis)) if dis > 0 else 1
        zi = ins.get('zoom', [1.0, 1.0]); z = zi[0] + (zi[1] - zi[0]) * ease({'ease': 'sineInOut'}, u / ins['d'])   # a slow push (or pull) on the shot itself
        sr = ins.get('soft', 0) * (1 - a)
        shot = card if abs(z - 1) < 1e-3 else cv2.warpAffine(card, np.float32([[z, 0, (1 - z) * W / 2], [0, z, (1 - z) * H / 2]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if sr > 0.4: shot = cv2.GaussianBlur(shot, (0, 0), sr)
        if a < 1:
            base = cv2.GaussianBlur(frame, (0, 0), ins.get('soft', 0) * a) if ins.get('soft', 0) * a > 0.4 else frame
            shot = cv2.addWeighted(base, 1 - a, shot, a, 0)
        frame[:] = shot
        return
    a_in = min(1, u / dis) if dis > 0 else 1
    a_out = min(1, out_u / dis) if dis > 0 else 1
    bg = plate_bg(plate)
    base = frame.copy()
    k_bg = min(a_in, a_out)
    comp = (base.astype(np.float32) * (1 - k_bg) + bg.astype(np.float32) * k_bg).astype(np.uint8)
    settle = ins.get('settle', 0)            # card pieces: x1.08 -> 1.0 with deblur over N frames
    sc, bl = 1.0, 0
    if settle and u < settle / FPS:
        f = u / (settle / FPS); sc = 1.08 - 0.08 * (1 - (1 - f) ** 3); bl = 6 * (1 - f)
    rgba = np.dstack([card, ins['mask']])
    cx, cy = int(W / 2 - ins['cw'] / 2), int(ins.get('y', 0.40) * H - ins['ch'] / 2)
    sh = np.zeros((ins['ch'] + 80, ins['cw'] + 80, 4), np.uint8); sh[40:-40, 40:-40, 3] = (ins['mask'] * 0.55).astype(np.uint8)
    sh = cv2.GaussianBlur(sh, (0, 0), 18)
    blend(comp, sh, cx - 40, cy - 28, alpha=min(1, 2 * k_bg))
    blend(comp, rgba, cx, cy, alpha=min(1, 2 * min(a_in, a_out)) if dis > 0 else 1, scale=sc, blur=bl)
    frame[:] = comp



# ---------- alpha motion layers (text, image, bar), in front of or behind the speaker ----------
# layer: {t, e, kind: text|image|bar, behind, x, y (centre, 0..1), align: center|left,
#   text: {text, font, weight, size, color, tracking, stroke: [px, color], shadow: [blur, opacity, color (default black; a light one is a glow)], lh}
#   image: file (png with alpha), w (px) on the layer itself      bar: {w, h, color, opacity, radius}
#   in: {d, bez|ease, dy, dx, scale, blur, stagger (s per letter), wipe (bar reveal left->right)}
#   out: {d, bez|ease, dy, scale, blur, track_open (px per letter)}
#   move: [{t, d, dx, dy, scale, bez|ease}] group motion in output seconds (a scroll, a drift, a zoom out)}
LAY = E.get('layers', [])
SPR = {}


def layer_sprites(L):
    """list of (rgba, x_off, y_off, index) units relative to the layer anchor; letters are units when the layer staggers."""
    if id(L) in SPR: return SPR[id(L)]
    units = []
    if L['kind'] == 'text':
        T = L['text']; fn = font(T['font'], T['size'], T.get('weight'))
        col = hexrgb(T.get('color', '#FFFFFF')) + (255,)
        stroke = T.get('stroke'); trk = T.get('tracking', 0)
        asc, desc = fn.getmetrics(); lh = int((asc + desc) * T.get('lh', 1.1)); pad = max(30, int(3 * T['shadow'][0]) if T.get('shadow') else 30)
        lines = T['text'].split('\n'); per_letter = L.get('in', {}).get('stagger', 0) > 0 or L.get('out', {}).get('track_open', 0)
        k = 0
        for li, ln in enumerate(lines):
            widths = [fn.getlength(ch) for ch in ln]
            lw = sum(widths) + trk * max(0, len(ln) - 1)
            x = -lw / 2 if L.get('align', 'center') == 'center' else 0
            y = li * lh - len(lines) * lh / 2
            chunks = [(ch, wd) for ch, wd in zip(ln, widths)] if per_letter else [(ln, lw)]
            for ch, wd in chunks:
                im = Image.new('RGBA', (int(wd + 2 * pad + (trk * len(ch) if not per_letter else 0)), asc + desc + 2 * pad), (0, 0, 0, 0))
                dr = ImageDraw.Draw(im)
                cx_ = pad
                for c1 in ch:
                    if stroke: dr.text((cx_, pad), c1, font=fn, fill=col, stroke_width=int(stroke[0]), stroke_fill=hexrgb(stroke[1]) + (255,))
                    else: dr.text((cx_, pad), c1, font=fn, fill=col)
                    cx_ += fn.getlength(c1) + trk
                if T.get('shadow'):
                    sh = Image.new('RGBA', im.size, hexrgb(T['shadow'][2]) + (0,) if len(T['shadow']) > 2 else (0, 0, 0, 0))
                    sh.putalpha(im.getchannel('A').filter(ImageFilter.GaussianBlur(T['shadow'][0])).point(lambda v, o_=T['shadow'][1]: int(v * o_)))
                    sh.alpha_composite(im); im = sh
                if ch.strip(): units.append((np.array(im), x - pad, y - pad, k))
                x += wd + trk; k += 1
    elif L['kind'] == 'image':
        im = Image.open(L['file']).convert('RGBA'); w = int(L.get('w', im.width)); im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
        units.append((np.array(im), -im.width / 2, -im.height / 2, 0))
    elif L['kind'] == 'bar':
        B = L['bar']; w, h = int(B['w']), int(B['h']); r = int(B.get('radius', 0))
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=hexrgb(B['color']) + (int(255 * B.get('opacity', 1)),))
        units.append((np.array(im), -w / 2 if L.get('align', 'center') == 'center' else 0, -h / 2, 0))
    SPR[id(L)] = units
    return units


def path_sprite(L, p):
    """a stroke that draws itself on: path.pts [[x,y],..] px around the anchor, drawn up to fraction p of its length; head = arrowhead px."""
    P = L['path']; pts = np.array(P['pts'], float); wd = int(P.get('width', 8)); hd = P.get('head', 0)
    seg = np.hypot(*np.diff(pts, axis=0).T); cum = np.concatenate([[0], np.cumsum(seg)]); upto = cum[-1] * min(max(p, 0), 1)
    k = int(np.searchsorted(cum, upto, side='right')); keep = pts[:max(k, 1)].tolist()
    if k < len(pts) and seg[k - 1] > 0:
        f = (upto - cum[k - 1]) / seg[k - 1]; keep.append((pts[k - 1] + (pts[k] - pts[k - 1]) * f).tolist())
    pad = wd + hd + 4; x0, y0 = pts.min(0) - pad; x1, y1 = pts.max(0) + pad
    im = Image.new('RGBA', (int(x1 - x0), int(y1 - y0)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = hexrgb(P.get('color', '#FFFFFF')) + (int(255 * P.get('opacity', 1)),)
    q = [(x - x0, y - y0) for x, y in keep]
    if len(q) > 1: d.line(q, fill=col, width=wd, joint='curve')
    for x, y in (q[0], q[-1]): d.ellipse([x - wd / 2, y - wd / 2, x + wd / 2, y + wd / 2], fill=col)
    if hd and len(q) > 1 and p >= 0.999:
        (ax_, ay_), (bx, by_) = q[-2], q[-1]; ang = np.arctan2(by_ - ay_, bx - ax_)
        for s_ in (0.5236, -0.5236): d.line([(bx, by_), (bx - hd * np.cos(ang + s_), by_ - hd * np.sin(ang + s_))], fill=col, width=wd)
    if P.get('shadow'):
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel('A').filter(ImageFilter.GaussianBlur(P['shadow'][0])).point(lambda v: int(v * P['shadow'][1])))
        sh.alpha_composite(im); im = sh
    return np.array(im), x0, y0


def draw_layer(frame, L, t):
    ui, uo = t - L['t'], L['e'] - t
    if L['kind'] == 'path':
        I, O = L.get('in', {}), L.get('out', {})
        p = ease(I, ui / I['d']) if I.get('d') else 1
        q = ease(O, 1 - uo / O['d']) if O.get('d') and uo < O['d'] else 0
        gx = gy = 0.0
        for m in L.get('move', []):
            if t < m['t']: continue
            f = ease(m, (t - m['t']) / m['d']) if m.get('d', 0) > 0 else 1
            gx += m.get('dx', 0) * f; gy += m.get('dy', 0) * f
        hx, hy = head_off(L, t); gx += hx; gy += hy
        img, x0, y0 = path_sprite(L, p)
        al = L.get('opacity', 1) * (1 - q)
        if p > 0 and al > 0.004: blend(frame, img, L.get('x', 0.5) * W + gx + x0, L.get('y', 0.5) * H + gy + y0 + O.get('dy', 0) * q, min(1, al), 1, O.get('blur', 0) * q)
        return
    gx, gy, gs = 0.0, 0.0, 1.0
    for m in L.get('move', []):
        if t < m['t']: continue
        f = ease(m, (t - m['t']) / m['d']) if m.get('d', 0) > 0 else 1
        gx += m.get('dx', 0) * f; gy += m.get('dy', 0) * f; gs *= 1 + (m.get('scale', 1) - 1) * f
    hx, hy = head_off(L, t); gx += hx; gy += hy
    I, O = L.get('in', {}), L.get('out', {})
    q = ease(O, 1 - uo / O['d']) if O.get('d') and uo < O['d'] else 0
    ax, ay = L.get('x', 0.5) * W + gx, L.get('y', 0.5) * H + gy
    for rgba, xo, yo, k in layer_sprites(L):
        p = ease(I, (ui - k * I.get('stagger', 0)) / I['d']) if I.get('d') else 1
        if p <= 0: continue
        al = L.get('opacity', 1) * (I.get('opacity0', 0) + (1 - I.get('opacity0', 0)) * p) * (1 - q)
        if al <= 0.004: continue
        sc = gs * (I.get('scale', 1) + (1 - I.get('scale', 1)) * p) * (1 + (O.get('scale', 1) - 1) * q)
        bl = I.get('blur', 0) * (1 - p) + O.get('blur', 0) * q
        dx = I.get('dx', 0) * (1 - p) + O.get('track_open', 0) * q * (k - len(SPR[id(L)]) / 2)
        dy = I.get('dy', 0) * (1 - p) + O.get('dy', 0) * q
        img = rgba
        if I.get('wipe') and p < 1:
            img = rgba.copy(); img[:, max(1, int(rgba.shape[1] * p)):, 3] = 0
        x = ax + (xo + dx) * gs; y = ay + (yo + dy) * gs
        blend(frame, img, x, y, min(1, al), sc, bl)


def recomposite(src, newbg, m):
    """put the speaker from src over newbg, only where newbg differs from src (a drawn layer, a dimmed plate): every other pixel
    stays exactly src, so a matte error far from any graphic (a swinging hand, a soft hair edge) never shows. Where something
    was drawn, the soft matte edge of src still holds the old room (I = m*F + (1-m)*B) and a plain m-blend would carry it onto
    the graphic as an outline, so the old room B is estimated from nearby room pixels and taken out of the edge first."""
    M = m[..., None] if m.ndim == 2 else m
    I = src.astype(np.float32)
    c = np.abs(newbg.astype(np.int16) - src.astype(np.int16)).max(2).astype(np.float32)
    if not c.any(): return src
    c = np.clip(cv2.GaussianBlur(np.minimum(c / 8, 1), (0, 0), 3) * 2, 0, 1)[..., None]
    q = cv2.resize(I, (W // 4, H // 4), interpolation=cv2.INTER_AREA); wq = cv2.resize((1 - M[..., 0]) ** 2, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    num = cv2.GaussianBlur(q * wq[..., None], (0, 0), 6); den = cv2.GaussianBlur(wq, (0, 0), 6)[..., None]
    B = cv2.resize(num / np.maximum(den, 1e-3), (W, H), interpolation=cv2.INTER_LINEAR)
    edge = (M > 0.02) & (M < 0.98)
    F = np.where(edge, np.clip((I - (1 - M) * B) / np.maximum(M, 0.05), 0, 255), I)
    return np.clip(I + c * (newbg.astype(np.float32) * (1 - M) + F * M - I), 0, 255).astype(np.uint8)


# ---------- speaker matte for behind layers (ONNX, run only on frames that need it) ----------
# MODNet (one frame at a time, at matte.size) or RVM (recurrent: it carries its state from frame to frame inside a take, so
# the edge does not flicker; at output size with matte.downsample). The model is told apart by its inputs.
MAT = E.get('matte')
_ms = None; _mprev = None; _mlast_seg = None; _mhist = []; _mrec = None


def fill_body(al):
    """matte.fill: a body that runs off the bottom edge is closed there and every hole inside it filled, so the torso never flickers see-through."""
    from scipy import ndimage
    b = al > 0.5; row = np.where(b[-1])[0]; w = al.shape[1]
    if len(row) < 0.2 * w: return al
    p = np.vstack([b, np.zeros((1, w), bool)]); p[-1, row[0]:row[-1] + 1] = True
    holes = ndimage.binary_fill_holes(p)[:-1] & ~b     # only what the body encloses: the outline itself is left to the model, or a halo grows round it
    return np.maximum(al, cv2.GaussianBlur(holes.astype(np.float32), (0, 0), 1) * holes) if holes.any() else al


def matte(frame, seg_i):
    global _ms, _mprev, _mlast_seg, _mhist, _mrec
    if _ms is None:
        import onnxruntime as ort
        pv = [p for p in ('CUDAExecutionProvider', 'CPUExecutionProvider') if p in ort.get_available_providers()]
        so = ort.SessionOptions()     # default ORT spins one thread per core and ignores nice/taskset: cap it to the cores this job may use
        try: ncpu = len(os.sched_getaffinity(0))
        except AttributeError: ncpu = os.cpu_count() or 4
        so.intra_op_num_threads = max(1, min(int(os.environ.get('OMP_NUM_THREADS') or 8), ncpu)); so.inter_op_num_threads = 1
        so.add_session_config_entry('session.intra_op.allow_spinning', '0')
        _ms = ort.InferenceSession(MAT['model'], sess_options=so, providers=pv)
    if _mlast_seg != seg_i: _mhist = []; _mrec = None
    if 'r1i' in [i.name for i in _ms.get_inputs()]:
        z = np.zeros((1, 1, 1, 1), np.float32); r = _mrec or {f'r{i}i': z for i in (1, 2, 3, 4)}
        o = dict(zip([x.name for x in _ms.get_outputs()], _ms.run(None, dict(r, src=(frame.astype(np.float32) / 255).transpose(2, 0, 1)[None],
                                                                                   downsample_ratio=np.array([MAT.get('downsample', 0.25)], np.float32)))))
        al = o['pha'][0, 0]; _mrec = {f'r{i}i': o[f'r{i}o'] for i in (1, 2, 3, 4)}
    else:
        mw, mh = MAT.get('size', [384, 672])
        x = cv2.resize(frame, (mw, mh), interpolation=cv2.INTER_AREA).astype(np.float32) / 127.5 - 1
        al = _ms.run(None, {_ms.get_inputs()[0].name: x.transpose(2, 0, 1)[None]})[0][0, 0]
    if MAT.get('fill'): al = fill_body(al)
    if MAT.get('median', 0) > 1:                     # per-pixel median of the last n mattes (one take): a patch that pops for a frame or two never shows
        _mhist = (_mhist + [al])[-MAT['median']:]
        al = np.median(np.stack(_mhist), 0) if len(_mhist) > 2 else al
    al = cv2.resize(al, (W, H), interpolation=cv2.INTER_LINEAR)
    if MAT.get('guided') and hasattr(cv2, 'ximgproc'):
        g = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
        al = cv2.ximgproc.guidedFilter(g, al.astype(np.float32), MAT['guided'][0], MAT['guided'][1])
    if _mprev is not None and _mlast_seg == seg_i and MAT.get('ema', 0) > 0:   # temporal smoothing inside one take, reset on a cut
        al = MAT['ema'] * _mprev + (1 - MAT['ema']) * al
    _mprev, _mlast_seg = al, seg_i
    ch = MAT.get('choke', 0)                         # pull the soft edge in: a cut-out at 384 px runs a few px wide into the room
    if ch: al = (al - ch) / (1 - 2 * ch)
    return np.clip(al, 0, 1)[..., None]


# ---------- video source: one decoder per segment (with dissolve handles), graded once by lut3d ----------
def dec(s, n0):
    n0 = max(s['s0'], n0)
    return subprocess.Popen([FF, '-v', 'error'] + (['-hwaccel', 'cuda'] if a.cuda else []) + ['-ss', f"{(s['fi'] - s['hp'] + n0 - s['s0']) / FPS:.4f}", '-i', E['mezz'],
                             '-frames:v', str(s['s1'] - n0), '-vf', f"lut3d={E['lut']}:interp=tetrahedral", '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                            stdout=subprocess.PIPE, bufsize=SW * SH * 3)


DEC = {}
fsz = SW * SH * 3


HOLD = {}


def src_frame(k):
    b = subprocess.run([FF, '-v', 'error', '-ss', f'{k / FPS:.4f}', '-i', E['mezz'], '-frames:v', '1', '-vf', f"lut3d={E['lut']}:interp=tetrahedral",
                        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    return np.frombuffer(b[:fsz], np.uint8).reshape(SH, SW, 3) if len(b) >= fsz else None


def frame_of(i, n):
    if i not in DEC: DEC[i] = dec(segs[i], n)
    b = DEC[i].stdout.read(fsz)
    img = np.frombuffer(b, np.uint8).reshape(SH, SW, 3) if len(b) == fsz else None
    s = segs[i]; k = s['fi'] - s['hp'] + (max(s['s0'], n) - s['s0']) if 's0' in s else None
    cv = next(((a_, b_) for a_, b_ in s['cover'] if k is not None and a_ <= k < b_), None)
    if cv is None:
        if img is not None: HOLD[i] = img
        return img
    if HOLD.get(('c', i)) != cv:      # a card inside the take: the speaker's last frame before it (or the first after it, at a take start) holds
        HOLD[i] = HOLD[i] if i in HOLD else src_frame(cv[1]); HOLD[('c', i)] = cv
    return HOLD[i]


# ---------- --fit: words behind the speaker and pinned stills, measured against the speaker's cut-out and moved where the edit asks ----------
# layer.legible (or edit.legible): the share of a behind word's letters that must stay clear of the speaker; layers with with=<id>
# (a strike, a ring) move with their word. overlay.clear: the share of the still that may sit over the speaker; edit.ui: boxes
# [x0, y0, x1, y1] (0..1) the platform draws over (none by default: an organic reel has no published safe zone). The engine only
# measures and moves; how much hides behind the head, and where a logo belongs, is the edit's call.
def grab(n):
    sg = next((s for s in segs if s['o'] <= n < s['o'] + s['len']), segs[-1]); sf = sg['fi'] + (n - sg['o'])
    b = subprocess.run([FF, '-v', 'error', '-ss', f'{sf / FPS:.4f}', '-i', E['mezz'], '-frames:v', '1', '-vf', f"lut3d={E['lut']}:interp=tetrahedral",
                        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    return warp(np.frombuffer(b[:fsz], np.uint8).reshape(SH, SW, 3), *view(sg, n, n / FPS))


def still_matte(img, key):
    global _mprev
    _mprev = None
    for _ in range(3): m_ = matte(img, ('fit', key))       # a recurrent model settles on the same picture in a few passes
    return m_[..., 0]


def moved_at(L, t):
    gx = gy = 0.0
    for mv in L.get('move', []):
        if t >= mv['t']:
            f = ease(mv, (t - mv['t']) / mv['d']) if mv.get('d', 0) > 0 else 1
            gx += mv.get('dx', 0) * f; gy += mv.get('dy', 0) * f
    hx, hy = head_off(L, t)
    return gx + hx, gy + hy


def glyph_alpha(L, t, s):
    """the settled letters of a text layer at size scale s: (alpha float HxW, bbox)."""
    L2 = dict(L, text=dict(L['text'], size=max(8, int(round(L['text']['size'] * s))), shadow=None), **{'in': {}, 'out': {}})
    g = np.zeros((H, W), np.float32); gx, gy = moved_at(L, t); ax, ay = L.get('x', .5) * W + gx, L.get('y', .5) * H + gy
    for rgba, xo, yo, _ in layer_sprites(L2):
        x, y = int(round(ax + xo)), int(round(ay + yo)); h_, w_ = rgba.shape[:2]
        X0, Y0, X1, Y1 = max(x, 0), max(y, 0), min(x + w_, W), min(y + h_, H)
        if X1 > X0 and Y1 > Y0: g[Y0:Y1, X0:X1] = np.maximum(g[Y0:Y1, X0:X1], rgba[Y0 - y:Y1 - y, X0 - x:X1 - x, 3] / 255.0)
    SPR.pop(id(L2), None)
    ys, xs = np.nonzero(g > 0.5)
    return g, ((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1) if len(xs) else None)


def fit():
    from concurrent.futures import ThreadPoolExecutor
    for L in LAY:                                       # a re-run starts from what the edit wrote, never from the last fit
        for k_, v_ in L.pop('fit0', {}).items():
            if k_ == 'size': L['text']['size'] = v_
            elif k_ == 'pts': L['path']['pts'] = v_
            else: L[k_] = v_
    for o_ in E.get('overlays', []):
        for k_, v_ in o_.pop('fit0', {}).items(): o_[k_] = v_
    words = [L for L in LAY if L.get('behind') and L['kind'] == 'text' and L.get('with') is None and L.get('legible', E.get('legible')) is not None]   # a word that swaps into another's seat moves with it
    ovs = [o_ for o_ in E.get('overlays', []) if o_.get('clear') is not None]
    want = {}
    group = [[L] + [m_ for m_ in LAY if m_ is not L and m_['kind'] == 'text' and m_.get('with') is not None and m_.get('with') == L.get('id')] for L in words]
    for i, Ls in enumerate(group):                      # a word and the words that take its seat are measured together
        want[('w', i)] = []
        for L in Ls:
            a0 = L['t'] + L.get('in', {}).get('d', 0) + L.get('in', {}).get('stagger', 0) * len(L['text']['text']); a1 = L['e'] - L.get('out', {}).get('d', 0)
            if a1 <= a0: a0, a1 = L['t'], L['e']
            want[('w', i)] += [(L, int((a0 + (a1 - a0) * f) * FPS)) for f in (0.1, 0.4, 0.7, 0.95)]
    for i, o_ in enumerate(ovs):
        t0, t1 = o_.get('t', 0), min(o_.get('e', DUR), DUR)
        want[('o', i)] = [min(NF - 1, int((t0 + (t1 - t0) * f) * FPS)) for f in np.linspace(0.05, 0.95, 8)]
    ns = sorted({(x[1] if isinstance(x, tuple) else x) for v in want.values() for x in v})
    if not ns: return {'fit': 'nothing to measure'}
    if not MAT: sys.exit('--fit measures against the speaker: edit.json needs "matte"')
    t_ = time.time()
    with ThreadPoolExecutor(16) as ex: pics = dict(zip(ns, ex.map(grab, ns)))
    t_grab = time.time() - t_
    M = {n: still_matte(pics[n], n) for n in ns}
    t_mat = time.time() - t_ - t_grab
    ui = [np.array(b) * [W, H, W, H] for b in E.get('ui', [])]
    def cap_boxes(t0, t1):
        out = []
        for c in E.get('captions', []):
            if c['t'] < t1 and c['e'] > t0:
                arr, x, y = render_caption(c); out.append((x, y, x + arr.shape[1], y + arr.shape[0]))
        return out
    rep = {'words': [], 'overlays': []}
    M4 = {n: cv2.resize(M[n], (W // 4, H // 4), interpolation=cv2.INTER_AREA) for n in ns}
    def seen(G, S, dx, dy, q):
        out = []
        for (g, (bx0, by0, bx1, by1)), n in zip(G, S):
            if q == 1: gg, mm = g[by0:by1, bx0:bx1], M[n][by0 + dy:by1 + dy, bx0 + dx:bx1 + dx]
            else: gg, mm = g[by0 // 4:by1 // 4, bx0 // 4:bx1 // 4], M4[n][(by0 + dy) // 4:(by1 + dy) // 4, (bx0 + dx) // 4:(bx1 + dx) // 4]
            out.append(float((gg * (1 - mm)).sum() / max(gg.sum(), 1e-6)))
        return out
    for i, L in enumerate(words):
        goal = L.get('legible', E.get('legible'))
        LS = want[('w', i)]; S = [n for _, n in LS]; scales = [1.0, 0.92, 0.84, 0.76] if goal is not None else [1.0]
        caps_ = cap_boxes(L['t'], L['e'])
        best = None; v_was = None; Gs = {}
        for s in scales:
            G = [glyph_alpha(L_, n / FPS, s) for L_, n in LS]
            if any(b is None for _, b in G): continue
            Gs[s] = G; G4 = [(cv2.resize(g, (W // 4, H // 4), interpolation=cv2.INTER_AREA), b) for g, b in G]
            if s == 1.0: v_was = float(np.mean(seen(G, S, 0, 0, 1)))
            cy = np.mean([(b[1] + b[3]) / 2 for _, b in G])
            top = max([0.02 * H] + [b[3] + 0.006 * H for b in caps_ if (b[1] + b[3]) / 2 < cy])
            dys = range(0, -int(0.16 * H), -8) if goal is not None else [0]
            dxs = sorted(range(-int(0.2 * W), int(0.2 * W) + 1, 12), key=abs) if goal is not None else [0]
            for dy in dys:
                if dy and min(b[1] for _, b in G) + dy < top: break
                for dx in dxs:
                    if min(b[0] for _, b in G) + dx < 0.02 * W or max(b[2] for _, b in G) + dx > 0.98 * W: continue
                    vis = seen(G4, S, dx, dy, 4); v = float(np.mean(vis))
                    cost = abs(dx) / W + 1.5 * abs(dy) / H + 0.6 * (1 - s); ok = goal is None or v >= goal
                    cand = (not ok, cost if ok else -v, dx, dy, s)
                    if best is None or cand < best: best = cand
        if best is None: continue
        dx, dy, s = best[2:]; vis = seen(Gs[s], S, dx, dy, 1); v, vmin = float(np.mean(vis)), min(vis)
        r = {'t': round(L['t'], 2), 'text': ' / '.join(L_['text']['text'] for L_ in group[i]), 'legible': goal, 'visible_was': None if v_was is None else round(v_was, 3), 'visible': round(v, 3), 'visible_min': round(vmin, 3)}
        if (dx, dy, s) != (0, 0, 1.0):
            mates = [L] + [m_ for m_ in LAY if m_ is not L and m_.get('with') is not None and m_.get('with') == L.get('id')]
            for m_ in mates:
                f0 = {'x': m_.get('x', .5), 'y': m_.get('y', .5)}
                if m_['kind'] == 'text': f0['size'] = m_['text']['size']; m_['text']['size'] = max(8, int(round(m_['text']['size'] * s)))
                if m_['kind'] == 'path': f0['pts'] = m_['path']['pts']; m_['path']['pts'] = [[p[0] * s, p[1] * s] for p in m_['path']['pts']]
                m_['fit0'] = f0; m_['x'] = round(f0['x'] + dx / W, 4); m_['y'] = round(f0['y'] + dy / H, 4)
            r.update(moved={'dx': round(dx / W, 3), 'dy': round(dy / H, 3), 'scale': s}, mates=len(mates) - 1)
        if goal is not None and v < goal: r['short'] = True            # the best the frame allows is named; the edit can pick another word or seat
        rep['words'].append(r)
    for i, o_ in enumerate(ovs):
        S = want[('o', i)]; mean_m = cv2.resize(np.mean([M[n] for n in S], 0), (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        ii = cv2.integral(mean_m.astype(np.float64))
        im = Image.open(o_['file']); w_ = int(o_['w']); h_ = int(im.height * w_ / im.width); q = 4
        boxes = cap_boxes(o_.get('t', 0), o_.get('e', DUR)) + [tuple(b) for b in ui]
        def over(cx, cy):
            X0, Y0 = int((cx - w_ / 2) / q), int((cy - h_ / 2) / q); X1, Y1 = X0 + max(1, w_ // q), Y0 + max(1, h_ // q)
            return (ii[Y1, X1] - ii[Y0, X1] - ii[Y1, X0] + ii[Y0, X0]) / ((X1 - X0) * (Y1 - Y0))
        def hits(cx, cy):
            return any(cx + w_ / 2 > b[0] and cx - w_ / 2 < b[2] and cy + h_ / 2 > b[1] and cy - h_ / 2 < b[3] for b in boxes)
        ox, oy = o_['x'] * W, o_['y'] * H; m0 = over(min(max(ox, w_ / 2 + q), W - w_ / 2 - q), min(max(oy, h_ / 2 + q), H - h_ / 2 - q))
        cands = []
        for cy in range(int(h_ / 2) + 24, int(H - h_ / 2) - 24, 12):
            for cx in range(int(w_ / 2) + 24, int(W - w_ / 2) - 24, 12):
                v = over(cx, cy)
                if v <= o_['clear'] and not hits(cx, cy): cands.append((np.hypot(cx - ox, cy - oy), cx, cy, v))
        r = {'file': os.path.basename(o_['file']), 'clear': o_['clear'], 'over_speaker': round(float(m0), 3), 'in_ui_or_caption': bool(hits(ox, oy))}
        if (m0 > o_['clear'] or hits(ox, oy)) and cands:
            d, cx, cy, v = min(cands); o_['fit0'] = {'x': o_['x'], 'y': o_['y']}; o_['x'], o_['y'] = round(cx / W, 4), round(cy / H, 4)
            r.update(moved_to=[o_['x'], o_['y']], over_speaker_after=round(float(v), 3))
        elif m0 > o_['clear'] or hits(ox, oy): r['short'] = True
        rep['overlays'].append(r)
    rep['secs'] = {'grab': round(t_grab, 1), 'matte': round(t_mat, 1), 'all': round(time.time() - t_, 1)}
    E['fit'] = rep
    json.dump(E, open(a.edit, 'w'), ensure_ascii=False, indent=1)
    return rep


if a.fit:
    print(json.dumps(fit(), ensure_ascii=False)); sys.exit(0)

tmpv = a.reuse_video or os.path.splitext(a.out)[0] + '.video.mp4'
enc = None if a.reuse_video else subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        ] + (['-c:v', 'h264_nvenc', '-preset', 'p6', '-tune', 'hq', '-rc', 'vbr', '-cq', '18', '-b:v', '0', '-maxrate', '20M', '-bufsize', '40M']
                             if a.encoder == 'h264_nvenc' else ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-maxrate', '20M', '-bufsize', '40M']) + ['-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                        '-color_range', 'tv', tmpv], stdin=subprocess.PIPE)

caps = E.get('captions', []); accs = E.get('accents', []); fx = E.get('fx', {})
COLF = {}                                         # column pictures from files, decoded once at column size
for cl in fx.get('columns', []):
    k_ = len(cl['items']); g_ = cl.get('gap', 12); cw_ = (W - g_ * (k_ - 1)) // k_ // 2 * 2
    for it in cl['items']:
        if it.get('file') and (it['file'], cw_) not in COLF:
            still = it['file'].lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
            x_, y_, w_, h_ = it.get('crop') or cover_crop(it['file'], cw_ / H, *it.get('focus', [0.5, 0.5]))
            src_in = ['-loop', '1', '-t', str(cl['d'] + 0.1), '-i', it['file']] if still else ['-ss', str(it.get('in', 0)), '-t', str(cl['d'] + 0.1), '-i', it['file']]
            raw = subprocess.run([FF, '-v', 'error'] + src_in + ['-vf', f'crop={w_}:{h_}:{x_}:{y_},scale={cw_}:{H}:flags=lanczos,fps={FPS}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                 capture_output=True).stdout
            if not raw: sys.exit(f"column picture {it['file']}: ffmpeg gave no frames")
            COLF[(it['file'], cw_)] = np.frombuffer(raw, np.uint8).reshape(-1, H, cw_, 3)


def draw_columns(frame, cl, t, n):
    """items: [{file, in, focus} | {speaker: true, dx}]; gap px of gap_color; each column slides up in turn (stagger s, in s), out the same way"""
    k_ = len(cl['items']); g_ = cl.get('gap', 12); cw_ = (W - g_ * (k_ - 1)) // k_ // 2 * 2
    out = np.empty_like(frame); out[:] = hexrgb(cl.get('gap_color', '#0b0b0b'))
    u, uo = t - cl['t'], cl['t'] + cl['d'] - t
    hc = head_at(n); hx = hc[0] if hc else W / 2
    for j, it in enumerate(cl['items']):
        p = ease({'ease': 'expoInOut'}, min(1, max(0, (u - j * cl.get('stagger', 0.08)) / cl.get('in', 0.45)), max(0, uo - (k_ - 1 - j) * cl.get('stagger', 0.08)) / cl.get('in', 0.45)))
        if p <= 0: continue
        if it.get('file'):
            F_ = COLF[(it['file'], cw_)]; pic = F_[min(int(u * FPS), len(F_) - 1)]
        else:                                     # the speaker, cut round the head (dx shifts the cut, so two columns can show two halves)
            sx = int(min(max(hx + it.get('dx', 0) * W - cw_ / 2, 0), W - cw_)); pic = frame[:, sx:sx + cw_]
        x0_ = j * (cw_ + g_); dy = int(round((1 - p) * H * (1 if j % 2 == 0 else -1) * cl.get('slide', 1)))
        ys, ye = max(0, dy), min(H, H + dy)
        if ye > ys: out[ys:ye, x0_:x0_ + cw_] = pic[ys - dy:ye - dy]
    return out


def face_span_y(n):
    """(hair top, chin) of the face as output-frame fractions at output frame n; None without a face track."""
    if FSM is None: return None
    act = [s for s in segs if s['o'] <= n < s['o'] + s['len']] or [s for s in segs if s['s0'] <= n < s['s1']]
    if not act: return None
    sg = act[0]; x0, y0, ww = view(sg, n, n / FPS)
    sf = min(max(sg['fi'] + (n - sg['o']), 0), len(FSM) - 1)
    if HAS[sf] < 0.5: return None
    k = (W / ww) / H
    return (FSM[sf][3] - (FOL or {}).get('hair_k', 0.35) * FSM[sf][4] - y0) * k, (FSM[sf][3] + FSM[sf][4] - y0) * k


def head_box(n):
    """the speaker's head (hair top to chin, cheek to cheek) as an output-pixel box at output frame n; None without a face."""
    if FSM is None: return None
    act = [s for s in segs if s['o'] <= n < s['o'] + s['len']] or [s for s in segs if s['s0'] <= n < s['s1']]
    if not act: return None
    sg = act[0]; x0, y0, ww = view(sg, n, n / FPS)
    sf = min(max(sg['fi'] + (n - sg['o']), 0), len(FSM) - 1)
    if HAS[sf] < 0.5: return None
    k = W / ww; ex, io, top, hh = FSM[sf][0], FSM[sf][2], FSM[sf][3], FSM[sf][4]
    return ((ex - 1.15 * io - x0) * k, (top - (FOL or {}).get('hair_k', 0.35) * hh - y0) * k, (ex + 1.15 * io - x0) * k, (top + hh - y0) * k)


def chin_y(n):
    """lowest point of the face (output-frame fraction) at output frame n; None without a face track."""
    v = face_span_y(n)
    return v and v[1]


SAFE_Y = (E['safe'][1], E['safe'][3]) if E.get('safe') else (0.12, 0.86)     # edit.json "safe": [x0, y0, x1, y1] (0..1), as yerlesim.py reads it
def rest_box(L):
    """a still layer's box in output pixels where it rests (None for kinds without sprites)."""
    sp = layer_sprites(L) if L.get('kind') in ('text', 'image', 'bar') else []
    if not sp: return None
    ax, ay = L.get('x', 0.5) * W, L.get('y', 0.5) * H
    return (min(ax + xo for _, xo, yo, _k in sp), min(ay + yo for _, xo, yo, _k in sp),
            max(ax + xo + r.shape[1] for r, xo, yo, _k in sp), max(ay + yo + r.shape[0] for r, xo, yo, _k in sp))


def reserved(t0, t1):
    """boxes a caption must stay out of over [t0, t1): every layer in front of the speaker on screen then (a panel, a title, a card)."""
    out = []
    for L in E.get('layers', []):
        if L.get('behind') or L.get('track') or not (L['t'] < t1 and t0 < L['e']): continue
        b = rest_box(L)
        if b: out.append(b)
    return out


def _hit(a, b): return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


ON_FACE, CAPS_MOVED = [], []
if E['caption'].get('below_face') is not None and FSM is not None:      # never on the face: each page sits under the chin over its own span,
    SAFE_TOP = SAFE_Y[0] * H                                              # or above the hair when the bottom of the frame has no room
    for c in caps:
        arr, x, y = render_caption(c)
        fs = [face_span_y(n) for n in range(int(c['t'] * FPS), max(int(c['t'] * FPS) + 1, int(c['e'] * FPS)))]
        fs = [v for v in fs if v is not None]
        if not fs: continue
        top = (max(v[1] for v in fs) + E['caption']['below_face']) * H
        if y < top:
            lim = H * E['caption'].get('y_max', 0.86) - arr.shape[0]
            rz = reserved(c['t'], c['e']); clear = lambda yy: not any(_hit((x, yy, x + arr.shape[1], yy + arr.shape[0]), r) for r in rz)
            if top <= lim and clear(top): CAP_CACHE[id(c)] = (arr, x, int(top)); continue
            above = (min(v[0] for v in fs) - E['caption']['below_face']) * H - arr.shape[0]
            if above >= SAFE_TOP and clear(above): CAP_CACHE[id(c)] = (arr, x, int(above)); CAPS_MOVED.append(round(c['t'], 2))
            else: ON_FACE.append(round(c['t'], 2)); CAP_CACHE[id(c)] = (arr, x, int(lim))   # no room above or below: named in the report


HEAD_IN_PANEL = []       # seconds where the hair still reaches into a top panel (a face too big to fit under it): named in the report
if FSM is not None:
    for n in range(0, sum(s_['len'] for s_ in segs), 3):
        hb_, pb_ = head_box(n), panel_b(n / FPS)
        if hb_ and pb_ and hb_[1] < pb_ * H - 4 and not (HEAD_IN_PANEL and n / FPS - HEAD_IN_PANEL[-1] < 1): HEAD_IN_PANEL.append(round(n / FPS, 2))
LAYERS_MOVED_OFF_FACE, LAYERS_ON_FACE = [], []
if FSM is not None:      # a text layer in front of the speaker never sits on the head: it moves above the hair, else under the chin, else beside the head, inside the
    SX0, SX1 = ((E['safe'][0], E['safe'][2]) if E.get('safe') else (0.04, 0.96)); SX0, SX1 = SX0 * W, SX1 * W
    SY0, SY1 = SAFE_Y[0] * H, SAFE_Y[1] * H                                                    # free frame and clear of the captions;
    def _cap_boxes(t0, t1):                                                                     # "on_face": true keeps one there on purpose
        out = []
        for c in caps:
            if c['t'] < t1 and t0 < c['e']:
                arr, x, y = render_caption(c); out.append((x, y, x + arr.shape[1], y + arr.shape[0]))
        return out
    hit = lambda a, b: a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
    for li, L in enumerate(LAY):
        if L.get('kind') != 'text' or L.get('behind') or L.get('track') or L.get('full') or L.get('on_face') or L.get('move'): continue
        bx = rest_box(L)
        if not bx: continue
        if any(Q is not L and Q['kind'] != 'text' and not Q.get('behind') and Q['t'] <= L['t'] + 0.05 and L['e'] <= Q['e'] + 0.05
               and (r := rest_box(Q)) and r[0] <= bx[0] + 8 and r[1] <= bx[1] + 8 and bx[2] <= r[2] + 8 and bx[3] <= r[3] + 8 for Q in LAY): continue   # text on its own card goes with the card
        hb = [head_box(n) for n in range(int(L['t'] * FPS), max(int(L['t'] * FPS) + 1, int(L['e'] * FPS)), 5)]
        hb = [b for b in hb if b and hit(b, bx)]
        if not hb: continue
        u = (min(b[0] for b in hb), min(b[1] for b in hb), max(b[2] for b in hb), max(b[3] for b in hb)); hgt = bx[3] - bx[1]; gap = 0.015 * H
        others = [Q for q, Q in enumerate(LAY) if q != li and not Q.get('behind') and Q['t'] < L['e'] and L['t'] < Q['e']
                  and not (Q['kind'] == 'bar' and Q['bar']['w'] >= 0.9 * W)]          # a full-width panel is the ground titles sit on, not in the way
        cb = _cap_boxes(L['t'], L['e']) + [r for r in map(rest_box, others) if r]
        sg = 0.04 * W                                                                 # hair reaches wider than the face box
        sides = sorted((u[0] - sg - bx[2], u[2] + sg - bx[0]), key=abs)               # then beside the head, the nearer side first,
        lift = sorted(range(int(SY0 - bx[1]), int(SY1 - bx[3]) + 1, 20), key=abs)     # at the height nearest the edit's that is free
        for dx, dy in [(0, u[1] - gap - bx[3]), (0, u[3] + gap - bx[1])] + [(d, y_) for y_ in lift for d in sides]:
            nb = (bx[0] + dx, bx[1] + dy, bx[2] + dx, bx[3] + dy)
            if SY0 <= nb[1] and nb[3] <= SY1 and SX0 <= nb[0] and nb[2] <= SX1 and not hit(nb, u) and not any(hit(nb, c) for c in cb):
                L['x'] = round(L.get('x', 0.5) + dx / W, 4); L['y'] = round(L.get('y', 0.5) + dy / H, 4); LAYERS_MOVED_OFF_FACE.append(li); break
        else: LAYERS_ON_FACE.append(li)


def _rl(rgb):
    """relative luminance (WCAG) of an array of 0..255 RGB values."""
    v = rgb.astype(np.float32) / 255.0
    v = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
    return v[..., 0] * 0.2126 + v[..., 1] * 0.7152 + v[..., 2] * 0.0722


def _cr(a, b): return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def caption_contrast(arr, x, y, frame, tile=120):
    """worst contrast (WCAG ratio) a caption page shows over this frame, tile by tile: the letters' core against their own edge, or that
    edge against the picture right outside it (so a stroke or shadow counts). Large text reads from 3:1."""
    h, w = arr.shape[:2]
    X0, Y0, X1, Y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if X1 <= X0 or Y1 <= Y0: return 99
    sp = arr[Y0 - y:Y1 - y, X0 - x:X1 - x]; a = sp[..., 3:4].astype(np.float32) / 255
    comp = frame[Y0:Y1, X0:X1].astype(np.float32) * (1 - a) + sp[..., :3].astype(np.float32) * a
    L = _rl(comp); m = (sp[..., 3] > 128).astype(np.uint8)
    core = cv2.erode(m, np.ones((5, 5), np.uint8)); edge = m - cv2.erode(m, np.ones((3, 3), np.uint8))
    ring = cv2.dilate(m, np.ones((9, 9), np.uint8)) - m
    worst = 99
    for c0 in range(0, X1 - X0, tile):
        sl = np.s_[:, c0:c0 + tile]
        if core[sl].sum() < 40 or ring[sl].sum() < 40: continue
        lc, le, lr = (float(np.median(L[sl][q[sl] > 0])) for q in (core, edge, ring))
        worst = min(worst, max(_cr(lc, le), _cr(le, lr), _cr(lc, lr)))
    return worst


def with_halo(arr, light):
    """the page with an outline + soft shadow round its letters (dark under light letters, light under dark ones)."""
    r = max(3, int(arr.shape[0] / 40))
    pad = np.pad(arr, ((r * 2, r * 2), (r * 2, r * 2), (0, 0)))
    a = pad[..., 3]
    halo = cv2.GaussianBlur(cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))), (0, 0), r * 0.6)
    out = np.zeros_like(pad); out[..., :3] = 20 if light else 240; out[..., 3] = (halo.astype(np.float32) * 0.92).astype(np.uint8)
    fa = a[..., None].astype(np.float32) / 255; oa = out[..., 3:4].astype(np.float32) / 255
    na = fa + oa * (1 - fa)
    rgb = (pad[..., :3] * fa + out[..., :3] * oa * (1 - fa)) / np.maximum(na, 1e-6)
    return np.dstack([rgb, na * 255]).clip(0, 255).astype(np.uint8), r * 2


def busy(arr, x, y, frame):
    """how busy the picture right round the letters is (spread of its luminance, 0..0.5): a print, a crowd, foliage."""
    h, w = arr.shape[:2]; X0, Y0, X1, Y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if X1 <= X0 or Y1 <= Y0: return 0.0
    m = (arr[Y0 - y:Y1 - y, X0 - x:X1 - x, 3] > 60).astype(np.uint8)
    ring = cv2.dilate(m, np.ones((25, 25), np.uint8)) > 0
    L = _rl(frame[Y0:Y1, X0:X1])[ring]
    return float(L.std()) if L.size > 200 else 0.0


def with_box(arr, light):
    """the page on a rounded backing box (dark under light letters, light under dark ones): for a picture too busy for an outline."""
    a = arr[..., 3]; ys, xs = np.nonzero(a > 40)
    if not len(ys): return arr
    r = max(10, int(arr.shape[0] / 12))
    im = Image.new('RGBA', (arr.shape[1], arr.shape[0]), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([max(0, xs.min() - r), max(0, ys.min() - r // 2), min(arr.shape[1] - 1, xs.max() + r), min(arr.shape[0] - 1, ys.max() + r // 2)],
                                         radius=r, fill=((16, 16, 16) if light else (240, 240, 240)) + (200,))
    im.alpha_composite(Image.fromarray(arr)); return np.array(im)


CAP_LEG = {}            # id(page) -> last check time; a page that reads below 3:1 gets a halo (a gate fixes before it refuses)
CAPS_HALO, CAPS_BOX = [], []
CAP_PLAIN = {}


n_out = 0; r0, r1 = int(round(sl[0] * FPS)), int(round(sl[1] * FPS))
WARM = 12
for n in range(0 if a.reuse_video else NF):
    if n >= r1: break
    if n < r0 - WARM: continue
    t = n / FPS
    act = [i for i, s in enumerate(segs) if s['s0'] <= n < s['s1']]
    imgs = [(i, frame_of(i, n)) for i in act]       # a decoder opens on the first frame it is asked for
    if n < r0:                                      # the warm-up frames before a slice: only the matte runs, to carry its state in
        if MAT and imgs and imgs[-1][1] is not None and (any(L.get('behind') and L['t'] <= t < L['e'] for L in LAY)
                                                         or any(p['t'] <= t < p['t'] + p['d'] for p in fx.get('bgplate', []))):
            matte(warp(imgs[-1][1], *view(segs[imgs[-1][0]], n, t)), imgs[-1][0])
        continue
    outs = []
    for i, img in imgs:
        if img is None: continue
        x0, y0, ww = view(segs[i], n, t)
        s_prev = cam_at(t - 1 / FPS)[0]; s_now = cam_at(t)[0]
        if abs(s_now - s_prev) > fx.get('camblur_ds', 0.006) and not any(abs(t - c) < 1.5 / FPS for c in cut_times):
            acc = np.zeros((H, W, 3), np.float32)       # camera-velocity motion blur: 3 sub-samples when the zoom moves fast
            for j in range(3): acc += warp(img, *view(segs[i], n, t - (j / 3) / FPS))
            outs.append((i, (acc / 3).astype(np.uint8)))
        else:
            outs.append((i, warp(img, x0, y0, ww)))
    if not outs: break
    if len(outs) == 2:                              # dissolve across the joint, eased
        sg = segs[outs[1][0]]; k = {'bez': E.get('joint_bez', [0.42, 0, 0.58, 1])}
        al_ = ease(k, (n - sg['s0'] + 0.5) / max(1, sg['x']))
        frame = cv2.addWeighted(outs[0][1], 1 - al_, outs[1][1], al_, 0)
    else:
        frame = np.ascontiguousarray(outs[0][1])
    seg_i = outs[-1][0]
    for sf in fx.get('soften', []):                 # soft -> sharp (after an insert, or an opening rack focus)
        if sf['t'] <= t < sf['t'] + sf['d']:
            r = sf['r'] * (1 - (t - sf['t']) / sf['d']) ** 2
            if r > 0.4: frame = cv2.GaussianBlur(frame, (0, 0), r)
    for so in fx.get('soft', []):                   # soft look: blur, a slight fade (lifted toward a colour) and a smooth zoom, ramped in and out
        if so['t'] <= t < so['t'] + so['d']:
            u = (t - so['t']) / so['d']; rp = so.get('ramp', min(0.4, so['d'] / 3))
            r = ease({'ease': 'sineInOut'}, min(1, (t - so['t']) / rp, (so['t'] + so['d'] - t) / rp)) if rp > 0 else 1
            z0, z1 = so.get('zoom', [1.0, 1.0]); z = z0 + (z1 - z0) * ease(so, u)
            if abs(z - 1) > 1e-3:
                hc = head_at(n) if so.get('at') == 'head' else None; cx_, cy_ = hc or (W / 2, H / 2)
                frame = cv2.warpAffine(frame, np.float32([[z, 0, (1 - z) * cx_], [0, z, (1 - z) * cy_]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            if so.get('blur', 0) * r > 0.4: frame = cv2.GaussianBlur(frame, (0, 0), so['blur'] * r)
            if so.get('fade', 0) * r > 0.002:
                c = np.array(hexrgb(so.get('color', '#ffffff')), np.float32)
                frame = (frame.astype(np.float32) * (1 - so['fade'] * r) + c * so['fade'] * r).astype(np.uint8)
    for bc in fx.get('blurcol', []):                # one sharp column over the same frame blurred and dimmed; the column opens from full width over ramp s
        if bc['t'] <= t < bc['t'] + bc['d']:
            rp = bc.get('ramp', 0.35); r = ease({'ease': 'sineInOut'}, min(1, (t - bc['t']) / rp, (bc['t'] + bc['d'] - t) / rp)) if rp > 0 else 1
            cwid = int(W * (1 - (1 - bc.get('w', 0.62)) * r)) // 2 * 2
            hc = head_at(n) if bc.get('x', 'head') == 'head' else None; cx_ = hc[0] if hc else bc.get('x', 0.5) * W if bc.get('x') != 'head' else W / 2
            x0_ = int(min(max(cx_ - cwid / 2, 0), W - cwid))
            bz = 1.12; bg = cv2.warpAffine(frame, np.float32([[bz, 0, (1 - bz) * W / 2], [0, bz, (1 - bz) * H / 2]]), (W, H), flags=cv2.INTER_LINEAR)
            bg = cv2.GaussianBlur(cv2.resize(bg, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), bc.get('blur', 24) / 4)
            bg = (cv2.resize(bg, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) * (1 - (1 - bc.get('dim', 0.6)) * r)).astype(np.uint8)
            bg = cv2.addWeighted(frame, 1 - r, bg, r, 0)
            bg[:, x0_:x0_ + cwid] = frame[:, x0_:x0_ + cwid]
            if bc.get('line', 0) and r > 0.01:
                lc = hexrgb(bc.get('line_color', '#ffffff')); lw_ = int(bc['line'])
                for xx in (x0_, x0_ + cwid - lw_): bg[:, max(0, xx):xx + lw_] = (bg[:, max(0, xx):xx + lw_] * (1 - r) + np.array(lc) * r).astype(np.uint8)
            frame = bg
    for cl in fx.get('columns', []):                # the frame split into columns, each its own picture; they slide in one after another
        if cl['t'] <= t < cl['t'] + cl['d']:
            frame = draw_columns(frame, cl, t, n)
    for bw in fx.get('bw', []):                     # statement beat plate: dimmed black and white
        if bw['t'] <= t < bw['t'] + bw['d']:
            g = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            frame = (np.dstack([g, g, g]).astype(np.float32) * bw.get('dim', 0.45)).astype(np.uint8)
    live = [L for L in LAY if L['t'] <= t < L['e']]
    back = [L for L in live if L.get('behind')]
    plate = [p for p in fx.get('bgplate', []) if p['t'] <= t < p['t'] + p['d']]
    if (back or plate) and MAT:                     # graphics behind the speaker: draw them, then put the person back on top
        fg = frame.copy(); m = matte(fg, seg_i)
        for p in plate:                             # the room behind the speaker: dimmed / desaturated, ramped in and out over p.ramp s
            r = min(1, (t - p['t']) / p['ramp'], (p['t'] + p['d'] - t) / p['ramp']) if p.get('ramp') else 1
            g = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)[..., None].astype(np.float32)
            bgp = (g + (frame.astype(np.float32) - g) * p.get('sat', 1)) * p.get('dim', 1)
            frame = (frame.astype(np.float32) * (1 - r) + bgp * r).astype(np.uint8)
        for L in back: draw_layer(frame, L, t)
        frame = recomposite(fg, frame, m)
    elif back or plate:
        sys.exit('a behind layer or a bgplate needs "matte" (the cut-out model) in edit.json')
    for L in live:
        if not L.get('behind') and not L.get('over_caps'): draw_layer(frame, L, t)
    ins = active_insert(t)
    if ins is not None:
        draw_insert(frame, frame.copy(), ins, t)
    hide = any(c.get('hide_caps') and c['t'] <= t < c['e'] for c in accs) or any(L.get('hide_caps') for L in live)
    cs = E['caption']
    for c in caps:
        if not hide and c['t'] <= t < c['e']:
            arr, x, y = render_caption(c)
            if cs.get('auto_contrast', True) and CAP_LEG.get(id(c), -9) <= t - 0.1:     # the picture under a page can change mid-page (a blur ends)
                CAP_LEG[id(c)] = t
                if caption_contrast(arr, x, y, frame) < 3.0:
                    if t > c['t'] + 0.05: CAP_PLAIN[id(c)] = (arr, x, y, t)              # fixed mid-page: the outline / box fades in, never pops
                    lum = _rl(arr[..., :3][arr[..., 3] > 200]); arr2, d = with_halo(arr, float(np.median(lum)) > 0.35 if lum.size else True)
                    if busy(arr, x, y, frame) > 0.14:      # an outline does not carry letters over a busy picture: a backing box does
                        arr2 = with_box(arr2, float(np.median(lum)) > 0.35 if lum.size else True); CAPS_BOX.append(round(c['t'], 2))
                    CAP_CACHE[id(c)] = (arr2, x - d, y - d); arr, x, y = arr2, x - d, y - d; CAP_LEG[id(c)] = 1e9; CAPS_HALO.append(round(c['t'], 2))
            fade = cs.get('fade', 0)
            u = (t - c['t']) / fade if fade else 1
            al = ease({'bez': cs.get('bez', [0.25, 0.1, 0.25, 1])}, u) if fade else 1
            pop = cs.get('pop', 0)
            sc = 1 + pop * max(0, 1 - (t - c['t']) / 0.18) if pop else 1
            pl = CAP_PLAIN.get(id(c)); k = min(1.0, (t - pl[3]) / 0.15) if pl else 1.0
            if k < 1: blend(frame, pl[0], pl[1], pl[2] + cs.get('rise', 0) * (1 - al), al * (1 - k), sc)
            blend(frame, arr, x, y + cs.get('rise', 0) * (1 - al), al * k, sc)
    for L in live:
        if L.get('over_caps'): draw_layer(frame, L, t)       # marks on the caption itself (a strike, a circle) go over it
    for c in accs:
        if c['t'] <= t < c['e']:
            arr, x, y = render_accent(c)
            u = t - c['t']; fade = c.get('fade', 0.1)
            al = min(1, u / fade if fade else 1, (c['e'] - t) / 0.08 if fade else 1)
            sc = 1.0 + c.get('settle', 0.0) * max(0, 1 - u / 0.35) ** 2
            blend(frame, arr, x, y, al, sc, blur=c.get('blur_in', 0) * max(0, 1 - u / 0.2))
    for fl in fx.get('flash', []):
        if fl['t'] <= t < fl['t'] + fl['d']:
            frame = (255 - frame) if fl.get('invert') else np.clip(frame.astype(np.int16) + 120, 0, 255).astype(np.uint8)
    enc.stdin.write(np.ascontiguousarray(frame).tobytes()); n_out += 1
for d_ in DEC.values(): d_.kill()
if enc: enc.stdin.close(); enc.wait()
else: n_out = r1 - r0
tv = time.time() - T0

# ---------- audio: same segments; a dissolve joint gets an equal-power crossfade of the same length, a hard joint 12 ms edge fades ----------
af = []
for i, s in enumerate(segs):
    st, en = (s['fi'] - s['hp']) / FPS, (s['fo'] + s['hn']) / FPS
    ln = en - st
    edge = '' if (s['hp'] or s['hn']) else f",afade=t=in:d=0.012,afade=t=out:st={max(0, ln - 0.012):.3f}:d=0.012"
    af.append(f"[0:a]atrim={st:.4f}:{en:.4f},asetpts=PTS-STARTPTS{edge}[a{i}]")
cur = 'a0'
for i in range(1, len(segs)):
    ov = segs[i]['x']
    af.append(f"[{cur}][a{i}]" + (f"acrossfade=d={ov / FPS:.4f}:c1=qsin:c2=qsin" if ov else "concat=n=2:v=0:a=1") + f"[x{i}]"); cur = f'x{i}'
af.append(f"[{cur}]atrim={sl[0]:.3f}:{sl[1]:.3f},asetpts=PTS-STARTPTS,highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120[vo]")
ain = ['-i', E['audio']]; mu = E.get('music')
if mu:                                               # music: {file, db, start (s into the track), duck (dB the voice pulls it down), fade}: looped, ducked under the voice
    ain += ['-stream_loop', '-1', '-i', mu['file']]; fd = mu.get('fade', 1.0); ln = sl[1] - sl[0]
    af.append(f"[1:a]atrim={mu.get('start', 0) + sl[0]:.3f}:{mu.get('start', 0) + sl[0] + ln:.3f},asetpts=PTS-STARTPTS,aresample=48000,volume={mu.get('db', -20)}dB,"
              f"afade=t=in:d={fd}" + (f",afade=t=out:st={max(0, DUR - sl[0] - fd):.3f}:d={fd}" if sl[1] >= DUR - 0.01 else '') + "[mu]")
    af.append("[vo]asplit[v1][v2]")
    if mu.get('duck', 8): af.append(f"[mu][v2]sidechaincompress=threshold=0.03:ratio={1 + mu.get('duck', 8) / 2}:attack=30:release=400[md]")
    else: af.append("[v2]anullsink;[mu]anull[md]")
    af.append("[v1][md]amix=inputs=2:duration=first:normalize=0[vo2]"); last = 'vo2'
else: last = 'vo'
fx_ = [x for x in E.get('sfx', []) if sl[0] - 0.01 <= x['t'] < sl[1]]   # sfx: [{t (output s), file, db (gain, about -12..-19 under the voice), lp (Hz low-pass), fade (s soft start)}]
for k, x in enumerate(fx_):
    ain += ['-i', x['file']]; n_ = ain.count('-i') - 1; dl = int(round((x['t'] - sl[0]) * 1000))
    af.append(f"[{n_}:a]aresample=48000,aformat=channel_layouts=mono,volume={x.get('db', -16)}dB" + (f",lowpass=f={x['lp']}" if x.get('lp') else '')
              + f",afade=t=in:d={x.get('fade', 0.08)},adelay={dl}:all=1[s{k}]")
if fx_:
    af.append(f"[{last}]" + ''.join(f'[s{k}]' for k in range(len(fx_))) + f"amix=inputs={len(fx_) + 1}:duration=first:normalize=0[vsfx]"); last = 'vsfx'
af.append(f"[{last}]loudnorm=I=-15.2:TP=-1.2:LRA=9[aout]")
tmpa = a.out + '.a.wav'
subprocess.run([FF, '-v', 'error', '-y'] + ain + ['-filter_complex', ';'.join(af), '-map', '[aout]', '-ar', '48000', tmpa], check=True)
OV = E.get('overlays', [])                           # overlays: {file, x, y (centre 0..1), w px, t, e, fade, opacity}: stills pinned over the finished frame (logo, sticker); they change without re-rendering frames
vin, vf = ['-i', tmpv, '-i', tmpa], []
cur = '0:v'
for k, o in enumerate(OV):
    t0, t1 = o.get('t', 0) - sl[0], min(o.get('e', DUR), sl[1]) - sl[0]
    if t1 <= 0 or t0 >= sl[1] - sl[0]: continue
    vin += ['-loop', '1', '-i', o['file']]; j = vin.count('-i') - 1; fd = o.get('fade', 0.25)
    vf.append(f"[{j}:v]scale={int(o['w'])}:-1:flags=lanczos,format=rgba,colorchannelmixer=aa={o.get('opacity', 1)},"
              f"fade=t=in:st={max(0, t0):.3f}:d={fd}:alpha=1,fade=t=out:st={max(0, t1 - fd):.3f}:d={fd}:alpha=1[o{k}]")
    vf.append(f"[{cur}][o{k}]overlay=x=main_w*{o['x']}-overlay_w/2:y=main_h*{o['y']}-overlay_h/2:eof_action=pass:shortest=0:enable='between(t,{max(0, t0):.3f},{t1:.3f})'[ov{k}]")
    cur = f'ov{k}'
venc = (['-c:v', 'h264_nvenc', '-preset', 'p6', '-tune', 'hq', '-rc', 'vbr', '-cq', '18', '-b:v', '0', '-maxrate', '20M', '-bufsize', '40M'] if a.encoder == 'h264_nvenc'
        else ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-maxrate', '20M', '-bufsize', '40M']) + ['-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709']
vmap = ['-filter_complex', ';'.join(vf), '-map', f'[{cur}]'] + venc if vf else ['-map', '0:v', '-c:v', 'copy']
subprocess.run([FF, '-v', 'error', '-y'] + vin + vmap + ['-map', '1:a', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', a.out], check=True)
os.remove(tmpa)
print(json.dumps({'out': a.out, 'caps_on_face': ON_FACE, 'caps_moved_above_face': CAPS_MOVED, 'caps_halo': CAPS_HALO, 'caps_box': CAPS_BOX, 'layers_moved_off_face': LAYERS_MOVED_OFF_FACE, 'layers_on_face': LAYERS_ON_FACE, 'head_in_panel': HEAD_IN_PANEL, 'frames': n_out, 'dur': round(n_out / FPS, 2), 'cuts': len(cut_times), 'cut_t': [round(c, 2) for c in cut_times],
                  'video_s': round(tv, 1), 'total_s': round(time.time() - T0, 1)}))
