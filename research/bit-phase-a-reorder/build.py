"""Build a bitE8/1 word from an annealing solution (phase-A order + raise flags), verify it with e8core.replay
(exact legality, F2 restoration, source-span) and price the bit saving on #454's 11-stage hosted profile.
usage: build.py WORD SOLUTION.json OUT_WORD.json.gz CODE_DIR EXPECTED.json"""
import sys, json, gzip, copy
from fractions import Fraction as Q
from collections import Counter
import core
W = core.Word(sys.argv[1]); sol = json.load(open(sys.argv[2])); out = sys.argv[3]
sys.path.insert(0, sys.argv[4]); import e8core as E
order, rf = sol['order'], sol.get('raise_flags')
cost, bad, hist, frames = core.evaluate2(W, order, rf, frames_out=True); assert bad == 0
c = copy.deepcopy(W.c); key = {}
for i, fr in enumerate(c['frames']): key.setdefault(W.fmask[i], i)
def fid(mask):
    if mask in key: return key[mask]
    idx = [i for i in range(W.L.v) if mask >> i & 1]; rows, piv, basis = W.L._basis(idx)
    c['frames'].append(basis); key[mask] = len(c['frames']) - 1; return key[mask]
c['A'] = [[fid(frames[gi]), W.A[gi][1], list(W.A[gi][2])] for gi in order]
with gzip.open(out, 'wt') as f: json.dump(c, f, separators=(',', ':'))
r0 = E.replay(W.c); r1 = E.replay(c)
assert not r1['viol'], ('source-span violations', len(r1['viol']))
print('exact replay PASS (legality, F2 restoration, source-span); new frames added', len(c['frames']) - len(W.c['frames']))
H0, H1 = r0['H'], r1['H']; dH = {k: H1.get(k, 0) - H0.get(k, 0) for k in sorted(set(H0) | set(H1)) if H1.get(k, 0) != H0.get(k, 0)}
print('local histogram delta per invocation:', dH, '| local mass unchanged:', sum(k * v for k, v in H0.items()) == sum(k * v for k, v in H1.items()))
exp = json.load(open(sys.argv[5])); prof = Counter({int(k): v for k, v in exp['bit_profile'].items()})
new = Counter(prof)
for k, d in dH.items(): new[k] += 88 * d
assert all(x >= 0 for x in new.values())
c0 = E.coarse(prof, 78, 9600); c1 = E.coarse(new, 78, 9600)
print('bit saving c: %s -> %s (%.15e -> %.15e, %+.3e, %+.4f%%)' % (c0, c1, float(c0), float(c1), float(c1 - c0), 100 * float((c1 - c0) / c0)))
