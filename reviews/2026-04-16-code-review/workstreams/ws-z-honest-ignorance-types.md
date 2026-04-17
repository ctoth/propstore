# Workstream Z-types — Honest-Ignorance Type System

Date: 2026-04-16
Status: active 2026-04-17; solver-result and UNKNOWN propagation slice in progress
Depends on: `disciplines.md`, `judgment-rubric.md`. Full payoff requires WS-A phase 1 (provenance type) but partial work can land in parallel.
Blocks: WS-C phase C-5 (consumes `ConflictClass.UNKNOWN`)
Review context: `../axis-1-principle-adherence.md` (Findings 2.1, 2.2, 2.4, 2.5, 2.6 + Structural S1-S3), `../axis-5-silent-failures.md` (categories 1, 2, 5, 6), `../axis-3e-reasoning-infra.md` (CRIT findings on Z3 collapse and timeouts), `../SYNTHESIS.md` patterns A and B

## Progress log

- 2026-04-17: Phase Z-types-1/Z-types-2 solver-unknown slice started with red tests for the missing `SolverResult` sum type and `ConflictClass.UNKNOWN` propagation (`logs\test-runs\ztypes-solver-red-20260417-104956.log`). Added timeout-aware `SolverSat | SolverUnsat | SolverUnknown`, made `Z3ConditionSolver` expose result-returning checks, routed condition classification and cross-class parameter conflicts through explicit pattern matching, added `ConflictClass.UNKNOWN`, made repository merge classify unknowns as ignorance rather than attacks, and moved `dung_z3` extension enumeration under the same timeout/unknown discipline. Verification passed: focused unknown/condition suite (`8 passed`, `logs\test-runs\ztypes-solver-green-2-20260417-105202.log`), Z3 condition integration suite (`55 passed`, `logs\test-runs\ztypes-solver-z3-20260417-105314.log`), Dung Z3 suite (`24 passed`, `logs\test-runs\ztypes-dung-z3-20260417-105332.log`), conflict/parameter/merge suite (`72 passed`, `logs\test-runs\ztypes-solver-conflict-merge-2-20260417-105448.log`), direct `solver.check()` grep gate clean outside `propstore.z3_conditions.solver_result_from_z3`, and targeted Pyright over touched solver/conflict files (`0 errors`).
- 2026-04-17: Phase Z-types-3/Z-types-4 category-prior slice completed. Added provenance-aware opinion factory parameters and `Opinion.with_provenance`, introduced `CategoryPrior`, `CategoryPriorRegistry`, and `CalibrationSource`, removed `_DEFAULT_BASE_RATES`, and made uncalibrated categorical opinions use vacuous `a=0.5` unless an explicit provenance-bearing prior is supplied. Red tests captured the missing prior type (`logs\test-runs\ztypes-category-red-20260417-105724.log`). Verification passed: category/calibration/relate opinion suite (`57 passed`, `logs\test-runs\ztypes-category-green-2-20260417-105905.log`), `_DEFAULT_BASE_RATES` grep gate clean across `propstore` and `tests`, and targeted Pyright over `propstore/calibrate.py propstore/opinion.py` (`0 errors`).
- 2026-04-17: Phase Z-types-5 PrAF calibration sentinel slice completed for `praf/engine.py` and shared PrAF construction. Red tests captured that bare claims, sample-size-only claims, bare stances, and zero-confidence stance rows were still becoming dogmatic probabilities (`logs\test-runs\ztypes-praf-red-20260417-110304.log`). Added `NoCalibration`, made `p_arg_from_claim` and `p_relation_from_stance` return `Opinion | NoCalibration`, attached provenance to PrAF-derived opinions, made `build_praf_from_shared_input` omit uncalibrated arguments/relations and expose omission records on `ProbabilisticAF`, removed the PrAF "backward compat" dogmatic fallback, and updated integration fixtures to provide explicit P_A calibration where they actually test PrAF probabilities. Verification passed: focused PrAF/source trust suite (`58 passed`, `logs\test-runs\ztypes-praf-green-20260417-110527.log`), expanded PrAF/analyzer suite (`84 passed`, `logs\test-runs\ztypes-praf-analyzers-2-20260417-110937.log`), targeted Pyright over touched production PrAF/analyzer files (`0 errors`), and grep gate clean for `Opinion.dogmatic_true()` in `propstore/praf` and `propstore/core`.
- 2026-04-17: Phase Z-types-5 fragility slice completed. Red tests captured that `fragility_scoring.imps_rev` accepted no probabilistic inputs and fabricated dogmatic PrAF opinions (`logs\test-runs\ztypes-fragility-red-20260417-111221.log`). Changed `imps_rev` to require explicit provenance-bearing `p_args` and `p_defeats`, reject missing or unprovenanced opinions, and pass supplied opinions through unchanged to DF-QuAD. Verification passed: fragility micro-suite (`3 passed`, `logs\test-runs\ztypes-fragility-green-20260417-111304.log`), full fragility suite (`30 passed`, `logs\test-runs\ztypes-fragility-suite-20260417-111320.log`), production Pyright over `propstore/fragility_scoring.py` (`0 errors`), no production callers still using the old signature, and grep gate clean for `Opinion.dogmatic_true()` across `propstore/fragility_scoring.py`, `propstore/praf`, and `propstore/core`.
- 2026-04-17: Phase Z-types-6 document schema/classify slice completed. Red tests captured that `OpinionDocument` still accepted missing provenance, `classify.py` wrote unprovenanced opinion payloads, and `type="none"` still serialized a fabricated vacuous opinion (`logs\test-runs\ztypes-docs-red-20260417-111921.log`). Made `OpinionDocument.provenance` mandatory, made `classify.py` serialize only provenance-bearing opinions or explicit `opinion=None`, and updated stance authoring fixtures to the strict schema. Verification passed: focused red slice (`3 passed`, `logs\test-runs\ztypes-docs-green-20260417-112002.log`), schema/relate/source/analyzer suite (`46 passed`, `logs\test-runs\ztypes-docs-suite-2-20260417-112049.log`), and targeted Pyright over `propstore/artifacts/documents/claims.py propstore/classify.py` (`0 errors`).

