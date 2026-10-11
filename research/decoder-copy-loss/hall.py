"""Hall (matching) filter for 8 centres with smaller frames: every maximum clique Q (size 8) of the non-orthogonality graph
must match one-to-one onto centres whose frames contain the members' ports (needed for the 8x8 identity on Q)."""
import gzip, json, sys, pickle, itertools
from collections import Counter
c = json.load(gzip.open(sys.argv[1])); P = c['ports']; v = len(P)
Q = [[i for i in range(v) if q >> i & 1] for q in pickle.load(open(sys.argv[2], 'rb'))]
dot = lambda a, b: bin(a & b).count('1') & 1
def matchable(q, frames):   # frames: list of predicates on ports; bipartite perfect matching by augmenting paths
    adj = [[k for k, f in enumerate(frames) if f(P[s])] for s in q]; own = {}
    def aug(i, seen):
        for k in adj[i]:
            if k in seen: continue
            seen.add(k)
            if k not in own or aug(own[k], seen): own[k] = i; return True
        return False
    return all(aug(i, set()) for i in range(len(q)))
full = lambda p: True
hyp = lambda a: (lambda p: dot(p, a) == 0)
# one hyperplane centre (cst 71)
ok1 = [a for a in range(1, 512) if all(matchable(q, [full]*7 + [hyp(a)]) for q in Q)]
print('cst 71 (7 full + 1 hyperplane a^perp): Hall-feasible a count =', len(ok1), '| weights of a:', Counter(bin(a).count('1') for a in ok1))
# where do failures come from for the rest?
fail = Counter(bin(a).count('1') for a in range(1, 512) if a not in set(ok1)); print('  infeasible a by weight:', dict(fail))
# two hyperplane centres (cst 70), up to the cost of 511^2/2 pairs: test pairs among ok1
ok2 = []
for a, b in itertools.combinations(ok1, 2):
    if all(matchable(q, [full]*6 + [hyp(a), hyp(b)]) for q in Q): ok2.append((a, b))
print('cst 70 (6 full + 2 hyperplanes): Hall-feasible pairs =', len(ok2))
json.dump(dict(ok1=ok1, ok2=ok2[:2000]), open(sys.argv[3], 'w'))
