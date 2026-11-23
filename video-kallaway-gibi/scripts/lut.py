#!/usr/bin/env python3
"""One look, one definition: builds the .cube LUT for an edit at any strength.
usage: lut.py <out.cube> [--strength 0..1] [--size 33] [--warm 0..1] [--pink keep 0..1]
Input domain: Rec.709 video (after HLG->SDR tonemap), RGB 0..1."""
import argparse
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('out')
ap.add_argument('--strength', type=float, default=1.0)
ap.add_argument('--size', type=int, default=33)
ap.add_argument('--warm', type=float, default=1.0)
ap.add_argument('--pink', type=float, default=1.0)   # saturation kept on pink/magenta (lip hue ~345 deg); 1 = untouched
a = ap.parse_args()

N = a.size
g = np.linspace(0, 1, N)
b, gg, r = np.meshgrid(g, g, g, indexing='ij')          # .cube order: r fastest
rgb = np.stack([r, gg, b], -1).reshape(-1, 3)
x = rgb.copy()

luma = lambda c: c @ np.array([0.2126, 0.7152, 0.0722])


def tone(y):
    y = 0.018 + y * (1 - 0.018)                          # soft black floor (no crushed shirt)
    s = y + 0.10 * np.sin((y - 0.08) * np.pi / 0.84) * (y > 0.08) * (y < 0.92)   # gentle mid S
    knee = 0.78                                           # highlight roll-off: the white wall never clips
    hi = s > knee
    s = np.where(hi, knee + (0.955 - knee) * (1 - np.exp(-(s - knee) / (0.955 - knee) * 1.35)), s)
    return np.clip(s, 0, 1)


Y = luma(x)
Yt = tone(Y)
x = x * (Yt / np.maximum(Y, 1e-4))[:, None]
x = np.clip(x, 0, 1)

# split tone: warm mids/highlights, faint cool-green shadows (filmic, not teal-orange)
Y = luma(x)
w = a.warm
sh = np.clip(1 - Y / 0.35, 0, 1)[:, None]
hl = np.clip((Y - 0.35) / 0.65, 0, 1)[:, None]
x = x + sh * np.array([-0.010, 0.004, 0.012]) * w + hl * np.array([0.022, 0.006, -0.022]) * w

# saturation: everything a touch quieter, skin hues (orange/red, ~0-50 deg) kept whole
mx, mn = x.max(1), x.min(1)
d = np.maximum(mx - mn, 1e-6)
h = np.where(mx == x[:, 0], ((x[:, 1] - x[:, 2]) / d) % 6, np.where(mx == x[:, 1], (x[:, 2] - x[:, 0]) / d + 2, (x[:, 0] - x[:, 1]) / d + 4)) * 60
skin = np.exp(-((((h - 25) + 180) % 360 - 180) / 22) ** 2)
sat = 0.86 + 0.14 * skin
lip = np.clip(1 - np.abs(((h - 345) + 180) % 360 - 180) / 28, 0, 1) ** 1.5
sat = sat * (1 - (1 - a.pink) * lip)
Y = luma(x)[:, None]
x = Y + (x - Y) * sat[:, None]
x = np.clip(x, 0, 1)

out = rgb + (x - rgb) * a.strength
with open(a.out, 'w') as f:
    f.write(f'TITLE "film s={a.strength:.2f}"\nLUT_3D_SIZE {N}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
    np.savetxt(f, out, fmt='%.6f')
print(a.out)
