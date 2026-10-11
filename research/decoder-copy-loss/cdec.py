"""Complex-side decoder over F_p with frame-restricted centres (proxy for the rational decoder).
c_s, u_t in F_p^K;  u_t . c_s = [s == t] (mod p) for every s whose binary port is NOT orthogonal to t's (incl. t).
Centre k may only use sources whose port lies in its frame F_k (an F2^9 subspace); copy cost = dim F_k.
usage: cdec.py p seconds CONFIG     CONFIG: python list of frames, e.g. "[('hyp',s),...,('line',s)]" """
import sys, os, gzip, json, time, itertools
from ortools.sat.python import cp_model
D = os.path.dirname(os.path.abspath(__file__))
w = json.load(gzip.open(os.path.join(D, 'complex433.json.gz'))); P = w['ports']; V = len(P)
dot = lambda a, b: bin(a & b).count('1') & 1
def basis(vs):
    b = []
    for x in vs:
        for y in b:
            if x ^ y < x: x ^= y
        if x: b.append(x); b.sort(reverse=True)
    return b
def inspan(x, B):
    for y in B:
        if x ^ y < x: x ^= y
    return x == 0
def frame(spec):
    kind = spec[0]
    if kind == 'full': return basis([1 << i for i in range(9)])
    if kind == 'hyp': return basis([x for x in range(1, 512) if not dot(x, P[spec[1]])])          # P[s]-perp
    if kind == 'hypv': return basis([x for x in range(1, 512) if not dot(x, spec[1])])            # vector-perp
    if kind == 'line': return basis([P[spec[1]]])
    if kind == 'span': return basis([P[s] for s in spec[1]])
    raise ValueError(kind)
coord = [s for s in range(V) if bin(P[s]).count('1') == 7]  # placeholder, overwritten below
if __name__ == '__main__':
    p = int(sys.argv[1]); tl = float(sys.argv[2]); cfg = eval(sys.argv[3])
    F = [frame(x) for x in cfg]; K = len(F)
    allow = [[inspan(P[s], F[k]) for k in range(K)] for s in range(V)]
    print('p', p, 'K', K, 'frame dims', [len(f) for f in F], 'cost', sum(len(f) for f in F), '| sources per centre', [sum(allow[s][k] for s in range(V)) for k in range(K)], flush=True)
    m = cp_model.CpModel()
    c = [[m.NewIntVar(0, p - 1, '') if allow[s][k] else None for k in range(K)] for s in range(V)]
    u = [[m.NewIntVar(0, p - 1, '') for k in range(K)] for t in range(V)]
    for t in range(V):
        for s in range(V):
            if not dot(P[s], P[t]): continue
            terms = []
            for k in range(K):
                if c[s][k] is None: continue
                z = m.NewIntVar(0, (p - 1) ** 2, ''); m.AddMultiplicationEquality(z, [u[t][k], c[s][k]]); terms.append(z)
            if not terms:
                if s == t: m.Add(0 == 1)
                continue
            tot = m.NewIntVar(0, len(terms) * (p - 1) ** 2, ''); m.Add(tot == sum(terms))
            m.AddModuloEquality(1 if s == t else 0, tot, p)
    sol = cp_model.CpSolver(); sol.parameters.max_time_in_seconds = tl; sol.parameters.num_workers = 3
    t0 = time.time(); r = sol.Solve(m); print('status', sol.StatusName(r), '%.0fs' % (time.time() - t0), flush=True)
