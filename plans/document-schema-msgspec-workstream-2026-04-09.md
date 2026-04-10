# Document Schema Msgspec Workstream

Date: 2026-04-09

## Goal

Replace the current loader story:

- `yaml.safe_load(...)`
- raw `dict`
- normalize/repair helpers
- validation over anonymous maps
- later conversion into semantic objects

with a document-schema architecture:

1. read bytes from disk or `KnowledgePath`
2. decode one YAML file into one typed `...Document`
3. convert immediately into canonical domain objects where appropriate
4. keep `dict` only at explicit serialization/report boundaries

This is not just “add msgspec”. It is a full cleanup of the repo’s YAML ingress
story.

## Naming And Layers

Use `document` as the layer term.

That gives four clean layers:

- document layer
  - typed on-disk YAML shape
  - `ConceptDocument`, `ClaimsFileDocument`, `WorldlineDocument`, etc.
- domain layer
  - canonical semantic objects
  - `ConceptRecord`, canonical claims, contexts, forms, worldline runtime objects
- row layer
  - sidecar/storage objects
  - `ClaimRow`, `ConceptRow`, `StanceRow`, etc.
- runtime layer
  - world/revision/worldline execution objects

This matters because the repo has been blurring those layers.

The point of the workstream is:
- document objects are not raw dicts
- document objects are not canonical domain objects unless the shape is truly identical
- document objects are not sidecar rows

## Shared Module

The shared decode module should be:

- [document_schema.py](/C:/Users/Q/code/propstore/propstore/document_schema.py)

Not `typed_yaml.py`.

Reason:
- the important role is schema-bound document decoding
- not “typed YAML” as a transport trick

## Why This Workstream Exists

The current repo still has many YAML ingress points that decode to raw maps and
then mutate them:

- [validate.py](/C:/Users/Q/code/propstore/propstore/validate.py)
- [validate_claims.py](/C:/Users/Q/code/propstore/propstore/validate_claims.py)
- [data_utils.py](/C:/Users/Q/code/propstore/propstore/data_utils.py)
- [form_utils.py](/C:/Users/Q/code/propstore/propstore/form_utils.py)
- [loaded.py](/C:/Users/Q/code/propstore/propstore/loaded.py)
- [compiler/context.py](/C:/Users/Q/code/propstore/propstore/compiler/context.py)
- [core/concepts.py](/C:/Users/Q/code/propstore/propstore/core/concepts.py)
- [worldline/definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py)
- [source/concepts.py](/C:/Users/Q/code/propstore/propstore/source/concepts.py)
- [source/claims.py](/C:/Users/Q/code/propstore/propstore/source/claims.py)
- [source/relations.py](/C:/Users/Q/code/propstore/propstore/source/relations.py)
- [source/common.py](/C:/Users/Q/code/propstore/propstore/source/common.py)
- [artifact_codes.py](/C:/Users/Q/code/propstore/propstore/artifact_codes.py)

That is why the repo still has:
- silent field repair
- widening to `dict[str, Any]`
- normalize-first, validate-later shape mutation
- loader code acting like a hidden migration engine

## Technology Choice

Use `msgspec`.

Reason:
- lightweight dependency
- strict typed decode
- good fit for “decode boundary only”
- does not try to become the whole application model

Do not use Pydantic as the primary solution here.

## Controlled-Stack Assumption

This repo controls the relevant YAML files and the callers that consume them.

That means this workstream should be executed as a hard cut:

- no compatibility readers
- no permissive fallback parse path
- no old/new dual-path document loading
- strict unknown-field failure is correct
- when a document interface changes, fix every caller rather than carrying a bridge

There is no requirement here to preserve loose behavior for hand-authored legacy
files. We do not have that constraint.

## Architectural Rules

- Core semantic/domain types remain plain dataclasses we control.
- Document types are the file-schema layer.
- The shared document-schema module owns generic decode mechanics and decode
  error shaping.
- Document modules own typed file shapes.
- Conversion from document types into canonical domain types is explicit.
- No `cast(...)`.
- No dual raw-dict / typed-document production path.
- No permissive unknown-field swallowing by default.
- No keeping `LoadedEntry.data: dict[str, Any]` as the central abstraction.
- If a document-family interface changes, update every caller instead of adding
  a compatibility layer.

