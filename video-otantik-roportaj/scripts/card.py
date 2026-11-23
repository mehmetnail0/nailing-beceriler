#!/usr/bin/env python3
"""Turn a frame (a screen, a reel, a post) into a card PNG with alpha for an image layer: crop, optional straighten, rounded corners,
border, and a soft halo (white or dark). Every look number is an argument the model chooses from its refs.
usage: card.py src.(png|jpg|mp4) out.png --crop x0,y0,x1,y1 [--at 3.2 (seconds, for a video)] [--quad x,y,x,y,x,y,x,y (corners tl,tr,br,bl of a screen filmed at an angle)]
               [--w 620] [--radius 28] [--border 6] [--border-color #FFFFFF] [--halo 40] [--halo-color #FFFFFF] [--halo-opacity 0.55] [--sharpen 0.6]"""
import argparse, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--crop', default=''); ap.add_argument('--at', type=float, default=0); ap.add_argument('--quad', default='')
ap.add_argument('--w', type=int, default=620); ap.add_argument('--radius', type=int, default=28); ap.add_argument('--border', type=int, default=6)
ap.add_argument('--border-color', default='#FFFFFF'); ap.add_argument('--halo', type=int, default=40); ap.add_argument('--halo-color', default='#FFFFFF')
ap.add_argument('--halo-opacity', type=float, default=0.55); ap.add_argument('--sharpen', type=float, default=0.0)
a = ap.parse_args()
if a.src.lower().endswith(('.mp4', '.mov')):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(a.at), '-i', a.src, '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, check=True).stdout
    im = cv2.cvtColor(cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
else:
    im = np.asarray(Image.open(a.src).convert('RGB'))
if a.quad:
    q = np.array([float(v) for v in a.quad.split(',')], np.float32).reshape(4, 2)
    w = int(max(np.linalg.norm(q[1] - q[0]), np.linalg.norm(q[2] - q[3]))); h = int(max(np.linalg.norm(q[3] - q[0]), np.linalg.norm(q[2] - q[1])))
    im = cv2.warpPerspective(im, cv2.getPerspectiveTransform(q, np.float32([[0, 0], [w, 0], [w, h], [0, h]])), (w, h), flags=cv2.INTER_CUBIC)
elif a.crop:
    x0, y0, x1, y1 = [int(v) for v in a.crop.split(',')]; im = im[y0:y1, x0:x1]
h = int(im.shape[0] * a.w / im.shape[1])
im = cv2.resize(im, (a.w, h), interpolation=cv2.INTER_AREA if a.w < im.shape[1] else cv2.INTER_CUBIC)
if a.sharpen: im = cv2.addWeighted(im, 1 + a.sharpen, cv2.GaussianBlur(im, (0, 0), 2), -a.sharpen, 0)
pad = a.halo * 2 + a.border
W, H = a.w + 2 * pad, h + 2 * pad
card = Image.new('RGBA', (W, H), (0, 0, 0, 0))
m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([pad - a.border, pad - a.border, pad + a.w + a.border - 1, pad + h + a.border - 1], a.radius + a.border, fill=255)
if a.halo:
    hc = tuple(int(a.halo_color[i:i + 2], 16) for i in (1, 3, 5))
    halo = Image.new('RGBA', (W, H), hc + (0,)); halo.putalpha(m.filter(ImageFilter.GaussianBlur(a.halo)).point(lambda v: int(v * a.halo_opacity)))
    card = Image.alpha_composite(card, halo)
if a.border:
    bc = tuple(int(a.border_color[i:i + 2], 16) for i in (1, 3, 5))
    b = Image.new('RGBA', (W, H), bc + (255,)); b.putalpha(m); card = Image.alpha_composite(card, b)
inner = Image.new('L', (W, H), 0); ImageDraw.Draw(inner).rounded_rectangle([pad, pad, pad + a.w - 1, pad + h - 1], a.radius, fill=255)
ph = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ph.paste(Image.fromarray(im), (pad, pad)); ph.putalpha(inner)
Image.alpha_composite(card, ph).save(a.out)
print(a.out, W, H)
