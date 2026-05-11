# Cluster E: world (ATMS) + conflict_detector + support_revision

## Scope

Reviewed (full read):
- `propstore/world/atms.py` (2601 LOC) — `ATMSEngine`
- `propstore/world/{consistency, resolution, assignment_selection_merge}.py`
- `propstore/conflict_detector/{orchestrator, parameter_claims, parameterization_conflicts, algorithms, equations, measurements, context, models, collectors}.py`
- `propstore/support_revision/{operators, state}.py`
- `propstore/provenance/nogoods.py` (47 LOC — note: NOT the ATMS NogoodSet; it is the polynomial-term filter)
- `propstore/core/labels.py` (NogoodSet, Label, EnvironmentKey, combine_labels, merge_labels, normalize_environments)
- `docs/atms.md`, `docs/conflict-detection.md`

Reviewed (notes): de Kleer 1986 ATMS; Forbus & de Kleer 1993 (BPS); Doyle 1979; McAllester 1978 (intro).

Not reviewed (out of time budget for the cap):
`world/{model, queries, hypothetical, value_resolver, bound, types}.py`; `support_revision/{af_adapter, entrenchment, explain, explanation_types, history, iterated, projection, snapshot_types, workflows}.py`; `tests/test_atms_engine.py`, `tests/atms_helpers.py`, `tests/test_assignment_selection_merge.py`. Findings about test coverage are inferred from the engine surface only.

## ATMS algorithm fidelity (step-by-step vs Forbus/de Kleer)

Forbus 1993 Ch. 12 specifies the canonical algorithm: `PROPAGATE(j, n, L)` is the per-justification entry point that calls `WEAVE` (cross-product of antecedent labels minus nogoods and subsumed environments) and then `UPDATE` (push the new label to consequents, recursively). de Kleer 1986 (p.151) uses the same shape: incremental propagation per added justification, with immediate nogood pruning.

`ATMSEngine._build` (`atms.py:1276-1297`) does not implement this algorithm. Instead it runs a global rebuild loop:

```
while True:
    iteration += 1
    self._propagate_labels()
    added = self._materialize_parameterization_justifications()
    nogoods_changed = self._update_nogoods()
    if not added and not nogoods_changed:
        self._propagate_labels()
        break
```

Inside `_propagate_labels` (`atms.py:1382-1420`) all non-assumption/context labels are wiped to `Label(())` at the start of every iteration, and a naive "scan-all-justifications-until-no-change" inner loop refills them. Concrete consequences:

1. **Not incremental.** Adding one justification cannot trigger localized propagation. The engine's only mode is full rebuild. For a store with N claims and M justifications this is O(M·passes) per build, where each pass also re-walks every parameterization edge.

2. **Stale-nogood window inside a single pass.** `_propagate_labels` filters with `self.nogoods`, but `_update_nogoods` runs *after* propagation (`atms.py:1294`). During propagation, labels can include environments that an in-flight conflict will eventually exclude. The fixed-point loop converges, but for any caller that inspects state mid-iteration the ATMS soundness invariant ("no environment in any label is a superset of a nogood", de Kleer p.144) does not hold. The fix requires interleaving nogood updates with propagation, the way Forbus's `UPDATE` does.

3. **Hard cap raises mid-build.** `max_iterations=10_000` (`atms.py:1284-1290`) raises `EnumerationExceeded` instead of returning a partial result. For a store that genuinely needs a long fixpoint, the engine becomes unusable. The Zilberstein 1996 citation in the docstring describes anytime computation, but raising is not anytime — it is failing.

4. **Multi-consequent justification is dead code.** `ATMSJustification.consequent_ids: tuple[str, ...]` (`atms.py:285-289`) supports multiple consequents, but `_add_justification` always sets it to a 1-tuple (`atms.py:1605`). `_explain_justification` (`atms.py:2284, 2326, 2334`) reads `consequent_ids[0]` unsafely; an externally constructed 0-tuple would `IndexError`. Either collapse to `consequent_id: str` or actually support the general case.

