# Family Lifecycle Kernel Workstream

Date: 2026-05-25

## Target

Quire owns generic lifecycle mechanics for typed family records. Consumer
projects own domain meaning.

The final state is a small typed lifecycle kernel:

- `FamilyState` names lifecycle states on a `FamilyCharter`.
- `FamilyTransition` names allowed state changes on a `FamilyCharter`.
- `run_transition` executes one transition by validating charter metadata,
  running an optional guard callback, running an optional materializer callback,
  and returning a typed result.
- Batch execution runs the same transition over many records and returns a
  deterministic typed batch result.
- Expected domain failures are diagnostics, not ad hoc exceptions.
- Programming errors remain exceptions.

Quire must not import or encode Propstore concepts, source branches, claims,
concepts, promotion, finalization, alignment, provenance, or policy semantics.

## Deletion Targets

- `FamilyCharter.lifecycle_states`.
- Any lifecycle implementation carried through `metadata` mappings.
- Any consumer-specific lifecycle naming inside Quire.

## Owner Boundary

Quire owns:

- state and transition value objects
- transition lookup and validation
- state-specific generated document shape validation
- guard and materializer callback dispatch by callback id
- conflict policy application
- typed transition plans, writes, deletes, diagnostics, results, and batch
  results

Consumers own:

- semantic guard logic
- semantic materialization logic
- persistence of returned plans
- provenance and user-facing diagnostics
- domain-specific conflict interpretation beyond Quire's generic policy

## Required API

`quire.lifecycle` provides:

- `ConflictPolicy`
- `FamilyState`
- `FamilyTransition`
- `FamilyRecordWrite`
- `FamilyRecordDelete`
- `TransitionContext`
- `TransitionDiagnostic`
- `TransitionGuardResult`
- `TransitionPlan`
- `TransitionResult`
- `TransitionBatchResult`
- `LifecycleCallbacks`
- `LifecycleError`
- `run_transition`
- `run_transition_batch`

`FamilyCharter` provides:

- `states: tuple[FamilyState, ...]`
- `transitions: tuple[FamilyTransition, ...]`

`quire.__init__` re-exports the public lifecycle API.

## Execution Order

1. Add red tests for value objects and charter validation:
   - unknown transition source state is rejected
   - unknown transition target state is rejected
   - duplicate state names are rejected
   - duplicate transition names are rejected
   - `lifecycle_states` is absent
2. Add red tests for single-record execution:
   - guard failure blocks materializer
   - missing callback id raises `LifecycleError`
   - materializer returns a typed plan and result
   - source and target generated document types are selected by state
3. Add red tests for conflict policies:
   - `FAIL`
   - `SKIP`
   - `REPLACE`
   - `MERGE` requires a merge callback id
4. Add red tests for batch execution:
   - successes and skips are reported deterministically
   - failures are diagnostics on the item result
   - programming errors stop the batch
5. Implement `quire.lifecycle`.
6. Replace `FamilyCharter.lifecycle_states` with typed `states` and
   `transitions`.
7. Export the public lifecycle API.
8. Run the targeted test gate.
9. Run the full Quire gate.
10. Push Quire so consumers can pin an immutable remote SHA.

## Gates

```powershell
rg -n -F -- "lifecycle_states" quire tests
rg -n -F -- "metadata={\"transition\"" quire tests
rg -n -F -- "FamilyState" quire tests
rg -n -F -- "FamilyTransition" quire tests
uv run pytest -vv tests/test_lifecycle.py tests/test_charter_codegen.py tests/test_charters_schema_ir.py tests/test_charters_typed_attributes.py
uv run pytest -vv
uv run pyright
```

The `lifecycle_states` and `metadata={"transition"` searches must be zero-hit
gates. The `FamilyState` and `FamilyTransition` searches are presence checks.

## Completion

- Quire has typed lifecycle metadata and execution.
- `FamilyCharter.lifecycle_states` is gone.
- No lifecycle behavior is encoded in metadata bags.
- The targeted and full Quire gates pass.
- The final Quire commit is pushed.
