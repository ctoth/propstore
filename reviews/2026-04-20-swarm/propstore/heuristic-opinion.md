# Heuristic Analysis Layer & Opinion Math Review — 2026-04-20

Scope: propstore/opinion.py, calibrate.py, classify.py, proposals.py, stances.py, fragility*.py, relate.py, relation_analysis.py, conflict_detector/, probabilistic_relations.py, sensitivity.py, propagation.py, embed.py, source_calibration.py (skim), equation_comparison.py, equation_parser.py, value_comparison.py.

Reviewer: adversary analyst; dual mandate was principle enforcement + ordinary bug hunting. Findings are unsoftened.

---

## Source Mutation Violations

### source_calibration.py:137-140 — derived prior silently overwrites authored prior without provenance audit
File: `C:\Users\Q\code\propstore\propstore\source_calibration.py:114-140`
Summary: `derive_source_trust` calls `wm.chain_query(...)` to look up a `source_trust_base_rate`. If it resolves, `prior = resolved_prior; trust["status"] = CALIBRATED.value`. A caller who supplied their own prior (e.g., status=MEASURED) has that prior silently overwritten by a calibration lookup. Worse: when the resolution path is `ValueResult/DETERMINED`, `value` is extracted with `isinstance(value, (int, float))` — a raw float is lifted into the trust record and the claim's own provenance is discarded. The returned SourceDocument carries a CALIBRATED stamp but the upstream provenance chain is not propagated into `quality`.
Severity: high. Concept/semantic-layer provenance being replaced by a derived numeric without typed carryover is exactly the "fabricated confidence" failure mode CLAUDE.md forbids.
Fix: require that `resolved_prior` carry ProvenanceStatus; never overwrite a MEASURED/CALIBRATED user input with a DERIVED lookup; propagate `result.steps` into `trust["derived_from"]` AND into the `quality` record.

No other hard source-mutation violations found. `proposals.py` correctly writes to a dedicated proposal branch (`PROPOSAL_STANCE_FAMILY`) and has an explicit promote step. Conflict/fragility/relate modules all produce records or proposal payloads without touching source artifacts.

---

## Provenance-Drop Sites

### classify.py:96-120 — `_build_error_pair` emits `confidence: 0.0` with no opinion and no provenance
File: `C:\Users\Q\code\propstore\propstore\classify.py:96-120`
Summary: Classification failure (connection error, JSON parse error, missing content) returns a stance with `"type": "error", "strength": "weak", "confidence": 0.0` and no `opinion` key. 0.0 is fabricated confidence of failure; honest ignorance is `Opinion.vacuous(provenance=Provenance(VACUOUS, (), ("classification_failed",)))`.
Severity: high.
Fix: thread a vacuous opinion with explicit VACUOUS provenance; drop `"confidence": 0.0` or derive it from `opinion.expectation()` (0.5 for the default base rate — honest ignorance, not a fake zero).

