# WS-H: Probabilistic argumentation correctness

**Status**: CLOSED dd69f2bd
**Depends on**: WS-D (subjective-logic operator naming and `from_probability` semantics), **WS-O-gun** (D-18 `EnumerationExceeded` budget wired before any propstore caller relies on argument enumeration), **WS-O-arg-gradual** (upstream DF-QuAD fix per Codex #17 — the math contract is decided in that stream's paper-resolution step; WS-H consumes it)
**Blocks**: nothing downstream — but every "probability of acceptance" surface in the codebase is wrong until this lands.
**Owner**: Codex implementation owner + human reviewer required

---

## Why this workstream exists

PrAF and probabilistic gradual argumentation are propstore's claim-strength surfaces. Each currently lies:

- `praf-paper-td-complete` runs ordinary Dung acceptance; the Popescu-Wallner extension-probability path is reachable in the dep package but propstore never routes there. The enum value is decorative.
- Uncalibrated arguments are deleted from the framework before the kernel runs; the answer is reported against a smaller graph as if it were the answer for the original.
- `confidence=1.0` becomes dogmatic Opinion (u=0). `confidence=0.5` becomes expectation 0.6 because `from_probability(.., 1, ..)` lets the W=2 prior dominate.
- DF-QuAD over QBAFs has supporters edge-weighted and attackers raw — a code drift with no paper basis on either side. The fix must come from the cited paper, not from a symmetry intuition.
- `_defeat_summary_opinion` invents (b, d, u) from a scalar probability and stamps `CALIBRATED`.
- `enforce_coh` runs a silent 100-iteration cap and uses `n=10.0` as a magic dogmatic-input fallback.
- Sensitivity is local OAT only; Ballester-Ripoll 2024 is cited but ignored.
- Calibration ships uniform-bin ECE only — no Brier, no log-loss, no MCE, despite Guo 2017 defining all of these on the same page the module cites.

## Review findings covered

This workstream closes ALL of the following. "Done means done" — every finding listed is gone from `gaps.md` and has a green test gating it.

| Finding | Source | Citation | Description |
|---|---|---|---|
| **Codex #14** | `reviews/2026-04-26-codex/workstreams/ws-06-argumentation-belief-and-probability.md` | `propstore/world/types.py:623`, `propstore/world/resolution.py:687-691`, `propstore/app/world_reasoning.py:235-244` | `praf-paper-td-complete` is advertised as a semantics but the resolver hard-codes `query_kind="argument_acceptance"` and uses the policy-default `strategy` (typically `"auto"`), so the Popescu-Wallner paper-TD extension-probability path is never reached. |
| **Codex #15** | ws-06 | `propstore/core/analyzers.py:660-715` | `build_praf_from_shared_input` deletes uncalibrated arguments and incident relations from the kernel framework and reports acceptance over the surviving subgraph. Honest-ignorance contract requires an explicit vacuous representation or a hard boundary error. |
| **Codex #16** | ws-06 | `propstore/praf/engine.py:291-314` | `p_relation_from_stance` converts raw `confidence=1.0` into `Opinion.dogmatic_true` (u=0) and intermediate confidences into `from_probability(confidence, 1, a)` — raw user confidence becomes either infinite evidence or prior-dominated bias. |
| **Codex #17** | `reviews/2026-04-26-claude/cluster-P-argumentation-pkg.md` and ws-06 | `argumentation/src/argumentation/probabilistic_dfquad.py:163-167` | Attackers contribute `strengths[a]`; supporters contribute `strengths[a] * supports[(a, arg)]`. Asymmetric edge-weighting under the same DF-QuAD policy. **Upstream fix lives in WS-O-arg-gradual.** |
| **Cluster F #3 / HIGH** | `reviews/2026-04-26-claude/cluster-F-probabilistic-subjective.md:73-77` | `propstore/praf/engine.py:82-111` | `_defeat_summary_opinion` invents Opinion mass from a scalar probability via a heuristic that conflates Beta variance with subjective-logic uncertainty, with no defensive clamp and a falsified `CALIBRATED` provenance. |
| **Cluster F #4 / HIGH** | cluster-F.md:79 | `propstore/praf/engine.py:309-314` | `from_probability(confidence, 1, a)` makes a stance with confidence=0.5 emerge as expectation 0.6 because the W=2 prior dominates n=1. Effective sample size must come from the data, not a hard-coded literal. |
| **Cluster F #12 / HIGH** | cluster-F.md:114-120 | `propstore/praf/engine.py:329-409` | `enforce_coh` runs a 100-iteration cap with no convergence detection (silent partial enforcement) and falls back to `n=10.0` for dogmatic inputs (magic number, no citation). |
| **Cluster F #14 / MED** | cluster-F.md:124 | `propstore/praf/engine.py:412-437` | `summarize_defeat_relations` builds opinions via the manufactured-uncertainty function and stamps them `CALIBRATED`. Same fabricated-evidence class as Codex #16. |
| **Cluster F #16 / HIGH** | cluster-F.md:147 | `propstore/sensitivity.py:260-286` | Pure local OAT via sympy `diff`; no Sobol indices, no Saltelli sampling, no variance decomposition. The docstring promises "which input most influences this output?" — OAT cannot answer that question for any function with interaction terms. |
| **Cluster F #25 / HIGH** | cluster-F.md:184 | `propstore/calibrate.py` | Brier score not implemented; log-loss not exposed as a metric; only uniform-bin ECE. Standard scoring rules and adaptive ECE are absent. |
| **Cluster F #15 / MED** | cluster-F.md:126 | `propstore/praf/engine.py:49-61` | `PropstorePrAF` is `frozen=True` but `__post_init__` re-binds `omitted_arguments` and `omitted_relations` to mutable dicts. Hashability and aliasing footgun. |

Adjacent finding kept in scope (cheaper here than later):

| Finding | Citation | Why included |
|---|---|---|
| Provenance lie in `summarize_defeat_relations` (Cluster F #14) | `propstore/praf/engine.py:84-87` | The same `_praf_provenance(ProvenanceStatus.CALIBRATED, "defeat_distribution_variance")` line is the upstream of every "calibrated" defeat record reaching consumers. Touching it here, once, instead of letting it leak into WS-J/WS-K. |

What this WS does NOT cover, and where it goes instead:

- `from_probability` operator semantics (W=2, base rate): **WS-D**. WS-H owns the consumer's choice of `n`, not the operator definition.
- WBF / CCF (vdH 2018, Cluster F #1, #2): **WS-D**.
- Multinomial / hyper-opinion / BCF / ABF / CBF: Tier 7.
- ASPIC contrariness (T2.1), ASPIC grounded conflict-free (T2.9): **WS-F**.
- Worldline merge-parent evidence: **WS-J**.
- DF-QuAD upstream math (Codex #17): **WS-O-arg-gradual**. WS-H pins the propstore-side consumer regression after the dep advances.
- `gunray.evaluate(max_arguments=...)` / `EnumerationExceeded` (D-18): **WS-O-gun**. WS-H consumes the result.

## Code references (verified by direct read on 2026-04-26)

- **Codex #14** — `propstore/world/types.py:623` declares `PRAF_PAPER_TD_COMPLETE`; `propstore/world/resolution.py:687-698` and `propstore/app/world_reasoning.py:235-244` hard-code `query_kind="argument_acceptance"` regardless of semantics. The dep supports the right path via `analyze_praf(..., strategy="paper_td", query_kind="extension_probability", ...)` (per `tests/test_argumentation_package_track_e.py:144-198`); resolution never reaches it.
- **Codex #15** — `propstore/core/analyzers.py:660-715` filters uncalibrated arguments into `omitted_arguments` and constructs `framework = ArgumentationFramework(arguments=active_args, ...)` from the surviving subset (`:711-715`). The kernel sees the smaller graph; the omitted dicts ride on the wrapper only.
- **Codex #16 + Cluster F #4** — `propstore/praf/engine.py:304-308` returns `Opinion.dogmatic_true(a)` for `confidence >= 1 − 1e-12`; `:309-314` calls `from_probability(confidence, 1, a, ...)` with literal `1` (W=2 prior dominates: confidence=0.5 → expectation 0.6).
- **Cluster F #3 / #14** — `propstore/praf/engine.py:82-111`: provenance stamped `CALIBRATED("defeat_distribution_variance")` (`:84-87`). Non-zero-variance branch (`:99-111`) computes `u = max_uncertainty · variance / 0.25`, `b = p − 0.5·u`, `d = 1 − b − u`, no pre-construct clamp, `a` hard-wired 0.5. `:412-437` propagates the false stamp into `ProbabilisticRelation` records.
- **Cluster F #12** — `propstore/praf/engine.py:344-347`: `evidence_n[arg] = W · (1/u − 1)` if `u > 1e-9` else `10.0`. `:350-367`: 100-iteration loop exits silently; no `COHNotConverged`. `:380-385`: violator rebuild reuses the magic.
- **Cluster F #15** — `propstore/praf/engine.py:38` `@dataclass(frozen=True)` with `:59-61` `object.__setattr__(self, "omitted_arguments", dict(...))`; fields typed `dict | None`, mutable after construction.
- **Cluster F #16** — `propstore/sensitivity.py:265-289` is sympy-`diff`-per-input local OAT; docstring at `:79` claims "which input most influences this output?" while the method cannot answer that for any function with interaction.
- **Cluster F #25** — `propstore/calibrate.py:473-510` is uniform-bin `expected_calibration_error` (`:492`); no Brier, no exposed log-loss (`nll` at `:82-88` is private to `TemperatureScaler.fit`), no adaptive ECE, no MCE, no reliability diagram.
- **Codex #17** (upstream — WS-O-arg-gradual owns) — `argumentation/src/argumentation/probabilistic_dfquad.py:163-167`: attackers contribute `strengths[a]`; supporters contribute `strengths[a] * supports[(a, arg)]`. Asymmetry leaks into both `dfquad_baf` and `dfquad_quad` (`:193-222`). WS-H does not pick the math; the propstore-side consumer test pins to WS-O-arg-gradual's "Paper contract resolved" formula.

## Argument-enumeration gating (Codex 1.13)

WS-H's praf engine consumes argument enumeration for any code path that returns or inspects argument sets. The gunray budget (D-18) is the upstream that raises `EnumerationExceeded` with a partial result when enumeration exceeds `max_arguments`. Until WS-O-gun ships and WS-M flips the default, the propstore consumer must NOT request argument-set return.

- WS-H tests that depend on argument-set return are `@pytest.mark.skip(reason="depends on WS-O-gun D-18")` until the WS-O-gun sentinel flips.
- Pre-WS-O-gun, WS-H tests assume `return_arguments=False` (the safe default) and exercise opinion-only paths. The opinion-only contract has no enumeration risk.
- Post-WS-O-gun + post-WS-M flip, the gated WS-H tests un-skip in a follow-up commit and must turn green against the same code under test.
- WS-H's "done" gate requires the gated tests to **exist and be correctly skip-marked**, not to be green at WS-H close. WS-H stays CLOSED through the un-skip flip.

## First failing tests (write these first; they MUST fail before any production change)

Each test name encodes the finding ID for `gaps.md` consistency. Each test docstring cites the cluster-F line or the Codex finding number.

1. **`tests/test_praf_paper_td_complete_routing.py`** (Codex #14) — drive `_resolve_praf` (or `world_reasoning`) with `semantics="praf-paper-td-complete"`. Assert `metadata["strategy_used"] == "paper_td"`, `metadata["query_kind"] == "extension_probability"`, `metadata["extension_probability"] is not None`. Pattern from `tests/test_argumentation_package_track_e.py:144-198`. Fails today: `query_kind` hard-coded `"argument_acceptance"`, so `extension_probability is None`. **Opinion-only path: not gated on WS-O-gun.**

2. **`tests/test_praf_uncalibrated_explicit.py`** (Codex #15) — three-argument graph, one with no calibration columns. Call `build_praf_from_shared_input`. Assert kernel `framework.arguments` includes the uncalibrated arg AND `analyze_praf` either returns the arg as `Opinion.vacuous(...)` or raises `PrAFCalibrationError` with the missing field list. Fails today: silent topology shrink at `analyzers.py:711-715`. **Opinion-only path: not gated.**

3. **`tests/test_praf_raw_confidence_not_dogmatic.py`** (Codex #16, Cluster F #4) — stance with `confidence=1.0`: result is not dogmatic OR raises `RawConfidenceNotEvidence`. Stance with `confidence=0.5, a=0.5`: expectation equals 0.5 OR returns `NoCalibration("missing_evidence_count", ...)`. Fails today on both: `engine.py:304` returns `dogmatic_true`, `:309-314` returns expectation 0.6. **Opinion-only path: not gated.**

4. **`tests/test_defeat_summary_opinion_honest.py`** (Cluster F #3, #14) — Hypothesis property over `p ∈ [0, 1]`. Assert `_defeat_summary_opinion(p)` either returns `Opinion.vacuous(a=p)` OR returns an Opinion whose provenance is **never** `CALIBRATED` and whose b, d, u are clamped into `[0, 1]`. Fails today: stamped `CALIBRATED("defeat_distribution_variance")` regardless. **Opinion-only path: not gated.**

5. **`tests/test_enforce_coh_convergence.py`** (Cluster F #12) — divergent constraint cycle (mutual attack, both expectations 0.9). Assert `enforce_coh` returns `EnforceCohResult(converged=False, ...)` or raises `COHNotConverged`. All-dogmatic input: assert no silent `n=10.0` fallback. Fails today. **Opinion-only path: not gated.**

6. **`tests/test_dfquad_attack_support_per_paper_contract.py`** (Codex #17, upstream) — propstore-side regression test, lives in `tests/`, assertions written **only after** WS-O-arg-gradual publishes its "Paper contract resolved" subsection. The test asserts the four-case formula from that subsection verbatim — not symmetry, not "both edge-weighted." If the paper says edge weights are absent (raw `c(...)` combinative function), the test asserts that contract; if a subsequent paper introduces edge weights with a specific form, the test asserts that form. **The test body is NOT writable until WS-O-arg-gradual's paper-contract step lands.** Until then the file exists with `pytest.fail("blocked on WS-O-arg-gradual paper-contract resolution")` and is on the WS-O-arg-gradual blocked-on list. Pinned to the propstore-pin advance, not to WS-O-arg-gradual's upstream merge alone.

7. **`tests/test_sensitivity_global_method_or_honest_naming.py`** (Cluster F #16) — parameterization `f(x1, x2) = x1·x2` at `(1, 1)`. Assert EITHER `SensitivityResult` has a `method="local_oat"` field AND a sibling `analyze_global_sensitivity` returns Sobol indices, OR the existing analyzer returns `method="sobol"` matching analytic indices. Fails today: no `method` field, no global analyzer.

8. **`tests/test_calibrate_brier_and_log_loss.py`** (Cluster F #25) — three datasets (perfect random / confident-correct / confident-wrong). Assert `brier_score` and `log_loss` exist and match analytic values within 1e-6. Fails today: neither function exists.

9. **`tests/test_praf_frozen_immutable.py`** (Cluster F #15) — construct `PropstorePrAF`; assert `omitted_arguments.__setitem__` raises (e.g., `MappingProxyType`). Fails today: mutable `dict`.

10. **`tests/test_praf_argument_enumeration_budget.py`** (Codex 1.13 / D-18 consumer) — gated test. Marked `@pytest.mark.skip(reason="depends on WS-O-gun D-18")` until WS-O-gun closes. Body: drive the praf engine with `return_arguments=True` against an argumentation graph engineered to exceed `max_arguments`. Assert the propstore consumer surfaces a typed budget-exhaustion result (e.g., `ResultStatus.BUDGET_EXCEEDED` with `partial_arguments` populated) and never silently truncates or fabricates. Cross-reference: `propstore/grounding/grounder.py` is the canonical surface for `BUDGET_EXCEEDED` per D-18; the praf consumer mirrors its discipline.

11. **`tests/test_workstream_h_done.py`** — gating sentinel; `xfail` until WS-H closes. The sentinel asserts the non-gated WS-H tests are green and the gated argument-enumeration test exists, is correctly skip-marked, and references the WS-O-gun sentinel.

## Production change sequence

Each step lands as one or more commits with messages of the form `WS-H step N — <slug>`.

### Step 1 — Route paper-TD complete (Codex #14)
- `propstore/world/resolution.py:_resolve_praf`: when `normalized_semantics == PRAF_PAPER_TD_COMPLETE`, set `strategy="paper_td"`, `semantics="complete"`, `query_kind="extension_probability"`, `inference_mode=None`, `queried_set=target_ids`.
- Mirror the routing in `propstore/app/world_reasoning.py`.
- Per Q's no-shim rule: either the semantics value means what its name says, or it is removed from the enum entirely. No backward-compatible double meaning.
- Acceptance: `test_praf_paper_td_complete_routing.py` turns green.

### Step 2 — Represent uncalibrated arguments as ignorance (Codex #15)
- `propstore/core/analyzers.py:build_praf_from_shared_input`: keep `framework.arguments` equal to the input set. For each argument without calibration, install `Opinion.vacuous(a=base_rate or 0.5, provenance=ProvenanceStatus.VACUOUS)` AND record the omission in `omitted_arguments`.
- Same for relations: include with vacuous edge opinion, OR raise `PrAFCalibrationError` driven by `policy.uncalibrated_relations = "vacuous" | "reject"`.
- If `compute_probabilistic_acceptance` cannot accept vacuous-argument framings, escalate to WS-O-arg — do not paper over.
- Acceptance: `test_praf_uncalibrated_explicit.py` turns green.

### Step 3 — Stop fabricating evidence from raw confidence (Codex #16, Cluster F #4)
- `propstore/praf/engine.py:p_relation_from_stance`:
  - Remove the `confidence >= 1 − 1e-12 → dogmatic_true` path; return `NoCalibration("raw_confidence_not_evidence", missing_fields=("effective_sample_size", ...))` instead.
  - Remove the `from_probability(confidence, 1, a)` path; read `effective_sample_size` (or `sample_size`) from the stance row; if absent, return `NoCalibration`.
- Coordinate with WS-A for any schema column addition.
- Acceptance: `test_praf_raw_confidence_not_dogmatic.py` turns green.

### Step 4 — Honest `_defeat_summary_opinion` (Cluster F #3, #14)
- Pick one contract:
  - (a) Return `Opinion.vacuous(a=p)`; downstream computes `expectation = p`. A scalar p has no information about (b, d, u) independently.
  - (b) Require an explicit evidence count `n` and return `from_probability(p, n, a)`; provenance `CALIBRATED` only when `n` came from data.
- Either way: `CALIBRATED` is never produced from a scalar probability alone. `summarize_defeat_relations` follows the chosen contract.
- Acceptance: `test_defeat_summary_opinion_honest.py` turns green.

### Step 5 — Convergence-aware `enforce_coh` (Cluster F #12)
- Replace the silent loop with a typed `EnforceCohResult(praf, converged, iterations, max_violation)`. On non-convergence, raise `COHNotConverged` by default; opt-in flag for soft return.
- Replace the `n=10.0` magic: either reject dogmatic inputs explicitly or expose a documented `dogmatic_pseudo_n` parameter with citation. No magic literal in the body.
- Acceptance: `test_enforce_coh_convergence.py` turns green.

### Step 6 — DF-QuAD propstore-side pin (Codex #17, upstream owned by WS-O-arg-gradual)
- WS-H does NOT pick the DF-QuAD math contract. The paper contract is resolved upstream in WS-O-arg-gradual's "Paper contract resolved" subsection (the per-paper formula citation, with page/equation reference, that fixes whether edge weights apply at all and, if so, how).
- Once WS-O-arg-gradual ships and the propstore pin to `argumentation` advances past the upstream fix, WS-H writes the body of `tests/test_dfquad_attack_support_per_paper_contract.py` to assert the formula verbatim from the upstream "Paper contract resolved" subsection. Reading the formula from the paper directly (rather than inferring it from a "symmetry intuition") is the entire point of Codex 2.7.
- Until then the file holds `pytest.fail("blocked on WS-O-arg-gradual paper-contract resolution")` and the WS-H sentinel acknowledges it as upstream-blocked.
- Cross-link: WS-O-arg-gradual lists WS-H as the propstore consumer that will pin. WS-H lists WS-O-arg-gradual as the upstream owner.

### Step 7 — Sensitivity: honest naming + global method (Cluster F #16)
- Add `method: Literal["local_oat", "sobol_first_order", "sobol_total"]` to `SensitivityResult`; default existing output to `"local_oat"`.
- Implement `analyze_global_sensitivity(world, concept_id, bound, *, n_samples=1024, method="sobol_total")` — SALib or hand-rolled Saltelli; cite Saltelli 2008 / Ballester-Ripoll 2024 inline.
- Replace the "which input most influences" docstring claim with a precise local-OAT contract.
- Acceptance: `test_sensitivity_global_method_or_honest_naming.py` turns green.

### Step 8 — Brier + log-loss (Cluster F #25)
- `calibrate.brier_score(confidences, correct)` = `mean((conf − int(correct))^2)`.
- `calibrate.log_loss(confidences, correct)` = `−mean(correct·log(conf) + (1−correct)·log(1−conf))` with epsilon guard.
- Optional cheap add: `expected_calibration_error(..., bin_strategy="uniform" | "adaptive")` per Naeini 2015.
- Cite Guo 2017 inline at each definition.
- Acceptance: `test_calibrate_brier_and_log_loss.py` turns green.

### Step 9 — Actually-frozen `PropstorePrAF` (Cluster F #15)
- Replace `dict` typing on `omitted_arguments`/`omitted_relations` with `Mapping[...]` stored via `MappingProxyType`.
- Acceptance: `test_praf_frozen_immutable.py` turns green.

### Step 10 — Argument-enumeration consumer wiring (Codex 1.13 / D-18)
- Mirror gunray's `BUDGET_EXCEEDED` discipline at the praf-engine boundary: when an upstream call signals partial enumeration via `EnumerationExceeded`, the praf consumer surfaces `ResultStatus.BUDGET_EXCEEDED` with `partial_arguments` populated. No silent truncation; no fabrication of "complete" sets from partial input.
- The wiring is implementable independent of WS-O-gun close — the consumer can catch `EnumerationExceeded` from any call site that may eventually raise it. The corresponding test (`test_praf_argument_enumeration_budget.py`) stays `skip` until WS-O-gun lands and the gunray callsite actually raises.
- Acceptance: skipped test exists, references WS-O-gun's sentinel, and flips to green in a follow-up commit after WS-O-gun + WS-M flip the default.

### Step 11 — Close gaps and gate
- Update `docs/gaps.md`: remove the entries for Codex #14, #15, #16 and the Cluster F HIGH items in this WS's table. Add a `# WS-H closed <sha>` line in the "Closed gaps" section. Codex #17 row stays open in `gaps.md` until WS-O-arg-gradual closes; cross-link WS-H's deferral.
- Flip `tests/test_workstream_h_done.py` from `xfail` to `pass`.
- Update this file's STATUS line to `CLOSED <sha>`.

## Acceptance gates

Before declaring WS-H done, ALL must hold:

- [x] `uv run pyright propstore` — passes with 0 errors.
- [x] `uv run lint-imports` — passes (this WS does not change layered contracts; if it does, coordinate with WS-N).
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-H tests/test_praf_paper_td_complete_routing.py tests/test_praf_uncalibrated_explicit.py tests/test_praf_raw_confidence_not_dogmatic.py tests/test_defeat_summary_opinion_honest.py tests/test_enforce_coh_convergence.py tests/test_sensitivity_global_method_or_honest_naming.py tests/test_calibrate_brier_and_log_loss.py tests/test_praf_frozen_immutable.py tests/test_praf_argument_enumeration_budget.py tests/test_workstream_h_done.py` — all green or correctly `skip`-marked per the gating discipline.
- [x] `tests/test_dfquad_attack_support_per_paper_contract.py` exists, holds `pytest.fail("blocked on WS-O-arg-gradual paper-contract resolution")` until that stream's contract subsection lands, and is cross-referenced from WS-O-arg-gradual.
- [x] `tests/test_praf_argument_enumeration_budget.py` exists, is `skip`-marked with reason naming D-18 / WS-O-gun, and is referenced by `test_workstream_h_done.py` so WS-O-gun close is observable from the WS-H sentinel.
- [x] Full propstore suite `powershell -File scripts/run_logged_pytest.ps1` — no NEW failures vs the baseline log.
- [x] `propstore/praf/engine.py:_defeat_summary_opinion` no longer stamps `CALIBRATED` from a scalar.
- [x] `propstore/praf/engine.py:p_relation_from_stance` no longer contains the literal `from_probability(..., 1, ...)`.
- [x] `propstore/world/resolution.py:_resolve_praf` and `propstore/app/world_reasoning.py` route `praf-paper-td-complete` to `strategy="paper_td"`, `query_kind="extension_probability"`.
- [x] `propstore/sensitivity.py:SensitivityResult` has an explicit `method` field.
- [x] `docs/gaps.md` has no open rows for the findings owned by WS-H. Codex #17 row is annotated as upstream-blocked on WS-O-arg-gradual.
- [x] STATUS line of this workstream file reads `CLOSED <sha>`.

## Done means done

WS-H is done when **every finding owned by this WS is closed**, and the upstream-blocked findings have correctly-gated propstore-side test scaffolding ready to flip when their upstream close. Specifically:

- Codex #14, #15, #16 each have a corresponding green test in CI.
- Codex #17 has a green test in the upstream `argumentation` package's own suite (owned by WS-O-arg-gradual) AND a propstore-side regression file that holds `pytest.fail` until WS-O-arg-gradual's paper-contract subsection lands; flipping that file to a paper-faithful assertion is a follow-up commit, not a WS-H gate.
- D-18 / Codex 1.13: the propstore-side argument-enumeration consumer test exists, is correctly skip-marked on WS-O-gun, and surfaces the budget-exhaustion result type when un-skipped.
- Cluster F #3, #4, #12, #14, #15, #16, #25 each have a corresponding green test in CI.
- `gaps.md` is updated.
- `tests/test_workstream_h_done.py` has flipped from xfail to pass.

If any one of those is not true, WS-H stays OPEN. No "we'll get to Brier later" — either Brier+log-loss is in scope and closed, or it is explicitly removed from this WS in this file (and moved to a successor) before declaring done.

## Papers / specs referenced

Each is read before the relevant production change; cited inline in test docstring and code comment.

- **Hunter & Thimm 2017** (`papers/Hunter_2017_ProbabilisticReasoningAbstractArgumentation/`) — COH postulate (p.9), self-attack bound. Step 5.
- **Hunter 2021** (`papers/Hunter_2021_ProbabilisticArgumentationSurvey/`) — constellation/epistemic/labelling taxonomy; argument-acceptance vs extension-probability query distinction. Step 1.
- **Li et al. 2011** (`papers/Li_2011_ProbabilisticArgumentationFrameworks/`) — constellation semantics, MC sampling; already cited in `_resolve_praf` docstring.
- **Popescu & Wallner 2024** (three variants in `papers/Popescu_2024_*/`) — paper TD complete; the algorithm `strategy="paper_td"` actually invokes. Step 1.
- **Potyka 2019** (`papers/Potyka_2019_PolynomialTimeEpistemicProbabilistic/`) — polynomial-time epistemic fragments; target for a successor WS that replaces the `enforce_coh` 100-iteration loop.
- **Sensoy et al. 2018** (`papers/Sensoy_2018_EvidentialDeepLearningQuantify/`) — Dirichlet evidence; bandwidth choice in `CorpusCalibrator` reconciliation deferred.
- **Saltelli 2008** (`papers/Saltelli_2008_GlobalSensitivityAnalysisPrimer/`) — Sobol indices, Saltelli sampling. Step 7.
- **Coupé et al. 2002** (`papers/Coupé_2002_PropertiesSensitivityAnalysisBayesian/`) — Prop 4.1 linear-fractional sensitivity, closed-form alternative to symbolic diff. Optional in Step 7.
- **Guo et al. 2017** (`papers/Guo_2017_CalibrationModernNeuralNetworks/`) — temperature scaling, ECE, Brier, reliability diagrams. Step 8.
- **Rago et al. 2016** (`papers/Rago_2016_DiscontinuityFreeQuAD/notes.md`, Definition 1, p.2) — DF-QuAD `F^*(v_0, v_a, v_s)` formula and the noisy-OR combinative `c(v_1,...,v_n) = 1 − Π(1 − v_i)`. Read by **WS-O-arg-gradual** when resolving the paper contract; WS-H consumes the result.
- **Rago et al. 2016** (`papers/Rago_2016_AdaptingDFQuADBipolarArgumentation/notes.md`, Defs 2-3, p.2-3) — BAF adaptation without base scores; `SF(a) = 0.5 + 0.5·(Π(1−s_i) − Π(1−a_j))` closed form. Same role: WS-O-arg-gradual resolves; WS-H consumes.
- **Freedman et al. 2025** — DF-QuAD over QBAFs; if this is the paper that actually licenses edge weights, WS-O-arg-gradual cites it in its "Paper contract resolved" subsection and the WS-H consumer test pins to its formula.

## Cross-stream notes

- **WS-D**: owns the SL operator semantics (`from_probability`, `wbf`, `consensus_pair`). WS-H takes them as given and fixes consumers. Coordinate Cluster F #4 via shared `tests/test_subjective_logic_consumer_contract.py`.
- **WS-O-arg-gradual**: owns the DF-QuAD math fix (Codex #17, Step 6). Its first deliverable is the "Paper contract resolved" subsection with verbatim formula + page/equation cite. WS-H pins to it.
- **WS-O-gun**: owns D-18 `EnumerationExceeded`. WS-H consumes; the gated test flips after WS-O-gun's sentinel.
- **WS-M**: owns the `return_arguments=True` default flip (Codex 1.13). The gated WS-H test un-skips after WS-O-gun + WS-M close.
- **WS-A**: gates new stance columns. If WS-A is open when Step 3 lands, Step 3 surfaces missing fields as `NoCalibration("missing_evidence_count", ...)`.
- **WS-F / WS-J / WS-N**: no overlap with WS-H scope.

## What this WS does NOT do

- Does NOT pick the DF-QuAD math contract — **WS-O-arg-gradual**'s "Paper contract resolved" deliverable.
- Does NOT implement the gunray budget — **WS-O-gun** (D-18).
- Does NOT flip the `return_arguments` default — **WS-M** (Codex 1.13).
- Does NOT fix `wbf()` / `consensus_pair()` (vdH 2018) — **WS-D**.
- Does NOT add multinomial / hyper-opinion / BCF / ABF / CBF, maximum-entropy probability (Thimm 2012), Riveret labelling PrAF — Tier 7.
- Does NOT add Pearl/Halpern causal sensitivity — Tier 6 research spike.
- Does NOT touch `aspic_bridge/translate.py` — **WS-F**.
- Does NOT add reliability-diagram rendering or a `b + d + u = 1` SQLite CHECK constraint — UI / WS-A respectively.
