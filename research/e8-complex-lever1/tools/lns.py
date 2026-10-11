"""CP-SAT large-neighbourhood frame re-optimisation on a (split) gcert/1 E8 unit, fixed gate order and operator.
For a window of gates, every other frame is fixed; each window gate chooses a frame F with L_g <= F <= U_g, where
L_g = span(source-span lower bound + fixed predecessor frames) and U_g = AND of fixed successor frames. Nesting between
window gates is encoded by vector membership. Objective: sum of chi(climb rank) over all climbs touching the window,
chi(r) = r((m/r)^a - 1), the linearised moment term #378 uses.
usage: lns.py PKG_DIR START.json.gz OUT.json.gz SEED ROUNDS WINDOW"""
import sys, os, gzip, json, math, random, time, itertools
pkg = os.path.abspath(sys.argv[1]); sys.path[:0] = [os.path.join(pkg, 'code'), os.path.join(pkg, 'complex', 'gx'), os.path.dirname(os.path.abspath(__file__))]
from ortools.sat.python import cp_model
from cxretime import CX, span_vecs, to_cert
from cxsplit import split
from cxkernel import echelon, inside, rehist
from evaluate import evaluate, nine_profile
from e8core import coarse

M_ = 73; SCALE = 10**6

def subspaces_between(L, U):
    """all subspaces F with span(L) <= F <= span(U) (echelon tuples), if the quotient dimension is small"""
    Ls = span_vecs(L); Q = []
    for u in U:
        if u not in span_vecs(echelon(list(L) + Q)): Q.append(u)
    d = len(Q); out = []
    if d > 5: return None
    # subspaces of span(Q) ~ F2^d: enumerate generating sets via all subsets of nonzero combos, dedupe by echelon
    combos = []
    for mask in range(1, 1 << d):
        x = 0
        for i in range(d):
            if mask >> i & 1: x ^= Q[i]
        combos.append(x)
    seen = set()
    def rec(basis, start):
        key = tuple(echelon(list(L) + basis))
        if key in seen: return
        seen.add(key); out.append(key)
        span_now = span_vecs(echelon(list(L) + basis))
        for j in range(start, len(combos)):
            if combos[j] not in span_now: rec(basis + [combos[j]], j + 1)
    rec([], 0)
    return out

def candidates(M, g, L, U, table_in):
    c = subspaces_between(L, U)
    if c is not None: return c
    Us = span_vecs(U); Ls = span_vecs(L); out = {tuple(L), tuple(U)}
    for u in sorted(Us - Ls)[:200]: out.add(tuple(echelon(list(L) + [u])))
    out |= table_in
    out.add(M.fr[M.gf[g]])
    return sorted(out)

def window_from(M, seed, size, rng):
    W = {seed}; frontier = [seed]
    while frontier and len(W) < size:
        g = frontier.pop(rng.randrange(len(frontier)))
        for r, i in M.where[g].items():
            for j in (i - 1, i + 1):
                k, x = M.occ[r][j]
                if k == 'g' and x not in W and len(W) < size: W.add(x); frontier.append(x)
    return W