### calibrate.py:193-207 — `CorpusCalibrator.to_opinion` emits no provenance
File: `C:\Users\Q\code\propstore\propstore\calibrate.py:193-207`
Summary: `from_probability(p, n_eff)` is called with no `provenance=` keyword. Resulting Opinion has `provenance=None`. Calibration demonstrably happened (CDF lookup, local density counting); the status should be `CALIBRATED` with operation `corpus_cdf_calibration`. A caller downstream (e.g., classify.py's fuse) sees a provenance-less opinion and drops the calibration pedigree.
Severity: high — direct violation of "every probability-bearing value must carry typed provenance."
Fix: accept `provenance: Provenance | None = None` OR construct `Provenance(CALIBRATED, (), ("corpus_cdf_calibration",))` internally and pass to `from_probability`.

### calibrate.py:207 — `CorpusCalibrator.to_opinion` hardcodes base_rate=0.5
File: `C:\Users\Q\code\propstore\propstore\calibrate.py:207`
Summary: `from_probability(p, n_eff)` (no `a=` argument) uses the default 0.5. No callable path lets a caller supply a CategoryPrior. Every corpus-calibrated opinion silently gets a fabricated binary-frame prior.
Severity: medium.
Fix: accept `prior: CategoryPrior | None = None` (as in `categorical_to_opinion`) and propagate value+provenance.

### classify.py:151-160 — fuse(opinion, corpus_opinion) launders away the provenance drop
File: `C:\Users\Q\code\propstore\propstore\classify.py:157-160`
Summary: `opinion` from categorical_to_opinion has CALIBRATED/VACUOUS provenance; `corpus_opinion` has `None` (see above). `_compose_opinion_provenance` skips None entries. The fused opinion therefore records only the categorical contributor, losing the fact that corpus calibration participated. Provenance silently asymmetric.
Severity: medium — cascades from the calibrate.py bug above; fixing that fixes this.

### classify.py:163-165 — `stance_type == "none"` → opinion=None, confidence=0.0
File: `C:\Users\Q\code\propstore\propstore\classify.py:163-165`
Summary: When the LLM emits `type:none`, the code drops the opinion entirely and writes `confidence: 0.0, opinion: None`. An LLM asserting "no relationship" with `strength:strong` IS evidence for `¬relation` — not ignorance. Storing None discards that evidence. The downstream consumer cannot distinguish "LLM said no" from "LLM wasn't asked" from "LLM errored".
Severity: medium.
Fix: build an opinion for the negated proposition ("there IS no relationship"), stamped CALIBRATED; preserve the LLM's strength signal.

### classify.py:151 — silent fabrication: `raw.get("strength", "moderate")`
File: `C:\Users\Q\code\propstore\propstore\classify.py:151`
Summary: If the LLM returns JSON missing "strength", the code invents "moderate". That string then becomes an opinion via `categorical_to_opinion`. Missing input is treated as if the LLM asserted a definite moderate-strength claim.
Severity: high — textbook fabricated confidence.
Fix: treat missing strength as a parse error → route to `_build_error_pair` with explicit VACUOUS provenance.

### classify.py:242 — `forward_raw = result.get("forward", result)` fabricates a reverse stance
File: `C:\Users\Q\code\propstore\propstore\classify.py:242-243`
Summary: On structurally-malformed LLM output (e.g., flat `{"type":..., "strength":...}` missing the `forward`/`reverse` wrapper), the code silently treats the flat blob as "forward" AND fabricates a reverse `{"type":"none", "strength":"weak", "note":"not classified"}`. That reverse stance is a pure invention — the LLM emitted no such claim — and it flows into the stance proposal with no marker that it is fabricated.
Severity: high — fabricated data masquerading as LLM output. Fix: on structural mismatch, route to `_build_error_pair` for both directions.

---

## Fabricated Confidence

### classify.py:75 — `_ENRICHMENT_THRESHOLD_DEFAULT = 0.75` hardcoded magic
File: `C:\Users\Q\code\propstore\propstore\classify.py:75`
Summary: Embedding-distance enrichment threshold is hardcoded. No literature citation, no per-model-family scaling, no documented basis. calibrate.py:113-115 itself calls out the problem: raw distances are unnormalized and model-dependent. Yet relate/classify still compares raw distance against 0.75.
Severity: high. Violates the principled-thresholds discipline (no arbitrary heuristic gates). The `CorpusCalibrator` exists precisely to fix this; its output is used for fusion but not for enrichment gating.
Fix: feed the distance through `CorpusCalibrator.percentile` and compare a percentile (e.g., bottom 10%) — or pass an explicit, CLI-configurable threshold with provenance.

### fragility_contributors.py:395-400 — `_SECTION_FRAGILITY` magic mapping
File: `C:\Users\Q\code\propstore\propstore\fragility_contributors.py:395-400`
Summary: `"definitely": 0.25, "defeasibly": 0.75, "not_defeasibly": 0.5, "undecided": 1.0` — fabricated fragility numbers with no defense. No paper cited. No calibration story. These numbers become `local_fragility` in RankedIntervention, which callers treat as [0,1] fragility scores.
Severity: medium/high. These are unchecked fabricated probabilities flowing into a user-facing ranking.
Fix: either justify each number with a citation and stamp the provenance, or derive from stance counts at runtime.

### fragility_contributors.py:479-481 — grounded-rule fragility is a magic sum
File: `C:\Users\Q\code\propstore\propstore\fragility_contributors.py:479-482`
Summary: `0.3 + (0.1 * len(rule.antecedents)) + (0.25 * min(undercut_count, 2))` — three magic coefficients with caps. No derivation, no citation.
Severity: medium.

### fragility_contributors.py:555 — bridge-undercut fragility is a magic sum
File: `C:\Users\Q\code\propstore\propstore\fragility_contributors.py:555`
Summary: `0.3 + (0.25 * min(attack_count, 2)) + (0.35 * min(defeat_count, 2))` — same problem.
Severity: medium.

### fragility_contributors.py:429 — ground_fact bump `0.1 * min(dependency_count, 3)`
Severity: medium.

### relation_analysis.py:51 — `opinion_value > 0.99` "vacuous" threshold
File: `C:\Users\Q\code\propstore\propstore\relation_analysis.py:51-52`
Summary: Vacuous is mathematically `u == 1.0`. The code applies a 0.99 threshold to count "vacuous" opinions — a float tolerance masquerading as a semantic category.
Severity: low.
Fix: compare against `Opinion`'s own tolerance constant (`_TOL = 1e-9`) or accept user policy.

### classify.py:118-121 — "error" stance emits `confidence: 0.0`
Same pattern as provenance-drop finding above; reiterated because the numeric 0.0 IS fabricated certainty of failure.

---

## Opinion Algebra Correctness

### opinion.py:482-484 — WBF silent clamping of negative fused components
File: `C:\Users\Q\code\propstore\propstore\opinion.py:482-484`
Summary: After the division, `b_fused = max(0.0, b_fused); d_fused = max(0.0, d_fused); u_fused = max(0.0, u_fused)`. If any component went genuinely negative (not just float drift), the sum will no longer equal 1 and the Opinion constructor will raise. For tiny-negative float drift the clamp renormalizes silently — but there is no post-clamp `b+d+u≈1` check. A pathological κ could produce a state where constructor accepts `b=0, d=0, u=1-ε` with ε hidden in the base rate.
Severity: medium.
Fix: after clamp, assert `abs((b+d+u)-1) <= _TOL * 10` or explicitly renormalize with a warning.

### opinion.py:490-492 — WBF "all vacuous" branch skips `_clamp_base_rate`
File: `C:\Users\Q\code\propstore\propstore\opinion.py:490-492`
Summary: In the `total_weight < _TOL` (all vacuous) branch, `a_fused = sum(op.a for op in opinions) / N`. The clamp `_clamp_base_rate(a_fused)` is applied after — but the similar all-vacuous fallback in `_ccf_binomial` at line 654 is ALSO pre-clamp (then clamped at 657). Checking more carefully: wbf DOES call `_clamp_base_rate` at line 500 for all paths. So this is actually fine — BUT the dogmatic-source branch at 451 uses `_clamp_base_rate(a_fused)` explicitly, while the CCF dogmatic-equivalent path does not exist (CCF handles dogmatic via the main algorithm). Asymmetry is cosmetic.
Severity: low.

### opinion.py:458 — `prod_except[i] = total_prod / op.u` — unsafe division protected only by preceding guard
File: `C:\Users\Q\code\propstore\propstore\opinion.py:457-458`
Summary: Correct today because the `if dogmatic:` branch at 436 catches `u < _TOL`, but the safety depends on that guard remaining in place. A numerically robust form uses O(N) prefix/suffix scans.
Severity: low (latent hazard).

### opinion.py:624-625 — CCF cancellation risk in `comp_X = prod_res_total - prod(res_b) - prod(res_d)`
File: `C:\Users\Q\code\propstore\propstore\opinion.py:624-625`
Summary: Textbook catastrophic-cancellation recipe: three small products of the same magnitudes subtracted. The `comp_sum < _TOL` edge case catches exact agreement but not near-agreement where the subtraction produces a sign-flipped tiny value. No property test exercises near-identical opinions with random perturbations.
Severity: medium.
Fix: property test; if cancellation detected, route to the exact-agreement branch.

### calibrate.py:444 — `bin_boundaries` built and never used
File: `C:\Users\Q\code\propstore\propstore\calibrate.py:444`
Summary: Dead code. The actual bin assignment uses `int(conf * n_bins)`. Red flag — author intended to use boundaries then didn't, suggesting the hand-computed index was not cross-checked against the nominal boundary list.
Severity: low (dead code) but indicative.

### calibrate.py:448-452 — ECE bin assignment silently bins out-of-range confidence
File: `C:\Users\Q\code\propstore\propstore\calibrate.py:450`
Summary: `idx = min(int(conf * n_bins), n_bins - 1)`. No lower bound. `conf = -0.1, n_bins=15` → `idx = int(-1.5) = -1` → accesses `bin_correct[-1]` (last bin) silently. `conf > 1` is capped to the last bin. No validation that `conf ∈ [0,1]`.
Severity: medium.
Fix: validate `0 <= conf <= 1` up front, or clamp with a warning.

### fragility_scoring.py:100 — `score_conflict` divides by `total = len(framework.arguments)`
File: `C:\Users\Q\code\propstore\propstore\fragility_scoring.py:82-100`
Summary: `total = len(framework.arguments)`. Then `min(1.0, max(dist_a, dist_b) / total)`. If `framework.arguments` is empty the function returns 0.0 early at line 80; otherwise division is safe. OK. But: `dist_a = len(current.symmetric_difference(ext_remove_a))` — if removing argument `a` from a 3-arg framework shifts the extension by up to 3, `3/3 = 1.0`. The `min(1.0, ...)` is then redundant. Fine, just noting that the normalization can saturate.
Severity: low.

### fragility_scoring.py:343 — `opinion_sensitivity` uses fixed `delta=0.01`
File: `C:\Users\Q\code\propstore\propstore\fragility_scoring.py:339-383`
Summary: Finite-difference derivative with hardcoded `delta=0.01`. The retry loop halves delta up to 3 times. No adaptive stepping based on the opinion's proximity to boundaries. A tight opinion (u near 0.01) gets perturbed right into the dogmatic regime and returns None, silently reporting "no sensitivity."
Severity: low.

---

## Bugs & Silent Failures

### classify.py:106 — `"type": "error"` is NOT in VALID_STANCE_TYPES
File: `C:\Users\Q\code\propstore\propstore\classify.py:106` + `stances.py:8-18`
Summary: `_build_error_pair` emits `"type": "error"`. `VALID_STANCE_TYPES` contains only rebuts/undercuts/undermines/supports/explains/supersedes/none. Any downstream `StanceType(stance["type"])` call raises ValueError. `_build_stance_dict` coerces unknown types to "none" but `_build_error_pair` bypasses that path — it emits the raw `"error"` into the proposal payload.
Severity: high (data-poisoning: downstream deserialization will crash).
Fix: either add "error" to StanceType enum (and make VALID_STANCE_TYPES include it) or route errors through a separate `ErrorStance` record, not a stance dict.

### classify.py:227 — catching `ValueError` for `litellm.acompletion`
File: `C:\Users\Q\code\propstore\propstore\classify.py:227`
Summary: `except (ConnectionError, TimeoutError, OSError, ValueError)` — catching ValueError from an HTTP call masks programmer errors in message construction. Correctness risk.
Severity: low.

### classify.py:262-265 — circular import path via `from propstore.relate import _run_async`
File: `C:\Users\Q\code\propstore\propstore\classify.py:264`
Summary: classify.py imports from relate.py at function-call time; relate.py imports classify_stance_async at module-import time. Not strictly circular in practice (lazy), but structurally the dependency is reversed from the module comment "Classification logic lives in propstore.classify; this module handles pair selection...".
Severity: low.

### fragility_contributors.py:155-161 — `derive_scored_concepts` swallows everything to empty list
File: `C:\Users\Q\code\propstore\propstore\fragility_contributors.py:143-161`
Summary: `except Exception as exc: warnings.warn(...); return []`. Caller receives [] on any error — discovery failure is indistinguishable from "no concepts to score." Downstream, `rank_fragility` iterates the empty list and returns `world_fragility=0.0` cheerfully. Silent failure.
Severity: medium.
Fix: narrow the except to documented failure modes; let unexpected exceptions propagate.

### fragility_contributors.py:185-191 — `collect_assumption_interventions` swallows per-concept ATMS errors
File: `C:\Users\Q\code\propstore\propstore\fragility_contributors.py:183-191`
Summary: Each concept's ATMS call is wrapped in `except Exception`. Consumers cannot distinguish "this concept has no witnesses" from "ATMS engine crashed on this concept." Same blunt-instrument pattern.
Severity: medium.

### fragility_contributors.py:133 — `json.loads` without try/except
File: `C:\Users\Q\code\propstore\propstore\fragility_contributors.py:133`
Summary: `json.loads(parameterization.conditions_cel)` raises JSONDecodeError on malformed input and propagates out of `_parameterizations_to_queryables`. Inconsistent error handling with the sibling `derive_scored_concepts` that swallows everything.
Severity: low.

### fragility_contributors.py:294 — ZeroDivisionError edge case
File: `C:\Users\Q\code\propstore\propstore\fragility_contributors.py:294-297`
Summary: `max_downstream = max(len(subjects) for subjects in downstream_by_input.values())`. If all sets are empty → max=0 → `len(subjects) / max_downstream = 0/0`. The loop that builds `downstream_by_input` only adds to an input set when the set gets a new concept, so in practice they're coupled. Fragile coupling invariant.
Severity: low.

### fragility_scoring.py:321 — `_try_perturb` imports Opinion inside the function
File: `C:\Users\Q\code\propstore\propstore\fragility_scoring.py:321`
Summary: `from propstore.opinion import Opinion` inside the function (also in `opinion_sensitivity`, `imps_rev`). These lazy imports are load-bearing for circular-import avoidance but should be documented.
Severity: info.

### fragility.py:219-223 — `world_fragility` averages top-10 of an already-top-k-truncated list
File: `C:\Users\Q\code\propstore\propstore\fragility.py:219-223`
Summary: `ranked = ranked[:top_k]; world_fragility = sum(item.local_fragility for item in ranked[:min(10, len(ranked))]) / min(10, len(ranked))`. If caller passes `top_k=3`, world fragility is the mean of only 3 items. The magic number 10 (documented nowhere) silently caps how many interventions contribute. Low-severity but the averaging policy deserves docs+citation.
Severity: low.

### sensitivity.py:280 — `output_value != 0` exact equality
File: `C:\Users\Q\code\propstore\propstore\sensitivity.py:280`
Summary: Elasticity guards on `output_value != 0`. Near-zero floats pass the guard and produce elasticity magnitudes dominated by float noise. No tolerance check.
Severity: low.
Fix: `abs(output_value) > DEFAULT_TOLERANCE` with a documented tolerance.

### sensitivity.py:267 — `input_sym = symbols.get(input_symbol, Symbol(input_symbol))` silently constructs a fresh Symbol
File: `C:\Users\Q\code\propstore\propstore\sensitivity.py:267`
Summary: If the input symbol is missing from `symbols`, sympy creates a fresh Symbol. Then `sym_diff(expr, input_sym)` differentiates a symbol not in `expr`, returning 0. The function will report zero elasticity for that input — indistinguishable from a genuine zero sensitivity. Silent failure.
Severity: medium.
Fix: raise/skip if `input_symbol not in symbols`.

### embed.py:223 — `top_k + 1` requested, `!= resolved_id` filter
File: `C:\Users\Q\code\propstore\propstore\embed.py:223-224`
Summary: Requests k+1 results and filters out the query entity by id. If the query entity's embedding is not literally the nearest (common when multiple entities share text), this filter over-consumes results by 0. If more than one record has the query's id (shouldn't happen, but schema-unenforced), results can over-filter.
Severity: low.

### value_comparison.py:52 — absolute tolerance `1e-9` is unit-blind
File: `C:\Users\Q\code\propstore\propstore\value_comparison.py:52` (and DEFAULT_TOLERANCE at line 11)
Summary: Point-vs-point comparison uses `abs(lo_a - lo_b) < 1e-9`. SI normalization happens *before* the call, but absolute tolerance on SI values still treats 1e-12 meters as "noisy zero" even if the measurement legitimately has femtometer precision. For large magnitudes (Avogadro-scale), 1e-9 is vastly stricter than needed; for nanoscale, 1e-9 SI (nm) is coarser than the data.
Severity: medium.
Fix: relative tolerance (e.g., `abs(a-b) <= tol * max(abs(a), abs(b), 1.0)`) or propagate per-form precision from the form definition.

### equation_parser.py:227 — `render_equation` exists but is not called anywhere in scope
File: `C:\Users\Q\code\propstore\propstore\equation_parser.py:229-230`
Summary: Helper not referenced by the reviewed modules. If orphaned: dead code.
Severity: info.

### equation_comparison.py:178 — `sympy.cancel(sympy.expand(lhs - rhs))` canonical form is sensitive to SymPy version
File: `C:\Users\Q\code\propstore\propstore\equation_comparison.py:178`
Summary: `canonical = str(diff)` produces a canonical form dependent on SymPy's internal ordering. Two equations that should compare equivalent may produce different canonical strings across minor SymPy versions. No hash-stability property test.
Severity: medium.
Fix: pin SymPy version OR use structural hashing via `sympy.srepr` + an ordering canonicalization pass.

### conflict_detector/parameterization_conflicts.py:213 — `abs(hi - lo) >= DEFAULT_TOLERANCE` filters out ranges
File: `C:\Users\Q\code\propstore\propstore\conflict_detector\parameterization_conflicts.py:213`
Summary: Only point-valued claims become derived states. Range-valued claims are silently dropped from the forward-chaining derivation. That's a policy choice — but undocumented. A user with range-valued measurements sees no derived conflicts and no warning.
Severity: medium.
Fix: document or handle ranges via interval propagation.

### conflict_detector/parameterization_conflicts.py:548 — `max_iterations = len(group) * 4` cap
File: `C:\Users\Q\code\propstore\propstore\conflict_detector\parameterization_conflicts.py:548`
Summary: Transitive derivation caps at `4N` iterations. For deeply chained groups, the cap can terminate before saturation — dropping valid derived conflicts. No warning is emitted when the cap fires. No principled justification for 4.
Severity: medium.
Fix: emit a warning when `iteration == max_iterations && changed`; document the bound as a citation or remove the arbitrary constant.

### probabilistic_relations.py:75 — `repr(row[key])` in row_identity
File: `C:\Users\Q\code\propstore\propstore\probabilistic_relations.py:75`
Summary: Uses `repr(value)` to stabilize row_identity. `repr` can differ subtly across Python minor versions for floats and ordered containers. Using `repr` as identity is brittle.
Severity: low.
Fix: canonical JSON serialization with sort_keys=True and fixed float format.

### classify.py:259-264 — `stance["type"] != "none"` branch is identical to its else branch
File: `C:\Users\Q\code\propstore\propstore\relate.py:259-264`
Summary: The `if stance["type"] != "none":` and `else:` branches both call `all_stances.setdefault(source_id, []).append(stance)` — the only difference is which counter increments. The guard is vestigial; simplification available.
Severity: trivial (code smell, not a bug).

### fragility.py:198-199 — `bundle_getter = getattr(bound._store, "grounding_bundle", None); bundle = bundle_getter() if callable(bundle_getter) else GroundedRulesBundle.empty()`
File: `C:\Users\Q\code\propstore\propstore\fragility.py:198-199`
Summary: Runtime duck-typing based on attribute presence. If the method exists but raises internally, the exception escapes. If it exists but returns None, downstream code expects a bundle.
Severity: low.

---

## Dead Code / Drift

- `calibrate.py:444` — unused `bin_boundaries`.
- `calibrate.py:295-313` — `load_calibration_counts` indexes tuple rows by position; fragile if row order changes.
- `equation_parser.py:229` — `render_equation` appears unused in the reviewed scope.
- `fragility_scoring.py:7` — `replace` imported, not used.
- `probabilistic_relations.py:51` — `RelationProvenance.stance_type` stored but never consumed in the reviewed files.

---

## Positive Observations

- `opinion.py` is thoroughly literature-grounded: Jøsang 2001 with page/theorem citations throughout, van der Heijden 2018 reference and deviation documented (base-rate clamping), Table I of the paper is cited as a regression anchor.
- `opinion.py:172-187` `__bool__` raises TypeError — principled guard against Python `and`/`or` short-circuiting past the dispatched `__and__`/`__or__`. Exceptional discipline.
- `opinion.py:189-211` unified `_quantized` helper for `__eq__` and `__hash__` — correctly addressed a prior review finding about hash contract violations.
- `opinion.py:246-280` `maximize_uncertainty` carries thorough invariant documentation tying the bound to the constructor's `0 < a < 1` check.
- `calibrate.py:357-378` `categorical_to_opinion` explicitly stamps `VACUOUS` when no calibration data is present and `CALIBRATED` when counts apply. This is exactly the typed-provenance discipline CLAUDE.md demands — model behavior to replicate elsewhere.
- `calibrate.py` TemperatureScaler.fit uses golden-section search on NLL — correct and cited.
- `proposals.py` uses a dedicated proposal branch with an explicit promote step — correct per "proposals never mutate source."
- `fragility_scoring.py:386-443` `imps_rev` explicitly rejects opinions without provenance with a clear ValueError — exemplary provenance discipline.
- `probabilistic_relations.py` dataclasses are frozen with typed provenance; no raw floats float around.
- `relation_analysis.py:20-24` docstring explicitly cites "no gates before render time" — correctly implementing CLAUDE.md's render-layer discipline.
- `conflict_detector/parameterization_conflicts.py` uses a proper `_Sentinel` enum for INCOHERENT_CONTEXT rather than a magic None.

---

## Summary

High-severity items requiring attention:
1. **classify.py:96-120 and classify.py:151** — error stances and missing-strength default fabricate confidence and emit invalid stance types.
2. **classify.py:106** — `"type":"error"` escapes the VALID_STANCE_TYPES contract; will crash downstream deserialization.
3. **calibrate.py:193-207** — CorpusCalibrator.to_opinion drops both provenance and base-rate inputs.
4. **classify.py:242** — structurally-bad LLM JSON silently produces a fabricated reverse stance.
5. **source_calibration.py:114-140** — derived prior silently overwrites authored prior and drops claim provenance.
6. **classify.py:75** — hardcoded 0.75 enrichment threshold on raw (uncalibrated) embedding distance.

Medium severity (opinion algebra and silent failure):
7. **opinion.py:624-625** — CCF cancellation risk; no property test.
8. **calibrate.py:448-452** — ECE binning silently accepts out-of-range confidence.
9. **sensitivity.py:267** — missing symbol silently returns zero elasticity.
10. **conflict_detector/parameterization_conflicts.py:548** — 4N iteration cap truncates transitive derivation without warning.
11. **equation_comparison.py:178** — SymPy canonical form is version-dependent.
12. **value_comparison.py:52** — absolute tolerance is unit-blind on large/small magnitudes.
13. **fragility_contributors.py:395-400, 479-481, 555** — fabricated fragility coefficients with no derivation or citation.
14. Multiple `except Exception → warnings.warn → return []` swallow-and-empty patterns in fragility_contributors.py.

The system has strong opinion-algebra discipline in `opinion.py` and `calibrate.py`'s categorical path, but the classify→relate pipeline that feeds those primitives routinely drops provenance, fabricates defaults, and compares raw uncalibrated distances to hardcoded thresholds. Fragility scoring has unexplained magic coefficients that violate the "honest ignorance" principle.
