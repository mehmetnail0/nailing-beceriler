#!/usr/bin/env python3
"""One-command setup check for this skill: python3 scripts/setup_check.py
Checks ffmpeg (lut3d, loudnorm, acrossfade), the python packages, an optional NVIDIA GPU, and fetches the free models into ./models
(YuNet face detector from opencv_zoo, MODNet and RVM person mattes from Hugging Face / GitHub). Prints what is missing and how to install it; exit 0 = ready."""
import hashlib, importlib, os, shutil, subprocess, sys, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = {
    'yunet.onnx': ('https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx', None),
    'modnet.onnx': ('https://huggingface.co/Xenova/modnet/resolve/main/onnx/model.onnx', '07c308cf0fc7e6e8b2065a12ed7fc07e1de8febb7dc7839d7b7f15dd66584df9'),
    'rvm.onnx': ('https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx', '88d4531297118f595bf2fd60f6f566aec2e559393802d1f436c380f0cbbd2828'),
}
PKGS = [('numpy', 'numpy'), ('cv2', 'opencv-contrib-python'), ('PIL', 'Pillow'), ('scipy', 'scipy'), ('faster_whisper', 'faster-whisper'),
        ('onnxruntime', 'onnxruntime'), ('soundfile', 'soundfile')]   # every import of every script in scripts/ (tests/test_paket.py keeps this list whole)


def main():
    bad, pip = [], []
    ff = os.environ.get('FF', 'ffmpeg')
    if not shutil.which(ff) or not shutil.which(os.environ.get('FP', 'ffprobe')):
        bad.append('ffmpeg + ffprobe on PATH  (mac: brew install ffmpeg · linux: apt install ffmpeg · windows: gyan.dev build)')
    else:
        f = subprocess.run([ff, '-hide_banner', '-filters'], capture_output=True, text=True).stdout
        for flt in ('lut3d', 'loudnorm', 'acrossfade'):   # zscale is optional: mezz.sh turns an HDR clip to SDR with hdr_lut.py without it
            if f' {flt} ' not in f: bad.append(f'ffmpeg filter "{flt}" missing: use a full build (brew ffmpeg / johnvansickle static / gyan full)')
    for mod, pip_name in PKGS:
        try: importlib.import_module(mod)
        except Exception: pip.append(pip_name)
    try:
        import cv2
        if not hasattr(cv2, 'FaceDetectorYN'): bad.append('opencv too old for YuNet: pip install -U opencv-contrib-python')
    except Exception: pass
    os.makedirs(os.path.join(ROOT, 'models'), exist_ok=True)
    for name, (url, sha) in MODELS.items():
        p = os.path.join(ROOT, 'models', name)
        if not os.path.exists(p):
            if name == 'rvm.onnx': print('note: downloading rvm.onnx (RobustVideoMatting, GPL-3.0, https://github.com/PeterL1n/RobustVideoMatting). It is fetched to your own machine at first run and is not part of this package.')
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'skill-setup-check'})
                with urllib.request.urlopen(req, timeout=120) as r, open(p + '.part', 'wb') as o: shutil.copyfileobj(r, o)
                os.replace(p + '.part', p)
            except Exception as e:
                bad.append(f'model {name}: download failed ({e}); fetch {url} into models/'); continue
        if sha and hashlib.sha256(open(p, 'rb').read()).hexdigest() != sha:
            bad.append(f'model {name}: checksum mismatch, delete models/{name} and re-run')
    gpu = 'none (CPU path: transcribe --model medium, render --encoder libx264)'
    if shutil.which('nvidia-smi'):
        r = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip(): gpu = r.stdout.strip().splitlines()[0] + ' (transcribe --gpu, render --encoder h264_nvenc)'
    print('gpu:', gpu)
    if pip:
        bad.append('python packages missing, install them with this one line:\n     python3 -m pip install ' + ' '.join(pip)
                   + ('\n     (on an NVIDIA machine use onnxruntime-gpu instead of onnxruntime)' if 'onnxruntime' in pip else ''))
    if bad:
        print('NOT READY:'); [print(' -', b) for b in bad]; sys.exit(1)
    print('ready')


if __name__ == '__main__':
    main()
