# WS-I: ATMS / world correctness

**Status**: CLOSED 6a6cc9d6
**Depends on**: WS-D (math/operator naming — CEL semantic equality overlaps; the ATMS condition-matching fix at `atms.py:1562` reuses the canonical CEL pipeline that WS-D stabilises)
**Blocks**: WS-J formally, WS-J2 via WS-J, and practical trust in WS-F (ASPIC) and WS-K (heuristic discipline). Every consumer of `ATMSEngine.argumentation_state` (`worldline`, `support_revision`, `app/world_atms.py`, the `pks world` CLI surfaces, the ASPIC bridge that lifts `OUT(NOGOOD_PRUNED)` into defeats) is currently reading values that this workstream proves are wrong.
**Owner**: Codex implementation owner + human reviewer required

---

## Why this workstream exists

The ATMS is the load-bearing belief substrate. Every "is this claim IN?", "what minimal assumption set supports it?", "what would have to change for it to flip?", "which derived values conflict?" answer comes out of `ATMSEngine`. Cluster E's full read turned up three classes of failure the engine cannot recover from on its own:

1. **Soundness overclaim.** `is_stable`, `node_relevance`, `node_interventions` are documented as ranging over "all bounded consistent futures" but visit ≤8 subsets of a power set frequently containing thousands. A `True` from `is_stable` is consistent with demonstrable instability at subset 9. Downstream code treats it as fact.
2. **Mis-classification at the OUT/IN boundary.** `_was_pruned_by_nogood` returns `False` on DFS cycle re-visit regardless of what consistent resolution would conclude. Cyclic justification graphs collapse to `OUT(MISSING_SUPPORT)`. `_future_reaches_node_target` switches on `out_kind == NOGOOD_PRUNED` (`atms.py:2148-2152`); wrong discriminator → planner silently proposes no plan.
3. **Disagreement-collapse at the orchestration boundary.** Per the non-commitment principle (`feedback_imports_are_opinions.md`), every imported value is a defeasible claim. `_materialize_parameterization_justifications` drops categorical inputs (HIGH); `value_resolver` returns first-compatible without checking contradictory later candidates (Codex #24); environment serialisation strips contexts (Codex #25); antecedent matching uses raw CEL string equality (Codex #26). The substrate that should *preserve* disagreement is collapsing it.

WS-I makes ATMS output mean what its docstrings say it means.

## Review findings covered

| Finding | Source | Citation | Description |
|---|---|---|---|
| **E.H1a** | Cluster E HIGH | `atms.py:765-855`, `:1841-1860`; `docs/atms.md:118` | `is_stable(node)` enumerates ≤ `limit=8` subsets and presents the result as a soundness fact. Docstring promises "all bounded consistent futures." Per Codex 2.9 this is **interface replacement, not rename**: the old bounded `is_stable(node)` API is **deleted**; a new unbounded `is_stable(node, limit=None)` is added with explicit budget semantics. |
| **E.H1b** | Cluster E HIGH | `atms.py:765-855`, `:1841-1860` | `node_relevance(node)` silently truncates at 8 subsets. Same fix shape as E.H1a — delete the old bounded API; add `node_relevance(node, limit=None)`. |
| **E.H1c** | Cluster E HIGH | `atms.py:765-855`, `:1841-1860` | `node_interventions(node)` silently truncates at 8 subsets. Same fix shape — delete the old bounded API; add `node_interventions(node, limit=None)`. |
| **E.H2** | Cluster E HIGH | `atms.py:1696-1718`, `:1700-1703`; consumer `:2148-2152` | `_was_pruned_by_nogood` returns `False` on cycle re-visit, so cyclic NOGOOD_PRUNED becomes MISSING_SUPPORT, suppressing intervention plans. |
| **E.H3** | Cluster E HIGH | `atms.py:1448-1477` | `_materialize_parameterization_justifications` silently breaks out of the for-loop on bool/non-numeric provider values; categorical claims produce no derivation, no `ATMSDerivedNode`, no log. |
| **E.M1** | Cluster E MED | `atms.py:1284-1290`, `:1276-1297` | `max_iterations=10_000` raises `EnumerationExceeded` instead of returning anytime partial result. |
| **E.M2** | Cluster E MED | `atms.py:285-289`, `:1605`, `:2284`, `:2326`, `:2334` | Multi-consequent justification field is dead code; collapse to `consequent_id: str` or actually exercise it. |
| **E.M3** | Cluster E MED | `atms.py:1382-1420` vs `:1294`, `:1481-1517` | Stale-nogood window inside a single propagation pass (nogood update happens only between passes). Interleave per Forbus `UPDATE`. |
| **E.M4** | Cluster E MED | `conflict_detector/orchestrator.py:43-66`, `:106-112`, `:124-182`, `:140-147` | Orchestrator concerns: synthetic-concept shadowing of registry, mutable-list injection, lifting-decision cache absent, and the `seen` key drops derivation provenance. |
| **Codex #24** | Codex ws-05 (line 8, 51-57) | `atms.py:1481-1517` (only direct-claim conflicts feed `_update_nogoods`); `world/value_resolver.py:166-178` | Derived-vs-derived contradictions are hidden, not nogoods. The first compatible candidate wins; later candidates that disagree never trigger a `ConflictRecord`, never feed the ATMS. |
| **Codex #25** | Codex ws-05 (line 6, 41-44) | `atms.py:2369-2372`, `:2375-2381`, `:2383-2387`; `app/world_atms.py:195-197` | `_serialize_environment_key` returns `list(environment.assumption_ids)`, dropping context IDs. Status/explain/JSON/CLI surfaces report environments as assumption-only even when contexts were load-bearing. |
| **Codex #26** | Codex ws-05 (line 7, 46-49) | `atms.py:1562`, full `_exact_antecedent_sets` block `:1559-1584` | Exact antecedent matching does `assumption.cel == condition` raw string equality. Two CEL conditions that the runtime considers active-equivalent under canonicalisation produce distinct antecedent sets, so identical support is split into incomparable nodes. |
| **gaps.md** | Cluster E principle drift | n/a | Items 1, 2, 7, 8 in cluster-E.md "Principle drift" — non-commitment violations through silent disagreement-drop. Promote each to a `gaps.md` row with this WS as owner. |

Adjacent findings closed in the same WS because the touch-surface overlaps:

| Finding | Citation | Why included |
|---|---|---|
| Direct-claim-only `BoundWorld.conflicts` | `world/bound.py:299`, `:920` | The ATMS reads `_runtime.conflicts()`. Once derived-vs-derived emit conflicts, `BoundWorld.conflicts` has to expose them or the propagation never sees them. |
| `value_resolver._derive_from_parameterization` first-wins selection | `world/value_resolver.py:166-178` | The exact site that swallows the second compatible candidate. Has to change to "collect all, decide, conflict if disagree." |
| `_support_ids` context-stripping | `app/world_atms.py:195-197` | App-layer mirror of `_serialize_environment_key`'s bug. Same fix shape. |

Out of scope (explicitly deferred):

- **Incremental WEAVE/UPDATE/PROPAGATE** (Forbus 1993 Ch. 12). Tier 6 spike `T6.3` — multi-week rewrite. WS-I makes the *batch* engine sound, not incremental.
- **Bit-vector environments** (de Kleer 1986 p.157). Same Tier 6 spike.
- **Consumer / focus / interpretations / CMS / DATMS / BMS variants.** Coverage gaps from cluster-E "Missing TMS variants"; each is its own future WS, not this one.
- **`provenance/nogoods.py` rename.** Naming hazard cluster-E flagged; trivial cleanup that lives in WS-N (architecture).

## Code references (verified by direct read at master `94486356`)

### Soundness overclaim (E.H1a/b/c)
- `propstore/world/atms.py:765-855` — `is_stable`, `node_relevance`, `node_interventions` definitions; each takes a `limit: int = 8` parameter that is forwarded into `_iter_future_queryable_sets`. The current callers receive a silently-truncated result with no exception, no marker, no way to distinguish a sound `True` from a bounded `True`.
- `propstore/world/atms.py:1841-1860` — `_iter_future_queryable_sets` iterates `combinations(queryables, width)` for increasing `width` and stops when `count >= limit`.
- `docs/atms.md:118` — public docstring "stable across all bounded consistent futures." This is the false claim — the implementation is bounded by `limit`, not by feasibility.
- Consumer surfaces: `propstore/world/atms.py:1184-1274` (`argumentation_state`) calls all three per claim. `worldline`, `support_revision`, the ASPIC bridge, and the `pks world` CLI surfaces all read these values.

### OUT-kind cycle bug (E.H2)
- `propstore/world/atms.py:1696-1718` — `_was_pruned_by_nogood`. Lines 1700-1703 return `False` on `node_id in _visited`.
- `propstore/world/atms.py:2148-2152` — `_future_reaches_node_target` discriminates `out_kind == NOGOOD_PRUNED`. Wrong classification → no plan.

### Categorical-input drop (E.H3)
- `propstore/world/atms.py:1448-1477` — for/else with `break` on `isinstance(raw_value, bool) or not isinstance(raw_value, int | float)`. The `else` clause (which calls `evaluate_parameterization`) is silently skipped.

### Derived-vs-derived hidden (Codex #24)
- `propstore/world/atms.py:1481-1517` — `_update_nogoods` reads `self._runtime.conflicts()`. That iterator exposes only direct-claim conflicts (`world/bound.py:299`, `:920`); no derived-derived rows pass through it.
- `propstore/world/value_resolver.py:166-178` — `for param in params:` returns the first `ValueStatus.DERIVED` candidate. Subsequent compatible candidates that would derive a contradictory value are never inspected.

### Context loss in serialisation (Codex #25)
- `propstore/world/atms.py:2369-2372` — `_serialize_environment_key` returns `list(environment.assumption_ids)`. `EnvironmentKey` carries both `assumption_ids` and `context_ids` (per `core/labels.py`); only the first half survives serialisation.
- `propstore/world/atms.py:2375-2381` — `_serialize_label` calls the same helper per environment, propagating the loss.
- `propstore/world/atms.py:2383-2387` — `_serialize_nogood_detail` does its own `list(environment.assumption_ids)` — the bug repeats.
- `propstore/app/world_atms.py:195-197` — `_support_ids(support)` calls `getattr(support, "assumption_ids", ())` only. Independent code path, same shape, same bug.

### Raw CEL equality (Codex #26)
- `propstore/world/atms.py:1562-1584` — `_exact_antecedent_sets`. Line 1576: `assumption.cel == condition`. Plain string compare against a JSON-loaded list. Two semantically-equal CELs (`a == b` vs `b == a`, whitespace differences, etc.) produce zero matches.

### Conflict orchestrator (E.M4)
- `propstore/conflict_detector/orchestrator.py:43-66` — synthetic concept injection (`__source__`, `__domain__`, …) into the registry.
- `propstore/conflict_detector/orchestrator.py:106-112` — `records` list passed mutably into `_detect_parameterization_conflicts`.
- `propstore/conflict_detector/orchestrator.py:124-182` — `_expand_lifted_conflict_claims`; the `seen` key at `:140-147` is `(claim_id, context_id, conditions)` and ignores derivation chain.
- `propstore/conflict_detector/parameter_claims.py:53-57` — Z3 `RuntimeError` aborts the whole detector instead of degrading per-group.

### Engine global rebuild (E.M1, E.M3)
- `propstore/world/atms.py:1276-1297` — outer `while True:` rebuild loop with `max_iterations=10_000`.
- `propstore/world/atms.py:1382-1420` — `_propagate_labels` wipes labels then refills.
- `propstore/world/atms.py:1481-1517` — nogood update runs only after a full propagation pass.
- `propstore/world/atms.py:285-289`, `:1605`, `:2284`, `:2326`, `:2334` — `consequent_ids` tuple field is read at index 0 unsafely; only ever written as a 1-tuple.

## First failing tests (write these first; they MUST fail before any production change)

Each test gets a docstring naming its finding ID and citing the file:line of the bug.

1. **`tests/test_atms_unbounded_stability_api.py`** (new — covers E.H1a/b/c)
   - **New API contract** (the test pins the contract before any implementation runs):
     - `is_stable(node, limit=None)` returns `bool` when `limit=None` and the unbounded enumeration completes; the result is sound over the full power set of queryables.
     - `is_stable(node, limit=N)` returns `bool` if the verdict is determined within `N` examined subsets; otherwise raises `BudgetExhausted(examined=N, total=...)` carrying both counts. The exception is **not** suppressed by the caller's default-handling; the budget is a real constraint and exhaustion is a real signal, never a silent under-approximation.
     - Identical contract for `node_relevance(node, limit=None)` and `node_interventions(node, limit=None)`.
   - **Caller-shape assertions**: AST-walk `propstore/` and assert no module imports or calls these three names with the old single-positional shape (`is_stable(node)` with no `limit` kwarg). Every call site either passes `limit=None` (accepting the unbounded semantics) or passes `limit=N` (and a try/except for `BudgetExhausted` is statically present in the same function — verified by AST walk for `try`/`except BudgetExhausted` framing the call). No call site passes the old shape.
   - **Soundness assertion (limit=None branch)**: build an engine with K=12 queryable assumptions where a known bit pattern at subset index 9 flips the label. Call `is_stable(node, limit=None)`; assert the result is `False` (the unbounded check sees subset 9 and returns the correct verdict). This is the assertion the old bounded `limit=8` code silently got wrong.
   - **Budget-exhaustion assertion (limit=8 branch)**: same engine; call `is_stable(node, limit=8)`; assert it raises `BudgetExhausted(examined=8, total=4096)`. Not a `True`/`False` return. The exception type is the visible signal that the caller's budget was the constraint.
   - **Old-API-deletion assertion**: importing `propstore.world.atms` and calling `engine.is_stable(node)` (no kwarg) raises `TypeError` because the new signature requires the `limit` keyword. Same for `node_relevance` and `node_interventions`. The old bounded-with-default-8 API is **gone**, not aliased.
   - **Must fail today**: the old API exists and accepts `is_stable(node)` returning a silently-truncated `True`. There is no `BudgetExhausted` exception class. There is no unbounded mode.

2. **`tests/test_atms_was_pruned_by_nogood_cycle.py`** (new — covers E.H2)
   - Build a parameterization graph with two derived nodes `D1, D2` whose justifications form a cycle, both pruned by the same nogood. Assert `_out_kind_for_node(D1) == NOGOOD_PRUNED` and that `node_interventions(D1, limit=None)` proposes a plan that targets the nogood.
   - **Must fail today**: cycle re-visit returns `False`, OUT becomes `MISSING_SUPPORT`, no plan.

3. **`tests/test_atms_categorical_provider_visibility.py`** (new — covers E.H3)
   - Configure a parameterization whose input concept has only a string-valued provider (`"red"`). Assert one of:
     - The engine emits an `ATMSDerivedNode` with status `OUT(MISSING_SUPPORT)` and a `reason` recording the categorical-input rejection, OR
     - The engine emits a `ConflictRecord(class=PARAMETERIZATION_INPUT_TYPE)` referencing the provider.
   - **Must fail today**: silent drop, no node, no record, no log.

4. **`tests/test_atms_derived_contradictions.py`** (canonical first failing test from REMEDIATION-PLAN Part 4 WS-I — covers Codex #24)
   - Configure two parameterizations P1, P2 deriving the same target concept under compatible (overlapping) assumption sets. P1 derives value `1.0`, P2 derives `2.0`. Assert `_runtime.conflicts()` exposes a derived-derived `ConflictRecord` and that after the next ATMS rebuild, the derived nodes' label environments are mutually nogood (i.e. `EnvironmentKey({a1, a2})` ∈ `engine.nogoods.environments`).
   - **Must fail today**: `value_resolver` returns the first compatible candidate (P1's `1.0`), the second is never examined, no conflict, no nogood.

5. **`tests/test_atms_environment_context_serialisation.py`** (new — covers Codex #25)
   - Build an environment with assumption IDs `{a1}` and context IDs `{c1}`. Call `_serialize_environment_key` and assert both halves survive — either as a structured dict `{"assumption_ids": [...], "context_ids": [...]}` or as a flat list with stable prefixed IDs (`assumption:a1`, `context:c1`). Mirror the assertion for `_serialize_label`, `_serialize_nogood_detail`, and `app/world_atms.py:_support_ids`.
   - **Must fail today**: all four call sites strip contexts.

6. **`tests/test_atms_cel_semantic_equality.py`** (new — covers Codex #26)
   - Two assumptions A1, A2 with CEL strings `a == b` and `b == a` respectively. Both are runtime-active. A parameterization condition references `a == b`. Assert `_exact_antecedent_sets` returns *both* antecedent sets (or one canonicalised set covering both nodes).
   - **Must fail today**: raw `==` matches only A1's exact spelling.

7. **`tests/test_atms_max_iterations_anytime.py`** (new — covers E.M1)
   - Configure a small store that reaches fixpoint in 3 iterations; pass `max_iterations=2` and assert the engine returns the partial state with a marker (`engine.fixpoint_reached == False`, an entry in `engine.warnings`), not `EnumerationExceeded`.
   - **Must fail today**: raises.

8. **`tests/test_atms_consequent_field_discipline.py`** (new — covers E.M2)
   - AST-walks `propstore/world/atms.py`; finds every read of `consequent_ids`; asserts either the field is renamed to `consequent_id: str` everywhere OR a constructive test exercises a 2-tuple `consequent_ids` through a real propagation. Pick one and gate it.
   - **Must fail today**: dead code present, no exercise test.

9. **`tests/test_atms_propagation_nogood_interleave.py`** (new — covers E.M3)
   - Mid-iteration assertion: hook `_propagate_labels` to inspect a label after pass N but before `_update_nogoods` runs; assert no environment in any label is a superset of any nogood that a *later* same-iteration `_update_nogoods` will derive. The test must construct the case where a stale-window violation is observable.
   - **Must fail today**: stale window exists.

10. **`tests/test_conflict_orchestrator_isolation.py`** (new — covers E.M4)
    - Exercise four sub-cases:
      a. Inject a real concept named `name`/`domain`/`source_kind`; assert `with_synthetic_concepts` raises (loud) instead of shadowing.
      b. Patch `_detect_parameterization_conflicts` to *return* records rather than mutate; assert orchestrator composes returns, not side-effects.
      c. Cache lifting decisions across detectors; assert per-pair Z3 calls in a 5-pair run are 5, not 25.
      d. `seen` key at `:140-147` includes derivation chain; assert two records differing only in derivation are both kept.
    - **Must fail today**: all four.

11. **`tests/test_workstream_i_done.py`** (new — gating sentinel; per WS-A pattern Mechanism 2)
    - `xfail` until WS-I closes; flips to `pass` on the final commit.

## Production change sequence

Each step lands in its own commit `WS-I step N — <slug>`. Each step turns a specific failing test green, with no extra production change beyond that. No refactoring drive-bys.

### Step 1 — Interface replacement for `is_stable` / `node_relevance` / `node_interventions` (E.H1a/b/c)

Per Codex 2.9, this is **not a rename** and **not a thin wrapper at the old name**. It is **interface replacement** — the old bounded API is deleted, the new unbounded API is added, and every caller is updated in a single PR per `feedback_no_fallbacks.md`.

Three production sub-changes inside the one step (one PR):

**(a) Delete the old API.** `propstore/world/atms.py:765-855`: remove the existing `is_stable(node)`, `node_relevance(node)`, `node_interventions(node)` definitions in their entirety, including the `limit: int = 8` default and the `_iter_future_queryable_sets` truncate-at-limit behavior at `:1841-1860`. There is no thin `is_stable(node)` wrapper kept around. The old bounded-with-silent-truncation behavior is gone from the codebase.

**(b) Add the new API with explicit budget semantics.** Three new methods on `ATMSEngine` with the contract from test 1:

- `is_stable(node, *, limit: int | None) -> bool`. `limit=None` means **truly unbounded** — `_iter_future_queryable_sets` enumerates the full power set; correctness over performance. If a caller passes `limit=None` against a 4096-subset space and the machine runs out of memory, the failure is loud (the caller asked for unbounded; it got unbounded). `limit=N` with `N: int` means budget mode — the engine examines at most `N` subsets and raises `BudgetExhausted(examined=N, total=...)` if the verdict is not determined within budget. **Not a silent under-approximation.** A returned `bool` always means soundness over the full space (unbounded mode) or soundness within a verdict that fits in budget (budget mode where the verdict was reached before the budget); it never means "I looked at 8 of 4096 and guessed."
- `node_relevance(node, *, limit: int | None) -> RelevanceWitnesses`. Same shape: `limit=None` = unbounded; `limit=N` = `BudgetExhausted` on overflow.
- `node_interventions(node, *, limit: int | None) -> InterventionPlans`. Same shape.

The `limit` parameter is **keyword-only** (the leading `*`) so callers cannot accidentally pass it positionally and end up replicating the old `limit=8` mistake.

A new exception class `propstore.world.atms.BudgetExhausted` carries the budget information. It is a typed signal, not a generic `RuntimeError`. Callers that want to handle budget exhaustion catch it explicitly; callers that don't want to handle it let it propagate (which is the correct loud behavior — a `True` would have been a lie).

If a caller wants typed `Result.Pending`-style return rather than exception, that is a separate WS — for WS-I the shape is `BudgetExhausted` raised. Q has chosen the raise variant per Codex 2.9 ("raises `BudgetExhausted` (or returns typed `Result.Pending`)") and we pick raise for cohesion with `EnumerationExceeded` (Step 7) which is being changed to anytime-return; the two failure modes are semantically distinct (Step 7 is "fixpoint not reached, here is what we know"; Step 1 is "verdict not reached, no claim made").

**(c) Update every caller in one pass.** Locate every caller of the old three names — by grep across `propstore/` for `is_stable(`, `node_relevance(`, `node_interventions(` — and update each:

- `propstore/world/atms.py:1184-1274` `argumentation_state` calls all three per claim. Decide per call site: does this surface need a sound answer (pass `limit=None`) or a bounded answer with explicit fallback (pass `limit=N` and handle `BudgetExhausted` to record a `WARNING_BUDGET_EXHAUSTED` marker on the result row)? The decision is per-surface: CLI explain output should pass `limit=None` and let the unbounded computation run because correctness wins; planner code paths that have to return within an interactive budget pass `limit=N` and surface `BudgetExhausted` to the planner's output as a typed "I do not know within budget" verdict, never as silent `False`.
- Every consumer in `worldline`, `support_revision`, `app/world_atms.py`, `pks world` CLI surfaces, the ASPIC bridge — same decision per call site.

**No call site is left passing the old single-positional shape.** AST walk in test 1 enforces this. If any module is missed, the test fails.

Acceptance: `tests/test_atms_unbounded_stability_api.py` green. The unbounded soundness assertion passes (subset 9 is found in the K=12 case). The budget-exhaustion assertion passes (`limit=8` raises `BudgetExhausted`, not silently returns). The old-API-deletion assertion passes (calling `is_stable(node)` with no kwarg raises `TypeError`). The caller-shape AST walk passes (no module passes the old shape).

### Step 2 — Cycle-aware `_was_pruned_by_nogood` (E.H2)
- `propstore/world/atms.py:1696-1718`: replace cycle-protection `return False` with explicit pending-set + post-order resolve. When all justifications in a strongly-connected component would be pruned by some nogood, the SCC's nodes are `OUT(NOGOOD_PRUNED)`; otherwise `OUT(MISSING_SUPPORT)`. Document the algorithm referencing Forbus 1993 §12.4 (label propagation) and de Kleer 1986 p.146 (assumption hierarchies).
- Update `_out_kind_for_node` and `node_status` accordingly.

Acceptance: `test_atms_was_pruned_by_nogood_cycle.py` green; intervention plans for cyclic-pruned OUT cases now generated.

### Step 3 — Categorical input visibility (E.H3)
- `propstore/world/atms.py:1448-1477`: replace the silent `break` with explicit branch. On non-numeric input emit either an `ATMSDerivedNode` with `out_kind=PARAMETERIZATION_INPUT_TYPE_INCOMPATIBLE` citing the provider, or a structured conflict (preferred — feeds the same nogood path as Codex #24). Pick at test-write time.

Acceptance: `test_atms_categorical_provider_visibility.py` green.

### Step 4 — Derived-vs-derived conflict propagation (Codex #24)
- `propstore/world/value_resolver.py:166-178`: change the loop to **collect** every compatible candidate before returning. If multiple candidates with different values exist, the resolver returns `DerivedResult(status=ValueStatus.CONFLICTED, candidates=...)`.
- `propstore/world/bound.py:299, :920`: extend `BoundWorld.conflicts()` to surface derived-derived `ConflictRecord` rows from the resolver.
- `propstore/world/atms.py:1481-1517`: `_runtime.conflicts()` now yields derived rows; `_update_nogoods` consumes them. The provider environments of the conflicting candidates become the nogood environments; provenance entries reference the parameterization indices.

Acceptance: `test_atms_derived_contradictions.py` green.

### Step 5 — Context-preserving environment serialisation (Codex #25)
- `propstore/world/atms.py:2369-2372, :2375-2381, :2383-2387`: `_serialize_environment_key` returns the structured form (`{"assumption_ids": [...], "context_ids": [...]}` is the cluster-E recommendation; the test pins which). Update `_serialize_label`, `_serialize_nogood_detail`, and the JSON/CLI consumers in `propstore/cli/world.py` and `propstore/app/world_atms.py:195-197`.
- Per Codex ws-05 step 3: "minimality/consistency checks compare full environment keys, not assumptions only." Verify `core/labels.py:NogoodSet.excludes` already handles full keys; if it strips contexts during polynomial conversion, fix at the polynomial layer.

Acceptance: `test_atms_environment_context_serialisation.py` green.

### Step 6 — CEL semantic equality at antecedent matching (Codex #26)
- `propstore/world/atms.py:1559-1584`: replace `assumption.cel == condition` with the canonical CEL equivalence check from WS-D. Concretely: parse `assumption.cel` and `condition` to the canonical form WS-D produces, compare canonicalisations. If WS-D ships a Z3-backed equivalence, fall through to it for non-syntactic matches.
- This is the WS-D dependency. Cannot land before WS-D delivers the canonicalisation surface.

Acceptance: `test_atms_cel_semantic_equality.py` green.

### Step 7 — Anytime fixpoint, dead-code field, propagation interleave (E.M1, E.M2, E.M3)
- `atms.py:1284-1290`: replace `raise EnumerationExceeded` with returning the partial-state engine; record `fixpoint_reached: bool` and `iterations_run: int` on the engine; add a `warnings` list. (This is fixpoint anytime — semantically distinct from Step 1's `BudgetExhausted` which is per-query verdict-budget.)
- `atms.py:285-289` (and read sites at `:1605, :2284, :2326, :2334`): collapse `consequent_ids: tuple[str, ...]` to `consequent_id: str` everywhere. No multi-consequent code currently exists; the field is dead.
- `atms.py:1382-1420`: interleave `_update_nogoods` inside the per-justification UPDATE step, per Forbus 1993 §12.4 and de Kleer 1986 p.151. The `while True` outer loop becomes redundant for nogood-staleness purposes; keep it only for the parameterization-materialisation pass that genuinely adds new justifications.

Acceptance: `test_atms_max_iterations_anytime.py`, `test_atms_consequent_field_discipline.py`, `test_atms_propagation_nogood_interleave.py` all green.

### Step 8 — Conflict-detector orchestrator hardening (E.M4)
- `conflict_detector/orchestrator.py:43-66`: `with_synthetic_concepts` raises `SyntheticConceptCollision` when a real concept canonical name shadows `__source__`/`__domain__`/etc.
- `:106-112`: `_detect_parameterization_conflicts` returns a list rather than mutating in place; orchestrator composes.
- `:124-182`: introduce a `LiftingDecisionCache` keyed by `(claim_id_a, claim_id_b, context_id)`; detectors share it.
- `:140-147`: extend `seen` key to include the derivation chain hash.

Acceptance: `test_conflict_orchestrator_isolation.py` (all four sub-cases) green.

### Step 9 — Close gaps and gate
- Update `docs/gaps.md`: remove every cluster-E "Principle drift" item (1, 2, 7, 8) and Codex #24/#25/#26 entries. Add `# WS-I closed <sha>` line to "Closed gaps."
- Flip `tests/test_workstream_i_done.py` from `xfail` to `pass`.
- Update this file's STATUS line to `CLOSED <sha>`.

Acceptance: `test_workstream_i_done.py` passes; `gaps.md` reflects.

## Acceptance gates

Before declaring WS-I done, ALL must hold:

- [x] `uv run pyright propstore` — passes with 0 errors.
- [x] `uv run lint-imports` — passes (WS-I doesn't add new layers; this WS doesn't change contracts).
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-I tests/test_atms_unbounded_stability_api.py tests/test_atms_was_pruned_by_nogood_cycle.py tests/test_atms_categorical_provider_visibility.py tests/test_atms_derived_contradictions.py tests/test_atms_environment_context_serialisation.py tests/test_atms_cel_semantic_equality.py tests/test_atms_max_iterations_anytime.py tests/test_atms_consequent_field_discipline.py tests/test_atms_propagation_nogood_interleave.py tests/test_conflict_orchestrator_isolation.py tests/test_workstream_i_done.py` — green, `logs/test-runs/WS-I-20260428-062435.log`.
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-I-existing tests/test_atms_engine.py tests/test_world_atms*.py tests/test_labels_properties.py tests/test_assignment_selection_merge.py` — no `test_world_atms*.py` files exist in this repo state; available companion files passed in `logs/test-runs/WS-I-existing-20260428-062524.log`.
- [x] Full suite `powershell -File scripts/run_logged_pytest.ps1` — green, `logs/test-runs/pytest-20260428-062603.log`.
- [x] No call site in `propstore/` calls `is_stable`, `node_relevance`, or `node_interventions` with the old single-positional shape. Every call passes `limit=None` (accepting unbounded semantics) or `limit=N` (with `BudgetExhausted` handled in the same function). Verified by AST walk in `test_atms_unbounded_stability_api.py`.
- [x] Calling `engine.is_stable(node)` with no `limit` kwarg raises `TypeError`. The old API is gone from the codebase, not aliased.
- [x] `propstore/world/atms.py` has no remaining `consequent_ids` references.
- [x] `app/world_atms.py:_support_ids` returns a structured `(assumption_ids, context_ids)` shape.
- [x] WS-I property-based gates from `PROPERTY-BASED-TDD.md` are included in `tests/test_atms_unbounded_stability_api.py` and companion label properties in `tests/test_labels_properties.py`, both included in logged WS-I runs.
- [x] `docs/gaps.md` has no open rows for the findings listed at the top of this file; WS-I closures are recorded under "Closed gaps."
- [x] STATUS line is `CLOSED 6a6cc9d6`.

## Done means done

WS-I is done when **every finding in the table at the top is closed**. Specifically:

- E.H1a, E.H1b, E.H1c (the three interface-replacement findings), E.H2, E.H3, E.M1, E.M2, E.M3, E.M4, Codex #24, Codex #25, Codex #26 — each has a corresponding green test in CI.
- Cluster-E "Principle drift" items 1, 2, 7, 8 are closed in `gaps.md` (the other principle-drift items belong to MED bugs not in this table; they ride along but their close-state is per-bug).
- The workstream's gating sentinel (`test_workstream_i_done.py`) flips from `xfail` to `pass`.

If any one of those is not true, WS-I stays OPEN. No "we'll do the orchestrator hardening later." Either it's in scope and closed, or it's explicitly removed from this WS in this file (and moved to a successor WS) before declaring done.

## Papers / specs referenced

- **de Kleer 1986 — "An Assumption-Based TMS"** (`papers/deKleer_1986_AssumptionBasedTMS/notes.md`). Pages 144 (label minimality), 146 (assumption hierarchies — used by Step 2's SCC argument), 148 (nogood superset closure — confirms the polynomial `live` filter is correct), 151 (incremental UPDATE — motivates Step 7's interleave). Pages 157 (bit-vector envs) and 158 (assumption GC) explicitly out of scope (Tier 6.3).
- **Forbus & de Kleer 1993 — "Building Problem Solvers"** (`papers/Forbus_1993_BuildingProblemSolvers/notes.md`). Ch. 12 §12.4 PROPAGATE/UPDATE/WEAVE pseudocode — Step 7's interleave cites this directly. Ch. 13 CMS, Ch. 14 ATRE focus — out of scope.
- **McAllester 1978 — "Three-Valued TMS"** (`papers/McAllester_1978_ThreeValuedTMS/notes.md`). Background reference; WS-I does not introduce three-valued replay results — Step 1's `BudgetExhausted` raise is a typed budget signal, not a three-valued return. McAllester remains a future-WS reference for genuine three-valued belief representation.
- **Martins 1983 / Martins 1988** (`papers/Martins_1983_MultipleBeliefSpaces/notes.md`, `Martins_1988_BeliefRevision/notes.md`). Contexts are belief spaces; the assumption-only serialisation Codex #25 flags is precisely the bug MBS architecture is designed to avoid. Step 5 cites.
- **de Kleer 1984 (confluences), Doyle 1979 (CP justifications), Falkenhainer 1987 (BMS / continuous belief), Mason 1989 (DATMS).** Background and missing-variant references; out of scope for this WS.
- **Shapiro 1998 / Dixon 1993** (`papers/Shapiro_1998_BeliefRevisionTMS/notes.md`, `papers/Dixon_1993_ATMSandAGM/notes.md`). Cross-cut with WS-G; Step 4's nogood-update changes must remain compatible with the AGM/revision postulates WS-G enforces. Step 5's environment-shape change must keep contraction operating over full keys.
- **de Kleer 1986 — "Problem Solving with the ATMS"** (`papers/deKleer_1986_ProblemSolvingATMS/notes.md`). §6 `interpretations` procedure — flagged as missing in cluster-E, future WS.

## Cross-stream notes

- **WS-D dependency.** Step 6 cannot land until WS-D ships canonical CEL equivalence. If WS-D slips, ship Steps 1-5 and 7-8 and defer Step 6; document on STATUS line.
- **WS-F (ASPIC).** After Step 2, WS-F sees more `NOGOOD_PRUNED` (cyclic cases that previously masked as MISSING). Re-run WS-F acceptance against post-WS-I master.
- **WS-J (worldline) hashing.** Step 5 changes serialised env shape; WS-J's content-hash test must be re-baselined. Step 1 also affects WS-J: any worldline path that previously called `is_stable(node)` now must pass `limit=None` or handle `BudgetExhausted`. **WS-J formally depends on WS-I (Codex 2.8 ordering fix). WS-J2 also formally depends on WS-I via the WS-J chain.** The "pick one" wording is resolved — both formal dependencies are declared in their respective WS files.
- **WS-K (heuristic).** Step 4 moves resolver from "first wins" to "collect all"; the import-linter contract should keep this behind `value_resolver`.
- **WS-M (provenance).** Step 4 changes nogood-provenance shape (provider environments, not just claim IDs); WS-M's semiring code must accept the richer input.

## What this WS does NOT do

- **Does not preserve the old bounded `is_stable` API. Callers update in one pass per `feedback_no_fallbacks.md`.** No thin wrapper at the old name. No `limit=8` default. No silent truncation. The old API is deleted and the new unbounded API takes its place; every caller is updated in the same PR. Same shape applies to `node_relevance` and `node_interventions` — interface replacement, not rename, not aliasing.
- Does NOT rewrite the engine to be incremental (Forbus PROPAGATE/UPDATE/WEAVE) or switch to bit-vector environments — Tier 6 spike `T6.3`. WS-I makes the *batch* engine sound and serialisation honest; it does not change the algorithmic shape.
- Does NOT add consumer architecture, focus environments, `interpretations`, CMS, DATMS, BMS, or McAllester three-valued ATMS — all under cluster-E "Missing TMS variants" as future WSes.
- Does NOT rename `provenance/nogoods.py` (WS-N), touch `_direct_state_for_claim`'s wide-interval exclusion (WS-H / future BMS WS), add empty-environment-as-nogood detection (defer to a 1-line PR if Q approves), broaden orchestrator synthetic-concept lifecycle work (Tier 6 spike), or cap `support_revision/operators.py` enumeration (WS-G or future WS).

If any excluded item turns out to be a blocker for closing one of the in-scope findings, that finding moves to a successor WS in this file *before* WS-I declares done — not after.
