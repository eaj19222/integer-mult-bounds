"""Per-register climb chains of a gcert/1 E8 unit; cost decomposition vs one-climb-per-register."""
import sys, gzip, json, math
from collections import Counter, defaultdict
c = json.load(gzip.open(sys.argv[1])); c = c.get('cert', c)
v, R, h = c['v'], c['R'], c['h']; n = 2*v + R; m = 73
fr = [tuple(f) for f in c['frames']]; dim = [len(f) for f in fr]
def regs(g):
    if g[0] == 'neg': return [g[2]]
    if g[0] == 'out': return [g[2]] + [t for t, _, _ in g[3]] + list(g[4])
    return [g[2]] + [s for s, _, _ in g[3]]
cls = lambda r: 'x' if r < v else 'y' if r < 2*v else 's'
seq = [[c['start'][r]] for r in range(n)]
retf = {s: f for _, s, f in c['ret']}
for ph in ('A', 'B'):
    if ph == 'B':
        for s, f in retf.items(): seq[s].append(f)
    for g in c[ph]:
        for r in regs(g): seq[r].append(g[1])
for r in range(n): seq[r].append(c['final'][r])
J = lambda k: k*math.log(m/k)
tot = Counter(); ideal = Counter(); nclimb = Counter(); dist = defaultdict(Counter)
for r in range(n):
    ds = [dim[f] for f in seq[r]]
    # collapse repeats
    steps = [b - a for a, b in zip(ds, ds[1:]) if b != a]
    k = cls(r); tot[k] += sum(J(s) for s in steps); ideal[k] += J(ds[-1]-ds[0]) if ds[-1] > ds[0] else 0
    nclimb[k] += len(steps); dist[k][len(steps)] += 1
cc = sum(J(dim[f]) for _, _, f in c['ret'])
print('class  regs  climbs  cost(sum r ln(m/r))  one-climb floor  excess')
for k, cnt in (('x', v), ('y', v), ('s', R)):
    print(f'{k:5s} {cnt:5d} {nclimb[k]:7d} {tot[k]:16.1f} {ideal[k]:16.1f} {tot[k]-ideal[k]:9.1f}')
print(f'c (retained copies) cost {cc:.1f}')
print('total', round(sum(tot.values()) + cc, 1), 'floor', round(sum(ideal.values()) + cc, 1))
for k in 'xys': print(k, 'climbs per register:', dict(sorted(dist[k].items())))
