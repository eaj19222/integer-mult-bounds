"""All root-spanned hyperplanes of Q^8 (as sets of E8 root lines inside them), up to size; for each orbit-type
representative, decide by CP-SAT whether a 9-centre bit decoder has a centre supported inside it."""
import sys, os, random, itertools, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')); os.environ.pop('E8COORD', None)
import e8lib as E
from ortools.sat.python import cp_model
V = E.V; rng = random.Random(1)
L = E.LINES
def closure(idx):
    d = E.span_dim(idx)
    return frozenset(s for s in range(V) if E.span_dim(list(idx) + [s]) == d), d
seen = {}
t0 = time.time()
for trial in range(6000):
    idx = []
    while E.span_dim(idx) < 7:
        s = rng.randrange(V)
        if E.span_dim(idx + [s]) > E.span_dim(idx): idx.append(s)
    H, d = closure(idx); assert d == 7
    seen.setdefault(len(H), set()).add(H)
print('hyperplanes found by size (lines inside: count):', {k: len(v) for k, v in sorted(seen.items())}, '%.0fs' % (time.time() - t0), flush=True)
def nb(a, b): return abs(E.G[a][b]) == 1
def clique_outside(H):
    out = [s for s in range(V) if s not in H]
    adj = {a: {b for b in out if b != a and nb(a, b)} for a in out}
    best = []
    def bk(R, P):
        nonlocal best
        if len(R) > len(best): best = list(R)
        if len(best) >= 8: return
        for x in sorted(P):
            bk(R + [x], P & adj[x]); P = P - {x}
            if len(best) >= 8: return
    bk([], set(out)); return best
def solve(H, k=9, tl=600):
    Q = clique_outside(H); norm = len(Q) == 8
    m = cp_model.CpModel()
    w = [[m.NewBoolVar('') for i in range(k)] for s in range(V)]; u = [[m.NewBoolVar('') for i in range(k)] for s in range(V)]
    for S in range(V):
        if S not in H: m.Add(w[S][k - 1] == 0)
    if norm:
        for j, c in enumerate(Q):
            for i in range(k - 1): m.Add(w[c][i] == (1 if i == j else 0)); m.Add(u[c][i] == (1 if i == j else 0))
    for t in range(V):
        for S in [t] + E.NEIGH[t]:
            ps = []
            for i in range(k):
                p = m.NewBoolVar(''); m.AddBoolAnd([u[t][i], w[S][i]]).OnlyEnforceIf(p)
                m.AddBoolOr([u[t][i].Not(), w[S][i].Not()]).OnlyEnforceIf(p.Not()); ps.append(p)
            m.AddBoolXOr(ps if S == t else ps + [m.NewConstant(1)])
    sol = cp_model.CpSolver(); sol.parameters.max_time_in_seconds = tl; sol.parameters.num_workers = 4
    r = sol.Solve(m); return sol.StatusName(r), norm
res = {}
for size, Hs in sorted(seen.items(), reverse=True):
    H = sorted(Hs, key=lambda h: sorted(h))[0]
    st, norm = solve(H)
    res[size] = st; print('hyperplane with %d lines (%d distinct found): %s (clique-normalized: %s)' % (size, len(Hs), st, norm), flush=True)
json.dump({str(k): v for k, v in res.items()}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hyperplane-results.json'), 'w'))
