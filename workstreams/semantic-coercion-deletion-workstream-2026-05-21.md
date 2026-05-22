# Semantic Coercion Deletion Workstream - 2026-05-21

Status: executable follow-on to
`workstreams/helper-shaped-debt-deletion-workstream-2026-05-21.md`.

## Refactor Zen

Field, identity, and schema shape is written once. Quire charters carry storage
field shape and generic family reference mechanics. Propstore semantic owners
carry domain behavior. After an IO boundary has parsed input, the type system
carries meaning.

This workstream deletes remaining semantic coercion helpers that let core code
accept `object`, stringify it, and rebuild domain meaning locally. StrEnum
constructors, NewType constructors, and exact owner constructors are valid at
IO/document/app/CLI boundaries. Broad `coerce_*`, `to_*`, and mixed-view
normalization helpers are not valid semantic pipeline APIs.

## Goal

Delete the remaining enum/string and mixed-type semantic coercion surfaces
identified after the helper-shaped debt cleanup.

## Final State

- `propstore/core/algorithm_stage.py` defines only `AlgorithmStage`; it does
  not define `to_algorithm_stage` or `coerce_algorithm_stage`.
- Claim type, exactness, stance type, and value status construction happens
  through the StrEnum class at the IO/document owner boundary. The core
  semantic pipeline does not import or call `coerce_claim_type`,
  `coerce_exactness`, `coerce_stance_type`, or `coerce_value_status`.
- Dataclass/model `__post_init__` methods do not accept `object` only to
  stringify it into a semantic enum. If a dataclass is semantic runtime state,
  its field type carries the already parsed enum.
- Queryable assumptions enter world/ATMS/fragility/worldline runtime APIs as
  `QueryableAssumption` instances with `CelExpr` already parsed. CLI/app text
  shorthands are parsed in CLI/app owner modules before crossing into the world
  runtime layer.
- `propstore/world/resolution.py` resolves over a single internal claim-view
  type. Public entrypoints convert `Claim` values to the internal view once at
  the resolution owner boundary; resolution algorithms do not call
  `_coerce_resolution_claim` or accept `Sequence[_ResolutionClaimView | Claim]`.
- No replacement helper family, shim, adapter, fallback reader, alias, old/new
  dual path, or renamed coercer is added.

## Non-Goals

- Do not remove legitimate math/unit normalization such as `normalize_to_si`.
- Do not change durable artifact IDs or repository storage formats.
- Do not move Propstore semantic enum ownership into Quire.
- Do not broaden public APIs to keep old mixed string/object inputs alive.
- Do not add compatibility for old data shapes unless the user explicitly names
  an older repository or old data surface as a supported target.

## Current Evidence

Recorded 2026-05-21 before implementation:

- `git status --short --untracked-files=no`: clean.
- Exact helper scan found these production deletion targets:
  - `propstore/core/algorithm_stage.py:to_algorithm_stage`
  - `propstore/core/algorithm_stage.py:coerce_algorithm_stage`
  - `propstore/core/claim_types.py:coerce_claim_type`
  - `propstore/core/exactness_types.py:coerce_exactness`
  - `propstore/stances.py:coerce_stance_type`
  - `propstore/world/types.py:coerce_value_status`
  - `propstore/world/types.py:normalize_queryable_cel`
  - `propstore/world/types.py:coerce_queryable_assumptions`
  - `propstore/world/resolution.py:_coerce_resolution_claim`
- Caller scan showed live production callers in family declarations/stages,
  graph types, source claim/relation parsing, app source/world ATMS parsing,
  world query construction, value resolver, bound world queryable methods,
  fragility contributors, worldline argumentation, probabilistic relations,
  merge structured-merge parsing, and resolution algorithms.
- `ClaimType`, `Exactness`, `StanceType`, and `ValueStatus` are already
  `StrEnum` classes. Direct class construction at IO/document boundaries is the
  target enum parser; no project-local helper is needed for those cases.

## Global Execution Rules

- Execute phases in order.
- Before each production edit, reread this workstream and state the active
  phase.
