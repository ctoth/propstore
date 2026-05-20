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
    FamilyCharter,
    charter_catalog,
)
from quire.families import FamilyDefinition
from quire.schema_catalog import SchemaCatalog
from quire.sqlalchemy_schema import SqlAlchemySchema, build_sqlalchemy_schema
from quire.versions import VersionId
from propstore.families.forms.stages import Form, FormAlgebra
from propstore.families.sources.declaration import Source, source_charter

PROPSTORE_WORLD_SCHEMA_VERSION = 6
PROPSTORE_WORLD_META_KEY = "sidecar"
_WORLD_CONTRACT_VERSION = VersionId("2026.05.20", allow_placeholder=False)


class WorldModel:
    def __init__(self, **values: object) -> None:
        for key, value in values.items():
            setattr(self, key, value)


class MetaRecord(WorldModel): ...
class ConceptRecord(WorldModel): ...
class AliasRecord(WorldModel): ...
class ParameterizationRecord(WorldModel): ...
class ParameterizationGroupRecord(WorldModel): ...
class RelationshipRecord(WorldModel): ...
class RelationEdgeRecord(WorldModel): ...
class ContextRecord(WorldModel): ...
class ContextAssumptionRecord(WorldModel): ...
class ContextLiftingRuleRecord(WorldModel): ...
class ContextLiftingMaterializationRecord(WorldModel): ...
class ClaimCoreRecord(WorldModel): ...
class ClaimConceptLinkRecord(WorldModel): ...
class ClaimNumericPayloadRecord(WorldModel): ...
class ClaimTextPayloadRecord(WorldModel): ...
class ClaimAlgorithmPayloadRecord(WorldModel): ...
class ConflictWitnessRecord(WorldModel): ...
class GroundedFactRecord(WorldModel): ...
class GroundedFactEmptyPredicateRecord(WorldModel): ...
class GroundedBundleInputRecord(WorldModel): ...
class JustificationRecord(WorldModel): ...
class MicropublicationRecord(WorldModel): ...
class MicropublicationClaimRecord(WorldModel): ...
class CalibrationCountsRecord(WorldModel): ...
class EmbeddingModelRecord(WorldModel): ...
class EmbeddingStatusRecord(WorldModel): ...
class ConceptEmbeddingStatusRecord(WorldModel): ...
class BuildDiagnostic(WorldModel): ...


_MODELS: dict[str, type[Any]] = {
    "meta": MetaRecord,
    "source": Source,
    "concept": ConceptRecord,
    "alias": AliasRecord,
    "parameterization": ParameterizationRecord,
    "parameterization_group": ParameterizationGroupRecord,
    "relationship": RelationshipRecord,
    "relation_edge": RelationEdgeRecord,
    "form": Form,
    "form_algebra": FormAlgebra,
    "context": ContextRecord,
    "context_assumption": ContextAssumptionRecord,
    "context_lifting_rule": ContextLiftingRuleRecord,
    "context_lifting_materialization": ContextLiftingMaterializationRecord,
    "claim_core": ClaimCoreRecord,
    "claim_concept_link": ClaimConceptLinkRecord,
    "claim_numeric_payload": ClaimNumericPayloadRecord,
    "claim_text_payload": ClaimTextPayloadRecord,
    "claim_algorithm_payload": ClaimAlgorithmPayloadRecord,
    "conflict_witness": ConflictWitnessRecord,
    "grounded_fact": GroundedFactRecord,
    "grounded_fact_empty_predicate": GroundedFactEmptyPredicateRecord,
    "grounded_bundle_input": GroundedBundleInputRecord,
    "justification": JustificationRecord,
    "micropublication": MicropublicationRecord,
    "micropublication_claim": MicropublicationClaimRecord,
    "calibration_counts": CalibrationCountsRecord,
    "embedding_model": EmbeddingModelRecord,
    "embedding_status": EmbeddingStatusRecord,
    "concept_embedding_status": ConceptEmbeddingStatusRecord,
    "build_diagnostics": BuildDiagnostic,
}


def world_model(table_name: str) -> type[Any]:
    return _MODELS[table_name]


def world_record(table_name: str, values: object) -> Any:
    model = world_model(table_name)
    if isinstance(values, model):
        return values
    payload = _payload(values)
    if table_name == "relationship" and "relationship_type" in payload:
        payload["type"] = payload.pop("relationship_type")
    return model(**payload)


def world_records(table_name: str, rows: Iterable[object] | None) -> tuple[Any, ...]:
    return tuple(world_record(table_name, row) for row in rows or ())