## What you're doing

The 2026-04-16 review found a single recurring antipattern across five different files: **fabricated certainty at calibration-free defaults**. Same shape, different sites:

- `propstore/calibrate.py:211-217` — `_DEFAULT_BASE_RATES = {"strong": 0.7, "moderate": 0.5, "weak": 0.3, "none": 0.1}`. Documented as "corpus frequency priors" without a corpus. Every uncalibrated LLM stance classification inherits these as the `a` parameter of a vacuous opinion.
- `propstore/praf/engine.py:155-157, 197-199, 252` — defaults to `Opinion.dogmatic_true()` when calibration data is missing, with a "backward compat" comment. Literal inversion of honest-ignorance.
- `propstore/source_calibration.py:39, 65, 94-97` — silently defaults `prior_base_rate=0.5` without provenance on the stored payload.
- `propstore/fragility_scoring.py:366-367` — fabricates dogmatic opinions for every argument and defeat in the framework before "sensitivity analysis" runs.
- `propstore/classify.py:148-161` — writes `(0.0, 0.0, 0.0, 0.5)` opinion fields when LLM emits "no stance," violating the `b+d+u=1` invariant.

And a second recurring antipattern: **three-valued solver results collapsed to two-valued at the interface boundary**:

- `propstore/z3_conditions.py:444, 463, 481, 489` — Z3 `sat | unsat | unknown` collapses to `bool`. No `SolverResult` sum type.
- `propstore/condition_classifier.py:32-36` — every Z3 unknown silently becomes `ConflictClass.OVERLAP`. Propagates into merge + argumentation.
- `propstore/dung_z3.py:151, 197` — enumeration loops silently truncate on Z3 unknown.
- No `timeout|set_param|set_option` calls anywhere in `propstore/` — Z3 has no time budget; "unknown" can mean "I gave up" or "this is genuinely undecidable" with no way to distinguish.

Your job: build the type system that makes these antipatterns **impossible to re-introduce structurally**, not "discouraged by code review." Concretely: introduce `Provenance`, `CategoryPrior`, `SolverResult`, `Opinion | NoCalibration`, `ConflictClass.UNKNOWN`. Migrate every fabrication site to the typed alternative. Remove the silent defaults.

