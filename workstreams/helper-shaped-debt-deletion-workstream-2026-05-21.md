# Helper-Shaped Debt Deletion Workstream - 2026-05-21

Status: executable control surface for the next cleanup after
`workstreams/quire-sqlalchemy-charter-cutover-2026-05-18`.

## Refactor Zen

Field, identity, and schema shape is written once. Quire charters carry storage
field shape and generic family reference mechanics. Propstore semantic owners
carry domain behavior. After an IO boundary has parsed input, the type system
carries meaning.

This workstream deletes helper-shaped code that keeps meaning in loose strings,
generic coercers, normalizers, row DTOs, broad records, adapters, shims, or
old/new compatibility paths. Do not replace a deleted helper with another
helper-shaped spelling, a repeated field-name list, a local kwargs builder, or a
per-field type narrowing block. Delete first; compiler, type, test, and search
failures are the work queue.

## Goal

Remove the remaining helper-shaped identity and normalization debt left outside
the completed SQLAlchemy charter cutover gates, starting with the known
`to_*_id` helper family in `propstore/core/id_types.py`.

## Final State

- `propstore/core/id_types.py` defines semantic ID types only. It does not
  define `to_*_id` or plural `to_*_ids` conversion helpers.
- Production code does not call `str(value)` through generic semantic-ID
  conversion helpers after the IO boundary.
- Typed IDs enter the semantic pipeline from typed documents, Quire family
  reference/FK APIs, exact semantic owners, or explicit IO parsing boundaries.
- No new generic helper family, adapter, shim, compatibility layer, alias,
  fallback reader, old/new dual path, broad normalizer, or row DTO is added.
- Remaining `coerce_*`, `normalize_*`, `*Record`, and `*Row` names are either
  deleted or recorded as exact owner-boundary artifacts with a named reason and
  a search gate that prevents them from becoming generic shape carriers.
- App/CLI/web presentation rows remain presentation-only and do not encode
  storage or semantic field shape.

## Non-Goals

- Do not move Propstore semantics into Quire.
- Do not replace `to_*_id` with `as_*_id`, `make_*_id`, `parse_*_id`,
  `ensure_*_id`, or another helper-shaped conversion family.
- Do not replace deleted coercers with repeated `str(...)`, `cast(...)`, or
  per-field validation blocks in core semantic paths.
- Do not change durable artifact IDs or repository storage formats unless a
  phase explicitly says that is the target.
- Do not do broad cleanup outside the active phase.

## Current Evidence

Recorded 2026-05-21 before this workstream was authored:

- Completed SQLAlchemy charter final gates were rechecked for the explicit
  old-path names: `ProjectionTable`, `ProjectionModel`, `ProjectionRow`,
  `from_mapping`, `coerce_active_micropublication`,
  `SidecarClaimRelationStore`, `find_similar_claim_rows`,
  `find_similar_concept_rows`, `resolve_claim_id`, and `resolve_concept_id`
  were zero-hit in the searched production/test surfaces.
- `propstore/core/id_types.py` still defines:
  `to_concept_id`, `to_claim_id`, `to_assertion_id`, `to_context_id`,
  `to_condition_id`, `to_provenance_graph_id`, `to_justification_id`,
  `to_assumption_id`, `to_queryable_id`, `to_concept_ids`, `to_claim_ids`,
  `to_assumption_ids`, and `to_queryable_ids`.
- `git blame` shows the original `to_*_id` helpers mostly predate this
  SQLAlchemy charter workstream; that does not make them acceptable.
- Broad helper-shaped scans still find `coerce_*`, `normalize_*`, `*Record`,
  and `*Row` names across production and tests. Those are not automatically
  wrong, but each must be classified by owner boundary before this cleanup can
  be called complete.

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
- If a deletion reveals missing generic Quire capability, stop, add the exact
  missing capability to Quire, push Quire, pin Propstore to the pushed commit,
  and then continue. Do not add a Propstore workaround.

## Phase 0: Baseline And Gates

Repository: Propstore.

Run and record the current baseline before implementation edits:

```powershell
git status --short --untracked-files=no
rg -n -F -- "from propstore.core.id_types import" propstore tests
rg -n -F -- "to_concept_id" propstore tests
rg -n -F -- "to_claim_id" propstore tests
rg -n -F -- "to_assertion_id" propstore tests
rg -n -F -- "to_context_id" propstore tests
rg -n -F -- "to_condition_id" propstore tests
rg -n -F -- "to_provenance_graph_id" propstore tests
rg -n -F -- "to_justification_id" propstore tests
rg -n -F -- "to_assumption_id" propstore tests
rg -n -F -- "to_queryable_id" propstore tests
rg -n -- "\b(def|class)\s+\w*(helper|adapter|shim|coerce|normalize|from_row|from_mapping|resolve_\w+_id|to_\w+_id)\w*\b|\b\w*(Helper|Adapter|Shim|Row|Record|DTO)\b" propstore tests
```

