#!/usr/bin/env python3
"""tarz-cikar: reference reel in -> measured style pack (hareket.json) out.

olc     <video> --out DIR      measure one video
karsilastir <ref hareket.json> <own hareket.json>   ours vs the reference, field by field
dogrula <video> DIR            reverse loop: rebuild each move from the fit, overlay on the ref, report error
hepsi   stiller.json --out DIR measure + verify every style in the list
"""
import argparse, json, math, os, subprocess, sys
import numpy as np, cv2
from scipy.optimize import least_squares

AW = 360
LK = dict(winSize=(21, 21), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))


def read_frames(path, width=AW, only=None):
    cap = cv2.VideoCapture(path)
    i = 0
    want = None if only is None else set(only)
    last = max(want) if want else None
    while True:
        if want is not None and i not in want:
            if not cap.grab():
                break
        else:
            ok, f = cap.read()
            if not ok:
                break
            h, w = f.shape[:2]
            yield i, cv2.resize(f, (width, int(round(h * width / w / 2)) * 2), interpolation=cv2.INTER_AREA)
        i += 1
        if last is not None and i > last:
            break
    cap.release()


def video_fps(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.release()
    return float(fps)


def similarity(g0, g1, max_pts=400):
    """Dominant similarity transform g0 -> g1 by tracked corners (LK, forward-backward check, RANSAC).
    Returns (M 2x3 or None, inlier share, second-layer log-scale or None, second-layer share)."""
    p0 = cv2.goodFeaturesToTrack(g0, max_pts, 0.01, 6)
    if p0 is None or len(p0) < 20:
        return None, 0.0, None, 0.0
    p1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g1, p0, None, **LK)
    pb, sb, _ = cv2.calcOpticalFlowPyrLK(g1, g0, p1, None, **LK)
    ok = (st.ravel() == 1) & (sb.ravel() == 1) & (np.linalg.norm((p0 - pb).reshape(-1, 2), axis=1) < 1.0)
    a, b = p0.reshape(-1, 2)[ok], p1.reshape(-1, 2)[ok]
    if len(a) < 20:
        return None, 0.0, None, 0.0
    M, inl = cv2.estimateAffinePartial2D(a, b, method=cv2.RANSAC, ransacReprojThreshold=1.0, maxIters=2000, confidence=0.995)
    if M is None:
        return None, 0.0, None, 0.0
    inl = inl.ravel().astype(bool)
    share = float(inl.mean())
    ls2, share2 = None, 0.0
    out = ~inl
    if out.sum() >= 30:
        M2, inl2 = cv2.estimateAffinePartial2D(a[out], b[out], method=cv2.RANSAC, ransacReprojThreshold=1.0)
        if M2 is not None and inl2.sum() >= 20:
            ls2 = math.log(math.hypot(M2[0, 0], M2[1, 0]))
            share2 = float(inl2.sum() / len(a))
    return M, share, ls2, share2


def bezier_y(u, x1, y1, x2, y2):
    t = np.linspace(0, 1, 201)
    xs = 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3
    ys = 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t ** 2 * y2 + t ** 3
    return np.interp(u, xs, ys)


POWER = {"power1": 2, "power2": 3, "power3": 4, "power4": 5}


def power_y(u, kind, k):
    if kind == "out":
        return 1 - (1 - u) ** k
    if kind == "in":
        return u ** k
    return np.where(u < 0.5, 0.5 * (2 * u) ** k, 1 - 0.5 * (2 * (1 - u)) ** k)


