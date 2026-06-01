# Project Understanding

Propstore is a knowledge and argument store.

It is for authored objects: sources, concepts, claims, stances,
justifications, contexts, rules, worldlines, and the references between them.
Those objects should have typed representations, stable identity, and one
declared field contract.

## Hierarchy

The project is Propstore.

Inside that project, one architectural rule is that core code works with typed
semantic objects, Charter-backed documents, Quire I/O boundaries, and
family/query surfaces. Core code should not carry fake payload, dict, record, or
parser shapes for authored knowledge objects.

Inside that architectural rule, one workstream is deleting `to_payload`,
`from_payload`, and related payload-shaped surfaces.

Inside that workstream, one slice is one concrete payload surface or one
concrete value-flow.

Inside that slice, one step is: delete the wrong call, helper, record, or parser
surface first; follow only the breakage caused by that deletion; repair that
value-flow by using the real owner; then stop at the slice boundary.

## Owners

Quire and Charters own the mechanics of documents: field declarations,
placement, storage, references, serialization, rendering, and generated query
surfaces. Propstore should use those objects and surfaces. It should not create
parallel payloads, record DTOs, dict mirrors, parser objects, compatibility
helpers, or local field lists for the same facts.

## Recursion

The deletion rule recurs at each level of the hierarchy. At the workstream
level, delete the old payload surface. At the slice level, delete one concrete
surface and follow its direct breakage. At the caller level, delete the local
fake representation and use the typed object, Charter field, Quire boundary, or
family/query surface that already owns the fact.

The rule does not mean broad demolition. It means the same question is asked at
each level: what is the wrong surface here, what owner already owns the fact,
and what direct breakage belongs to this level?

## Current Cleanup Slice

The current cleanup work is one part of that project. `to_payload` and
`from_payload` are bad because they mark places where Propstore is turning real
objects into fake transport shapes and then treating those shapes as domain
objects. Deleting the method names is not enough. The replacement must also
delete the payload-shaped representation and make callers use the real typed
object, Charter field, Quire boundary, or generated/family query surface.

For the concept cleanup slice, `ConceptRecord`,
`concept_document_to_record_payload`, and `parse_concept_record_document` are
deletion targets. Keeping that layer under a new name is not progress.

## Concept Record Deletion Todo

`ConceptRecord`, `ConceptAlias`, `ConceptRelationship`,
`ParameterizationSpec`, `parse_concept_record`, and
`parse_concept_record_document` are deletion targets. Their callers must move to
the Charter document, family surface, generated row/query surface, or be
deleted.

- `app/compiler.py::export_aliases` parses each concept document only to read
  primary logical id, canonical name, and aliases. Those are document/family
  fields; this caller should not use `parse_concept_record_document`.
- `app/forms.py::form_references` and `validate_forms` parse each concept
  document only to read form and artifact id. Those belong on the concept
  document or family surface.
- `compiler/context.py` and `compiler/workflows.py` build compiler context by
  storing `LoadedConcept(record=...)`. Compiler inputs should use the concept
  document or a real compiled/indexed family surface instead of the record
  mirror.
- `app/concepts/mutation.py` builds `LoadedConcept(record=...)`, then searches
  and mutates through record payloads and record fields. It should use
  `ConceptDocument` and Charter/family APIs directly.
- `families/concepts/lifecycle.py` converts document to record to payload. That
  document -> record -> payload projection should be deleted.
- `grounding/loading.py` builds `LoadedConcept(record=...)` for fact extraction.
  Grounding should receive documents or a real concept registry/family index.
- `source/promote.py` builds `LoadedConcept(record=...)` from promoted concept
  documents for validation/compilation. Promotion already has concept documents.
- `families/concepts/declaration.py::compile_concept_sidecar_rows` reads
  `record` fields to create sidecar rows, even though this module declares the
  concept document, nested Charter documents, and generated row models.
