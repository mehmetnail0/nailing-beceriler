"""Package guard: denetle(root) -> a list of problems (empty = the package is safe to publish).
Every rule here is about what may ship in a public skills package, none is about taste."""
import ast, glob, hashlib, os, re

TEXT = ('.md', '.py', '.sh', '.json', '.txt', '.svg', '.yml', '.yaml', '.toml', '.cfg', '.html', '.css', '.js')
NOT_SKILLS = {'gorseller', 'kilavuzlar', 'tests', '.git', '.github'}
BANNED_EXT = {'.mogrt': 'Premiere template (.mogrt)', '.cube': 'LUT file', '.3dl': 'LUT file', '.lut': 'LUT file', '.aep': 'After Effects project',
              '.prproj': 'Premiere project', '.mp4': 'video file', '.mov': 'video file', '.webm': 'video file', '.mkv': 'video file', '.m4v': 'video file'}
AUDIO = ('.wav', '.mp3', '.m4a', '.aac', '.flac', '.ogg', '.opus', '.aif', '.aiff')
FONTS = ('.ttf', '.otf', '.woff', '.woff2')
PAID_FONTS = re.compile(r'din[\s_-]?pro|dinpro|realhead|alameda', re.I)
NAMES = [(re.compile(p, f), why) for p, f, why in [
    (r'\bGZT\b', re.I, 'client name'), (r'\bRana\b', 0, 'client presenter name'), (r'Çayır', 0, 'client presenter name'),
    (r'Sare\s+Aydın', 0, 'client presenter name'), (r'\bTigno\b', re.I, 'internal product name'), (r'gzt-kit', re.I, 'internal path'),
    (r'/Users/', 0, 'a personal Mac path'), (r'/root/', 0, 'a server path'), (r'~/Works\b', 0, 'internal folder'), (r'/lanes/', 0, 'internal box path'), (r'\bhandoffs/', 0, 'internal notes path'),
    (r'backblazeb2|b2://|s3://|\bb2_bucket', re.I, 'storage bucket'), (r'185\.226\.\d+\.\d+', 0, 'server address')]]
KEYS = [re.compile(p) for p in [r'sk-ant-[A-Za-z0-9_\-]{10,}', r'\bsk-[A-Za-z0-9]{32,}', r'AKIA[0-9A-Z]{16}', r'\bghp_[A-Za-z0-9]{30,}',
                                r'\bxox[abps]-[A-Za-z0-9-]{10,}', r'-----BEGIN [A-Z ]*PRIVATE KEY-----', r'\bnk_[A-Za-z0-9]{16,}',
                                r'AIza[0-9A-Za-z_\-]{30,}', r'\b[a-f0-9]{32}:[a-f0-9]{32}\b']]
REF = re.compile(r'(?<![\w/.$-])((?:scripts|reference|example|fonts|sablonlar|referans|ornekler)/[\w.\-*/<>]*\w)')
SKIP_REF = re.compile(r'^example/ilk-ornek$')


def files(root):
    for d, ds, fs in os.walk(root):
        ds[:] = [x for x in ds if x not in ('.git', '__pycache__', 'models', '.pytest_cache')]
        for f in fs:
            if f != '.DS_Store': yield os.path.join(d, f)


def frontmatter(text):
    m = re.match(r'---\n(.*?)\n---\n', text, re.S)
    if not m: return None
    out = {}
    for ln in m.group(1).splitlines():
        if ':' in ln and not ln.startswith(' '): k, v = ln.split(':', 1); out[k.strip()] = v.strip()
    return out


def skills(root):
    return sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and d not in NOT_SKILLS and not d.startswith('.'))


