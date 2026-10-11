# #377's complete nine-stage verifier, run on #378's re-timed E8 unit

#384 claims κ = 998634656132003/10¹⁸ by putting #378's re-timed E8 unit (`gcert1-e8-r783-far`, same operator) into
#377's nine-stage complex component. It states that #377's certificate-specific finite checks were **not** re-run on the
new unit. Those are the #352 emitter/splice, the scalar-word and lifetime replay, the local Clifford frame checks and the
finite invoice's local terms. This directory re-runs **all seven** of #377's verification stages with that unit
substituted. All pass.

| #377 stage | Sussman's original (#377) | #378's unit (this run) |
| --- | --- | --- |
| fresh local admission: #352 splice, dirty scalar words in both directions on all 1,023 live columns, corrected finite guard | pass | pass (forward 10,886 / backward 11,669 scalar macros) |
| finite data, banks, profile | pass | pass |
| exact Gaussian Clifford recipes: frames / directed transitions / endpoint adapters | 946 / 3,120 / 240 | 948 / 3,122 / 240 |
| exact data and cover phases | pass | pass |
| global template and finite invoice: local source events | 1,242,936 | 1,242,864 |
| finite invoice: row coefficient / router bits / halving degree | 15,445 / 7,984 / 2 | 15,445 / 7,984 / 2 |
| independent emitted-template audit, two moment engines: b | 999240641319551/10¹⁸ | **999632926176283/10¹⁸**, next grid point rejected, 5 structural controls rejected |
| fixed-bit outer check (#361 bit, bit-bound) | pass | pass |

The template audit's b is computed from the freshly emitted global template. It equals the b that #384 derives with its own
profile rule. With #382's bit word, PR #315's assembly then gives #384's κ = 998634656132003/10¹⁸ (see `../tools/evaluate.py`).
The splice receipt records the substituted certificate's sha256 `f2664ee7…`, so the admission ran on #378's file, not on
Sussman's.

## Exactly what was changed in #377's tree

`run_pr377_on_cert.py` copies #377's `work/` tree into a fresh directory and makes these edits, recorded in `receipts/RESULT.json`:

1. The certificate file at both of its locations (`pr352/.../inputs/e8/tools/certificate/` and `pr361/complex/`) is
   replaced by #378's unit. Its two hash pins in `source-pins.json` are updated.
2. In `pins-e8.json` the structural pins V, R, H, cst, N, the scatter table hash and the centre ranks are **kept**. Ten pins
   that only record the old certificate's own statistics are removed and recomputed by the guard: frames, gates, label
   histogram, ledger, scalar steps, climbs (three), local bill and stock bits. All assertions that check the certificate
   still run.
3. Two hard-coded results in #377's stage scripts are changed to the values under test:
   - `global_nine.py`: `local_children==3974` becomes `==3973`. The guard independently recomputes 3,973.
   - `audit_nine_template.py`: the expected b becomes #384's claimed `999632926176283/10¹⁸`.
4. #377's `frozen-source-integrity` stage is not run, because it checks the manifest of the unmodified tree, which these
   edits intentionally change.

Two receipts embedded the local work-directory path. It is replaced by `<work>`, and the as-generated hashes are kept in
`receipts/ORIGINAL-HASHES-BEFORE-PATH-REDACTION.txt`. The three large regenerated artifacts are not committed; their
hashes are in `receipts/LARGE-ARTIFACTS.sha256`. Stage logs are in `receipts/logs/`, renamed `*.log.txt` because the
repository ignores `*.log`.

## Reproduce

Check out #377's package, for example `git fetch https://github.com/CrocSwap/integer-mult-bounds pull/377/head`, then:

```sh
python3 -B research/e8-complex-lever1/pr377-replay/run_pr377_on_cert.py \
  <pr377-checkout>/research/nine-stage-complex-e8/work \
  research/e8-far-nine-complex/data/gcert1-e8-r783-far.json.gz /tmp/pr377-on-378
```

The output directory must not exist. Python 3.11+, standard library only, about 4.5 minutes.

## Scope

This is an independent finite replay of #377's own checks on a substituted certificate. It is not a review of #377's
proofs, a new Lean build, or a new κ. All of #377's and #384's retained interfaces remain conditional: the local E8
invocation theorem, the general Clifford/compiler interfaces, m = 73 beyond #375's cover bound, #382's halving-degree-two
bit admission, precision and row allowances, and the analytic interfaces.

Prepared with substantial Anthropic Claude assistance. The checks are #377's (jacklightChen / Zhihao Chen, with OpenAI
Codex assistance), #352's and Jacob Sussman's. The unit is Chafik Boukhalfa's #378. Apache-2.0.