@lru_cache(maxsize=1)
def world_charter_catalog() -> SchemaCatalog:
    return charter_catalog(
        _charter("meta", MetaRecord, "key", _f("key", primary_key=True), _i("schema_version", nullable=False)),
        source_charter(),
        _charter("concept", ConceptRecord, "id",
            _f("id", primary_key=True), _f("primary_logical_id", nullable=False, default_sql="''"),
            _f("logical_ids_json", nullable=False, default_sql="'[]'"), _f("version_id", nullable=False, default_sql="''"),
            _f("content_hash", nullable=False), _i("seq", nullable=False), _f("canonical_name", nullable=False),
            _f("status", nullable=False), _f("domain"), _f("definition", nullable=False), _f("kind_type", nullable=False),
            _f("form", nullable=False), _f("form_parameters"), _r("range_min"), _r("range_max"),
            _i("is_dimensionless", nullable=False, default_sql="0"), _f("unit_symbol"), _f("created_date"),
            _f("last_modified"), indexes=(CharterIndex("idx_concept_primary_logical_id", ("primary_logical_id",)),),
            fts_indexes=(CharterFtsIndex("concept_fts", "concept_id", ("canonical_name", "aliases", "definition", "conditions"), source_query=_CONCEPT_FTS_SOURCE_QUERY),)),
        _charter("alias", AliasRecord, "concept_id", _f("concept_id", nullable=False), _f("alias_name", nullable=False), _f("source", nullable=False),
            indexes=(CharterIndex("idx_alias_name", ("alias_name",)), CharterIndex("idx_alias_concept", ("concept_id",)))),
        _charter("parameterization", ParameterizationRecord, "output_concept_id",
            _f("output_concept_id", nullable=False), _f("concept_ids", nullable=False), _f("formula", nullable=False),
            _f("sympy"), _f("exactness", nullable=False), _f("conditions_cel"), _f("conditions_ir")),
        _charter("parameterization_group", ParameterizationGroupRecord, "concept_id",
            _f("concept_id", nullable=False), _i("group_id", nullable=False),
            indexes=(CharterIndex("idx_param_group", ("group_id",)),)),
        _charter("relationship", RelationshipRecord, "source_id",
            _f("source_id", nullable=False), _f("type", nullable=False), _f("target_id", nullable=False),
            _f("conditions_cel"), _f("note"),
            indexes=(CharterIndex("idx_rel_source", ("source_id",)), CharterIndex("idx_rel_target", ("target_id",)))),
        _charter("relation_edge", RelationEdgeRecord, "id",
            _i("id", primary_key=True, nullable=False), _f("source_kind", nullable=False), _f("source_id", nullable=False),
            _f("relation_type", nullable=False), _f("target_kind", nullable=False), _f("target_id", nullable=False),
            _f("perspective_source_claim_id"), _f("target_justification_id"), _f("conditions_cel"), _f("strength"),
            _f("conditions_differ"), _f("note"), _f("resolution_method"), _f("resolution_model"), _f("embedding_model"),
            _r("embedding_distance"), _i("pass_number"), _r("confidence"), _r("opinion_belief"), _r("opinion_disbelief"),
            _r("opinion_uncertainty"), _r("opinion_base_rate"),
            indexes=(CharterIndex("idx_relation_edge_source", ("source_kind", "source_id")),
                     CharterIndex("idx_relation_edge_target", ("target_kind", "target_id")),
                     CharterIndex("idx_relation_edge_type", ("relation_type",)))),
        _charter("form", Form, "name", _f("name", primary_key=True), _f("kind", nullable=False), _f("unit_symbol"),
            _i("is_dimensionless", nullable=False, default_sql="0"), _f("dimensions")),
        _charter("form_algebra", FormAlgebra, "id",
            _i("id", primary_key=True, nullable=False), _f("output_form", nullable=False), _f("input_forms", nullable=False),
            _f("operation", nullable=False), _f("source_concept_id"), _f("source_formula"),
            _i("dim_verified", nullable=False, default_sql="1"), indexes=(CharterIndex("idx_form_algebra_output", ("output_form",)),)),
        _charter("context", ContextRecord, "id", _f("id", primary_key=True, nullable=False), _f("name", nullable=False),
            _f("description"), _f("parameters_json"), _f("perspective")),
        _charter("context_assumption", ContextAssumptionRecord, "context_id", _f("context_id", nullable=False), _f("assumption_cel", nullable=False), _i("seq", nullable=False),
            indexes=(CharterIndex("idx_context_assumption_context_id", ("context_id",)),)),
        _charter("context_lifting_rule", ContextLiftingRuleRecord, "id",
            _f("id", primary_key=True, nullable=False), _f("source_context_id", nullable=False), _f("target_context_id", nullable=False),
            _f("conditions_cel"), _f("mode", nullable=False), _f("justification"),
            indexes=(CharterIndex("idx_context_lifting_rule_source_context_id", ("source_context_id",)),
                     CharterIndex("idx_context_lifting_rule_target_context_id", ("target_context_id",)))),
        _charter("context_lifting_materialization", ContextLiftingMaterializationRecord, "id",
            _i("id", primary_key=True, nullable=False), _f("rule_id", nullable=False), _f("source_context_id", nullable=False),
            _f("target_context_id", nullable=False), _f("proposition_id", nullable=False), _f("status", nullable=False),
            _f("exception_id"), _f("provenance_json", nullable=False),
            indexes=(CharterIndex("idx_context_lifting_materialization_source_context_id", ("source_context_id",)),
                     CharterIndex("idx_context_lifting_materialization_target_context_id", ("target_context_id",)))),
        _claim_core_charter(),
        _charter("claim_concept_link", ClaimConceptLinkRecord, "claim_id",
            _f("claim_id", primary_key=True, nullable=False), _f("concept_id", primary_key=True, nullable=False),
            _f("role", primary_key=True, nullable=False), _i("ordinal", primary_key=True, nullable=False), _f("binding_name"),
            indexes=(CharterIndex("idx_claim_concept_link_claim", ("claim_id",)), CharterIndex("idx_claim_concept_link_concept", ("concept_id",)), CharterIndex("idx_claim_concept_link_role", ("role",)))),
        _claim_payload_charters()[0], _claim_payload_charters()[1], _claim_payload_charters()[2],
        _charter("conflict_witness", ConflictWitnessRecord, "id",
            _i("id", primary_key=True, nullable=False), _f("claim_a_id", nullable=False), _f("claim_b_id", nullable=False),
            _f("concept_id", nullable=False), _f("warning_class", nullable=False), _f("conditions_a"), _f("conditions_b"),
            _f("value_a"), _f("value_b"), _f("derivation_chain"), indexes=(CharterIndex("idx_conflict_witness_concept", ("concept_id",)),)),
        _charter("grounded_fact", GroundedFactRecord, "predicate", _f("predicate", primary_key=True, nullable=False), _f("arguments", primary_key=True, nullable=False), _f("section", primary_key=True, nullable=False)),
        _charter("grounded_fact_empty_predicate", GroundedFactEmptyPredicateRecord, "section", _f("section", primary_key=True, nullable=False), _f("predicate", primary_key=True, nullable=False)),
        _charter("grounded_bundle_input", GroundedBundleInputRecord, "kind", _f("kind", primary_key=True, nullable=False), _i("position", primary_key=True, nullable=False), _b("payload", nullable=False)),
        _charter("justification", JustificationRecord, "id",
            _f("id", primary_key=True, nullable=False), _f("justification_kind", nullable=False), _f("conclusion_claim_id", nullable=False),
            _f("premise_claim_ids", nullable=False), _f("source_relation_type"), _f("source_claim_id"), _f("provenance_json"),
            _f("rule_strength", nullable=False, default_sql="'defeasible'")),
        _charter("micropublication", MicropublicationRecord, "id",
            _f("id", primary_key=True, nullable=False), _f("context_id", nullable=False), _f("assumptions_json", nullable=False, default_sql="'[]'"),
            _f("evidence_json", nullable=False, default_sql="'[]'"), _f("stance"), _f("provenance_json"), _f("source_slug"),
            indexes=(CharterIndex("idx_micropub_context", ("context_id",)),)),
        _charter("micropublication_claim", MicropublicationClaimRecord, "micropublication_id",
            _f("micropublication_id", primary_key=True, nullable=False), _f("claim_id", primary_key=True, nullable=False), _i("seq", nullable=False),
            indexes=(CharterIndex("idx_micropub_claim", ("claim_id",)),)),
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
) -> FamilyCharter:
    return FamilyCharter(
        family=_world_family(name, model, identity_field),
        model=model,
        fields=fields,
        indexes=indexes,
        fts_indexes=fts_indexes,
        semantic_metadata={"semantic": "propstore.world"},
    )


