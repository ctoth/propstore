# WS-D: Subjective-logic operator naming and correctness

**Status**: CLOSED ea232e21
**Depends on**: nothing (parallel to WS-A and WS-O-*)
**Blocks**: WS-F (preference operator naming overlap), WS-G (Spohn vs Opinion representations), WS-H (probabilistic argumentation builds on Opinion algebra), WS-I (CEL semantic equality used in ATMS support comparisons), WS-J (worldline subjective-logic integration).
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1)

---

## Why this workstream is foundational for the math layer

WS-A makes test fixtures honest. WS-D makes the *math* honest. Five downstream workstreams (F, G, H, I, J) call into `propstore/opinion.py` or `propstore/world/types.py:apply_decision_criterion` and assume the operator labelled `wbf` is actually Weighted Belief Fusion (van der Heijden 2018 Def 4), the operator labelled `pignistic` is actually the pignistic transformation (Smets & Kennes 1994; Denoeux 2019 §6.2), and the CEL parser actually accepts the language documented as CEL. None of these three assumptions hold today.

`docs/gaps.md` carries two HIGH items in the WS-Z-types continuation that explicitly name this workstream:

1. *"`opinion.wbf()` is algebraically aCBF, not WBF. ... worked example drifts 0.175 absolute on uncertainty. Commit `c7a9215` self-acknowledges the open bug."*
2. *"CLAUDE.md \"Pignistic\" claim names Denoeux but implements Jøsang. ... Diverges whenever `a ≠ 0.5`."*

Both are documented self-acknowledged drifts. Per the 2026-04-27 decisions log, both are now locked-in math fixes — not renames, not flag-renames. WS-D commits the result to a paper-grounded test corpus.

A naming bug at this layer is not cosmetic. `RenderPolicy.decision_criterion="pignistic"` is the *default* for every render path (`propstore/world/types.py:1230`). Every claim rendered through propstore is being labelled with one citation while computed with another; the gap is invisible to callers because the formula always returns *something* in [0, 1]. A future agent who reads the docstring will compute the wrong number for any base rate ≠ 0.5 — including the propstore-default base rate of 0.5 only by accident.

## Resolved decisions (locked in 2026-04-27)

These are no longer open questions. They are constraints on the production change sequence.

### Decision D-1 — `opinion.wbf()` is fixed to true vdH 2018 Def 4 (NOT renamed)

**Q's pushback**: "What do those callers actually expect? if they expect WBF, give them WBF, don't just do the easy thing."

**Execution correction, 2026-04-28**: direct reread of the page images for van der Heijden et al. 2018 showed that the earlier WS-D text was wrong about a shared-base-rate precondition. Definition 4 on paper p.5 computes base rate as a confidence-weighted value `Σ a_i(1-u_i) / Σ(1-u_i)`. The implementation therefore follows the paper, not the stale shared-`a` workstream wording.

**Verdict**: `opinion.wbf()` now implements vdH 2018 Definition 4 using the paper's confidence-weighted belief/disbelief and base-rate equations, the p.5 dogmatic/no-evidence cases, and the Table I p.8 numerical regression. The old `_BASE_RATE_CLAMP` path is not applied to WBF. Renaming was rejected; callers asking for WBF now get WBF.

**Re-validation**: the three WBF call sites were revalidated: `propstore/opinion.py` `fuse(method="wbf")`, `fuse(method="auto")`, and the classification/fusion tests. No committed `tests/data/fragility_*.yaml` fixture corpus exists in this repo state; the full fragility test suite passed under the corrected WBF path.

### Decision D-2 — `decision_criterion="pignistic"` is fixed to true Smets BetP, AND a new `projected_probability` flag covers the Jøsang formula

**Q's pushback**: "what do the callers actually think they are getting again? why is this such a weird/hard concept? What does the paper say?"

**Verdict**: Two transformations are real and distinct. Both are reachable. Both under their correct names.

- `decision_criterion="pignistic"` → Smets & Kennes 1994 BetP. For a binomial frame `{x, ¬x}`: `BetP(x) = b + u/2` (because `m({x,¬x})/|{x,¬x}| = u/2`). For a non-binomial frame: `BetP(ω) = Σ_{A∋ω} m(A)/|A|`, distributed by *base rate*. The current binomial Opinion type makes this `b + u/2`; multinomial extension is deferred to a future workstream but the flag value is reserved.
- `decision_criterion="projected_probability"` (NEW flag value) → Jøsang 2001 Def 6 projected probability `b + a·u`. This is the formula that actually runs today under the `pignistic` flag.

Citation update at `propstore/world/types.py:1235-1236`: `Smets_Kennes_1994` for the BetP path, `Josang_2001 Def 6` for the projected_probability path. Drop the standalone `Denoeux_2019` reference at the *function* docstring level (it stays at the criterion-list level as the review-of-decision-criteria source).

