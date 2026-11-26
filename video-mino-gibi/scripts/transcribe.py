#!/usr/bin/env python3
"""Word-timed transcript with faster-whisper. usage: transcribe.py <media or wav> <out.json> [--lang tr] [--model medium] [--gpu]
Default runs on a laptop CPU (int8). --gpu uses CUDA with large-v3 when an NVIDIA GPU is there. Language auto-detects unless --lang is given.
Needs: pip install faster-whisper numpy ; plain ffmpeg on PATH (or FF env). Output: segments with word start/end/probability."""
import argparse, json, os, subprocess, sys, tempfile, time, wave
import numpy as np
from faster_whisper import WhisperModel

ap = argparse.ArgumentParser()
ap.add_argument('media'); ap.add_argument('out')
ap.add_argument('--lang', default=None); ap.add_argument('--model', default='medium'); ap.add_argument('--gpu', action='store_true')
a = ap.parse_args()
FF = os.environ.get('FF', 'ffmpeg')
wav = a.media
if not a.media.lower().endswith('.wav'):
    wav = os.path.join(tempfile.mkdtemp(), 'a16.wav')
    subprocess.run([FF, '-v', 'error', '-y', '-i', a.media, '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', wav], check=True)
wf = wave.open(wav)
if wf.getframerate() != 16000:   # whisper wants 16 kHz: resample a 48 kHz wav through ffmpeg
    w2 = os.path.join(tempfile.mkdtemp(), 'a16.wav')
    subprocess.run([FF, '-v', 'error', '-y', '-i', wav, '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', w2], check=True); wf = wave.open(w2)
audio = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768.0
t0 = time.time()
kw = dict(language=a.lang, word_timestamps=True, vad_filter=True, beam_size=5)
if a.gpu:
    try:
        m = WhisperModel('large-v3', device='cuda', compute_type='float16'); dev = 'cuda large-v3'
        segs, info = m.transcribe(audio, **kw); segs = list(segs)
    except Exception as e:
        print('GPU failed, CPU fallback:', str(e)[:200], flush=True); a.gpu = False
if not a.gpu:
    m = WhisperModel(a.model, device='cpu', compute_type='int8', cpu_threads=int(os.environ.get('OMP_NUM_THREADS') or min(os.cpu_count() or 4, 8))); dev = f'cpu {a.model}'
    segs, info = m.transcribe(audio, **kw); segs = list(segs)
res = {'device': dev, 'language': info.language, 'secs': round(time.time() - t0, 1), 'segments': [
    {'start': s.start, 'end': s.end, 'text': s.text.strip(),
     'words': [{'w': w.word.strip(), 's': round(w.start, 3), 'e': round(w.end, 3), 'p': round(w.probability, 2)} for w in s.words]}
    for s in segs]}
json.dump(res, open(a.out, 'w'), ensure_ascii=False, indent=1)
print(dev, res['language'], res['secs'], 's')