- Commit every intentional edit slice atomically with explicit path-limited
  Git commands.
- After every commit and every passing substantial targeted test run, reread
  this file before selecting the next action.
- Use `uv run pyright propstore` for package type checks.
- Run tests through `powershell -File scripts/run_logged_pytest.ps1`.
- Delete first. Compiler, pyright, test, and search failures are the work
  queue.

## Phase 0: Baseline And Gates

Run and record:

```powershell
git status --short --untracked-files=no
rg -n -- "\b(to_algorithm_stage|coerce_algorithm_stage|coerce_claim_type|coerce_exactness|coerce_stance_type|coerce_value_status|coerce_queryable_assumptions|normalize_queryable_cel|_coerce_resolution_claim)\b" propstore tests
rg -n -- "\bdef (to_[A-Za-z0-9_]+|coerce_[A-Za-z0-9_]+|_coerce_[A-Za-z0-9_]+|normalize_[A-Za-z0-9_]+|_normalize_[A-Za-z0-9_]+)\b" propstore
```

Gate:

- tracked worktree is clean before deletion;
- all Phase 1 through Phase 4 deletion targets are still present exactly where
  this workstream records them;
- broad `def coerce/normalize/to` output is captured in the execution record
  or a sibling inventory before Phase 1 begins.

## Phase 1: Delete Algorithm Stage Conversion Helpers

Owned files:

- `propstore/core/algorithm_stage.py`
- every production/test caller importing or calling `to_algorithm_stage` or
  `coerce_algorithm_stage`

Delete first:

- `to_algorithm_stage`
- `coerce_algorithm_stage`

Required final state:

- `AlgorithmStage` remains the single branded type.
- IO/document owner code constructs `AlgorithmStage(value)` directly when the
  incoming field is known to be text.
- Runtime/query code receives `AlgorithmStage | None`; it does not call a
  generic helper to accept `object`.

Invalid fixes:

- adding `as_algorithm_stage`, `make_algorithm_stage`, `parse_algorithm_stage`,
  `ensure_algorithm_stage`, or another helper-shaped replacement;
- accepting `object` in runtime code for stage and then stringifying it;
- converting `AlgorithmStage` into a closed enum in this workstream.

Search gate:

```powershell
rg -n -- "\b(to_algorithm_stage|coerce_algorithm_stage)\b" propstore tests
```

Targeted tests:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label semantic-coercion-algorithm-stage tests/test_algorithm_stage_types.py tests/test_world_query.py
```

## Phase 2: Delete Enum Coercers

Owned files:

- `propstore/core/claim_types.py`
- `propstore/core/exactness_types.py`
- `propstore/stances.py`
- `propstore/world/types.py`
- every production/test caller importing or calling deleted enum coercers

Delete first:

- `coerce_claim_type`
- `coerce_exactness`
- `coerce_stance_type`
- `coerce_value_status`

Required final state:

- `ClaimType(value)`, `Exactness(value)`, `StanceType(value)`, and
  `ValueStatus(value)` appear only at IO/document/app/CLI owner boundaries and
  exact `from_dict`/row-decoding methods.
- Semantic dataclasses that are not IO codecs require typed enum fields and do
  not repair arbitrary objects in `__post_init__`.
- Boundary parsing failures are hard failures from the enum constructor or an
  owner-specific error type. They are not hidden by generic coercion helpers.

Known production caller queue:

- `propstore/families/claims/declaration.py`
- `propstore/families/concepts/stages.py`
- `propstore/families/relations/declaration.py`
- `propstore/app/world_atms.py`
- `propstore/app/sources.py`
- `propstore/core/graph_types.py`
- `propstore/probabilistic_relations.py`
- `propstore/merge/structured_merge.py`
- `propstore/source/claims.py`
- `propstore/source/relations.py`
- `propstore/world/value_resolver.py`
- `propstore/world/types.py`
- `propstore/world/atms.py`
- `propstore/world/queries.py`

Search gate:

```powershell
rg -n -- "\b(coerce_claim_type|coerce_exactness|coerce_stance_type|coerce_value_status)\b" propstore tests
```

Targeted tests:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label semantic-coercion-enums tests/test_core_graph_types.py tests/test_source_claims.py tests/test_source_relations.py tests/test_world_query.py tests/test_atms_engine.py tests/test_value_resolver_failure_reasons.py tests/test_cli.py
```

