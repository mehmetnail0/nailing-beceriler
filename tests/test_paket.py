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


def test_yerlesim_title_lines_move_as_one_block():
    """a two-line title under the app bar moves down together, the lines never stack on each other."""
    y = load(VS[0], 'yerlesim'); fonts = os.path.join(ROOT, VS[0], 'fonts')
    T = lambda yy, txt, sz: {'kind': 'text', 't': 0, 'e': 3, 'x': 0.5, 'y': yy, 'text': {'font': 'Inter.ttf', 'size': sz, 'text': txt}}
    E = {'layers': [T(0.045, 'Wikipedia', 90), T(0.1, 'özgür ansiklopedi', 110)]}
    assert y.ink_box(E['layers'][1], fonts)[1] > y.ink_box(E['layers'][0], fonts)[3]
    fixed, left, _ = y.check(E, fonts, fix=True)
    assert fixed and left == []
    a, b = (y.ink_box(L, fonts) for L in E['layers'])
    assert b[1] > a[3] and not y.inter(a, b)                                   # still two lines, one under the other
    assert y.check(E, fonts)[1] == []


def test_yerlesim_counts_the_pop_in():
    """a big word that pops in at 1.18x is checked at its biggest, so it is not cut by the frame edge at the peak."""
    y = load(VS[0], 'yerlesim'); fonts = os.path.join(ROOT, VS[0], 'fonts')
    L = {'kind': 'text', 't': 0, 'e': 2, 'x': 0.5, 'y': 0.4, 'in': {'d': 0.25, 'scale': 1.18}, 'text': {'font': 'Inter.ttf', 'size': 145, 'text': '60 MİLYON'}}
    E = {'layers': [L]}
    y.check(E, fonts, fix=True)
    b = y.layer_box(L, fonts)
    assert b[0] >= 70 - 0.5 and b[2] <= 940 + 0.5


def test_yerlesim_names_overlapping_text():
    y = load(VS[0], 'yerlesim'); fonts = os.path.join(ROOT, VS[0], 'fonts')
    T = lambda yy, txt: {'kind': 'text', 't': 0, 'e': 3, 'x': 0.5, 'y': yy, 'move': [{'t': 0, 'd': 1, 'dx': 0}], 'text': {'font': 'Inter.ttf', 'size': 90, 'text': txt}}
    assert any(l.startswith('overlap:') for l in y.check({'layers': [T(0.4, 'bir'), T(0.42, 'iki')]}, fonts)[1])


def test_noface_spans_and_check_edit_covers_a_take_through_one(tmp_path):
    """frames with no face (a title card in the clip) become source spans; check_edit covers a take that runs through one."""
    tl = load(VS[0], 'timeline')
    f = [[1, 1, 1, 1]] * 60 + [[]] * 30 + [[1, 1, 1, 1]] * 60 + [[]] * 3 + [[1, 1, 1, 1]] * 10
    (tmp_path / 'face.json').write_text(json.dumps({'fps': 30, 'f': f}))
    assert tl.noface(str(tmp_path / 'face.json')) == [(2.0, 3.0)]          # a 0.1 s blink is not a card
    import subprocess
    w = tmp_path / 'work'; w.mkdir()
    (w / 'face.json').write_text(json.dumps({'fps': 30, 'f': f}))
    for n in ('mezz.mp4', 'a48.wav', 'look.cube'): (w / n).write_bytes(b'x')
    E = {'mezz': 'work/mezz.mp4', 'audio': 'work/a48.wav', 'lut': 'work/look.cube', 'fps': 30, 'style': {}, 'caption': {'y': 0.7},
         'segments': [{'in': 0.5, 'out': 4.5}], 'captions': [], 'camera': [{'t': 0, 'd': 0, 'to': 1.0}]}
    (w / 'edit.json').write_text(json.dumps(E))
    r = subprocess.run([sys.executable, os.path.join(ROOT, VS[0], 'scripts', 'check_edit.py'), 'work/edit.json'], cwd=tmp_path, capture_output=True, text=True)
    assert 'holds over' in r.stdout, r.stdout + r.stderr                  # fixed, not refused: the voice goes on, the picture holds the speaker
    assert json.load(open(w / 'edit.json'))['segments'][0]['cover'] == [[2.0, 3.0]]
    E['segments'] = [{'in': 0.5, 'out': 1.9}, {'in': 3.1, 'out': 4.5}]; (w / 'edit.json').write_text(json.dumps(E))
    r = subprocess.run([sys.executable, os.path.join(ROOT, VS[0], 'scripts', 'check_edit.py'), 'work/edit.json'], cwd=tmp_path, capture_output=True, text=True)
    assert 'holds over' not in r.stdout and 'cover' not in json.load(open(w / 'edit.json'))['segments'][0], r.stdout


