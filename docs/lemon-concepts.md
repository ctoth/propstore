# Lemon Concepts

WS-A Phase 2 moves concept lexicalization toward the lemon / OntoLex-Lemon shape.

## Paper Commitments

Buitelaar et al. 2011 separates ontology knowledge from lexical knowledge. Propstore uses that split directly:

- `OntologyReference` is the ontology entity side.
- `LexicalEntry` is the linguistic entry.
- `LexicalForm` is the written or phonetic surface realization.
- `LexicalSense` is the disambiguating link from one entry to one ontology reference.

The W3C OntoLex-Lemon community report keeps the same core and adds the sharper invariant that `LexicalSense.reference` is functional. Propstore models that by making each `LexicalSense` point at exactly one `OntologyReference`, while a `LexicalEntry` may carry multiple senses for polysemy.

## Dimension Boundary

`LexicalForm` does not carry physical-dimensional metadata. A form is linguistic: written representation, language, and optional phonetic representation.

The existing dimensional algebra belongs on the lexical entry or a sibling measurement/document layer. The initial core type exposes this as `LexicalEntry.physical_dimension_form`, not as a property of `LexicalForm`.

## Alignment

Concept alignment no longer uses definition-token overlap as evidence. The relation classifier now uses exact lemon-shaped identity:

- identical `LexicalEntry` identity with conflicting definitions attacks;
- identical `OntologyReference` is non-attacking;
- otherwise the alternatives remain non-attacking candidates on the proposal artifact.

No Jaccard fallback remains in `propstore/source/alignment.py`.

## Tests

The Phase 2 lemon foundation is guarded by:

- `tests/test_lemon_concepts.py`
- `tests/test_concept_alignment_cli.py`
