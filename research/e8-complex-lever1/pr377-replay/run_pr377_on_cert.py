"""Run every stage of #377's nine-stage verifier with #378's re-timed E8 unit substituted for Sussman's certificate.
Structural pins (V, R, H, cst, N, scatter, centre ranks) are kept; pins that only record the old certificate's statistics
(frames, gates, histograms, ledgers, scalar steps, climbs, local bill, stock bits) are removed and recomputed by the guard.
The certificate hash pins are updated to the substituted file. usage: run_far.py WORK377_DIR CERT.json.gz OUTDIR"""
import sys, os, shutil, json, gzip, hashlib, subprocess, time
from pathlib import Path
src, cert, wd = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
assert not wd.exists(); wd.mkdir(); shutil.copytree(src, wd / 'work'); logs = wd / 'logs'; logs.mkdir()
sha = lambda b: hashlib.sha256(b).hexdigest()
z = cert.read_bytes(); raw = gzip.decompress(z); c = json.loads(raw)
P = wd / 'work/native358/vendor/complex-reserve/upstream/pr352/code/complex'
sp = json.loads((P / 'inputs/complex/source-pins.json').read_text())
old = dict(sp['certificate'])
for p in (P / sp['certificate']['path'], wd / 'work/pr361/complex/gcert1-e8-r783.json.gz'): p.write_bytes(z)
sp['certificate']['compressed_sha256'] = sha(z); sp['certificate']['uncompressed_sha256'] = sha(raw)
(P / 'inputs/complex/source-pins.json').write_text(json.dumps(sp, indent=1))
pins = json.loads((P / 'pins-e8.json').read_text())
dropped = {k: pins.pop(k) for k in ['frames', 'gates', 'label_histogram', 'ledger', 'scalar_steps', 'climbed', 'climb_forward', 'climb_backward', 'local_bill', 'stock_bits'] if k in pins}
(P / 'pins-e8.json').write_text(json.dumps(pins, indent=1))
# Two hard-coded certificate results in #377's stage scripts: the local child count (recomputed by the guard as
# label_checks.invocation_calls) and the expected coarse complex saving (set to the value under test).
EXPECT_CHILDREN = sum(n for blk in c['blocks'].values() for n in blk.values())
EXPECT_B = sys.argv[4] if len(sys.argv) > 4 else '999632926176283'
patches = []
for rel, a, b in [('work/odd-stages/global_nine.py', 'assert local_children==3974', 'assert local_children==%d' % EXPECT_CHILDREN),
                  ('work/odd-stages/audit_nine_template.py', 'assert b==Q(999240641319551,10**18)', 'assert b==Q(%s,10**18)' % EXPECT_B)]:
    f = wd / rel; t = f.read_text(); assert t.count(a) == 1, (rel, a); f.write_text(t.replace(a, b)); patches.append(dict(file=rel, old=a, new=b))
done = []
def run(name, argv):
    t = time.monotonic(); log = logs / (name + '.log'); print(name, flush=True)
    with log.open('w') as f: r = subprocess.run([sys.executable, '-B'] + argv, cwd=wd, stdout=f, stderr=subprocess.STDOUT)
    done.append(dict(stage=name, returncode=r.returncode, seconds=round(time.monotonic() - t, 1)))
    if r.returncode: print('  FAILED, see', log); print(log.read_text()[-3000:]); return False
    return True
ok = run('fresh-local-admission', ['work/native358/vendor/complex-reserve/admit.py', '--source', 'work/native358/vendor/complex-reserve/upstream/pr352', '--output', 'work/complex-nine-native/local-admission'])
for name, script in [('finite-data-banks-profile', 'complex_candidate.py'), ('exact-clifford-recipes', 'verify_clifford_frames.py'), ('exact-data-and-cover-phases', 'data_phases.py'), ('global-template-and-invoice', 'global_nine.py'), ('independent-template-two-moments', 'audit_nine_template.py'), ('fixed-bit-outer-check', 'outer_fixed.py')]:
    if not ok: break
    ok = run(name, ['work/odd-stages/' + script])
out = wd / 'work/complex-nine-native'; res = dict(patches=patches, stages=done, certificate=dict(path=str(cert.name), compressed_sha256=sha(z), uncompressed_sha256=sha(raw), replaced=old), dropped_statistic_pins=dropped)
if ok:
    res['independent_template_audit'] = json.loads((out / 'INDEPENDENT-TEMPLATE-AUDIT.json').read_text())
    res['global_review'] = {k: v for k, v in json.loads((out / 'GLOBAL-REVIEW.json').read_text()).items() if k in ('m', 'live', 'deficit', 'profile', 'cover_correction_calls', 'finite_invoice', 'local_source_events', 'status')}
    res['outer_fixed'] = json.loads((out / 'OUTER-FIXED-BIT.json').read_text())
(wd / 'RESULT.json').write_text(json.dumps(res, indent=1, default=str)); print('ALL STAGES PASS' if ok else 'STOPPED')
