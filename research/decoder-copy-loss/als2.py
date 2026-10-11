"""ALS feasibility for a decoder with an arbitrary list of centre frames, each given as a list of F2^9 vectors a whose
orthogonal complements it lies in (empty list = full frame). Constraint per target t: u_t . c_s = [s == t] for all s
non-orthogonal to t. usage: als2.py CERT.json.gz FRAMES_JSON [restarts] [iters]
FRAMES_JSON example: '[[],[],[],[],[],[],[],[3]]' (7 full + one hyperplane 3^perp)."""
import gzip, json, sys
import numpy as np
c = json.load(gzip.open(sys.argv[1])); P = c['ports']; v = len(P)
dot = lambda a, b: bin(a & b).count('1') & 1
frames = json.loads(sys.argv[2]); K = len(frames)
allow = np.array([[all(dot(P[s], a) == 0 for a in fr) for fr in frames] for s in range(v)])
def fdim(fr):
    # dimension of the intersection of the hyperplanes a^perp in F2^9 = 9 - rank(a's)
    rows = []; 
    for a in fr:
        for r in rows:
            if a ^ r < a: a ^= r
        if a: rows.append(a); rows.sort(reverse=True)
    return 9 - len(rows)
print('K', K, 'frame dims', [fdim(f) for f in frames], 'cst bound', sum(fdim(f) for f in frames), '| sources allowed per centre', allow.sum(0).tolist())
O = [[s for s in range(v) if dot(P[s], P[t])] for t in range(v)]
restarts = int(sys.argv[3]) if len(sys.argv) > 3 else 5; iters = int(sys.argv[4]) if len(sys.argv) > 4 else 3000
rng = np.random.default_rng(1); best = np.inf
tgt = [np.array([1.0 if s == t else 0.0 for s in O[t]]) for t in range(v)]
for r in range(restarts):
    C = rng.standard_normal((v, K)) * allow; U = rng.standard_normal((v, K))
    for it in range(iters):
        for t in range(v): U[t] = np.linalg.lstsq(C[O[t]], tgt[t], rcond=None)[0]
        for s in range(v):
            ks = np.flatnonzero(allow[s]); A = U[O[s]][:, ks]; b = tgt[s]
            C[s] = 0
            if len(ks): C[s, ks] = np.linalg.lstsq(A, b, rcond=None)[0]
        if it % 50 == 0 or it == iters - 1:
            res = sum(float(np.sum((C[O[t]] @ U[t] - tgt[t])**2)) for t in range(v))
            if res < 1e-24: break
    best = min(best, res); print('restart %d: residual %.3e after %d iterations' % (r, res, it + 1), flush=True)
    if res < 1e-20: break
print('best residual %.3e' % best)
