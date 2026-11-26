#!/usr/bin/env python3
"""Word-level cut QC on a FINAL mix (any talking-head edit).

usage: kesim_qc.py FINAL.mp4 --cuts CUTS [--lang tr] [--out DIR] [--model large-v3]
  CUTS = edl.json with pieces[].o (output seconds), or a JSON list of cut times, or "1.2,3.4,...".
Finds, on the final audio only (no source words needed):
  repeat      the same word twice in a row (<1.5 s apart)
  false_start a word that is a cut-off prefix of the next one ("mü- müthiş"), or ends in "-"/"…"
  in_word     a cut lands >= 40 ms inside a word AND the audio is voiced on both sides of the cut
  tight_joint (warning) voiced on both sides, but the word reads whole when its side is transcribed alone
  word_edge   (warning) same, but one side is quiet: usually Whisper smearing a word over a pause; read the window
  fragment    a word shorter than 120 ms touching a cut (stray syllable / clipped consonant)
  av_drift    (--src) a piece's audio sits >=20 ms off its source position: crossfade/handle math bug
  blob        (warning, --voice) a 30-250 ms sound alone between two dips >= 10 dB deep: breath/“ım”/hum OR a short word;
              not decidable from transcripts (see the comment at the pass), listened to via blobs/*.wav; nasal=True = no energy >400 Hz
  hot_cut     (warning) voice energy on both sides of the cut within 15 ms: check by ear
Per cut it writes cut_NN_<t>.wav (1.5 s around the cut) and a separate Whisper read of that window
(language auto) as the listen-proof; repeats/false starts are also searched in that window read,
because a whole-file pass often merges “müthiş… müthiş” into one word, and each piece between cuts
is also read on its own and its seam (last 2 words | first 2 words) checked. report.json = {words, cuts:[...], issues:[...]}; exit 1 if issues.
It does not edit the EDL: map each issue's out time back to the source and re-cut, then re-run to exit 0."""
import argparse, json, os, re, subprocess, sys, unicodedata
import numpy as np, soundfile as sf

ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--cuts', required=True)
ap.add_argument('--lang', default='tr'); ap.add_argument('--out', default='kesim_qc'); ap.add_argument('--model', default=None, help='default: large-v3 on an NVIDIA GPU, medium on a CPU (the model transcribe.py already downloaded)')
ap.add_argument('--src', help='source wav of pieces with src==main: checks each piece lands in sync (av_drift)')
ap.add_argument('--voice', help='voice-only render (before music/SFX): lists isolated short blobs (breath/hum candidates) with wavs')
ap.add_argument('--margin', type=float, default=0.04); ap.add_argument('--frag', type=float, default=0.12)
A = ap.parse_args(); os.makedirs(A.out, exist_ok=True); SR = 16000

def load_cuts(c):
    if c.endswith('.json') and not os.path.exists(c): sys.exit(f'no such file: {c}')
    if os.path.exists(c):
        j = json.load(open(c))
        if isinstance(j, dict): return sorted(round(p['o'], 3) for p in j['pieces'][1:])
        return sorted(float(x) for x in j)
    return sorted(float(x) for x in c.split(','))

cuts = load_cuts(A.cuts)
a = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', A.video, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32).copy()
dur = len(a) / SR
from faster_whisper import WhisperModel
try: m = WhisperModel(A.model or 'large-v3', device='cuda', compute_type='float16')
except Exception: m = WhisperModel(A.model or 'medium', device='cpu', compute_type='int8', cpu_threads=int(os.environ.get('OMP_NUM_THREADS') or min(os.cpu_count() or 4, 8)))

def words(x, lang, off=0.0):
    segs, info = m.transcribe(x, language=lang, word_timestamps=True, condition_on_previous_text=False, temperature=0, vad_filter=False)
    return [dict(w=w.word.strip(), s=round(w.start + off, 3), e=round(w.end + off, 3), p=round(w.probability, 2)) for s in segs for w in s.words], getattr(info, 'language', lang)

