"""Every change the engine made on its own in the last go, in one list (nothing moves silently). usage: soyle.py work/
Reads work/yerlesim.txt, work/check.txt (their "fixed:" lines) and the render report in work/render.txt; prints one line each."""
import json, os, sys

TELL = (('caps_halo', 'caption pages outlined (low contrast)'), ('caps_box', 'caption pages on a backing box (busy picture)'),
        ('caps_moved_above_face', 'caption pages moved above the hair'), ('caps_on_face', 'STILL ON THE FACE, fix it in the edit'),
        ('layers_moved_off_face', 'text layers moved off the head'), ('layers_on_face', 'text layers STILL ON THE HEAD, fix it in the edit'),
        ('head_in_panel', 'the head STILL REACHES INTO THE TOP PANEL (lower follow.max or frame wider)'))


def said(W):
    out = []
    for f in ('yerlesim.txt', 'check.txt'):
        p = os.path.join(W, f)
        if os.path.exists(p): out += [f'{f[:-4]}: {x.strip()[7:]}' for x in open(p) if x.startswith('fixed:')]
    p = os.path.join(W, 'render.txt')
    js = [x for x in open(p) if x.startswith('{"out"')] if os.path.exists(p) else []
    R = json.loads(js[-1]) if js else {}
    out += [f'render: {why}: {R[k]}' for k, why in TELL if R.get(k)]
    return out or ['the engine changed nothing on its own']


if __name__ == '__main__':
    print('\n'.join(said(sys.argv[1] if len(sys.argv) > 1 else 'work')))
