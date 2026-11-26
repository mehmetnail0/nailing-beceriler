#!/usr/bin/env python3
"""Where every word lands, checked and FIXED before the render. usage: yerlesim.py work/edit.json [--fix] [--json]
Checks that hold for any style (none of them is a look):
  safe   captions, text layers and small images stay inside the part of the frame the phone app leaves free
         (Reels/TikTok at 1080x1920: x 70-940, y 230-1640; the right strip holds the like/comment buttons);
         bars and full-width plates are backgrounds and may bleed off the edge; edit.json "safe": [x0, y0, x1, y1] (0..1) replaces
         the area when the refs you measured write somewhere else (a top label at y 0.07): the refs decide, this is the default
  card   a text layer that sits on a card (a bar or image layer under its centre at the same time) fits inside that card
  corner nothing written enters a reserved corner: edit.json "reserved": [[x0, y0, x1, y1], ...] in 0..1 of the frame (your logo, a handle)
  move   (note only) a layer move of 300 px or more that lasts under 0.75 s reads as a jump; see hareket.py
With --fix it moves or shrinks what it can (a caption seat, a layer's x/y, a text size, caption.maxw) and writes edit.json back;
what it cannot fix is listed and the exit code is 1. hizli.sh runs it with --fix after decide.py, so a re-run of decide.py is safe."""
import argparse, json, os, sys
from PIL import ImageFont

W, H = 1080, 1920
SAFE = (70, 230, 940, 1640)


def font(fonts, name, size, weight=None):
    f = ImageFont.truetype(os.path.join(fonts, name), max(8, int(size)))
    if weight:
        try:
            vals = []
            for ax in f.get_variation_axes():
                nm = ax.get('name', b''); nm = nm.decode() if isinstance(nm, bytes) else str(nm)
                vals.append(weight if 'eight' in nm or nm == 'wght' else ax['default'])
            f.set_variation_by_axes(vals)
        except Exception:
            pass
    return f


def low(s):
    return s.replace('İ', 'i').replace('I', 'ı').lower()


def caption_box(cap, cs, fonts):
    """the box render.py draws for one caption page (explicit caption font; the style presets fall back to Inter)."""
    size = cs.get('size', 70)
    fn = font(fonts, cs.get('font', 'Inter.ttf'), size, cs.get('weight'))
    fk = font(fonts, cs.get('key_font', cs.get('font', 'Inter.ttf')), size * cs.get('key_scale', 1.0), cs.get('key_weight', cs.get('weight')))
    keys = {low(k.strip('.,!?…“”')) for k in cap.get('key', [])}
    gap, maxw = fn.getlength(' '), cs.get('maxw', 880)
    lines, cur, cw = [], [], 0.0
    for w in cap['text'].split():
        ww = (fk if low(w.strip('.,!?…“”')) in keys else fn).getlength(w)
        if cur and cw + gap + ww > maxw: lines.append(cw); cur, cw = [], 0.0
        cur.append(w); cw += (gap if cw else 0) + ww
    if cur: lines.append(cw)
    asc, desc = fk.getmetrics(); lh = (asc + desc) * cs.get('lh', 1.08)
    bw, bh = max(lines or [0]), lh * len(lines)
    cy = cs.get('y', 0.74) * H
    return [W / 2 - bw / 2, cy - bh / 2, W / 2 + bw / 2, cy + bh / 2]