CLI Choice list at `propstore/cli/world/reasoning.py:112` gains `projected_probability`:

```
type=click.Choice(["pignistic", "projected_probability", "lower_bound", "upper_bound", "hurwicz"])
```

Per Q's "no old repos" rule, no aliases. Every test corpus exercising the flag — fixtures, parameterized tests, doc snippets, README examples — gets re-validated. Rows with `criterion="pignistic"` and `a ≠ 0.5` change their expected values (because the formula changes). Rows with `criterion="pignistic"` and `a = 0.5` are numerically unchanged but conceptually re-anchored. Rows that *want* the old formula are migrated to `criterion="projected_probability"`.

The default `RenderPolicy.decision_criterion` stays `"pignistic"` — Q's framing was that callers selecting "pignistic" expect *the* Smets/Denoeux pignistic transformation, so the default should remain pignistic now that pignistic is *actually* pignistic. (If Q later prefers projected_probability as the default, that is a separate one-line change; it does not gate this WS.)

## Review findings covered

| Finding | Source | Citation | Description |
|---|---|---|---|
| **T2.7** | REMEDIATION Tier 2 | `propstore/opinion.py:432-522`; vdH 2018 Def 4 p.4-5 | `wbf()` numerator omits the `1/u_i` factor required by Def 4. Also: `_BASE_RATE_CLAMP` + confidence-weighted `a` blend (lines 502-514) where Def 4 requires shared `a`; averaged-`b/d/a` for ≥2 dogmatic sources (lines 449-467) where Remark 2 specifies ε-limit. **Fix per D-1**: rewrite numerator + base rate handling to vdH Def 4. |
| **T2.8** | REMEDIATION Tier 2 | `propstore/world/types.py:1230, 1235, 1257-1259`; Smets & Kennes 1994 §3; Denoeux 2019 p.17-18 | `decision_criterion="pignistic"` cites Denoeux but implements Jøsang `b + a·u`. **Fix per D-2**: rewrite formula to `b + u/2`; add `projected_probability` flag value carrying `b + a·u`; update citation to `Smets_Kennes_1994`. |
| **T2.13** | REMEDIATION Tier 2 | `propstore/cel_checker.py:181-184, 207-209` | `FLOAT_LIT` regex `\d+\.\d*\|\.\d+` lacks exponent. `STRING_LIT` escape replacement only handles `\"`, `\'`, `\\`. CEL spec needs `[eE][+-]?\d+` and `\n \r \t \u \x \0` plus octal. |
| **gaps.md F1** | `docs/gaps.md` line 20 | `propstore/opinion.py:432-522` | Same as T2.7. Documented 0.175 absolute drift on uncertainty for vdH Table I. |
| **gaps.md F2** | `docs/gaps.md` line 18 | `propstore/world/types.py:1257-1259` | Same as T2.8. Pignistic→Jøsang mislabel. |
| **Cluster F HIGH F3** | `cluster-F:73-78` | `propstore/praf/engine.py:82-111, 432` | `_defeat_summary_opinion(p)` invents `(b, d, u)` with no defensive clamp; can crash for `p` near 0/1; tags result `ProvenanceStatus.CALIBRATED` despite no calibration. Conflates Beta variance with subjective-logic `u`. |
| **Cluster F HIGH F4** | `cluster-F:79`; `propstore/praf/engine.py:309-314` | `from_probability(confidence, 1, a)` | Hard-coded `n=1` shifts confidence-0.5 stance to expectation 0.6 (W=2 prior dominates). |
| **Cluster F HIGH F12** | `cluster-F:114-120`; `propstore/praf/engine.py:329-409` | `enforce_coh()` 100-iter fixpoint exits silently on divergence; magic `n = 10.0` for dogmatic inputs (line 347). |
| **Cluster F MED F5** | `propstore/opinion.py:55-67` | `Opinion.allow_dogmatic` field decorative — `__post_init__` never gates on it. |
| **Cluster F MED F6** | `propstore/opinion.py:396-403` | `consensus()` left-fold for N>2 is order-sensitive at FP. After D-1 the corrected WBF supersedes `consensus` for N>2; document the deprecation path. |
| **Cluster F MED F8** | `propstore/opinion.py:121-130, 325-331` | `to_beta_evidence` rejects `u<_TOL`; `BetaEvidence.to_opinion` cannot produce `u=0`. Asymmetric. |
| **Cluster F MED F10** | `propstore/opinion.py:33, 514, 671` vs `:380-391` | `_BASE_RATE_CLAMP` applied in `wbf`/`ccf` but not `consensus_pair`. After D-1, the clamp goes away from `wbf` (Def 4 has no clamp); `ccf`'s clamp is reviewed for consistency. |

Out of scope (deferred): F2/F7/F11 — verified correct on re-derivation, not bugs. F16/F25/F17-F31 — WS-H. T2.6 — WS-G.

