"""Phase-A reordering and frame selection on #466's rank151/mixed bit word, with #466's complex supplier unchanged.
Usage: python -B research/r740-dual-kernel-reorder/verify.py /absolute/new/output [--quick] [--selection FILE] [--reuse-parent DIR]
Runs #466's complete verifier as the parent, deterministically rebuilds the new bit word from #466's word and the frozen
selection, re-runs every bit-side check of #466 on it (official C++ legality/columns/k4, record mutations, Gram frames,
emitter, independent audit) and the exact assembly against #466's freshly rebuilt complex supplier.
Apache-2.0. Prepared with substantial Anthropic Claude assistance.
"""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, time
assert __debug__
ROOT = Path(__file__).resolve().parent; RES = ROOT.parent; PARENT = RES / 'r740-dual-kernel'
out = Path(sys.argv[1]).resolve(); quick = '--quick' in sys.argv[2:]
sel = Path(sys.argv[sys.argv.index('--selection') + 1]).resolve() if '--selection' in sys.argv else ROOT / 'data/selection.json'
assert not out.exists() and not out.is_relative_to(RES)
read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory(p):
    return {f.relative_to(p).as_posix(): sha(f) for f in p.rglob('*') if f.is_file() and '__pycache__' not in f.parts}
def integrity():
    if not (ROOT / 'MANIFEST.json').exists(): return False          # unfrozen development tree
    actual = inventory(ROOT); actual.pop('MANIFEST.json')
    assert actual == read(ROOT / 'MANIFEST.json'), 'package manifest differs'
    for name, pins in read(ROOT / 'SOURCE.json')['packages'].items():
        for rel, h in pins.items(): assert sha(RES / name / rel) == h, ('pinned parent file differs', name, rel)
    return True
frozen = integrity()
out.mkdir(parents=True)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONINTMAXSTRDIGITS='0', PYTHON=sys.executable)
env.pop('PYTHONOPTIMIZE', None); steps = []
def run(name, cmd, cwd=None):
    log = out / (name + '.log'); t = time.monotonic(); print('RUN', name, flush=True)
    with log.open('w') as f: q = subprocess.run(list(map(str, cmd)), env=env, stdout=f, stderr=subprocess.STDOUT, cwd=cwd)
    if q.returncode: raise RuntimeError((name, q.returncode, log.read_text()[-4000:]))
    steps.append(dict(name=name, seconds=round(time.monotonic() - t, 2), log_sha256=sha(log))); print('PASS', name, flush=True)
def py(name, path, *args): run(name, [sys.executable, '-B', path, *args])
try:
    args = ['--quick'] if quick else []
    if '--reuse-parent' in sys.argv:          # development only: link an already PASSing #466 run instead of rebuilding it
        src = Path(sys.argv[sys.argv.index('--reuse-parent') + 1]).resolve()
        assert read(src / 'RECEIPT.json')['status'] == 'PASS_DUAL_KERNEL_ELEVEN_HOSTING'
        (out / 'parent466').symlink_to(src); steps.append(dict(name='parent466-reused', receipt_sha256=sha(src / 'RECEIPT.json')))
    else:
        py('parent466', PARENT / 'verify.py', out / 'parent466', *args)
    p466 = out / 'parent466'; parent_word = PARENT / 'data/word.json.gz'
    B = RES / 'e8-r740-replica32/parent436/code/bit'; bins = p466 / 'parent445/parent444/base443/parent/bin'
    base = out / 'local'; host = out / 'bit'; word = out / 'word.json.gz'
    py('apply-selection', ROOT / 'code/apply.py', parent_word, sel, word)
    if sel == ROOT / 'data/selection.json':
        assert sha(word) == sha(ROOT / 'data/word.json.gz'), 'rebuilt word differs from the frozen word'
    py('e8core-replay', ROOT / 'code/replay_check.py', RES / 'e8-r740-replica32/code', parent_word, word)
    py('export-records', B / 'export_records.py', word, base / 'records')
    py('stage-cohort', B / 'regression/stage_cohort.py', base / 'records', base / 'records', base / 'cin', base / 'cout')
    run('official-legality', [bins / 'legality', base / 'cin', base / 'cout', base / 'cout/legality.json'])
    run('official-columns', [bins / 'columns_h', base / 'cout/COHORT249-RECORDS.bin', base / 'cout/columns.json'])
    run('official-k4-columns', [bins / 'columns_k4', base / 'cout/COHORT249-RECORDS.bin', base / 'cout/columns_k4.json'])
    py('record-mutations', B / 'mutate_records.py', base / 'records', base / 'cin', base / 'cout', bins / 'legality', bins / 'columns_k4', bins / 'legality_ncopy_h')
    py('positive-gram', B / 'checkers/gram_frames.py', base / 'records', '--gram', 'e8ham', '--h', 8, '--positive')
    host.mkdir(); (host / 'GEOMETRY.json').write_bytes((p466 / 'bit/GEOMETRY.json').read_bytes())
    py('emit', PARENT / 'code/emit.py', '--word', word, '--local-check', base, '--out', host, '--isometries', PARENT / 'data/residual-isometries.json')
    py('independent-audit', PARENT / 'code/audit.py', base, p466 / 'parent445/parent444/base443/candidate/nine', host)
    assert len(read(host / 'AUDIT.json')['mutations_rejected']) == 22
    py('exact-assembly', PARENT / 'code/assemble.py', p466 / 'parent445', host, p466 / 'complex')
    (out / 'RESULT.json').write_bytes((host / 'RESULT.json').read_bytes())
    actual = read(out / 'RESULT.json')
    if sel == ROOT / 'data/selection.json' and (ROOT / 'EXPECTED.json').exists():
        for k, v in read(ROOT / 'EXPECTED.json').items(): assert actual[k] == v, (k, actual[k], v)
    if frozen: assert integrity()
    receipt = dict(status='PASS_PHASE_A_REORDER_ON_DUAL_KERNEL', mode=('reused-parent' if '--reuse-parent' in sys.argv else 'quick' if quick else 'full'), kappa=actual['kappa'],
                   binding=actual.get('binding_component'), bit_lower=actual.get('bit_lower'), complex_lower=actual.get('complex_lower'),
                   parent_kappa=read(p466 / 'RESULT.json')['kappa'], frozen_package=frozen, selection_sha256=sha(sel), word_sha256=sha(word),
                   checks=steps, python=sys.version.split()[0])
    (out / 'RECEIPT.json').write_text(json.dumps(receipt, indent=2) + '\n'); print(json.dumps(receipt, indent=2))
except BaseException as e:
    (out / 'FAILURE.json').write_text(json.dumps(dict(error=repr(e), completed=steps), indent=2) + '\n'); raise