## Phase 3: Delete Queryable Assumption Coercion

Owned files:

- `propstore/world/types.py`
- every production/test caller importing or calling
  `normalize_queryable_cel` or `coerce_queryable_assumptions`

Delete first:

- `normalize_queryable_cel`
- `coerce_queryable_assumptions`
- `QueryableInput`

Required final state:

- Runtime world, ATMS, fragility, and worldline APIs receive
  `Iterable[QueryableAssumption]`.
- `QueryableAssumption.from_cel` accepts a `CelExpr`, not arbitrary `str`.
- CLI/app text shorthands such as `name=value` are parsed in CLI/app modules
  before runtime APIs are called.
- Bound-world methods do not silently accept mixed `str | CelExpr |
  QueryableAssumption` collections.

Known production caller queue:

- `propstore/fragility_contributors.py`
- `propstore/app/world_atms.py`
- `propstore/world/bound.py`
- `propstore/worldline/argumentation.py`

Invalid fixes:

- adding a new `parse_queryables`, `ensure_queryables`,
  `queryables_from_any`, or similarly broad replacement helper in
  `propstore/world/types.py`;
- moving the same mixed-input coercion into bound-world methods;
- preserving a public mixed-input alias that keeps the old runtime contract.

Search gate:

```powershell
rg -n -- "\b(normalize_queryable_cel|coerce_queryable_assumptions|QueryableInput)\b" propstore tests
```

Targeted tests:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label semantic-coercion-queryables tests/test_world_query.py tests/test_fragility.py tests/test_worldline_argumentation_multi_extension.py tests/test_cli.py
```

## Phase 4: Delete Resolution Claim Mixed-View Coercion

Owned files:

- `propstore/world/resolution.py`
- production/test callers affected by narrowed resolution signatures

Delete first:

- `_coerce_resolution_claim`

Required final state:

- Private resolution algorithms accept `Sequence[_ResolutionClaimView]` for
  target and active claim views.
- The public resolution owner boundary converts `Claim` values to
  `_ResolutionClaimView` once, before dispatching to private algorithms.
- `_resolve_structured_argumentation` and ASPIC paths still pass full
  `Claim` objects only where the structured projection requires full claim
  documents; target resolution IDs come from prebuilt `_ResolutionClaimView`
  values.
- No generator expression or local wrapper reintroduces the deleted mixed-view
  coercion.

Search gate:

```powershell
rg -n -- "\b_coerce_resolution_claim\b|Sequence\[_ResolutionClaimView \| Claim\]" propstore tests
```

Targeted tests:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label semantic-coercion-resolution tests/test_world_query.py tests/test_resolution_helpers.py tests/test_structured_projection.py tests/test_ws_f_aspic_bridge.py
```

## Phase 5: Final Gates

Run:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label semantic-coercion-full
rg -n -- "\b(to_algorithm_stage|coerce_algorithm_stage|coerce_claim_type|coerce_exactness|coerce_stance_type|coerce_value_status|coerce_queryable_assumptions|normalize_queryable_cel|_coerce_resolution_claim|QueryableInput)\b" propstore tests
rg -n -- "\bdef (to_[A-Za-z0-9_]+|coerce_[A-Za-z0-9_]+|_coerce_[A-Za-z0-9_]+)\b" propstore
```

Completion requires:

- every Phase 1 through Phase 4 deletion target is zero-hit in production and
  tests;
- remaining `normalize_*` names are exact IO/document/presentation/domain
  operations already classified by the helper-shaped debt inventory or recorded
  in this workstream execution record;
- no new helper-shaped replacement, shim, adapter, fallback, alias, or old/new
  dual path was added;
- `uv run pyright propstore` passes;
- the full test suite passes through the logged pytest wrapper.
