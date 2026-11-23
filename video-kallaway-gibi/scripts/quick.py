#!/usr/bin/env python3
"""A one-line ask (“put the logo top right”, “swap that caption”, “change the music”) re-renders only what it changed.
usage: quick.py old_edit.json new_edit.json old_out.mp4 new_out.mp4 [--encoder libx264|h264_nvenc] [--cuda] [--jobs N] [--dry]
- only overlays and/or music changed: no frame is drawn again; the kept <old_out>.video.mp4 is re-mixed (seconds).
- timed items changed (layers, captions, accents, inserts, camera keys, fx entries): each changed span, widened back to the start of
  its take so the matte and camera state match a full render, is rendered alone and spliced into the kept frames.
- anything global (segments, caption style, matte, lut, follow, ...) or changes over 60 % of the reel: a full render.
--jobs N: the full render is split into N parallel slices (render.py --jobs) and changed spans render side by side.
Prints one JSON line: path taken, spans, seconds."""
import argparse, json, os, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
FF = os.environ.get('FF', 'ffmpeg')
TIMED = ('layers', 'captions', 'accents', 'inserts', 'camera')
LIVE = ('overlays', 'music')
FITTED = ('fit', 'legible', 'ui')          # read by render.py --fit, whose moves land in layers and overlays
ap = argparse.ArgumentParser()
ap.add_argument('old'); ap.add_argument('new'); ap.add_argument('old_out'); ap.add_argument('new_out')
ap.add_argument('--encoder', default='libx264'); ap.add_argument('--cuda', action='store_true'); ap.add_argument('--dry', action='store_true')
ap.add_argument('--jobs', type=int, default=1)
a = ap.parse_args()
O, N = json.load(open(a.old)), json.load(open(a.new))
FPS = N.get('fps', 30)
DUR = sum(s['out'] - s['in'] for s in N['segments']) - sum(s.get('x', 0) / FPS for s in N['segments'][1:])
starts, o = [], 0.0
for i, s in enumerate(N['segments']):
    if i: o -= s.get('x', 0) / FPS
    starts.append(o); o += s['out'] - s['in']
T0 = time.time()


def span(item, nxt=None):
    t = item.get('t')
    if t is None: return None
    e = item.get('e', t + item.get('d', 0))
    if nxt is not None: e = max(e, nxt.get('t', e) + nxt.get('d', 0))
    return [t, e]


def diff_spans():
    sp = []
    for k in TIMED:
        ol, nl = O.get(k, []), N.get(k, [])
        oj, nj = [json.dumps(x, sort_keys=True) for x in ol], [json.dumps(x, sort_keys=True) for x in nl]
        for lst, mine, other in ((ol, oj, nj), (nl, nj, oj)):
            srt = sorted(range(len(lst)), key=lambda i: lst[i].get('t', 0))
            for r, i in enumerate(srt):
                if mine[i] in other: continue
                nxt = lst[srt[r + 1]] if k == 'camera' and r + 1 < len(srt) else None   # a camera key also bends the move after it
                s = span(lst[i], nxt) if k != 'camera' or nxt else [lst[i]['t'], DUR]
                if s is None: return None
                sp.append(s)
    of, nf = O.get('fx', {}), N.get('fx', {})
    for k in set(of) | set(nf):
        oj, nj = [json.dumps(x, sort_keys=True) for x in of.get(k, [])], [json.dumps(x, sort_keys=True) for x in nf.get(k, [])]
        for lst, mine, other in ((of.get(k, []), oj, nj), (nf.get(k, []), nj, oj)):
            for x, j in zip(lst, mine):
                if j in other: continue
                s = span(x) if isinstance(x, dict) else None
                if s is None: return None
                sp.append(s)
    return sp


def merge(sp):
    out = []
    for s, e in sorted(sp):
        s = max(0, max([b for b in starts if b <= s + 1e-6], default=0))   # back to the start of the take
        e = min(DUR, e + 0.1)
        if out and s <= out[-1][1] + 0.5: out[-1][1] = max(out[-1][1], e)
        else: out.append([s, e])
    return [[round(s * FPS), round(e * FPS)] for s, e in out]