def _world_family(name: str, model: type[Any], identity_field: str) -> FamilyDefinition[Any, Any, Any, Any]:
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
    )


def _f(name: str, *, nullable: bool = True, primary_key: bool = False, default_sql: str | None = None) -> CharterField:
    return CharterField(name, str, nullable=nullable and not primary_key, primary_key=primary_key, default_sql=default_sql)


def _i(name: str, *, nullable: bool = True, primary_key: bool = False, default_sql: str | None = None) -> CharterField:
    return CharterField(name, int, nullable=nullable and not primary_key, primary_key=primary_key, default_sql=default_sql)


def _r(name: str, *, nullable: bool = True) -> CharterField:
    return CharterField(name, float, nullable=nullable)


def _b(name: str, *, nullable: bool = True) -> CharterField:
    return CharterField(name, bytes, nullable=nullable)


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


def _claim_core_charter() -> FamilyCharter:
    return _charter("claim_core", ClaimCoreRecord, "id",
        _f("id", primary_key=True, nullable=False), _f("primary_logical_id", nullable=False, default_sql="''"),
        _f("logical_ids_json", nullable=False, default_sql="'[]'"), _f("version_id", nullable=False, default_sql="''"),
        _f("content_hash", nullable=False, default_sql="''"), _i("seq", nullable=False), _f("type", nullable=False),
        _f("target_concept"), _f("source_slug"), _f("source_paper", nullable=False), _i("provenance_page", nullable=False),
        _f("provenance_json"), _f("context_id"), _f("premise_kind", nullable=False, default_sql="'ordinary'"),
        _f("branch"), _f("build_status", nullable=False, default_sql="'ingested'"), _f("stage"), _f("promotion_status"),
        indexes=(CharterIndex("idx_claim_core_target", ("target_concept",)), CharterIndex("idx_claim_core_type", ("type",)),
                 CharterIndex("idx_claim_core_primary_logical_id", ("primary_logical_id",)), CharterIndex("idx_claim_core_build_status", ("build_status",)),
                 CharterIndex("idx_claim_core_stage", ("stage",)), CharterIndex("idx_claim_core_promotion_status", ("promotion_status",))),
        fts_indexes=(CharterFtsIndex("claim_fts", "claim_id", ("statement", "conditions", "expression"), source_query=_CLAIM_FTS_SOURCE_QUERY),))


