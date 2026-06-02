from quire.documents import LoadedDocument
from propstore.families.concepts.declaration import (
    ConceptDocument,
    ConceptLogicalIdDocument,
    ConceptRelationshipDocument,
    LexicalEntryDocument,
    LexicalFormDocument,
    LexicalSenseDocument,
    OntologyReferenceDocument,
)
from propstore.families.concepts.passes import (
    _concept_reference_index,
    _concept_satisfies_type,
)


def _relationship(relation: str, target: str) -> ConceptRelationshipDocument:
    return ConceptRelationshipDocument(
        type=relation,
        target=target,
    )


def _concept(
    name: str,
    relationships=(),
) -> LoadedDocument[ConceptDocument]:
    artifact_id = f"ps:concept:{name}"
    ontology_reference = OntologyReferenceDocument(
        uri=artifact_id,
        label=name,
    )
    document = ConceptDocument(
        artifact_id=artifact_id,
        status="accepted",
        ontology_reference=ontology_reference,
        lexical_entry=LexicalEntryDocument(
            identifier=name,
            canonical_form=LexicalFormDocument(written_rep=name, language="en"),
            senses=(LexicalSenseDocument(reference=ontology_reference),),
            physical_dimension_form="structural",
        ),
        logical_ids=(ConceptLogicalIdDocument(namespace="propstore", value=name),),
        version_id=f"sha256:{name:0<64}"[:71],
        relationships=tuple(relationships),
    )
    return LoadedDocument(
        filename=f"{name}.yaml",
        artifact_path=None,
        store_root=None,
        document=document,
    )


def test_concept_satisfies_type_walks_full_is_a_kind_of_chain():
    concept_a = _concept("a", (_relationship("is_a", "ps:concept:b"),))
    concept_b = _concept("b", (_relationship("kind_of", "ps:concept:c"),))
    concept_c = _concept("c", (_relationship("is_a", "ps:concept:d"),))
    concept_d = _concept("d")
    concepts = [concept_a, concept_b, concept_c, concept_d]

    assert _concept_satisfies_type(
        concept_a,
        "ps:concept:d",
        _concept_reference_index(concepts),
    )
