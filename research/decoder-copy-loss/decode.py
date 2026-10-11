"""Check the decoding model on Sussman's complex E8 unit: after phase A and the scatter, D_t = sum_k S[t,k] T_k must have
D_t[t] = 1 and D_t[s] = 0 for every s whose port is NOT orthogonal (mod 2) to t's port; junk only on orthogonal sources."""
import gzip, json, sys
from fractions import Fraction as Fr
from collections import Counter
c = json.load(gzip.open(sys.argv[1])); c = c.get('cert', c)
v, R = c['v'], c['R']; P = c['ports']
dot = lambda a, b: bin(a & b).count('1') & 1
reg = [({r: Fr(1)} if r < v else {}) for r in range(2*v + R)]
def axpy(t, src, co):
    d = reg[t]
    for k, u in src.items():
        w = d.get(k, 0) + co*u
        if w: d[k] = w
        else: d.pop(k, None)
for g in c['A']:
    if g[0] == 'neg': reg[g[2]] = {k: -u for k, u in reg[g[2]].items()}
    elif g[0] == 'out':
        src = dict(reg[g[2]])
        for t, a, b in g[3]: axpy(t, src, Fr(a, b))
    else:
        for s, a, b in g[3]: axpy(g[2], reg[s], Fr(a, b))
T = {k: dict(reg[s]) for k, s, _ in c['ret']}
bad = 0; junk = Counter(); diag = Counter()
for t in range(v):
    D = {}
    for k, a, b in c['scat']['table'][t]:
        for s, u in T[k].items(): D[s] = D.get(s, 0) + Fr(a, b)*u
    D = {s: u for s, u in D.items() if u}
    diag[D.get(t, 0)] += 1
    for s, u in D.items():
        if s != t and dot(P[s], P[t]): bad += 1
    junk[sum(1 for s in D if s != t)] += 1
print('D_t[t] values:', dict(diag)); print('nonzero entries on non-orthogonal s != t:', bad); print('junk support sizes:', dict(junk))
nonorth = Counter(sum(dot(P[s], P[t]) for s in range(v)) for t in range(v)); print('|O_t| (non-orthogonal incl. t):', dict(nonorth))
