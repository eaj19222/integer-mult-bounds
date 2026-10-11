"""Simulated annealing over the phase-A order (commuting relocations only), forward-minimal frames.
usage: sa.py WORD SEED MOVES T0 T1 OUT.json"""
import sys, math, random, time, json
import core
W = core.Word(sys.argv[1]); seed = int(sys.argv[2]); moves = int(sys.argv[3]); T0, T1 = float(sys.argv[4]), float(sys.argv[5])
rng = random.Random(seed); n = len(W.A)
order = list(range(n)); cost, bad = W.evaluate(order); assert bad == 0
best, best_order = cost, list(order); start = cost; t0 = time.time(); acc = 0
for it in range(moves):
    T = T0 * (T1 / T0) ** (it / max(1, moves - 1))
    p = rng.randrange(n); g = order[p]
    lo = p
    while lo > 0 and W.commute(g, order[lo - 1]): lo -= 1
    hi = p
    while hi < n - 1 and W.commute(g, order[hi + 1]): hi += 1
    if lo == hi: continue
    q = rng.randint(lo, hi)
    if q == p: continue
    new = order[:p] + order[p + 1:]; new.insert(q, g)
    c2, b2 = W.evaluate(new)
    if b2: continue
    if c2 <= cost or rng.random() < math.exp(-(c2 - cost) / T):
        order, cost = new, c2; acc += 1
        if cost < best - 1e-9: best, best_order = cost, list(order)
    if it % 5000 == 0:
        print('it %d T %.2f cost %.1f best %.1f (start %.1f, gain %.1f) acc %d cache %d %.0fs' % (it, T, cost, best, start, start - best, acc, len(W.L.cache), time.time() - t0), flush=True)
json.dump(dict(order=best_order, cost=best, start=start), open(sys.argv[6], 'w'))
print('final best %.1f gain %.1f' % (best, start - best))