Gate:

- tracked worktree is clean before deletion;
- this workstream contains the exact Phase 1 deletion targets;
- broad helper-shaped output is captured in the Phase 0 execution record or a
  sibling inventory file committed before Phase 2 begins.

### Phase 0 Execution Record

Recorded 2026-05-21.

- `git status --short --untracked-files=no` was clean before deletion.
- `rg -n -F -- "from propstore.core.id_types import" propstore tests` found
  the active import queue in core, families, world, worldline,
  support-revision, app, ASPIC, provenance, and tests.
- The required `to_*_id` searches confirmed live production/test callers for
  every Phase 1 deletion target except that some hits are only definitions or
  tests for the narrower IDs.
- The broad helper-shaped scan found the expected remaining `coerce_*`,
  `normalize_*`, `*Record`, `*Row`, adapter, and helper-looking surfaces. The
  complete classification belongs to Phase 2 inventory after Phase 1 deletes
  the known semantic-ID helper family.

## Phase 1: Delete Semantic ID Conversion Helpers

Owned files:

- `propstore/core/id_types.py`
- every production/test caller that imports or calls the deleted helper names

Delete first:

- `to_concept_id`
- `to_claim_id`
- `to_assertion_id`
- `to_context_id`
- `to_condition_id`
- `to_provenance_graph_id`
- `to_justification_id`
- `to_assumption_id`
- `to_queryable_id`
- `to_concept_ids`
- `to_claim_ids`
- `to_assumption_ids`
- `to_queryable_ids`

The semantic ID type aliases may remain in `id_types.py` only as type names.
They must not be paired with generic conversion functions.

After deletion, run:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label helper-id-types-targeted tests/test_init.py tests/test_core_graph_types.py tests/test_condition_ir.py tests/test_condition_z3_backend.py tests/test_world_query.py tests/test_worldline.py tests/test_atms_engine.py tests/test_revision_phase1.py tests/test_resolution_helpers.py
```

Fix only failures caused by deleting the helper family. Valid fixes:

- carry the already typed ID through the call path;
- construct the `NewType` directly at an IO/document boundary;
- use Quire family reference/FK lookup when the value is a family reference;
- move parsing to the exact owner boundary that already owns the incoming
  payload shape.

Invalid fixes:

- adding a replacement helper family;
- adding local stringifying/casting blocks throughout core semantic code;
- accepting `object` in a core semantic path only to immediately stringify it;
- adding compatibility for old shapes not explicitly required by the user.

Phase 1 search gates:

```powershell
rg -n -- "\b(to_concept_id|to_claim_id|to_assertion_id|to_context_id|to_condition_id|to_provenance_graph_id|to_justification_id|to_assumption_id|to_queryable_id|to_concept_ids|to_claim_ids|to_assumption_ids|to_queryable_ids)\b" propstore tests
rg -n -- "def to_[A-Za-z0-9_]+_id|def to_[A-Za-z0-9_]+_ids" propstore tests
```

Gate: zero production hits for the deleted helper symbols. Test hits are
allowed only in tests that assert the old helper family is deleted; otherwise
they must be removed. Do not rename valid non-helper fields or APIs such as
`argument_to_claim_id` or `snapshot_to_claim_ids` to satisfy a substring search.

Execution record:

- Deleted the semantic ID conversion helper family from
  `propstore/core/id_types.py`.
- Replaced helper callers with direct type construction at typed boundaries and
  repaired the `snapshot_to_claim_ids` codemod fallout without renaming the valid
  API.
- `uv run pyright propstore`: passed with `0 errors, 0 warnings, 0 informations`.
- Phase 1 symbol search gates: zero hits for deleted helper symbols and zero
  `def to_*_id` / `def to_*_ids` hits under `propstore` and `tests`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label helper-id-types-targeted tests/test_init.py tests/test_core_graph_types.py tests/test_condition_ir.py tests/test_condition_z3_backend.py tests/test_world_query.py tests/test_worldline.py tests/test_atms_engine.py tests/test_revision_phase1.py tests/test_resolution_helpers.py`:
  passed, `304 passed, 29 warnings`, log
  `logs\test-runs\helper-id-types-targeted-20260521-174047.log`.

## Phase 2: Classify Remaining Helper-Shaped Surfaces

Input: Phase 0 broad helper-shaped scan.

Create a sibling inventory file:

```text
workstreams/helper-shaped-debt-inventory-2026-05-21.md
```

For every production hit from the broad scan, record exactly one classification:

- `delete`: generic helper, coercer, adapter, shim, row DTO, or duplicate field
  carrier;
- `io-boundary`: parser/decoder for YAML, JSON, CLI, web, or external input;
- `presentation`: app/web/CLI report row with no storage or semantic field
  authority;
