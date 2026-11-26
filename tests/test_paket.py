"""Run: python3 -m pytest tests -q   (needs numpy and Pillow; nothing else, no network)"""
import copy, importlib.util, json, os, sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import denetim  # noqa: E402

VS = denetim.video_skills(ROOT)


def load(skill, name):
    spec = importlib.util.spec_from_file_location(f'{skill}_{name}', os.path.join(ROOT, skill, 'scripts', name + '.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def test_package_is_clean():
    assert denetim.denetle(ROOT) == []


def make(tmp, files):
    for rel, body in files.items():
        p = tmp / rel; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body if isinstance(body, bytes) else body.encode())
    return str(tmp)


GOOD = '---\nname: ok-skill\ndescription: does a thing\n---\n# x\n'


@pytest.mark.parametrize('files, expect', [
    ({'ok-skill/SKILL.md': '# no frontmatter\n'}, 'no frontmatter'),
    ({'ok-skill/SKILL.md': GOOD.replace('name: ok-skill', 'name: other')}, 'not the folder name'),
    ({'ok-skill/SKILL.md': GOOD + 'run `scripts/yok.py`\n'}, 'refers to scripts/yok.py'),
    ({'ok-skill/SKILL.md': GOOD + 'see /Users/someone/x\n'}, 'personal Mac path'),
    ({'ok-skill/SKILL.md': GOOD + 'copy to /root/box\n'}, 'server path'),
    ({'ok-skill/SKILL.md': GOOD + 'made for GZT\n'}, 'client name'),
    ({'ok-skill/SKILL.md': GOOD + 'see `handoffs/x/notes.md`\n'}, 'internal notes path'),
    ({'ok-skill/SKILL.md': GOOD + 'the Tigno engine\n'}, 'internal product name'),
    ({'ok-skill/SKILL.md': GOOD, 'ok-skill/.env': 'A=1\n'}, '.env file'),
    ({'ok-skill/SKILL.md': GOOD + 'key sk-ant-abcdefghijklmnop1234\n'}, 'secret key'),
    ({'ok-skill/SKILL.md': GOOD, 'ok-skill/a.mogrt': b'x'}, '.mogrt'),
    ({'ok-skill/SKILL.md': GOOD, 'ok-skill/look.cube': 'LUT_3D_SIZE 2\n'}, 'LUT'),
    ({'ok-skill/SKILL.md': GOOD, 'ok-skill/fonts/DINPro-Bold.otf': b'x', 'ok-skill/fonts/OFL.txt': 'x'}, 'paid brand font'),
    ({'ok-skill/SKILL.md': GOOD, 'ok-skill/fonts/Free.ttf': b'x'}, 'font without a licence'),
    ({'ok-skill/SKILL.md': GOOD, 'ok-skill/sfx/whoosh.wav': b'x'}, 'audio without a licence note'),
    ({'ok-skill/SKILL.md': GOOD, 'ok-skill/clip.mp4': b'x'}, 'video file'),
])
def test_guard_catches(tmp_path, files, expect):
    probs = denetim.denetle(make(tmp_path, files))
    assert any(expect in p for p in probs), probs


def test_guard_passes_licensed_audio_and_fonts(tmp_path):
    root = make(tmp_path, {'ok-skill/SKILL.md': GOOD + 'uses `fonts/Free.ttf`\n', 'ok-skill/fonts/Free.ttf': b'x', 'ok-skill/fonts/OFL.txt': 'x',
                           'ok-skill/sfx/whoosh.wav': b'x', 'ok-skill/sfx/LISANS.md': 'whoosh.wav: CC0, https://freesound.org/...\n'})
    assert denetim.denetle(root) == []


def test_guard_sees_drifting_shared_scripts(tmp_path):
    root = make(tmp_path, {'a/SKILL.md': GOOD.replace('ok-skill', 'a'), 'a/scripts/x.py': 'print(1)\n',
                           'b/SKILL.md': GOOD.replace('ok-skill', 'b'), 'b/scripts/x.py': 'print(2)\n'})
    assert any('differs' in p for p in denetim.denetle(root))


@pytest.mark.parametrize('skill', VS)
def test_setup_check_lists_every_import(skill):
    sc = load(skill, 'setup_check')
    listed = {m for m, _ in sc.PKGS}
    stdlib = set(sys.stdlib_module_names)
    local = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(ROOT, skill, 'scripts'))}
    used = set()
    for f in os.listdir(os.path.join(ROOT, skill, 'scripts')):
        if f.endswith('.py'): used |= denetim.imports(os.path.join(ROOT, skill, 'scripts', f))
    missing = used - stdlib - local - listed
    assert not missing, f'imported by scripts/ but not checked by setup_check.py: {missing}'


