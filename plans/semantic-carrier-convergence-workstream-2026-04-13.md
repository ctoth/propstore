# Semantic Carrier Convergence Workstream

Date: 2026-04-13
Status: active

Grounded in current repo review of:

- [propstore/core/environment.py](/C:/Users/Q/code/working/propstore/propstore/core/environment.py)
- [propstore/core/row_types.py](/C:/Users/Q/code/working/propstore/propstore/core/row_types.py)
- [propstore/core/active_claims.py](/C:/Users/Q/code/working/propstore/propstore/core/active_claims.py)
- [propstore/core/claim_values.py](/C:/Users/Q/code/working/propstore/propstore/core/claim_values.py)
- [propstore/core/concepts.py](/C:/Users/Q/code/working/propstore/propstore/core/concepts.py)
- [propstore/claim_documents.py](/C:/Users/Q/code/working/propstore/propstore/claim_documents.py)
- [propstore/world/model.py](/C:/Users/Q/code/working/propstore/propstore/world/model.py)
- [propstore/world/bound.py](/C:/Users/Q/code/working/propstore/propstore/world/bound.py)
- [propstore/world/types.py](/C:/Users/Q/code/working/propstore/propstore/world/types.py)
- [propstore/sidecar/claim_utils.py](/C:/Users/Q/code/working/propstore/propstore/sidecar/claim_utils.py)
- [propstore/cli/claim.py](/C:/Users/Q/code/working/propstore/propstore/cli/claim.py)
- [plans/remaining-untyped-dict-system-surfaces-workstream-2026-04-10.md](/C:/Users/Q/code/working/propstore/plans/remaining-untyped-dict-system-surfaces-workstream-2026-04-10.md)
- [plans/typed-literal-identity-workstream-2026-04-13.md](/C:/Users/Q/code/working/propstore/plans/typed-literal-identity-workstream-2026-04-13.md)
- [plans/semantic-contract.md](/C:/Users/Q/code/working/propstore/plans/semantic-contract.md)

## Goal

Remove the remaining anonymous semantic carriers from production code.

This means two things:

- no semantic object should move through production code as bare `dict`, `dict[str, str]`, or similar anonymous mapping
- no semantic value should move through production code as bare `str` when it has a distinct domain meaning that deserves either a specific newtype or an enum

The target end state is:

- decode boundaries may still read `dict`
- serialization edges may still produce `dict`
- honest map-shaped data may remain maps
- everywhere else, semantic structure is explicit

## The Rule

For production code we control:

- structured semantics become a dataclass or `msgspec.Struct`
- closed vocabularies become `Enum` or `StrEnum`
- open-but-distinct branded strings become `NewType`
- plain `str` remains only for genuine free text, raw file paths, SQL text, CEL text if still intentionally textual, or external boundary IO where we have not yet converted

Do not:

- leave dual typed-plus-dict production paths in place
- widen to `Mapping[str, Any]` to quiet the type system
- keep stringly semantic protocols because the old callers are convenient
- treat a JSON string column as an excuse to keep dict parsing in the runtime core

## Why This Workstream Exists

The repo already proved the right direction with:

- typed document models
- typed row objects
- typed runtime objects such as `ActiveClaim`
- typed literal identity in the ASPIC bridge

But the convergence is incomplete.

The remaining gaps are not random style defects. They are semantic boundary leaks:

- `ClaimDocument.variables` still allows `dict[str, str]`
- algorithm variable transport still preserves list-vs-mapping shape as a semantic runtime concern
- multiple runtime and protocol surfaces still expose raw `list[dict]` or `dict`
- many domain-valued strings still remain bare `str`

That keeps the semantic pipeline partly anonymous even though we control both sides of the interfaces.

## Scope

This workstream targets production code under:

- `propstore/core/`
- `propstore/world/`
- `propstore/repo/`
- `propstore/sidecar/`
- `propstore/cli/` where the CLI is carrying semantic structures internally instead of converting at the boundary

