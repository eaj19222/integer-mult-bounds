"""Float sensitivity model for the #377/#384 nine-stage complex saving b.
b solves sum_r (r n_r/(m W)) (m/r)^a + fallback = 1."""
import gzip, json, math, sys
from collections import Counter
def root(H, m, W, fb=True):
    tot = sum(H.values()); f = 32*m*m*tot/1e16/(m*W) if fb else 0  # rank-1 fallback, as e8core.coarse
    g = lambda a: sum(r*n/(m*W)*math.exp(a*math.log(m/r)) for r, n in H.items()) + f*math.exp(a*math.log(m)) - 1
    lo, hi = 0.0, 0.01
    for _ in range(200):
        mid = (lo+hi)/2
        lo, hi = (mid, hi) if g(mid) < 0 else (lo, mid)
    return lo
def nine(cert, k=4, L=9, T=8):
    h, v, R, cst = cert['h'], cert['v'], cert['R'], cert['cst']
    H = Counter()
    for blk in cert['blocks'].values():
        for r, n in blk.items(): H[int(r)] += L*T*n
    idle = [x for j in range(1, k) for x in (2*j*(h-1), h-1)] + [2*(k-j)*(h-1) for j in range(1, k+1)]
    for r in idle:
        if r: H[r] += 2*v*T
    H[1] += L*R
    m, W = h + 8*(L-1), 2*k*v*T + L*R
    return H, m, W
cert = json.load(gzip.open(sys.argv[1]))
H, m, W = nine(cert)
D = m*W - sum(r*n for r, n in H.items())
b = root(H, m, W); kap = lambda x: x/(1+x)
E = sum(r*n/(m*W)*math.log(m/r) for r, n in H.items())
print(f"m={m} W={W} deficit={D}  delta=D/(mW)={D/(m*W):.6e}  E[ln(m/r)]={E:.5f}  first-order b~delta/E={D/(m*W)/E:.6e}")
print(f"b(float)={b:.12e}  kappa~b/(1+b)={kap(b):.12e}")
loc = Counter()
for blk in cert['blocks'].values():
    for r, n in blk.items(): loc[int(r)] += n
mass = sum(r*n for r, n in loc.items())
J = sum(r*n*math.log(m/r) for r, n in loc.items())
print(f"\nlocal E8 unit (per invocation): histogram {dict(sorted(loc.items()))}  mass N={mass}  sum r ln(m/r)={J:.1f}")
mx = max(loc)
print(f"  floor if every local child had rank {mx}: {mass*math.log(m/mx):.1f}  -> headroom {J-mass*math.log(m/mx):.1f} per invocation")
# contribution breakdown of E
parts = {'local (72 invocations)': sum(72*r*n*math.log(m/r) for r, n in loc.items())}
idle = Counter(); [idle.__setitem__(r, idle[r]+2*cert['v']*8) for r in [16,8,32,8,48,8,48,32,16]]
parts['idle data advances'] = sum(r*n*math.log(m/r) for r, n in idle.items())
parts['bank padding (rank 1)'] = 9*cert['R']*math.log(m)
for k_, x in parts.items(): print(f"  share of sum r n ln(m/r): {k_:28s} {x/(E*m*W):6.1%}")
# levers
def report(name, H2, m2, W2):
    b2 = root(H2, m2, W2); print(f"  {name:62s} b={b2:.6e}  kappa={kap(b2):.6e}  dkappa={kap(b2)-kap(b):+.3e}")
cap = kap(1.006907040309932e-3)
print(f"\nlevers (complex side; bit c = 1.006907e-3 caps kappa at {cap:.6e}, i.e. +{cap-kap(b):.3e})")
H2 = H.copy(); H2[1] -= 2*72; H2[2] += 72; report("per invocation: two rank-1 children merged into one rank-2", H2, m, W)
H2 = H.copy(); H2[4] -= 2*72; H2[8] += 72; report("per invocation: two rank-4 children merged into one rank-8", H2, m, W)
H2 = H.copy(); H2[8] -= 9; report("copy loss cst 72->71 (deficit +72; 72 less rank-8 mass)", H2, m, W)
# conversion: kappa gain per unit reduction of local sum r ln(m/r), per invocation, at fixed mass
H2 = H.copy(); H2[1] -= 2*72; H2[2] += 72
dJ = 72*(2*1*math.log(m/1) - 2*math.log(m/2))
per = (kap(root(H2, m, W)) - kap(b)) / (dJ/72)
print(f"\n  ~{per:.3e} kappa per unit of local sum r ln(m/r) removed per invocation")
print(f"  #378 removed {13.6:.1f}/invocation -> ~{13.6*per:.2e};  +1e-6 needs ~{1e-6/per:.0f};  reaching the bit cap needs ~{(cap-kap(b))/per:.0f} (of {J:.0f})")
