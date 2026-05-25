from __future__ import annotations

from quire.schema_catalog import SchemaCatalog
from quire.sqlalchemy_schema import SqlAlchemySchema

from propstore.families import registry


_WORLD_TABLES_BY_REGISTRY_FAMILY = {
    "claims": (
        "claim_core",
        "claim_concept_link",
        "claim_numeric_payload",
        "claim_text_payload",
        "claim_algorithm_payload",
        "claim_source_assertion",
    ),
    "concepts": (
        "concept",
        "alias",
        "parameterization",
        "parameterization_group",
        "relationship",
    ),
    "contexts": (
        "context",
        "context_assumption",
        "context_lifting_rule",
        "context_lifting_materialization",
    ),
    "forms": ("form", "form_algebra"),
    "sources": ("source",),
    "micropubs": ("micropublication", "micropublication_claim"),
    "justifications": ("justification",),
}

_WORLD_SUPPORT_TABLES = {
    "meta",
    "relation_edge",
    "conflict_witness",
    "grounded_fact",
    "grounded_fact_empty_predicate",
    "grounded_bundle_input",
    "calibration_counts",
    "embedding_model",
    "embedding_status",
    "concept_embedding_status",
    "build_diagnostics",
}


def test_world_schema_and_catalog_are_cached_singletons() -> None:
    assert isinstance(registry.world_catalog(), SchemaCatalog)
    assert isinstance(registry.world_schema(), SqlAlchemySchema)
    assert registry.world_catalog() is registry.world_catalog()
    assert registry.world_schema() is registry.world_schema()
    assert registry.world_schema().catalog is registry.world_catalog()


def test_world_catalog_metadata_and_families_match_registry() -> None:
    catalog = registry.world_catalog()
    assert catalog.metadata["projection"] == "propstore.world"
    assert catalog.metadata["schema_version"] == 6

    catalog_names = {schema_object.family_name for schema_object in catalog.objects}
    expected_names = set(_WORLD_SUPPORT_TABLES)
    for family in registry.PROPSTORE_FAMILY_REGISTRY.families:
        expected_names.update(_WORLD_TABLES_BY_REGISTRY_FAMILY.get(family.name, ()))
    assert expected_names <= catalog_names


def test_world_schema_meta_model_is_world_meta() -> None:
    meta_model = registry.world_schema().model("meta")
    assert meta_model.__name__ == "WorldMeta"
    assert meta_model.__module__ == "propstore.families.meta.declaration"
