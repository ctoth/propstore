# Conflict Detector Parameterization Cleanup Workstream

Date: 2026-04-13
Status: proposed

Grounded in current repo review of:

- [propstore/param_conflicts.py](/C:/Users/Q/code/propstore/propstore/param_conflicts.py)
- [propstore/conflict_detector/__init__.py](/C:/Users/Q/code/propstore/propstore/conflict_detector/__init__.py)
- [propstore/conflict_detector/orchestrator.py](/C:/Users/Q/code/propstore/propstore/conflict_detector/orchestrator.py)
- [propstore/conflict_detector/parameters.py](/C:/Users/Q/code/propstore/propstore/conflict_detector/parameters.py)
- [propstore/conflict_detector/context.py](/C:/Users/Q/code/propstore/propstore/conflict_detector/context.py)
- [propstore/conflict_detector/collectors.py](/C:/Users/Q/code/propstore/propstore/conflict_detector/collectors.py)
- [propstore/conflict_detector/models.py](/C:/Users/Q/code/propstore/propstore/conflict_detector/models.py)
- [propstore/sidecar/claims.py](/C:/Users/Q/code/propstore/propstore/sidecar/claims.py)
- [propstore/cli/compiler_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/compiler_cmds.py)
- [tests/test_conflict_detector.py](/C:/Users/Q/code/propstore/tests/test_conflict_detector.py)
- [tests/test_param_conflicts.py](/C:/Users/Q/code/propstore/tests/test_param_conflicts.py)
- [tests/test_parameter_z3_strictness.py](/C:/Users/Q/code/propstore/tests/test_parameter_z3_strictness.py)
- [tests/test_exception_narrowing_group3.py](/C:/Users/Q/code/propstore/tests/test_exception_narrowing_group3.py)
- [tests/test_contexts.py](/C:/Users/Q/code/propstore/tests/test_contexts.py)
- [docs/conflict-detection.md](/C:/Users/Q/code/propstore/docs/conflict-detection.md)
- [docs/parameterization.md](/C:/Users/Q/code/propstore/docs/parameterization.md)

## Goal

Clean up the ownership, typing, and parameterization semantics around conflict
detection so the system has one honest conflict-detection package, one honest
typed claim surface at the package boundary, and one coherent implementation of
single-hop and transitive parameterization-derived `PARAM_CONFLICT`.

The target end state is:

- `propstore.conflict_detector` owns all conflict detection code
- `propstore.param_conflicts` no longer exists as a production module
- direct parameter-claim disagreement and parameterization-chain disagreement
  have clearly separated module names
- package-internal helpers operate on typed conflict claim objects, not ad hoc
  `dict` payloads
- single-hop and transitive parameterization conflicts propagate derived
  conditions and derived context honestly
- transitive search is no longer order-dependent on "first available input"
- package root exports only the intended public API, not underscored internals

## Why This Workstream Exists

The current implementation works, but the decomposition stopped halfway:

- the public package is `propstore.conflict_detector`
- the orchestrator still reaches outside the package into
  [propstore/param_conflicts.py](/C:/Users/Q/code/propstore/propstore/param_conflicts.py)
- that external module imports back into `conflict_detector` for collectors,
  context helpers, and models
- `conflict_detector.parameters` means direct parameter-claim disagreement,
  while `param_conflicts` means parameterization-chain contradiction
- the parameterization path is still dict-heavy in core code even though the
  package already has typed `ConflictClaim`
- single-hop and transitive parameterization conflict handling do not carry the
  same regime metadata, and the transitive path uses a documented shortcut:
  "For simplicity, use first available value per input"

That is a bad ownership boundary and a weak semantic surface. We control the
stack, so the right move is a direct cutover:

1. make the package own all conflict detection
2. move parameterization conflict code inside it
3. type the boundary honestly
4. fix the regime propagation semantics
5. delete the old path

## Scope

Primary production files:

- `propstore/conflict_detector/__init__.py`
- `propstore/conflict_detector/orchestrator.py`
- `propstore/conflict_detector/parameters.py`
- `propstore/conflict_detector/context.py`
- `propstore/conflict_detector/collectors.py`
- `propstore/conflict_detector/models.py`
- `propstore/param_conflicts.py`
- `propstore/sidecar/claims.py`
- `propstore/cli/compiler_cmds.py`

Primary tests and docs:

- `tests/test_conflict_detector.py`
- `tests/test_param_conflicts.py`
- `tests/test_parameter_z3_strictness.py`
- `tests/test_exception_narrowing_group3.py`
- `tests/test_contexts.py`
- `tests/test_world_model.py`
- `tests/test_build_sidecar.py`
- `docs/conflict-detection.md`
- `docs/parameterization.md`