## Non-goals

- Do not rewrite every YAML write path in the same first commit.
- Do not turn the whole repo into `msgspec.Struct` just because it is available.
- Do not unify source-local and canonical document models.
- Do not keep backward-compatibility shims for old shapes unless we explicitly
  have old repos/data we must support.
- Do not preserve loose parsing behavior for uncontrolled hand-authored files;
  that is not a constraint in this repo.

## Shared Boundary API

Add [document_schema.py](/C:/Users/Q/code/propstore/propstore/document_schema.py)
with a minimal API like:

- `decode_document_bytes(data: bytes, type_: type[T], *, source: str) -> T`
- `decode_document_path(path: KnowledgePath | Path, type_: type[T]) -> T`
- `load_document(path: KnowledgePath | Path, type_: type[T]) -> LoadedDocument[T]`

Responsibilities:
- bytes/path reading
- YAML parsing
- `msgspec` conversion into typed document object
- strict error wrapping with path and field context

This module should not own the actual document models.

## Replace `LoadedEntry`

The current [LoadedEntry](/C:/Users/Q/code/propstore/propstore/loaded.py) is
the wrong center of gravity because it makes “loaded file” mean “dict payload”.

Replace it with a typed envelope:

- `LoadedDocument[T]`
  - `filename: str`
  - `source_path: KnowledgePath | None`
  - `knowledge_root: KnowledgePath | None`
  - `document: T`

Then define family-specific aliases as needed:

- `LoadedConceptDocument`
- `LoadedClaimsFileDocument`
- `LoadedContextDocument`
- `LoadedWorldlineDocument`
- `LoadedSourceClaimsDocument`

If a compatibility wrapper is temporarily needed while callers are converted,
that wrapper must not remain the primary production path.

## Module Layout

Suggested additions:

- [document_schema.py](/C:/Users/Q/code/propstore/propstore/document_schema.py)
- [documents/](/C:/Users/Q/code/propstore/propstore/documents/) package:
  - [concepts.py](/C:/Users/Q/code/propstore/propstore/documents/concepts.py)
  - [claims.py](/C:/Users/Q/code/propstore/propstore/documents/claims.py)
  - [contexts.py](/C:/Users/Q/code/propstore/propstore/documents/contexts.py)
  - [forms.py](/C:/Users/Q/code/propstore/propstore/documents/forms.py)
  - [worldlines.py](/C:/Users/Q/code/propstore/propstore/documents/worldlines.py)
  - [source.py](/C:/Users/Q/code/propstore/propstore/documents/source.py)

Shared convention:

- `...Document` = on-disk file schema
- `...document_to_...(...)` = explicit conversion into canonical/domain objects

## Document Families

## Family A: Form documents

Current ingress:

- [form_utils.py](/C:/Users/Q/code/propstore/propstore/form_utils.py)

This is a strong first implementation slice because:
- the family is comparatively local
- forms are already conceptually typed
- the blast radius is small

Add:

- `FormDocument`
- nested form parameter/specification document types

Convert directly to:

- `FormDefinition`

Delete or reduce:
- raw dict-based form load helpers
- repeated `yaml.safe_load(...)` form parsing

## Family B: Worldline documents

Current ingress:

- [worldline/definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py)
- [cli/worldline_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/worldline_cmds.py)

Worldline is already mostly typed semantically. The file load is still:

- `yaml.safe_load(...)`
- `dict`
- `WorldlineDefinition.from_dict(...)`

Replace with:

- `WorldlineDocument`
- immediate conversion to `WorldlineDefinition`

This is the second recommended implementation slice because the domain side is
already largely ready.

## Family C: Canonical concept documents

Current ingress:

- [validate.py](/C:/Users/Q/code/propstore/propstore/validate.py)
- [data_utils.py](/C:/Users/Q/code/propstore/propstore/data_utils.py)
- [compiler/context.py](/C:/Users/Q/code/propstore/propstore/compiler/context.py)
- [cel_checker.py](/C:/Users/Q/code/propstore/propstore/cel_checker.py)
- [core/concepts.py](/C:/Users/Q/code/propstore/propstore/core/concepts.py)

