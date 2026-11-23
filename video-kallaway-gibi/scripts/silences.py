#!/usr/bin/env python3
"""Pauses in the voice track (ffmpeg silencedetect). usage: silences.py <a48.wav> <out.json> [--db -35] [--min 0.2]
Output: {"silences": [[start, end], ...]} in source seconds. Cut points belong inside these spans, never inside a word."""
import argparse, json, os, re, subprocess
ap = argparse.ArgumentParser(); ap.add_argument('wav'); ap.add_argument('out')
ap.add_argument('--db', type=float, default=-35); ap.add_argument('--min', type=float, default=0.2)
a = ap.parse_args()
r = subprocess.run([os.environ.get('FF', 'ffmpeg'), '-hide_banner', '-nostats', '-i', a.wav, '-af', f'silencedetect=n={a.db}dB:d={a.min}', '-f', 'null', '-'],
                   capture_output=True, text=True)
st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', r.stderr)]
en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r.stderr)]
sil = [[round(s, 2), round(e, 2)] for s, e in zip(st, en)]
json.dump({'silences': sil}, open(a.out, 'w'))
print(len(sil), 'pauses')