def layer_box(L, fonts, at_end=False):
    """settled box of a text / bar / image layer (after its moves when at_end)."""
    dx = sum(m.get('dx', 0) for m in L.get('move', [])) if at_end else 0
    dy = sum(m.get('dy', 0) for m in L.get('move', [])) if at_end else 0
    ax, ay = L.get('x', 0.5) * W + dx, L.get('y', 0.5) * H + dy
    if L['kind'] == 'text':
        T = L['text']; fn = font(fonts, T['font'], T['size'], T.get('weight'))
        asc, desc = fn.getmetrics(); lh = (asc + desc) * T.get('lh', 1.1); trk = T.get('tracking', 0)
        lines = T['text'].split('\n')
        w = max(fn.getlength(ln) + trk * max(0, len(ln) - 1) for ln in lines); h = lh * len(lines)
    elif L['kind'] == 'bar':
        w, h = L['bar']['w'], L['bar']['h']
    elif L['kind'] == 'image' and os.path.exists(L.get('file', '')):
        from PIL import Image
        im = Image.open(L['file']); w = L.get('w', im.width); h = im.height * w / im.width
    else:
        return None
    x0 = ax - w / 2 if L.get('align', 'center') == 'center' or L['kind'] == 'image' else ax
    return [x0, ay - h / 2, x0 + w, ay + h / 2]