## Vision

When this workstream is complete:

- **No probability enters the argumentation layer without provenance.** Every `Opinion`, every prior, every fused result carries a `Provenance` whose `status` distinguishes `measured | calibrated | stated | defaulted | vacuous`. `Opinion(0.7, 0.0, 0.3, 0.5)` is a type error; `Opinion(0.7, 0.0, 0.3, 0.5, provenance=<...>)` is the only construction path.
- **No category prior is a hardcoded module constant.** `_DEFAULT_BASE_RATES` is replaced by `CategoryPrior` — a typed object with `value: float`, `source: CalibrationSource`, `provenance: Provenance`. Modules requiring a prior request one explicitly; defaults mean opting in to a named "I want the default" mode that records the choice in provenance.
- **No three-valued solver result collapses to two-valued silently.** `SolverResult` is a sum type: `SAT(model)`, `UNSAT(unsat_core)`, `UNKNOWN(reason: TimeOut | Incomplete | Other)`. Every Z3 caller pattern-matches on the result; there is no `bool(result)` path.
- **No Z3 query runs without a timeout.** Z3 calls go through a thin wrapper that sets a configured timeout and returns `UNKNOWN(reason=TimeOut)` on expiration.
- **`ConflictClass.UNKNOWN` exists.** `condition_classifier.py` returns `UNKNOWN` when Z3 returns `UNKNOWN`; downstream consumers (merge classifier, argumentation) treat unknown as not-evidence-of-conflict, not as overlap.
- **`praf/engine.py` returns `Opinion | NoCalibration`** when calibration data is missing. PrAF construction handles the two cases distinctly. `dogmatic_true()` defaults are gone.
- **`SourceTrustDocument` and `SourceTrustQualityDocument` carry mandatory `status` fields.** No silent prior defaulting; every numeric value is labeled.
- **`ResolutionDocument`'s four scalar opinion fields collapse to a single `opinion: OpinionDocument | None`.** The invariant-violating `(0, 0, 0, 0.5)` write at `classify.py:148-161` becomes either a valid vacuous opinion with provenance or an explicit `None`.
- **Property tests prevent regression.** Construction tests verify that an Opinion without provenance, or a `SourceTrust` without status, fails to type-check at the test level.

## What you are NOT doing

- **Not designing the full `Provenance` type.** WS-A phase 1 owns that. Z-types declares the *interface* that consumers will use (`provenance: Provenance` field positions; status-discriminator structure); the real type lands in WS-A. You can land partial work using a placeholder provenance shape that WS-A will fill in.
- **Not redesigning `Opinion`'s mathematical operators.** They're correct (post-fix per commits 34d0074 and c7a9215). You're adding a provenance-bearing wrapper; the operator math stays.
- **Not implementing CKR or any defeasibility semantics.** WS-C does that. You provide the `ConflictClass.UNKNOWN` variant; WS-C consumes it.
- **Not building heuristic LLM proposals to populate the now-required calibration data.** That's a separate proposal-branch workstream. Z-types just makes the absence of calibration explicit and labelable.
- **Not removing the existing `Opinion` API.** Add the provenance-bearing variant; migrate callers; the math API survives.

## Phase structure

### Phase Z-types-1 — `SolverResult` sum type + Z3 timeout config

The most contained piece. No paper dependency, no provenance dependency.

- Design `SolverResult` as a tagged union: `SAT(model)`, `UNSAT(unsat_core)`, `UNKNOWN(reason: TimeOut | Incomplete | Other, hint: str)`.
- Configure a default Z3 timeout (start with 30 seconds; make it overridable per-call). The choice of default needs a one-line justification in the docstring; every Z3 query should have a *reason* its timeout is what it is, not a magic number.
- Wrap every Z3 call site in `propstore/z3_conditions.py`, `propstore/dung_z3.py`, `propstore/world/ic_merge.py`, `propstore/aspic_bridge/`, `propstore/conflict_detector/` with the new wrapper.
- Each call site that used to bool-coerce now pattern-matches. Most call sites have a sensible behavior for SAT and UNSAT; UNKNOWN paths must be designed deliberately — usually "propagate UNKNOWN upward" until reaching the render layer or a policy boundary that can choose how to handle it.
- Property tests: every public Z3-using function returns either a typed result or propagates UNKNOWN explicitly; no caller silently coerces UNKNOWN to a definite value.

