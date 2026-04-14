# Canonical Concept Typing Workstream

Date: 2026-04-09

## Goal

Replace canonical concept-as-`dict` usage with explicit dataclasses across the concept pipeline.

This workstream is intentionally concept-first, not claim-first.

Target outcome:
- canonical concepts are represented by typed dataclasses
- concept nested structures are typed
- concept loading/normalization/context/CEL/sidecar concept compilation stop depending on raw concept dicts
- sidecar row types remain distinct from canonical concept types

Non-goal for this workstream:
- full claim-family typing
- full world/store row typing
- source-local proposal typing beyond what is required to keep concept compilation working

## Existing Typed Surfaces To Reuse

- `ConceptId` from [id_types.py](/C:/Users/Q/code/propstore/propstore/core/id_types.py#L8)
- `ContextId` and `JustificationId` where applicable from [id_types.py](/C:/Users/Q/code/propstore/propstore/core/id_types.py#L10)
- `FormDefinition` from [form_utils.py](/C:/Users/Q/code/propstore/propstore/form_utils.py#L46)
- `ConceptInfo` as a CEL-facing reduced projection from [cel_checker.py](/C:/Users/Q/code/propstore/propstore/cel_checker.py#L32)
- `ParameterizationRow` as a sidecar row boundary from [row_types.py](/C:/Users/Q/code/propstore/propstore/core/row_types.py#L111)
- `ConceptNode`, `RelationEdge`, `ParameterizationEdge`, `ProvenanceRecord` as runtime graph types from [graph_types.py](/C:/Users/Q/code/propstore/propstore/core/graph_types.py#L79)

Do not reuse as canonical concept types:
- `ConceptInfo`
- `ConceptNode`
- `ParameterizationRow`
- `LoadedEntry`

## New Canonical Types

Add a new canonical concept module, likely `propstore/core/concepts.py` or similar.

Minimum types:
- `LogicalId`
- `ConceptAlias`
- `ConceptRelationship`
- `ParameterizationSpec`
- `ConceptRecord`

Recommended fields:

`LogicalId`
- `namespace: str`
- `value: str`

`ConceptAlias`
- `name: str`
- `source: str | None = None`

`ConceptRelationship`
- `type: str`
- `target: ConceptId`
- `conditions: tuple[str, ...] = ()`
- `note: str | None = None`

`ParameterizationSpec`
- `inputs: tuple[ConceptId, ...]`
- `formula: str | None = None`
- `sympy: str | None = None`
- `exactness: str | None = None`
- `conditions: tuple[str, ...] = ()`

`ConceptRecord`
- `artifact_id: ConceptId`
- `canonical_name: str`
- `status: str`
- `definition: str`
- `form: str`
- `domain: str | None = None`
- `logical_ids: tuple[LogicalId, ...] = ()`
- `aliases: tuple[ConceptAlias, ...] = ()`
- `relationships: tuple[ConceptRelationship, ...] = ()`
- `parameterizations: tuple[ParameterizationSpec, ...] = ()`
- `form_parameters: Mapping[str, object] | tuple[tuple[str, object], ...] = ()`
- `range_min: float | None = None`
- `range_max: float | None = None`
- `replaced_by: ConceptId | None = None`
- `version_id: str | None = None`
- `created_date: str | None = None`
- `last_modified: str | None = None`

Notes:
- `form_parameters` can remain mapping-like initially if we want to avoid overfitting the first slice.
- `range` should stop being a raw list in the canonical object; split it into `range_min` and `range_max`.
- `parameterization_relationships` should be renamed at the canonical type layer to `parameterizations`.

## Architectural Invariants

- Canonical concept typing is the control surface for this workstream.
- `dict` is allowed only at YAML/JSON decode and encode boundaries.
- Sidecar rows must not become the canonical concept type.
- Runtime graph nodes must not become the canonical concept type.
- No old/new dual-path production API should survive at the end of the workstream.
- If an adapter is temporarily required, it must be strictly local and deleted before the workstream is declared complete.

## File Clusters

### Cluster A: Canonical concept types and parsing

Primary files:
- [validate.py](/C:/Users/Q/code/propstore/propstore/validate.py#L176)
- [loaded.py](/C:/Users/Q/code/propstore/propstore/loaded.py#L13)
- [data_utils.py](/C:/Users/Q/code/propstore/propstore/data_utils.py#L16)

Work:
- add canonical concept dataclasses
- add parse/serialize helpers
- move logical-id normalization for concepts into typed constructors or parser helpers
- replace `normalize_concept_record(data: dict) -> dict` with typed normalization returning `ConceptRecord`
- replace concept file load helpers that return bare concept dicts

Likely concrete API additions:
- `parse_concept_record(data: Mapping[str, object]) -> ConceptRecord`
- `concept_record_to_dict(concept: ConceptRecord) -> dict[str, object]`
- `normalize_concept_record(...)` becomes typed or is deleted in favor of parser/normalizer functions

### Cluster B: Compilation context and concept lookup

Primary files:
- [compiler/context.py](/C:/Users/Q/code/propstore/propstore/compiler/context.py#L23)

Work:
- replace `concept_payloads_by_id: Mapping[str, Mapping[str, Any]]` with typed concept storage
- build concept lookup from `ConceptRecord`, not raw payloads
- rewrite concept-reference rewriting over typed relationships and parameterizations
- stop deep-copying concept dicts into `_form_definition` payloads

Target shape:
- `CompilationContext.concepts_by_id: Mapping[ConceptId, ConceptRecord]`
- `CompilationContext.concept_lookup: Mapping[str, tuple[ConceptId, ...]]`
- `CompilationContext.cel_registry: Mapping[str, ConceptInfo]`

Open design choice:
- either store `FormDefinition` externally in `form_registry`, or attach it transiently in a typed view object
- do not inject `_form_definition` into the canonical concept object

### Cluster C: CEL registry projection

Primary files:
- [cel_checker.py](/C:/Users/Q/code/propstore/propstore/cel_checker.py#L42)
- [condition_classifier.py](/C:/Users/Q/code/propstore/propstore/condition_classifier.py#L17)
- [z3_conditions.py](/C:/Users/Q/code/propstore/propstore/z3_conditions.py#L21)

Work:
- make `build_cel_registry_from_loaded` and concept-info construction consume typed concepts
- keep `ConceptInfo` as the reduced CEL-facing type
- remove direct dependence on concept dict field scanning where possible

Desired final state:
- CEL receives `ConceptRecord -> ConceptInfo` projection
- no `dict[str, dict]` concept registries in CEL-facing code

### Cluster D: Concept validation

Primary files:
- [validate.py](/C:/Users/Q/code/propstore/propstore/validate.py#L212)

Work:
- rewrite validation to validate `ConceptRecord` objects
- keep YAML-shape validation at parse boundary
- move cross-reference validation to typed fields
- stop reading nested alias/logical-id/relationship/parameterization payloads as untyped dicts

Important:
- preserve current semantic checks
- avoid turning this into a claim-related workstream

### Cluster E: Sidecar concept compilation

Primary files:
- [sidecar/concepts.py](/C:/Users/Q/code/propstore/propstore/sidecar/concepts.py#L22)
- [sidecar/concept_utils.py](/C:/Users/Q/code/propstore/propstore/sidecar/concept_utils.py#L27)
- [parameterization_groups.py](/C:/Users/Q/code/propstore/propstore/parameterization_groups.py#L12)

Work:
- sidecar concept compilation should consume `ConceptRecord`
- replace concept utility helpers that accept `concept: dict`
- make parameterization grouping accept typed concepts
- stop rebuilding identity from raw dict scans

Desired final state:
- `populate_concepts`, `populate_aliases`, `populate_relationships`, `populate_parameterizations`, `populate_parameterization_groups`, and `build_concept_fts_index` consume typed concepts directly

### Cluster F: Immediate concept consumers outside the core pipeline

Primary files:
- [description_generator.py](/C:/Users/Q/code/propstore/propstore/description_generator.py#L13)
- [parameterization_groups.py](/C:/Users/Q/code/propstore/propstore/parameterization_groups.py#L12)
- [param_conflicts.py](/C:/Users/Q/code/propstore/propstore/param_conflicts.py#L38)
- [repo/repo_import.py](/C:/Users/Q/code/propstore/propstore/repo/repo_import.py#L179)

Work:
- update obvious concept consumers to typed concepts
- if a module only needs a reduced concept view, pass that reduced typed view explicitly

### Cluster G: Deliberately deferred source-local concept proposal typing

Files to defer unless needed:
- [source/concepts.py](/C:/Users/Q/code/propstore/propstore/source/concepts.py#L34)
- [source/registry.py](/C:/Users/Q/code/propstore/propstore/source/registry.py#L82)
- [source/promote.py](/C:/Users/Q/code/propstore/propstore/source/promote.py#L54)
- [source/alignment.py](/C:/Users/Q/code/propstore/propstore/source/alignment.py#L47)

Policy:
- these are source-local proposal surfaces, not the canonical concept core
- they may get a follow-on typed pass
- do not let them force canonical concept typing to preserve proposal-shaped fields

## Execution Sequence

### Phase 1: Introduce canonical concept dataclasses

Deliverables:
- new concept module with the types above
- parse/serialize helpers
- unit tests for parse/normalize/serialize and logical-id handling

Keep:
- old dict-based callers still compiling via small local adapters

Do not keep:
- new production logic that introduces more raw concept dict usage

### Phase 2: Convert concept validation and loading

Deliverables:
- typed concept loading from YAML
- typed concept normalization
- typed concept validation

Expected changed files:
- `propstore/validate.py`
- `propstore/data_utils.py`
- maybe `propstore/loaded.py` or typed wrappers around it

Checkpoint:
- concept validation should no longer require raw concept dicts past parse

### Phase 3: Convert compilation context

Deliverables:
- typed `CompilationContext`
- typed concept lookup builder
- typed reference rewriting for `replaced_by`, relationships, and parameterizations

Expected changed files:
- `propstore/compiler/context.py`

Checkpoint:
- no `Mapping[str, Any]` concept payload registry in `CompilationContext`

### Phase 4: Convert CEL projection

Deliverables:
- CEL registry constructors take typed concepts or typed concept iterables
- concept-info projection isolated and explicit

Expected changed files:
- `propstore/cel_checker.py`
- any direct callers building concept registries

### Phase 5: Convert sidecar concept compilation

Deliverables:
- sidecar concept population functions consume typed concepts
- parameterization grouping consumes typed concepts
- concept identity helper functions are typed or deleted

Expected changed files:
- `propstore/sidecar/concepts.py`
- `propstore/sidecar/concept_utils.py`
- `propstore/parameterization_groups.py`

Checkpoint:
- concept-side sidecar build no longer scans raw concept dicts

### Phase 6: Sweep direct concept consumers

Deliverables:
- update reduced consumers that were left behind
- delete temporary adapters

Expected changed files:
- `propstore/description_generator.py`
- `propstore/param_conflicts.py`
- `propstore/repo/repo_import.py`
- any remaining concept-dict helpers found during implementation

### Phase 7: Final cleanup

Deliverables:
- remove superseded dict-based concept helpers
- remove compatibility bridges added during Phases 1-6
- update docs if concept APIs changed materially

Completion gate:
- canonical concept flow is typed end to end
- no concept dicts in load/normalize/context/CEL/sidecar concept compilation path

## Temporary Adapters: Allowed and Forbidden

Allowed temporarily:
- local `to_dict()` only at YAML/JSON/SQL boundaries
- local projection from `ConceptRecord` to `ConceptInfo`
- local adapters for still-unconverted consumers during the middle phases

Forbidden:
- adding new global `concept: dict` helper APIs
- extending `CompilationContext` with both typed concepts and concept payload dicts as co-equal production paths
- using sidecar row types as canonical concept types

## Main Risks

### Risk 1: `LoadedEntry` keeps forcing dict payloads

Issue:
- `LoadedEntry.data` is currently `dict[str, Any]`

Mitigation:
- either introduce typed wrappers immediately
- or keep `LoadedEntry` only as raw file transport and parse into typed concepts at the first consumer

### Risk 2: `_form_definition` payload injection in `CompilationContext`

Issue:
- current code mutates concept payload dicts by injecting `_form_definition`

Mitigation:
- keep form data in a separate map or create a separate typed enriched view

### Risk 3: source-local proposal code drags proposal-only fields into canonical types

Issue:
- source proposal surfaces use `local_name`, `proposed_name`, `registry_match`

Mitigation:
- defer proposal typing or model it separately
- do not contaminate `ConceptRecord`

### Risk 4: sidecar utilities continue to back-compute identity from loose payloads

Issue:
- current `sidecar/concept_utils.py` rebuilds logical IDs and artifact IDs from dicts

Mitigation:
- once canonical concepts are typed, make sidecar utilities take typed concepts or delete them

## Verification Plan

Run targeted tests after each phase. Full command form in this repo must use `uv`.

Suggested focused suites:
- `uv run pytest -vv tests/test_validate_claims.py` only if concept registry coupling breaks claim validation
- `uv run pytest -vv tests/test_validator.py`
- `uv run pytest -vv tests/test_cel_checker.py` if present, otherwise CEL-related tests
- `uv run pytest -vv tests/test_world_model.py`
- `uv run pytest -vv tests/test_build_sidecar.py`
- `uv run pytest -vv tests/test_graph_build.py`
- `uv run pytest -vv tests/test_claim_compiler.py`

Project rule:
- tee full output to a timestamped file under `logs/test-runs/`

Completion verification:
- full suite run once the workstream is complete

## First Slice Recommendation

The first coding slice should be:

1. add `LogicalId`, `ConceptAlias`, `ConceptRelationship`, `ParameterizationSpec`, `ConceptRecord`
2. implement typed parse/normalize for canonical concepts
3. convert `compiler/context.py` to store typed concepts and build lookup/CEL projections from them

Reason:
- this gives the biggest rigor gain with the smallest initial blast radius
- it fixes the core concept registry/control surface before touching sidecar or source proposal code

## Definition Of Done

This workstream is done only when:
- canonical concept YAML is parsed into typed concepts immediately
- typed concepts are the only canonical concept representation in validation, compilation context, CEL projection, and sidecar concept compilation
- old dict-based canonical concept helpers are deleted
- source-local proposal code is either converted separately or isolated behind explicit boundary adapters