- `semantic-owner`: behavior object or domain record owned by the exact
  semantic module;
- `quire-needed`: deletion is blocked by a named missing Quire capability.

No escape-hatch wording is allowed in the inventory. A hit that cannot be
classified from current code reading blocks Phase 2 completion.

Gate:

```powershell
rg -n "candidate|maybe|if appropriate|later cleanup|decide later|TBD|TODO" workstreams/helper-shaped-debt-inventory-2026-05-21.md
```

Gate result must be zero-hit.

Execution record:

- Created and committed
  `workstreams/helper-shaped-debt-inventory-2026-05-21.md`.
- The inventory classifies the current broad production scan into `delete`,
  `io-boundary`, `presentation`, `semantic-owner`, and `quire-needed`.
- `rg -n -i -- "candidate|maybe|TBD|TODO|if appropriate|may remain|unless justified|later cleanup|decide later" workstreams/helper-shaped-debt-inventory-2026-05-21.md`:
  zero hits.
- Phase 3 deletion queue from the inventory:
  `propstore/core/justifications.py:_normalize_attrs`,
  `propstore/conflict_detector/models.py:coerce_conflict_class`,
  `propstore/support_revision/state.py:coerce_assumption_ref`.
- Non-coercer deletion queue:
  `propstore/world/overlay.py:_ParameterizationCatalogAdapter`.

## Phase 3: Delete Generic Coercers And Normalizers

Owned surfaces: every Phase 2 `delete` row whose name starts with
`coerce_`, `_coerce_`, `normalize_`, or `_normalize_`.

Delete first, then fix callers from compiler/type/test failures.

Allowed remaining surfaces:

- enum constructors or exact domain constructors that validate an already typed
  domain value;
- IO-boundary parsers named for the boundary, not generic normalization;
- unit conversion or mathematical normalization where the operation is the
  domain behavior itself.

Search gates:

```powershell
rg -n -- "\bdef _?coerce_[A-Za-z0-9_]+\b" propstore tests
rg -n -- "\bdef _?normalize_[A-Za-z0-9_]+\b" propstore tests
```

Gate: every remaining production hit appears in the Phase 2 inventory as
`io-boundary`, `presentation`, or `semantic-owner`; every `delete` row is
zero-hit.

Execution record:

- Deleted `propstore/core/justifications.py:_normalize_attrs`.
- Deleted `propstore/conflict_detector/models.py:coerce_conflict_class`.
- Deleted `propstore/support_revision/state.py:coerce_assumption_ref`.
- `rg -n -- "\b(coerce_conflict_class|coerce_assumption_ref|_normalize_attrs)\b" propstore tests`:
  zero hits.
- Remaining `def _?coerce_*` and `def _?normalize_*` production hits are
  classified in `workstreams/helper-shaped-debt-inventory-2026-05-21.md` as
  `io-boundary`, `presentation`, or `semantic-owner`.
- `uv run pyright propstore`: passed with `0 errors, 0 warnings, 0 informations`.

## Phase 4: Delete Row/Record/DTO Shape Carriers

Owned surfaces: every Phase 2 `delete` row ending in `Row`, `Record`, or `DTO`.

Delete row/record classes that duplicate charter fields, sidecar rows, storage
payloads, or domain model fields. Do not rename them to avoid the search gate.

Allowed remaining surfaces:

- exact provenance records;
- exact assertion codec records that are true IO/document codecs;
- presentation table rows for app/web/CLI reports;
- semantic trace or domain records that own behavior and do not restate Quire
  storage shape.

Search gates:

```powershell
rg -n -- "\bclass [A-Za-z0-9_]*(Row|Record|DTO)\b" propstore tests
```

Gate: every remaining production hit appears in the Phase 2 inventory as
`io-boundary`, `presentation`, or `semantic-owner`; every `delete` row is
zero-hit.

## Phase 5: Final Gates

Run:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label helper-shaped-debt-full
rg -n -- "\b(to_concept_id|to_claim_id|to_assertion_id|to_context_id|to_condition_id|to_provenance_graph_id|to_justification_id|to_assumption_id|to_queryable_id|to_concept_ids|to_claim_ids|to_assumption_ids|to_queryable_ids)\b" propstore tests
rg -n -- "def to_[A-Za-z0-9_]+_id|def to_[A-Za-z0-9_]+_ids" propstore tests
```

Completion requires:

- Phase 1 helper family is deleted;
- all Phase 2 `delete` rows are zero-hit;
- remaining helper-shaped names are recorded with exact owner-boundary reasons;
- no compatibility layer, adapter, shim, alias, old/new dual path, or renamed
  helper-shaped replacement was added;
- Propstore gates pass through the logged wrappers and `uv run pyright
  propstore`.
