# Can the decoder copy loss go below 72?

Both E8 suppliers pay a copy loss of 72 per local invocation: the summed rank of the retained-total copies (cst). It
enters the deficit as D = T(2kv − L·cst). In #454's eleven-stage layout, each unit of copy loss saved adds 88 to the
deficit 3,264, roughly +2.7% on that supplier's saving. This directory checks whether either decoder can be made
cheaper. **No new κ is claimed.** The results below are negative or inconclusive, and are recorded so the question
need not be re-run.

## Bit side (F₂ decoder on the 120 E8 root lines): exact

Model (Dylan Crow's #370 `centres_sat.py`, vendored in `src/`): w_S, u_t ∈ F₂ᵏ with ⟨u_t, w_t⟩ = 1 and ⟨u_t, w_S⟩ = 0
for each of the 56 neighbours S of t. Centre i holds T_i = Σ_S (w_S)_i x_S, and its copy rank is the rank of the root
span of its support. #370 shows k = 8 is infeasible and k = 9 is feasible. Every known 9-centre decoder copies at
rank 8, giving 9·8 = 72.

**Question:** can some centre of a 9-centre decoder have its support inside a root-spanned hyperplane (copy rank ≤ 7,
copy loss ≤ 71)? Any nonzero functional on F₂⁹ becomes a centre after a change of basis, so it suffices to constrain
one coordinate, with no normalization (`sat_hyp.py 9 T free 8:<root>`). That run is UNKNOWN after 1,200 s.

**Normalization without loss of generality** (`normh`, `hyperplanes.py`): choose 8 pairwise-neighbour lines outside
the hyperplane H. Their w-vectors vanish in the constrained coordinate. The Gram block of the clique is the
identity, so the w-vectors form a basis of that coordinate hyperplane of F₂⁹. A basis change that fixes the
constrained coordinate maps them to e₁…e₈. Then u of each clique line equals e_j in those coordinates, and every
constraint is preserved.

**Result:** sampling 6,000 random 7-root spans finds root-spanned hyperplanes containing 63, 42, 37, 28, 23, 22, 16
and 14 lines. For one representative of each size, CP-SAT proves INFEASIBLE in seconds (`hyperplanes-representatives.log.txt`).
`hyperplanes_all.py` re-proves every distinct hyperplane found (1,630); the 120 E7-type ones are all infeasible so far.
Smaller frames lie inside some hyperplane, so they are excluded too. With k ≥ 10, copy loss below 72 would need at
least 9 centres of rank ≤ 7. **Within this decoder model, 72 is the minimum copy loss for the bit word.**

Also checked: for one CP-SAT 9-centre decoder, all 511 nonzero functionals have support spanning Q⁸ (rank 8).

## Complex side (rational decoder on binary ports in F₂⁹): structural evidence, not a proof

`decode.py` verifies the decoding model exactly on Sussman's unit. After phase A and the scatter, each target has
coefficient 1 on its own source, 0 on its 63 non-orthogonal sources, and junk only on its 56 orthogonal sources.
Consequences:

- At least 8 centres are needed (`cliques.py`). There are exactly 2,025 maximum sets of pairwise non-orthogonal
  ports, all of size 8. On each one the decoder is an 8×8 identity.
- Both admitted decoders are **Gram-type**: source s carries its root vector, and u_t·c_s = r_t·r_s/4, which vanishes
  on every orthogonal line.
  - In this family a centre is a linear functional on Q⁸ and its support is the set of lines not orthogonal to it.
  - The smallest supports come from roots: 56 neighbours whose ports lie in one binary hyperplane, plus the root
    itself, whose port does not.
  - Splitting off the root costs 8 + 1, so 72 is the floor of the family. #433's split-centre decoder (8 rank-eight
    and 8 rank-one copies) attains it.
- **The coordinate copies cannot be absorbed.** The 8 coordinate lines 2e_i are pairwise orthogonal as roots, so
  their binary ports are pairwise non-orthogonal. Each one lies outside every hyperplane P(2e_j)^⊥, including its
  own, so they need their own centres.
- **Non-Gram decoders remain open.** In Sussman's decoder, the sources outside every one of the 511 binary hyperplanes
  span all of Q⁸ (`rigid.py`, exact). Decoders are not rigid, though, so this does not cover every decoder. The
  matching filter (`hall.py`) does not exclude hyperplane centres.
  - Alternating least squares and trust-region solvers (`als2.py`) fail on every cheaper layout tried.
  - They also fail on a restricted problem known to be feasible, so these failures are not evidence.
  - An F₃ CP-SAT proxy (`cdec.py`) cannot recover #433's known layout within 600 s.

## Reproduce

```sh
pip install ortools numpy scipy
cd research/decoder-copy-loss
python3 sat_hyp.py 9 60 norm             # #370's 9-centre decoder: OPTIMAL, copy loss 72
python3 sat_hyp.py 9 600 normh 8:0       # a centre inside the E7 hyperplane 0^perp: INFEASIBLE
python3 hyperplanes.py                   # one representative of each hyperplane size: all INFEASIBLE
```

The complex-side scripts (`decode.py`, `cliques.py`, `hall.py`, `als2.py`, `rigid.py`) take Sussman's certificate
`gcert1-e8-r783.json.gz` as their first argument. It is pinned in the #377 and #384 packages and is not in this tree.
`cdec.py` reads #433's canonical complex word from `$COMPLEX433`. That word is written to `split-centres/CANONICAL-WORD.json.gz`
by `research/split-centres-global/verify.py`.

Prepared with substantial Anthropic Claude assistance. `src/` is Dylan Crow's #370 code (Apache-2.0). The decoder
structure is Jacob Sussman's (#352), and the split-centre decoder is icekylinx's (#433).