5. **Construction-order dependency.** `_build_claim_nodes_and_justifications` runs *before* `_build_micropublication_nodes_and_justifications` (`atms.py:1278-1280`), so first-pass justifications cannot reference micropub-derived nodes. Subsequent fixpoint iterations re-propagate from scratch, so this is masked — but it makes the build sequence load-bearing for correctness.

6. **`combine_labels` re-normalises on every multiplication step** (`labels.py:265-282`). For a justification with k antecedents each carrying e environments, the engine performs k normalisations of size up to e^k. de Kleer's WEAVE only normalises once at the end. This is the single hottest correctness-irrelevant slowdown.

7. **`_exact_antecedent_sets` linear-scans `self._nodes` per condition** (`atms.py:1571-1577`), called per claim and per parameterization. With C claims, P parameterizations, K average conditions per claim, and N total nodes, the build is O((C+P)·K·N). At even a few thousand claims this is the dominant cost.

## Nogood handling correctness

`core/labels.py:NogoodSet` is structurally sound. It stores `ProvenanceNogood`s as squarefree polynomial variable sets. `excludes(env)` works via `live(_environment_to_polynomial(env), self.provenance_nogoods).terms` (`labels.py:97-99`), and `live` (`provenance/nogoods.py:34-47`) filters terms whose squarefree support is a *superset* of any nogood. So de Kleer's "nogoods are closed under superset" (1986 p.148) is realised correctly through the polynomial layer. Subset minimality of stored nogoods is also enforced through `normalize_environments` (`labels.py:102-126`).

The bugs are in the *orchestration* around the NogoodSet, not the data structure:

8. **`_update_nogoods` accumulates without invalidation** (`atms.py:1481-1517`). It starts from `list(self.nogoods.environments)` and appends new ones derived from active conflicts. Old nogoods are never dropped, even if the conflict that caused them is no longer active. With monotonic assumption growth this is benign, but the propstore conflict pipeline does not guarantee monotonic conflict membership — `_runtime.conflicts()` reflects whatever the active claims/lifting say *now*. A nogood derived in pass N from a conflict that has been lifted away by pass N+1 lingers.

9. **NogoodSet rebuilt every pass with the full environment list** (`atms.py:1509`). Even when no new nogood is added but a duplicate is, equality may fail because of de-duplication ordering inside the polynomial layer. Worth a property test.

10. **Conflict-derived nogoods cross all label environments unconditionally** (`atms.py:1496-1499`). For a conflict between claims with |L_a| and |L_b| environments, `|L_a|·|L_b|` candidate nogoods are appended. No de-dup before NogoodSet construction. With wide labels this becomes the dominant memory/time cost.

11. **Empty-environment nogood is silently allowed.** Nothing special-cases the empty environment becoming a nogood (de Kleer p.157: "a contradiction of the empty environment indicates an error"). If two unconditionally-supported claims conflict, the resulting `EnvironmentKey(())` would be added to the nogood set; this would prune *every* label and give a silently universal-OUT engine with no error raised.

12. **No detection of contradiction nodes (`gamma_perp`).** The ATMS itself does not infer contradictions from justifications; it only consumes externally-supplied conflict witnesses. This is a load-bearing architectural choice — see "Principle drift" below.

13. **`_was_pruned_by_nogood` recurses through justifications without depth bound** (`atms.py:1696-1718`). Cycle protection by `_visited`, but on dense parameterization graphs the breadth is exponential. Called inside `_out_kind_for_node` which is called inside `node_status`, which is called per claim by `argumentation_state` and many other entry points. A single inspection on a deep graph can dominate runtime.

14. **`provenance/nogoods.py` is not the ATMS nogood module.** It is a polynomial-term filter (`live`) that supports `core.labels.NogoodSet`. The naming collision between two completely different "nogood" modules is a maintenance hazard. Recommend renaming the polynomial filter to `polynomial_filter.py` or merging it into `core/labels.py`.

## Bugs (HIGH/MED/LOW)

**HIGH — silent drop of non-numeric parameterization inputs.** `_materialize_parameterization_justifications` (`atms.py:1448-1477`) uses Python's `for...else` with `break` on bool/non-numeric values:

```
for concept_id, node_id in zip(...):
    raw_value = _node_value(self._nodes[node_id])
    if isinstance(raw_value, bool) or not isinstance(raw_value, int | float):
        break
    input_values[concept_id] = float(raw_value)
else:
    evaluation = evaluate_parameterization(...)
```

