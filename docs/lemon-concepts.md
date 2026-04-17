# Lemon Concepts

WS-A Phase 2 moves concept lexicalization onto the lemon / OntoLex-Lemon
shape. This document describes the implemented Phase 2 surface; qualia,
proto-roles, description-kinds, contexts, and micropublications are later
WS-A phases.

## Paper Commitments

Buitelaar et al. 2011 separates ontology knowledge from lexical knowledge. Propstore uses that split directly:

- `OntologyReference` is the ontology entity side.
- `LexicalEntry` is the linguistic entry.
- `LexicalForm` is the written or phonetic surface realization.
- `LexicalSense` is the disambiguating link from one entry to one ontology reference.

The W3C OntoLex-Lemon community report keeps the same core and adds the sharper invariant that `LexicalSense.reference` is functional. Propstore models that by making each `LexicalSense` point at exactly one `OntologyReference`, while a `LexicalEntry` may carry multiple senses for polysemy.

Canonical concept artifacts are now authored in that shape:

- `ontology_reference` names the ontology-side entity for the concept artifact.
- `lexical_entry.canonical_form` carries the primary written or phonetic form.
- `lexical_entry.senses` carries one or more sense-to-reference links.
- `lexical_entry.physical_dimension_form` is the entry-level bridge to the existing form/dimension system.

The runtime `ConceptRecord` is a projection from this artifact boundary for
older compiler and sidecar consumers. It is not the authored artifact shape.

## Dimension Boundary

`LexicalForm` does not carry physical-dimensional metadata. A form is linguistic: written representation, language, and optional phonetic representation.

The existing dimensional algebra belongs on the lexical entry or a sibling measurement/document layer. The initial core type exposes this as `LexicalEntry.physical_dimension_form`, not as a property of `LexicalForm`.

Physical unit conversion, Pint aliases, and dimensional algebra live in
`propstore.dimensions`. `propstore.form_utils` loads and validates authored
form documents; it does not own or re-export dimension conversion APIs.

## Identity

The OntoLex-Lemon distinction between an entry and a form matters operationally:

- Entry identity includes `LexicalEntry.identifier`, so homographs do not collapse merely because their written form is the same.
- Form identity is separately available for alignment proposal analysis.
- Polysemy is represented as multiple `LexicalSense` values on one entry.
- Homography is represented as distinct entries that may share a written form.

The validator now inspects the canonical `ConceptDocument`, not only the flat
runtime projection. It rejects duplicate sense references inside one entry and
requires the concept artifact's `ontology_reference` to have a matching lexical
sense. It no longer treats the filename as canonical concept identity.

## Alignment

Concept alignment no longer uses definition-token overlap as evidence. The relation classifier now uses exact lemon-shaped identity:

- identical `LexicalEntry` identity with conflicting definitions attacks;
- identical `OntologyReference` is non-attacking;
- otherwise the alternatives remain non-attacking candidates on the proposal artifact.

No Jaccard fallback remains in `propstore/source/alignment.py`.

## Tests

The Phase 2 lemon foundation is guarded by:

- `tests/test_lemon_concepts.py`
- `tests/test_lemon_form_dimension_boundary.py`
- `tests/test_lemon_concept_documents.py`
- `tests/test_validator.py::TestLemonInvariants`
- `tests/test_concept_alignment_cli.py`