def test_check_edit_caption_zone_follows_the_edit_safe_area(tmp_path):
    import subprocess
    w = tmp_path / 'work'; w.mkdir()
    for n in ('mezz.mp4', 'a48.wav', 'look.cube'): (w / n).write_bytes(b'x')
    E = {'mezz': 'work/mezz.mp4', 'audio': 'work/a48.wav', 'lut': 'work/look.cube', 'fps': 30, 'style': {}, 'caption': {'y': 0.875},
         'segments': [{'in': 0.5, 'out': 4.5}], 'captions': [], 'camera': [{'t': 0, 'd': 0, 'to': 1.0}]}
    run = lambda: subprocess.run([sys.executable, os.path.join(ROOT, VS[0], 'scripts', 'check_edit.py'), 'work/edit.json'], cwd=tmp_path, capture_output=True, text=True).stdout
    (w / 'edit.json').write_text(json.dumps(E)); out = run()
    assert 'caption y 0.875 -> 0.86' in out and json.load(open(w / 'edit.json'))['caption']['y'] == 0.86   # fixed, not refused
    E['safe'] = [0.05, 0.1, 0.9, 0.9]; (w / 'edit.json').write_text(json.dumps(E)); assert 'caption y' not in run()


def test_decide_skeleton_stops_empty_then_writes_an_edit(tmp_path):
    """the decide.py skeleton carries no look: empty it names what to fill; filled it writes an edit.json the check reads."""
    import shutil, subprocess
    run = tmp_path / 'kurgu-1'; (run / 'work').mkdir(parents=True)
    shutil.copytree(os.path.join(ROOT, VS[0], 'scripts'), run / 'scripts')
    shutil.copy(os.path.join(ROOT, VS[0], 'scripts', 'decide_iskelet.py'), run / 'work' / 'decide.py')
    words = {'language': 'tr', 'segments': [{'words': [{'w': w, 's': 0.5 + i * 0.4, 'e': 0.8 + i * 0.4, 'p': 0.9} for i, w in enumerate('bu bir deneme cümlesi'.split())]}]}
    (run / 'work' / 'words.json').write_text(json.dumps(words))
    r = subprocess.run([sys.executable, 'work/decide.py'], cwd=run, capture_output=True, text=True)
    assert r.returncode and 'TAKES' in r.stderr
    d = (run / 'work' / 'decide.py').read_text()
    for k, v in {'TAKES': '[(0.4, 2.2)]', 'WORDS_PER_PAGE': '2', 'CHARS_PER_PAGE': '20', 'CAPTION': "{'y': 0.7}", 'STYLE': "{}",
                 'CAMERA': "[{'t': 0, 'd': 0, 'to': 1.0}]", 'FOLLOW': '{}'}.items():
        d = d.replace(f'{k} = REF', f'{k} = {v}', 1)
    (run / 'work' / 'decide.py').write_text(d)
    r = subprocess.run([sys.executable, 'work/decide.py'], cwd=run, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    E = json.load(open(run / 'work' / 'edit.json'))
    assert E['segments'] and E['captions'] and E['captions'][0]['text'].startswith('bu')


def test_noface_counts_a_short_flash_where_the_picture_jumps(tmp_path):
    tl = load(VS[0], 'timeline')
    f = [[1, 1, 1, 1]] * 60 + [[]] * 3 + [[1, 1, 1, 1]] * 60
    (tmp_path / 'face.json').write_text(json.dumps({'fps': 30, 'f': f, 'jumps': [60, 63]}))
    assert tl.noface(str(tmp_path / 'face.json')) == [(2.0, 2.1)]       # a green flash frame, not a blink


def _render(tmp_path, colour, caption, face=None, layers=(), seg=None, at=0.5):
    """a 1 s plain clip of one colour through render.py; returns the report and the middle frame (RGB)."""
    import subprocess, numpy as np
    w = tmp_path / 'work'; w.mkdir(exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', colour if '=' in colour else f'color=c={colour}:s=1440x2560:r=30:d=1', '-f', 'lavfi', '-i',
                    'sine=f=220:d=1:sample_rate=48000', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-shortest', str(w / 'mezz.mp4')], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(w / 'mezz.mp4'), '-vn', '-ac', '1', '-ar', '48000', str(w / 'a48.wav')], check=True)
    (w / 'look.cube').write_text('LUT_3D_SIZE 2\n' + ''.join(f'{r} {g} {b}\n' for b in (0, 1) for g in (0, 1) for r in (0, 1)))   # identity
    E = {'mezz': 'work/mezz.mp4', 'audio': 'work/a48.wav', 'lut': 'work/look.cube', 'fps': 30, 'style': {}, 'fonts': os.path.join(ROOT, VS[0], 'fonts'),
         'segments': [seg or {'in': 0, 'out': 1}], 'camera': [{'t': 0, 'd': 0, 'to': 1.0}], 'caption': caption,
         'captions': [{'t': 0, 'e': 1, 'text': 'beyaz yazı'}], 'layers': list(layers)}
    if face: (w / 'face.json').write_text(json.dumps(face)); E['caption']['face'] = 'work/face.json'
    (w / 'edit.json').write_text(json.dumps(E))
    r = subprocess.run([sys.executable, os.path.join(ROOT, VS[0], 'scripts', 'render.py'), 'work/edit.json', 'work/out.mp4'], cwd=tmp_path,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-800:]
    rep = json.loads([x for x in r.stdout.splitlines() if x.startswith('{')][-1])
    fr = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(at), '-i', str(w / 'out.mp4'), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                        capture_output=True, check=True).stdout
    return rep, np.frombuffer(fr, np.uint8).reshape(1920, 1080, 3)


@pytest.mark.skipif(not __import__('shutil').which('ffmpeg') or not importlib.util.find_spec('cv2') or not importlib.util.find_spec('scipy'),
                    reason='a render test needs ffmpeg and the skills\' own install (setup_check.py)')
def test_render_gives_an_unreadable_caption_a_halo(tmp_path):
    """white letters on a white picture: the render measures it and outlines the page by itself; on black it leaves it alone."""
    cap = {'y': 0.7, 'size': 80, 'color': '#FFFFFF', 'stroke': [0, '#FFFFFF']}
    rep, fr = _render(tmp_path, 'white', dict(cap))
    assert rep['caps_halo'] == [0.0]
    band = fr[int(0.64 * 1920):int(0.76 * 1920)]
    assert band.min() < 80                                                   # something dark now edges the letters
    assert rep['caps_box'] == []                                             # a plain picture: an outline is enough
    rep, _ = _render(tmp_path, 'black', dict(cap))
    assert rep['caps_halo'] == []
    rep, _ = _render(tmp_path, 'life=s=1440x2560:r=30:ratio=0.7:mold=0:life_color=#FFFFFF:death_color=#000000:seed=3', dict(cap))
    assert rep['caps_box'] == [0.0], rep                                     # a busy print: the page gets a backing box
    rep, fr = _render(tmp_path, "color=c=black:s=1440x2560:r=30:d=1,format=yuv420p,geq=lum='if(lt(T,0.3),16,235)':cb=128:cr=128", dict(cap), at=0.9)
    assert rep['caps_halo'] == [0.0], rep                                    # the picture turns white mid-page: the outline comes in then
    assert fr[int(0.64 * 1920):int(0.76 * 1920)].min() < 80


@pytest.mark.skipif(not __import__('shutil').which('ffmpeg') or not importlib.util.find_spec('cv2') or not importlib.util.find_spec('scipy'),
                    reason='a render test needs ffmpeg and the skills\' own install (setup_check.py)')
def test_render_moves_a_caption_off_a_low_face(tmp_path):
    """the face fills the bottom of the frame, so under the chin there is no room: the page goes above the hair instead."""
    box = [720, 1800, 300, 300, 1400, 840, 1100, 0.9]             # eye centre, eye distance, face box x y w h (y 1400-2500 of a 2560 mezz)
    face = {'w': 1440, 'h': 2560, 'fps': 30, 'f': [box] * 30}
    rep, _ = _render(tmp_path, 'gray', {'y': 0.74, 'size': 70, 'below_face': 0.02, 'y_max': 0.86}, face)
    assert rep['caps_moved_above_face'] == [0.0] and rep['caps_on_face'] == []


@pytest.mark.skipif(not __import__('shutil').which('ffmpeg') or not importlib.util.find_spec('cv2') or not importlib.util.find_spec('scipy'),
                    reason='a render test needs ffmpeg and the skills\' own install (setup_check.py)')
def test_render_moves_a_title_off_the_head(tmp_path):
    """a title set across the speaker's head moves above the hair by itself; one marked on_face stays where the edit put it."""
    box = [720, 1350, 200, 300, 1000, 840, 900, 0.9]               # head from y 685 (hair) to 1900 of a 2560 mezz
    face = {'w': 1440, 'h': 2560, 'fps': 30, 'f': [box] * 30}
    title = {'kind': 'text', 't': 0, 'e': 1, 'x': 0.5, 'y': 0.45, 'text': {'text': 'BAŞLIK', 'font': 'Inter.ttf', 'size': 90}}
    rep, _ = _render(tmp_path, 'gray', {'y': 0.8, 'size': 60}, face, [dict(title)])
    assert rep['layers_moved_off_face'] == [0] and rep['layers_on_face'] == [], rep
    rep, _ = _render(tmp_path, 'gray', {'y': 0.8, 'size': 60}, face, [dict(title, on_face=True)])
    assert rep['layers_moved_off_face'] == []
    tall = {'w': 1440, 'h': 2560, 'fps': 30, 'f': [[720, 1000, 150, 620, 60, 200, 2480, 0.9]] * 30}    # a head from top to bottom: no room above or under
    num = {'kind': 'text', 't': 0, 'e': 1, 'x': 0.5, 'y': 0.45, 'text': {'text': '1.', 'font': 'Inter.ttf', 'size': 90}}
    rep, fr = _render(tmp_path, 'gray', {'y': 0.8, 'size': 60}, tall, [num])
    assert rep['layers_moved_off_face'] == [0] and rep['layers_on_face'] == [], rep          # beside the head instead
    card = {'kind': 'bar', 't': 0, 'e': 1, 'x': 0.5, 'y': 0.45, 'bar': {'w': 1000, 'h': 160, 'color': '#FFFFFF'}}
    rep, _ = _render(tmp_path, 'gray', {'y': 0.8, 'size': 60}, tall, [dict(num, y=0.40), card])
    assert rep['layers_moved_off_face'] == [0] and rep['layers_on_face'] == [], rep          # a card beside it too: slides to a free height


def test_cutfix_judges_a_whole_word_in_source_seconds_then_honours_keep(tmp_path):
    """“lisansla lisanslanmıştır” is meant Turkish: the engine never drops it alone, it hands the model a span in SOURCE seconds;
    once that span is in "keep" it is never asked again."""
    import subprocess
    ws = [('bu', 10.0, 10.2), ('program', 10.25, 10.7), ('lisansla', 11.0, 11.4), ('lisanslanmıştır', 11.5, 12.2), ('ve', 12.3, 12.4)]
    (tmp_path / 'words.json').write_text(json.dumps({'segments': [{'words': [{'w': w, 's': a, 'e': b, 'p': 0.9} for w, a, b in ws]}]}))
    E = {'fps': 30, 'audio': 'none.wav', 'segments': [{'in': 9.5, 'out': 13.0}]}
    (tmp_path / 'edit.json').write_text(json.dumps(E))
    R = {'issues': [{'kind': 'false_start', 't': 1.5, 'words': ['lisansla', 'lisanslanmıştır']}],
         'words': [{'w': w, 's': a - 9.5, 'e': b - 9.5} for w, a, b in ws]}
    (tmp_path / 'report.json').write_text(json.dumps(R))
    run = lambda: json.loads(subprocess.run([sys.executable, os.path.join(ROOT, VS[0], 'scripts', 'cutfix.py'), 'report.json', 'edit.json', 'words.json'],
                                            cwd=tmp_path, capture_output=True, text=True).stdout)
    r = run()
    assert not r['changed'] and len(r['judge']) == 1
    a, b = r['judge'][0]['src_span']
    assert 10.7 <= a <= 11.0 and 11.4 <= b <= 11.5                          # source seconds round “lisansla”, not output seconds
    fx = json.load(open(tmp_path / 'cut_fixes.json')) if (tmp_path / 'cut_fixes.json').exists() else {}
    fx['keep'] = [[a, b]]; (tmp_path / 'cut_fixes.json').write_text(json.dumps(fx))
    r = run()
    assert r['judge'] == [] and r['checked']


def test_cutfix_closes_an_opened_edge_in_to_the_words_and_may_run_over_a_card(tmp_path):
    """a joint that failed again after its edge was opened: --retreat closes the out edge to just after the take's last whole
    word and the in edge to just before the next take's first word. A word cut by an edge inside a stretch with no speaker is let
    finish (the picture holds there), not left cut."""
    import subprocess
    ws = [('özgür', 10.8, 11.2), ('lisanslanmıştır', 11.5, 12.96), ('Günümüzü', 13.26, 13.7), ('güncelleyebilir', 23.38, 24.18), ('Bir', 25.2, 25.4), ('site', 25.45, 25.8)]
    (tmp_path / 'words.json').write_text(json.dumps({'segments': [{'words': [{'w': w, 's': a, 'e': b, 'p': 0.9} for w, a, b in ws]}]}))
    (tmp_path / 'face.json').write_text(json.dumps({'w': 100, 'h': 100, 'fps': 30, 'f': [[50, 50, 10, 40, 40, 20, 20, .9]] * 708 + [None] * 56 + [[50, 50, 10, 40, 40, 20, 20, .9]] * 300}))
    E = {'fps': 30, 'audio': 'none.wav', 'segments': [{'in': 10.5, 'out': 13.1}, {'in': 23.0, 'out': 24.0}, {'in': 25.1, 'out': 26.0}]}
    (tmp_path / 'edit.json').write_text(json.dumps(E))
    run = lambda R, *x: json.loads(subprocess.run([sys.executable, os.path.join(ROOT, VS[0], 'scripts', 'cutfix.py'), 'report.json', 'edit.json', 'words.json', *x],
                                                  cwd=tmp_path, capture_output=True, text=True).stdout)
    (tmp_path / 'report.json').write_text(json.dumps({'issues': [{'kind': 'in_word', 't': 2.6, 'cut': 2.6, 'words': ['Ayrıca']}], 'words': []}))
    r = run(None, '--retreat', '2.6')
    assert r['unmapped'] == [] and any('closes to its last whole word' in x for x in r['changed'])
    snap = json.load(open(tmp_path / 'cut_fixes.json'))['snap']
    assert any(abs(o - 13.1) < 0.02 and 12.96 <= n <= 13.02 for o, n in snap)                 # just after “lisanslanmıştır”, before 13.26
    (tmp_path / 'cut_fixes.json').unlink()
    (tmp_path / 'report.json').write_text(json.dumps({'issues': [{'kind': 'in_word', 't': 3.6, 'cut': 3.6, 'words': ['güncelleyebilir']}],
                                                      'words': [{'w': 'güncelleyebilir', 's': 3.0, 'e': 3.7}]}))
    r = run(None)
    snap = json.load(open(tmp_path / 'cut_fixes.json'))['snap']
    assert any(abs(o - 24.0) < 0.02 and n >= 24.18 for o, n in snap), r                     # finishes inside the card stretch (23.6-25.47)
    assert r['unmapped'] == []                                                                  # the cut at the last joint maps to a source edge
    (tmp_path / 'cut_fixes.json').unlink()
    E['segments'] = [{'in': 25.0, 'out': 26.0}, {'in': 0.03, 'out': 1.0}]; (tmp_path / 'edit.json').write_text(json.dumps(E))
    (tmp_path / 'words.json').write_text(json.dumps({'segments': [{'words': [{'w': 'Türkiye', 's': 0.0, 'e': 0.3, 'p': 0.9}, {'w': 'site', 's': 25.45, 'e': 25.8, 'p': 0.9}]}]}))
    (tmp_path / 'report.json').write_text(json.dumps({'issues': [{'kind': 'in_word', 't': 1.0, 'cut': 1.0, 'words': ['Türkiye']}],
                                                      'words': [{'w': 'Türkiye', 's': 0.95, 'e': 1.25}]}))
    run(None)
    assert all(n >= 0 for _, n in json.load(open(tmp_path / 'cut_fixes.json'))['snap'])          # an edge never opens before the clip starts


@pytest.mark.skipif(not __import__('shutil').which('ffmpeg') or not importlib.util.find_spec('cv2') or not importlib.util.find_spec('scipy'),
                    reason='a render test needs ffmpeg and the skills\' own install (setup_check.py)')
def test_render_holds_the_speaker_over_a_covered_card(tmp_path):
    """a moving source; the take covers 0.33-0.67 s: every frame in there is the same held picture, outside it moves."""
    src = 'testsrc2=s=1440x2560:r=30:d=1'
    cov = {'in': 0, 'out': 1, 'cover': [[0.333, 0.667]]}
    frames = [_render(tmp_path, src, {'y': 0.8, 'size': 40}, seg=cov, at=t)[1] for t in (0.4, 0.6)]
    assert abs(frames[0].astype(int) - frames[1].astype(int)).mean() < 2
    plain = [_render(tmp_path, src, {'y': 0.8, 'size': 40}, at=t)[1] for t in (0.4, 0.6)]
    assert abs(plain[0].astype(int) - plain[1].astype(int)).mean() > 2


@pytest.mark.skipif(not __import__('shutil').which('ffmpeg') or not importlib.util.find_spec('cv2') or not importlib.util.find_spec('scipy'),
                    reason='a render test needs ffmpeg and the skills\' own install (setup_check.py)')
def test_render_fits_the_head_under_a_top_panel_and_keeps_captions_out_of_it(tmp_path):
    """a black panel over the top half: the follow crop puts the hair under it (padding above the clip if needed), and a caption with
    no room under the chin is not moved up into the panel."""
    box = [720, 700, 260, 400, 420, 640, 800, 0.9]                # a head high in the clip: hair near the top
    face = {'w': 1440, 'h': 2560, 'fps': 30, 'f': [box] * 30}
    panel = {'kind': 'bar', 't': 0, 'e': 1, 'x': 0.5, 'y': 0.255, 'bar': {'w': 1080, 'h': 980, 'color': '#08080A'}}
    w = tmp_path / 'work'; w.mkdir()
    (w / 'face.json').write_text(json.dumps(face))
    _render(tmp_path, 'testsrc2=s=1440x2560:r=30:d=1', {'y': 0.6, 'size': 60, 'below_face': 0.02, 'y_max': 0.7}, face, [panel])
    E = json.load(open(w / 'edit.json')); E['follow'] = {'face': 'work/face.json'}; (w / 'edit.json').write_text(json.dumps(E))
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(ROOT, VS[0], 'scripts', 'render.py'), 'work/edit.json', 'work/out.mp4'], cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-800:]
    rep = json.loads([x for x in r.stdout.splitlines() if x.startswith('{')][-1])
    assert rep['caps_moved_above_face'] == []                                # never up into the panel
    assert rep['head_in_panel'] == []                                        # the hair sits under the panel


def test_caption_pages_keep_a_name_and_a_turkish_suffix_whole():
    """«Türkiye Kullanıcı Grubu» is one name: pages never break inside it; «Wikipedia 'nın» from the ASR joins to «Wikipedia'nın»."""
    sys.path.insert(0, os.path.join(ROOT, VS[0], 'scripts'))
    import importlib; tlm = importlib.import_module('timeline')
    ws = 'Türkiye Kullanıcı Grubu üyesi Caner.'.split()
    assert [' '.join(ws[i:j]) for i, j in tlm.split_phrase(ws, 4, 24)] == ['Türkiye Kullanıcı Grubu', 'üyesi Caner.']
    words = [('Bugün', 0.0, 0.3), ('Wikipedia', 0.35, 0.9), ("'nın", 0.9, 1.1), ('gücü', 1.15, 1.5), ('büyük.', 1.55, 2.0)]
    d = {'segments': [{'words': [{'w': w, 's': a, 'e': b} for w, a, b in words]}]}
    caps = tlm.pages_from_words(tlm.TL([(0.0, 2.0)], fixes={}), d, 4, 24)
    text = ' '.join(c['text'] for c in caps)
    assert "Wikipedia'nın" in text and " 'nın" not in text, text