### Phase Z-types-2 — `ConflictClass.UNKNOWN` + condition_classifier propagation

- Add `UNKNOWN` variant to `ConflictClass`.
- Update `propstore/condition_classifier.py:32-36` to return `UNKNOWN` when the Z3 result is `UNKNOWN`. No silent fallback to `OVERLAP`.
- Update consumers: `merge_classifier.py` handles `UNKNOWN` distinctly from `OVERLAP` (UNKNOWN means "couldn't decide"; OVERLAP means "decided that they overlap"). Render policy decides what to do with UNKNOWN-flagged conflict records.
- Property tests: every conflict record carries enough provenance to recover the underlying solver result.

### Phase Z-types-3 — `Opinion` provenance-bearing wrapper

Coordinates with WS-A phase 1. Can land a placeholder `Provenance` type now and migrate to the WS-A real type when it lands.

- Add `provenance: Provenance | None` field to `Opinion`. Initially `None` is permitted (so existing code keeps working through migration); after callers update, flip to mandatory.
- Add `Opinion.with_provenance(...)`, `Opinion.vacuous(provenance=...)`, `Opinion.dogmatic_true(provenance=...)`, etc. — explicit construction paths that take provenance.
- Update fusion operators (`consensus_pair`, `_ccf_binomial`, `wbf` once-fixed) to compose provenance. For now, composition is "list of source provenances" — WS-A phase 1 finalizes the algebra.
- Property tests: every Opinion construction in production (non-test) code paths supplies provenance; tests catch the absence.

### Phase Z-types-4 — `CategoryPrior` replacing `_DEFAULT_BASE_RATES`

- Design `CategoryPrior(category: str, value: float, source: CalibrationSource, provenance: Provenance)`.
- `CalibrationSource` is a discriminated string: `"measured" | "user_default" | "module_default" | "vacuous"`.
- Remove `_DEFAULT_BASE_RATES` from `calibrate.py:211-217`. Replace with a `CategoryPriorRegistry` that callers consult explicitly. The registry can be empty (the default); a CLI command (`pks calibrate set-prior --category=strong --value=0.7 --source=user_default`) populates it.
- Functions that previously called `_DEFAULT_BASE_RATES[cat]` now take an explicit `CategoryPrior` argument or accept a registry handle and look it up. Missing priors raise (or return `NoCalibration`); they do not silently default.
- `categorical_to_opinion(cat, pass_n)` becomes `categorical_to_opinion(cat, pass_n, prior: CategoryPrior | None)`. The `None` branch returns `Opinion.vacuous(a=0.5, provenance=Provenance(status="vacuous", reason="no_prior_supplied"))` — explicitly vacuous, explicitly provenanced, never carrying a guessed `a`.
- Property tests: no path through `categorical_to_opinion` can produce an Opinion with a non-vacuous `a` value unless a `CategoryPrior` was supplied.

### Phase Z-types-5 — `praf/engine.py` `Opinion | NoCalibration` return

