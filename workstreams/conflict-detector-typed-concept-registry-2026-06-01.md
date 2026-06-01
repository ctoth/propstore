# Conflict Detector Typed Concept Registry Cutover - 2026-06-01

## Final State

Conflict detection consumes typed concept/form/parameterization inputs. No
Propstore production conflict-detector path accepts `dict[str, dict]` concept
registries, builds conflict concept payloads, or reads concept fields through
string-indexed mappings.

This is the prerequisite for deleting the `record.to_payload()` calls in
`propstore/compiler/context.py`.

## Owner Boundaries

- Conflict detector owns the typed input contract it needs for conflict checks:
  concept identity, reference keys, form name, optional `FormDefinition`, and
  parameterization edges.
- Compiler context owns compiler-side production from `ConceptRecord` and
  `FormDefinition`.
- World projection owns world-side production from the actual `Concept` and
  `Parameterization` rows.
- Quire remains the document I/O boundary. This workstream must not introduce
  document payload serialization.

## Deletion Targets

- `detect_conflicts(..., concept_registry: dict[str, dict], ...)`
- `detect_transitive_conflicts(..., concept_registry: dict[str, dict], ...)`
- `concept_registry_for_context_payloads`
- `concept_registry_for_world`
- `ConflictDetectorInputs.concept_registry: dict[str, dict]`
- `ConceptBehavior.conflict_detector_payload`
- `ParameterizationBehavior.conflict_detector_payload`
- `parameterization_edges_from_registry`
- conflict-detector reads like `value.get("form")`, `value.get("logical_ids")`,
  `value.get("parameterization_relationships")`

## Forbidden Replacements

- Parallel typed APIs beside dict APIs for the same semantic operation.
- `TypedThing | Mapping[...]` or `TypedThing | dict[...]` compatibility.
- `document_to_payload`, `to_document_builtins`, `msgspec.to_builtins`, or
  hand-built concept payload dictionaries.
- New `*_payload`, `*_dict`, `as_dict`, or mapping-normalizer helpers.

## Dependency Graph

- P1 typed detector contract has no prerequisite.
- P2 conflict detector implementation depends on P1.
- P3 compiler producer depends on P1 and P2.
- P4 world producer depends on P1 and P2.
- P5 public call-site/test cutover depends on P3 and P4.
- P6 deletion/search cleanup depends on P5.
- P7 verification depends on P6.

Topological order: P1, P2, P3, P4, P5, P6, P7.

## Phase Order

| Phase | Slice | Required State |
| --- | --- | --- |
| P1 | Typed detector input contract | A conflict-detector-owned typed contract exists for concept entries and parameterization edges. It is not a wrapper around payload dicts. |
| P2 | Detector implementation cutover | `detect_conflicts` and `detect_transitive_conflicts` use the typed contract in place, with no parallel typed API. |
| P3 | Compiler producer cutover | `concept_registry_for_context` returns the typed contract from `ConceptRecord` and `FormDefinition`; `concept_registry_for_context_payloads` is gone. |
| P4 | World producer cutover | `conflict_detector_inputs_for_world` returns the typed contract from `Concept` and `Parameterization` rows; world projection no longer builds dict registries. |
| P5 | Direct caller cutover | App, world, relation, and test helper direct callers use the typed contract. No independent dict producer remains for `detect_conflicts`. |
| P6 | Delete old paths | Delete row `conflict_detector_payload` methods and `parameterization_edges_from_registry`; remove string-indexed concept-registry reads. |
| P7 | Verify | Search gates are green; focused tests and pyright run through project wrappers. |

## Search Gates

- `rg -n "concept_registry: dict\\[str, dict\\]|dict\\[str, dict\\].*concept_registry" propstore tests`
- `rg -n -F "concept_registry_for_context_payloads" propstore tests`
- `rg -n -F "concept_registry_for_world" propstore tests`
- `rg -n -F "conflict_detector_payload" propstore tests`
- `rg -n -F "parameterization_edges_from_registry" propstore tests`
- `rg -n -F "record.to_payload()" propstore/compiler/context.py`
- `rg -n "get\\(\"form\"\\)|get\\(\"logical_ids\"\\)|get\\(\"parameterization_relationships\"\\)" propstore/conflict_detector`

## Verification Gates

- `uv run pyright propstore`
- `powershell -File scripts/run_logged_pytest.ps1 tests/test_conflict_detector.py tests/test_param_conflicts.py tests/test_parameter_conflict_unit_aware.py`
- `powershell -File scripts/run_logged_pytest.ps1 tests/test_claim_compiler.py tests/test_world_query.py`

## Current Evidence

- `propstore/compiler/context.py:240` builds a dict registry by calling
  `record.to_payload()` and adding `_form_definition`.
- `propstore/conflict_detector/orchestrator.py:43` accepts
  `concept_registry: dict[str, dict]`.
- `propstore/conflict_detector/orchestrator.py:232` and `:244` read concept
  registry values as mappings.
- `propstore/conflict_detector/parameterization_conflicts.py` reads `form`,
  `canonical_name`, and `parameterization_relationships` through mapping APIs.
- `propstore/world/conflict_projection.py:17` stores a dict concept registry in
  `ConflictDetectorInputs`.
- `propstore/world/conflict_projection.py:28` builds that registry from
  `ConceptBehavior.conflict_detector_payload()` and
  `ParameterizationBehavior.conflict_detector_payload()`.
- `propstore/world/bound.py:136` calls `detect_conflicts` with the world
  projection registry.

## Execution Rule

Run one phase at a time. Each phase must either keep a typed reduction that
removes an old path or stop with the exact first independent caller that blocks
the phase. Do not add compatibility bridges to make a phase pass.

## Execution Log

### Slice 1 - Detector Registry Contract Cutover

Changed production detector registry flow in place:

- Added detector-owned `ConflictConceptRegistry`, `ConflictConcept`, and
  `ConflictParameterization` typed inputs.
- Changed `detect_conflicts`, `detect_transitive_conflicts`,
  `compile_conflict_witness_models`, compiler conflict projection, world
  conflict projection, and merge classification to use the typed registry.
- Deleted `concept_registry_for_context_payloads`.
- Deleted `concept_registry_for_world`.
- Deleted `ConceptBehavior.conflict_detector_payload`.
- Deleted `ParameterizationBehavior.conflict_detector_payload`.
- Deleted `parameterization_edges_from_registry`.
- Deleted `build_authored_concept_registry`; claim compilation now reads
  concept form/name facts through the existing compilation context instead of
  an authored concept payload registry.

Gate results:

- Pass: `uv run pyright propstore`
- Pass: `rg -n "concept_registry: dict\\[str, dict\\]|dict\\[str, dict\\].*concept_registry" propstore tests`
- Pass: `rg -n -F "concept_registry_for_context_payloads" propstore tests`
- Pass: `rg -n -F "concept_registry_for_world" propstore tests`
- Pass: `rg -n -F "conflict_detector_payload" propstore tests`
- Pass: `rg -n -F "parameterization_edges_from_registry" propstore tests`
- Pass: `rg -n -F "record.to_payload()" propstore/compiler/context.py`
- Pass: `rg -n -F 'get("form")' propstore/conflict_detector`
- Pass: `rg -n -F 'get("logical_ids")' propstore/conflict_detector`
- Pass: `rg -n -F 'get("parameterization_relationships")' propstore/conflict_detector`

Remaining broader payload work after this slice:

- `rg -n -F ".to_payload(" propstore` reports 64 production call sites.
- `rg -n -F ".from_payload(" propstore` reports 3 production call sites.