## Non-goals

- Do not redesign the conflict classes themselves.
- Do not redesign the general CEL or Z3 subsystems beyond what this cleanup
  requires.
- Do not add compatibility shims or alias modules unless an external interface
  we do not control forces that requirement.
- Do not broaden this into a whole-repo concept-registry redesign.
- Do not change approximate parameterization semantics unless the current
  cleanup reveals a concrete bug that forces it.

## Current Problems To Fix

### Problem A: Wrong ownership boundary

Current shape:

- package root delegates transitive conflict detection to an external module
- orchestrator imports `_detect_param_conflicts` from that same external module
- external module imports package internals back from `conflict_detector`

Required fix:

- move parameterization-derived conflict logic into
  `propstore/conflict_detector/`
- delete `propstore/param_conflicts.py`
- update every caller directly

### Problem B: Confusing module naming

Current shape:

- `conflict_detector/parameters.py` means direct parameter claims
- `param_conflicts.py` means parameterization-chain contradictions

Required fix:

- rename modules so direct claim-vs-claim logic and derivation-vs-direct logic
  are clearly distinguished

Preferred end state:

- `propstore/conflict_detector/parameter_claims.py`
- `propstore/conflict_detector/parameterization_conflicts.py`

If the repo prefers shorter names, use a similarly explicit pair. Do not keep
the ambiguous current split.

### Problem C: Typed boundary not completed

Current shape:

- `conflict_detector` already defines `ConflictClaim`
- `param_conflicts.py` still accepts `dict[str, list[dict]]`
- helpers still read through `claim.get(...)`
- `ConflictClaim` still exposes dict-style compatibility methods
- derived claims are represented as synthetic dicts such as `{"value": ...}`

Required fix:

- make parameterization conflict helpers consume typed conflict claims
- add a dedicated typed representation for derived claims when needed
- keep raw dict decoding at the claim-file boundary only

### Problem D: Single-hop semantics under-report derived regime metadata

Current shape:

- `_detect_param_conflicts()` records `conditions_b=[]`
- the derived side does not merge input claim conditions
- the single-hop path does not context-classify derivation-vs-direct conflicts
  before emitting `PARAM_CONFLICT`

Required fix:

- derive conditions from input claims and relationship conditions
- derive context from input claim contexts and the context hierarchy
- run context classification before emitting `PARAM_CONFLICT`
- make single-hop and transitive records carry the same kind of regime metadata

### Problem E: Transitive search is order-dependent and incomplete

Current shape:

- transitive propagation uses only the first available resolved value per input
- this can miss valid contradictions or produce unstable behavior under claim
  ordering
- the code gathers input conditions but does not carry them forward as a merged
  derivation condition set

Required fix:

- replace "first available value per input" with an honest derivation search
- propagate merged path conditions and merged path context
- deduplicate derived states by typed provenance, not just approximate numeric
  value

## Target Architecture

## Package ownership

Conflict detection should be owned entirely by `propstore/conflict_detector/`.

Preferred modules:

- `__init__.py`
- `orchestrator.py`
- `models.py`
- `collectors.py`
- `context.py`
- `parameter_claims.py`
- `parameterization_conflicts.py`
- `measurements.py`
- `equations.py`
- `algorithms.py`

Delete:

- `propstore/param_conflicts.py`

## Public API

Keep the package root minimal:

- `ConflictClass`
- `ConflictRecord`
- `detect_conflicts`
- `detect_transitive_conflicts`

Do not re-export underscored helpers from package root.

If a test needs an internal helper, it should import from the specific submodule
that owns it. If a helper is genuinely public, remove the underscore and expose
it from that owning submodule, not via a kitchen-sink package root.

## Typed claim surface

Use `ConflictClaim` as the package boundary claim surface for authored claims.

Add an explicit typed representation for derived parameterization values, for
example:

- `DerivedConflictValue`

Suggested fields:

- `value: float`
- `source_claim_ids: tuple[str, ...]`
- `conditions: tuple[str, ...]`
- `context_id: str | None`
- `derivation_chain: str`

Rules:

- authored claim payloads become `ConflictClaim` once at collection time
- derived values stay typed and never become ad hoc dicts
- value comparison helpers may receive a claim-like protocol if needed, but the
  core parameterization logic must not go back to anonymous maps

## Derived regime propagation

Parameterization-derived conflicts must carry the regime under which the
derivation holds.

For every derived value:

- merge all source-claim conditions
- merge relationship-edge conditions across the full chain
- canonicalize the merged condition tuple
- merge contexts from source claims using the existing hierarchy
- reject incoherent derivation paths whose source contexts are mutually
  exclusive

