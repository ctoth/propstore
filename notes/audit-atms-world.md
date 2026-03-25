# ATMS & World Model Audit -- 2026-03-24

## Scope

Audit of ATMS engine, world model, labelled kernel, bound world, hypothetical world,
resolution, and value resolver against de Kleer 1986 and Dixon 1993.

Files reviewed:
- `propstore/world/atms.py` (~1450 lines)
- `propstore/world/model.py` (~634 lines)
- `propstore/world/hypothetical.py` (~175 lines)
- `propstore/world/bound.py` (~766 lines)
- `propstore/world/labelled.py` (~241 lines)
- `propstore/world/resolution.py` (~427 lines)
- `propstore/world/types.py` (~324 lines)
- `propstore/world/value_resolver.py` (~321 lines)
- `propstore/world/__init__.py` (~50 lines)
- `tests/test_atms_engine.py` (~1300+ lines)
- `tests/test_world_model.py` (~400+ lines)
- `tests/test_labelled_core.py` (~322 lines)
- `papers/Dixon_1993_ATMSandAGM/notes.md`

---

## Finding 1: ATMS Label Computation -- Minimality is Correct but Propagation is Batch-Only

**Severity: Observation (design limitation, not a bug)**

The `normalize_environments()` function in `labelled.py` (line 218-235) correctly
maintains minimality by deduplication, nogood pruning, and superset removal. The
implementation is sound against de Kleer 1986 Section 3 (label conditions 1-4):

1. Assumptions only -- enforced by `_build_assumption_nodes()` only creating nodes from `AssumptionRef` objects
2. Soundness -- `_propagate_labels()` only produces labels via cross-product of justified antecedents
3. Minimality -- `normalize_environments()` prunes supersets
4. Consistency -- nogoods are checked in `normalize_environments()` via `NogoodSet.excludes()`

However, label propagation (`_propagate_labels()`, atms.py line 844-882) is **batch
recomputation, not incremental**. Every call clears all non-assumption labels and
re-propagates from scratch. de Kleer 1986 describes an incremental update protocol
(Update procedure, Section 3.2) where adding a justification only updates affected
nodes. The batch approach is correct but O(n * j * e) per propagation where n=nodes,
j=justifications, e=environments.

The `_build()` method (line 784-794) loops `_propagate_labels + _materialize + _update_nogoods`
until fixpoint. This is correct for static graphs but would not scale to incremental use.

## Finding 2: Nogood Management is Sound but Incomplete for Derived-Derived Conflicts

**Severity: Medium**

`_update_nogoods()` (atms.py line 941-978) derives nogoods from `BoundWorld.conflicts()`,
which comes from the sidecar's precomputed `conflicts` table plus runtime
`_recomputed_conflicts()`. Nogoods are correctly computed as the cross-product union
of environments supporting conflicting claims.

**Gap**: Nogoods are only derived from claim-to-claim conflicts. If two derived nodes
for the same concept produce different values, no nogood is generated. The engine
materializes derived nodes (line 920) keyed by `derived:{concept}:{value}`, so two
different derived values for the same concept *can* coexist without generating a
nogood. This is a semantic gap: de Kleer's ATMS treats contradictions (nogoods) as
arising from the problem solver reporting them, so this is arguably correct -- the
problem solver (conflict detector) hasn't reported derived-vs-derived conflicts.
But it means the engine can hold two contradictory derived values with overlapping
support without detecting the inconsistency.

## Finding 3: Dixon 1993 Context Switching / AGM Revision is NOT Implemented

**Severity: Major (stated in CLAUDE.md as grounding but not implemented)**

The project's CLAUDE.md lists "Dixon 1993: ATMS context switching = AGM operations;
entrenchment from justification structure" as a key literature grounding. The actual
code does **none** of this:

1. **No entrenchment ordering**: There is no entrenchment function, no E1-E5 levels,
   no `Ent()` computation anywhere in the codebase.
2. **No AGM contraction**: There is no `contract()` or equivalent operation. BoundWorld
   is immutable after construction.
3. **No AGM expansion as context switch**: Adding assumptions requires constructing a
   new BoundWorld from scratch.
4. **No ATMS_to_AGM algorithm**: The translation algorithm from Dixon 1993 Section 4.3
   is not implemented.

The engine's docstring (atms.py line 1-12) is honest about this: "This remains a
bounded ATMS-native analysis over rebuilt future bound worlds rather than AGM-style
revision, entrenchment maintenance, or a full de Kleer runtime manager." So the code
itself does not overclaim. But the project's CLAUDE.md and architectural documentation
cite Dixon 1993 as grounding without distinguishing "cited as aspirational" from
"currently implemented."

The `essential_support()` method (atms.py line 571-598) implements Dixon's ES(p,E) =
intersection of FB(p,E), which is one piece of the Dixon framework. But the rest
(entrenchment encoding, contraction, expansion as environment changes) is absent.