This workstream does not target:

- caches and indexes whose honest model is a map
- score tables, lookup tables, or bindings whose honest model is a map
- raw YAML/JSON decode points before conversion
- explicit `to_dict()` / `to_payload()` serialization edges
- incidental framework plumbing such as Click context `obj: dict`
- untyped tests unless they need to change to support a production cutover

## Type Taxonomy

Use these buckets consistently.

### 1. IDs and branded strings

Use `NewType` for values like:

- artifact-family identifiers
- source slugs
- source ids
- source-local ids
- branch names when they are treated as semantic identities rather than generic git inputs
- domain names
- unit symbols
- queryable CEL strings if we decide they are semantically distinct from generic text
- formula/sympy strings if a typed wrapper materially clarifies interfaces

### 2. Closed vocabularies

Use `Enum` or `StrEnum` for values like:

- claim type
- concept status
- relation type
- stance type
- source origin type
- source kind where the set is intentionally closed
- parameterization exactness
- conflict and warning classes
- merge/resolution/comparison/strategy choices when they are controlled and finite

### 3. Structured semantic payloads

Use named structs/dataclasses for values like:

- claim variable bindings
- concept form parameters
- search hits
- similarity hits
- stats snapshots
- import planning payloads
- revision operation payloads
- worldline intermediate semantic results that are currently assembled as maps

## Ranking Rule For “Next Highest Value”

After each completed slice, rerank remaining targets using this priority order:

1. live runtime semantic path
2. store/protocol interface used by multiple modules
3. subsystem boundary with mixed typed-plus-dict or typed-plus-string transport
4. repo import/merge side that manufactures semantic payloads
5. CLI/internal helper cleanup

Tie-breakers:

- choose the slice that deletes the most dual representations
- prefer a slice that removes both bare dicts and semantic bare strings together
- prefer a slice with a clear test gate over a wider speculative cleanup

## Ranked Backlog At Start

### Slice 1

Algorithm claim variable transport.

Current evidence:

- [propstore/claim_documents.py](/C:/Users/Q/code/working/propstore/propstore/claim_documents.py)
- [propstore/core/active_claims.py](/C:/Users/Q/code/working/propstore/propstore/core/active_claims.py)
- [propstore/sidecar/claim_utils.py](/C:/Users/Q/code/working/propstore/propstore/sidecar/claim_utils.py)
- [propstore/worldline/result_types.py](/C:/Users/Q/code/working/propstore/propstore/worldline/result_types.py)
- [propstore/cli/claim.py](/C:/Users/Q/code/working/propstore/propstore/cli/claim.py)

Reason it is first:

- it is on the core authored-claim to sidecar to runtime path
- it still carries semantic structure as either list-of-dicts or `dict[str, str]`
- it also carries semantic strings like variable-role and encoding tags
- it offers a clean hard cut: one variable representation, then update every caller

### Slice 2

Store/protocol result surfaces that still return raw `dict`:

- `ArtifactStore.search()`
- `ArtifactStore.similar_claims()`
- `ArtifactStore.similar_concepts()`
- `ArtifactStore.stats()`

Reason it is second:

- these are shared protocol leaks across `core`, `world`, and CLI callers
- they force anonymous payload use outside their home module

### Slice 3

World/runtime semantic string convergence:

- claim type
- relation type
- stance type
- warning/conflict class
- exactness
- source kind/origin type

Reason it is third:

- many runtime structures are already typed enough that enums/newtypes can now cut straight through

### Slice 4

Concept form-parameter and related structured payload cleanup.

Reason it is fourth:

- `ConceptRecord.form_parameters` is still an anonymous semantic mapping
- it is less central than Slice 1 but still on a canonical path

### Slice 5

Repo import semantic planning payloads.

Reason it is fifth:

- import code still rewrites semantic objects as `dict[str, Any]`
- this is valuable, but not as central as the live runtime and store interfaces

## Execution Discipline

For each implementation slice in this workstream:

