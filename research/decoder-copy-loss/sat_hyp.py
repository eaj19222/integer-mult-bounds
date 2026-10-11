"""Bit-E8 F2 decoder with a frame-restricted centre. Extends Dylan Crow's centres_sat.py (#370).
Need w_S, u_t in F2^k with <u_t,w_t> = 1 and <u_t,w_S> = 0 for every neighbour S (|<r_t,r_S>| = 1).
Extra: centres listed in HYP have support {S : w_S[i] = 1} inside the root hyperplane r^perp (copy rank <= 7).
usage: sat_hyp.py k seconds [norm|free] [i:root,i:root,...]"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')); os.environ.pop('E8COORD', None)
import e8lib as E
from ortools.sat.python import cp_model
V = E.V; k = int(sys.argv[1]); tl = float(sys.argv[2]); mode = sys.argv[3] if len(sys.argv) > 3 else 'norm'
hyp = [tuple(map(int, x.split(':'))) for x in sys.argv[4].split(',')] if len(sys.argv) > 4 and sys.argv[4] else []
m = cp_model.CpModel()
w = [[m.NewBoolVar('') for i in range(k)] for s in range(V)]
u = [[m.NewBoolVar('') for i in range(k)] for s in range(V)]
if mode == 'norm':
    clique = [0, 2, 6, 8, 56, 57, 64, 65]
    for j, c in enumerate(clique[:k]):
        for i in range(k): m.Add(w[c][i] == (1 if i == j else 0)); m.Add(u[c][i] == (1 if i == j else 0))
if mode == 'normh':                         # clique of pairwise neighbours outside 0^perp; requires hyp on centre k-1 = 8, root 0
    assert hyp == [(k - 1, 0)]
    clique = [0, 2, 4, 6, 8, 10, 56, 12]
    for j, c in enumerate(clique):
        for i in range(k - 1): m.Add(w[c][i] == (1 if i == j else 0)); m.Add(u[c][i] == (1 if i == j else 0))
for i, r in hyp:
    out = [S for S in range(V) if S != r and E.G[r][S] != 0]          # lines not orthogonal to r (incl. r itself)
    out.append(r)
    for S in set(out): m.Add(w[S][i] == 0)
    print('centre', i, 'confined to', r, '^perp:', V - len(set(out)), 'lines allowed')
for t in range(V):
    for S in [t] + E.NEIGH[t]:
        ps = []
        for i in range(k):
            p = m.NewBoolVar('')
            m.AddBoolAnd([u[t][i], w[S][i]]).OnlyEnforceIf(p)
            m.AddBoolOr([u[t][i].Not(), w[S][i].Not()]).OnlyEnforceIf(p.Not())
            ps.append(p)
        if S == t: m.AddBoolXOr(ps)
        else: m.AddBoolXOr(ps + [m.NewConstant(1)])
sol = cp_model.CpSolver(); sol.parameters.max_time_in_seconds = tl; sol.parameters.num_workers = 4
t0 = time.time(); r = sol.Solve(m)
print('k', k, 'mode', mode, 'hyp', hyp, 'status', sol.StatusName(r), '%.0fs' % (time.time() - t0), flush=True)
if r in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    W = [[sol.Value(w[s][i]) for i in range(k)] for s in range(V)]
    dims = [E.span_dim([s for s in range(V) if W[s][i]]) for i in range(k)]
    print('centre support sizes', [sum(W[s][i] for s in range(V)) for i in range(k)], 'frame dims', dims, 'copy loss', sum(dims))
    import json; json.dump(dict(W=W, U=[[sol.Value(u[s][i]) for i in range(k)] for s in range(V)], dims=dims), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sol-k%d-%s-%s.json' % (k, mode, '_'.join('%d-%d' % h for h in hyp) or 'none')), 'w'))