Categorical or structural-valued provider nodes silently produce no derived support. No log, no warning, no `ATMSDerivedNode` with a "could-not-evaluate" marker. Disagreement at the parameterization layer is invisible.

**HIGH — bounded replay claims more soundness than it delivers.** `node_stability`, `node_relevance`, and `node_interventions` cap future enumeration at `limit=8` by default (`atms.py:765-855`, etc.). `_iter_future_queryable_sets` (`atms.py:1841-1860`) iterates subsets in increasing width and stops when `count >= limit`. With limit=8 and 5+ queryables, the engine inspects a tiny fraction of the power set yet `is_stable` returns True if no flip is found among those 8. The docstring says "Whether the node keeps its current ATMS status in all bounded consistent futures" (`atms.py:771`); the doc says "stable across all bounded consistent futures" (`docs/atms.md:118`). These are unsound under-approximations and presented as facts. Either rename to `is_stable_within_limit` everywhere or document explicitly that the result is partial.

**HIGH — `_was_pruned_by_nogood` may report false negatives on cycles.** `atms.py:1700-1703` returns `False` when a node is re-visited. So a cycle of justifications all of which would be pruned by a nogood reports OUT as `MISSING_SUPPORT`, not `NOGOOD_PRUNED`. Intervention planning depends on this distinction (`_future_reaches_node_target` at `atms.py:2148-2152` requires `out_kind == NOGOOD_PRUNED` for OUT-targeted plans). Silent miscategorisation → silent missing intervention plans.

**MED — `_bound_environment_key` recomputes on every essential_support call.** `atms.py:1753-1760` is O(|env.assumptions|+|contexts|), invoked from `essential_support` (`atms.py:1085`), invoked per `node_status`, invoked from `argumentation_state` per claim. Cubic in claims for large assumption sets.

**MED — `_future_engine` rebuilds the full ATMS per future** (`atms.py:1862-1866`). `argumentation_state` (`atms.py:1184-1274`) computes futures, stability, relevance, witness_futures, and why_out for every claim in `claim_inspections`. Each call may trigger 8 full rebuilds per claim per analysis dimension. For N claims, this is O(N · 8 · 5) ≈ 40N rebuilds per `argumentation_state` invocation.

**MED — `_justification_id` collision risk.** `atms.py:1617-1625` builds the ID as `f"{informant}->{consequent_id}[{joined}]"` with comma-joined antecedents. No escaping. If any informant or assumption ID contains comma, `[`, `]`, or `->`, the ID becomes ambiguous. Should hash or use a structured key.

**MED — orchestrator silently downgrades when Z3 is unavailable.** `_build_condition_solver` (`orchestrator.py:116-121`) catches `ImportError` and returns `None`. `detect_conflicts` then passes `solver=None` to all detectors. `_expand_lifted_conflict_claims` (`orchestrator.py:154-158`) and the per-detector classifiers degrade silently to weaker comparisons. Z3 unavailability should be loud — without Z3 the entire conflict-classification story collapses to literal string compare.

**MED — `_evaluate_parameterization_with_registry` swallows `AssertionError` and `ImportError`.** `parameterization_conflicts.py:48-54, 280-287`. AssertionError catches mask invariant violations; ImportError catches mask config bugs. Should propagate.

**MED — `_merge_contexts_for_derivation` silently drops state on incoherent context.** `parameterization_conflicts.py:170-190, 292`. Returns `_INCOHERENT_CONTEXT`, caller drops. No record. Context disagreement is invisible.

**MED — `_direct_state_for_claim` silently drops wide-interval claims.** `parameterization_conflicts.py:213-214`. `if abs(hi - lo) >= DEFAULT_TOLERANCE: return None`. Defeasible (interval) claims never participate in transitive derivation. They cannot conflict, cannot be conflicted with — they are excluded from ATMS-feeding conflict detection. This is the single most direct violation of the project non-commitment principle.