Single-hop and transitive flows must use the same derivation metadata model.

## Transitive derivation search

The transitive algorithm must no longer choose the first available value for
each input. It needs a deterministic, honest search over derivation states.

Minimum acceptable strategy:

1. maintain typed resolved states per concept
2. for each parameterization edge, enumerate compatible combinations of input
   states
3. derive a new state for each input combination
4. carry forward value, provenance, merged conditions, and merged context
5. deduplicate by a typed derivation key rather than just by numeric value

Possible pruning rules:

- numeric tolerance dedupe only after provenance and regime metadata are
  considered
- skip incoherent context combinations early
- use deterministic ordering for stable output

Do not keep the current shortcut in production.

## Representation and deletion rules

- no dual-path production support for old and new module names
- no compatibility alias from `propstore.param_conflicts` to the new package
  module unless the user explicitly requires that compatibility
- no new dict-normalizer helper inside the core package
- change the interface, update every caller, delete the old path

## Execution Discipline

For each implementation slice in this workstream:

1. add or update the failing tests first
2. run the targeted red test and keep the log
3. change types first
4. change behavior
5. delete the replaced path
6. run focused pytest
7. run targeted `pyright` on touched files if the surface is covered
8. run the next broader regression gate
9. reread this workstream before deciding the next slice

Project command rules:

- use `uv`, not bare `python`, `pip`, or `pytest`
- run pytest as `uv run pytest -vv`
- tee logs to `logs/test-runs/`
- assume PowerShell when writing commands

## Phase Plan

### Phase 0: Baseline and Inventory

Tasks:

1. run `uv sync --upgrade`
2. run a focused conflict-detector baseline and keep the log
3. inventory every import of `propstore.param_conflicts`
4. inventory every package-root import of underscored internals from
   `propstore.conflict_detector`
5. inventory every dict-based parameterization conflict helper that survives
   beyond the IO boundary

Suggested gate:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run pytest -vv tests/test_conflict_detector.py tests/test_param_conflicts.py tests/test_parameter_z3_strictness.py tests/test_exception_narrowing_group3.py tests/test_contexts.py | Tee-Object -FilePath "logs/test-runs/$ts-conflict-baseline.txt"
```

Exit criteria:

- baseline log exists
- imports and dict-heavy surfaces are enumerated

### Phase 1: Own Parameterization Conflicts Inside The Package

Tasks:

1. create `propstore/conflict_detector/parameterization_conflicts.py`
2. move single-hop and transitive parameterization conflict logic into it
3. update orchestrator and package root to use the new internal module
4. update direct callers and tests
5. delete `propstore/param_conflicts.py`

Required caller updates:

- `propstore/conflict_detector/__init__.py`
- `propstore/conflict_detector/orchestrator.py`
- `propstore/sidecar/claims.py`
- `propstore/cli/compiler_cmds.py`
- tests that currently import from `propstore.param_conflicts`

Exit criteria:

- no production import of `propstore.param_conflicts` remains
- `propstore/param_conflicts.py` is deleted
- package ownership is one-way and internal

### Phase 2: Rename Parameter Modules For Honest Semantics

Tasks:

1. rename `parameters.py` to `parameter_claims.py`
2. keep parameterization-derived conflicts in
   `parameterization_conflicts.py`
3. update imports and tests
4. keep package-root API stable only for the true public functions

Exit criteria:

- direct parameter claims and parameterization-derived conflicts have distinct,
  explicit module names
- no ambiguous module naming remains in production code

### Phase 3: Finish Typed Claim And Derived-State Surfaces

Tasks:

1. convert parameterization conflict internals from dict-shaped claims to
   `ConflictClaim`
2. introduce a typed derived-state representation for computed values
3. delete `ConflictClaim` dict-style compatibility accessors if nothing honest
   still needs them
4. delete any synthetic `{"value": ...}` derived-claim placeholder
5. change helper signatures to typed forms first, then update all callers

Files likely touched:

- `propstore/conflict_detector/models.py`
- `propstore/conflict_detector/collectors.py`
- `propstore/conflict_detector/parameterization_conflicts.py`

Exit criteria:

- no core parameterization conflict helper accepts `dict[str, list[dict]]`
- no `claim.get(...)` remains in the parameterization conflict core path
- `ConflictClaim` is no longer pretending to be a dict in production code
- derived values are represented by typed objects, not dict shims

### Phase 4: Unify Single-Hop Derivation Semantics

Tasks:

1. define one derivation metadata model for single-hop and transitive flows
2. merge input-claim conditions with edge conditions in the single-hop path
3. merge source contexts in the single-hop path
4. run context classification before emitting `PARAM_CONFLICT`
5. update tests to assert derived conditions and context-sensitive splits where
   appropriate

New coverage to add:

- single-hop derived conditions are not dropped
- mutually excluded source contexts do not emit `PARAM_CONFLICT`
- single-hop context splits can produce `CONTEXT_PHI_NODE` when appropriate

Exit criteria:

- single-hop records carry honest derived regime metadata
- single-hop and transitive flows follow the same semantics for context and
  conditions

### Phase 5: Replace Order-Dependent Transitive Search

Tasks:

1. remove the "first available value per input" shortcut
2. implement typed input-combination search for parameterization edges
3. thread already-collected parameter claims into the transitive pass instead
   of recollecting them independently
4. propagate merged path conditions and merged path context through each
   derivation step
5. replace the current fragile single-hop skip heuristic with a structural
   derivation test
6. deduplicate derived states by typed provenance plus regime metadata
7. keep deterministic iteration order for reproducible records

New coverage to add:

- multiple direct claims on an input concept do not collapse to the first claim
- input ordering does not change emitted transitive conflicts
- path conditions from earlier edges survive to the final derived record
- context-incoherent chains are skipped deterministically

Exit criteria:

- transitive conflict detection is not order-dependent on input claim order
- merged path regime metadata is preserved end to end
- no production comment or code path still relies on the old shortcut

### Phase 6: Shrink And Clarify Public API

Tasks:

1. remove underscored helper re-exports from `conflict_detector/__init__.py`
2. update tests that currently import `_classify_pair_context` or collector
   helpers from package root
3. keep the root API limited to the intended public surface
4. update docs to match the new module locations and names

Exit criteria:

- package root exports only the intended public API
- tests import internal helpers from owning submodules if they intentionally
  test internals
- docs no longer reference the deleted module or stale paths

### Phase 7: Sidecar, CLI, And Broader Validation

Tasks:

1. rerun focused conflict-detector suites
2. rerun sidecar/world integration suites
3. rerun docs-facing and CLI-facing flows touched by the import cutover
4. run targeted `pyright` on the touched package files
5. run the full repo pytest suite

Suggested focused gate:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run pytest -vv tests/test_conflict_detector.py tests/test_param_conflicts.py tests/test_parameter_z3_strictness.py tests/test_exception_narrowing_group3.py tests/test_contexts.py tests/test_world_model.py tests/test_build_sidecar.py | Tee-Object -FilePath "logs/test-runs/$ts-conflict-cleanup-targeted.txt"
```

