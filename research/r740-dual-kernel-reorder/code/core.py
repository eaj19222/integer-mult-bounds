"""Fast phase-A evaluator for bitE8/1 words: given an order of the A gates, compute forward-minimal legal frames
(root-closed span of source-span needs + participants' current frames), the climbs and J = sum r ln(m/r).
D, B, C, start and final are fixed; the end-of-A frame of every register must nest into its next fixed frame."""
import sys, math, gzip, json
from fractions import Fraction as Q
M = 78
def J(k): return k * math.log(M / k) if k > 0 else 0.0

class Lines:
    def __init__(self, lines):
        self.vec = [tuple(x) for x in lines]; self.v = len(lines); self.cache = {0: (0, 0)}
    def _basis(self, idx):
        rows = []                                   # fraction-free echelon over Q of the line vectors
        piv = []
        basis = []
        for i in idx:
            x = [Q(a) for a in self.vec[i]]
            for p, r in zip(piv, rows):
                if x[p]: f = x[p] / r[p]; x = [a - f * b for a, b in zip(x, r)]
            nz = next((j for j, a in enumerate(x) if a), None)
            if nz is not None: rows.append(x); piv.append(nz); basis.append(i)
        return rows, piv, basis
    def close(self, mask):
        """(closed mask, dim) of the rational span of the lines in mask"""
        hit = self.cache.get(mask)
        if hit is not None: return hit
        idx = [i for i in range(self.v) if mask >> i & 1]
        rows, piv, basis = self._basis(idx)
        d = len(basis)
        if d == 8: out = (1 << self.v) - 1
        else:
            out = 0
            for i in range(self.v):
                if mask >> i & 1: out |= 1 << i; continue
                x = [Q(a) for a in self.vec[i]]
                for p, r in zip(piv, rows):
                    if x[p]: f = x[p] / r[p]; x = [a - f * b for a, b in zip(x, r)]
                if not any(x): out |= 1 << i
        self.cache[mask] = (out, d); self.cache[out] = (out, d); return out, d

class Word:
    def __init__(self, path):
        self.c = c = json.load(gzip.open(path)); self.v, self.R = c['v'], c['R']; self.n = 2 * self.v + self.R
        self.L = Lines(c['lines']); v = self.v
        self.fmask = [self.L.close(sum(1 << i for i in fr))[0] for fr in c['frames']]
        self.A = [(f, d, list(s)) for f, d, s in c['A']]
        # frame of every register just before A (after D; D is at frame 0 and leaves helpers at their start frame)
        self.pre = [self.fmask[c['start'][r]] for r in range(self.n)]
        # next fixed frame after A for each register: the first B/C gate naming it, else its final frame
        nxt = {}
        for ph in ('B', 'C'):
            for f, d, s in c[ph]:
                for x in [d] + list(s): nxt.setdefault(x, self.fmask[f])
        self.next = [nxt.get(r, self.fmask[c['final'][r]]) for r in range(self.n)]
        # A-gate read/write sets for commutation
        self.rd = [set(s) for f, d, s in self.A]; self.wr = [d for f, d, s in self.A]
    def commute(self, i, j):
        a, b = self.A[i], self.A[j]
        return a[1] not in self.rd[j] and b[1] not in self.rd[i]          # same destination is fine (additions commute)
    def evaluate(self, order, frames_out=False):
        v = self.v; L = self.L; cur = list(self.pre); zs = [1 << r if r < v else 0 for r in range(self.n)]
        cost = 0.0; hist = {}; frames = [None] * len(self.A)
        dim = lambda mk: L.close(mk)[1]
        for gi in order:
            f, d, srcs = self.A[gi]
            need = 0
            for s in srcs:
                if s < v or s >= 2 * v: need |= zs[s]
            zd = zs[d]
            for s in srcs: zd |= zs[s]
            if d >= 2 * v: need |= zd
            mk = need
            for x in [d] + srcs: mk |= cur[x]
            mk, dm = L.close(mk)
            for x in [d] + srcs:
                if cur[x] != mk:
                    k = dm - dim(cur[x]); cost += J(k); hist[k] = hist.get(k, 0) + 1; cur[x] = mk
            zs[d] = zd; frames[gi] = mk
        # boundary into the fixed next frame
        bad = 0
        for r in range(self.n):
            if cur[r] & ~self.next[r]: bad += 1; continue
            if cur[r] != self.next[r]:
                k = dim(self.next[r]) - dim(cur[r]); cost += J(k); hist[('b', k)] = hist.get(('b', k), 0) + 1
        return (cost, bad, hist, frames) if frames_out else (cost, bad)
    def actual_cost(self):
        """J of the word's own A frames (same accounting), for comparison"""
        v = self.v; L = self.L; cur = list(self.pre); cost = 0.0
        for f, d, srcs in self.A:
            mk = self.fmask[f]
            for x in [d] + srcs:
                if cur[x] != mk: cost += J(L.close(mk)[1] - L.close(cur[x])[1]); cur[x] = mk
        for r in range(self.n):
            if cur[r] != self.next[r]: cost += J(L.close(self.next[r])[1] - L.close(cur[r])[1])
        return cost