def check_skill(root, name):
    out, base = [], os.path.join(root, name)
    p = os.path.join(base, 'SKILL.md')
    if not os.path.exists(p): return [f'{name}: no SKILL.md']
    text = open(p, encoding='utf-8').read()
    fm = frontmatter(text)
    if fm is None: return [f'{name}/SKILL.md: no frontmatter (--- name / description ---)']
    if fm.get('name') != name: out.append(f'{name}/SKILL.md: name "{fm.get("name")}" is not the folder name')
    if not fm.get('description'): out.append(f'{name}/SKILL.md: no description')
    srcs = [p] + [x for x in files(base) if x.endswith(('.sh', '.py', '.md')) and x != p]
    for src in srcs:
        t = open(src, encoding='utf-8', errors='replace').read().replace('$S/', 'scripts/').replace('$K/scripts/', 'scripts/')
        for ref in set(REF.findall(t)):
            ref = re.sub(r'<[^>]*>', '*', ref.rstrip('.'))
            if SKIP_REF.match(ref): continue
            hits = glob.glob(os.path.join(base, ref)) if '*' in ref else [os.path.join(base, ref)] if os.path.exists(os.path.join(base, ref)) else []
            if not hits: out.append(f'{os.path.relpath(src, root)}: refers to {ref}, which is not in {name}/')
    return out


def check_files(root):
    out, audio_ok = [], {}
    for f in files(root):
        rel = os.path.relpath(f, root); ext = os.path.splitext(f)[1].lower(); low = os.path.basename(f).lower()
        if rel.startswith('tests' + os.sep): continue
        if low == '.env' or low.startswith('.env.') or low.endswith('.env'): out.append(f'{rel}: an .env file')
        if low in ('credentials.json', 'id_rsa', 'id_ed25519') or ext in ('.pem', '.key', '.p12'): out.append(f'{rel}: a key file')
        if ext in BANNED_EXT: out.append(f'{rel}: {BANNED_EXT[ext]} may not ship')
        if ext in FONTS:
            if PAID_FONTS.search(low): out.append(f'{rel}: a paid brand font')
            d = os.path.dirname(f)
            if not any(os.path.exists(os.path.join(d, x)) for x in ('OFL.txt', 'LICENSE', 'LICENSE.txt', 'LISANS.md')): out.append(f'{rel}: font without a licence file next to it')
        if ext in AUDIO:
            d = os.path.dirname(f); notes = ''.join(open(x, encoding='utf-8', errors='replace').read() for x in glob.glob(os.path.join(d, '*'))
                                                    if os.path.basename(x).lower().startswith(('license', 'lisans', 'kaynak', 'credits')))
            if os.path.basename(f) not in notes: out.append(f'{rel}: audio without a licence note (name it in LISANS.md / kaynak.json next to it)')
        if ext in TEXT or low in ('readme', 'skill.md'):
            t = open(f, encoding='utf-8', errors='replace').read()
            for rx, why in NAMES:
                m = rx.search(t)
                if m: out.append(f'{rel}: "{m.group(0)}" ({why})')
            for rx in KEYS:
                m = rx.search(t)
                if m: out.append(f'{rel}: looks like a secret key ({m.group(0)[:8]}...)')
            if PAID_FONTS.search(t) and ext != '.md': out.append(f'{rel}: names a paid brand font')
    return out


def video_skills(root):
    return [s for s in skills(root) if os.path.isdir(os.path.join(root, s, 'scripts'))]


def check_shared(root):
    """the scripts are one engine copied into every video skill (each skill is installed alone), so they must stay identical."""
    out, vs = [], video_skills(root)
    if not vs: return out
    def h(d): return {os.path.relpath(f, d): hashlib.sha256(open(f, 'rb').read()).hexdigest() for f in files(d)}
    first = h(os.path.join(root, vs[0], 'scripts'))
    for s in vs[1:]:
        other = h(os.path.join(root, s, 'scripts'))
        for k in sorted(set(first) | set(other)):
            if first.get(k) != other.get(k): out.append(f'{s}/scripts/{k} differs from {vs[0]}/scripts/{k}')
    return out


def imports(path):
    tree = ast.parse(open(path, encoding='utf-8').read())
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import): mods |= {a.name.split('.')[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level: mods.add(n.module.split('.')[0])
    return mods


def denetle(root):
    out = []
    for s in skills(root): out += check_skill(root, s)
    return out + check_files(root) + check_shared(root)
