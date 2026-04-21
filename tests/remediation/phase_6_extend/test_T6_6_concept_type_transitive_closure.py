from propstore.core.id_types import LogicalId, to_concept_id
from propstore.families.concepts.passes import (
    _concept_reference_index,
    _concept_satisfies_type,
)
from propstore.families.concepts.stages import (
    ConceptRecord,
    ConceptRelationship,
    LoadedConcept,
)


def _relationship(relation: str, target: str) -> ConceptRelationship:
    return ConceptRelationship(
        relationship_type=relation,
        target=to_concept_id(target),
    )


def _concept(name: str, relationships=()) -> LoadedConcept:
    artifact_id = to_concept_id(f"ps:concept:{name}")
    record = ConceptRecord(
        artifact_id=artifact_id,
        canonical_name=name,
        status="active",
        definition=f"Test concept {name}.",
        form="entity",
        logical_ids=(LogicalId(namespace="propstore", value=name),),
        version_id=f"sha256:{name:0<64}"[:71],
        relationships=tuple(relationships),
    )
    return LoadedConcept(
        filename=f"{name}.yaml",
        source_path=None,
        knowledge_root=None,
        record=record,
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