norm = lambda w: re.sub(r"[^\w]", '', unicodedata.normalize('NFKC', w).casefold().replace('i̇', 'i'))
def rms_db(t0, t1):
    s = a[max(0, int(t0 * SR)):max(0, int(t1 * SR))]
    return float(20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-9)) if len(s) else -120.0

W, _ = words(a, A.lang)
fr = np.array([rms_db(t, t + 0.02) for t in np.arange(0, dur - 0.02, 0.02)]); speech = float(np.percentile(fr, 70)) if len(fr) else -20
voiced = lambda t0, t1: rms_db(t0, t1) > speech - 14
near = lambda t: min(cuts, key=lambda c: abs(c - t)) if cuts else None
issues, warns = [], []
def rep_check(WS, c=None):
    out = []
    for i, w in enumerate(WS):
        n0 = norm(w['w'])
        if w['w'].endswith(('-', '…', '...')) and 0 < len(n0) < 6 and c is None: out.append(dict(kind='false_start', t=w['s'], words=[w['w']], cut=near(w['s'])))
        if not i: continue
        p = WS[i - 1]; n1 = norm(p['w'])
        if c is not None and not (p['s'] < c + 0.3 and w['e'] > c - 0.3): continue
        if n1 and n0 and w['s'] - p['e'] < 1.5:
            if n1 == n0 and len(n0) > 1: out.append(dict(kind='repeat', t=p['s'], words=[p['w'], w['w']], cut=c if c is not None else near(p['s'])))
            elif len(n1) >= 2 and n0.startswith(n1) and len(n0) > len(n1) + 1: out.append(dict(kind='false_start', t=p['s'], words=[p['w'], w['w']], cut=c if c is not None else near(p['s'])))
        if i >= 2:   # A <cut-off word> A  (“müthiş içer- müthiş”)
            q, mid = WS[i - 2], WS[i - 1]
            if norm(q['w']) == n0 and len(n0) > 2 and (mid['w'].endswith(('-', '…', '...')) or mid['e'] - mid['s'] < 0.3) and (c is None or (q['s'] < c + 0.3 and w['e'] > c - 0.3)):
                out.append(dict(kind='repeat', t=q['s'], words=[q['w'], mid['w'], w['w']], cut=c if c is not None else near(q['s'])))
    return out
issues += rep_check(W)
for i, w in enumerate([]):
    n0 = norm(w['w'])
    if w['w'].endswith(('-', '…', '...')) and len(n0) < 6: issues.append(dict(kind='false_start', t=w['s'], words=[w['w']], cut=near(w['s'])))
    if i:
        p = W[i - 1]; n1 = norm(p['w'])
        if n1 and n0 and w['s'] - p['e'] < 1.5:
            if n1 == n0 and len(n0) > 1: issues.append(dict(kind='repeat', t=p['s'], words=[p['w'], w['w']], cut=near(p['s'])))
            elif len(n1) >= 2 and n0.startswith(n1) and len(n0) > len(n1) + 1: issues.append(dict(kind='false_start', t=p['s'], words=[p['w'], w['w']], cut=near(p['s'])))