def evaluate2(W, order, raise_flags=None, frames_out=False):
    """Forward evaluation with optional raises: a raised gate takes close(lb + bmax_g), where bmax_g is the largest
    root-closed frame that every participant's later occurrences (at their own bmax) and fixed next frames allow."""
    v = W.v; L = W.L; n = W.n
    # backward pass: bmax per gate for this order
    nxt = list(W.next); bmax = [0] * len(W.A)
    for gi in reversed(order):
        f, d, srcs = W.A[gi]; mk = -1
        for x in [d] + srcs: mk = nxt[x] if mk == -1 else (mk & nxt[x])
        mk = L.close(mk)[0]; bmax[gi] = mk
        for x in [d] + srcs: nxt[x] = mk
    cur = list(W.pre); zs = [1 << r if r < v else 0 for r in range(n)]; cost = 0.0; hist = {}; frames = [None] * len(W.A)
    dim = lambda mk: L.close(mk)[1]
    for gi in order:
        f, d, srcs = W.A[gi]; need = 0
        for s in srcs:
            if s < v or s >= 2 * v: need |= zs[s]
        zd = zs[d]
        for s in srcs: zd |= zs[s]
        if d >= 2 * v: need |= zd
        mk = need
        for x in [d] + srcs: mk |= cur[x]
        if raise_flags is None or raise_flags[gi]: mk |= bmax[gi]
        mk, dm = L.close(mk)
        for x in [d] + srcs:
            if cur[x] != mk:
                k = dm - dim(cur[x]); cost += J(k); hist[k] = hist.get(k, 0) + 1; cur[x] = mk
        zs[d] = zd; frames[gi] = mk
    bad = 0
    for r in range(n):
        if cur[r] & ~W.next[r]: bad += 1; continue
        if cur[r] != W.next[r]:
            k = dim(W.next[r]) - dim(cur[r]); cost += J(k); hist[('b', k)] = hist.get(('b', k), 0) + 1
    return (cost, bad, hist, frames) if frames_out else (cost, bad)

def evaluate3(W, order, mode, frames_out=False):
    """mode[g] in {0: minimal, 1: raise to bmax, 2: include the word's own frame for g}"""
    v = W.v; L = W.L; n = W.n
    nxt = list(W.next); bmax = [0] * len(W.A)
    if any(m == 1 for m in mode):
        for gi in reversed(order):
            f, d, srcs = W.A[gi]; mk = -1
            for x in [d] + srcs: mk = nxt[x] if mk == -1 else (mk & nxt[x])
            mk = L.close(mk)[0]; bmax[gi] = mk
            for x in [d] + srcs: nxt[x] = mk
    cur = list(W.pre); zs = [1 << r if r < v else 0 for r in range(n)]; cost = 0.0; hist = {}; frames = [None] * len(W.A)
    dim = lambda mk: L.close(mk)[1]
    for gi in order:
        f, d, srcs = W.A[gi]; need = 0
        for s in srcs:
            if s < v or s >= 2 * v: need |= zs[s]
        zd = zs[d]
        for s in srcs: zd |= zs[s]
        if d >= 2 * v: need |= zd
        mk = need
        for x in [d] + srcs: mk |= cur[x]
        md = mode[gi]
        if md == 1: mk |= bmax[gi]
        elif md == 2: mk |= W.fmask[f]
        mk, dm = L.close(mk)
        for x in [d] + srcs:
            if cur[x] != mk:
                k = dm - dim(cur[x]); cost += J(k); hist[k] = hist.get(k, 0) + 1; cur[x] = mk
        zs[d] = zd; frames[gi] = mk
    bad = 0
    for r in range(n):
        if cur[r] & ~W.next[r]: bad += 1; continue
        if cur[r] != W.next[r]:
            k = dim(W.next[r]) - dim(cur[r]); cost += J(k); hist[('b', k)] = hist.get(('b', k), 0) + 1
    return (cost, bad, hist, frames) if frames_out else (cost, bad)

def evaluate4(W, order, mode, extra, frames_out=False):
    """evaluate3 plus per-gate extra masks (extra[g] is OR-ed into gate g's frame before closure)"""
    v = W.v; L = W.L; n = W.n
    nxt = list(W.next); bmax = [0] * len(W.A)
    if any(m == 1 for m in mode):
        for gi in reversed(order):
            f, d, srcs = W.A[gi]; mk = -1
            for x in [d] + srcs: mk = nxt[x] if mk == -1 else (mk & nxt[x])
            mk = L.close(mk)[0]; bmax[gi] = mk
            for x in [d] + srcs: nxt[x] = mk
    cur = list(W.pre); zs = [1 << r if r < v else 0 for r in range(n)]; cost = 0.0; hist = {}; frames = [None] * len(W.A)
    dim = lambda mk: L.close(mk)[1]
    for gi in order:
        f, d, srcs = W.A[gi]; need = 0
        for s in srcs:
            if s < v or s >= 2 * v: need |= zs[s]
        zd = zs[d]
        for s in srcs: zd |= zs[s]
        if d >= 2 * v: need |= zd
        mk = need | extra.get(gi, 0)
        for x in [d] + srcs: mk |= cur[x]
        md = mode[gi]
        if md == 1: mk |= bmax[gi]
        elif md == 2: mk |= W.fmask[f]
        mk, dm = L.close(mk)
        for x in [d] + srcs:
            if cur[x] != mk:
                k = dm - dim(cur[x]); cost += J(k); hist[k] = hist.get(k, 0) + 1; cur[x] = mk
        zs[d] = zd; frames[gi] = mk
    bad = 0
    for r in range(n):
        if cur[r] & ~W.next[r]: bad += 1; continue
        if cur[r] != W.next[r]:
            k = dim(W.next[r]) - dim(cur[r]); cost += J(k); hist[('b', k)] = hist.get(('b', k), 0) + 1
    return (cost, bad, hist, frames) if frames_out else (cost, bad)