Add:

- `ConceptDocument`
- nested document types for:
  - logical ids
  - aliases
  - relationships
  - parameterizations

Convert explicitly to:

- `ConceptRecord`

Important:

- artifact-id derivation, logical-id synthesis, version-id computation, and
  similar canonicalization logic should become explicit document-to-domain
  conversion logic
- not “normalize dict” helpers

Delete or reduce:

- `normalize_concept_payload`
- raw `concept.data[...]` access
- dict-shaped concept load paths in compiler/CEL code

## Family D: Canonical context documents

Current ingress:

- [validate_contexts.py](/C:/Users/Q/code/propstore/propstore/validate_contexts.py)
- [context_types.py](/C:/Users/Q/code/propstore/propstore/context_types.py)

Add:

- `ContextDocument`

Convert directly to:

- `LoadedContext` or the canonical context record type

No raw `dict` transit should remain after the file decode boundary.

## Family E: Canonical claim documents

Current ingress:

- [validate_claims.py](/C:/Users/Q/code/propstore/propstore/validate_claims.py)
- [identity.py](/C:/Users/Q/code/propstore/propstore/identity.py)
- [compiler/passes.py](/C:/Users/Q/code/propstore/propstore/compiler/passes.py)
- [sidecar/claims.py](/C:/Users/Q/code/propstore/propstore/sidecar/claims.py)
- [conflict_detector/*](/C:/Users/Q/code/propstore/propstore/conflict_detector)

This is the largest and riskiest family because it is multi-record, heavily used,
and still partly compiler-shaped.

Add:

- `ClaimDocument`
- `ClaimsFileDocument`
- nested document types for:
  - provenance
  - source
  - logical ids
  - variables
  - parameters
  - embedded stances or related sections if they still exist in claim files

Convert explicitly into:

- the canonical claim family or the nearest typed compiler-facing claim surface

Important:

- recursive schema-coercion helpers should be deleted or sharply reduced
- JSON Schema may remain as an external contract check if useful, but it must
  not remain the primary typed representation mechanism

## Family F: Source-local authoring documents

Current ingress:

- [source/concepts.py](/C:/Users/Q/code/propstore/propstore/source/concepts.py)
- [source/claims.py](/C:/Users/Q/code/propstore/propstore/source/claims.py)
- [source/relations.py](/C:/Users/Q/code/propstore/propstore/source/relations.py)
- [source/common.py](/C:/Users/Q/code/propstore/propstore/source/common.py)
- [source/promote.py](/C:/Users/Q/code/propstore/propstore/source/promote.py)
- [source/finalize.py](/C:/Users/Q/code/propstore/propstore/source/finalize.py)

These must get their own document types:

- `SourceDocument`
- `SourceClaimsDocument`
- `SourceConceptsDocument`
- `SourceJustificationsDocument`
- `SourceStancesDocument`

These are not canonical concept/claim documents. They carry source-local proposal
and linking fields that must stay in the source subsystem.

## Family G: Utility/document readers

Current ingress:

- [artifact_codes.py](/C:/Users/Q/code/propstore/propstore/artifact_codes.py)
- [cli/helpers.py](/C:/Users/Q/code/propstore/propstore/cli/helpers.py)
- [repo/git_backend.py](/C:/Users/Q/code/propstore/propstore/repo/git_backend.py)
- [source/common.py](/C:/Users/Q/code/propstore/propstore/source/common.py)

These should stop being ad hoc `yaml.safe_load(...) or {}` readers for document
families we control. They should route through `document_schema.py`.

## Strictness Policy

Default decode policy:

- required fields must be present
- unknown fields fail by default
- unions are explicit
- number/string coercion is not implicit unless the document family explicitly
  allows it
- defaults live in the document types, not in free-floating loader repair code

Exceptions:

- source-local proposal docs may allow additional optional metadata when that is
  a deliberate part of the source subsystem
- if an old shape is still emitted by code we control, change the writer and
  reader together rather than adding a permanent compatibility shim

In this repo, “strict by default” is the intended behavior, not a later cleanup
phase. Because we control the files and callers, breakages should be fixed at
the caller/writer rather than tolerated in the document reader.

## Msgspec Usage Model

Use `msgspec` at the document-schema layer.

Recommended model:

- document types may be `msgspec.Struct` if convenient
- canonical semantic/domain types remain stdlib dataclasses
- conversion from document to domain stays explicit

That keeps the dependency in the document layer and prevents model-framework
semantics from leaking into the semantic core.

## Execution Order

This should land in many commits.

### Commit 1: Add `msgspec` and `document_schema.py`

Files:

- [pyproject.toml](/C:/Users/Q/code/propstore/pyproject.toml)
- new [document_schema.py](/C:/Users/Q/code/propstore/propstore/document_schema.py)

End state:

- shared document decode boundary exists
- strict decode/error shape exists

### Commit 2: Add typed document envelope and demote raw `LoadedEntry`

Files:

- [loaded.py](/C:/Users/Q/code/propstore/propstore/loaded.py)
- new typed loaded-document envelope module if needed

End state:

- new code can traffic in `LoadedDocument[T]`
- raw `LoadedEntry.data` stops being the preferred production abstraction

### Commit 3: Form documents

Files:

- [form_utils.py](/C:/Users/Q/code/propstore/propstore/form_utils.py)
- new [documents/forms.py](/C:/Users/Q/code/propstore/propstore/documents/forms.py)

End state:

- forms decode through document schema
- `FormDefinition` loading stops starting from dicts

### Commit 4: Worldline documents

Files:

- [worldline/definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py)
- [cli/worldline_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/worldline_cmds.py)
- new [documents/worldlines.py](/C:/Users/Q/code/propstore/propstore/documents/worldlines.py)

End state:

- worldline files decode through `WorldlineDocument`
- `yaml.safe_load(...) -> from_dict(...)` path is gone there

### Commit 5: Canonical concept documents

Files:

- [core/concepts.py](/C:/Users/Q/code/propstore/propstore/core/concepts.py)
- [validate.py](/C:/Users/Q/code/propstore/propstore/validate.py)
- [compiler/context.py](/C:/Users/Q/code/propstore/propstore/compiler/context.py)
- [cel_checker.py](/C:/Users/Q/code/propstore/propstore/cel_checker.py)
- [data_utils.py](/C:/Users/Q/code/propstore/propstore/data_utils.py)
- new [documents/concepts.py](/C:/Users/Q/code/propstore/propstore/documents/concepts.py)

End state:

- canonical concept file ingest is typed
- compiler/CEL no longer start from concept dicts

### Commit 6: Canonical context documents

Files:

- [validate_contexts.py](/C:/Users/Q/code/propstore/propstore/validate_contexts.py)
- [context_types.py](/C:/Users/Q/code/propstore/propstore/context_types.py)
- new [documents/contexts.py](/C:/Users/Q/code/propstore/propstore/documents/contexts.py)

End state:

- contexts decode through typed documents

### Commit 7: Canonical claim documents

Files:

- [validate_claims.py](/C:/Users/Q/code/propstore/propstore/validate_claims.py)
- [compiler/passes.py](/C:/Users/Q/code/propstore/propstore/compiler/passes.py)
- [sidecar/claims.py](/C:/Users/Q/code/propstore/propstore/sidecar/claims.py)
- [identity.py](/C:/Users/Q/code/propstore/propstore/identity.py)
- [conflict_detector/*](/C:/Users/Q/code/propstore/propstore/conflict_detector)
- new [documents/claims.py](/C:/Users/Q/code/propstore/propstore/documents/claims.py)

End state:

- claim files decode through typed documents
- compiler/sidecar/conflict detection stop depending on raw loaded dict files

### Commit 8: Source-local document families

Files:

- [source/concepts.py](/C:/Users/Q/code/propstore/propstore/source/concepts.py)
- [source/claims.py](/C:/Users/Q/code/propstore/propstore/source/claims.py)
- [source/relations.py](/C:/Users/Q/code/propstore/propstore/source/relations.py)
- [source/common.py](/C:/Users/Q/code/propstore/propstore/source/common.py)
- [source/promote.py](/C:/Users/Q/code/propstore/propstore/source/promote.py)
- [source/finalize.py](/C:/Users/Q/code/propstore/propstore/source/finalize.py)
- new [documents/source.py](/C:/Users/Q/code/propstore/propstore/documents/source.py)

End state:

- source-local YAML families have their own typed document surfaces
- source-local fields stop leaking through generic map loaders

### Commit 9: Utility/document-reader sweep

Files:

- [artifact_codes.py](/C:/Users/Q/code/propstore/propstore/artifact_codes.py)
- [cli/helpers.py](/C:/Users/Q/code/propstore/propstore/cli/helpers.py)
- [repo/git_backend.py](/C:/Users/Q/code/propstore/propstore/repo/git_backend.py)
- any remaining document-family readers that still use ad hoc `safe_load`

End state:

- `document_schema.py` is the default production ingress for repo-controlled
  YAML families

## Tests

Run targeted suites after each cluster.

Foundational:

- [test_worldline.py](/C:/Users/Q/code/propstore/tests/test_worldline.py)
- [test_render_contracts.py](/C:/Users/Q/code/propstore/tests/test_render_contracts.py)
- [test_form_utils.py](/C:/Users/Q/code/propstore/tests/test_form_utils.py)
- [test_contexts.py](/C:/Users/Q/code/propstore/tests/test_contexts.py)

Concept/compiler:

- [test_claim_compiler.py](/C:/Users/Q/code/propstore/tests/test_claim_compiler.py)
- [test_cel_checker.py](/C:/Users/Q/code/propstore/tests/test_cel_checker.py)
- [test_validate_claims.py](/C:/Users/Q/code/propstore/tests/test_validate_claims.py)
- [test_validator.py](/C:/Users/Q/code/propstore/tests/test_validator.py)

Source:

- [test_source_claims.py](/C:/Users/Q/code/propstore/tests/test_source_claims.py)
- [test_source_relations.py](/C:/Users/Q/code/propstore/tests/test_source_relations.py)
- [test_source_propose.py](/C:/Users/Q/code/propstore/tests/test_source_propose.py)
- [test_source_cli.py](/C:/Users/Q/code/propstore/tests/test_source_cli.py)
- [test_source_trust.py](/C:/Users/Q/code/propstore/tests/test_source_trust.py)

Sidecar/runtime safety:

- [test_build_sidecar.py](/C:/Users/Q/code/propstore/tests/test_build_sidecar.py)
- [test_world_model.py](/C:/Users/Q/code/propstore/tests/test_world_model.py)

All runs should use:

- `uv run pytest -vv ...`
- full output tee’d to `logs/test-runs/`

## Completion Criteria

This workstream is complete when all of the following are true:

- there is one shared `document_schema.py` decode boundary
- document types exist for the major repo-controlled YAML families
- canonical concept/context/form/worldline files no longer enter the core as raw dict payloads
- canonical claim files no longer flow through compiler/sidecar as raw loaded dict files
- source-local YAML families have their own typed document models
- `LoadedEntry.data: dict[str, Any]` is removed or clearly demoted from the
  main production path
- remaining `yaml.safe_load(...)` calls are either:
  - true ad hoc external config/report reads, or
  - explicit serialization-boundary code that is intentionally not part of the
    document-schema production path

## Risks And Checks

- Claims are the highest blast-radius family. Do not start there.
- Do not collapse source-local and canonical document models into one giant schema.
- Do not let `msgspec` convenience pull domain and document layers back together.
- The document-schema layer should reject bad shape hard. It must not become a
  prettier version of the old repair/massage pipeline.
- If a caller breaks because it relied on loose document dicts, the correct fix
  is to type that caller, not to widen the document reader again.

## Recommended First Coding Slice

Start with:

1. add `msgspec` plus [document_schema.py](/C:/Users/Q/code/propstore/propstore/document_schema.py)
2. type the form document family
3. type the worldline document family
4. then move into canonical concept documents

That proves the architecture on two contained YAML families first, then applies
it to the larger compiler-facing canonical surface.
