"""Where the bit word's climb cost sits: J = sum r ln(m/r) of climbs, split by phase (D/A/B/C/final) and register class."""
import sys, math
from collections import Counter
sys.path.insert(0, sys.argv[1]); import e8core as E
c = E.load_word(sys.argv[2]); m = int(sys.argv[3]); r = E.replay(c); L = r['L']; masks = r['masks']
v, R = c['v'], c['R']; n = 2*v + R; J = lambda k: k*math.log(m/k)
cls = lambda i: 'x' if i < v else 'y' if i < 2*v else 'h'
cur = [masks[f] for f in c['start']]; cost = Counter(); cnt = Counter(); gates = Counter()
def climb(i, mk, ph):
    if cur[i] != mk:
        d = L.dim(mk) - L.dim(cur[i]); cost[ph, cls(i)] += J(d); cnt[ph, cls(i), d] += 1; cur[i] = mk
for ph in ('D', 'A'):
    for f, d, srcs in c[ph]:
        gates[ph] += 1
        for x in [d] + srcs: climb(x, masks[f], ph)
for ph in ('B', 'C'):
    for f, d, srcs in c[ph]:
        gates[ph] += 1
        for x in [d] + srcs: climb(x, masks[f], ph)
for i in range(n): climb(i, masks[c['final'][i]], 'final')
print('gates per phase', dict(gates))
for ph in ('D', 'A', 'B', 'C', 'final'):
    row = {k: round(cost[ph, k], 1) for k in 'xyh' if cost[ph, k]}
    print(ph.ljust(5), 'J', round(sum(cost[ph, k] for k in 'xyh'), 1), row, '| rank-1 climbs', {k: cnt[ph, k, 1] for k in 'xyh' if cnt[ph, k, 1]})
# B-phase gate shapes: destination class and source classes
shape = Counter((cls(d), ''.join(sorted({cls(s) for s in srcs}))) for f, d, srcs in c['B']); print('B gate shapes (dst, srcs):', dict(shape))
shape = Counter((cls(d), ''.join(sorted({cls(s) for s in srcs}))) for f, d, srcs in c['A']); print('A gate shapes (dst, srcs):', dict(shape))
shape = Counter((cls(d), ''.join(sorted({cls(s) for s in srcs}))) for f, d, srcs in c['C']); print('C gate shapes (dst, srcs):', dict(shape))
print('A reversed == C ?', [list(g) for g in reversed(c['A'])] == [list(g) for g in c['C']], '| same (dst,srcs) multiset:', Counter((d, tuple(sorted(s))) for f, d, s in c['A']) == Counter((d, tuple(sorted(s))) for f, d, s in c['C']))
