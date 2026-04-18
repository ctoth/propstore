"""Shared test helpers for propstore tests.

Plain functions (not pytest fixtures) since callers invoke them directly.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from copy import deepcopy
from types import MappingProxyType

from hypothesis import settings

from propstore.artifacts.codecs import convert_document
from propstore.artifacts.families import CONCEPT_FILE_FAMILY
from propstore.identity import normalize_canonical_concept_payload
from propstore.cel_checker import KindType
from propstore.core.concepts import concept_document_to_record_payload
from propstore.form_utils import FormDefinition
from propstore.identity import (
    compute_claim_version_id,
    compute_concept_version_id,
    derive_claim_artifact_id,
    derive_concept_artifact_id,
    normalize_identity_namespace,
    normalize_logical_value,
)
from propstore.sidecar.schema import SCHEMA_VERSION, SIDECAR_META_KEY


TEST_CONTEXT_ID = "ctx_test"
TEST_CONTEXT_PAYLOAD = {"id": TEST_CONTEXT_ID, "name": "Test context"}


def write_test_context(knowledge_root, context_id: str = TEST_CONTEXT_ID) -> None:
    """Author the explicit test context required by context-qualified claims."""
    import yaml

    contexts_dir = knowledge_root / "contexts"
    contexts_dir.mkdir(parents=True, exist_ok=True)
    (contexts_dir / f"{context_id}.yaml").write_text(
        yaml.dump({"id": context_id, "name": "Test context"}, default_flow_style=False)
    )


def make_test_context_commit_entry(context_id: str = TEST_CONTEXT_ID) -> tuple[str, bytes]:
    import yaml

    return (
        f"contexts/{context_id}.yaml",
        yaml.dump({"id": context_id, "name": "Test context"}, default_flow_style=False).encode(
            "utf-8"
        ),
    )


settings.register_profile("default", deadline=None)
settings.register_profile("overnight", deadline=None, max_examples=1000)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))


def _rewrite_concept_ref(value: object) -> object:
    if isinstance(value, str) and value.startswith("concept") and ":" not in value:
        return derive_concept_artifact_id("propstore", value)
    return value


def _canonical_concept_ref(value: str | None) -> str | None:
    if value is None:
        return None
    rewritten = _rewrite_concept_ref(value)
    return str(rewritten) if isinstance(rewritten, str) else value


def make_claim_identity(local_id: str, *, namespace: str = "test") -> dict:
    """Build deterministic test identity fields for a claim."""
    artifact_id = derive_claim_artifact_id(namespace, local_id)
    logical_ids = [{"namespace": namespace, "value": local_id}]
    return {
        "artifact_id": artifact_id,
        "logical_ids": logical_ids,
    }


def attach_claim_version_id(claim: dict) -> dict:
    """Return a claim dict with a correct version_id."""
    enriched = dict(claim)
    enriched["version_id"] = compute_claim_version_id(enriched)
    return enriched


def make_concept_identity(
    local_id: str,
    *,
    domain: str = "test",
    canonical_name: str | None = None,
) -> dict:
    """Build deterministic test identity fields for a concept."""
    primary_namespace = normalize_identity_namespace(domain or "propstore")
    primary_value = normalize_logical_value(canonical_name or local_id)
    logical_ids = [{"namespace": primary_namespace, "value": primary_value}]
    if local_id != primary_value or primary_namespace != "propstore":
        logical_ids.append({"namespace": "propstore", "value": normalize_logical_value(local_id)})
    return {
        "artifact_id": derive_concept_artifact_id("propstore", local_id),
        "logical_ids": logical_ids,
    }


def attach_concept_version_id(concept: dict) -> dict:
    """Return a concept dict with a correct version_id."""
    enriched = dict(concept)
    enriched["version_id"] = compute_concept_version_id(enriched)
    return enriched


def concept_artifact_to_record_payload(concept: dict) -> dict:
    """Project a canonical concept artifact payload to the runtime record payload."""
    document = convert_document(
        concept,
        CONCEPT_FILE_FAMILY.doc_type,
        source="test concept artifact",
    )
    return concept_document_to_record_payload(document)


def normalize_claims_payload(data: dict, *, default_namespace: str | None = None) -> dict:
    """Return a claim-file payload with deterministic claim identities."""
    normalized_data = dict(data)
    source = normalized_data.get("source")
    paper = (
        source.get("paper")
        if isinstance(source, dict) and isinstance(source.get("paper"), str)
        else (default_namespace or "test")
    )
    raw_claims = list(normalized_data.get("claims", []))
    local_to_artifact: dict[str, str] = {}
    normalized_claims = []
    for index, claim in enumerate(raw_claims, start=1):
        if not isinstance(claim, dict):
            normalized_claims.append(claim)
            continue
        normalized = dict(claim)
        if "artifact_id" not in normalized:
            raw_id = normalized.pop("id", f"claim{index}")
            logical = make_claim_identity(str(raw_id), namespace=paper)
            normalized.update(logical)
            if isinstance(raw_id, str):
                local_to_artifact[raw_id] = logical["artifact_id"]
        elif isinstance(normalized.get("artifact_id"), str):
            raw_id = normalized.get("id")
            if isinstance(raw_id, str):
                local_to_artifact[raw_id] = normalized["artifact_id"]
        normalized.setdefault("context", {"id": TEST_CONTEXT_ID})
        normalized_claims.append(normalized)

    for index, normalized in enumerate(normalized_claims):
        if not isinstance(normalized, dict):
            continue
        stances = normalized.get("stances")
        if isinstance(stances, list):
            rewritten_stances = []
            for stance in stances:
                if not isinstance(stance, dict):
                    rewritten_stances.append(stance)
                    continue
                rewritten = dict(stance)
                target = rewritten.get("target")
                if isinstance(target, str) and target in local_to_artifact:
                    rewritten["target"] = local_to_artifact[target]
                rewritten_stances.append(rewritten)
            normalized["stances"] = rewritten_stances
        normalized_claims[index] = attach_claim_version_id(normalized)
    normalized_data["claims"] = normalized_claims
    return normalized_data


def normalize_concept_payloads(
    concepts: list[dict],
    *,
    default_domain: str | None = None,
) -> list[dict]:
    """Return canonical lemon concept artifact payloads with stable identities."""
    raw_to_artifact: dict[str, str] = {}
    normalized_concepts: list[dict] = []
    for concept in concepts:
        raw_id = concept.get("id")
        normalized = normalize_canonical_concept_payload(
            deepcopy(concept),
            default_domain=default_domain,
            local_handle=str(raw_id) if isinstance(raw_id, str) else None,
        )
        if isinstance(raw_id, str) and isinstance(normalized.get("artifact_id"), str):
            raw_to_artifact[raw_id] = normalized["artifact_id"]
        normalized_concepts.append(normalized)

    for index, concept in enumerate(normalized_concepts):
        rewritten = deepcopy(concept)
        replaced_by = rewritten.get("replaced_by")
        if isinstance(replaced_by, str):
            rewritten["replaced_by"] = raw_to_artifact.get(replaced_by, _rewrite_concept_ref(replaced_by))

        relationships = rewritten.get("relationships")
        if isinstance(relationships, list):
            rewritten_relationships = []
            for rel in relationships:
                if not isinstance(rel, dict):
                    rewritten_relationships.append(rel)
                    continue
                rel_copy = dict(rel)
                target = rel_copy.get("target")
                if isinstance(target, str):
                    rel_copy["target"] = raw_to_artifact.get(target, _rewrite_concept_ref(target))
                rewritten_relationships.append(rel_copy)
            rewritten["relationships"] = rewritten_relationships

        parameterizations = rewritten.get("parameterization_relationships")
        if isinstance(parameterizations, list):
            rewritten_params = []
            for param in parameterizations:
                if not isinstance(param, dict):
                    rewritten_params.append(param)
                    continue
                param_copy = dict(param)
                inputs = param_copy.get("inputs")
                if isinstance(inputs, list):
                    param_copy["inputs"] = [
                        raw_to_artifact.get(str(input_id), _rewrite_concept_ref(input_id))
                        for input_id in inputs
                    ]
                rewritten_params.append(param_copy)
            rewritten["parameterization_relationships"] = rewritten_params

        normalized_concepts[index] = attach_concept_version_id(rewritten)

    return normalized_concepts


def create_argumentation_schema(conn: sqlite3.Connection) -> None:
    """Create minimal normalized claim/relation/conflict tables for testing."""
    conn.executescript("""
        CREATE TABLE claim_core (
            id TEXT PRIMARY KEY,
            primary_logical_id TEXT,
            logical_ids_json TEXT,
            version_id TEXT,
            type TEXT,
            concept_id TEXT,
            target_concept TEXT,
            seq INTEGER,
            source_slug TEXT,
            source_paper TEXT NOT NULL DEFAULT 'test',
            provenance_page INTEGER NOT NULL DEFAULT 1,
            provenance_json TEXT,
            context_id TEXT
        );

        CREATE TABLE claim_numeric_payload (
            claim_id TEXT PRIMARY KEY,
            value REAL,
            sample_size INTEGER,
            uncertainty REAL,
            confidence REAL,
            uncertainty_type TEXT,
            unit TEXT
        );

        CREATE TABLE claim_text_payload (
            claim_id TEXT PRIMARY KEY,
            conditions_cel TEXT,
            statement TEXT,
            expression TEXT,
            auto_summary TEXT
        );

        CREATE TABLE claim_algorithm_payload (
            claim_id TEXT PRIMARY KEY,
            body TEXT,
            canonical_ast TEXT,
            variables_json TEXT,
            algorithm_stage TEXT
        );

        CREATE TABLE relation_edge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_kind TEXT NOT NULL,
            source_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            target_kind TEXT NOT NULL,
            target_id TEXT NOT NULL,
            conditions_cel TEXT,
            target_justification_id TEXT,
            strength TEXT,
            conditions_differ TEXT,
            note TEXT,
            resolution_method TEXT,
            resolution_model TEXT,
            embedding_model TEXT,
            embedding_distance REAL,
            pass_number INTEGER,
            confidence REAL,
            opinion_belief REAL,
            opinion_disbelief REAL,
            opinion_uncertainty REAL,
            opinion_base_rate REAL DEFAULT 0.5,
            CHECK(opinion_belief IS NULL OR (opinion_belief >= 0 AND opinion_belief <= 1)),
            CHECK(opinion_disbelief IS NULL OR (opinion_disbelief >= 0 AND opinion_disbelief <= 1)),
            CHECK(opinion_uncertainty IS NULL OR (opinion_uncertainty >= 0 AND opinion_uncertainty <= 1)),
            CHECK(opinion_base_rate IS NULL OR (opinion_base_rate > 0 AND opinion_base_rate < 1)),
            CHECK(opinion_belief IS NULL OR ABS(opinion_belief + opinion_disbelief + opinion_uncertainty - 1.0) <= 1e-6)
        );

        CREATE TABLE IF NOT EXISTS conflict_witness (
            concept_id TEXT NOT NULL,
            claim_a_id TEXT NOT NULL,
            claim_b_id TEXT NOT NULL,
            warning_class TEXT NOT NULL,
            conditions_a TEXT,
            conditions_b TEXT,
            value_a TEXT,
            value_b TEXT,
            derivation_chain TEXT
        );
    """)


def create_world_model_schema(conn: sqlite3.Connection) -> None:
    """Create the canonical sidecar schema expected by WorldModel."""
    conn.executescript("""
        CREATE TABLE meta (
            key TEXT PRIMARY KEY,
            schema_version INTEGER NOT NULL
        );

        CREATE TABLE source (
            slug TEXT PRIMARY KEY,
            source_id TEXT,
            kind TEXT,
            origin_type TEXT,
            origin_value TEXT,
            origin_retrieved TEXT,
            origin_content_ref TEXT,
            prior_base_rate REAL,
            quality_json TEXT,
            derived_from_json TEXT
        );

        CREATE TABLE concept (
            id TEXT PRIMARY KEY,
            canonical_name TEXT,
            kind_type TEXT,
            form TEXT,
            form_parameters TEXT,
            primary_logical_id TEXT DEFAULT '',
            logical_ids_json TEXT DEFAULT '[]',
            status TEXT,
            domain TEXT,
            definition TEXT
        );

        CREATE TABLE alias (
            concept_id TEXT NOT NULL,
            alias_name TEXT NOT NULL
        );

        CREATE TABLE relationship (
            source_id TEXT,
            type TEXT,
            target_id TEXT,
            conditions_cel TEXT,
            note TEXT
        );

        CREATE TABLE parameterization (
            output_concept_id TEXT NOT NULL,
            formula_text TEXT,
            sympy TEXT,
            source TEXT,
            exactness TEXT
        );

        CREATE TABLE parameterization_group (
            group_id INTEGER NOT NULL,
            concept_id TEXT NOT NULL
        );

        CREATE TABLE relation_edge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_kind TEXT NOT NULL,
            source_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            target_kind TEXT NOT NULL,
            target_id TEXT NOT NULL,
            conditions_cel TEXT,
            target_justification_id TEXT,
            strength TEXT,
            conditions_differ TEXT,
            note TEXT,
            resolution_method TEXT,
            resolution_model TEXT,
            embedding_model TEXT,
            embedding_distance REAL,
            pass_number INTEGER,
            confidence REAL,
            opinion_belief REAL,
            opinion_disbelief REAL,
            opinion_uncertainty REAL,
            opinion_base_rate REAL
        );

        CREATE TABLE form (
            name TEXT PRIMARY KEY,
            dimensions TEXT,
            is_dimensionless INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE form_algebra (
            output_form TEXT NOT NULL,
            input_forms TEXT NOT NULL,
            source_formula TEXT,
            source_concept_id TEXT
        );

        CREATE VIRTUAL TABLE concept_fts USING fts5(
            concept_id UNINDEXED,
            canonical_name,
            aliases,
            definition,
            conditions
        );

        CREATE TABLE context (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            parameters_json TEXT,
            perspective TEXT
        );

        CREATE TABLE context_assumption (
            context_id TEXT NOT NULL,
            assumption_cel TEXT NOT NULL,
            seq INTEGER NOT NULL
        );

        CREATE TABLE context_lifting_rule (
            id TEXT PRIMARY KEY,
            source_context_id TEXT NOT NULL,
            target_context_id TEXT NOT NULL,
            conditions_cel TEXT NOT NULL DEFAULT '[]',
            mode TEXT NOT NULL,
            justification TEXT
        );

        CREATE TABLE claim_core (
            id TEXT PRIMARY KEY,
            primary_logical_id TEXT NOT NULL DEFAULT '',
            logical_ids_json TEXT NOT NULL DEFAULT '[]',
            version_id TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            seq INTEGER NOT NULL,
            type TEXT NOT NULL,
            concept_id TEXT,
            target_concept TEXT,
            source_slug TEXT,
            source_paper TEXT NOT NULL DEFAULT 'test',
            provenance_page INTEGER NOT NULL DEFAULT 1,
            provenance_json TEXT,
            context_id TEXT,
            premise_kind TEXT NOT NULL DEFAULT 'ordinary',
            branch TEXT,
            build_status TEXT NOT NULL DEFAULT 'ingested',
            stage TEXT,
            promotion_status TEXT
        );

        CREATE TABLE claim_numeric_payload (
            claim_id TEXT PRIMARY KEY,
            value REAL,
            lower_bound REAL,
            upper_bound REAL,
            uncertainty REAL,
            uncertainty_type TEXT,
            sample_size INTEGER,
            unit TEXT,
            value_si REAL,
            lower_bound_si REAL,
            upper_bound_si REAL
        );

        CREATE TABLE claim_text_payload (
            claim_id TEXT PRIMARY KEY,
            conditions_cel TEXT,
            statement TEXT,
            expression TEXT,
            sympy_generated TEXT,
            sympy_error TEXT,
            name TEXT,
            measure TEXT,
            listener_population TEXT,
            methodology TEXT,
            notes TEXT,
            description TEXT,
            auto_summary TEXT
        );

        CREATE TABLE claim_algorithm_payload (
            claim_id TEXT PRIMARY KEY,
            body TEXT,
            canonical_ast TEXT,
            variables_json TEXT,
            algorithm_stage TEXT
        );

        CREATE TABLE conflict_witness (
            concept_id TEXT NOT NULL,
            claim_a_id TEXT NOT NULL,
            claim_b_id TEXT NOT NULL,
            warning_class TEXT NOT NULL,
            conditions_a TEXT,
            conditions_b TEXT,
            value_a TEXT,
            value_b TEXT,
            derivation_chain TEXT
        );
    """)
    conn.execute(
        "INSERT INTO meta (key, schema_version) VALUES (?, ?)",
        (SIDECAR_META_KEY, SCHEMA_VERSION),
    )
    conn.commit()


def insert_claim(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    claim_type: str | None = None,
    concept_id: str | None = None,
    target_concept: str | None = None,
    value: float | None = None,
    sample_size: int | None = None,
    uncertainty: float | None = None,
    confidence: float | None = None,
    uncertainty_type: str | None = None,
    unit: str | None = None,
    conditions_cel: str | None = None,
    statement: str | None = None,
    expression: str | None = None,
    auto_summary: str | None = None,
    source_paper: str = "test",
    source_slug: str | None = None,
    provenance_page: int = 1,
    seq: int = 0,
) -> None:
    logical_id = f"test:{claim_id}"
    version_id = f"sha256:{hashlib.sha256(claim_id.encode('utf-8')).hexdigest()}"
    resolved_source_slug = source_paper if source_slug is None else source_slug
    conn.execute(
        """
        INSERT INTO claim_core (
            id, primary_logical_id, logical_ids_json, version_id,
            type, concept_id, target_concept, seq,
            source_slug, source_paper, provenance_page, provenance_json, context_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            logical_id,
            json.dumps([{"namespace": "test", "value": claim_id}]),
            version_id,
            claim_type,
            concept_id,
            target_concept,
            seq,
            resolved_source_slug,
            source_paper,
            provenance_page,
            None,
            None,
        ),
    )
    conn.execute(
        """
        INSERT INTO claim_numeric_payload (
            claim_id, value, sample_size, uncertainty, confidence, uncertainty_type, unit
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (claim_id, value, sample_size, uncertainty, confidence, uncertainty_type, unit),
    )
    conn.execute(
        """
        INSERT INTO claim_text_payload (
            claim_id, conditions_cel, statement, expression, auto_summary
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (claim_id, conditions_cel, statement, expression, auto_summary),
    )


def insert_stance(
    conn: sqlite3.Connection,
    claim_id: str,
    target_claim_id: str,
    stance_type: str,
    *,
    target_justification_id: str | None = None,
    strength: str | None = None,
    conditions_differ: str | None = None,
    note: str | None = None,
    resolution_method: str | None = None,
    resolution_model: str | None = None,
    embedding_model: str | None = None,
    embedding_distance: float | None = None,
    pass_number: int | None = None,
    confidence: float | None = None,
    opinion_belief: float | None = None,
    opinion_disbelief: float | None = None,
    opinion_uncertainty: float | None = None,
    opinion_base_rate: float | None = 0.5,
) -> None:
    conn.execute(
        """
        INSERT INTO relation_edge (
            source_kind, source_id, relation_type, target_kind, target_id,
            target_justification_id,
            strength, conditions_differ, note, resolution_method, resolution_model,
            embedding_model, embedding_distance, pass_number, confidence,
            opinion_belief, opinion_disbelief, opinion_uncertainty, opinion_base_rate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "claim",
            claim_id,
            stance_type,
            "claim",
            target_claim_id,
            target_justification_id,
            strength,
            conditions_differ,
            note,
            resolution_method,
            resolution_model,
            embedding_model,
            embedding_distance,
            pass_number,
            confidence,
            opinion_belief,
            opinion_disbelief,
            opinion_uncertainty,
            opinion_base_rate,
        ),
    )


def insert_conflict(
    conn: sqlite3.Connection,
    *,
    concept_id: str,
    claim_a_id: str,
    claim_b_id: str,
    warning_class: str,
    conditions_a: str | None = None,
    conditions_b: str | None = None,
    value_a: str | None = None,
    value_b: str | None = None,
    derivation_chain: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO conflict_witness (
            concept_id, claim_a_id, claim_b_id, warning_class,
            conditions_a, conditions_b, value_a, value_b, derivation_chain
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            concept_id,
            claim_a_id,
            claim_b_id,
            warning_class,
            conditions_a,
            conditions_b,
            value_a,
            value_b,
            derivation_chain,
        ),
    )


def make_parameter_claim(id, concept_id, value, unit="Hz", *, page=1, paper="test_paper", **kwargs):
    """Build a minimal parameter claim dict for testing.

    Supports keyword-only extras via **kwargs (e.g. notes, conditions).
    """
    c = {
        **make_claim_identity(id, namespace=paper),
        "type": "parameter",
        "concept": _canonical_concept_ref(concept_id),
        "value": value,
        "unit": unit,
        "provenance": {"paper": paper, "page": page},
        "context": {"id": TEST_CONTEXT_ID},
    }
    c.update(kwargs)
    return attach_claim_version_id(c)


def make_concept_registry():
    """Build a mock concept registry for testing.

    Returns 3 concepts covering frequency, pressure, and category forms.
    """
    concept_artifacts = normalize_concept_payloads([
        {
            "id": "concept1",
            "canonical_name": "fundamental_frequency",
            "form": "frequency",
            "status": "accepted",
            "definition": "F0",
            "domain": "speech",
        },
        {
            "id": "concept2",
            "canonical_name": "subglottal_pressure",
            "form": "pressure",
            "status": "accepted",
            "definition": "Ps",
            "domain": "speech",
        },
        {
            "id": "concept3",
            "canonical_name": "task",
            "form": "category",
            "form_parameters": {"values": ["speech", "singing", "whisper"], "extensible": True},
            "status": "accepted",
            "definition": "Task type",
            "domain": "speech",
        },
        {
            "id": "concept4",
            "canonical_name": "hazard_ratio",
            "form": "ratio",
            "status": "accepted",
            "definition": "Ratio of hazard rates",
            "domain": "speech",
        },
    ], default_domain="speech")
    concepts = [
        concept_artifact_to_record_payload(concept)
        for concept in concept_artifacts
    ]
    registry: dict[str, dict] = {}
    form_definitions = {
        "frequency": FormDefinition(
            name="frequency",
            kind=KindType.QUANTITY,
            unit_symbol="Hz",
            allowed_units={"Hz"},
        ),
        "pressure": FormDefinition(
            name="pressure",
            kind=KindType.QUANTITY,
            unit_symbol="Pa",
            allowed_units={"Pa"},
        ),
        "category": FormDefinition(
            name="category",
            kind=KindType.CATEGORY,
            is_dimensionless=True,
        ),
        "ratio": FormDefinition(
            name="ratio",
            kind=KindType.QUANTITY,
            is_dimensionless=True,
        ),
    }
    for concept in concepts:
        form_name = concept.get("form")
        if isinstance(form_name, str) and form_name in form_definitions:
            concept["_form_definition"] = form_definitions[form_name]
        artifact_id = concept["artifact_id"]
        registry[artifact_id] = concept
        registry[concept["canonical_name"]] = concept
        for logical_id in concept.get("logical_ids", []):
            if isinstance(logical_id, dict):
                registry[f"{logical_id['namespace']}:{logical_id['value']}"] = concept
        if concept["canonical_name"] == "fundamental_frequency":
            registry["F0"] = concept
        if concept["canonical_name"] == "subglottal_pressure":
            registry["Ps"] = concept
    return registry


def make_compilation_context(registry: dict[str, dict] | None = None, *, claim_files=None, context_ids=None):
    from propstore.cel_registry import build_canonical_cel_registry
    from propstore.compiler.context import CompilationContext
    from propstore.compiler.references import build_claim_reference_lookup
    from propstore.core.concepts import concept_reference_keys, parse_concept_record

    source_registry = make_concept_registry() if registry is None else registry
    concepts_by_id = {}
    concept_lookup: dict[str, list[str]] = {}
    form_registry = {}

    def extend_lookup(key: object, target_id: str) -> None:
        if not isinstance(key, str) or not key:
            return
        values = concept_lookup.setdefault(key, [])
        if target_id not in values:
            values.append(target_id)

    for key, payload in source_registry.items():
        if not isinstance(payload, dict):
            continue
        record = parse_concept_record(payload)
        artifact_id = str(record.artifact_id)
        concepts_by_id.setdefault(artifact_id, record)
        extend_lookup(key, artifact_id)
        for reference_key in concept_reference_keys(record):
            extend_lookup(reference_key, artifact_id)
        form_definition = payload.get("_form_definition")
        if isinstance(form_definition, FormDefinition):
            form_registry.setdefault(record.form, form_definition)

    return CompilationContext(
        form_registry=MappingProxyType(dict(form_registry)),
        context_ids=frozenset(context_ids or set()),
        concepts_by_id=MappingProxyType(dict(concepts_by_id)),
        concept_lookup=MappingProxyType({
            key: tuple(values)
            for key, values in concept_lookup.items()
        }),
        claim_lookup=(
            MappingProxyType({})
            if claim_files is None
            else build_claim_reference_lookup(list(claim_files))
        ),
        cel_registry=MappingProxyType(dict(build_canonical_cel_registry(concepts_by_id.values()))),
    )


def make_cel_registry(registry: dict[str, dict] | None = None) -> dict[str, object]:
    return dict(make_compilation_context(registry).cel_registry)
