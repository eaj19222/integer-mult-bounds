# Phase-A reordering and frame selection on #454's bit word

Tools and measurements for the bit word in #454 (`e8-target-mixing-whole/data/word.json.gz`, bitE8/1, R740).
**No κ is claimed here.** #454 is complex-bound, so a bit-side gain does not raise its κ. The tools are reused on #466's
word, where the bit side binds.

## Where the local cost sits

The analysis tools are `bitphase.py`, `bitchains.py` and `bitslack.py`. Costs are J = Σ r·ln(78/r) per invocation.

| phase | gates | J | note |
| --- | ---: | ---: | --- |
| D | 8,928 | 0 | compensation at frame 0 |
| A | 2,740 | 17,674 | builds helper values; 1,622 rank-1 helper climbs |
| B | 508 | 3,992 | target deliveries and mixing |
| C | 2,740 | 5,275 | already entirely at the full frame, so optimal for its entry frames |

- **Frames are tight.** 14,833 of 14,916 gates sit at the lowest legal frame: the root-closed span of the source-span
  needs plus the participants' current frames.
- **Most of phase A is support growth.** 10,133 of its 17,674 J comes from a helper climbing to contain its own newly
  added support (`bitchains.py`), because helpers receive their inputs one addition at a time.
- **Room above the floor.** The one-climb floor of phase A (pre-A frame straight to the next fixed frame) is 14,574,
  so 9,418 J lies above it.

## Optimizer

`core.py` evaluates any phase-A order that keeps every non-commuting pair in place, so the F₂ and integer operators
are identical. Frames are computed forward; per gate, `evaluate2`/`evaluate3` may raise to the largest frame that every
later occurrence allows, or keep the word's own frame. `sa.py`, `sa2.py` and `sa3.py` anneal over order and frame modes.
`build.py` writes the word, replays it with `e8core`, and prices c on the 11-stage hosted profile.

## Result on #454's word

The word's own phase-A cost (including boundary climbs into B/C) is 23,992.1. Forward-minimal frames on the same order
give 24,017.3. Order-only annealing reached 23,988.9. Annealing over order plus raises reached 23,973.3 after 70,000
moves and was still improving: 18.8 J below the word, worth about +8×10⁻⁷ on c (+0.06%). Reordering cannot remove the
step-by-step support growth, so larger gains need a different phase-A program.

Prepared with substantial Anthropic Claude assistance. The word and `e8core` are Chafik Boukhalfa's and earlier
contributors' (see #454's notices). Apache-2.0.
