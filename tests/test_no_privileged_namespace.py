from __future__ import annotations

import pytest

from propstore.concept_ids import NamespaceAmbiguity, _numeric_concept_id
from propstore.core.concept_status import ConceptStatus
from propstore.families.concepts.documents import (
    ConceptDocument,
    ConceptLogicalIdDocument,
    LexicalEntryDocument,
    LexicalFormDocument,
    LexicalSenseDocument,
    OntologyReferenceDocument,
)


def _concept_with_ids(*logical_ids: tuple[str, str]) -> ConceptDocument:
    reference = OntologyReferenceDocument(uri="tag:example.com,2026:concept/example")
    return ConceptDocument(
        status=ConceptStatus.ACCEPTED,
        ontology_reference=reference,
        lexical_entry=LexicalEntryDocument(
            identifier="example",
            canonical_form=LexicalFormDocument(written_rep="example", language="en"),
            senses=(LexicalSenseDocument(reference=reference),),
            physical_dimension_form="dimensionless",
        ),
        logical_ids=tuple(
            ConceptLogicalIdDocument(namespace=namespace, value=value)
            for namespace, value in logical_ids
        ),
    )


def test_numeric_concept_id_raises_when_two_namespaces_encode_same_id() -> None:
    document = _concept_with_ids(("propstore", "concept42"), ("upstream", "concept42"))

    with pytest.raises(NamespaceAmbiguity) as excinfo:
        _numeric_concept_id(document)

    assert {candidate.namespace for candidate in excinfo.value.candidates} == {
        "propstore",
        "upstream",
    }


def test_numeric_concept_id_raises_when_namespaces_encode_different_ids() -> None:
    document = _concept_with_ids(("propstore", "concept42"), ("upstream", "concept99"))

    with pytest.raises(NamespaceAmbiguity):
        _numeric_concept_id(document)


def test_numeric_concept_id_uses_explicit_namespace_disambiguator() -> None:
    document = _concept_with_ids(("propstore", "concept42"), ("upstream", "concept99"))

    assert _numeric_concept_id(document, namespace="upstream") == 99
