"""Propstore world sidecar charter registration."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from functools import lru_cache
from collections.abc import Iterable
from typing import Any

from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import (
    CharterField,
    CharterFtsIndex,
    CharterIndex,
    CharterPolymorphicModel,
    CharterRelationship,
    CharterVectorCache,
    FamilyCharter,
    FamilyModel,
    charter_catalog,
)
from quire.families import FamilyDefinition
from quire.references import ForeignKeySpec, ReferenceKey
from quire.schema_catalog import SchemaCatalog
from quire.sqlalchemy_schema import SqlAlchemySchema, build_sqlalchemy_schema
from quire.versions import VersionId
from propstore.core.claim_types import ClaimType
from propstore.core.justifications import Justification
from propstore.core.relations import ClaimConceptLinkRole
from propstore.families.concepts.declaration import (
    Concept,
    ConceptAlias,
    ConceptRelationship,
    Parameterization,
    ParameterizationGroup,
)
from propstore.families.contexts.declaration import (
    Context,
    ContextAssumption,
    ContextLiftingMaterialization,
    ContextLiftingRule,
)
from propstore.families.forms.stages import Form, FormAlgebra
from propstore.families.micropublications.declaration import (
    Micropublication,
    MicropublicationClaimLink,
)
from propstore.families.relations.declaration import (
    ConceptRelation,
    ConflictWitness,
    RelationEdge,
    Stance,
)
from propstore.families.sources.declaration import Source, source_charter

PROPSTORE_WORLD_SCHEMA_VERSION = 6
PROPSTORE_WORLD_META_KEY = "sidecar"
_WORLD_CONTRACT_VERSION = VersionId("2026.05.20", allow_placeholder=False)


class WorldMeta(FamilyModel): ...
class GroundedFact(FamilyModel): ...
class GroundedFactEmptyPredicate(FamilyModel): ...
class GroundedBundleInput(FamilyModel): ...
class CalibrationCount(FamilyModel): ...
class EmbeddingModel(FamilyModel): ...
class EmbeddingStatus(FamilyModel): ...
class ConceptEmbeddingStatus(FamilyModel): ...
class BuildDiagnostic(FamilyModel): ...


_MODELS: dict[str, type[Any]] = {
    "meta": WorldMeta,
    "source": Source,
    "concept": Concept,
    "alias": ConceptAlias,
    "parameterization": Parameterization,
    "parameterization_group": ParameterizationGroup,
    "relationship": ConceptRelationship,
    "relation_edge": RelationEdge,
    "form": Form,
    "form_algebra": FormAlgebra,
    "context": Context,
    "context_assumption": ContextAssumption,
    "context_lifting_rule": ContextLiftingRule,
    "context_lifting_materialization": ContextLiftingMaterialization,
    "conflict_witness": ConflictWitness,
    "grounded_fact": GroundedFact,
    "grounded_fact_empty_predicate": GroundedFactEmptyPredicate,
    "grounded_bundle_input": GroundedBundleInput,
    "justification": Justification,
    "micropublication": Micropublication,
    "micropublication_claim": MicropublicationClaimLink,
    "calibration_counts": CalibrationCount,
    "embedding_model": EmbeddingModel,
    "embedding_status": EmbeddingStatus,
    "concept_embedding_status": ConceptEmbeddingStatus,
    "build_diagnostics": BuildDiagnostic,
}

_CLAIM_MODEL_TABLES = {
    "claim_core",
    "claim_concept_link",
    "claim_numeric_payload",
    "claim_text_payload",
    "claim_algorithm_payload",
    "claim_source_assertion",
}


def world_model(table_name: str) -> type[Any]:
    if table_name in _CLAIM_MODEL_TABLES:
        return _claim_models()[table_name]
    return _MODELS[table_name]


def world_record(table_name: str, values: object) -> Any:
    model = world_sqlalchemy_schema().model(table_name)
    if isinstance(values, model):
        return values
    return world_sqlalchemy_schema().construct(table_name, _payload(values))


def world_records(table_name: str, rows: Iterable[object] | None) -> tuple[Any, ...]:
    return tuple(world_record(table_name, row) for row in rows or ())


@lru_cache(maxsize=1)
def world_charter_catalog() -> SchemaCatalog:
    return charter_catalog(
        _charter("meta", WorldMeta, "key", _f("key", primary_key=True), _i("schema_version", nullable=False)),
        source_charter(),
        _charter("concept", Concept, "id",
            _f("id", primary_key=True), _f("primary_logical_id", nullable=False, default_sql="''"),
            _f("logical_ids_json", nullable=False, default_sql="'[]'"), _f("version_id", nullable=False, default_sql="''"),
            _f("content_hash", nullable=False), _i("seq", nullable=False), _f("canonical_name", nullable=False),
            _f("status", nullable=False), _f("domain"), _f("definition", nullable=False), _f("kind_type", nullable=False),
            _f("form", nullable=False), _f("form_parameters"), _r("range_min"), _r("range_max"),
            _i("is_dimensionless", nullable=False, default_sql="0"), _f("unit_symbol"), _f("created_date"),
            _f("last_modified"), indexes=(CharterIndex("idx_concept_primary_logical_id", ("primary_logical_id",)),),
            reference_keys=(
                ReferenceKey.field("primary_logical_id"),
                ReferenceKey.field("logical_ids[].value"),
                ReferenceKey.format("{namespace}:{value}", from_field="logical_ids[]"),
                ReferenceKey.field("canonical_name"),
            ),
            fts_indexes=(CharterFtsIndex("concept_fts", "concept_id", ("canonical_name", "aliases", "definition", "conditions"), source_query=_CONCEPT_FTS_SOURCE_QUERY),),
            vector_caches=(CharterVectorCache(
                "concept_embeddings",
                table="concept_vec_{model_identity_hash}_{dimensions}",
                entity_id_field="id",
                source_seq_field="seq",
                source_content_hash_field="content_hash",
                status_table="concept_embedding_status",
            ),)),
        _charter("alias", ConceptAlias, "concept_id", _f("concept_id", nullable=False), _f("alias_name", nullable=False), _f("source", nullable=False),
            indexes=(CharterIndex("idx_alias_name", ("alias_name",)), CharterIndex("idx_alias_concept", ("concept_id",))),
            reference_keys=(ReferenceKey.field("alias_name"),)),
        _charter("parameterization", Parameterization, "output_concept_id",
            _f("output_concept_id", nullable=False), _f("concept_ids", nullable=False), _f("formula", nullable=False),
            _f("sympy"), _f("exactness", nullable=False), _f("conditions_cel"), _f("conditions_ir")),
        _charter("parameterization_group", ParameterizationGroup, "concept_id",
            _f("concept_id", nullable=False), _i("group_id", nullable=False),
            indexes=(CharterIndex("idx_param_group", ("group_id",)),)),
        _charter("relationship", ConceptRelationship, "source_id",
            _f("source_id", nullable=False), _f("type", nullable=False), _f("target_id", nullable=False),
            _f("conditions_cel"), _f("note"),
            indexes=(CharterIndex("idx_rel_source", ("source_id",)), CharterIndex("idx_rel_target", ("target_id",)))),
        _charter("relation_edge", RelationEdge, "id",
            _i("id", primary_key=True, nullable=False, generated=True), _f("source_kind", nullable=False), _f("source_id", nullable=False),
            _f("relation_type", nullable=False), _f("target_kind", nullable=False), _f("target_id", nullable=False),
            _f("perspective_source_claim_id"), _f("target_justification_id"), _f("conditions_cel"), _f("strength"),
            _f("conditions_differ"), _f("note"), _f("resolution_method"), _f("resolution_model"), _f("embedding_model"),
            _r("embedding_distance"), _i("pass_number"), _r("confidence"), _r("opinion_belief"), _r("opinion_disbelief"),
            _r("opinion_uncertainty"), _r("opinion_base_rate"),
            indexes=(CharterIndex("idx_relation_edge_source", ("source_kind", "source_id")),
                     CharterIndex("idx_relation_edge_target", ("target_kind", "target_id")),
                     CharterIndex("idx_relation_edge_type", ("relation_type",))),
            polymorphic_on="source_kind",
            polymorphic_identity="edge",
            polymorphic_models=(
                CharterPolymorphicModel(Stance, "claim"),
                CharterPolymorphicModel(ConceptRelation, "concept"),
            )),
        _charter("form", Form, "name", _f("name", primary_key=True), _f("kind", nullable=False), _f("unit_symbol"),
            _i("is_dimensionless", nullable=False, default_sql="0"), _f("dimensions")),
        _charter("form_algebra", FormAlgebra, "id",
            _i("id", primary_key=True, nullable=False), _f("output_form", nullable=False), _f("input_forms", nullable=False),
            _f("operation", nullable=False), _f("source_concept_id"), _f("source_formula"),
            _i("dim_verified", nullable=False, default_sql="1"), indexes=(CharterIndex("idx_form_algebra_output", ("output_form",)),)),
        _charter("context", Context, "id", _f("id", primary_key=True, nullable=False), _f("name", nullable=False),
            _f("description"), _f("parameters_json"), _f("perspective")),
        _charter("context_assumption", ContextAssumption, "context_id", _f("context_id", nullable=False), _f("assumption_cel", nullable=False), _i("seq", nullable=False),
            indexes=(CharterIndex("idx_context_assumption_context_id", ("context_id",)),)),
        _charter("context_lifting_rule", ContextLiftingRule, "id",
            _f("id", primary_key=True, nullable=False), _f("source_context_id", nullable=False), _f("target_context_id", nullable=False),
            _f("conditions_cel"), _f("mode", nullable=False), _f("justification"),
            indexes=(CharterIndex("idx_context_lifting_rule_source_context_id", ("source_context_id",)),
                     CharterIndex("idx_context_lifting_rule_target_context_id", ("target_context_id",)))),
        _charter("context_lifting_materialization", ContextLiftingMaterialization, "id",
            _i("id", primary_key=True, nullable=True), _f("rule_id", nullable=False), _f("source_context_id", nullable=False),
            _f("target_context_id", nullable=False), _f("proposition_id", nullable=False), _f("status", nullable=False),
            _f("exception_id"), _f("provenance_json", nullable=False),
            indexes=(CharterIndex("idx_context_lifting_materialization_source_context_id", ("source_context_id",)),
                     CharterIndex("idx_context_lifting_materialization_target_context_id", ("target_context_id",)))),
        _claim_core_charter(),
        _charter("claim_concept_link", _claim_models()["claim_concept_link"], "claim_id",
            CharterField("claim_id", str, primary_key=True, nullable=False, foreign_key=_fk("claim_concept_link_claim", "claim_concept_link", "claim_id", "claim_core")),
            CharterField("concept_id", str, primary_key=True, nullable=False, foreign_key=_fk("claim_concept_link_concept", "claim_concept_link", "concept_id", "concept")),
            CharterField("role", ClaimConceptLinkRole, primary_key=True, nullable=False), _i("ordinal", primary_key=True, nullable=False), _f("binding_name"),
            indexes=(CharterIndex("idx_claim_concept_link_claim", ("claim_id",)), CharterIndex("idx_claim_concept_link_concept", ("concept_id",)), CharterIndex("idx_claim_concept_link_role", ("role",))),
            relationships=(CharterRelationship(
                "claim",
                target_family="claim_core",
                foreign_key="claim_id",
                back_populates="concept_links",
                uselist=False,
            ),)),
        _claim_payload_charters()[0], _claim_payload_charters()[1], _claim_payload_charters()[2],
        _claim_source_assertion_charter(),
        _charter("conflict_witness", ConflictWitness, "id",
            _i("id", primary_key=True, nullable=False, generated=True), _f("claim_a_id", nullable=False), _f("claim_b_id", nullable=False),
            _f("concept_id", nullable=False), _f("warning_class", nullable=False), _f("conditions_a"), _f("conditions_b"),
            _f("value_a"), _f("value_b"), _f("derivation_chain"), indexes=(CharterIndex("idx_conflict_witness_concept", ("concept_id",)),)),
        _charter("grounded_fact", GroundedFact, "predicate", _f("predicate", primary_key=True, nullable=False), _f("arguments", primary_key=True, nullable=False), _f("section", primary_key=True, nullable=False)),
        _charter("grounded_fact_empty_predicate", GroundedFactEmptyPredicate, "section", _f("section", primary_key=True, nullable=False), _f("predicate", primary_key=True, nullable=False)),
        _charter("grounded_bundle_input", GroundedBundleInput, "kind", _f("kind", primary_key=True, nullable=False), _i("position", primary_key=True, nullable=False), _b("payload", nullable=False)),
        _charter("justification", Justification, "id",
            _f("id", primary_key=True, nullable=False), _f("justification_kind", nullable=False), _f("conclusion_claim_id", nullable=False),
            _f("premise_claim_ids", nullable=False), _f("source_relation_type"), _f("source_claim_id"), _f("provenance_json"),
            _f("rule_strength", nullable=False, default_sql="'defeasible'")),
        _charter("micropublication", Micropublication, "id",
            _f("id", primary_key=True, nullable=False), _f("context_id", nullable=False), _f("assumptions_json", nullable=False, default_sql="'[]'"),
            _f("evidence_json", nullable=False, default_sql="'[]'"), _f("stance"), _f("provenance_json"), _f("source_slug"),
            indexes=(CharterIndex("idx_micropub_context", ("context_id",)),),
            relationships=(CharterRelationship(
                "claim_links",
                target_family="micropublication_claim",
                foreign_key="micropublication_id",
                back_populates="micropublication",
                association_object=True,
                order_by=("seq",),
            ),)),
        _charter("micropublication_claim", MicropublicationClaimLink, "micropublication_id",
            CharterField("micropublication_id", str, primary_key=True, nullable=False, foreign_key=_fk("micropublication_claim_micropublication", "micropublication_claim", "micropublication_id", "micropublication")),
            CharterField("claim_id", str, primary_key=True, nullable=False, foreign_key=_fk("micropublication_claim_claim", "micropublication_claim", "claim_id", "claim_core")), _i("seq", nullable=False),
            indexes=(CharterIndex("idx_micropub_claim", ("claim_id",)),),
            relationships=(CharterRelationship(
                "micropublication",
                target_family="micropublication",
                foreign_key="micropublication_id",
                back_populates="claim_links",
                uselist=False,
            ),)),
        _support_charters()[0], _support_charters()[1], _support_charters()[2], _support_charters()[3], _support_charters()[4],
        metadata={"projection": "propstore.world", "schema_version": PROPSTORE_WORLD_SCHEMA_VERSION},
    )


@lru_cache(maxsize=1)
def world_sqlalchemy_schema() -> SqlAlchemySchema:
    return build_sqlalchemy_schema(world_charter_catalog())


def _charter(
    name: str,
    model: type[Any],
    identity_field: str,
    *fields: CharterField,
    indexes: tuple[CharterIndex, ...] = (),
    fts_indexes: tuple[CharterFtsIndex, ...] = (),
    vector_caches: tuple[CharterVectorCache, ...] = (),
    relationships: tuple[CharterRelationship, ...] = (),
    reference_keys: tuple[ReferenceKey, ...] = (),
    polymorphic_on: str | None = None,
    polymorphic_identity: str | None = None,
    polymorphic_models: tuple[CharterPolymorphicModel, ...] = (),
) -> FamilyCharter:
    return FamilyCharter(
        family=_world_family(
            name,
            model,
            identity_field,
            reference_keys=reference_keys,
        ),
        model=model,
        fields=fields,
        indexes=indexes,
        fts_indexes=fts_indexes,
        vector_caches=vector_caches,
        relationships=relationships,
        polymorphic_on=polymorphic_on,
        polymorphic_identity=polymorphic_identity,
        polymorphic_models=polymorphic_models,
        semantic_metadata={"semantic": "propstore.world"},
    )


def _world_family(
    name: str,
    model: type[Any],
    identity_field: str,
    *,
    reference_keys: tuple[ReferenceKey, ...] = (),
) -> FamilyDefinition[Any, Any, Any, Any]:
    return FamilyDefinition(
        key=name,
        name=name,
        contract_version=_WORLD_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name=f"propstore-world-{name}",
            contract_version=_WORLD_CONTRACT_VERSION,
            doc_type=model,
            placement=FlatYamlPlacement(f".derived/{name}", str),
        ),
        identity_field=identity_field,
        reference_keys=reference_keys,
    )


def _f(name: str, *, nullable: bool = True, primary_key: bool = False, default_sql: str | None = None) -> CharterField:
    return CharterField(name, str, nullable=nullable and not primary_key, primary_key=primary_key, default_sql=default_sql)


def _i(
    name: str,
    *,
    nullable: bool = True,
    primary_key: bool = False,
    default_sql: str | None = None,
    generated: bool = False,
) -> CharterField:
    return CharterField(
        name,
        int,
        nullable=nullable and not primary_key,
        primary_key=primary_key,
        default_sql=default_sql,
        generated=generated,
    )


def _r(name: str, *, nullable: bool = True) -> CharterField:
    return CharterField(name, float, nullable=nullable)


def _b(name: str, *, nullable: bool = True) -> CharterField:
    return CharterField(name, bytes, nullable=nullable)


def _fk(
    name: str,
    source_family: str,
    source_field: str,
    target_family: str,
    *,
    target_field: str = "id",
    required: bool = True,
    many: bool = False,
) -> ForeignKeySpec:
    return ForeignKeySpec(
        name=name,
        contract_version=_WORLD_CONTRACT_VERSION,
        source_family=source_family,
        source_field=source_field,
        target_family=target_family,
        target_field=target_field,
        required=required,
        many=many,
    )


def _payload(values: object) -> dict[str, object]:
    if hasattr(values, "values"):
        row_values = getattr(values, "values")
        if isinstance(row_values, dict):
            return dict(row_values)
    if is_dataclass(values) and not isinstance(values, type):
        return asdict(values)
    if isinstance(values, dict):
        return dict(values)
    return dict(vars(values))


def _claim_models() -> dict[str, type[Any]]:
    from propstore.families.claims.declaration import (
        Claim,
        ClaimAlgorithmPayload,
        ClaimConceptLink,
        ClaimNumericPayload,
        ClaimSourceAssertion,
        ClaimTextPayload,
    )

    return {
        "claim_core": Claim,
        "claim_concept_link": ClaimConceptLink,
        "claim_numeric_payload": ClaimNumericPayload,
        "claim_text_payload": ClaimTextPayload,
        "claim_algorithm_payload": ClaimAlgorithmPayload,
        "claim_source_assertion": ClaimSourceAssertion,
    }


def _claim_core_charter() -> FamilyCharter:
    claim = _claim_models()["claim_core"]
    return _charter("claim_core", claim, "id",
        _f("id", primary_key=True, nullable=False), _f("primary_logical_id", nullable=False, default_sql="''"),
        _f("logical_ids_json", nullable=False, default_sql="'[]'"), _f("version_id", nullable=False, default_sql="''"),
        _f("content_hash", nullable=False, default_sql="''"), _i("seq", nullable=False), CharterField("type", ClaimType, nullable=False),
        _f("target_concept"),
        _f("source_slug"),
        _f("source_paper", nullable=False), _i("provenance_page", nullable=False),
        _f("provenance_json"), _f("context_id"), _f("premise_kind", nullable=False, default_sql="'ordinary'"),
        _f("branch"), _f("build_status", nullable=False, default_sql="'ingested'"), _f("stage"), _f("promotion_status"),
        indexes=(CharterIndex("idx_claim_core_target", ("target_concept",)), CharterIndex("idx_claim_core_type", ("type",)),
                 CharterIndex("idx_claim_core_primary_logical_id", ("primary_logical_id",)), CharterIndex("idx_claim_core_build_status", ("build_status",)),
                 CharterIndex("idx_claim_core_stage", ("stage",)), CharterIndex("idx_claim_core_promotion_status", ("promotion_status",))),
        reference_keys=(
            ReferenceKey.field("primary_logical_id"),
            ReferenceKey.field("logical_ids[].value"),
            ReferenceKey.format("{namespace}:{value}", from_field="logical_ids[]"),
        ),
        fts_indexes=(CharterFtsIndex("claim_fts", "claim_id", ("statement", "conditions", "expression"), source_query=_CLAIM_FTS_SOURCE_QUERY),),
        vector_caches=(CharterVectorCache(
            "claim_embeddings",
            table="claim_vec_{model_identity_hash}_{dimensions}",
            entity_id_field="id",
            source_seq_field="seq",
            source_content_hash_field="content_hash",
            status_table="embedding_status",
        ),),
        relationships=(CharterRelationship(
            "concept_links",
            target_family="claim_concept_link",
            foreign_key="claim_id",
            back_populates="claim",
            association_object=True,
            order_by=("ordinal",),
        ), CharterRelationship(
            "numeric_payload",
            target_family="claim_numeric_payload",
            foreign_key="claim_id",
            back_populates="claim",
            uselist=False,
        ), CharterRelationship(
            "text_payload",
            target_family="claim_text_payload",
            foreign_key="claim_id",
            back_populates="claim",
            uselist=False,
        ), CharterRelationship(
            "algorithm_payload",
            target_family="claim_algorithm_payload",
            foreign_key="claim_id",
            back_populates="claim",
            uselist=False,
        ), CharterRelationship(
            "source_assertions",
            target_family="claim_source_assertion",
            foreign_key="claim_id",
            back_populates="claim",
            association_object=True,
            order_by=("ordinal",),
        ),))


def _claim_payload_charters() -> tuple[FamilyCharter, FamilyCharter, FamilyCharter]:
    models = _claim_models()
    return (
        _charter("claim_numeric_payload", models["claim_numeric_payload"], "claim_id",
            CharterField("claim_id", str, primary_key=True, nullable=False, foreign_key=_fk("claim_numeric_payload_claim", "claim_numeric_payload", "claim_id", "claim_core")), _r("value"), _r("lower_bound"), _r("upper_bound"), _r("uncertainty"),
            _f("uncertainty_type"), _i("sample_size"), _f("unit"), _r("value_si"), _r("lower_bound_si"), _r("upper_bound_si"),
            relationships=(CharterRelationship(
                "claim",
                target_family="claim_core",
                foreign_key="claim_id",
                back_populates="numeric_payload",
                uselist=False,
            ),)),
        _charter("claim_text_payload", models["claim_text_payload"], "claim_id",
            CharterField("claim_id", str, primary_key=True, nullable=False, foreign_key=_fk("claim_text_payload_claim", "claim_text_payload", "claim_id", "claim_core")), _f("conditions_cel"), _f("conditions_ir"), _f("statement"),
            _f("expression"), _f("sympy_generated"), _f("sympy_error"), _f("name"), _f("measure"), _f("listener_population"),
            _f("methodology"), _f("notes"), _f("description"), _f("auto_summary"),
            relationships=(CharterRelationship(
                "claim",
                target_family="claim_core",
                foreign_key="claim_id",
                back_populates="text_payload",
                uselist=False,
            ),)),
        _charter("claim_algorithm_payload", models["claim_algorithm_payload"], "claim_id",
            CharterField("claim_id", str, primary_key=True, nullable=False, foreign_key=_fk("claim_algorithm_payload_claim", "claim_algorithm_payload", "claim_id", "claim_core")), _f("body"), _f("canonical_ast"), _f("variables_json"), _f("algorithm_stage"),
            indexes=(CharterIndex("idx_claim_algorithm_stage", ("algorithm_stage",)),),
            relationships=(CharterRelationship(
                "claim",
                target_family="claim_core",
                foreign_key="claim_id",
                back_populates="algorithm_payload",
                uselist=False,
            ),)),
    )


def _claim_source_assertion_charter() -> FamilyCharter:
    models = _claim_models()
    return _charter("claim_source_assertion", models["claim_source_assertion"], "claim_id",
        CharterField("claim_id", str, primary_key=True, nullable=False, foreign_key=_fk("claim_source_assertion_claim", "claim_source_assertion", "claim_id", "claim_core")),
        _f("source_assertion_id", nullable=False),
        _i("ordinal", primary_key=True, nullable=False),
        indexes=(CharterIndex("idx_claim_source_assertion_claim", ("claim_id",)),
                 CharterIndex("idx_claim_source_assertion_source", ("source_assertion_id",))),
        relationships=(CharterRelationship(
            "claim",
            target_family="claim_core",
            foreign_key="claim_id",
            back_populates="source_assertions",
            uselist=False,
        ),))


def _support_charters() -> tuple[FamilyCharter, FamilyCharter, FamilyCharter, FamilyCharter, FamilyCharter]:
    return (
        _charter("calibration_counts", CalibrationCount, "pass_number",
            _i("pass_number", primary_key=True, nullable=False), _f("category", primary_key=True, nullable=False), _i("correct_count", nullable=False), _i("total_count", nullable=False)),
        _charter("embedding_model", EmbeddingModel, "model_identity_hash",
            _f("model_identity_hash", primary_key=True, nullable=False), _f("provider", nullable=False), _f("model_name", nullable=False),
            _f("model_version", nullable=False, default_sql="''"), _f("content_digest", nullable=False), _i("dimensions", nullable=False), _f("created_at", nullable=False)),
        _charter("embedding_status", EmbeddingStatus, "model_identity_hash",
            _f("model_identity_hash", primary_key=True, nullable=False), _f("claim_id", primary_key=True, nullable=False), _f("content_hash", nullable=False), _f("embedded_at", nullable=False),
            indexes=(CharterIndex("idx_embedding_status_model_identity", ("model_identity_hash",)),)),
        _charter("concept_embedding_status", ConceptEmbeddingStatus, "model_identity_hash",
            _f("model_identity_hash", primary_key=True, nullable=False), _f("concept_id", primary_key=True, nullable=False), _f("content_hash", nullable=False), _f("embedded_at", nullable=False),
            indexes=(CharterIndex("idx_concept_embedding_status_model_identity", ("model_identity_hash",)),)),
        _charter("build_diagnostics", BuildDiagnostic, "id",
            _i("id", primary_key=True, nullable=False), _f("claim_id"), _f("source_kind", nullable=False), _f("source_ref"), _f("diagnostic_kind", nullable=False),
            _f("severity", nullable=False), _i("blocking", nullable=False), _f("message", nullable=False), _f("file"), _f("detail_json"),
            indexes=(CharterIndex("idx_build_diagnostics_claim", ("claim_id",)), CharterIndex("idx_build_diagnostics_kind", ("diagnostic_kind",)),
                     CharterIndex("idx_build_diagnostics_source", ("source_kind", "source_ref")))),
    )


_CONCEPT_FTS_SOURCE_QUERY = """
    SELECT
        c.id AS concept_id,
        c.canonical_name AS canonical_name,
        COALESCE((SELECT group_concat(a.alias_name, ' ') FROM alias a WHERE a.concept_id = c.id), '') AS aliases,
        c.definition AS definition,
        COALESCE((SELECT group_concat(value, ' ') FROM (
            SELECT rel_condition.value AS value FROM relationship r, json_each(r.conditions_cel) AS rel_condition WHERE r.source_id = c.id AND r.conditions_cel IS NOT NULL
            UNION ALL
            SELECT param_condition.value AS value FROM parameterization p, json_each(p.conditions_cel) AS param_condition WHERE p.output_concept_id = c.id AND p.conditions_cel IS NOT NULL
        )), '') AS conditions
    FROM concept c
    ORDER BY c.seq
"""


_CLAIM_FTS_SOURCE_QUERY = """
    SELECT
        c.id AS claim_id,
        COALESCE(t.statement, '') AS statement,
        COALESCE((SELECT group_concat(value, ' ') FROM json_each(t.conditions_cel)), '') AS conditions,
        COALESCE(t.expression, '') AS expression
    FROM claim_core c
    JOIN claim_text_payload t ON t.claim_id = c.id
    ORDER BY c.seq
"""
