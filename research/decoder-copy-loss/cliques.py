"""Cliques of the non-orthogonality graph on the 120 ports (s ~ t iff p_s . p_t = 1 mod 2)."""
import gzip, json, sys, pickle
from collections import Counter
c = json.load(gzip.open(sys.argv[1])); P = c['ports']; v = len(P)
dot = lambda a, b: bin(a & b).count('1') & 1
nb = [sum(1 << s for s in range(v) if s != t and dot(P[s], P[t])) for t in range(v)]
best = [0]; cl = []
def bk(R, Pm, size, out):
    if Pm == 0:
        if size > best[0]: best[0] = size
        if size >= 8: out.append(R)
        return
    if size + bin(Pm).count('1') < 8: return
    while Pm:
        x = Pm & -Pm; i = x.bit_length() - 1
        bk(R | x, Pm & nb[i], size + 1, out)
        Pm &= ~x
out = []
bk(0, (1 << v) - 1, 0, out)
print('clique number', best[0], '| maximal cliques of size >= 8:', len(out), Counter(bin(q).count('1') for q in out))
pickle.dump(out, open(sys.argv[2], 'wb'))