**MED — `algorithms.detect_algorithm_conflicts` silently skips parse failures.** `algorithms.py:46-54`. ValueError, SyntaxError, AlgorithmParseError, RecursionError → log warning, skip the pair. No ConflictRecord with class UNKNOWN. Two algorithm claims that the parser cannot compare are silently treated as compatible.

**MED — `equations.detect_equation_conflicts` compares canonical strings via `==`.** `equations.py:51`. If canonicalization is non-deterministic across sympy versions or symbol orderings, equivalent equations would be reported as conflicts and vice versa.

**MED — `_detect_transitive_conflicts_for_claims` magic iteration cap.** `parameterization_conflicts.py:548`: `max_iterations = len(group) * 4`. No justification for the constant. For a group of 5 concepts with 6 edges in a chain, 20 iterations may not reach fixpoint and the loop exits silently with derived states missing.

**MED — `detect_conflicts` injects synthetic concepts into the CEL registry that may shadow real names.** `orchestrator.py:43-66`. Adds `__source__`, `__domain__`, `__source_kind__`, `__origin_type__`, `__name__` and uses canonical names `source`, `domain`, `source_kind`, `origin_type`, `name`. If a real concept's `canonical_name` is `name`, `domain`, etc., behaviour depends on how `with_synthetic_concepts` resolves the collision. Loud failure on collision is safer than silent shadowing.

**MED — orchestrator-level mutation of the `records` list.** `orchestrator.py:106-112` passes `records` (a mutable list) into `_detect_parameterization_conflicts`, which appends in place with no return value. Side-effect orchestration; isolated testing requires pre/post inspection of a captured list.

**MED — `_expand_lifted_conflict_claims` `seen` key omits warning class and value.** `orchestrator.py:140-147`. Key is `(claim_id, context_id, conditions)`. If two distinct lifted versions differ only in some other field (e.g. derivation chain), one is dropped.

**MED — `consistency.py:50` uses `"?"` placeholder for `warning_class` when `None`.** Stringly-typed sentinel that callers may confuse with the legitimate string "?" if it ever appeared in `ConflictClass`. Use the enum's `MISSING` member or an explicit tag.

**LOW — `cel_to_binding` decimal heuristic.** `labels.py:222-224`. `if "." in raw: float else int` — coerces strings like `"1.0"` to float and `"1"` to int. The same value re-rendered may not round-trip. Unlikely to cause a correctness bug today but a foot-gun.

**LOW — `_normalize_value` keeps bool as bool, but `_value_key` then JSON-encodes it.** `atms.py:1631-1640`. A bool-valued claim and an int-valued claim with `True` vs `1` produce different derived-node IDs. Probably intentional but worth a test.

**LOW — `assignment_selection_merge.claim_distance` returns `0.0` for equal non-numeric values, `1.0` otherwise.** `assignment_selection_merge.py:39-51`. Hamming distance on heterogenous types — comparing `True` to `"True"` returns `1.0`. Not necessarily wrong, but worth documenting.

**LOW — `enumerate_candidate_assignments` may return `tuple()` (no candidates) when any concept has no observed values.** `assignment_selection_merge.py:133-134`. Fine. But the caller `solve_assignment_selection_merge` then returns `admissible_count=0, total_candidate_count=len(candidates)=0` — the result reason is "no admissible assignments" even though the actual cause was "no candidates". Telemetry confusion.

## Missing TMS variants / features

- **No incremental PROPAGATE/UPDATE/WEAVE.** propstore's ATMS is a batch-rebuild engine. Forbus's incremental architecture is missing. This makes interactive use (rule firing on label change) impossible.

- **No consumer architecture (Forbus Ch. 8/14).** No analog of `:condition :pattern :options` consumer triggers. Justifications are static at build time.

- **No focus environments (Forbus Ch. 14).** The ATRE focus mechanism (`in-rules`/`imp-rules`/`intern-rules`) for many-worlds-vs-focused control is absent.

- **No `interpretations` procedure.** de Kleer 1986 §6 / Forbus 12.3 define `interpretations(choice_sets, defaults) → maximal-consistent-environments`. propstore's `argumentation_state` returns inspection records, not interpretations. Diagnosis-style minimal-cardinality-cover queries cannot be answered directly.