def _claim_payload_charters() -> tuple[FamilyCharter, FamilyCharter, FamilyCharter]:
    return (
        _charter("claim_numeric_payload", ClaimNumericPayloadRecord, "claim_id",
            _f("claim_id", primary_key=True, nullable=False), _r("value"), _r("lower_bound"), _r("upper_bound"), _r("uncertainty"),
            _f("uncertainty_type"), _i("sample_size"), _f("unit"), _r("value_si"), _r("lower_bound_si"), _r("upper_bound_si")),
        _charter("claim_text_payload", ClaimTextPayloadRecord, "claim_id",
            _f("claim_id", primary_key=True, nullable=False), _f("conditions_cel"), _f("conditions_ir"), _f("statement"),
            _f("expression"), _f("sympy_generated"), _f("sympy_error"), _f("name"), _f("measure"), _f("listener_population"),
            _f("methodology"), _f("notes"), _f("description"), _f("auto_summary")),
        _charter("claim_algorithm_payload", ClaimAlgorithmPayloadRecord, "claim_id",
            _f("claim_id", primary_key=True, nullable=False), _f("body"), _f("canonical_ast"), _f("variables_json"), _f("algorithm_stage"),
            indexes=(CharterIndex("idx_claim_algorithm_stage", ("algorithm_stage",)),)),
    )


def _support_charters() -> tuple[FamilyCharter, FamilyCharter, FamilyCharter, FamilyCharter, FamilyCharter]:
    return (
        _charter("calibration_counts", CalibrationCountsRecord, "pass_number",
            _i("pass_number", primary_key=True, nullable=False), _f("category", primary_key=True, nullable=False), _i("correct_count", nullable=False), _i("total_count", nullable=False)),
        _charter("embedding_model", EmbeddingModelRecord, "model_identity_hash",
            _f("model_identity_hash", primary_key=True, nullable=False), _f("provider", nullable=False), _f("model_name", nullable=False),
            _f("model_version", nullable=False, default_sql="''"), _f("content_digest", nullable=False), _i("dimensions", nullable=False), _f("created_at", nullable=False)),
        _charter("embedding_status", EmbeddingStatusRecord, "model_identity_hash",
            _f("model_identity_hash", primary_key=True, nullable=False), _f("claim_id", primary_key=True, nullable=False), _f("content_hash", nullable=False), _f("embedded_at", nullable=False),
            indexes=(CharterIndex("idx_embedding_status_model_identity", ("model_identity_hash",)),)),
        _charter("concept_embedding_status", ConceptEmbeddingStatusRecord, "model_identity_hash",
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
