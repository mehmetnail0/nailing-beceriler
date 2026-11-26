#!/usr/bin/env python3
"""The reel is done only when its FINAL mix passes the word-level cut QC. Run from the skill folder after render.py:
    cutgate.py work/out.mp4 [--edit work/edit.json] [--words work/words.json] [--lang tr] [--rounds 4] [--render "<cmd>"]
Each round: kesim_qc.py (shared script, vendored unchanged) on the final mix at every cut -> cutfix.py writes the fixes
into work/cut_fixes.json -> decide.py, check_edit.py and the render run again -> QC again. Exit 0 = clean, with the cut list
(time, last words | first words) in work/cutqc/PASS.json; exit 2 = the model's ear is needed: a word said twice inside one take, or a spot
that failed again after an engine fix (work/cutqc/judge.json: set it in cut_fixes.json, run again); exit 1 = still faulty: the reel is not done."""
import argparse, json, os, re, subprocess, sys

H = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--edit', default='work/edit.json')
ap.add_argument('--words', default='work/words.json'); ap.add_argument('--lang', default=None, help='default: the language transcribe.py found in --words'); ap.add_argument('--rounds', type=int, default=4)
ap.add_argument('--render', default=''); ap.add_argument('--out', default='work/cutqc')
A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
if not A.lang: A.lang = (json.load(open(A.words)).get('language') if os.path.exists(A.words) else None) or 'tr'
import shutil
GPU = bool(shutil.which('nvidia-smi')) and subprocess.run(['nvidia-smi', '-L'], capture_output=True).returncode == 0
render = A.render or f'{sys.executable} {H}/render.py {A.edit} {A.video} --encoder ' + ('h264_nvenc' if GPU else 'libx264')
py = lambda *a: subprocess.run([sys.executable, *a], capture_output=True, text=True)
log = []
nw = lambda i: {re.sub(r'\W', '', w).casefold() for w in i['words']} - {''}
same = lambda i, j: abs(i['t'] - j['t']) < 0.6 and any(a.startswith(b) or b.startswith(a) for a in nw(i) for b in nw(j))
for r in range(1, A.rounds + 1):
    E = json.load(open(A.edit)); fps = E.get('fps', 30); o, pieces = 0, []
    for s in E['segments']:
        fi, fo = round(s['in'] * fps), round(s['out'] * fps); pieces.append(dict(o=round(o / fps, 3), src='main', **{'in': fi / fps, 'out': fo / fps})); o += fo - fi
    cj = f'{A.out}/cuts_r{r}.json'; json.dump(dict(pieces=pieces), open(cj, 'w')); cuts = pieces[1:]
    src = ['--src', E['audio']] if E.get('audio') and os.path.exists(E['audio']) else []
    q = py(f'{H}/kesim_qc.py', A.video, '--cuts', cj, '--lang', A.lang, '--out', f'{A.out}/r{r}', *src)
    if not os.path.exists(f'{A.out}/r{r}/report.json'):
        sys.exit(f'kesim_qc.py wrote no report (exit {q.returncode}):\n' + (q.stderr or q.stdout)[-1500:])
    R = json.load(open(f'{A.out}/r{r}/report.json'))
    log.append(dict(round=r, cuts=len(cuts), issues=R['issues']))
    if q.returncode == 0 and not R['issues']: break
    back = [i for i in R['issues'] if len(log) > 1 and log[-2].get('rerendered') and any(same(i, j) for j in log[-2]['issues'])]
    if back:     # the engine moved this spot and the same words failed again: the source stamps are wrong here, so the model listens
        J = [dict(words=i['words'], out_t=i['t'], kind=i['kind'], wav=next((c['wav'] for c in R['cuts'] if abs(c['t'] - (i.get('cut') or i['t'])) < 0.05), ''),
                  why='same spot failed after an engine fix') for i in back]
        json.dump(J, open(f'{A.out}/judge.json', 'w'), ensure_ascii=False, indent=1)
        print(json.dumps(dict(done=False, why='a spot the engine already fixed failed again: listen to the cut wav and the source, then set its edges '
                              'in work/cut_fixes.json (drop / snap / keep) and run cutgate again', judge=J, log=log), ensure_ascii=False)); sys.exit(2)
    f = py(f'{H}/cutfix.py', f'{A.out}/r{r}/report.json', A.edit, A.words)
    fr = json.loads(f.stdout); log[-1]['fix'] = fr
    if not fr['changed']:
        if fr['unmapped']: print(json.dumps(dict(done=False, why='issues the engine cannot place', log=log), ensure_ascii=False)); sys.exit(1)
        if fr['judge']:
            json.dump(fr['judge'], open(f'{A.out}/judge.json', 'w'), ensure_ascii=False, indent=1)
            print(json.dumps(dict(done=False, why='the model judges each word said twice in one take: listen, then put its span in '
                                  'work/cut_fixes.json "drop" (a stumble) or "keep" (meant), and run cutgate again', judge=fr['judge']), ensure_ascii=False)); sys.exit(2)
        R['issues'] = []; log[-1]['all_checked'] = True; break
    for cmd in ([sys.executable, 'work/decide.py'], [sys.executable, f'{H}/check_edit.py', A.edit]):
        c = subprocess.run(cmd, capture_output=True, text=True)
        if c.returncode or (cmd[-1] == A.edit and not c.stdout.strip().endswith('ok')):
            print(json.dumps(dict(done=False, why=f'{cmd[-1]} failed', err=(c.stdout + c.stderr)[-800:], log=log), ensure_ascii=False)); sys.exit(1)
    c = subprocess.run(render, shell=True, capture_output=True, text=True)
    if c.returncode: print(json.dumps(dict(done=False, why='render failed', err=c.stderr[-800:], log=log))); sys.exit(1)
    log[-1]['rerendered'] = True
else:
    print(json.dumps(dict(done=False, why=f'issues left after {A.rounds} rounds', log=log), ensure_ascii=False)); sys.exit(1)
P = dict(done=True, video=A.video, rounds=len(log), cuts=[dict(t=c['t'], left=' '.join(c['left']), right=' '.join(c['right']), wav=c['wav']) for c in R['cuts']],
         fixed=[x for l in log for x in l.get('fix', {}).get('changed', [])], checked=[x for l in log for x in l.get('fix', {}).get('checked', [])],
         warnings=R.get('warnings', []), log=log)
json.dump(P, open(f'{A.out}/PASS.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: P[k] for k in ('done', 'rounds', 'fixed', 'checked')}, ensure_ascii=False)); print(f'{len(P["cuts"])} cuts clean -> {A.out}/PASS.json')