def test_hdr_lut_maps_black_and_white():
    h = load(VS[0], 'hdr_lut')
    for kind in ('hlg', 'pq'):
        rows = h.build(kind, n=9)
        assert rows.shape == (9 ** 3, 3)
        assert rows[0].max() < 0.01                       # black stays black
        assert ((rows >= 0) & (rows <= 1)).all()
        # grey ramp rises monotonically
        grey = [rows[i * 81 + i * 9 + i].mean() for i in range(9)]
        assert all(b >= a for a, b in zip(grey, grey[1:]))
    assert h.build('hlg', n=9)[-1].min() > 0.9            # HLG peak white lands near SDR white


def test_hareket_values():
    m = load(VS[0], 'hareket')
    assert m.move_d(300) >= 0.75 and m.move_d(900) >= 0.75 and m.move_d(40) < 0.75
    k = m.snap(2.0)
    assert k[0]['to'] == 1.18 and k[0]['d'] == 0.32
    assert abs(m.bez_y(m.AE, 1.0) - 1) < 1e-6 and m.bez_y(m.AE, 0.0) < 1e-6
    assert max(m.bez_y(m.AE, x / 100) for x in range(101)) > 1.0     # AE overshoots a little, then settles


def edit():
    return {'caption': {'font': 'Inter.ttf', 'size': 70, 'y': 0.95},
            'captions': [{'t': 0, 'e': 1, 'text': 'bu bir deneme cümlesi oldukça uzun olsun'}],
            'layers': [{'kind': 'text', 't': 0, 'e': 2, 'x': 0.97, 'y': 0.5, 'text': {'font': 'Inter.ttf', 'size': 120, 'text': 'BÜYÜK'}},
                       {'kind': 'bar', 't': 0, 'e': 2, 'x': 0.5, 'y': 0.3, 'bar': {'w': 300, 'h': 120, 'color': '#000000'}},
                       {'kind': 'text', 't': 0, 'e': 2, 'x': 0.5, 'y': 0.3, 'text': {'font': 'Inter.ttf', 'size': 140, 'text': 'KARTTA UZUN YAZI'}},
                       {'kind': 'text', 't': 0, 'e': 2, 'x': 0.5, 'y': 0.5, 'move': [{'t': 0, 'd': 0.3, 'dx': 400}],
                        'text': {'font': 'Inter.ttf', 'size': 60, 'text': 'a'}}]}


def test_yerlesim_finds_then_fixes():
    y = load(VS[0], 'yerlesim'); fonts = os.path.join(ROOT, VS[0], 'fonts')
    E = edit()
    _, left, notes = y.check(copy.deepcopy(E), fonts, fix=False)
    assert any(l.startswith('safe: caption') for l in left)
    assert any('BÜYÜK' in l for l in left) and any(l.startswith('card:') for l in left)
    assert any(n.startswith('move:') for n in notes)          # a 400 px move in 0.3 s is named, not refused
    fixed, left, _ = y.check(E, fonts, fix=True)
    assert fixed and left == []
    assert y.check(E, fonts, fix=False)[1] == []               # what it fixed holds on a fresh check
    card = y.layer_box(E['layers'][1], fonts); txt = y.layer_box(E['layers'][2], fonts)
    assert y.inside(txt, card)


def test_yerlesim_reserved_corner():
    y = load(VS[0], 'yerlesim'); fonts = os.path.join(ROOT, VS[0], 'fonts')
    E = {'reserved': [[0.6, 0.4, 0.9, 0.6]], 'layers': [{'kind': 'text', 't': 0, 'e': 1, 'x': 0.7, 'y': 0.5, 'text': {'font': 'Inter.ttf', 'size': 80, 'text': 'logo altında'}}]}
    assert any(l.startswith('corner:') for l in y.check(E, fonts)[1])


def test_example_edits_place_cleanly():
    """every shipped example edit passes the placement check after its own fix (a member copies these)."""
    for s in VS:
        p = os.path.join(ROOT, s, 'example', 'edit.json')
        if not os.path.exists(p): continue
        E = json.load(open(p)); y = load(s, 'yerlesim')
        y.check(E, os.path.join(ROOT, s, 'fonts'), fix=True)
        assert y.check(E, os.path.join(ROOT, s, 'fonts'))[1] == [], s


def test_yerlesim_safe_area_comes_from_the_edit():
    y = load(VS[0], 'yerlesim'); fonts = os.path.join(ROOT, VS[0], 'fonts')
    L = {'kind': 'text', 't': 0, 'e': 1, 'x': 0.5, 'y': 0.08, 'text': {'font': 'Inter.ttf', 'size': 60, 'text': 'Adım 1'}}
    assert y.check({'layers': [dict(L)]}, fonts)[1]                                   # default: the top label sits under the app bar
    assert y.check({'safe': [0.05, 0.05, 0.9, 0.86], 'layers': [dict(L)]}, fonts)[1] == []   # the refs measured it there