def fit_curve(p):
    """p: progress samples at u = 0..1 (p[0]=0, settles at 1). Returns the fitted easing."""
    n = len(p) - 1
    u = np.linspace(0, 1, n + 1)
    best = None
    for x0 in ([0.33, 0.33, 0.67, 0.67], [0.2, 0.8, 0.3, 1.0], [0.7, 0.0, 0.9, 0.3], [0.5, 0.0, 0.5, 1.0], [0.3, 1.4, 0.6, 1.0]):
        r = least_squares(lambda q: bezier_y(u, *q) - p, x0, bounds=([0, -0.6, 0, -0.6], [1, 2.2, 1, 2.2]))
        if best is None or r.cost < best.cost:
            best = r
    bz = [round(float(v), 3) for v in best.x]
    rmse = float(np.sqrt(np.mean((bezier_y(u, *best.x) - p) ** 2)))
    cands = [("none", "linear", float(np.sqrt(np.mean((u - p) ** 2))))]
    for name, k in POWER.items():
        for kind in ("out", "in", "inOut"):
            cands.append((f"{name}.{kind}", kind, float(np.sqrt(np.mean((power_y(u, kind, k) - p) ** 2)))))
    gs = min(cands, key=lambda c: c[2])
    lin = cands[0][2]
    shape = "linear" if lin - gs[2] < 0.015 else gs[1]
    return {"bezier": bz, "bezier_rmse": round(rmse, 4), "gsap": gs[0] if shape != "linear" else "none",
            "gsap_rmse": round(gs[2], 4), "linear_rmse": round(lin, 4), "sekil": shape, "ornek": n + 1,
            "guven": "dusuk" if n + 1 < 6 else "iyi"}


def runs(mask):
    out, s = [], None
    for i, m in enumerate(mask):
        if m and s is None:
            s = i
        if not m and s is not None:
            out.append((s, i))
            s = None
    if s is not None:
        out.append((s, len(mask)))
    return out


def find_events(cum, a, b, fps, min_delta, thr_per_s):
    """Moves of one channel inside a shot [a, b). cum = cumulative value per frame."""
    seg = cum[a:b]
    if len(seg) < 5:
        return []
    v = np.diff(seg)
    vs = np.convolve(v, np.ones(5) / 5, mode="same")
    noise = 1.4826 * np.median(np.abs(v - np.median(v)))
    thr = max(thr_per_s / fps, 0.0)
    ev = []
    for sign in (1, -1):
        rr = runs(sign * vs > thr)
        merged = []
        for r in rr:
            if merged and r[0] - merged[-1][1] <= 2:
                merged[-1] = (merged[-1][0], r[1])
            else:
                merged.append(r)
        for s, e in merged:
            s0, e0 = max(0, s - 4), min(len(seg) - 1, e + 4)
            d = seg[e0] - seg[s0]
            if abs(d) < min_delta or sign * d <= 0:
                continue
            prog = (seg[s0:e0 + 1] - seg[s0]) / d
            i0 = int(np.argmax(prog > 0.01)) - 1
            i1 = int(np.argmax(prog >= 0.99))
            i0 = max(i0, 0)
            if i1 - i0 < 2:
                continue
            ev.append([a + s0 + i0, a + s0 + i1])
    ev.sort()
    return ev, float(noise)


def detect_cuts(mad, hist, fps):
    n = len(mad)
    cuts = []
    for i in range(1, n):
        lo, hi = max(1, i - 6), min(n, i + 7)
        nb = np.median(np.r_[mad[lo:i], mad[i + 1:hi]]) if hi - lo > 2 else 0
        if hist[i] > 0.28 and mad[i] > 10 and mad[i] > 3 * nb + 4:
            if not cuts or i - cuts[-1] > 2:
                cuts.append(i)
    return cuts


def detect_flashes(luma, fps):
    out = []
    n = len(luma)
    i = 3
    while i < n - 1:
        base = float(np.median(luma[i - 3:i]))
        d = luma[i] - base
        if abs(d) > 28:
            j = i
            while j < min(n, i + int(0.35 * fps)) and abs(luma[j] - base) > 12:
                j += 1
            if j < min(n, i + int(0.35 * fps)) and j > i:
                pk = i + int(np.argmax(np.abs(luma[i:j] - base)))
                out.append({"t": round(i / fps, 3), "sure_kare": j - i, "tepe_kare": pk - i,
                            "yon": "beyaz" if d > 0 else "siyah", "siddet": round(float(abs(luma[pk] - base)) / 255, 3)})
                i = j
        i += 1
    return out