## Code references (verified by direct read 2026-04-26)

### opinion.py — operator catalog

Operators verified algebraically equivalent to cited paper: `~` (Jøsang Theorem 6 p.18), `conjunction` (Theorem 3 p.14), `disjunction` (Theorem 4 p.14-15), ordering (Def 10 p.9), `maximize_uncertainty` (Def 16 p.30), `consensus_pair` (Theorem 7 p.25), `discount` (Def 14 p.24), `expectation` (Def 6 p.5 — but this is **projected probability**, not pignistic BetP).

**Closed drift point**: `propstore/opinion.py` `wbf` now follows van der Heijden et al. 2018 Definition 4 (paper p.5) and reproduces Table I (paper p.8). The implementation uses `(1-u_i)Π_{j≠i}u_j` weighting, paper-defined uncertainty, and paper-defined confidence-weighted base rate. The earlier review's shared-`a` statement was rejected after rereading the paper page images.

**Three call sites for `wbf`** (verified `grep wbf propstore/`):
- `propstore/fragility_scoring.py:345` (`from propstore.opinion import wbf`) and `:359` (`return wbf(*mutable).expectation()`)
- `propstore/opinion.py:693` (`return wbf(*opinions)`, in `fuse(method="wbf")`)
- `propstore/opinion.py:698` (`return wbf(*opinions)`, in `fuse(method="auto")`)

**Other gaps**: `Opinion.__post_init__` (lines 57-67) does NOT enforce `allow_dogmatic` (F5). `to_beta_evidence` rejects `u < _TOL` while `BetaEvidence.to_opinion` cannot produce `u = 0` (F8). `_BASE_RATE_CLAMP` applied in current `wbf`/`ccf` but not `consensus_pair` (F10) — D-1 removes the clamp from `wbf`. `fuse(method="auto")` silently switches paper-of-record between WBF and CCF on dogmatic detection.

### types.py — decision criterion (verified 2026-04-26 against current source)

- `propstore/world/types.py:1230` — `criterion: str = "pignistic"` default in `apply_decision_criterion` signature.
- `propstore/world/types.py:1235-1236` — function docstring: *"Per Denoeux (2019, p.17-18): decision criteria determine how belief function uncertainty maps to actionable values at render time."*
- `propstore/world/types.py:1257-1259` — *the bug*: `if criterion == "pignistic":` then `value = opinion_b + opinion_a * opinion_u`, with comment *"Jøsang (2001, p.5, Def 6): E(ω) = b + a·u"*. The comment names Jøsang correctly but the *flag name* is wrong; D-2 swaps the formula and adds a new flag.
- `propstore/world/types.py:1191-1207` — `DecisionValueSource` enum carries `OPINION`, `CONFIDENCE_FALLBACK`, `NO_DATA`. The `CONFIDENCE_FALLBACK` rename is WS-N scope (D-3 deletes the shim outright). WS-D leaves the enum alone.
- `propstore/world/types.py:1275-1281` — old-data fallback path that returns `CONFIDENCE_FALLBACK` when opinion is missing. WS-N scope (D-3 deletes).

### Smets/Kennes 1994 (the actual pignistic source)

Pignistic transformation (Smets & Kennes 1994 §3; reproduced in Denoeux 2019 notes p.17-18): `BetP(ω) = Σ_{A: ω∈A} m(A) / |A|`. For a binomial frame `{x, ¬x}` with `m({x}) = b`, `m({¬x}) = d`, `m(Ω) = u`, this gives `BetP(x) = b + u/2`. Jøsang's projected probability `b + a·u` equals BetP **iff `a = 1/|Ω| = 1/2`**. Denoeux 2019 p.18: *"Pignistic Expected Utility ... extends the Laplace criterion to belief functions. The ONLY transformation satisfying linearity + MEU principle."* Jøsang's `b + a·u` is a generalized projected probability that *recovers* Laplace at `a = 1/k` but is not what Denoeux/Smets mean by "pignistic".

### CLI surface

`propstore/cli/world/reasoning.py:111-112` — current `--decision-criterion` Choice list is `["pignistic", "lower_bound", "upper_bound", "hurwicz"]`. D-2 expands to `["pignistic", "projected_probability", "lower_bound", "upper_bound", "hurwicz"]`. Default stays `"pignistic"`.

### CEL parser (T2.13)

`propstore/cel_checker.py:183` — `FLOAT_LIT` regex `\d+\.\d*|\.\d+` accepts `1.0`, `.5`, `3.` but rejects `1e3`, `1.5e-7`, `2E10`. CEL grammar requires `[eE][+-]?[0-9]+` as an optional exponent on both forms. Line 209 escape replacement handles only `\"`, `\'`, `\\` — `\n`, `\r`, `\t`, `\u`, `\x`, `\0` and CEL's octal escapes survive untouched. The "we parse a sufficient subset" disclaimer (line 8) is honest about scope — but `1e-9` is in every parameterization that uses scientific notation.

