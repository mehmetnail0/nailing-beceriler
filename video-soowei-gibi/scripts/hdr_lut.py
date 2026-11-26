#!/usr/bin/env python3
"""HDR phone clip -> SDR Rec.709 as one 3D LUT, for an ffmpeg without zscale (Homebrew's ffmpeg has no zimg).
usage: hdr_lut.py <out.cube> hlg|pq [--size 65] [--npl 100] [--peak 1000]
The same chain mezz.sh runs through zscale + tonemap: BT.2020 non-linear RGB -> display light (HLG: inverse OETF + OOTF at
--peak nits; PQ: EOTF) in units of --npl nits -> BT.2020 to BT.709 primaries -> hable tonemap on the brightest channel
(desat 0, like ffmpeg's tonemap) -> BT.709 OETF. mezz.sh feeds it full-range BT.2020 RGB and applies it with lut3d."""
import argparse
import numpy as np


def hlg_display(e, peak):
    a, b, c = 0.17883277, 0.28466892, 0.55991073
    s = np.where(e <= 0.5, e * e / 3, (np.exp((e - c) / a) + b) / 12)          # scene light 0..1
    y = 0.2627 * s[..., 0] + 0.6780 * s[..., 1] + 0.0593 * s[..., 2]
    g = 1.05   # matched to ffmpeg zscale's HLG output (the path mezz.sh takes when it can): luma PSNR 41.4 dB vs 26.8 at BT.2100's 1.2
    return peak * s * np.power(np.maximum(y, 1e-12), g - 1)[..., None]


def pq_display(e):
    m1, m2, c1, c2, c3 = 0.1593017578125, 78.84375, 0.8359375, 18.8515625, 18.6875
    p = np.power(np.clip(e, 0, 1), 1 / m2)
    return 10000 * np.power(np.maximum(p - c1, 0) / (c2 - c3 * p), 1 / m1)


def hable(x):
    A, B, C, D, E, F = 0.15, 0.50, 0.10, 0.20, 0.02, 0.30
    return (x * (A * x + C * B) + D * E) / (x * (A * x + B) + D * F) - E / F


def bt709_oetf(l):
    l = np.clip(l, 0, 1)
    return np.where(l < 0.018, 4.5 * l, 1.099 * np.power(l, 0.45) - 0.099)


def build(kind, n=65, npl=100.0, peak=1000.0):
    g = np.linspace(0, 1, n)
    b, gg, r = np.meshgrid(g, g, g, indexing='ij')                               # .cube order: r fastest
    e = np.stack([r, gg, b], -1)
    lin = (hlg_display(e, peak) if kind == 'hlg' else pq_display(e)) / npl
    M = np.array([[1.6605, -0.5876, -0.0728], [-0.1246, 1.1329, -0.0083], [-0.0182, -0.1006, 1.1187]])   # BT.2020 -> BT.709
    lin = np.maximum(lin @ M.T, 0)
    sig = lin.max(-1, keepdims=True)
    pk = peak / npl
    mapped = hable(sig) / hable(pk)
    out = lin * np.where(sig > 1e-9, mapped / np.maximum(sig, 1e-9), 0)
    return bt709_oetf(out).reshape(-1, 3)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('kind', choices=['hlg', 'pq'])
    ap.add_argument('--size', type=int, default=65); ap.add_argument('--npl', type=float, default=100); ap.add_argument('--peak', type=float, default=1000)
    a = ap.parse_args()
    rows = build(a.kind, a.size, a.npl, a.peak)
    with open(a.out, 'w') as f:
        f.write(f'LUT_3D_SIZE {a.size}\n' + ''.join(f'{x:.6f} {y:.6f} {z:.6f}\n' for x, y, z in rows))
    print(a.out)