## Finding 4: Hypothetical Reasoning is Additive-Only, Cannot Retract Assumptions

**Severity: Medium**

`HypotheticalWorld` (hypothetical.py) allows removing claims and adding synthetic
claims. But it operates as an overlay on a BoundWorld -- it cannot retract assumptions
from the underlying environment. This means:

- You can ask "what if claim X were removed?" (claim-level)
- You CANNOT ask "what if assumption A were no longer held?" (environment-level)

The `_future_engine()` method (atms.py line 1255-1298) builds future worlds by
**adding** queryable assumptions, never removing existing ones. The docstring calls
this "additive-only" which is honest. But this means the system cannot model AGM
contraction or genuine ATMS context switching (where you move from environment {a,b,c}
to {a,b}).

## Finding 5: Resolution is Correctly Render-Time

**Severity: No issue**

Per the project's design principle ("lazy until rendering, filtering at render time
not build time"), resolution is correctly implemented at render time:

- `resolve()` in `resolution.py` takes a `BeliefSpace` and applies strategy only
  when queried
- `BoundWorld.resolved_value()` delegates to `resolve()` at call time
- No resolution result is stored back into the sidecar or source storage
- Multiple `RenderPolicy` objects can be applied to the same `BoundWorld`

This is architecturally correct per the design checklist.

## Finding 6: Value Resolution Strategies -- Recency Tie-Breaking is Correct

**Severity: No issue for recency/sample_size; observation for argumentation**

- `_resolve_recency()` correctly returns `(None, reason)` on ties rather than picking
  arbitrarily (line 51-52)
- `_resolve_sample_size()` similarly handles ties (line 76)
- `_resolve_atms_support()` correctly filters to ATMS-supported claims only (line 267-283)
- `_resolve_praf()` uses probabilistic acceptance probabilities with tie detection

## Finding 7: Label Algebra -- `subsumes` Direction is Inverted from Intuitive Reading

**Severity: Low (correct but confusing)**

`EnvironmentKey.subsumes()` (labelled.py line 36-37):
```python
def subsumes(self, other: EnvironmentKey) -> bool:
    return set(self.assumption_ids).issubset(other.assumption_ids)
```

This means "self subsumes other" iff self is a **subset** of other. In de Kleer's
terminology, a smaller environment subsumes a larger one because the smaller one
supports a datum in more contexts. This is correct per de Kleer 1986 (a label
environment {A} subsumes {A,B} because anything supported under {A} is also
supported under {A,B}). But the name `subsumes` with `issubset` is easy to misread.

Used correctly in `normalize_environments()`:
```python
if any(existing.subsumes(candidate) for existing in minimal):
    continue  # skip candidate because a smaller env already covers it
```
This prunes supersets, keeping only minimal environments. Correct.

## Finding 8: No Bound/Interval Reasoning Module Exists

**Severity: Observation**

There is no `bound.py` implementing interval arithmetic. The file at
`propstore/world/bound.py` is `BoundWorld` (a condition-bound view), not
interval/bound reasoning. The `RenderPolicy` has `show_uncertainty_interval`
and the types module has `apply_decision_criterion()` for Josang opinion intervals
[Bel, Pl], but there is no general interval arithmetic module.

## Finding 9: `_propagate_labels()` Has Potential Quadratic Blowup

**Severity: Low (correctness OK, performance concern)**

In `_propagate_labels()` (atms.py line 844-882), on each iteration the code
iterates over ALL justifications in sorted order and for each one:
1. Collects antecedent labels
2. Computes `combine_labels()` (cross-product)
3. Merges into consequent's current label

The cross-product in `combine_labels()` can produce O(e^k) environments where e is
the number of environments per antecedent and k is the number of antecedents.
`normalize_environments()` prunes this, but the intermediate blowup happens first.

For the current use case (small numbers of assumptions and claims), this is fine. But
it would not scale to large ATMS problems.

## Finding 10: Test Coverage Gaps

**Severity: Medium**

### Well-covered:
- Label normalization (dedup, superset pruning, nogoods)
- Combined support through parameterization chains
- Nogood pruning of derived environments
- Order independence of label propagation
- Cycle detection (no self-bootstrapping)
- Semantic vs exact support distinction
- Context-scoped claim handling
- Essential support computation
- Future queryable activation
- Stability, relevance, interventions
- CLI integration

### Not covered:
1. **Multiple justifications for the same node with different environments**: The test
   `test_atms_essential_support_intersection_and_environment_queries_are_exact` has
   claim_y_a and claim_y_b providing alternative support for concept2, and the derived
   node gets two environments. But there is no test for a claim node itself having
   multiple justifications (e.g., a claim with conditions ["x == 1"] where two different
   assumptions both match "x == 1").

