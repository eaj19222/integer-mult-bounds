"""For each register occurrence: frame dim vs the dim of its own x-support span (the minimum the source-span rule allows
for that register) and vs the gate's lower bound. Counts climbs that are 'forced' (next frame dim == support dim there)."""
import sys, gzip, json, math
from collections import Counter
sys.path.insert(0, sys.argv[2])
from cxretime import CX, regs_of
from cxkernel import echelon
c = json.load(gzip.open(sys.argv[1])); c = c.get('cert', c)
M = CX(c); v = c['v']; ports = c['ports']; d = lambda f: len(M.fr[f])
# x-support per register over time (support only grows in this replay, like CX._lb)
sup = [{r} if r < v else set() for r in range(M.n)]
occ_sup = {}   # (gate, reg) -> support span dim after gate
for gi, (ph, g) in enumerate(M.gates):
    if g[0] == 'out':
        for t, _, _ in g[3]: sup[t] |= sup[g[2]]
    elif g[0] == 'in':
        for s, _, _ in g[3]: sup[g[2]] |= sup[s]
    for r in regs_of(g):
        occ_sup[gi, r] = len(echelon([ports[x] for x in sup[r]]))
cls = lambda r: 'x' if r < v else 'y' if r < 2*v else 's'
slack = Counter(); lbslack = Counter(); forced = Counter(); free = Counter()
for r in range(M.n):
    k = cls(r); prev = None
    for i, (kind, x) in enumerate(M.occ[r]):
        if kind != 'g': continue
        f = M.gf[x]; sd = occ_sup[x, r]
        slack[k, d(f) - sd] += 1; lbslack[k, d(f) - len(M.lb[x])] += 1
        pf = M.F(r, i - 1)
        if d(f) > d(pf):
            (forced if d(f) == sd else free)[k] += 1
for k in 'xys':
    print(k, 'frame dim - own support dim:', {s: n for (kk, s), n in sorted(slack.items()) if kk == k})
    print(k, 'frame dim - gate lower bound dim:', {s: n for (kk, s), n in sorted(lbslack.items()) if kk == k})
    print(k, 'climbs into a gate: tight to own support', forced[k], ' above own support', free[k])
