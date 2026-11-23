#!/usr/bin/env python3
"""Turn what the word-level cut QC (kesim_qc.py, on the FINAL mix) found into SOURCE-time fixes in work/cut_fixes.json;
timeline.TL applies them on the next decide.py run, so the edit is re-cut, not patched.
usage: cutfix.py report.json edit.json words.json [cut_fixes.json]
  in_word / fragment  the take edge at that cut opens to the quietest point of the pause next to its word (the word is let
                      finish / starts whole): no word he says is lost. A fragment that is a whole short word in the source,
                      with room at the edge, is listed as checked.
  false_start         the broken-off saying goes, cut at the quietest points of the pauses round it.
  repeat across a cut the earlier take ends before its saying (the last take wins).
  repeat in one take  the model's call, never a rule: Turkish doubles words on purpose (“adım adım”, “yavaş yavaş”) and also
                      stumbles (“müthiş… müthiş”; “tekrar tekrar” read as a stutter). It is listed under "judge";
                      the model listens to the wav and writes cut_fixes.json "drop": [[a, b]] or "keep": [[a, b]].
The render gives every hard joint its 12 ms ease. Prints JSON {changed, checked, judge, unmapped}; exit 1 if anything is unmapped."""
import json, math, os, re, sys, unicodedata
import numpy as np

rep, ej, wj = sys.argv[1:4]
out = sys.argv[4] if len(sys.argv) > 4 else os.path.join(os.path.dirname(os.path.abspath(ej)), 'cut_fixes.json')
E = json.load(open(ej)); FPS = E.get('fps', 30); R = json.load(open(rep))
SW = [w for s in json.load(open(wj))['segments'] for w in s['words']]
OW = R.get('words', [])
fx = json.load(open(out)) if os.path.exists(out) else {}
for k in ('drop', 'snap', 'keep'): fx.setdefault(k, [])
P, o = [], 0
for s in E['segments']:
    fi, fo = round(s['in'] * FPS), round(s['out'] * FPS); P.append((fi / FPS, fo / FPS, o / FPS)); o += fo - fi
changed, checked, judge, unmapped = [], [], [], []
AU, SR = None, 16000
try:
    import subprocess
    ap = E.get('audio'); ap = ap if os.path.isabs(ap) else os.path.join(os.getcwd(), ap)
    AU = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', ap, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32)
except Exception:
    AU = None


def quiet(a, b):
    """the quietest frame boundary in [a, b] of the source voice (the render cuts on frames); with no boundary inside, the
    quieter of the two around it; the middle one when the audio is not readable"""
    ks = list(range(math.ceil(a * FPS - 1e-6), math.floor(b * FPS + 1e-6) + 1)) or [math.floor(a * FPS), math.ceil(b * FPS)]
    if AU is None: return round(round((a + b) / 2 * FPS) / FPS, 3)
    lv = lambda t: float((AU[max(0, int((t - 0.01) * SR)):int((t + 0.01) * SR)] ** 2).mean() + 1e-12)
    return round(min(ks, key=lambda k: lv(k / FPS)) / FPS, 3)


def src_of(t):
    for k, (a, b, po) in enumerate(P):
        if po - 1e-3 <= t < po + (b - a) + 1e-3: return a + (t - po), k
    return None, None


def move(old, new, why):
    if abs(new - old) < 0.005: return False
    for d in fx['drop']:
        for j in (0, 1):
            if abs(d[j] - old) <= 0.021:
                d[j] = round(new, 3)
                if d[1] - d[0] < 0.05: fx['drop'].remove(d); changed.append(f'drop at {old:.2f} s undone ({why})')
                else: changed.append(f'drop edge {old:.2f}->{new:.2f} s ({why})')
                return True
    for p in fx['snap']:
        if abs(p[0] - old) <= 0.021 and abs(p[1] - new) <= 0.021: return True
        if abs(p[1] - old) <= 0.021:
            p[1] = round(new, 3); changed.append(f'edge {p[0]:.2f}->{new:.2f} s ({why})'); return True
    fx['snap'].append([round(old, 3), round(new, 3)]); changed.append(f'edge {old:.2f}->{new:.2f} s ({why})'); return True


