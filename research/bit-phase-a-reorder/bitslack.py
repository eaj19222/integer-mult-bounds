"""Frame slack of a bitE8/1 word: per gate, dim(frame) - dim(lower bound), where the lower bound is the root-closed span
of (a) the x-supports required by the source-span rule and (b) the current frames of all participants (nesting)."""
import sys
from collections import Counter
sys.path.insert(0, sys.argv[1]); import e8core as E
c = E.load_word(sys.argv[2]); r = E.replay(c); L = r['L']; masks = r['masks']; v, R = c['v'], c['R']; n = 2*v + R
cur = [masks[f] for f in c['start']]; zs = [{i: 1} if i < v else {} for i in range(n)]
slack = Counter(); tight_from = Counter()
def gate(f, d, srcs):
    m = masks[f]; need = 0
    for s in srcs:
        if s < v or s >= 2*v: need |= sum(1 << i for i in zs[s])
    after = dict(zs[d])
    for s in srcs:
        for i, a in zs[s].items():
            w = after.get(i, 0) + a
            if w: after[i] = w
            else: after.pop(i, None)
    if d >= 2*v: need |= sum(1 << i for i in after)
    prev = 0
    for x in [d] + srcs: prev |= cur[x]
    lb = L.close(need | prev)
    slack[L.dim(m) - L.dim(lb)] += 1
    for x in [d] + srcs: cur[x] = m
    zs[d] = after
for ph in ('D', 'A'):
    for g in c[ph]: gate(*g)
for t in range(v): pass
for ph in ('B', 'C'):
    for g in c[ph]: gate(*g)
print('gates by dim(frame) - dim(lower bound):', dict(sorted(slack.items())), 'total', sum(slack.values()))
