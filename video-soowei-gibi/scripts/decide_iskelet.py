"""The shape of a work/decide.py: copy it there (cp scripts/decide_iskelet.py work/decide.py) and fill every value marked REF from the
style's numbers in SKILL.md, the measured refs in reference/ and your look at work/src.jpg. It holds no look of its own: run as it is,
it stops and names what is still empty. Then `bash scripts/hizli.sh go .` (or check_edit.py + render.py by hand).
Every time below is in SOURCE seconds (read them in work/brief.md / work/words.json); timeline.TL turns them into output seconds."""
import json, os, sys
K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # the run folder (this file sits in work/)
sys.path.insert(0, os.path.join(K, 'scripts'))
from timeline import TL, pages_from_words, noface
REF = None

# 1. takes in story order: (in, out) or (in, out, dissolve frames). Cut inside pauses (work/sil.json), never through a stretch in noface().
TAKES = REF                      # e.g. [(0.42, 5.10), (7.60, 12.95)]
# 2. caption pages from the spoken words
WORDS_PER_PAGE = REF             # the refs' words per page
CHARS_PER_PAGE = REF
CAPTION = REF                    # edit.json "caption": font, size, y, colour, stroke/shadow ... as SKILL.md lists them
STYLE = REF                      # edit.json "style": the style's preset name and fields from SKILL.md
CAMERA = REF                     # [{t, d, to, ...}] output-second camera keys; hareket.py (snap, drift) gives eased starting values
FOLLOW = REF                     # {"face": "work/face.json", ...} or {} when the framing is locked
LAYERS = []                      # titles, numbers, cards, bars: [{kind, t, e, x, y, ...}] in output seconds (tl.T(src, take))
EXTRA = {}                       # anything else the style uses: inserts, accents, music, sfx, safe, reserved, ...

empty = [k for k, v in dict(TAKES=TAKES, WORDS_PER_PAGE=WORDS_PER_PAGE, CHARS_PER_PAGE=CHARS_PER_PAGE, CAPTION=CAPTION, STYLE=STYLE,
                            CAMERA=CAMERA, FOLLOW=FOLLOW).items() if v is REF]
if empty: sys.exit('decide.py: fill these from the refs first: ' + ', '.join(empty))

tl = TL(TAKES)
W_ = os.path.join(K, 'work')
E = dict(fps=30, mezz='work/mezz.mp4', audio='work/a48.wav', lut='work/look.cube', fonts='fonts',
         style=STYLE, segments=tl.seg_json(), caption=CAPTION, camera=CAMERA, layers=LAYERS,
         captions=pages_from_words(tl, os.path.join(W_, 'words.json'), max_words=WORDS_PER_PAGE, max_chars=CHARS_PER_PAGE), **EXTRA)
if FOLLOW: E['follow'] = FOLLOW
json.dump(E, open(os.path.join(W_, 'edit.json'), 'w'), ensure_ascii=False, indent=1)
print('edit.json:', round(tl.dur, 2), 's,', len(E['segments']), 'takes,', len(E['captions']), 'pages; no-speaker stretches in the source:', noface(os.path.join(W_, 'face.json')))
