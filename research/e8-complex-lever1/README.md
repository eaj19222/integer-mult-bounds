# Lever 1: re-timing the E8 complex unit (work in progress)

Working notes and tools for improving the local E8 complex unit inside #377's nine-stage component, starting from
#384 (κ = 998634656132003/10¹⁸, complex-bound). Nothing here is a new κ claim yet.

## Cost model

κ ≈ s/(1+s) with s = min(b, c). Here b ≈ 9.99633·10⁻⁴ (complex, binds) and c ≈ 1.006907·10⁻³ (#382 bit word). Work on
the complex unit alone therefore caps at κ ≈ 1.005894·10⁻³ (+7.26·10⁻⁶).

To first order b ≈ (deficit/(m·W)) / Σ_r p_r ln(m/r), where p_r is the rank-weighted share of children of rank r. At fixed
mass, b rises when the local objective J = Σ r·ln(73/r) over the unit's climbs falls. The local unit is 84% of the
total log cost (idle advances 15%, bank padding 1%). One unit of J removed per invocation is worth about 2.88·10⁻⁸ in κ.
#378's re-timing removed 13.6. +10⁻⁶ needs about 35, and the bit-side cap needs about 252.

## Where the cost sits (#378's certificate)

| class | registers | climbs | J | one-climb floor | excess |
| --- | ---: | ---: | ---: | ---: | ---: |
| x (sources) | 120 | 285 | 2,676.6 | 2,122.6 | 554.1 |
| y (targets) | 120 | 287 | 2,770.0 | 2,122.6 | 647.4 |
| s (slots) | 783 | 3,393 | 23,417.9 | 14,751.0 | 8,666.8 |
| retained copies | 9 | | 150.7 | 150.7 | 0 |

Slots carry 88% of the excess, with 4 to 5 climbs each. About 72% of slot occurrences already sit at their gate's
source-span lower bound. Frame-only moves are near exhausted, so further gains need re-ordering or coordinated multi-gate
frame changes. Exact cancellation-aware supports loosen only 28 of 2,001 gate bounds, so that is not a lever.

## Tools (`tools/`)

Run from the repository root with Python 3.11+ (standard library only). `P=research/e8-far-nine-complex`.

| tool | purpose |
| --- | --- |
| `evaluate.py P CERT` | gx.check1 (E0–E7), source-span rule, invariants, full operator identical to Sussman's original, then b and κ (two engines, PR #315 assembly) |
| `sens.py CERT` | float sensitivity model of b and κ to profile changes |
| `chains.py CERT` | per-register climb chains and the cost table above |
| `tight.py CERT P/code` | frame slack against own support and gate lower bound |
| `exactsup.py CERT P/code` | union vs exact (cancellation-aware) support lower bounds |
| `ils.py P START OUTDIR SEED ITERS` | iterated local search around #378's move family: Metropolis kick, greedy descent |

## Credits

Builds on Jacob Sussman's E8 unit and `gx` checker, jacklightChen's (Zhihao Chen) #377 nine-stage component, and Chafik
Boukhalfa's #378/#382/#384 search code and packages; see their notices. Prepared with substantial Anthropic Claude
assistance. Apache-2.0.
