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

For the concept cleanup slice, the old concept record/wrapper/parser layer is
not an owner. Keeping that layer under a new name is not progress.

## Concept Cleanup Status

The current slice deletes the old concept record/wrapper/parser surface from
the concept stages module and rewires its direct runtime callers to
`ConceptDocument`, Quire `LoadedDocument`, family handles, and generated
reference indexes.

The executable gate for this slice is zero hits for the deleted concept
record/wrapper/parser names under `propstore` and `tests`. Historical plans,
prompts, reviews, and workstream notes may still describe the old surface; those
files are not runtime code and should not be used as replacement guidance.

The form wrapper slice deletes the Propstore-specific form loaded-document
wrapper. Form pipeline callers now use Quire `LoadedDocument[FormDocument]`
directly when filename/path provenance is needed, and `FormDocument` directly
when only fields are needed.

Next slices should keep the same recursion:
- delete one remaining fake representation or helper surface;
- follow only direct breakage from that deletion;
- use the existing Charter document, family surface, generated row/query
  surface, or Quire boundary;
- commit the kept reduction before switching targets.
