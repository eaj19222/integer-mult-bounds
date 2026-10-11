"""Exact replay of the parent and new bit words with Chafik Boukhalfa's e8core engine (legality, nesting, common frames,
source-span, F2 restoration of sources/helpers and target delivery), plus the claims this package relies on:
the A phase is a permutation of the parent's A gates, every other phase and field is unchanged, and the local rank
mass is unchanged. usage: replay_check.py E8CORE_DIR PARENT_WORD NEW_WORD"""
import sys, json
from collections import Counter
sys.path.insert(0, sys.argv[1]); import e8core as E
p, c = E.load_word(sys.argv[2]), E.load_word(sys.argv[3])
for k in p:
    if k not in ('A', 'frames'): assert p[k] == c[k], ('field changed', k)
assert c['frames'][:len(p['frames'])] == p['frames'], 'existing frames must be kept'
key = lambda g: (g[1], tuple(g[2]))
assert Counter(map(key, p['A'])) == Counter(map(key, c['A'])), 'A is not a permutation of the parent A gates'
rp, rc = E.replay(p), E.replay(c)
assert not rc['viol'], ('source-span violations', len(rc['viol']))
mass = lambda H: sum(r * n for r, n in H.items())
assert mass(rp['H']) == mass(rc['H']), 'local rank mass changed'
dH = {k: rc['H'].get(k, 0) - rp['H'].get(k, 0) for k in sorted(set(rp['H']) | set(rc['H'])) if rc['H'].get(k, 0) != rp['H'].get(k, 0)}
print(json.dumps(dict(status='PASS_E8CORE_EXACT_REPLAY', parent_local_histogram={str(k): v for k, v in sorted(rp['H'].items())},
                      new_local_histogram={str(k): v for k, v in sorted(rc['H'].items())}, delta={str(k): v for k, v in dH.items()},
                      new_frames=len(c['frames']) - len(p['frames']))))
