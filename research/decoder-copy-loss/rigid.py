"""(1) Rigidity: are independent random 8-centre decoders the same up to GL(8) and per-source scaling?
(2) Exact: in Sussman's decoder (c_s = column s of the centre totals T), for every nonzero a in F2^9, the rank over Q of
{c_s : p_s . a = 1}. Rank 8 for all a means no centre functional can vanish outside a hyperplane."""
import gzip, json, sys, pickle
import numpy as np
from fractions import Fraction as Fr
c = json.load(gzip.open(sys.argv[1])); P = c['ports']; v = len(P); K = 8
dot = lambda a, b: bin(a & b).count('1') & 1
O = [[s for s in range(v) if dot(P[s], P[t])] for t in range(v)]
tgt = [np.array([1.0 if s == t else 0.0 for s in O[t]]) for t in range(v)]
def solve(seed):
    rng = np.random.default_rng(seed); C = rng.standard_normal((v, K)); U = rng.standard_normal((v, K))
    for it in range(3000):
        for t in range(v): U[t] = np.linalg.lstsq(C[O[t]], tgt[t], rcond=None)[0]
        for s in range(v): C[s] = np.linalg.lstsq(U[O[s]], tgt[s], rcond=None)[0]
        if it % 25 == 0 and sum(float(np.sum((C[O[t]] @ U[t] - tgt[t])**2)) for t in range(v)) < 1e-24: break
    return C
Q0 = [i for i in range(v) if pickle.load(open(sys.argv[2], 'rb'))[0] >> i & 1]
def normal(C):
    # gauge: map clique Q0 to the standard basis; then scale each c_s to unit max-abs entry with positive leading sign
    X = C @ np.linalg.inv(C[Q0]); out = []
    for x in X:
        j = int(np.argmax(np.abs(x))); out.append(x / x[j])
    return np.array(out)
sols = [normal(solve(s)) for s in (11, 22, 33)]
def cosdev(A, B):
    return max(1 - abs(float(a @ b) / (np.linalg.norm(a) * np.linalg.norm(b))) for a, b in zip(A, B))
print('rigidity: max (1 - |cos|) between source directions of random decoders, after the clique gauge:', max(cosdev(sols[0], x) for x in sols[1:]))
# exact ranks in Sussman's decoder
reg = [({r: Fr(1)} if r < v else {}) for r in range(2*v + c['R'])]
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
T = [reg[s] for _, s, _ in sorted(c['ret'])]
col = [[T[k].get(s, Fr(0)) for k in range(K)] for s in range(v)]
def rank(rows):
    M = [list(r) for r in rows]; rk = 0
    for j in range(K):
        p = next((i for i in range(rk, len(M)) if M[i][j] != 0), None)
        if p is None: continue
        M[rk], M[p] = M[p], M[rk]
        for i in range(len(M)):
            if i != rk and M[i][j] != 0:
                f = M[i][j] / M[rk][j]; M[i] = [x - f*y for x, y in zip(M[i], M[rk])]
        rk += 1
    return rk
from collections import Counter
print('exact rank of {c_s : p_s . a = 1} over all 511 nonzero a:', dict(Counter(rank([col[s] for s in range(v) if dot(P[s], a)]) for a in range(1, 512))))
sus = normal(np.array([[float(x) for x in r] for r in col]))
print('Sussman decoder vs random decoder: max (1 - |cos|) =', cosdev(sus, sols[0]))