def audio_onsets(path):
    try:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                             capture_output=True, timeout=120).stdout
    except Exception:
        return None
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    if len(x) < 16000:
        return None
    hop = 160
    e = np.sqrt(np.convolve(x ** 2, np.ones(320) / 320, mode="same")[::hop] + 1e-9)
    db = 20 * np.log10(e + 1e-6)
    rise = db[3:] - db[:-3]
    on = []
    for i in np.where(rise > 14)[0]:
        t = (i + 3) * hop / 16000
        if not on or t - on[-1] > 0.08:
            on.append(t)
    return np.array(on)


def measure(frames, fps, audio=None):
    """frames: iterable of BGR frames at analysis size. Returns the pack dict."""
    prev = None
    M_list, share, ls2, sh2, mad, hist, luma, resid, rbox, hs = [], [], [], [], [0.0], [0.0], [], [0.0], [None], []
    sat, cols = [], []
    H = Wd = None
    for i, f in enumerate(frames):
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        H, Wd = g.shape
        luma.append(float(g.mean()))
        if i % 15 == 0:
            hsv = cv2.cvtColor(cv2.resize(f, (18, 32)), cv2.COLOR_BGR2HSV)
            sat.append(float(hsv[..., 1].mean()) / 255)
            cols.append(cv2.resize(f, (18, 32)).reshape(-1, 3))
        hh = cv2.calcHist([cv2.resize(f, (64, 114))], [0, 1, 2], None, [8, 8, 8], [0, 256] * 3)
        cv2.normalize(hh, hh, 1, 0, cv2.NORM_L1)
        hs.append(hh)
        if prev is not None:
            pg, ph = prev
            mad.append(float(cv2.absdiff(g, pg).mean()))
            hist.append(float(cv2.compareHist(ph, hh, cv2.HISTCMP_BHATTACHARYYA)))
            M, s, l2, s2 = similarity(pg, g)
            M_list.append(M); share.append(s); ls2.append(l2); sh2.append(s2)
            if M is not None:
                d = cv2.absdiff(cv2.warpAffine(pg, M, (Wd, H), borderMode=cv2.BORDER_REPLICATE), g) > 40
                d[:4] = d[-4:] = False; d[:, :4] = d[:, -4:] = False
                fr = float(d.mean())
                resid.append(fr)
                if fr > 0.004:
                    ys, xs = np.where(d)
                    rbox.append([float(np.percentile(xs, 5)) / Wd, float(np.percentile(ys, 5)) / H,
                                 float(np.percentile(xs, 95)) / Wd, float(np.percentile(ys, 95)) / H])
                else:
                    rbox.append(None)
            else:
                resid.append(0.0); rbox.append(None)
        prev = (g, hh)
    n = len(luma)
    luma = np.array(luma); mad = np.array(mad); hist = np.array(hist)
    flashes = detect_flashes(luma, fps)
    cuts = detect_cuts(mad, hist, fps)
    for fl in flashes:
        a = int(round(fl["t"] * fps))
        b = min(n - 1, a + fl["sure_kare"])
        inside = [c for c in cuts if a - 1 <= c <= b + 1]
        cuts = [c for c in cuts if c not in inside]
        fl["kesimle"] = bool(a >= 1 and cv2.compareHist(hs[a - 1], hs[b], cv2.HISTCMP_BHATTACHARYYA) > 0.28)
        if fl["kesimle"]:
            cuts.append(a + fl["tepe_kare"])
    cuts = sorted(set(cuts))
    del hs
    # per-frame channels: log scale, frame-centre shift (x, y) in frame widths
    L = np.zeros(n); CX = np.zeros(n); CY = np.zeros(n)
    c0 = np.array([Wd / 2, H / 2, 1.0])
    bounds = [0] + cuts + [n]
    cutset = set(cuts)
    for i in range(1, n):
        M = M_list[i - 1]
        if i in cutset or M is None or share[i - 1] < 0.3:
            dl = dx = dy = 0.0
        else:
            dl = math.log(math.hypot(M[0, 0], M[1, 0]))
            sft = M @ c0 - c0[:2]
            dx, dy = sft[0] / Wd, sft[1] / Wd
        L[i] = L[i - 1] + dl; CX[i] = CX[i - 1] + dx; CY[i] = CY[i - 1] + dy
    shots, zoom_ev, pan_ev, noise_all = [], [], [], []
    for a, b in zip(bounds[:-1], bounds[1:]):
        shots.append((a, b))
        r = find_events(L, a, b, fps, 0.008, 0.005)
        if r:
            noise_all.append(r[1])
            for s, e in r[0]:
                zoom_ev.append((s, e, a, b))
        for ch, nm in ((CX, "x"), (CY, "y")):
            r = find_events(ch, a, b, fps, 0.012, 0.01)
            if r:
                for s, e in r[0]:
                    pan_ev.append((s, e, nm))
    # overshoot merge + curve fit
    events = []
    k = 0
    while k < len(zoom_ev):
        s, e, a, b = zoom_ev[k]
        d1 = math.exp(L[e] - L[s]) - 1
        over = 0.0
        e_fit = e
        if k + 1 < len(zoom_ev):
            s2, e2, a2, _ = zoom_ev[k + 1]
            d2 = math.exp(L[e2] - L[s2]) - 1
            if a2 == a and s2 - e <= 2 and d1 * d2 < 0 and abs(d2) <= 0.4 * abs(d1) and (e2 - s2) / fps <= 0.4:
                over = abs(d2) / abs(d1 + d2)
                e_fit = e2
                k += 1
        sc = np.exp(L[s:e_fit + 1] - L[s])
        settle = sc[-1] - 1
        fit = fit_curve((sc - 1) / settle)
        dur = (e_fit - s) / fps
        speed = abs(settle) / dur * 100
        kind = "punch" if dur < 0.3 else ("drift" if speed < 3 and dur >= 1.2 else "push")
        base = math.exp(L[s] - L[a])
        l2 = [ls2[j] for j in range(s, e_fit) if ls2[j] is not None and sh2[j] >= 0.15]
        dl1 = (L[e_fit] - L[s]) / max(1, e_fit - s)
        par = None
        if len(l2) >= max(2, (e_fit - s) // 2) and abs(dl1) > 1e-5:
            par = round(float(np.median(l2) / dl1), 2)
        fx, fy = (CX[e_fit] - CX[s]), (CY[e_fit] - CY[s])
        den = 1 - math.exp(L[e_fit] - L[s])
        centre = [round(0.5 + fx / den, 2), round(0.5 * H / Wd + fy / den, 2)] if abs(den) > 0.02 else None
        if centre:
            centre[1] = round(centre[1] * Wd / H, 2)
        events.append({"t": round(s / fps, 3), "sure_s": round(dur, 3), "kare": [int(s), int(e_fit)],
                       "olcek": [round(base, 4), round(base * (1 + settle), 4)], "yuzde": round(settle * 100, 2),
                       "tur": kind, "hiz_yuzde_s": round(speed, 1), "asma_yuzde": round(over * 100, 1),
                       "merkez_xy": centre, "ikinci_katman_orani": par, "kesimden_sonra_s": round((s - a) / fps, 3),
                       "kesime_kadar_s": round((b - 1 - e_fit) / fps, 3), **fit})
        k += 1
    pans = []
    for s, e, nm in pan_ev:
        ch = CX if nm == "x" else CY
        d = ch[e] - ch[s]
        if any(z["kare"][0] <= e and s <= z["kare"][1] for z in events):
            continue
        fit = fit_curve((ch[s:e + 1] - ch[s]) / d)
        pans.append({"t": round(s / fps, 3), "sure_s": round((e - s) / fps, 3), "kare": [int(s), int(e)], "eksen": nm,
                     "kayma_genislik_yuzde": round(d * 100, 2), **fit})
    # holds / moving share per shot
    moving = np.zeros(n, bool)
    for z in events:
        moving[z["kare"][0]:z["kare"][1] + 1] = True
    for p in pans:
        moving[p["kare"][0]:p["kare"][1] + 1] = True
    holds, at_cut = [], []
    for a, b in shots:
        if b - a < 0.5 * fps:
            continue
        for s, e in runs(~moving[a:b]):
            holds.append((e - s) / fps)
        at_cut.append(bool(moving[max(a, b - 1 - int(0.2 * fps)):b].any()))
    # overlay entrances: residual bursts after motion compensation, away from cuts
    resid = np.array(resid)
    near_cut = np.zeros(n, bool)
    for c in cuts:
        near_cut[max(0, c - 1):c + 2] = True
    bursts = []
    for s, e in runs((resid > 0.006) & ~near_cut):
        ys = [rbox[j] for j in range(s, e) if rbox[j]]
        if not ys:
            continue
        bb = np.array(ys)
        bursts.append({"t": round(s / fps, 3), "kare": e - s, "alan": round(float(resid[s:e].max()), 4),
                       "kutu": [round(float(v), 2) for v in (bb[:, 0].min(), bb[:, 1].min(), bb[:, 2].max(), bb[:, 3].max())]})
    dur_s = n / fps
    shot_len = np.array([(b - a) / fps for a, b in shots])
    zs = np.array([abs(z["yuzde"]) for z in events]) if events else np.array([0.0])
    def q(x, p):
        return round(float(np.percentile(x, p)), 3) if len(x) else None
    shapes = {}
    for z in events:
        shapes[z["sekil"]] = shapes.get(z["sekil"], 0) + 1
    good = [z for z in events if z["guven"] == "iyi"]
    typical = None
    if good:
        dom = max(set(z["sekil"] for z in good), key=lambda s_: sum(z["sekil"] == s_ for z in good))
        grp = [z for z in good if z["sekil"] == dom]
        typical = {"sekil": dom, "n": len(grp), "bezier_medyan": [round(float(np.median([z["bezier"][i] for z in grp])), 3) for i in range(4)],
                   "gsap": max(set(z["gsap"] for z in grp), key=lambda g_: sum(z["gsap"] == g_ for z in grp)),
                   "sure_s_medyan": q([z["sure_s"] for z in grp], 50), "yuzde_medyan": q([abs(z["yuzde"]) for z in grp], 50)}
    pack = {
        "surum": 1, "fps": round(fps, 3), "kare": n, "sure_s": round(dur_s, 2), "analiz_genislik": Wd,
        "kesim": {"sayi": len(cuts), "on_saniyede": round(len(cuts) / dur_s * 10, 2), "plan_medyan_s": q(shot_len, 50),
                  "plan_p25_s": q(shot_len, 25), "plan_p75_s": q(shot_len, 75), "plan_min_s": q(shot_len, 0),
                  "plan_max_s": q(shot_len, 100), "zamanlar_s": [round(c / fps, 3) for c in cuts]},
        "zoom": {"sayi": len(events), "on_saniyede": round(len(events) / dur_s * 10, 2),
                 "iceri": sum(z["yuzde"] > 0 for z in events), "disari": sum(z["yuzde"] < 0 for z in events),
                 "yuzde_medyan": q(zs, 50), "yuzde_p25": q(zs, 25), "yuzde_p75": q(zs, 75),
                 "sure_medyan_s": q([z["sure_s"] for z in events], 50), "tur": {t: sum(z["tur"] == t for z in events) for t in ("punch", "push", "drift")},
                 "sekil": shapes, "asmali": sum(z["asma_yuzde"] > 0 for z in events), "tipik_egri": typical,
                 "kesimde_hala_hareketli_pay": round(float(np.mean(at_cut)), 2) if at_cut else None,
                 "hareketli_zaman_payi": round(float(moving.mean()), 2),
                 "bekleme_medyan_s": q(holds, 50), "bekleme_p75_s": q(holds, 75), "olaylar": events},
        "kayma": {"sayi": len(pans), "olaylar": pans},
        "flas": {"sayi": len(flashes), "olaylar": flashes},
        "katman_girisi": {"sayi": len(bursts), "on_saniyede": round(len(bursts) / dur_s * 10, 2),
                          "tek_karede_pay": round(float(np.mean([b_["kare"] <= 1 for b_ in bursts])), 2) if bursts else None,
                          "animasyonlu_sure_medyan_kare": q([b_["kare"] for b_ in bursts if b_["kare"] > 1], 50),
                          "merkez_y_medyan": q([(b_["kutu"][1] + b_["kutu"][3]) / 2 for b_ in bursts], 50),
                          "olaylar": bursts[:400]},
        "renk": {"parlaklik": round(float(luma.mean()) / 255, 3), "kontrast": round(float(luma.std()) / 255, 3),
                 "doygunluk": round(float(np.mean(sat)), 3)},
        "olcum_hatasi": {"olcek_gurultu_yuzde_kare": round(float(np.median(noise_all)) * 100, 4) if noise_all else None,
                         "zaman_cozunurlugu_s": round(1 / fps, 4),
                         "izleme_zayif_kare_payi": round(float(np.mean(np.array(share) < 0.3)), 3) if share else None},
    }
    if cols:
        px = np.float32(np.vstack(cols))
        _, lab, cen = cv2.kmeans(px, 5, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 2, cv2.KMEANS_PP_CENTERS)
        cnt = np.bincount(lab.ravel(), minlength=5)
        pack["renk"]["palet"] = [{"hex": "#%02x%02x%02x" % (int(c[2]), int(c[1]), int(c[0])), "pay": round(float(m / cnt.sum()), 2)}
                                 for c, m in sorted(zip(cen, cnt), key=lambda t: -t[1])]
    if audio is not None and len(audio):
        def hit(times):
            return round(float(np.mean([np.min(np.abs(audio - t)) <= 0.07 for t in times])), 2) if len(times) else None
        pack["ses"] = {"vurus_on_saniyede": round(len(audio) / dur_s * 10, 2),
                       "kesimde_vurus_payi": hit([c / fps for c in cuts]),
                       "zoom_basinda_vurus_payi": hit([z["t"] for z in events]),
                       "flasta_vurus_payi": hit([f_["t"] for f_ in flashes]),
                       "not": "vurus = 30 ms icinde 14 dB yukselis; konusma hecesi de sayilir, sfx ile ayrilmaz"}
    return pack


def olc(video, out):
    if not os.path.isfile(video): sys.exit(f'video not found: {video}')
    os.makedirs(out, exist_ok=True)
    fps = video_fps(video)
    pack = measure((f for _, f in read_frames(video)), fps, audio_onsets(video))
    pack["kaynak"] = os.path.basename(video)
    json.dump(pack, open(os.path.join(out, "hareket.json"), "w"), ensure_ascii=False, indent=1, default=lambda o: o.item())
    return pack


def warp_zoom(img, s, centre, shift):
    h, w = img.shape[:2]
    cx, cy = centre[0] * w, centre[1] * h
    M = np.float32([[s, 0, cx - s * cx + shift[0] * w], [0, s, cy - s * cy + shift[1] * w]])
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def dogrula(video, out, width=540, max_events=40, sheet=True):
    """Reverse loop. For every measured zoom: take the ref frame at the start, re-render the move from the
    fitted curve alone, lay it over the real ref frames and measure what is left (scale %, shift px)."""
    pack = json.load(open(os.path.join(out, "hareket.json")))
    evs = sorted(pack["zoom"]["olaylar"], key=lambda z: -abs(z["yuzde"]))[:max_events]
    need = set()
    for z in evs:
        s, e = z["kare"]
        need.update([s, (s + e) // 2, s + (e - s) * 3 // 4, e, s + (e - s) // 4])
    fr = dict(read_frames(video, width, need))
    rows, best = [], None
    for z in evs:
        s, e = z["kare"]
        if s not in fr or e not in fr:
            continue
        g0 = fr[s]
        total = z["olcek"][1] / z["olcek"][0]
        # centre and end shift straight from the two end frames (independent of the per-frame chain)
        Mse, sh, _, _ = similarity(cv2.cvtColor(g0, cv2.COLOR_BGR2GRAY), cv2.cvtColor(fr[e], cv2.COLOR_BGR2GRAY))
        if Mse is None or sh < 0.3:
            continue
        direct = math.hypot(Mse[0, 0], Mse[1, 0])
        h, w = g0.shape[:2]
        for name, frac in (("ceyrek", 0.25), ("orta", 0.5), ("ucceyrek", 0.75)):
            k = s + int((e - s) * frac)
            if k not in fr:
                continue
            u = (k - s) / (e - s)
            res = {}
            for label, p in (("egri", float(bezier_y(np.array([u]), *z["bezier"])[0])), ("duz", u), ("yok", 0.0)):
                sc = 1 + (direct - 1) * p
                Mk = Mse.copy()
                Mk[:, :2] = np.eye(2) * sc
                Mk[:, 2] = Mse[:, 2] * ((sc - 1) / (direct - 1) if abs(direct - 1) > 1e-6 else p)
                syn = cv2.warpAffine(g0, Mk, (w, h), borderMode=cv2.BORDER_REPLICATE)
                Mr, shr, _, _ = similarity(cv2.cvtColor(syn, cv2.COLOR_BGR2GRAY), cv2.cvtColor(fr[k], cv2.COLOR_BGR2GRAY))
                if Mr is None or shr < 0.3:
                    res = None
                    break
                res[label] = (abs(math.hypot(Mr[0, 0], Mr[1, 0]) - 1) * 100,
                              float(np.hypot(*(Mr @ np.array([w / 2, h / 2, 1.0]) - np.array([w / 2, h / 2])))) / w * 1080)
                if label == "egri" and name == "orta":
                    cand = (abs(z["yuzde"]), syn, fr[k], z)
            if res:
                rows.append({"t": z["t"], "an": name, "zincir_vs_dogrudan_yuzde": round(abs(total - direct) * 100, 3),
                             **{f"{l}_olcek_hata_yuzde": round(v[0], 3) for l, v in res.items()},
                             **{f"{l}_kayma_px1080": round(v[1], 2) for l, v in res.items()}})
                if name == "orta" and (best is None or cand[0] > best[0]) and z["guven"] == "iyi":
                    best = cand
    def med(key, p=50):
        v = [r[key] for r in rows]
        return round(float(np.percentile(v, p)), 3) if v else None
    rep = {"olay": len(set(r["t"] for r in rows)), "olcum_noktasi": len(rows),
           "egri_olcek_hata_yuzde": {"medyan": med("egri_olcek_hata_yuzde"), "p90": med("egri_olcek_hata_yuzde", 90)},
           "duz_olcek_hata_yuzde": {"medyan": med("duz_olcek_hata_yuzde"), "p90": med("duz_olcek_hata_yuzde", 90)},
           "hareketsiz_olcek_hata_yuzde": {"medyan": med("yok_olcek_hata_yuzde")},
           "egri_kayma_px1080": {"medyan": med("egri_kayma_px1080"), "p90": med("egri_kayma_px1080", 90)},
           "zincir_vs_dogrudan_yuzde": {"medyan": med("zincir_vs_dogrudan_yuzde"), "p90": med("zincir_vs_dogrudan_yuzde", 90)},
           "satirlar": rows}
    pack["dogrulama"] = {k: v for k, v in rep.items() if k != "satirlar"}
    json.dump(pack, open(os.path.join(out, "hareket.json"), "w"), ensure_ascii=False, indent=1, default=lambda o: o.item())
    json.dump(rep, open(os.path.join(out, "dogrulama.json"), "w"), ensure_ascii=False, indent=1, default=lambda o: o.item())
    if sheet and best is not None:
        _, syn, real, z = best
        diff = cv2.applyColorMap(cv2.convertScaleAbs(cv2.absdiff(syn, real), alpha=3), cv2.COLORMAP_INFERNO)
        cv2.imwrite(os.path.join(out, "ust-uste.jpg"), np.hstack([real, syn, cv2.addWeighted(real, 0.5, syn, 0.5, 0), diff]))
    return rep


def olay_kareleri(video, out, max_events=8, width=270):
    """One contact sheet: start / middle / end frame of the biggest moves. Stays local (third-party frames)."""
    pack = json.load(open(os.path.join(out, "hareket.json")))
    evs = sorted(pack["zoom"]["olaylar"], key=lambda z: -abs(z["yuzde"]))[:max_events]
    need = set()
    for z in evs:
        s, e = z["kare"]
        need.update([s, (s + e) // 2, e])
    fr = dict(read_frames(video, width, need))
    rows = []
    for z in evs:
        s, e = z["kare"]
        if all(k in fr for k in (s, (s + e) // 2, e)):
            row = np.hstack([fr[s], fr[(s + e) // 2], fr[e]])
            cv2.putText(row, f"t={z['t']} {z['yuzde']}% {z['sure_s']}s {z['gsap']}", (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            rows.append(row)
    for i in range(0, len(rows), 4):
        cv2.imwrite(os.path.join(out, f"olaylar-{i // 4 + 1}.jpg"), np.vstack(rows[i:i + 4]))


def karsilastir(ref_pack, own_pack):
    """Ours vs the reference, on the same measured fields. Numbers only; what to do about a gap is the editor's call."""
    a = json.load(open(ref_pack)); b = json.load(open(own_pack))
    if "refs" in a:
        a = next(iter(a["refs"].values()))
    rows = []
    for path in ("kesim.on_saniyede", "kesim.plan_medyan_s", "zoom.on_saniyede", "zoom.yuzde_medyan", "zoom.sure_medyan_s",
                 "zoom.hareketli_zaman_payi", "zoom.kesimde_hala_hareketli_pay", "zoom.bekleme_medyan_s", "zoom.tipik_egri.sekil",
                 "zoom.tipik_egri.bezier_medyan", "flas.sayi", "katman_girisi.on_saniyede", "katman_girisi.animasyonlu_sure_medyan_kare",
                 "renk.parlaklik", "renk.kontrast", "renk.doygunluk"):
        va, vb = a, b
        for k in path.split("."):
            va = va.get(k) if isinstance(va, dict) else None
            vb = vb.get(k) if isinstance(vb, dict) else None
        rows.append({"alan": path, "referans": va, "bizim": vb})
    return rows


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("olc"); a.add_argument("video"); a.add_argument("--out", required=True)
    b = sub.add_parser("dogrula"); b.add_argument("video"); b.add_argument("out")
    k = sub.add_parser("karsilastir"); k.add_argument("referans"); k.add_argument("bizim")
    c = sub.add_parser("hepsi"); c.add_argument("liste"); c.add_argument("--out", required=True); c.add_argument("--kok", default=".")
    x = ap.parse_args()
    if x.cmd == "olc":
        p = olc(x.video, x.out); olay_kareleri(x.video, x.out)
        print(json.dumps({"zoom": p["zoom"]["sayi"], "kesim": p["kesim"]["sayi"], "flas": p["flas"]["sayi"]}))
    elif x.cmd == "karsilastir":
        for r in karsilastir(x.referans, x.bizim):
            print(f"{r['alan']:48} ref {r['referans']!s:28} bizim {r['bizim']!s}")
    elif x.cmd == "dogrula":
        r = dogrula(x.video, x.out)
        print(json.dumps({k: v for k, v in r.items() if k != "satirlar"}, ensure_ascii=False))
    else:
        for name, v in json.load(open(x.liste)).items():
            video = os.path.join(x.kok, v["dosya"])
            out = os.path.join(x.out, name)
            if os.path.exists(os.path.join(out, "dogrulama.json")):
                continue
            if not os.path.exists(video):
                print(name, "VIDEO YOK", video, flush=True); continue
            try:
                p = olc(video, out); olay_kareleri(video, out); r = dogrula(video, out)
                print(name, p["sure_s"], "s zoom", p["zoom"]["sayi"], "kesim", p["kesim"]["sayi"], "egri hata", r["egri_olcek_hata_yuzde"], flush=True)
            except Exception as ex:
                print(name, "HATA", repr(ex)[:200], flush=True)


if __name__ == "__main__":
    main()
