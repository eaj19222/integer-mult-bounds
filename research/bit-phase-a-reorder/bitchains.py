"""Cost breakdown of a bitE8/1 word: per-register climbs (class x/y/helper, first/mid/last) and frame slack vs the
source-span lower bound, using Chafik's e8core replay semantics. usage: bitchains.py CODE_DIR WORD m"""
import sys, os, math, gzip, json
from collections import Counter
sys.path.insert(0, sys.argv[1]); import e8core as E
c = E.load_word(sys.argv[2]); m = int(sys.argv[3])
r = E.replay(c); L = r['L']; masks = r['masks']; v, R = c['v'], c['R']; n = 2*v + R
print('local histogram', dict(sorted(r['H'].items())), 'steps', r['steps'], 'span violations', len(r['viol']))
J = lambda k: k*math.log(m/k)
seq = [[masks[c['start'][i]]] for i in range(n)]
for ph in ('D', 'A'):
    for f, d, srcs in c[ph]:
        for x in [d] + srcs: seq[x].append(masks[f])
for ph in ('B', 'C'):
    for f, d, srcs in c[ph]:
        for x in [d] + srcs: seq[x].append(masks[f])
for i in range(n): seq[i].append(masks[c['final'][i]])
cls = lambda i: 'x' if i < v else 'y' if i < 2*v else 'h'
tab = Counter(); cost = Counter(); floor = Counter(); nclimb = Counter()
for i in range(n):
    ds = [L.dim(x) for x in seq[i]]
    st = [b - a for a, b in zip(ds, ds[1:]) if b > a]
    for j, s in enumerate(st):
        pos = 'first' if j == 0 else 'last' if j == len(st) - 1 else 'mid'
        tab[cls(i), pos, s] += 1; cost[cls(i)] += J(s)
    nclimb[cls(i)] += len(st)
    if ds[-1] > ds[0]: floor[cls(i)] += J(ds[-1] - ds[0])
ret = sum(J(L.dim(seq[q][-2])) for q in c['ret'])
for k in 'xyh':
    print(k, 'climbs', nclimb[k], 'J %.1f floor %.1f excess %.1f' % (cost[k], floor[k], cost[k] - floor[k]))
    for pos in ('first', 'mid', 'last'):
        print('   ', pos.ljust(5), {s: nn for (kk, p, s), nn in sorted(tab.items()) if kk == k and p == pos})
print('total J (excluding retained copies) %.1f, one-climb floor %.1f' % (sum(cost.values()), sum(floor.values())))