def solve_window(M, W, a, timelimit=10.0):
    d = lambda F: len(F)
    chi = lambda r: 0 if r <= 0 else int(round(SCALE * r * (math.exp(a * math.log(M_ / r)) - 1)))
    table = [M.fr[f] for f in range(len(M.fr))]
    # bounds
    LB, UB = {}, {}
    for g in W:
        lo = list(M.lb[g]); up = None
        for r, i in M.where[g].items():
            j = i - 1
            while True:
                k, x = M.occ[r][j]
                if k == 'g' and x in W: j -= 1; continue
                lo += list(M.fr[x if k == 'p' else M.gf[x]]); break
            j = i + 1
            while True:
                k, x = M.occ[r][j]
                if k == 'g' and x in W: j += 1; continue
                vs = span_vecs(M.fr[x if k == 'p' else M.gf[x]]); up = vs if up is None else up & vs; break
        L = echelon(lo)
        if not all(u in up for u in L): return None
        LB[g], UB[g] = tuple(L), tuple(echelon(sorted(up)))
    mdl = cp_model.CpModel(); X = {}; cand = {}
    for g in W:
        Ls, Us = span_vecs(LB[g]), span_vecs(UB[g])
        tin = {f for f in table if all(u in Us for u in f) and all(u in span_vecs(f) for u in LB[g])}
        cand[g] = candidates(M, g, LB[g], UB[g], tin)
        cur = M.fr[M.gf[g]]
        if cur not in cand[g]: cand[g] = list(cand[g]) + [cur]
        X[g] = [mdl.NewBoolVar('') for _ in cand[g]]
        mdl.AddExactlyOne(X[g])
        for v, F in zip(X[g], cand[g]): mdl.AddHint(v, F == cur)
    D = {g: sum(len(F) * v for v, F in zip(X[g], cand[g])) for g in W}
    cost = []; base = 0
    done = set()
    for g in W:
        for r, i in M.where[g].items():
            for (i1, i2) in ((i - 1, i), (i, i + 1)):
                if (r, i1) in done: continue
                done.add((r, i1))
                k1, x1 = M.occ[r][i1]; k2, x2 = M.occ[r][i2]
                in1 = k1 == 'g' and x1 in W; in2 = k2 == 'g' and x2 in W
                d1 = D[x1] if in1 else len(M.fr[x1 if k1 == 'p' else M.gf[x1]])
                d2 = D[x2] if in2 else len(M.fr[x2 if k2 == 'p' else M.gf[x2]])
                if in1 and in2:
                    S1 = [span_vecs(F) for F in cand[x1]]; S2 = [span_vecs(F) for F in cand[x2]]
                    U1 = span_vecs(UB[x1])
                    for u in U1:
                        if u == 0: continue
                        lhs = [v for v, s in zip(X[x1], S1) if u in s]
                        if not lhs: continue
                        rhs = [v for v, s in zip(X[x2], S2) if u in s]
                        mdl.Add(sum(lhs) <= sum(rhs))
                diff = mdl.NewIntVar(0, 9, ''); mdl.Add(diff == d2 - d1)
                cv = mdl.NewIntVar(0, chi(9) + 1, ''); mdl.AddElement(diff, [chi(r_) for r_ in range(10)], cv)
                cost.append(cv)
                c1 = len(M.fr[x1 if k1 == 'p' else M.gf[x1]]); c2 = len(M.fr[x2 if k2 == 'p' else M.gf[x2]])
                base += chi(c2 - c1)
    mdl.Minimize(sum(cost))
    sol = cp_model.CpSolver(); sol.parameters.max_time_in_seconds = timelimit; sol.parameters.num_workers = 1
    st = sol.Solve(mdl)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return None
    new = {g: cand[g][[sol.Value(v) for v in X[g]].index(1)] for g in W}
    return base - sol.ObjectiveValue(), new, st == cp_model.OPTIMAL

if __name__ == '__main__':
    src = json.load(gzip.open(sys.argv[2])); out = sys.argv[3]; seed = int(sys.argv[4]); rounds = int(sys.argv[5]); size = int(sys.argv[6]); tl = float(sys.argv[7]) if len(sys.argv) > 7 else 10.0
    c = src['cert'] if 'cert' in src else src
    c, tag = split(c); rng = random.Random(seed)
    b0 = coarse(nine_profile(rehist(c)), 73, 14727); a = float(b0); best = b0
    M = CX(c); t0 = time.time(); tot = 0
    print('seed', seed, 'start b', float(b0), 'gates', len(M.gates), flush=True)
    for rd in range(rounds):
        W = window_from(M, rng.randrange(len(M.gates)), size, rng)
        res = solve_window(M, W, a, timelimit=tl)
        if res is None: continue
        gain, new, opt = res
        if gain > 0:
            old = {g: M.gf[g] for g in W}
            for g, F in new.items(): M.gf[g] = M.fid(F)
            cand = rehist(to_cert(M))
            b = coarse(nine_profile(cand), 73, 14727)
            if b > best:
                best = b; tot += 1
                print('round %d window %d gain(chi) %.0f opt %s -> b %.15e (+%.3e vs start) %.0fs' % (rd, len(W), gain, opt, float(b), float(b - b0), time.time() - t0), flush=True)
                json.dump(dict(cert=cand, tag=[list(t) for t in tag]), gzip.open(out, 'wt'))
            else:
                for g, f in old.items(): M.gf[g] = f
        if rd % 5 == 0: print('round', rd, 'improvements', tot, '%.0fs' % (time.time() - t0), flush=True)
    print('final b', float(best), 'improvements', tot)
