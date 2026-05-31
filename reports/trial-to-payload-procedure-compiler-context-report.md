# `to_payload` Call Procedure Report

Target call:
- `propstore/compiler/context.py:240`

Classification:
- Receiver: `record` from `concepts_by_id.items()`, statically a `ConceptRecord`.
- Owner: Concept semantic fields belong to `propstore.families.concepts.stages.ConceptRecord`; form metadata belongs to `CompilationContext.form_registry`; alias/key expansion belongs to the existing `FamilyReferenceIndex[ConceptRecord]`.
- Intent: Build an internal conflict-detector concept registry keyed by artifact id and unique concept reference keys. The returned payload is consumed for `artifact_id`/`id`, `form`, `_form_definition`, `logical_ids`, `canonical_name`, and `parameterization_relationships`.
- Boundary: Internal compiler/app/conflict-detection logic, not external I/O, file rendering, YAML/JSON encoding, or a Quire serialization boundary.
- Disposition: Replace the payload registry with typed owner access. Keep `ConceptRecord` as the concept value, pair it with `FormDefinition` through the existing compiler context/form registry, and update conflict detection to read typed fields instead of string-indexed payload fields. Do not create a renamed payload helper or a dict-shaped projection.
- Search gate: `rg -n -F "record.to_payload()" propstore/compiler/context.py` must no longer report `propstore/compiler/context.py:240`.
- Expected follow-on: The first follow-on failure should be the conflict detector registry contract, because `detect_conflicts` and helpers currently require `dict[str, dict]` values and validate `artifact_id`/`id` through mapping access.

Verdict:
- PASS. The procedure points to a deletion-first typed repair: delete the payload-shaped compiler registry path and make the conflict detector consume typed concept/form data. It does not require, recommend, or preserve a renamed payload/dict replacement.

Evidence:
- `propstore/compiler/context.py:43` - `CompilationContext.concepts_by_id` stores `Mapping[str, ConceptRecord]`.
- `propstore/compiler/context.py:232` - `concept_registry_for_context_payloads` receives `Mapping[str, ConceptRecord]`.
- `propstore/compiler/context.py:240` - target call is `payload = record.to_payload()`.
- `propstore/compiler/context.py:243` - the caller mutates the payload with `_form_definition`.
- `propstore/families/concepts/stages.py:190` - `ConceptRecord` is the typed concept record class.
- `propstore/families/concepts/stages.py:191` - `ConceptRecord` owns `artifact_id`.
- `propstore/families/concepts/stages.py:204` - `ConceptRecord` owns typed `parameterizations`.
- `propstore/app/claims.py:366` - app conflict detection builds `registry = concept_registry_for_context(context)`.
- `propstore/conflict_detector/orchestrator.py:237` - conflict projection reads `form` from registry mappings.
- `propstore/conflict_detector/orchestrator.py:249` - concept form projection reads `form` from registry mappings.
- `propstore/conflict_detector/orchestrator.py:255` - concept form projection reads `logical_ids` from registry mappings.
- `propstore/conflict_detector/orchestrator.py:303` - validation requires `artifact_id` or `id` from each registry mapping.
- `propstore/conflict_detector/parameterization_conflicts.py:69` - normalization reads concept `form` through mapping access.
- `propstore/conflict_detector/parameterization_conflicts.py:112` - symbol generation reads `canonical_name` through mapping access.
- `propstore/conflict_detector/parameterization_conflicts.py:442` - parameterization conflict detection reads `parameterization_relationships` through mapping access.
