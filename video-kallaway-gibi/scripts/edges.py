#!/usr/bin/env python3
"""Every take edge, before the render and after each cut-QC fix: no word cut in half, no start of the next saying, and no more room
round a joint than the speaker's own pause. Goes by the source voice, not only by the word stamps (ASR stretches a first word back
into the pause before it). Fixes land in work/cut_fixes.json as snaps (their targets listed under "edges"); timeline.TL applies them on the next decide.py run.
An edge the cut QC (cutfix.py) set stays: the QC heard the final mix.
usage: edges.py edit.json words.json [cut_fixes.json]
  a word cut by an edge  more than half of its voice inside: the edge opens so it finishes (out) / starts whole (in); less: it goes,
                         with the edge in the pause before (after) it. This is how a retake's first word at a take's end leaves.
  room at an edge        the edge keeps edit.cut.tail (head) seconds past the voice and the word's stamp, whichever is later; by default half the speaker's median pause between
                         two words of a phrase, so a joint sounds like one of his own pauses. A breath or room past that goes.
Prints JSON {changed, edges, tail, head}."""
import json, math, os, subprocess, sys
import numpy as np

ej, wj = sys.argv[1:3]
out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(ej)), 'cut_fixes.json')
E = json.load(open(ej)); FPS = E.get('fps', 30)
SW = [w for s in json.load(open(wj))['segments'] for w in s['words'] if w['e'] > w['s']]
fx = json.load(open(out)) if os.path.exists(out) else {}
for k in ('drop', 'snap', 'keep', 'edges'): fx.setdefault(k, [])
SR, HOP = 16000, 0.01
ap_ = E['audio'] if os.path.isabs(E['audio']) else os.path.join(os.getcwd(), E['audio'])
AU = np.frombuffer(subprocess.run([os.environ.get('FF', 'ffmpeg'), '-v', 'error', '-i', ap_, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                                  capture_output=True, check=True).stdout, np.float32)
n = int(len(AU) / (SR * HOP)); FR = AU[:int(n * SR * HOP)].reshape(n, -1)
DB = 10 * np.log10((FR ** 2).mean(1) + 1e-10)
SP_ = np.abs(np.fft.rfft(FR * np.hanning(FR.shape[1]), axis=1)) ** 2 + 1e-12
FLAT = np.exp(np.log(SP_).mean(1)) / SP_.mean(1)          # spectral flatness: a voice is tonal (near 0), room tone and breath are noise
floor, top = np.percentile(DB, 10), np.percentile(DB, 95)
THR = floor + 0.3 * (top - floor)                        # loud: over this recording's room (p10), a third of the way to its loud voice (p95)
SOFT = floor + 0.15 * (top - floor)                      # soft: a quiet word still clears the room by this much
VOX = (DB > THR) | ((DB > SOFT) & (FLAT < 0.08))         # voice: loud, or soft and tonal (a breath or room is soft and noise)
_r = np.diff(np.r_[0, VOX.astype(int), 0]); _s, _e = np.nonzero(_r == 1)[0], np.nonzero(_r == -1)[0]
for x, y in zip(_s, _e):
    if y - x < 3: VOX[x:y] = False                       # under 30 ms is a click or a lip, not a syllable
gaps = [b['s'] - a['e'] for a, b in zip(SW, SW[1:]) if 0.02 < b['s'] - a['e'] < 0.6]
C = E.get('cut', {})
TAIL = C.get('tail', max(2 / FPS, float(np.median(gaps)) / 2 if gaps else 0.1))
HEAD = C.get('head', TAIL)
voiced = lambda a, b: int(VOX[max(0, int(a / HOP)):max(0, int(b / HOP))].sum())


def quiet(a, b):
    ks = list(range(math.ceil(a * FPS - 1e-6), math.floor(b * FPS + 1e-6) + 1)) or [round((a + b) / 2 * FPS)]
    lv = lambda t: float((AU[max(0, int((t - 0.01) * SR)):int((t + 0.01) * SR)] ** 2).mean() + 1e-12)
    return round(min(ks, key=lambda k: lv(k / FPS)) / FPS, 3)


LOUD = DB > floor + 0.5 * (top - floor)                 # a word's body, half way to the loud voice: an edge here cuts through it


def last_voice(a, b):
    ks = np.nonzero(VOX[max(0, int(a / HOP)):min(n, int(b / HOP))])[0]
    return max(0, int(a / HOP)) * HOP + (ks[-1] + 1) * HOP if len(ks) else None


def first_voice(a, b):
    ks = np.nonzero(VOX[max(0, int(a / HOP)):min(n, int(b / HOP))])[0]
    return max(0, int(a / HOP)) * HOP + ks[0] * HOP if len(ks) else None


def loud_run(t, step):
    """from a loud frame at t, walk (step +1 later / -1 earlier) to where the loud voice stops for 0.12 s: a cut through a word"""
    k = int(t / HOP); edge, quiet_ = k, 0
    while 0 <= k < n and quiet_ < 12:
        if LOUD[k]: edge, quiet_ = k, 0
        else: quiet_ += 1
        k += step
    return (edge + 1) * HOP if step > 0 else edge * HOP


QC = {round(v, 2) for d in fx['drop'] for v in d} | {round(p[1], 2) for p in fx['snap']}
QC -= {round(v, 2) for v in fx['edges']}                  # edges the cut QC set by listening to the final mix: those stay


def move(old, new, why):
    if abs(new - old) < 0.5 / FPS or any(abs(old - v) <= 0.021 for v in QC): return None
    fx['edges'].append(round(new, 3))
    for d in fx['drop']:
        for j in (0, 1):
            if abs(d[j] - old) <= 0.021: d[j] = round(new, 3); return why
    for p in fx['snap']:
        if abs(p[1] - old) <= 0.021: p[1] = round(new, 3); return why
    fx['snap'].append([round(old, 3), round(new, 3)]); return why


log = []
P = [(s['in'], s['out']) for s in E['segments']]
for k, (a, b) in enumerate(P):
    ws = [w for w in SW if w['e'] > a and w['s'] < b]
    keep = [w for w in ws if voiced(max(a, w['s']), min(b, w['e'])) >= 0.5 * max(1, voiced(w['s'], w['e']))]
    if not keep: continue
    l, f = keep[-1], keep[0]
    cut_out = [w for w in ws if w['s'] < b < w['e'] and w not in keep]
    cut_in = [w for w in ws if w['s'] < a < w['e'] and w not in keep]
    nxt = [w for w in SW if w['s'] >= l['e'] - 0.01 and w is not l]
    prv = [w for w in SW if w['e'] <= f['s'] + 0.01 and w is not f]
    nlim = cut_out[0]['s'] if cut_out else nxt[0]['s'] if nxt else l['e'] + 1.0
    plim = cut_in[-1]['e'] if cut_in else prv[-1]['e'] if prv else f['s'] - 1.0
    nb, na, wo, wi = b, a, '', ''
    if cut_out or LOUD[min(n - 1, int(b / HOP) - 1)]:                      # the edge cuts through voice
        ve = last_voice(l['s'], nlim) if cut_out else loud_run(b - HOP, +1)
        if ve is not None and ve < nlim - 0.02:                            # else the voice runs on into the next word: no pause to cut in
            nb = quiet(ve + 0.5 * TAIL, min(ve + TAIL, nlim)) if cut_out else max(b, quiet(ve + 0.5 * TAIL, min(ve + TAIL, nlim)))
            wo = '“%s” goes: the edge cut it with most of it outside' % cut_out[0]['w'] if cut_out else 'voice was clipped'
    else:
        ve = last_voice(l['s'], b); ve = max(ve, l['e']) if ve is not None else None     # the stamp bounds a trim: a soft word end can sit under the level
        if ve is not None and b - ve > TAIL + 1 / FPS:
            nb = quiet(ve + 0.5 * TAIL, ve + TAIL); wo = f'{b - nb:.2f} s of room past the voice'
    if cut_in or LOUD[min(n - 1, int(a / HOP))]:
        vs = first_voice(plim, f['e']) if cut_in else loud_run(a, -1)
        if vs is not None and vs > plim + 0.02:
            na = quiet(max(vs - HEAD, plim), vs - 0.5 * HEAD) if cut_in else min(a, quiet(max(vs - HEAD, plim), vs - 0.5 * HEAD))
            wi = '“%s” goes: the edge cut it with most of it outside' % cut_in[0]['w'] if cut_in else 'voice was clipped'
    else:
        vs = first_voice(a, f['e']); vs = min(vs, f['s']) if vs is not None else None    # (a quiet “Bunu” at -62 dB was heard by the QC, not the level)
        if vs is not None and vs - a > HEAD + 1 / FPS:
            na = quiet(vs - HEAD, vs - 0.5 * HEAD); wi = f'{na - a:.2f} s of room before the voice'
    if nb - na < 0.2: continue
    for side, old, new, why in (('out', b, nb, wo), ('in', a, na, wi)):
        r = move(old, new, why) if why else None
        if r: log.append(dict(k=k, side=side, was=round(old, 3), now=round(new, 3), why=r))
json.dump(fx, open(out, 'w'), indent=1)
print(json.dumps(dict(changed=len(log), edges=log, tail=round(TAIL, 3), head=round(HEAD, 3), speech_db=round(float(THR), 1), voice_s=round(float(VOX.sum() * HOP), 1)), ensure_ascii=False))