def inter(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def inside(a, b, pad=0):
    return a[0] >= b[0] + pad - 0.5 and a[1] >= b[1] + pad - 0.5 and a[2] <= b[2] - pad + 0.5 and a[3] <= b[3] - pad + 0.5


def shift_into(box, area):
    """dx, dy that bring box inside area (box must fit)."""
    dx = max(0, area[0] - box[0]) - max(0, box[2] - area[2])
    dy = max(0, area[1] - box[1]) - max(0, box[3] - area[3])
    return dx, dy


def check(E, fonts, fix=False):
    fixed, left, notes = [], [], []
    SF = [v * (W if i % 2 == 0 else H) for i, v in enumerate(E['safe'])] if E.get('safe') else SAFE   # the edit's own free area (0..1) when its refs write elsewhere
    reserved = [[r[0] * W, r[1] * H, r[2] * W, r[3] * H] for r in E.get('reserved', [])]
    sw, sh = SF[2] - SF[0], SF[3] - SF[1]
    cs = E.get('caption', {})
    caps = E.get('captions', [])
    # captions: one seat for all pages, so the fix is global (maxw, then the seat y)
    if caps and os.path.exists(os.path.join(fonts, cs.get('font', 'Inter.ttf'))):
        half = min(W / 2 - SF[0], SF[2] - W / 2)
        boxes = [caption_box(c, cs, fonts) for c in caps]
        if max(b[2] - b[0] for b in boxes) > 2 * half:
            if fix: cs['maxw'] = int(2 * half); fixed.append(f'caption.maxw -> {cs["maxw"]} (a line ran into the app buttons)'); boxes = [caption_box(c, cs, fonts) for c in caps]
            else: left.append('safe: a caption line is wider than the free part of the frame (caption.maxw)')
        top, bot = min(b[1] for b in boxes), max(b[3] for b in boxes)
        if top < SF[1] - 0.5 or bot > SF[3] + 0.5:
            dy = SF[1] + 2 - top if top < SF[1] else SF[3] - 2 - bot
            if fix and bot - top <= sh: cs['y'] = round(cs.get('y', 0.74) + dy / H, 4); fixed.append(f'caption.y -> {cs["y"]} (pages left the safe area)'); boxes = [caption_box(c, cs, fonts) for c in caps]
            else: left.append(f'safe: caption pages reach y {top:.0f}-{bot:.0f}, outside {SF[1]}-{SF[3]}')
        for c, b in zip(caps, boxes):
            for r in reserved:
                if inter(b, r): left.append(f'corner: caption "{c["text"]}" at {c["t"]:.2f} s enters a reserved corner; move caption.y or the corner')
    layers = E.get('layers', [])
    for n, L in enumerate(layers):
        if L['kind'] not in ('text', 'bar', 'image'): continue
        nm = L.get('text', {}).get('text', L.get('file', L['kind'])).replace('\n', ' ')
        for at_end in (False, True) if L.get('move') else (False,):
            b = layer_box(L, fonts, at_end)
            if not b: break
            if L['kind'] == 'text' and (b[2] - b[0] > sw or b[3] - b[1] > sh):
                k = min(sw / (b[2] - b[0]), sh / (b[3] - b[1]))
                if fix: L['text']['size'] = int(L['text']['size'] * k); fixed.append(f'layer {n} "{nm}": size -> {L["text"]["size"]} (wider than the free frame)'); b = layer_box(L, fonts, at_end)
                else: left.append(f'safe: layer {n} "{nm}" is bigger than the free frame')
            if not inside(b, SF) and not L.get('full') and L['kind'] != 'bar' and b[2] - b[0] < 0.9 * W:   # a bar or a full-width plate is a background, it may bleed
                b0 = layer_box(L, fonts); u = [min(b[0], b0[0]), min(b[1], b0[1]), max(b[2], b0[2]), max(b[3], b0[3])]   # start and end both must land inside
                if fix and u[2] - u[0] <= sw and u[3] - u[1] <= sh:
                    dx, dy = shift_into(u, SF); L['x'] = round(L.get('x', 0.5) + dx / W, 4); L['y'] = round(L.get('y', 0.5) + dy / H, 4)
                    fixed.append(f'layer {n} "{nm}": moved {dx:+.0f}, {dy:+.0f} px into the safe area')
                else: left.append(f'safe: layer {n} "{nm}" {"after its moves " if at_end else ""}reaches outside the free frame ({[round(v) for v in b]})')
            b = layer_box(L, fonts, at_end)
            for r in reserved:
                if inter(b, r): left.append(f'corner: layer {n} "{nm}" enters a reserved corner')
        for m in L.get('move', []):
            dist = (m.get('dx', 0) ** 2 + m.get('dy', 0) ** 2) ** 0.5
            if dist >= 300 and m.get('d', 0) < 0.75: notes.append(f'move: layer {n} "{nm}" travels {dist:.0f} px in {m.get("d", 0)} s (300 px or more reads as a jump under 0.75 s)')
    # card: a text layer whose centre sits on a bar/image layer that is on screen with it
    for n, L in enumerate(layers):
        if L['kind'] != 'text': continue
        b = layer_box(L, fonts); cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        for m, C in enumerate(layers):
            if C['kind'] not in ('bar', 'image') or C.get('full') or not (C['t'] < L['e'] and L['t'] < C['e']): continue
            cb = layer_box(C, fonts)
            if not cb or not (cb[0] <= cx <= cb[2] and cb[1] <= cy <= cb[3]): continue
            pad = 0.04 * (cb[2] - cb[0])
            if inside(b, cb, pad): break
            k = min((cb[2] - cb[0] - 2 * pad) / (b[2] - b[0]), (cb[3] - cb[1] - 2 * pad) / (b[3] - b[1]))
            if fix and k < 1: L['text']['size'] = int(L['text']['size'] * k); b = layer_box(L, fonts); fixed.append(f'layer {n} "{L["text"]["text"][:30]}": size -> {L["text"]["size"]} to fit its card (layer {m})')
            dx, dy = shift_into(b, [cb[0] + pad, cb[1] + pad, cb[2] - pad, cb[3] - pad])
            if fix and (dx or dy): L['x'] = round(L.get('x', 0.5) + dx / W, 4); L['y'] = round(L.get('y', 0.5) + dy / H, 4); fixed.append(f'layer {n}: moved {dx:+.0f}, {dy:+.0f} px onto its card')
            if not fix: left.append(f'card: layer {n} "{L["text"]["text"][:30]}" spills out of its card (layer {m})')
            break
    return fixed, left, notes


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('edit'); ap.add_argument('--fix', action='store_true'); ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    E = json.load(open(a.edit))
    fonts = E.get('fonts', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts'))
    fixed, left, notes = check(E, fonts, a.fix)
    if a.fix and fixed: json.dump(E, open(a.edit, 'w'), ensure_ascii=False, indent=1)
    if a.json: print(json.dumps(dict(fixed=fixed, left=left, notes=notes), ensure_ascii=False))
    else:
        for x in fixed: print('fixed:', x)
        for x in notes: print('note:', x)
        for x in left: print('left:', x)
        print('ok' if not left else f'{len(left)} left')
    sys.exit(1 if left else 0)