rep = []
for k, c in enumerate(cuts):
    inside = [w for w in W if w['s'] < c - A.margin and w['e'] > c + A.margin]
    pre, post = rms_db(c - 0.015, c), rms_db(c, c + 0.015)
    for w in inside:
        both = voiced(c - 0.015, c) and voiced(c, c + 0.015)
        if both:   # a tight joint (word ends / starts inside the crossfade) is fine if the word reads whole on its own side
            pad = np.zeros(int(0.3 * SR), np.float32)
            L_, _ = words(np.concatenate([a[int(max(0, c - 1.2) * SR):int(c * SR)], pad]), A.lang)
            R_, _ = words(np.concatenate([pad, a[int(c * SR):int(min(dur, c + 1.2) * SR)]]), A.lang)
            if (R_ and norm(R_[0]['w']) == norm(w['w'])) or (L_ and norm(L_[-1]['w']) == norm(w['w'])):
                warns.append(dict(kind='tight_joint', t=c, words=[w['w']], cut=c, left=L_[-1]['w'] if L_ else '', right=R_[0]['w'] if R_ else '')); continue
        (issues if both else warns).append(dict(kind='in_word' if both else 'word_edge', t=c, words=[w['w']], cut=c, db=[round(pre, 1), round(post, 1)]))
    for w in W:
        if w['e'] - w['s'] < A.frag and (abs(w['s'] - c) < 0.25 or abs(w['e'] - c) < 0.25):
            issues.append(dict(kind='fragment', t=w['s'], words=[w['w']], cut=c, ms=int(1000 * (w['e'] - w['s']))))
    if pre > speech - 8 and post > speech - 8: warns.append(dict(kind='hot_cut', t=c, db=[round(pre, 1), round(post, 1)]))
    t0, t1 = max(0, c - 0.75), min(dur, c + 0.75); seg = a[int(t0 * SR):int(t1 * SR)]
    fn = f"{A.out}/cut_{k + 1:02d}_{c:.2f}.wav"; sf.write(fn, seg, SR)
    lw, lang = words(seg, None, t0)
    w0 = max(0, c - 1.5); lw2, _ = words(a[int(w0 * SR):int(min(dur, c + 1.5) * SR)], A.lang, w0)   # wider read: a repeat often straddles two cuts
    issues += [dict(x, via='window') for x in rep_check(lw2, c)]
    rep.append(dict(n=k + 1, t=c, wav=fn, lang=lang, window=' '.join(f"{x['s']:.2f}:{x['w']}" for x in lw),
                    left=[x['w'] for x in W if c - 0.6 < x['e'] <= c + A.margin][-2:], right=[x['w'] for x in W if c - A.margin <= x['s'] < c + 0.6][:2]))