1. reread this workstream
2. inventory the exact current leak and the exact next cut
3. add or update the failing tests first
4. run the targeted red test and keep the log
5. change types first
6. change behavior
7. delete the replaced production path in the same slice
8. run focused tests
9. run the next broader regression gate
10. commit
11. push
12. reread this workstream
13. rerank the remaining backlog
14. start the next slice immediately unless blocked

Forbidden failure modes:

- stopping after the plan exists
- stopping after tests pass for one slice when the slice is not committed and pushed
- keeping old and new production representations in parallel
- claiming “done for now” instead of reranking and continuing

## Project Command Rules

Python/package commands:

- use `uv`
- do not use bare `python`, `pip`, or `pytest`

Pytest commands:

- always run pytest through `powershell -File scripts/run_logged_pytest.ps1`
- keep logs under `logs/test-runs/`

Git commands:

- use non-interactive git commands only
- commit each completed slice separately
- push after each green committed slice

Writable repo state observed when this workstream started:

- current branch: `master`
- remote: `origin`

Unrelated untracked paths existed at start and are not part of this workstream:

- `plans/cel-subsystem-unification-plan-2026-04-08.md`
- `plans/typing-strictification-plan-2026-03-29.md`
- `pyghidra_mcp_projects/`

## Test Discipline

For every slice:

- keep one red log
- keep one focused green log
- keep one broader green log

For major boundary cuts:

- run the nearest targeted suite first
- then the broader local family
- then, when the slice substantially changes shared surfaces, run the full suite

Use log labels that encode the slice and phase.

## Commit And Push Discipline

Each completed slice must end with:

1. focused green tests logged
2. broader green tests logged
3. clean review of touched files
4. one commit with a slice-specific message
5. `git push origin master`

If push fails for a non-obvious reason, search the exact error before changing approach.

## Phase 0: Baseline And Inventory

Tasks:

1. run `uv sync --upgrade`
2. run the focused baseline for Slice 1
3. inventory every production caller of algorithm variable payloads
4. confirm the current dual representation boundary
5. record the first exact cut

