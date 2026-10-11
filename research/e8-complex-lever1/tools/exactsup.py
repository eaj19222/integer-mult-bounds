"""Compare union-support lower bounds (CX._lb) with exact x-content supports (rational replay with cancellation),
in the same A-phase / scatter / B-phase order as gx.scal."""
import sys, gzip, json
from fractions import Fraction as Fr
from collections import Counter
sys.path.insert(0, sys.argv[2])
from cxretime import CX
from cxkernel import echelon
c = json.load(gzip.open(sys.argv[1])); c = c.get('cert', c)
M = CX(c); v = c['v']; ports = c['ports']
reg = [({r: Fr(1)} if r < v else {}) for r in range(M.n)]
def axpy(t, src, co):
    d = reg[t]
    for k, u in src.items():
        w = d.get(k, 0) + co*u
        if w: d[k] = w
        else: d.pop(k, None)
span = lambda keys: len(echelon([ports[x] for x in keys]))
diff = Counter(); nA = len(c['A'])
for gi, (ph, g) in enumerate(M.gates):
    if gi == nA:
        tot = {k: dict(reg[s]) for k, s, _ in c['ret']}
        for t in range(v):
            for k, a, b in c['scat']['table'][t]: axpy(v + t, tot[k], Fr(a, b))
    need = set()
    if g[0] == 'neg':
        reg[g[2]] = {k: -u for k, u in reg[g[2]].items()}
    elif g[0] == 'out':
        src = dict(reg[g[2]])
        if g[2] < v or g[2] >= 2*v: need |= set(src)
        for t, a, b in g[3]:
            axpy(t, src, Fr(a, b))
            if t >= 2*v: need |= set(reg[t])
    else:
        for s, a, b in g[3]:
            if s < v or s >= 2*v: need |= set(reg[s])
            axpy(g[2], reg[s], Fr(a, b))
        if g[2] >= 2*v: need |= set(reg[g[2]])
    diff[len(M.lb[gi]) - span(need)] += 1
print('gates by (union-support lb dim) - (exact-support lb dim):', dict(sorted(diff.items())))