Suggested final gate:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run pytest -vv | Tee-Object -FilePath "logs/test-runs/$ts-full-suite-conflict-cleanup.txt"
```

Exit criteria:

- focused conflict and integration suites are green
- full suite is green
- touched docs and callers reflect the new ownership and names

## Test Plan

Minimum targeted suites during the workstream:

- `tests/test_conflict_detector.py`
- `tests/test_param_conflicts.py`
- `tests/test_parameter_z3_strictness.py`
- `tests/test_exception_narrowing_group3.py`
- `tests/test_contexts.py`
- `tests/test_world_model.py`
- `tests/test_build_sidecar.py`

Likely supporting suites after integration changes:

- `tests/test_property.py`
- `tests/test_z3_conditions.py`

Mandatory new regression coverage:

- single-hop derived conditions are preserved
- single-hop derived contexts are merged and classified
- transitive search is stable under reordered input claims
- transitive search uses all relevant input combinations rather than the first
  value only
- path conditions survive across multi-hop chains
- package-root API no longer exports underscored helpers
- all imports and docs are updated away from `propstore.param_conflicts`

## Completion Criteria

This workstream is complete only when all of the following are true:

- `propstore.param_conflicts` has been deleted
- `propstore.conflict_detector` fully owns parameterization conflict detection
- direct parameter-claim and parameterization-chain modules have explicit names
- the core parameterization conflict path is typed, not dict-based
- single-hop and transitive derived conflicts propagate context and conditions
  honestly
- transitive search no longer depends on the first available input state
- package root exports only the true public API
- tests and docs are aligned with the new ownership and names
- the full pytest suite has passed with logged output

## Explicitly Forbidden End States

- leaving `propstore.param_conflicts` in place as a compatibility alias
- moving code but keeping the old import path alive "for now"
- keeping dict and typed claim paths both first-class in the package core
- fixing transitive search by choosing a different arbitrary preferred value
  instead of enumerating derivation states honestly
- treating passing focused tests as completion while the old production path
  still exists
