"""Apply a frozen phase-A selection (gate order + per-gate frame mode) to a bitE8/1 word.
Only phase A changes: its commuting gates are permuted (same F2 and integer operator) and each gate's frame is the
forward-minimal legal frame, optionally enlarged by mode 1 (the largest frame every later occurrence allows) or
mode 2 (the parent word's own frame for that gate), and by an optional frozen extra mask per gate. D, B, C, starts, finals, scatter, ret and target_mix are unchanged.
usage: apply.py PARENT_WORD.json.gz SELECTION.json OUT_WORD.json.gz"""
import sys, json, gzip, copy, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
W = core.Word(sys.argv[1]); sel = json.loads(Path(sys.argv[2]).read_text())
order, mode = sel['order'], sel['modes']; n = len(W.A)
assert sorted(order) == list(range(n)) and len(mode) == n and set(mode) <= {0, 1, 2}
# every relocation must be a sequence of commuting swaps: check that no non-commuting pair changed relative order
pos = {g: i for i, g in enumerate(order)}
for i in range(n):
    for j in range(i + 1, n):
        if not W.commute(i, j): assert pos[i] < pos[j], ('non-commuting gates reordered', i, j)
extra = {int(g): sum(1 << i for i in ls) for g, ls in sel.get('extra', {}).items()}
cost, bad, hist, frames = core.evaluate4(W, order, mode, extra, frames_out=True)
assert bad == 0, 'end-of-A frame does not nest into the fixed next frame'
c = copy.deepcopy(W.c); key = {}
for i, fr in enumerate(c['frames']): key.setdefault(W.fmask[i], i)
def fid(mask):
    if mask in key: return key[mask]
    idx = [i for i in range(W.L.v) if mask >> i & 1]; rows, piv, basis = W.L._basis(idx)
    c['frames'].append(basis); key[mask] = len(c['frames']) - 1; return key[mask]
c['A'] = [[fid(frames[g]), W.A[g][1], list(W.A[g][2])] for g in order]
raw = json.dumps(c, separators=(',', ':')).encode()
Path(sys.argv[3]).write_bytes(gzip.compress(raw, mtime=0))
print(json.dumps(dict(phase_a_cost=round(cost, 6), new_frames=len(c['frames']) - len(W.c['frames']), word_json_sha256=hashlib.sha256(raw).hexdigest())))
