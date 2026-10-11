"""Greedy frame polish after annealing: for each A gate, try OR-ing in the frame of a participant's next occurrence
(merging two climbs into one) and keep strict improvements. Output adds 'extra' {gate: root-line list} to the selection.
usage: polish.py WORD SELECTION_IN SELECTION_OUT [passes]"""
import sys, json, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import core
W = core.Word(sys.argv[1]); sel = json.loads(Path(sys.argv[2]).read_text()); order, mode = sel['order'], sel['modes']
extra = {int(g): sum(1 << i for i in ls) for g, ls in sel.get('extra', {}).items()}
passes = int(sys.argv[4]) if len(sys.argv) > 4 else 3; rng = random.Random(0)
cost, bad = core.evaluate4(W, order, mode, extra); assert bad == 0; start = cost
for p in range(passes):
    _, _, _, frames = core.evaluate4(W, order, mode, extra, frames_out=True)
    pos = {g: i for i, g in enumerate(order)}
    occ = {}                                   # register -> ordered list of gates
    for g in order:
        f, d, s = W.A[g]
        for x in [d] + s: occ.setdefault(x, []).append(g)
    improved = 0; gates = list(order); rng.shuffle(gates)
    for g in gates:
        f, d, s = W.A[g]; cands = set()
        for x in [d] + s:
            lst = occ[x]; i = lst.index(g)
            cands.add(frames[lst[i + 1]] if i + 1 < len(lst) else W.next[x])
        best = None
        for mk in cands:
            if mk == frames[g]: continue
            e2 = dict(extra); e2[g] = e2.get(g, 0) | mk
            c2, b2 = core.evaluate4(W, order, mode, e2)
            if not b2 and c2 < cost - 1e-9 and (best is None or c2 < best[0]): best = (c2, e2)
        if best: cost, extra = best; improved += 1
    print('pass %d: improved %d gates, cost %.3f (start %.3f, gain %.3f)' % (p, improved, cost, start, start - cost), flush=True)
    if not improved: break
lines = lambda mk: [i for i in range(W.L.v) if mk >> i & 1]
Path(sys.argv[3]).write_text(json.dumps(dict(order=order, modes=mode, extra={str(g): lines(mk) for g, mk in sorted(extra.items())}, cost=cost)))
