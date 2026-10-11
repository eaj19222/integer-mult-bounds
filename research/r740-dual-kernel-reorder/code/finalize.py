"""Freeze a selection into the package: data/selection.json, data/word.json.gz (rebuilt deterministically), SOURCE.json
(pins of #466's manifest and source pins); after a verify run, EXPECTED.json and MANIFEST.json.
usage: finalize.py data SELECTION.json  |  finalize.py expected RESULT.json  |  finalize.py manifest"""
import sys, json, hashlib, subprocess, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; RES = ROOT.parent; PARENT = RES / 'r740-dual-kernel'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
step = sys.argv[1]
if step == 'data':
    sel = json.loads(Path(sys.argv[2]).read_text())
    keep = {k: sel[k] for k in ('order', 'modes', 'extra') if k in sel}
    (ROOT / 'data').mkdir(exist_ok=True); (ROOT / 'data/selection.json').write_text(json.dumps(keep, separators=(',', ':')) + '\n')
    subprocess.run([sys.executable, '-B', ROOT / 'code/apply.py', PARENT / 'data/word.json.gz', ROOT / 'data/selection.json', ROOT / 'data/word.json.gz'], check=True)
    pins = {'r740-dual-kernel': {'MANIFEST.json': sha(PARENT / 'MANIFEST.json'), 'SOURCE.json': sha(PARENT / 'SOURCE.json'),
                                 'data/word.json.gz': sha(PARENT / 'data/word.json.gz')},
            'e8-r740-replica32': {'code/e8core.py': sha(RES / 'e8-r740-replica32/code/e8core.py')}}
    (ROOT / 'SOURCE.json').write_text(json.dumps(dict(parent_pr=466, parent_head='c2f8e18', packages=pins), indent=1) + '\n')
elif step == 'expected':
    r = json.loads(Path(sys.argv[2]).read_text())
    keys = ['status', 'kappa', 'bit_lower', 'complex_lower', 'binding_component', 'bit', 'complex', 'bit_profile', 'emitted_program_sha256',
            'complex_emitted_program_sha256', 'complex_template_sha256', 'bit_template_sha256', 'bank_assignments', 'row_bound', 'row_controls',
            'halving_depth', 'finite_controls']
    (ROOT / 'EXPECTED.json').write_text(json.dumps({k: r[k] for k in keys}, indent=2) + '\n')
elif step == 'manifest':
    inv = {f.relative_to(ROOT).as_posix(): sha(f) for f in ROOT.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name != 'MANIFEST.json'}
    (ROOT / 'MANIFEST.json').write_text(json.dumps(dict(sorted(inv.items())), indent=1) + '\n')
