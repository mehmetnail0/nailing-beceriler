"""Write the edit in SOURCE seconds, get edit.json in OUTPUT seconds.
    from timeline import TL, pages, words_between
    tl = TL([(in_s, out_s), (in_s, out_s, 4), ...])   # story order; 3rd value = dissolve frames into that take (0 = hard cut)
    tl.T(src_s, take_index) -> output seconds     tl.dur     tl.cuts     tl.seg_json() -> edit.json "segments"
    pages(tl, [(text, src_start, src_end, take_index), ...]) -> edit.json "captions" (touching pages swap on the same frame)
    words_between(words_json, a, b) -> [(word, start, end)] so you can group pages on the spoken words
    noface() -> [(a, b), ...] source seconds where no face was found (a title card, a logo, a cutaway): keep takes out of them
Holds no look values: every number in an edit comes from you, read from the references.
Audio fixes from the cut QC (cutfix.py) live in work/cut_fixes.json and are applied here, so a re-run of decide.py picks them up untouched:
    {"drop": [[src_a, src_b], ...]  a repeat / false start removed from inside a take (the take keeps its index; T() maps across the hole),
     "snap": [[old_src, new_src], ...]}  a take edge moved to the nearest word boundary."""
import json, os
FPS = 30


def load_fixes(path=None):
    p = path or os.environ.get('CUT_FIXES') or os.path.join(os.getcwd(), 'work', 'cut_fixes.json')
    return json.load(open(p)) if os.path.exists(p) else {}


class TL:
    def __init__(self, segs, fps=FPS, fixes=None):
        fx = load_fixes() if fixes is None else fixes
        snap = fx.get('snap', []); self.drops = [tuple(d) for d in fx.get('drop', [])]
        def sn(v):
            for old, new in snap:
                if abs(v - old) <= 0.021: return new
            return v
        self.fps, self.segs, self.pieces, o = fps, [], [], 0
        for s in segs:
            a, b = sn(s[0]), sn(s[1]); x = s[2] if len(s) > 2 else 0
            cuts = sorted((max(a, d0), min(b, d1)) for d0, d1 in self.drops if d0 < b and d1 > a)
            parts, cur = [], a
            for d0, d1 in cuts:
                if d0 > cur: parts.append((cur, d0))
                cur = max(cur, d1)
            if cur < b: parts.append((cur, b))
            o0 = o
            for k, (pa, pb) in enumerate(parts):
                fi, fo = round(pa * fps), round(pb * fps)
                if fo <= fi: continue
                self.pieces.append((fi / fps, fo / fps, o / fps, x if k == 0 else 0)); o += fo - fi
            self.segs.append((round(a * fps) / fps, round(b * fps) / fps, o0 / fps, x))
        self.dur = o / fps
        self.cuts = [round(p[2], 3) for p in self.pieces[1:]]

    def kept(self, s, e):
        """False when a word [s, e] was dropped by a cut fix."""
        m = (s + e) / 2
        return not any(d0 <= m <= d1 for d0, d1 in self.drops)

    def T(self, src, seg=None):
        tol = lambda i: 0.6 if seg is not None and i == seg else 0.02     # a cut fix may move a take edge a few words; times written against the old edge clamp onto the new one
        cand = [(i, x) for i, x in enumerate(self.segs) if x[0] - tol(i) <= src <= x[1] + tol(i) and (seg is None or i == seg)]
        if not cand: raise ValueError(f'source {src} s is not inside take {seg}')
        i, (a, b, o, _) = cand[0]
        src = min(max(src, a), b)
        ps = [p for p in self.pieces if p[2] >= o - 1e-6 and (i + 1 >= len(self.segs) or p[2] < self.segs[i + 1][2] - 1e-6)]
        for pa, pb, po, _ in ps:
            if src <= pb: return round(po + max(0, src - pa), 3)
        pa, pb, po, _ = ps[-1]
        return round(po + pb - pa, 3)

    def seg_json(self):
        return [{'in': a, 'out': b, 'x': x} for a, b, o, x in self.pieces]


def pages(tl, items, key=None):
    out = [{'t': tl.T(a, s), 'e': tl.T(b, s), 'text': txt, 'key': (key or {}).get(txt, [])} for txt, a, b, s in items]
    out.sort(key=lambda c: c['t'])
    for i in range(len(out) - 1):
        if out[i + 1]['t'] - out[i]['e'] < 0.25: out[i]['e'] = out[i + 1]['t']
        out[i]['e'] = min(out[i]['e'], out[i + 1]['t'])
    return out


def words_between(words_json, a, b):
    """words that overlap [a, b] by at least 80 ms (a shorter word: 60 % of itself; ASR gives “da”, “de” 20 ms), plus a first word that ends inside the take after starting before it
    (ASR stretches the first word after a pause back into the silence; its end is the reliable edge)."""
    d = json.load(open(words_json)) if isinstance(words_json, str) else words_json
    return [(w['w'], w['s'], w['e']) for s in d['segments'] for w in s['words']
            if min(w['e'], b) - max(w['s'], a) >= min(0.08, 0.6 * (w['e'] - w['s'])) or (w['s'] < a < w['e'] <= b and w['e'] - a >= 0.04)]


def pages_from_words(tl, words_json, max_words, max_chars=28, fix=None, keys=None):
    """caption pages on the spoken words of every kept take: phrases split at punctuation and take edges, then each phrase into
    near-equal pages of at most max_words words / max_chars characters (no orphan word on its own page).
    max_words / max_chars come from the ref (e.g. params.json caption_words_per_page); fix = {heard: right} spelling fixes."""
    import math
    fix = fix or {}; items = []; seen = set()
    for si, (a, b, o, _) in enumerate(tl.segs):
        ph, cur = [], []
        for w, s, e in words_between(words_json, a, b):
            if (s, e) in seen or not tl.kept(s, e): continue   # ASR stretches a word across the pause both takes are cut at; it is said once
            seen.add((s, e)); w = fix.get(w, w)
            if not w or w.endswith('...'): continue   # ASR marks a cut-off false start with '...'
            cur.append((w, max(s, a), min(e, b)))
            if w[-1] in '.,?!:;': ph.append(cur); cur = []
        if cur: ph.append(cur)
        for p in ph:
            chars = len(' '.join(x[0] for x in p))
            n = max(math.ceil(len(p) / max_words), math.ceil(chars / max_chars), 1)
            n = min(n, len(p)); size = len(p) / n
            for c in range(n):
                g = p[round(c * size):round((c + 1) * size)]
                if g: items.append((' '.join(x[0] for x in g), g[0][1], g[-1][2], si))
    return pages(tl, items, keys)


def noface(path=None, min_s=0.3):
    """source stretches of min_s or more with no face in work/face.json (facetrack.py, one entry per mezz frame)."""
    p = path or os.path.join(os.getcwd(), 'work', 'face.json')
    if not os.path.exists(p): return []
    F = json.load(open(p)); fps = F.get('fps', 30); out, a = [], None
    for i, x in enumerate(F['f'] + [[1]]):
        if not x and a is None: a = i
        elif x and a is not None:
            if (i - a) / fps >= min_s: out.append((round(a / fps, 3), round(i / fps, 3)))
            a = None
    return out