def open_edge(k, side, kind):
    """move the edge of piece k out to the pause next to the word it touches; False when it already sits in a pause"""
    a, b, _ = P[k]
    if side == 'out':
        last = [w for w in SW if w['s'] < b - 0.02 and w['s'] >= a]
        if not last: return False
        w = last[-1]; nxt = [x for x in SW if x['s'] >= w['e'] - 0.01 and x is not w]
        if b - w['e'] >= 0.06: return False
        lim = min(nxt[0]['s'], w['e'] + 0.25) if nxt else w['e'] + 0.15      # stay by the word: a long pause is not pulled in as dead air
        return move(b, max(b + 0.005, quiet(w['e'], lim)), f'{kind}: “{w["w"]}” finishes')
    first = [w for w in SW if w['e'] > a + 0.02 and w['s'] < b]
    if not first: return False
    w = first[0]; prv = [x for x in SW if x['e'] <= w['s'] + 0.01 and x is not w]
    if w['s'] - a >= 0.06: return False
    lim = max(prv[-1]['e'], w['s'] - 0.25) if prv else w['s'] - 0.15
    return move(a, min(a - 0.005, quiet(lim, w['s'])), f'{kind}: “{w["w"]}” starts whole')


def sliver(k, names, kind, side):
    """a fragment that is the end (or start) of a source word the edge cuts into: open the edge so the word is whole"""
    n = lambda x: re.sub(r'\W', '', x).casefold(); names = {n(x) for x in names}
    b, a = P[k - 1][1], P[k][0]
    for w in SW:
        if n(w['w']) not in names: continue
        if side == 'in' and w['s'] < a - 0.02 and a < w['e'] + 0.03:
            prv = [x for x in SW if x['e'] <= w['s'] + 0.01 and x is not w]; lim = max(prv[-1]['e'], w['s'] - 0.25) if prv else w['s'] - 0.15
            return move(a, min(a - 0.005, quiet(lim, w['s'])), f'{kind}: “{w["w"]}” was cut by the in edge, starts whole')
        if side == 'out' and w['s'] - 0.03 < b < w['e'] - 0.02:
            nxt = [x for x in SW if x['s'] >= w['e'] - 0.01 and x is not w]; lim = min(nxt[0]['s'], w['e'] + 0.25) if nxt else w['e'] + 0.15
            return move(b, max(b + 0.005, quiet(w['e'], lim)), f'{kind}: “{w["w"]}” was cut by the out edge, finishes')
    return False


def whole(ow):
    s0, kk = src_of(ow['s'])
    if s0 is None: return None
    ws = [x for x in SW if abs(x['s'] - s0) < 0.08 and P[kk][0] <= x['s'] and x['e'] <= P[kk][1]]
    return ws[0] if ws else None


