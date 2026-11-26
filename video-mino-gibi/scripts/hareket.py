"""Eased motion, as numbers you can put straight into edit.json (camera keys and layer moves). Import it in decide.py:
    sys.path.insert(0, 'scripts'); from hareket import AE, move_d, snap, drift
These are measured starting values, not a look: the refs you read (reference/hareket*.json, your own ref) win over them.
  AE        cubic-bezier(0.5, 0, 0.2, 1.08): slow start, about 3 % past the mark, settle (the After Effects "easy ease" feel)
  move_d    how long a move of N px should take so it reads as a move, not a jump (300 px or more: at least 0.75 s)
  snap      a quick push on an emphasis line (1.18x in 0.32 s, ease-out) and a slow way back
  drift     a slow push through a long hold so the frame is never frozen (about 5 % over the hold)"""

AE = [0.5, 0.0, 0.2, 1.08]
OUT = [0.16, 1.0, 0.3, 1.0]          # ease-out: leaves fast, settles


def move_d(px, short=0.35, long=0.75, far=300):
    """seconds for a move of px pixels: 0.35 s for a nudge, rising to 0.75 s at 300 px, a little longer beyond."""
    px = abs(px)
    if px >= far: return round(long + 0.15 * min(1.0, (px - far) / 600), 3)
    return round(short + (long - short) * px / far, 3)


def snap(t, base=1.0, scale=1.18, d=0.32, back=0.8, hold=0.6):
    """camera keys for one emphasis: push to base*scale over d (ease-out), hold, then ease back over back seconds."""
    return [dict(t=round(t, 3), d=d, to=round(base * scale, 4), bez=OUT),
            dict(t=round(t + d + hold, 3), d=back, to=base, bez=AE)]


def drift(t, d, base=1.0, amount=0.05):
    """one camera key: a slow push of amount over a hold of d seconds (use on holds of 1.6 s or more)."""
    return dict(t=round(t, 3), d=round(d, 3), to=round(base * (1 + amount), 4), bez=[0.37, 0.0, 0.63, 1.0])


def bez_y(b, x):
    """value of a cubic-bezier easing at progress x (0..1), for checking a curve by numbers."""
    x1, y1, x2, y2 = b
    lo, hi = 0.0, 1.0
    for _ in range(40):
        s = (lo + hi) / 2
        xs = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s ** 2 * x2 + s ** 3
        lo, hi = (s, hi) if xs < x else (lo, s)
    s = (lo + hi) / 2
    return 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s ** 2 * y2 + s ** 3
