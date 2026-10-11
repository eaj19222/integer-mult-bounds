"""Lever-1 evaluation loop for a candidate E8 complex unit (gcert/1) in #377's nine-stage setting.
Checks: Sussman's gx.check1 (E0-E7, exact scalar), source-span rule, full rational operator identical to Sussman's
original, unchanged invariants; then prices b (two engines, as #384's nine.py) and kappa against #382's bit c.
usage: evaluate.py PKG_DIR CANDIDATE.json.gz"""
import sys, os, gzip, json, copy
from collections import Counter
pkg = os.path.abspath(sys.argv[1]); sys.path[:0] = [os.path.join(pkg, 'code'), os.path.join(pkg, 'complex', 'gx')]
import gx
from cxretime import CX
from e8core import coarse, kappa, Q
from fractions import Fraction as Fr

def load(p):
    x = json.load(gzip.open(p)); return x['cert'] if 'cert' in x else x

def operator(c):
    v, R = c['v'], c['R']; reg = [{r: Fr(1)} for r in range(2*v + R)]
    def axpy(t, src, co):
        d = reg[t]
        for k, u in src.items():
            w = d.get(k, 0) + co*u
            if w: d[k] = w
            else: d.pop(k, None)
    def run(G):
        for g in G:
            if g[0] == 'neg': reg[g[2]] = {k: -u for k, u in reg[g[2]].items()}
            elif g[0] == 'out':
                src = dict(reg[g[2]])
                for t, a, b in g[3]: axpy(t, src, Fr(a, b))
            else:
                for s, a, b in g[3]: axpy(g[2], reg[s], Fr(a, b))
    run(c['A']); tot = {k: dict(reg[s]) for k, s, _ in c['ret']}
    for t in range(v):
        for k, a, b in c['scat']['table'][t]: axpy(v + t, tot[k], Fr(a, b))
    run(c['B']); return reg, tot

def nine_profile(c):
    H = Counter()
    for bl in c['blocks'].values():
        for r, n in bl.items(): H[int(r)] += 72*n
    for r in (16, 8, 32, 8, 48, 8, 48, 32, 16): H[r] += 1920
    H[1] += 7047; return H

C_BIT = Q(251726760077483, 25*10**16)   # PR #382 bit word, B_3 unsplit (fixed)
B_384 = Q(999632926176283, 10**18)

def evaluate(cand, orig=None, quiet=False):
    gx.check1(cand, scalar=True)
    assert CX(cand).span_ok() == 0, 'source-span rule'
    if orig is None: orig = load(os.path.join(pkg, 'complex', 'gcert1-e8-r783.json.gz'))
    for k in ('h', 'v', 'R', 'cst', 'N', 'ports', 'start', 'final', 'ret', 'scat'):
        assert cand[k] == orig[k], 'invariant changed: ' + k
    assert operator(cand) == operator(orig), 'operator differs from Sussman original'
    H = nine_profile(cand); assert max(H) == 48 and 73*14727 - sum(r*n for r, n in H.items()) == 2496
    b = coarse(H, 73, 14727); k, bind = kappa(C_BIT, b)
    if not quiet:
        print('PASS checks | b = %s = %.15e (vs #384 %+.3e) | kappa = %.15e (%s-bound)' % (b, float(b), float(b - B_384), float(k), bind))
    return b, k

if __name__ == '__main__':
    evaluate(load(sys.argv[2]))