for it in R.get('issues', []):
    kind, t, c = it['kind'], float(it['t']), it.get('cut')
    if kind in ('repeat', 'false_start'):
        i = min(range(len(OW)), key=lambda j: abs(OW[j]['s'] - t)) if OW else None
        if i is None: unmapped.append(it); continue
        p = OW[i]; w = OW[i + 1] if len(it['words']) > 1 and i + 1 < len(OW) else None
        sp, kp = src_of(p['s']); sw_, kw = src_of(w['s']) if w else (None, None)
        if kp is None: unmapped.append(it); continue
        f1 = min(SW, key=lambda x: abs(x['s'] - sp))
        pv = [x for x in SW if x['e'] <= f1['s'] + 0.01 and x is not f1]
        a0 = quiet(pv[-1]['e'], f1['s']) if pv else f1['s'] - 0.03
        if w is not None and kw is not None and kw != kp:
            move(P[kp][1], a0, f'{kind} across the cut: {p["w"]} … {w["w"]}, the later take wins'); continue
        nx = [x for x in SW if x['s'] >= f1['e'] - 0.01 and x is not f1]
        b0 = quiet(f1['e'], nx[0]['s']) if nx else f1['e'] + 0.03
        span = [round(a0, 3), round(b0, 3)]
        if any(k0 - 0.05 <= f1['s'] <= k1 + 0.05 for k0, k1 in fx['keep']):
            checked.append(f'{kind} “{" ".join(it["words"])}” at {f1["s"]:.2f} s: kept, the model judged it meant'); continue
        if kind == 'false_start' or (w is not None and len(re.sub(r'\W', '', p['w'])) < len(re.sub(r'\W', '', w['w'])) - 1):
            if span in fx['drop']: continue
            fx['drop'].append(span); changed.append(f'drop {a0:.2f}-{b0:.2f} s ({kind}: “{" ".join(it["words"])}”)'); continue
        ctx = ' '.join(x['w'] for x in SW if f1['s'] - 2.5 < x['s'] < f1['s'] + 3)
        gap = round((min(SW, key=lambda x: abs(x['s'] - sw_))['s'] - f1['e']) if sw_ is not None else 0, 2)
        judge.append(dict(words=it['words'], out_t=t, drop_if_stumble=span, pause_s=gap, context=ctx))
        continue
    if kind not in ('in_word', 'fragment') or c is None: unmapped.append(it); continue     # av_drift = the render's sync math, not an edit: refuse
    k = min(range(1, len(P)), key=lambda j: abs(P[j][2] - c)) if len(P) > 1 else None
    if k is None: unmapped.append(it); continue
    hit = [x for x in OW if x['s'] < c < x['e']] if kind == 'in_word' else []
    ow = hit[0] if hit else min(OW, key=lambda x: abs(x['s'] - t)) if OW else None
    if kind == 'in_word': done = open_edge(k - 1, 'out', kind) | open_edge(k, 'in', kind)
    else: done = open_edge(k - 1, 'out', kind) if ow and (ow['s'] + ow['e']) / 2 < c else open_edge(k, 'in', kind)
    if not done and kind == 'in_word' and AU is not None:      # the words' stamps say pause, the voice at the cut says not: go by the voice
        a1, b1, _ = P[k - 1]; a2 = P[k][0]
        lv = lambda t0, t1: float((AU[int(t0 * SR):int(t1 * SR)] ** 2).mean() + 1e-12)
        nx = [x['s'] for x in SW if x['s'] > b1 + 0.02]; pv = [x['e'] for x in SW if x['e'] < a2 - 0.02]
        if lv(b1 - 0.015, b1) >= lv(a2, a2 + 0.015): done = move(b1, quiet(b1, min(b1 + 0.25, nx[0] if nx else b1 + 0.25)), f'{kind}: voice at the out edge')
        else: done = move(a2, quiet(max(a2 - 0.25, pv[-1] if pv else a2 - 0.25), a2), f'{kind}: voice at the in edge')
    if not done and kind == 'fragment': done = sliver(k, it['words'], kind, 'out' if ow and (ow['s'] + ow['e']) / 2 < c else 'in')
    if done: continue
    if kind == 'fragment' and ow is not None and whole(ow):
        sw0 = whole(ow); checked.append(f'fragment “{ow["w"]}” {1000 * (ow["e"] - ow["s"]):.0f} ms: a whole word ({1000 * (sw0["e"] - sw0["s"]):.0f} ms in the source), edges in pauses'); continue
    unmapped.append(it)
json.dump(fx, open(out, 'w'), indent=1)
print(json.dumps(dict(out=out, changed=changed, checked=checked, judge=judge, unmapped=unmapped), ensure_ascii=False, indent=1))
sys.exit(1 if unmapped else 0)