- Define `NoCalibration(reason: str, missing_fields: list[str])` as the sentinel.
- Update `p_arg_from_claim` and `p_relation_from_stance` (per axis 5 findings 1.1, 1.2): return `Opinion | NoCalibration` instead of falling back to `dogmatic_true()`.
- Update PrAF construction sites to handle `NoCalibration` explicitly. Common handling: skip the argument/defeat, log the omission with provenance, propagate to the result (PrAF's output records which arguments were omitted for missing calibration).
- Update `fragility_scoring.imps_rev` (axis 1 Finding 2.3) to accept real `p_args` / `p_defeats` or to receive an explicit `Opinion.vacuous(provenance=...)` rather than fabricated dogmatic opinions. The function's *behavior* under vacuous inputs is itself a design question — verify with WS-A phase 1's provenance algebra.

### Phase Z-types-6 — Document schema migrations

- `SourceTrustDocument` and `SourceTrustQualityDocument` (`propstore/artifacts/documents/sources.py`) gain `status: Literal["measured", "calibrated", "defaulted", "vacuous"]`. Mandatory field; no default.
- `ResolutionDocument` (`propstore/artifacts/documents/claims.py`) collapses four scalar fields (`opinion_belief`, `opinion_disbelief`, `opinion_uncertainty`, `opinion_base_rate`) into `opinion: OpinionDocument | None`. The OpinionDocument carries the provenance per WS-A phase 1.
- Migration: existing on-disk documents fail-to-load until reauthored. Provide `pks migrate honest-ignorance` CLI that walks the repo and replaces each numeric-without-status with a `status="legacy"`-flagged value the user must explicitly review and confirm. **No silent defaulting during migration.**
- `propstore/classify.py:148-161` updated to write `opinion=None` when no stance is determined, or a properly-vacuous OpinionDocument with provenance when there is meaningful uncertainty to record.
- `propstore/source_calibration.py` updated to surface `status="defaulted"` on the stored payload, not just on a sibling finalize report.

## Red flags — stop if you find yourself

- About to add a `default` parameter to a function returning `Opinion`.
- About to write `if isinstance(result, SAT): ... else: ...` where the else branch silently treats `UNKNOWN` as `UNSAT` (or vice versa).
- About to set a Z3 timeout to a magic number with no docstring justification.
- About to keep `_DEFAULT_BASE_RATES` "just for backward compatibility."
- About to write a `status="legacy"` value in fresh data (the migration tool may write it, but only as a flag for human re-review, never as a permanent state).
- About to make `Opinion`'s provenance field optional after the migration phase.
- About to map `ConflictClass.UNKNOWN` to `OVERLAP` "for now."
- About to fix one fabrication site without checking whether the same antipattern exists elsewhere.

## Exit criteria

- `SolverResult` sum type lives; every Z3 call site uses it; no bool coercion.
- Z3 timeout configured globally (with per-call override) and documented.
- `ConflictClass.UNKNOWN` exists; `condition_classifier.py` and downstream consumers handle it.
- `Opinion` carries provenance; existing fusion operators compose it.
- `CategoryPrior` replaces `_DEFAULT_BASE_RATES`; no path produces a non-vacuous `a` without explicit prior input.
- `praf/engine.py` returns `Opinion | NoCalibration`; PrAF construction handles both cases.
- `fragility_scoring.imps_rev` accepts real or vacuous opinions; no fabricated dogmatic_true.
- `SourceTrustDocument`, `SourceTrustQualityDocument`, `ResolutionDocument` migrated.
- `classify.py:148-161` no longer writes invariant-violating opinions.
- `source_calibration.py` carries provenance status on the trust document, not just on the report.
- All five fabrication sites and three solver-collapse sites flagged in the review are unreachable from the new type system.
- Property tests verify the new invariants — provenance presence on Opinion, status presence on SourceTrust, SolverResult sum-type discrimination, no silent UNKNOWN coercion.
- All axis-1 findings 2.1-2.6 + Structural S1-S3, axis-5 categories 1+2+5+6, and axis-3e CRIT findings on Z3 collapse marked closed in `docs/gaps.md`.
- `uv run pytest tests/` green.

## On learning

The core insight here is that *types are how systems prevent recurring bugs*. The fabrication antipattern appeared in five places not because five different developers each made the same mistake, but because the type system *permitted* the antipattern — it was easier to return a default float than to return a sentinel-or-real-value sum type, so the easy thing won every time.

The fix is not vigilance. The fix is changing the types so the easy thing IS the right thing. After this workstream, the easiest way to use `Opinion` is the way that carries provenance; the easiest way to use Z3 is the way that pattern-matches on `SolverResult`; the easiest way to construct a stance is the way that records `status="vacuous"` when no evidence exists. The hard ways still exist (you can always cheat) but they are visible in code review and they fail at the type-system boundary.

Read Pierce's *Types and Programming Languages* if you want the deeper theoretical grounding for why "make the right thing easy" is the right design pressure on type systems. Practical version: every time you find yourself wanting to fabricate a default, the type is wrong. Fix the type.