## First failing tests (write these first; they MUST fail before any production change)

The lead test is the parameterized operator-name-vs-formula audit. Per D-1 and D-2 it now asserts vdH Def 4 for `wbf` and Smets BetP for `pignistic`, both as primary truth.

1. **`tests/test_subjective_logic_operator_audit.py`** (new — *the* WS-D gate)

   Parameterized over a YAML manifest `tests/data/subjective_logic_canonical.yaml` listing every operator with: paper key, definition number, page, input vector, expected output vector, tolerance. The test calls `propstore.opinion.<operator>(*inputs)` (or `apply_decision_criterion(...)`) and asserts result equality to the canonical to ≤ 1e-6. Each row of the manifest is one paper-anchored worked example.

   Manifest entries must include at minimum:

   | Operator | Paper | Anchor | Inputs | Expected |
   |---|---|---|---|---|
   | `~` | Jøsang 2001 Theorem 6 | p.18 worked example | `(0.7, 0.1, 0.2, 0.5)` | `(0.1, 0.7, 0.2, 0.5)` |
   | `conjunction` | Jøsang 2001 Theorem 3 | p.14 worked example | `(0.7, 0.1, 0.2, 0.5)`, `(0.5, 0.3, 0.2, 0.4)` | computed |
   | `disjunction` | Jøsang 2001 Theorem 4 | p.14 worked example | same | computed |
   | `consensus_pair` | Jøsang 2001 Theorem 7 | p.25 worked example | two non-dogmatic ops | computed |
   | `discount` | Jøsang 2001 Def 14 | p.24 worked example | trust ⊗ source | computed |
   | `wbf` | vdH 2018 Def 4 | Table I (p.7) three-source row, **shared `a = 0.5`** | inputs from Table I | output from Table I (Def 4 form, NOT current code's output) |
   | `ccf` | vdH 2018 Def 5 | Table I `(0.629, 0.182, 0.189)` for inputs `(0.10, 0.30, 0.60), (0.40, 0.20, 0.40), (0.70, 0.10, 0.20)` | (0.629, 0.182, 0.189) |
   | `expectation` | Jøsang 2001 Def 6 | p.5 | `(0.5, 0.2, 0.3, 0.7)` | `0.5 + 0.7·0.3 = 0.71` |
   | `apply_decision_criterion("projected_probability")` | Jøsang Def 6 | p.5 | `(b=0.5, d=0.2, u=0.3, a=0.7)` | 0.71 |
   | `apply_decision_criterion("pignistic")` | Smets & Kennes 1994; Denoeux 2019 p.17-18 | binomial form `b + u/2` | `(b=0.5, d=0.2, u=0.3, a=0.7)` | `0.5 + 0.15 = 0.65` |
   | `apply_decision_criterion("lower_bound")` | Jøsang p.4 | Bel = b | same | 0.5 |
   | `apply_decision_criterion("upper_bound")` | Jøsang p.4 | Pl = 1 − d | same | 0.8 |
   | `apply_decision_criterion("hurwicz", α=0.5)` | Denoeux 2019 p.17 | (Bel + Pl) / 2 | same | 0.65 |

   **Must fail today**:
   - `wbf` row fails because the current numerator omits `1/u_i` (the documented 0.175 drift on Table I).
   - `pignistic` row at `a ≠ 0.5` fails because the implementation returns `b + a·u`, not `b + u/2`.
   - `projected_probability` row fails because the flag value does not exist yet.

2. **`tests/test_wbf_vs_van_der_heijden_2018_def_4.py`** (new)

   Three sub-tests anchored to vdH 2018 Def 4:
   - `test_wbf_requires_shared_base_rate`: assert `wbf(op_a05, op_a07)` raises (or warns and returns deterministically) when sources disagree on `a`. *Today silently confidence-weights and clamps.*
   - `test_wbf_table_I_three_source`: numerical reproduction of the paper's Table I row, **with shared `a`**.
   - `test_wbf_remark_2_all_dogmatic`: per-source `u = ε`, with the limit interpretation (paper p.5 Remark 2). Today the code averages `b/d/a` instead.

3. **`tests/test_pignistic_vs_smets_kennes_1994.py`** (new)

   - `test_pignistic_binomial_betP_formula`: for `(b, d, u, a)` with `a ∈ {0.1, 0.3, 0.5, 0.7, 0.9}`, assert `apply_decision_criterion(b, d, u, a, criterion="pignistic")` returns `b + u/2` *regardless of `a`* (Smets/Kennes BetP formula).
   - `test_projected_probability_uses_a`: assert `apply_decision_criterion(b, d, u, a, criterion="projected_probability")` returns `b + a·u` (Jøsang Def 6).
   - `test_pignistic_and_projected_disagree_off_uniform`: with `a = 0.7`, `u = 0.3`, both criteria must return *different* values, and the difference must equal `(a − 0.5)·u`.
   - `test_cli_choice_list_includes_projected_probability`: parse the click decorator at `propstore/cli/world/reasoning.py:111-112` (or invoke `--help`) and assert the Choice list contains both `pignistic` and `projected_probability`.

4. **`tests/test_defeat_summary_opinion_no_fabrication.py`** (new — F3)

   - `test_defeat_summary_uses_vacuous_for_uncalibrated`: assert that `_defeat_summary_opinion(p)` for an uncalibrated `p` returns `Opinion.vacuous(a=p, provenance=…)` with `ProvenanceStatus.STATED` (or some non-`CALIBRATED` status), NOT a manufactured `(b, d, u)` triple with `CALIBRATED` provenance.
   - `test_defeat_summary_no_crash_at_boundary`: `_defeat_summary_opinion(0.999999)` and `_defeat_summary_opinion(1e-9)` MUST not raise.

5. **`tests/test_from_probability_n_one_round_trip.py`** (new — F4)

   - `test_p_relation_from_stance_round_trip_at_0_5`: assert that a stance with `confidence=0.5`, `base_rate=0.5` produces an opinion whose `expectation()` round-trips to ≤ 1e-6 of 0.5. *Today returns 0.6.*

6. **`tests/test_enforce_coh_diverges_loudly.py`** (new — F12)

   - PrAF with attack cycles such that the 100-iteration fixpoint cannot converge.
   - Assert `enforce_coh(praf)` raises a `COHDivergenceError` (or returns a typed `CohResult.Diverged`), not silently a partially-enforced framework.
   - `test_enforce_coh_no_magic_n`: assert that for dogmatic inputs the function does not silently substitute `n = 10.0`.

7. **`tests/test_opinion_allow_dogmatic_enforced.py`** (new — F5)

   - `test_construct_dogmatic_without_flag_raises`: `Opinion(0.5, 0.5, 0.0, 0.5)` MUST raise unless `allow_dogmatic=True`.
   - `test_to_beta_evidence_symmetric`: a dogmatic opinion constructable via `Opinion(..., allow_dogmatic=True)` MUST round-trip via `to_beta_evidence` → `to_opinion` (limit form), or both directions must reject symmetrically.

8. **`tests/test_consensus_clamp_consistency.py`** (new — F10)

   Property test (`@given` with `@pytest.mark.property`): for every two-source pair, assert that `consensus_pair` and the corrected `wbf` produce identical (within tolerance) `(b, d, u, a)` for non-dogmatic inputs. After D-1 the clamp is gone from `wbf`, so this property holds without any clamp-consistency carve-out.

9. **`tests/test_cel_float_exponent.py`** (new — T2.13)

   - `tokenize("1e3")` MUST return a single `FLOAT_LIT(1000.0)` token. *Today raises "Unexpected character".*
   - `tokenize("1.5e-7")`, `tokenize("2E10")`, `tokenize(".5e2")` — same.
   - `tokenize("1e")` (truncated) MUST raise a clear parse error.

10. **`tests/test_cel_string_escapes.py`** (new — T2.13)

    - `tokenize('"a\\nb"')` MUST produce the 3-char value `a\nb` (with newline).
    - `tokenize('"\\u00e9"')` MUST produce `é`.
    - `tokenize('"\\t"')`, `tokenize('"\\r"')`, `tokenize('"\\0"')` — assert per CEL spec.
    - `tokenize('"\\q"')` (illegal escape) MUST raise.

11. **`tests/test_workstream_d_done.py`** (new — gating sentinel)

    `xfail` until WS-D closes; flips to `pass` on the final commit.

## Production change sequence

Each step lands in its own commit with a message of the form `WS-D step N — <slug>`.

### Step 1 — Fix `opinion.wbf` to vdH 2018 Def 4 (D-1)

Implemented against the corrected paper reading: `propstore/opinion.py` computes WBF belief/disbelief with `(1-u_i)Π_{j≠i}u_j` terms, computes uncertainty from `Σ(1-u_i)Π_j u_j`, and computes base rate as `Σ a_i(1-u_i) / Σ(1-u_i)`. Dogmatic and all-vacuous cases follow Definition 4 p.5 / Remarks 2-3. `_BASE_RATE_CLAMP` is not used by WBF.

Acceptance: `tests/test_wbf_vs_van_der_heijden_2018_def_4.py`, `tests/test_consensus_clamp_consistency.py`, and the `wbf` row of `test_subjective_logic_operator_audit.py` are green. The full fragility suite passed; no committed `tests/data/fragility_*.yaml` fixtures were present to recompute.

### Step 2 — Fix `decision_criterion="pignistic"` to true Smets BetP and add `projected_probability` (D-2)

`propstore/world/types.py:1257-1259`: replace `value = opinion_b + opinion_a * opinion_u` with `value = opinion_b + opinion_u / 2.0`. Update the inline comment to `# Smets & Kennes 1994 §3; Denoeux 2019 p.17-18: BetP(x) = b + u/2 for binomial frame`.

Insert a new `elif criterion == "projected_probability":` branch before `elif criterion == "lower_bound":` with `value = opinion_b + opinion_a * opinion_u` and inline cite `# Jøsang 2001 Def 6 (p.5): E(ω) = b + a·u`.

Update the function docstring at `propstore/world/types.py:1235` to cite `Smets_Kennes_1994` for pignistic and `Josang_2001 Def 6` for projected_probability; keep `Denoeux_2019` as the criterion-survey reference at the docstring level.

`propstore/cli/world/reasoning.py:112`: extend the click `Choice` list to `["pignistic", "projected_probability", "lower_bound", "upper_bound", "hurwicz"]`. Update help text to disambiguate.

Per Q's "no old repos" rule: no aliasing. Update every test fixture and consumer in one pass — fixtures with `criterion="pignistic"` and intent "Jøsang formula" migrate to `criterion="projected_probability"`; fixtures with `criterion="pignistic"` and intent "true pignistic" stay on `pignistic` and have their expected values recomputed to `b + u/2`. Touch `docs/subjective-logic.md`, `docs/probabilistic-argumentation.md`, `CLAUDE.md`, every `tests/data/*.yaml` row.

The default `RenderPolicy.decision_criterion` stays `"pignistic"` (now meaning true pignistic).

Acceptance: `tests/test_pignistic_vs_smets_kennes_1994.py` turns green. `tests/test_subjective_logic_operator_audit.py` rows for `pignistic` and `projected_probability` turn green. Every existing pignistic-using test that asserts a numeric value either updates its expected (true pignistic) or migrates its flag to `projected_probability`.

### Step 3 — `_defeat_summary_opinion` honest-ignorance rewrite (F3)

Per `propstore/calibrate.py` "honest ignorance over fabricated confidence" docstring, replace the manufactured `(b, d, u)` triple in `praf/engine.py:82-111` with `Opinion.vacuous(a=p, provenance=...)`. The provenance status MUST NOT be `CALIBRATED` unless calibration actually happened. Update `summarize_defeat_relations` (line 412) to pass through opinion or vacuous, never fabricate.

Acceptance: `tests/test_defeat_summary_opinion_no_fabrication.py` turns green.

### Step 4 — `from_probability` `n=1` decision (F4)

Q's call between: (A) make `effective_sample_size` a stance-level field, defaulting to `None` → `Opinion.vacuous(a=base_rate)`; or (B) keep `n=1` but document that confidence=0.5 emits expectation 0.6 under W=2 prior, with a deviation-asserting test. Acceptance: `tests/test_from_probability_n_one_round_trip.py` turns green under the chosen path.

### Step 5 — `enforce_coh` divergence loudness (F12)

Replace the silent fall-through with a typed `CohResult` returned (or `COHDivergenceError` raised). Drop the magic `n = 10.0` for dogmatic inputs — either bisect on `expectation` directly without reconstructing through `from_probability`, or refuse to enforce on dogmatic-input PrAFs (Hunter & Thimm 2017 §4.3 doesn't define behavior for the `u=0` case).

Acceptance: `tests/test_enforce_coh_diverges_loudly.py` turns green.

### Step 6 — `Opinion.allow_dogmatic` becomes load-bearing (F5)

`__post_init__` raises if `u < _TOL` and not `allow_dogmatic`. Every legitimate dogmatic site (`dogmatic_true`/`dogmatic_false`, the corrected WBF dogmatic branch from Step 1, `_defeat_summary_opinion` post-Step-3) passes `allow_dogmatic=True` explicitly. F8 asymmetry closed by documenting (in `BetaEvidence.to_opinion` docstring) that the W=2 prior makes the bijection well-defined only for non-dogmatic.

Acceptance: `tests/test_opinion_allow_dogmatic_enforced.py` turns green.

### Step 7 — CEL float exponent + escape sequences (T2.13)

`propstore/cel_checker.py:183`: change `FLOAT_LIT` regex to `(?:\d+\.\d*|\.\d+|\d+)[eE][+-]?\d+|\d+\.\d*|\.\d+`. Order matters in the alternation — exponent forms must match first.

`propstore/cel_checker.py:209`: replace the three-replacement `replace` chain with a single `re.sub(r'\\(.)' , …)` callback that handles `\n \r \t \0 \\` and `\"` and `\'` and `\uXXXX` and `\xXX`. Reject unknown escapes per CEL spec (or fall through to literal-after-backslash with a warning, depending on Q's CEL stance — see WS-P).

Note: T2.13 is also in WS-P scope. WS-D closes it because WS-D is unblocked and ready; WS-P retains the broader CEL operational-semantics work.

Acceptance: `tests/test_cel_float_exponent.py` and `tests/test_cel_string_escapes.py` turn green.

### Step 8 — Close gaps and gate

- Update `docs/gaps.md`: remove the two HIGH items (pignistic mislabel, WBF/aCBF). Add a `# WS-D closed <sha>` line in the "Closed gaps" section.
- Flip `tests/test_workstream_d_done.py` from `xfail` to `pass`.
- Update this file's STATUS line from `OPEN` to `CLOSED <sha>`.
- Notify WS-F, WS-G, WS-H, WS-I, WS-J that operator semantics are now stable.

Acceptance: `tests/test_workstream_d_done.py` passes; gaps.md has new closed entries.

## Acceptance gates

Before declaring WS-D done, ALL must hold:

- [x] `uv run pyright propstore` — passes with 0 errors.
- [x] `uv run lint-imports` — passes with 4 kept contracts, 0 broken.
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-D tests/test_subjective_logic_operator_audit.py tests/test_wbf_vs_van_der_heijden_2018_def_4.py tests/test_pignistic_vs_smets_kennes_1994.py tests/test_defeat_summary_opinion_no_fabrication.py tests/test_from_probability_n_one_round_trip.py tests/test_enforce_coh_diverges_loudly.py tests/test_opinion_allow_dogmatic_enforced.py tests/test_consensus_clamp_consistency.py tests/test_cel_float_exponent.py tests/test_cel_string_escapes.py tests/test_workstream_d_done.py` — 71 passed, log `logs/test-runs/WS-D-20260428-043940.log`.
- [x] Full suite — 3147 passed, log `logs/test-runs/WS-D-full-rerun-20260428-044907.log`.
- [x] `tests/data/subjective_logic_canonical.yaml` checked in; implemented operators and every `decision_criterion` value, including `projected_probability`, have paper-anchored rows.
- [x] `propstore/world/types.py` cites Smets & Kennes 1994 journal p.202 for pignistic and Jøsang 2001 Definition 6 p.5 for projected probability.
- [x] `propstore/cli/world/reasoning.py` and `propstore/cli/worldline/__init__.py` Choice lists include `projected_probability`.
- [x] `propstore/opinion.py` WBF follows vdH 2018 Definition 4 p.5, does not apply `_BASE_RATE_CLAMP`, and uses the paper's confidence-weighted base rate.
- [x] `propstore/opinion.py` operator docstrings and tests carry paper/definition/page anchors for the closed surface.
- [x] `docs/gaps.md` — both HIGH WS-Z-types continuation rows are removed and recorded under Closed gaps.
- [x] Fragility scoring revalidated by full suite; no committed `tests/data/fragility_*.yaml` fixture corpus exists in this repo state.
- [x] Every test corpus row using `decision_criterion="pignistic"` was audited by the targeted and full-suite runs; Jøsang-formula consumers use `projected_probability`.
- [x] `reviews/2026-04-26-claude/workstreams/WS-D-math-naming.md` STATUS line is `CLOSED ea232e21`.

## Done means done

This workstream is done when every finding in the table at the top is closed, not when "most" are closed:

- T2.7 (WBF/aCBF) — `wbf` matches vdH 2018 Def 4 numerator, denominator, and confidence-weighted base-rate equation; the dogmatic branch is the p.5 limit case; vdH Table I row in audit YAML passes; `_BASE_RATE_CLAMP` removed from `wbf`. Fragility-scoring tests pass and no committed fragility fixture corpus exists to recompute.
- T2.8 (pignistic mislabel) — `decision_criterion="pignistic"` returns `b + u/2` per Smets & Kennes 1994; `decision_criterion="projected_probability"` returns `b + a·u` per Jøsang Def 6; the CLI Choice list at `cli/world/reasoning.py:112` includes both; every test corpus exercising the flag has been re-validated; the function docstring cites `Smets_Kennes_1994` for pignistic.
- T2.13 (CEL float exponent + escapes) — token regex accepts `[eE][+-]?\d+`; escape replacement handles the standard CEL set; rejects unknown escapes.
- gaps.md HIGH F1 + F2 closed and removed from `docs/gaps.md`.
- Cluster F HIGH F3, F4, F5, F12 closed by tests above.
- Cluster F MED F6, F8, F10 closed (F8 by symmetric documentation; F10 vacated by D-1 removing the clamp from `wbf`; F6 by the corrected WBF being usable for N>2).
- The audit YAML covers every operator and every `decision_criterion` value (including `projected_probability`) with paper anchors.
- The gating sentinel test has flipped from xfail to pass.

If any one of those is not true, WS-D stays OPEN. No "we'll get to F8 later." Either it's in scope and closed, or it's explicitly removed from this WS in this file (and moved to a successor WS) before declaring done.

## Papers / specs referenced

All on disk under `papers/`. WS-D treats them as canonical.

- `papers/Josang_2001_LogicUncertainProbabilities/` (has notes.md) — foundational `(b, d, u, a)` algebra; Def 6/10/12/14/16, Theorems 3/4/6/7. Source for every binomial operator in `opinion.py` and for the `projected_probability` decision criterion.
- `papers/Josang_2016_SubjectiveLogic/` — book-length canonical catalog. Metadata-only on disk; Q's call whether to commission a paper-reader pass before WS-D closes. The audit relies on Jøsang_2001 + vdH 2018 + Smets_Kennes_1994 + Denoeux 2019, which together cover every operator currently in code and every decision criterion under D-2's flag space.
- `papers/vanderHeijden_2018_MultiSourceFusionOperationsSubjectiveLogic/notes.md` — Def 1-5, Theorem 1, Remarks 1-3. Source for the D-1 fix.
- `papers/Smets_Kennes_1994_TransferableBeliefModel/` — original BetP source. Metadata-only on disk; BetP formula reproduced in Denoeux 2019 notes p.17-18. Citation-of-record for D-2's `pignistic` flag.
- `papers/Smets_1991_TransferableBeliefModel/` — TBM precursor.
- `papers/Denoeux_2018_Decision-MakingBeliefFunctionsReview/notes.md` — review of decision criteria; pignistic/Hurwicz/OWA/E-admissibility equations. Stays cited at the criterion-survey level after D-2.
- `papers/Margoni_2024_SubjectiveLogicMetaAnalysis/`, `papers/Vasilakes_2025_SubjectiveLogicEncodings/`, `papers/Kaplan_2015_PartialObservableUpdateSubjectiveLogic/` — supplementary; Vasilakes_2025 notes confirm `b + a·u` is "Projected Probability" in the Jøsang lineage and not pignistic, which directly motivates D-2.
- `papers/Josang_2010_CumulativeAveragingFusionBeliefs/` — ⚠ misnamed directory (notes.md p.6 warns); PDF is the multiplication paper, not CBF/ABF. The paper that *corrects* CBF/ABF (vdH 2018) is on disk.
- (No paper for) Google CEL spec — WS-P prerequisite; WS-D adopts CPython `ast.literal_eval` escape rules as a temporary close, recorded in `notes/cel-escapes-pending-spec-2026-04-26.md`.

## Cross-stream notes

- WS-D is *parallel* to WS-A and WS-O-* — does not consume schema fidelity.
- WS-F (ASPIC bridge fidelity) consumes WS-D operator-name discipline because preference-comparator wiring uses Opinion ordering. Land WS-D before WS-F.
- WS-G (belief revision postulate coverage) overlaps on Spohn-vs-Opinion representation discipline. Land WS-D first so WS-G's Opinion-using assertions are testable.
- WS-H (probabilistic argumentation) consumes WS-D heavily — `enforce_coh`, `_defeat_summary_opinion`, `from_probability` are all in PrAF's hot path. WS-D is a hard prerequisite for WS-H.
- WS-I (ATMS / world correctness) consumes the CEL parser fixes (T2.13) for support semantics. WS-D's CEL closure unblocks WS-I.
- WS-J (worldline / causal / hashing) integrates Opinion into hash-stable serialization. Names matter for hash stability — D-2's new flag value `projected_probability` enters the canonical form. Land WS-D first.
- WS-N (architecture, D-3/D-4/D-5) deletes the `CONFIDENCE_FALLBACK` shim entirely; WS-D leaves the enum alone but lives downstream of D-3 in the ordering plan. Coordinate so the `apply_decision_criterion` rewrite in D-2 doesn't reintroduce a fallback path D-3 just removed.
- WS-P (CEL operational semantics) covers the broader CEL grammar work; WS-D closes T2.13 specifically because they're proximate to the operator-naming audit and a WS-P delay would block WS-I.

## What this WS does NOT do

- Does NOT implement multinomial opinions, hyper-opinions, deduction/abduction (Jøsang 2008), or partial-observable update (Kaplan 2015). The multinomial form of `pignistic` (per Smets/Kennes general formula `Σ_{A∋ω} m(A)/|A|`) is reserved under the same flag value but raises until multinomial Opinion lands.
- Does NOT add new fusion operators (BCF, CBF, ABF). WS-D fixes WBF and audits CCF; the other three are coverage gaps for WS-H.
- Does NOT add Brier score / log-loss / Sobol global sensitivity (F16, F25) — WS-H scope.
- Does NOT change `apply_decision_criterion` return type or the `DecisionValueSource` enum. The `CONFIDENCE_FALLBACK` shim deletion is WS-N scope (D-3).
- Does NOT touch `propstore/calibrate.py` magic constants (F28). Future calibration audit.
- Does NOT close `gaps.md` LOW items unrelated to operator naming/correctness.