def cmd(args):
    return [sys.executable, os.path.join(HERE, 'render.py'), a.new] + args + ['--encoder', a.encoder] + (['--cuda'] if a.cuda else [])


def render(args):
    r = subprocess.run(cmd(args), capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr[-1500:])
    return r


def render_all(arg_lists):
    procs, k = [], 0
    while k < len(arg_lists) or procs:
        while k < len(arg_lists) and len(procs) < max(1, a.jobs):
            procs.append(subprocess.Popen(cmd(arg_lists[k]), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)); k += 1
        p = procs.pop(0); err = p.communicate()[1]
        if p.returncode:
            for q in procs: q.kill()
            sys.exit(err[-1500:])


def frames_of(p):
    r = subprocess.run([os.environ.get('FP', 'ffprobe'), '-v', 'error', '-count_packets', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0', p], capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


glob_o = {k: v for k, v in O.items() if k not in TIMED + LIVE + FITTED + ('fx', 'captions')}
glob_n = {k: v for k, v in N.items() if k not in TIMED + LIVE + FITTED + ('fx', 'captions')}
base_old = os.path.splitext(a.old_out)[0] + '.video.mp4'
base_new = os.path.splitext(a.new_out)[0] + '.video.mp4'
sp = diff_spans() if glob_o == glob_n and os.path.exists(base_old) else None
spans = merge(sp) if sp is not None else None
NF = round(DUR * FPS)
if spans is not None and sum(e - s for s, e in spans) > 0.6 * NF: spans = None
how = 'full' if spans is None else ('remix' if not spans else 'splice')
if a.dry:
    print(json.dumps({'path': how, 'spans_s': [[round(s / FPS, 2), round(e / FPS, 2)] for s, e in spans or []]})); sys.exit(0)
if how == 'full':
    render([a.new_out, '--jobs', str(a.jobs)])
elif how == 'remix':
    render([a.new_out, '--reuse-video', base_old])
    if os.path.abspath(base_new) != os.path.abspath(base_old):
        import shutil; shutil.copyfile(base_old, base_new)
else:
    td = tempfile.mkdtemp(prefix='quick-', dir=os.path.dirname(os.path.abspath(a.new_out)))
    parts, inputs, fc, k = [], ['-i', base_old], [], 0
    have = frames_of(base_old)
    if abs(have - NF) > 1: sys.exit(f'the kept frames ({have}) do not match this edit ({NF}): run a full render')
    cur = 0
    render_all([[os.path.join(td, f's{s}.mp4'), '--slice', f'{s / FPS:.6f},{e / FPS:.6f}'] for s, e in spans])
    for s, e in spans:
        sl = os.path.join(td, f's{s}.mp4')
        if s > cur: fc.append(f"[0:v]trim=start_frame={cur}:end_frame={s},setpts=PTS-STARTPTS[p{k}]"); parts.append(f'[p{k}]'); k += 1
        inputs += ['-i', os.path.splitext(sl)[0] + '.video.mp4']; j = inputs.count('-i') - 1
        fc.append(f"[{j}:v]setpts=PTS-STARTPTS[p{k}]"); parts.append(f'[p{k}]'); k += 1; cur = e
    if cur < have: fc.append(f"[0:v]trim=start_frame={cur},setpts=PTS-STARTPTS[p{k}]"); parts.append(f'[p{k}]')
    fc.append(''.join(parts) + f"concat=n={len(parts)}:v=1:a=0[v]")
    venc = (['-c:v', 'h264_nvenc', '-preset', 'p6', '-tune', 'hq', '-rc', 'vbr', '-cq', '18', '-b:v', '0'] if a.encoder == 'h264_nvenc' else ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18'])
    tmp = base_new + '.part.mp4'
    subprocess.run([FF, '-v', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(fc), '-map', '[v]'] + venc + ['-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', tmp], check=True)
    os.replace(tmp, base_new)
    render([a.new_out, '--reuse-video', base_new])
    for f in os.listdir(td): os.remove(os.path.join(td, f))
    os.rmdir(td)
print(json.dumps({'path': how, 'spans_s': [[round(s / FPS, 2), round(e / FPS, 2)] for s, e in spans or []], 'out': a.new_out, 'total_s': round(time.time() - T0, 1)}))