- **No assumption garbage collection** (de Kleer 1986 p.158). Assumptions are added to the environment but never removed when their singleton becomes nogood or when all consequents are TRUE/false. Long-lived stores leak.

- **No bit-vector environment representation** (de Kleer 1986 p.157). EnvironmentKey is `tuple[str, ...]`. Subset test is O(n) set comparison. de Kleer specifies bit-vector AND/NOT for O(1). For thousands of assumptions this is the difference between usable and unusable.

- **No three-valued (McAllester 1978) variant.** There is no genuine UNKNOWN distinct from OUT. propstore's `ATMSOutKind` (MISSING_SUPPORT vs NOGOOD_PRUNED) is a finer split of OUT but does not capture "we have no information either direction" as McAllester does.

- **No CP (Conditional Proof) justifications** (Doyle 1979). Hypothetical reasoning under temporary assumptions is not represented.

- **No CMS / prime-implicate extension** (Forbus Ch. 13). Cannot derive nogoods from disjunctive justifications.

- **No DATMS / distributed variant** (Mason 1989).

- **No BMS / continuous belief variant** (Falkenhainer 1987). Confidence intervals are dropped at the parameterization layer (`_direct_state_for_claim` MED bug above) rather than treated as graded support.

## Conflict_detector orchestrator concerns

**Order dependency and shared mutable state.** `detect_conflicts` calls detectors in a fixed sequence (parameter, measurement, equation, algorithm, parameterization) and accumulates into one `records` list. Each detector dedups internally with its own keys; the orchestrator does not dedup across detectors. Two detectors emitting overlapping records produce duplicates downstream.

**Lifting expansion runs once.** `_expand_lifted_conflict_claims` (`orchestrator.py:124-182`) expands the claim list once at the top of `detect_conflicts`. Subsequent detectors inspect the expanded list, but their per-pair context classification calls `_classify_pair_context` independently with the same `lifting_system`. There is no shared cache of lifting decisions — Z3 disjointness queries are reissued per pair per detector.

**Synthetic concept injection mutates registry semantics for downstream consumers.** Adding `__source__` and friends *before* building the Z3 solver means the solver treats `source == 'paperX'` as an enum comparison. Any other downstream consumer of `cel_registry` that received the original (non-synthetic) registry may interpret the same expressions differently. The registry returned by `with_synthetic_concepts` is rebound locally, so the original registry should be unaffected — but verify this; if it mutates, the bug surface is broad.

**Z3 RuntimeError fail-fast aborts the whole detector.** `parameter_claims.py:53-57` re-raises Z3 exceptions as RuntimeError. A single Z3 hiccup on one concept group aborts the entire run. Per-group fault isolation would let partial detection complete.

**No race conditions** (single-threaded), but **non-deterministic ordering**: `_iter_unique_concepts` iterates `concept_registry.values()` which preserves insertion order in CPython 3.7+ but ordering is implicit and load-bearing. Snapshot-test results may break across runs that reorder concept registration.

**No back-pressure on combinatorial explosion.** `_detect_parameterization_conflicts` iterates `for input_states in product(*input_state_lists)` (`parameterization_conflicts.py:458`) with no max-product guard. With wide input sets this is unbounded.

## Principle drift (non-commitment, defeasible imports)

The project memory (`feedback_imports_are_opinions.md`) states that every imported KB row is a defeasible claim with provenance, never truth — no source is privileged. The cluster contains multiple violations where disagreement is silently collapsed instead of recorded as defeasible:

1. `_materialize_parameterization_justifications` drops non-numeric provider values (HIGH bug above) — categorical claims are silently excluded from derivation.

2. `_direct_state_for_claim` drops wide-interval claims — interval (defeasible) claims are silently excluded from transitive conflict detection.

3. `_merge_contexts_for_derivation` returns `_INCOHERENT_CONTEXT` and the caller drops the derivation — no `ConflictRecord` is produced even though the inability to merge contexts IS a defeasible disagreement.

4. `algorithms.detect_algorithm_conflicts` silently skips parse-failure pairs — the disagreement "we cannot tell whether these algorithms are equivalent" is collapsed to "compatible".

