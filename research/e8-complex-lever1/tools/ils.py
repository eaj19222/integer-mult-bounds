"""Iterated local search around #378's move family (far piece relocation, single/block retiming, in-group piece
relocation) in #377's nine-stage setting: random-walk kick (Metropolis block moves) then greedy descent; keep if b rises.
usage: ils.py PKG_DIR START.json.gz OUTDIR SEED ITERS"""
import sys, os, gzip, json, random, time, math, copy
pkg = os.path.abspath(sys.argv[1]); sys.path[:0] = [os.path.join(pkg, 'code'), os.path.join(pkg, 'complex', 'gx'), os.path.dirname(os.path.abspath(__file__))]
from cxfar import far_pass, piece_pass, split, CX, rehist, to_cert, bsweep
from cxsplit import single_sweep
from evaluate import evaluate, load, nine_profile
from e8core import coarse

def price9(c): return coarse(nine_profile(c), 73, 14727)

def descend(c, tag, a, rng, limit=60):
    for p in range(limit):
        c, tag, g = far_pass(c, tag, a, 73); M = CX(c)
        for s in range(10):
            m1, _ = single_sweep(M, a, 73, rng); m2, _ = bsweep(M, a, 73, rng)
            if not (m1 or m2): break
        c = rehist(to_cert(M)); c, tag, g2 = piece_pass(c, tag, a, 73)
        if g == 0 and g2 == 0: break
    return c, tag

def kick(c, a, rng, temp, sweeps):
    M = CX(c)
    for _ in range(sweeps): bsweep(M, a, 73, rng, temp=temp)
    return rehist(to_cert(M))

if __name__ == '__main__':
    src = json.load(gzip.open(sys.argv[2])); outdir = sys.argv[3]; seed = int(sys.argv[4]); iters = int(sys.argv[5])
    os.makedirs(outdir, exist_ok=True); rng = random.Random(seed)
    c, tag = (src['cert'], [tuple(t) for t in src['tag']]) if 'cert' in src else split(src)
    best = cur = price9(c); a = float(best); bc, bt = c, tag
    print('seed', seed, 'start b', float(best), flush=True); t0 = time.time()
    for it in range(iters):
        temp = a * rng.choice([0.5, 1, 2, 4])
        c2 = kick(bc, a, rng, temp, rng.choice([1, 2, 3])); t2 = list(bt)
        c2, t2 = descend(c2, t2, a, rng)
        b = price9(c2)
        tag_ = 'NEW BEST' if b > best else ''
        print('it %d temp/a %.1f b %.15e (best %+.3e) %.0fs %s' % (it, temp / a, float(b), float(b - best), time.time() - t0, tag_), flush=True)
        if b > best:
            best, bc, bt = b, c2, t2
            json.dump(dict(cert=c2, tag=[list(x) for x in t2]), gzip.open(os.path.join(outdir, 'best-seed%d.json.gz' % seed), 'wt'))
    print('final best', float(best))
