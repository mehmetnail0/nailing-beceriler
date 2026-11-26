#!/usr/bin/env python3
"""Plain-words check of an edit.json before the expensive render. usage: check_edit.py edit.json
Exit 0 = nothing wrong, 1 = problems listed (one per line). Needs ffprobe on PATH (or FP env) for source durations."""
import json, os, subprocess, sys

E = json.load(open(sys.argv[1]))
base = os.path.dirname(os.path.abspath(sys.argv[1]))
FP = os.environ.get('FP', 'ffprobe')
bad = []
W, H = 1080, 1920


def low(s):
    return s.replace('İ', 'i').replace('I', 'ı').lower()


def path(p):
    return p if os.path.isabs(p) else os.path.join(os.getcwd(), p)


def dur(f):
    try:
        return float(subprocess.run([FP, '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip())
    except Exception:
        return None


for k in ('style', 'segments', 'mezz', 'audio', 'lut', 'camera', 'caption', 'captions'):
    if k not in E: bad.append(f'edit.json has no "{k}".')
if bad: print('\n'.join(bad)); sys.exit(1)

fps = E.get('fps', 30)
segs = E['segments']
total = 0.0
prev = -1
for i, s in enumerate(segs):
    if s['out'] <= s['in']: bad.append(f'segment {i}: out {s["out"]} is not after in {s["in"]}.')
    for j, q in enumerate(segs[:i]):   # story order is allowed (a hook can come first); the same source moment twice is not
        if s['in'] < q['out'] and q['in'] < s['out']: bad.append(f'segment {i} ({s["in"]}-{s["out"]}) overlaps segment {j} ({q["in"]}-{q["out"]}) in the source.')
    prev = s['out']; total += s['out'] - s['in']
DUR = round(round(total * fps) / fps, 2)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import noface
covered = []
if not E.get('allow_noface'):      # the voice goes on over a card: the take keeps it and the picture holds the speaker (fixed here, never refused)
    NF_ = noface(os.path.join(os.path.dirname(path(E['mezz'])), 'face.json'))
    for i, s in enumerate(E['segments']):
        cv = [[max(a, s['in']), min(b, s['out'])] for a, b in NF_ if min(b, s['out']) - max(a, s['in']) >= 0.05]
        if cv and s.get('cover') != cv:
            s['cover'] = cv; covered.append(f'segment {i}: the speaker\'s picture holds over {cv} (no speaker there; the voice goes on)')
    if covered:
        json.dump(E, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1); print('fixed: ' + '; '.join(covered))

for k in ('mezz', 'audio', 'lut'):
    if not os.path.exists(path(E[k])): bad.append(f'file for "{k}" is missing: {E[k]}' + (' (make it first: python3 scripts/lut.py work/look.cube --strength 0.75; hizli.sh go does this itself)' if k == 'lut' else ''))
if os.path.exists(path(E['mezz'])):
    d = dur(path(E['mezz']))
    if d and segs and segs[-1]['out'] > d + 0.05: bad.append(f'last segment ends at {segs[-1]["out"]} s but mezz.mp4 is only {d:.2f} s long.')
fonts = E.get('fonts', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts'))
for need in ('InstrumentSerif-Italic.ttf', 'Inter.ttf', 'ArchivoBlack-Regular.ttf'):
    if not os.path.exists(os.path.join(fonts, need)): bad.append(f'font {need} not found in {fonts}.')

cam = E['camera']
if not cam: bad.append('camera is empty; put at least one key {t:0,d:0,to:1.0}.')
for k in cam:
    if not E.get('follow') and (k.get('to', 1) < 1.0 or k.get('from', 1) < 1.0): bad.append(f'camera key at {k["t"]}: scale below 1.0 shows the edge of the frame.')
    if k['t'] > DUR + 0.01: bad.append(f'camera key at {k["t"]} s is after the end of the video ({DUR} s).')
    if k.get('d', 0) > 0 and 'bez' not in k and k.get('ease', 'sineInOut') not in ('sineInOut', 'expoInOut', 'backOut', 'linear'):
        bad.append(f'camera key at {k["t"]}: unknown ease "{k.get("ease")}".')

caps = sorted(E['captions'], key=lambda c: c['t'])
for i, c in enumerate(caps):
    if c['e'] <= c['t']: bad.append(f'caption "{c["text"]}": ends before it starts.')
    if c['e'] > DUR + 0.05: bad.append(f'caption "{c["text"]}" runs to {c["e"]} s, past the end ({DUR} s).')
    if i and c['t'] < caps[i - 1]['e'] - 0.001: bad.append(f'captions "{caps[i-1]["text"]}" and "{c["text"]}" overlap in time.')
    n = len(c['text'].split())
    if n > 7: bad.append(f'caption "{c["text"]}" has {n} words; a phrase caption is 2 to 5 words, split it.')
    for kw in c.get('key', []):
        if low(kw.strip('.,!?…“”')) not in [low(w.strip('.,!?…“”')) for w in c['text'].split()]:
            bad.append(f'caption "{c["text"]}": key word "{kw}" is not in the text, so it will not be emphasised.')

cs = E['caption']
cap_top = cs.get('y', 0.74) * H - (cs.get('size', 70) * 1.3 * 2 + 40) / 2   # worst case two lines
z0, z1 = (E['safe'][1], E['safe'][3]) if E.get('safe') else (0.12, 0.86)      # edit.json "safe" (0..1) when the measured refs write lower or higher
if cs.get('y', 0.74) > z1 or cs.get('y', 0.74) < z0:          # fixed here, never refused: the seat comes into the free frame
    y_ = cs.get('y', 0.74); cs['y'] = round(min(max(y_, z0), z1), 4)
    json.dump(E, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
    print(f'fixed: caption y {y_} -> {cs["y"]} (outside the free part of the frame, y {z0}-{z1}: the phone app covers the rest; '
          f'set edit.json "safe": [x0, y0, x1, y1] when your refs measured captions there)')

for a in E.get('accents', []):
    if a['e'] <= a['t']: bad.append(f'accent "{a["text"]}": ends before it starts.')
    if not a.get('hide_caps'): bad.append(f'accent "{a["text"]}": set hide_caps true, or it sits on top of the normal caption.')
    if a['e'] > DUR + 0.05: bad.append(f'accent "{a["text"]}" runs past the end of the video.')

for n, ins in enumerate(E.get('inserts', [])):
    f = path(ins['file'])
    if not os.path.exists(f): bad.append(f'insert {n}: file missing: {ins["file"]}'); continue
    d = None if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) else dur(f)   # a still is held as long as needed
    if d and ins.get('in', 0) + ins['d'] > d + 0.05: bad.append(f'insert {n}: needs {ins.get("in", 0)}..{ins.get("in", 0) + ins["d"]:.2f} s of its file, which is only {d:.2f} s long.')
    if ins['t'] + ins['d'] > DUR + 0.05: bad.append(f'insert {n} runs past the end of the video.')
    if ins.get('full'): continue                  # a whole-frame shot: no card to place
    cw = ins.get('w', 1000)
    x, y, w, h = ins.get('crop', [0, 0, 1920, 1080])
    if cw > W: bad.append(f'insert {n}: card width {cw} is wider than the {W} px canvas.')
    ch = cw * h / w
    bottom = ins.get('y', 0.40) * H + ch / 2
    top_edge = ins.get('y', 0.40) * H - ch / 2
    if top_edge < H * 0.06: bad.append(f'insert {n}: card top is at {top_edge:.0f} px, inside the top safe zone; lower y or narrow the card.')
    for c in caps:
        if c['t'] < ins['t'] + ins['d'] and c['e'] > ins['t'] and bottom > cs.get('y', 0.74) * H - cs.get('size', 70):
            bad.append(f'insert {n}: card bottom ({bottom:.0f} px) reaches the caption "{c["text"]}"; make the card shorter (crop) or move the caption down.'); break

for i, s_ in enumerate(segs):
    x = s_.get('x', E.get('joint_frames', 0)) if i else 0
    if x and (x > (s_['out'] - s_['in']) * fps or x > (segs[i - 1]['out'] - segs[i - 1]['in']) * fps):
        bad.append(f'segment {i}: dissolve of {x} frames is longer than one of the two takes it joins.')
if E.get('follow') and not os.path.exists(path(E['follow'].get('face', ''))): bad.append('follow.face (the face track json) is missing; run facetrack.py first.')
if E['caption'].get('below_face') is not None and not (E.get('follow') or {}).get('face') and not E['caption'].get('face'):
    bad.append('caption.below_face needs a face track: set caption.face to the facetrack.py json (or use follow), else captions sit on the face.')
if E['caption'].get('face') and not os.path.exists(path(E['caption']['face'])): bad.append('caption.face (the face track json) is missing; run facetrack.py first.')
for n, L in enumerate(E.get('layers', [])):
    nm = L.get('text', {}).get('text', L.get('file', L['kind']))
    if L['e'] <= L['t']: bad.append(f'layer {n} ("{nm}"): ends before it starts.')
    if L['e'] > DUR + 0.05: bad.append(f'layer {n} ("{nm}") runs past the end of the video ({DUR} s).')
    if L['kind'] == 'text' and not os.path.exists(os.path.join(fonts, L['text']['font'])): bad.append(f'layer {n}: font {L["text"]["font"]} not found in {fonts}.')
    if L['kind'] == 'image' and not os.path.exists(path(L['file'])): bad.append(f'layer {n}: image missing: {L["file"]}')
    if L['kind'] not in ('text', 'image', 'bar', 'path'): bad.append(f'layer {n}: unknown kind "{L["kind"]}" (text, image, bar, path).')
    if L['kind'] == 'path' and len(L.get('path', {}).get('pts', [])) < 2: bad.append(f'layer {n}: a path needs at least 2 points in path.pts.')
    if L.get('behind') and not E.get('matte'): bad.append(f'layer {n} ("{nm}") is behind the speaker but edit.json has no "matte" (the cut-out model).')
    for side in ('in', 'out'):
        k = L.get(side, {})
        if k.get('d', 0) > 0 and 'bez' not in k and k.get('ease', 'sineInOut') not in ('sineInOut', 'expoInOut', 'backOut', 'linear'):
            bad.append(f'layer {n} {side}: unknown ease "{k.get("ease")}".')
for k_ in ('soft', 'blurcol', 'columns'):
    for n, f_ in enumerate(E.get('fx', {}).get(k_, [])):
        if f_.get('d', 0) <= 0 or f_['t'] + f_['d'] > DUR + 0.05: bad.append(f'fx.{k_} {n}: needs t and d > 0 inside the {DUR} s video.')
        for it in f_.get('items', []) if k_ == 'columns' else []:
            if it.get('file') and not os.path.exists(path(it['file'])): bad.append(f'fx.columns {n}: file missing: {it["file"]}')
            if not it.get('file') and not it.get('speaker'): bad.append(f'fx.columns {n}: each item is {{file}} or {{speaker: true}}.')
        if k_ == 'columns' and not 2 <= len(f_.get('items', [])) <= 4: bad.append(f'fx.columns {n}: 2 to 4 items.')
if any(L.get('track') == 'head' for L in E.get('layers', [])) and not ((E.get('follow') or {}).get('face') or E['caption'].get('face')):
    bad.append('a layer with track "head" needs a face track: follow.face or caption.face.')
for p in E.get('fx', {}).get('bgplate', []):
    if not E.get('matte'): bad.append('fx.bgplate dims the room behind the speaker and needs "matte".'); break
if E.get('matte') and not os.path.exists(path(E['matte']['model'])): bad.append(f'matte model missing: {E["matte"]["model"]} (run scripts/setup_check.py).')
for n, o in enumerate(E.get('overlays', [])):
    miss = [k for k in ('file', 'x', 'y', 'w') if k not in o]
    if miss: bad.append(f'overlay {n}: needs {", ".join(miss)}'); continue
    if not os.path.exists(path(o['file'])): bad.append(f'overlay {n}: file missing: {o["file"]}')
if E.get('music') and not os.path.exists(path(E['music'].get('file', ''))): bad.append(f'music file missing: {E["music"].get("file")}')
for n, x in enumerate(E.get('sfx', [])):
    if not os.path.exists(path(x.get('file', ''))): bad.append(f'sfx {n}: file missing: {x.get("file")}')
    if not 0 <= x.get('t', -1) < DUR: bad.append(f'sfx {n}: t {x.get("t")} is outside the {DUR} s video.')
print(f'video length after cuts: {DUR} s, {len(caps)} captions, {len(cam)} camera keys, {len(E.get("inserts", []))} inserts')
print('\n'.join(bad) if bad else 'ok')
sys.exit(1 if bad else 0)
