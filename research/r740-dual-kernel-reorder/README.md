# Phase-A reordering on #466's bit word

Conditional **κ = 318912759793369/250000000000000000 = 0.001275651039173476**, **+0.0969% over #466**
(0.001274415506145115). The bit side still binds: bit endpoint 1277280403247194746593/10²⁴ ≈ 1.277280403·10⁻³
(#466: 1.276041713·10⁻³); complex endpoint unchanged at 129352661943759/10¹⁷ ≈ 1.293526619·10⁻³.

#466 (Rohan Arun) is bit-bound: bit endpoint ≈ 1.276041713·10⁻³, complex endpoint ≈ 1.293526619·10⁻³. Every gain on the
bit side therefore raises κ, up to about 1.4%. This package changes only phase A of #466's bit word (#459's mixed
rank151 word). It permutes commuting gates and selects legal frames so that registers climb in fewer, larger steps.
The phase-A cost J = Σ r·ln(78/r) per invocation falls from 23,998.69 to 23,970.55 (−28.15). Only two frames are added. The local
histogram changes by {1: +2, 2: −6, 3: −13, 4: +6, 5: +1, 6: +1, 7: +2} per call at unchanged rank mass, and the
hosted bit profile becomes `{1: 218280, 2: 93568, 3: 22216, 4: 31624, 5: 8720, 6: 5720, 7: 5280, 8: 792, 28: 8, 56: 456}`.
The integer prefix (155 bits, 192 charged), the three-level coefficient (520 bits, 1,024 charged) and the row coefficient
19,431 are unchanged.

`data/selection.json` freezes the order and per-gate modes found by simulated annealing (`code/core.py`; the annealer
itself is not needed for verification). `data/word.json.gz` is rebuilt from it and checked byte for byte.

## What changes and why it is sound

- **Same operator.** Phase A is a permutation of #466's A gates in which no two non-commuting gates change relative
  order. Gates commute when neither reads the other's destination; two additions into one destination also commute.
  So the F₂ map and the integer lift of A, and hence of the whole word, are unchanged. `code/apply.py` asserts the
  pairwise condition for all 2,746² pairs.
- **Legal frames.** Each A gate's frame is the forward-minimal legal frame: the root-closed span of the source-span
  needs and the participants' current frames. It may be enlarged by a frozen per-gate mode:
  - mode 1: the largest frame that every later occurrence allows;
  - mode 2: #466's own frame for that gate.

  Each register's end-of-A frame must nest into its fixed next frame in B, C or its final frame.
- **Unchanged.** D, B (including target mixing), C, starts, finals, scatter, retained totals, kernel, residual
  isometries and hosting are untouched. `code/replay_check.py` asserts every field except `A` and appended frames is
  equal. Kernel entries and isometries depend only on starts, D and the operator.
- **Re-checked from scratch on the new word.** Chafik Boukhalfa's exact `e8core` replay (nesting, common frames,
  source-span, F₂ restoration and target delivery; local rank mass unchanged), and #466's official C++ legality,
  columns and k4 checkers. Also re-run: record mutations, positive Gram frames, the emitter (which recomputes the
  integer-prefix majorants and the hosted template), the independent audit with 22 mutations, and the exact assembly
  against #466's freshly rebuilt complex supplier.

## Reproduce

Same requirements as #466 (Python 3.11+, SymPy, a C++17 compiler, Boost headers):

```sh
python -B research/r740-dual-kernel-reorder/verify.py /absolute/new/output
```

The output directory must not exist. The verifier runs #466's complete `verify.py` first.

## Scope and credit

Conditional exactly as #466: same interfaces and review points, including PR450's bit-label conjugation lemma for
target mixing, and both response kernels. No new interface is introduced. The construction is #466's (Rohan Arun) and
its lineage (see `research/r740-dual-kernel/NOTICE.md`); `e8core` is Chafik Boukhalfa's. The phase-A optimizer and this
package were prepared with substantial Anthropic Claude assistance. Apache-2.0.