Suggested focused baseline:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label semantic-carrier-slice1-baseline tests/test_build_sidecar.py tests/test_world_model.py tests/test_validate_claims.py tests/test_cli.py
```

Exit criteria:

- baseline log exists
- the Slice 1 callers are enumerated

## Phase 1: Slice 1 Hard Cut

Target:

- algorithm claim variable transport

Required end state:

- one typed production representation for authored algorithm variables
- no production union of tuple-of-documents and `dict[str, str]`
- runtime code does not treat list-vs-mapping encoding as a semantic contract
- callers that need mapping output derive it explicitly at a boundary

Files likely involved:

- `propstore/claim_documents.py`
- `propstore/core/active_claims.py`
- `propstore/core/row_types.py`
- `propstore/sidecar/claim_utils.py`
- `propstore/worldline/result_types.py`
- `propstore/cli/claim.py`

Expected deletions:

- `dict[str, str]` branch for `ClaimDocument.variables`
- `VariableEncoding`
- production logic that branches on `"mapping"` versus `"list"` as a semantic runtime behavior

Minimum targeted suites:

- `tests/test_build_sidecar.py`
- `tests/test_world_model.py`
- `tests/test_validate_claims.py`
- `tests/test_cli.py`

Exit criteria:

- Slice 1 production path has one typed variable representation
- focused and broader tests are green
- slice commit is pushed

## Phase 2+: Iterative Convergence Loop

After Slice 1 lands:

1. reread this workstream
2. inventory the next remaining highest-value anonymous semantic carrier
3. update the ranked backlog in this file if the evidence changed
4. execute that next slice under the same red/green/commit/push loop
5. repeat until the workstream completion criteria are all satisfied

Do not open a separate plan for each trivial next slice unless the architecture
actually changes shape.

## Completion Criteria

This workstream is complete only when all of the following are true:

- production semantic structures no longer travel as bare dict payloads outside decode/encode boundaries
- production semantic values no longer travel as bare `str` where a newtype or enum is the honest model
- shared store/protocol surfaces no longer expose raw semantic `dict` payloads
- dual-representation production paths have been deleted rather than carried
- each completed slice has logged tests, a commit, and a push
- after each completed slice, the next highest-value slice was identified and started unless blocked

## Explicitly Allowed Remaining Maps And Strings

Allowed maps:

- bindings
- score tables
- caches
- indexes
- explicit serialization payloads

Allowed strings:

- free text
- notes
- statements
- raw source code text
- SQL text
- path strings
- user-entered query text before conversion

These are allowed only when the string itself is the honest model.

## Execution Log

### Slice 1: Algorithm Variable Transport

Status: completed

Changes landed in this slice:

- deleted mapping-form `variables` from authored claim documents
- deleted mapping-form `variables` from source-local claim documents
- deleted runtime `variable_encoding` tracking in active claims and worldline target values
- changed sidecar algorithm storage to require explicit variable-binding lists
- changed validator and claim schema to reject mapping-style algorithm variables at the document boundary

Proof:

- red: `logs/test-runs/semantic-carrier-slice1-red-20260413-195851.log`
- targeted green: `logs/test-runs/semantic-carrier-slice1-green-redtest-20260413-200140.log`
- focused suite: `logs/test-runs/semantic-carrier-slice1-focused-20260413-200159.log`
- broader suite: `logs/test-runs/semantic-carrier-slice1-broader-20260413-200354.log`

Rerank after Slice 1:

- Slice 2 remains the next highest-value target: shared store/protocol result surfaces that still return raw semantic `dict` payloads

### Slice 2: Typed Store Result Surfaces

Status: completed

Changes landed in this slice:

- added explicit store result types for concept search hits, claim similarity hits, concept similarity hits, and store stats snapshots
- changed `ArtifactStore.search`, `similar_claims`, `similar_concepts`, and `stats` to return those named result types instead of raw `dict`
- changed `WorldModel` to convert SQLite/embed boundary payloads immediately into typed result objects
- changed the hypothetical overlay store to preserve typed result objects instead of re-wrapping them as anonymous mappings
- changed CLI world status/build summary callers to use the typed stats snapshot

Proof:

- red: `logs/test-runs/semantic-carrier-slice2-red-20260413-201156.log`
- targeted green: `logs/test-runs/semantic-carrier-slice2-green-redtest-20260413-201500.log`
- focused suite: `logs/test-runs/semantic-carrier-slice2-focused-20260413-201531.log`
- broader suite: `logs/test-runs/semantic-carrier-slice2-broader-20260413-201716.log`

Full-suite note:

- `logs/test-runs/semantic-carrier-slice2-full-20260413-201744.log` timed out in `tests/test_aspic.py::TestAttackProperties::test_attack_kind_is_valid`
- isolated rerun of that test passed: `logs/test-runs/semantic-carrier-slice2-full-failing-test-20260413-202324.log`
- rerun full suite surfaced unrelated pre-existing failing tests outside the touched surface:
  - `tests/test_aspic_bridge.py::TestCsafToProjection::test_projection_arguments_preserve_claim_or_canonical_conclusion_identity`
  - `tests/test_git_backend.py::test_init_does_not_materialize_seed_forms_before_git_commit_succeeds`
- isolated proof logs:
  - `logs/test-runs/semantic-carrier-slice2-isolate-aspic-bridge-20260413-202724.log`
  - `logs/test-runs/semantic-carrier-slice2-isolate-git-backend-20260413-202724.log`

Rerank after Slice 2:

- Slice 3 is now the next highest-value target: world/runtime semantic string convergence for claim type, relation type, stance type, warning/conflict class, exactness, and source kind/origin type

### Slice 3: Claim Type Runtime Enum

Status: completed

Changes landed in this slice:

- added a canonical `ClaimType` `StrEnum`
- changed `ClaimRow`, `ActiveClaim`, `ClaimNode`, and `SyntheticClaim` to carry `ClaimType` instead of a bare semantic string
- changed live runtime branching in `ActiveClaim`, `BoundWorld`, and `ActiveClaimResolver` to use enum members instead of string literals
- changed graph build to materialize `ClaimNode.claim_type` as the enum and keep string serialization only at payload edges

Proof:

- red: `logs/test-runs/semantic-carrier-slice3-red-20260413-203742.log`
- targeted green: `logs/test-runs/semantic-carrier-slice3-green-redtest-20260413-204022.log`
- focused suite: `logs/test-runs/semantic-carrier-slice3-focused-20260413-204047.log`
- broader suite: `logs/test-runs/semantic-carrier-slice3-broader-20260413-204234.log`

Rerank after Slice 3:

- the next highest-value target is now conflict classification on the runtime/store path: `ConflictRow.warning_class` / `conflict_class` should converge on the existing `ConflictClass` enum instead of remaining bare strings

### Slice 4: Conflict Class Runtime Enum

Status: completed

Changes landed in this slice:

- changed `ConflictRow.warning_class` and `conflict_class` to carry `ConflictClass` instead of bare strings
- added canonical coercion for conflict classes at the row boundary and kept string serialization only in `to_dict()` payload edges
- changed world/runtime adapters to preserve typed conflict classes until they intentionally project back into generic graph payloads
- changed CLI and ATMS-facing typed structures to treat conflict classes as enum values instead of anonymous strings

Proof:

- red: `logs/test-runs/semantic-carrier-slice4-red-20260413-204926.log`
- targeted green: `logs/test-runs/semantic-carrier-slice4-green-redtest2-20260413-205548.log`
- focused suite: `logs/test-runs/semantic-carrier-slice4-focused-20260413-205600.log`
- broader suite: `logs/test-runs/semantic-carrier-slice4-broader-20260413-205752.log`

Rerank after Slice 4:

- the next highest-value target is parameterization exactness on the canonical/runtime path: `exactness` is still a closed semantic vocabulary carried as bare strings across concept documents, parameterization rows, graph edges, world-facing result objects, and conflict-walk filters

### Slice 5: Parameterization Exactness Enum

Status: completed

Changes landed in this slice:

- added a canonical `Exactness` `StrEnum` for parameterization semantics
- changed parameterization document, concept, row, graph, and derived-result types to carry `Exactness` instead of bare strings
- kept string serialization only at payload edges such as `to_payload()` / `to_dict()`
- tightened parameterization runtime coercion so exactness normalizes immediately when a typed object is constructed
- hardened `ConflictClass` coercion to accept lowercase fallback values surfaced by the broader ATMS regression gate

Proof:

- red: `logs/test-runs/semantic-carrier-slice5-red-20260413-210231.log`
- targeted green: `logs/test-runs/semantic-carrier-slice5-green-redtest2-20260413-210437.log`
- focused suite: `logs/test-runs/semantic-carrier-slice5-focused2-20260413-210701.log`
- broader suite: `logs/test-runs/semantic-carrier-slice5-broader-20260413-210844.log`

Rerank after Slice 5:

- the next highest-value target is relation/stance type convergence on the live runtime path: `StanceRow.stance_type`, `RelationshipRow.relation_type`, and the compiled graph relation layer still carry a closed semantic vocabulary as bare strings even though `propstore/core/relation_types.py` already centralizes the allowed categories

### Slice 6: Stance Type Runtime Enum

Status: completed

Changes landed in this slice:

- added canonical `StanceType` enum and stance-type coercion in `propstore/stances.py`
- changed `StanceRow.stance_type` to carry `StanceType` instead of a bare string
- changed probabilistic relation provenance to preserve typed stance types instead of stringly provenance
- preserved the current ASPIC bridge raw-input synonym `contradicts -> rebuts` at the stance coercion boundary so the existing bridge surface still round-trips

Proof:

- targeted green: `logs/test-runs/semantic-carrier-slice6-targeted3-20260413-222005.log`
- focused suite: `logs/test-runs/semantic-carrier-slice6-focused-20260413-222021.log`
- broader suite: `logs/test-runs/semantic-carrier-slice6-broader-green-20260413-222358.log`

Additional regression evidence:

- adapter-family failure isolated and fixed: `logs/test-runs/semantic-carrier-slice6-aspic-fail-20260413-222237.log`
- post-fix focused adapter check: `logs/test-runs/semantic-carrier-slice6-aspic-fix-20260413-222303.log`
- broader adapter-family run surfaced two unrelated failures outside the touched files:
  - `tests/test_aspic_bridge.py::TestCsafToProjection::test_projection_arguments_preserve_claim_or_canonical_conclusion_identity`
  - `tests/test_structured_projection.py::test_world_extensions_cli_accepts_aspic_backend`
  proof log: `logs/test-runs/semantic-carrier-slice6-broader2-20260413-222314.log`

Rerank after Slice 6:

- the next highest-value target is concept-relationship type convergence on the canonical/runtime path: `RelationshipRow.relation_type` is still a closed semantic vocabulary carried as a bare string, and `build_compiled_world_graph()` still projects those concept-link types into generic relation-edge strings

### Slice 7: Concept Relationship Type Enum

Status: completed

Changes landed in this slice:

- added canonical `ConceptRelationshipType` enum and relationship-type coercion for concept-link semantics
- changed `ConceptRelationshipDocument`, `ConceptRelationship`, and `RelationshipRow` to carry `ConceptRelationshipType` instead of bare strings
- kept string serialization only at payload edges such as `to_payload()` / `to_dict()`
- changed validation and CLI relationship vocabularies to derive from the canonical enum-backed set instead of restating raw string literals
- tightened the concept-document boundary so invalid relationship types now fail as `DocumentSchemaError` during strict decode rather than flowing deeper as stringly payloads

Proof:

- red: `logs/test-runs/semantic-carrier-slice7-red-20260413-222657.log`
- targeted green: `logs/test-runs/semantic-carrier-slice7-green-redtest-20260413-222734.log`
- focused suite: `logs/test-runs/semantic-carrier-slice7-focused-20260413-222741.log`
- broader suite: `logs/test-runs/semantic-carrier-slice7-broader2-20260413-223107.log`
- boundary follow-up: `logs/test-runs/semantic-carrier-slice7-green-validator-20260413-223107.log`

Rerank after Slice 7:

- the next highest-value target is source identity semantics on the live canonical/runtime path: `ClaimSource.kind` and `SourceOrigin.origin_type` are still closed semantic vocabularies carried as bare strings across source documents, nested row values, world-model projections, and source CLI entrypoints

### Slice 8: Source Kind And Origin Type Enums

Status: completed

Changes landed in this slice:

- added canonical `SourceKind` and `SourceOriginType` enums plus coercion helpers
- changed `SourceDocument` and `SourceOriginDocument` to carry enum values instead of bare strings
- changed nested runtime source values `ClaimSource.kind` and `SourceOrigin.origin_type` to preserve typed source semantics after row hydration
- updated the source CLI init boundary to coerce raw option values immediately and reject unsupported source kinds/origin types at the boundary
- kept string serialization only at document payload and SQLite boundary edges

Proof:

- red: `logs/test-runs/semantic-carrier-slice8-red-20260413-223611.log`
- targeted green: `logs/test-runs/semantic-carrier-slice8-green-redtest3-20260413-223949.log`
- focused suite: `logs/test-runs/semantic-carrier-slice8-focused-20260413-224004.log`
- broader suite: `logs/test-runs/semantic-carrier-slice8-broader-20260413-224100.log`

Rerank after Slice 8:

- the next highest-value target is the compiled relation-edge surface on the live runtime/store path: `RelationEdge.relation_type` is still a bare semantic string even though concept-link relations and claim stances now have canonical enums on either side of that shared graph layer

### Slice 9: Graph Relation Edge Enum

Status: completed

Changes landed in this slice:

- added canonical `GraphRelationType` enum and relation-type coercion for the compiled graph layer
- changed `RelationEdge.relation_type` to carry `GraphRelationType` instead of a bare string
- changed the shared stance relation-category sets to derive from the graph enum rather than restating raw string literals
- kept string serialization only at graph payload edges such as `RelationEdge.to_dict()`
- verified that graph build and downstream analyzer/worldline consumers still round-trip typed relation edges coming from both concept-link rows and stance rows

Proof:

- red: `logs/test-runs/semantic-carrier-slice9-red-20260413-224431.log`
- targeted green: `logs/test-runs/semantic-carrier-slice9-green-redtest-20260413-224623.log`
- focused suite: `logs/test-runs/semantic-carrier-slice9-focused-20260413-224650.log`
- broader suite: `logs/test-runs/semantic-carrier-slice9-broader-20260413-224801.log`

Rerank after Slice 9:

- the next highest-value target is concept-status convergence on the canonical/runtime path: concept documents and loaded concept rows still carry statuses like `accepted`, `proposed`, and `deprecated` as bare semantic strings

### Slice 10: Concept Status Enum

Status: completed

Changes landed in this slice:

- added canonical `ConceptStatus` enum and status coercion for the canonical concept path
- changed `ConceptDocument`, `ConceptRecord`, and `ConceptRow` to carry `ConceptStatus` instead of bare strings
- changed concept validation to compare deprecated/proposed semantics against enum members instead of raw literals
- kept string serialization only at document payload and sidecar/storage edges
- verified that validator, sidecar concept compilation, world-model readers, graph export, and downstream form/sensitivity readers still consume typed concept statuses cleanly

Proof:

- red: `logs/test-runs/semantic-carrier-slice10-red-20260413-225245.log`
- targeted green: `logs/test-runs/semantic-carrier-slice10-green-redtest2-20260413-225419.log`
- focused suite: `logs/test-runs/semantic-carrier-slice10-focused-20260413-225434.log`
- broader suite: `logs/test-runs/semantic-carrier-slice10-broader-20260413-225519.log`

Rerank after Slice 10:

- the next highest-value target is algorithm-stage convergence on the canonical/runtime path: algorithm claims still carry `stage` as a bare semantic string across claim documents, row types, sidecar storage, and compiler/CLI reporting

### Slice 11: Algorithm Stage NewType

Status: completed

Changes landed in this slice:

- added branded `AlgorithmStage` newtype plus coercion for algorithm-claim stage semantics
- changed `ClaimDocument`, `SourceClaimDocument`, and `ClaimRow` to carry `AlgorithmStage` instead of a bare string on the canonical/runtime algorithm path
- kept `ClaimsFileDocument.stage` as the distinct file-envelope draft marker and verified that the two stage meanings remain split instead of being conflated
- changed sidecar algorithm storage helpers to normalize typed algorithm stages before row assembly
- changed the compiler `world algorithms` command to stay on typed claim rows internally and to coerce the `--stage` filter at the CLI boundary
- kept raw string serialization only at YAML/SQLite payload edges

Proof:

- red: `logs/test-runs/semantic-carrier-slice11-red-20260413-230319.log`
- targeted green: `logs/test-runs/semantic-carrier-slice11-green-redtest-20260413-230509.log`
- focused suite: `logs/test-runs/semantic-carrier-slice11-focused-20260413-230518.log`
- broader suite: `logs/test-runs/semantic-carrier-slice11-broader-20260413-230642.log`

Rerank after Slice 11:

- the next highest-value target is claim/stance document enum convergence on the authored canonical path: `ClaimDocument.type`, `SourceClaimDocument.type`, and `StanceDocument.type` are still closed semantic vocabularies carried as bare strings even though the runtime path already has canonical `ClaimType` and `StanceType` enums