if A.src and os.path.exists(A.cuts):
    sa = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', A.src, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32)
    env = lambda x, h=160: np.log(np.sqrt((x[:len(x) // h * h].reshape(-1, h) ** 2).mean(1)) + 1e-5)
    for p in json.load(open(A.cuts)).get('pieces', []):
        if p.get('src', 'main') != 'main' or p['out'] - p['in'] < 0.6: continue
        seg = env(a[int((p['o'] + 0.15) * SR):int((p['o'] + p['out'] - p['in'] - 0.15) * SR)]); best = (-2, 0)
        for lag in range(-30, 31):
            r0 = int((p['in'] + 0.15 + lag / 100) * SR); ref = env(sa[max(0, r0):r0 + len(seg) * 160])
            if len(ref) == len(seg): best = max(best, (float(np.corrcoef(seg, ref)[0, 1]), lag))
        if abs(best[1]) >= 2 and best[0] > 0.8: issues.append(dict(kind='av_drift', t=round(p['o'], 3), words=[], cut=round(p['o'], 3), ms=best[1] * 10))
# seam check: every piece read on its own (Whisper merges “müthiş… müthiş” when it hears both at once)
bounds = [0.0] + cuts + [dur]; pad = np.zeros(int(0.3 * SR), np.float32); PW = []
for b0, b1 in zip(bounds, bounds[1:]):
    ws, _ = words(np.concatenate([pad, a[int(b0 * SR):int(b1 * SR)], pad]), A.lang, b0 - 0.3); PW.append(ws)
for k, c in enumerate(cuts):
    L_, R_ = PW[k][-2:], PW[k + 1][:2]
    if L_ and L_[-1]['w'].endswith(('-', '…', '...')) and len(norm(L_[-1]['w'])) < 6: issues.append(dict(kind='false_start', t=L_[-1]['s'], words=[L_[-1]['w']], cut=c, via='seam'))
    for x in rep_check(L_ + R_):
        if x['kind'] != 'false_start' or len(x['words']) == 2: issues.append(dict(x, cut=c, via='seam'))
# voice-blob pass: every short sound standing alone between two deep dips (>= 10 dB below its peak on both sides) on the
# VOICE-ONLY render. Breaths, “ım”/hum, smacks live here, but so do short words and stressed syllables, and Whisper,
# MMS forced alignment, mute-invariance and CTC/Whisper likelihood all failed to tell them apart on this reel (v10 notes).
# So each one is listed with its spectrum and a wav for an ear pass; a nasal-shaped one (no energy above 400 Hz) is marked.
if A.voice:
    from scipy.signal import butter, sosfilt
    vv = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', A.voice, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32).astype(float)
    H = SR // 100; E_ = lambda x: 20 * np.log10(np.sqrt(np.convolve((x[:len(x) // H * H].reshape(-1, H) ** 2).mean(1), np.ones(2) / 2, 'same')) + 1e-9)
    ev = E_(vv); fl_ = np.percentile(ev, 5); vl = [i for i in range(2, len(ev) - 2) if ev[i] == ev[i - 2:i + 3].min()]
    F = np.fft.rfftfreq(512, 1 / SR); os.makedirs(f'{A.out}/blobs', exist_ok=True); nb = 0
    for v0, v1 in zip(vl, vl[1:]):
        pk = ev[v0:v1 + 1].max()
        if not (3 <= v1 - v0 <= 25 and pk - ev[v0] >= 10 and pk - ev[v1] >= 10 and pk > fl_ + 10): continue
        x = vv[v0 * H:v1 * H]; P = sum(np.abs(np.fft.rfft(x[i:i + 512] * np.hanning(512))) ** 2 for i in range(0, max(1, len(x) - 512), 128))
        bd = lambda l, h: 10 * np.log10(P[(F >= l) & (F < h)].sum() + 1e-12)
        r1, r2 = bd(400, 1000) - bd(80, 400), bd(1000, 3000) - bd(80, 400); nb += 1
        fn = f"{A.out}/blobs/blob_{nb:02d}_{v0 / 100:.2f}.wav"; sf.write(fn, a[max(0, v0 * H - 6400):v1 * H + 6400], SR)
        warns.append(dict(kind='blob', t=v0 / 100, t1=v1 / 100, peak_db=round(float(pk), 1), lo_rel=[round(r1, 1), round(r2, 1)], nasal=bool(r1 <= -12 and r2 <= -15), wav=fn,
                          words=[w['w'] for w in W if w['s'] < v1 / 100 and w['e'] > v0 / 100]))
    print(f"voice-blob pass: {nb} isolated blobs listed for the ear ({sum(w.get('nasal', False) for w in warns)} nasal-shaped)")
seen, uniq = set(), []
for x in issues:
    key = (x['kind'], round(x['t'], 2) if x['kind'] == 'filler' else round(x['cut'] or 0, 1), tuple(norm(w) for w in x['words']))
    if key not in seen: seen.add(key); uniq.append(x)
json.dump(dict(video=A.video, dur=round(dur, 2), speech_db=round(speech, 1), words=W, cuts=rep, issues=uniq, warnings=warns), open(f'{A.out}/report.json', 'w'), ensure_ascii=False, indent=1)
print(f"{len(W)} words, {len(cuts)} cuts, {len(uniq)} issues, {len(warns)} warnings -> {A.out}/report.json")
for x in uniq: print('ISSUE', json.dumps(x, ensure_ascii=False))
for x in warns: print('warn ', json.dumps(x, ensure_ascii=False))
for r in rep: print(f"cut {r['n']:02d} {r['t']:6.2f}  {' '.join(r['left'])} | {' '.join(r['right'])}   [{r['lang']}] {r['window']}")
sys.exit(1 if uniq else 0)