2. **Nogood cascading**: No test verifies that when a nogood prunes an intermediate
   node's label, downstream nodes that depend on it also lose their support. The
   `_propagate_labels()` recomputes from scratch each time, so this should work by
   construction, but it's untested.

3. **Empty parameterization results**: No test for `evaluate_parameterization` returning
   `None` (e.g., division by zero) during ATMS materialization. Line 914-915 handles it
   with `continue`, but no test exercises this path.

4. **HypotheticalWorld + ATMS interaction**: `HypotheticalWorld` creates its own
   `ActiveClaimResolver` but does not have an ATMS engine. If someone calls
   `resolved_value()` on a hypothetical world with an ATMS backend policy, it would
   go through `resolve()` which calls `view.atms_engine()` -- but HypotheticalWorld
   has no `atms_engine()` method. This would raise `AttributeError` at runtime.

5. **Large environment spaces**: No test with more than ~3 assumptions. The
   `_iter_future_queryable_sets` enumerates combinations up to `limit`, but there is
   no test verifying behavior when the combinatorial space exceeds the limit.

6. **Concurrent access**: `WorldModel` holds a raw `sqlite3.Connection` with no
   thread safety. The `_table_cache`, `_solver`, `_registry` are all lazily initialized
   without locks.

## Finding 11: `is_active` Returns True When No Bindings Exist

**Severity: Medium (design question)**

In `BoundWorld.is_active()` (bound.py line 186):
```python
if not self._binding_conds:
    return True  # no bindings -> everything active
```

When a BoundWorld is created with no bindings and no context, ALL claims are active
regardless of their conditions. This means an unbound query treats conditional claims
as active even when their conditions are not satisfied. This is defensible ("if we
don't know, don't exclude") but surprising -- a claim conditioned on "task == 'speech'"
would be active even when no task is specified.

## Finding 12: `_future_engine` Bypasses WorldModel.bind()

**Severity: Low**

`_future_engine()` (atms.py line 1255-1298) constructs a new BoundWorld directly via
`self._bound.__class__(...)` rather than going through `WorldModel.bind()`. This means
the future engine does not get:
- Context hierarchy effective_assumptions computation
- The `compile_environment_assumptions` call that `WorldModel.bind()` does

However, the future engine manually constructs the environment with future assumptions
already compiled (line 1259-1273), so this appears to be intentional -- the future
engine adds assumptions directly rather than re-deriving them from context hierarchy.

## Finding 13: `_was_pruned_by_nogood` Can Stack Overflow on Deep Justification Chains

**Severity: Low**

`_was_pruned_by_nogood()` (atms.py line 1152-1174) recurses through antecedents with
cycle detection via `_visited`. But it uses Python recursion, not an explicit stack.
For deeply nested justification chains, this could hit Python's default recursion limit
(1000). Given the current data sizes this is unlikely, but it is an architectural
fragility.

## Finding 14: HypotheticalWorld.conflicts() Can Miss Synthetic-vs-Synthetic Conflicts

**Severity: Low**

`HypotheticalWorld.conflicts()` (hypothetical.py line 96-110) filters base conflicts
by removed IDs, then adds recomputed conflicts from `_recomputed_conflicts()`. But
`_recomputed_conflicts()` calls `detect_conflicts()` which requires `LoadedClaimFile`
format with a `filepath` field. Synthetic claims converted via `_synthetic_to_dict()`
may not have all fields expected by `detect_conflicts()`. The `recompute_conflicts()`
method (line 119-151) exists as an alternative that does simple value comparison, but
`conflicts()` uses the more complex path.

---

## Summary

| # | Finding | Severity |
|---|---------|----------|
| 1 | Label computation correct but batch-only (not incremental per de Kleer) | Observation |
| 2 | No nogoods for derived-vs-derived conflicts of same concept | Medium |
| 3 | Dixon 1993 (AGM/entrenchment) is cited as grounding but not implemented | Major |
| 4 | Hypothetical reasoning is additive-only, no assumption retraction | Medium |
| 5 | Resolution is correctly render-time | No issue |
| 6 | Value resolution strategies correctly handle ties | No issue |
| 7 | `subsumes` naming is correct but counterintuitive | Low |
| 8 | No interval arithmetic module exists | Observation |
| 9 | Cross-product label propagation has potential combinatorial blowup | Low |
| 10 | Test gaps: nogood cascading, HypotheticalWorld+ATMS, empty params | Medium |
| 11 | Unbound queries treat all conditional claims as active | Medium |
| 12 | `_future_engine` bypasses `WorldModel.bind()` | Low |
| 13 | Recursive `_was_pruned_by_nogood` can stack overflow | Low |
| 14 | HypotheticalWorld.conflicts() may miss synthetic conflicts | Low |