5. `_evaluate_parameterization_with_registry` swallows `AssertionError`, `ImportError`, `ZeroDivisionError`, `TypeError`, `ValueError` (`parameterization_conflicts.py:48-54, 280-287`). Failures collapse to `None` and the derivation is dropped silently.

6. `equations.detect_equation_conflicts` compares canonicalized form via `==`. Non-canonicalizable equation pairs are dropped (line 47-50) with a logger warning, not recorded. Same collapse.

7. `_was_pruned_by_nogood` returning `False` on cycles silently mis-classifies OUT nodes, which collapses the reason for non-belief.

8. The bounded-replay `is_stable` family returning `True` when only 8 of 2^k subsets were enumerated collapses uncertainty into a confident "yes".

9. The Z3-unavailable silent downgrade (`_build_condition_solver` returns `None`) collapses Z3-decidable disagreement into stringly-typed weak compares.

10. `consistency.py:53` represents an unknown warning class as the literal string `"?"`. A missing classification is a defeasible "we don't know" — but the placeholder is indistinguishable from a real (legitimate) value.

The cluster does have one explicit non-commitment surface that works correctly: the ATMS preserves all justification paths in a label and exposes `OUT(MISSING_SUPPORT)` vs `OUT(NOGOOD_PRUNED)` distinctly. So the *core data structure* respects the principle; the *orchestration on top of it* does not.

## Open questions for Q

1. **Is bounded replay's `limit=8` default a soundness or a usability guarantee?** Currently the engine returns `True` from `is_stable` when only 8 of 2^k subsets have been examined and all 8 happened to agree. If this is intended as "best-effort within limit", method names should make that explicit (`stable_within_limit`, `relevance_witnesses_within_limit`). If it is intended as soundness, the limit needs to be removed or the semantics changed (e.g. return `Unknown` when the search was truncated).

2. **Should `_update_nogoods` be monotonic across the lifetime of the engine, or recomputed per build?** Currently it accumulates within one engine instance; replays start fresh. The semantics for "a nogood was derived from a conflict that has been lifted away" are unspecified.

3. **Is the multi-consequent justification field intentionally dead code, or a stub for a future feature?** If dead, drop `consequent_ids` and use `consequent_id`. If planned, add a test that exercises it.

4. **Should the Z3-unavailable path be a hard error?** Current silent degradation hides what is likely a deployment/install bug. A clear `ConflictDetectorRequiresZ3` exception at `detect_conflicts` entry would surface it immediately.

5. **Is the empty-environment-as-nogood case a real risk?** If two unconditional claims can ever conflict, the engine would silently nullify all labels. Worth a defensive assertion.

6. **`_direct_state_for_claim` excludes wide intervals.** Is the intent "intervals are non-points and so cannot conflict" (a documented semantic choice) or an oversight? Intervals are exactly the defeasible content the non-commitment principle says should be preserved.

7. **Should `argumentation_state` be split?** It currently runs futures/stability/relevance/witnesses/why_out/intervention for every claim — easily an O(N · 8 · 5) full-rebuild call. Lazy fields would let callers ask for the subset they actually need.

8. **`docs/atms.md` cites `propstore/world/labelled.py`** for `SupportQuality` and `combine_labels`/`merge_labels`. That file does not exist — these symbols live in `propstore/core/labels.py` and `propstore/provenance/support.py`. Stale doc, or symbols meant to be re-exported there?

9. **`docs/conflict-detection.md` lists six classes** but the orchestrator output is post-processed by other layers. Are `PHI_NODE` and `CONTEXT_PHI_NODE` records visible to the ATMS through `_runtime.conflicts()`? The doc says they do not generate defeats, but the ATMS `_update_nogoods` treats every `ConflictRowInput` from `_runtime.conflicts()` as a nogood-source. If `_runtime.conflicts()` filters by class, where? If it does not, PHI_NODEs become nogoods and silently prune labels that should remain `IN`.

10. **Should support_revision/operators.py incision-set search default to bounded enumeration?** `_choose_incision_set` (`operators.py:257-309`) iterates `combinations(candidates, size)` over all sizes; default `max_candidates=None` is unbounded. With ~30 candidates this is `2^30` worst case. The `EnumerationExceeded` overload exists but is not used by `contract`/`revise`. Dangerous default.
