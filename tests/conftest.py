"""Shared test helpers for propstore tests.

Plain functions (not pytest fixtures) since callers invoke them directly.
"""

from __future__ import annotations

import hashlib
import json
import os

import msgspec
from sqlite3 import Connection
import warnings
from types import MappingProxyType

import pytest
from hypothesis import settings
from quire.references import FamilyReferenceIndex

from propstore.core.conditions.registry import KindType
from propstore.families.identity.claims import (
    compute_claim_version_id,
    derive_claim_artifact_id,
)
from propstore.families.identity.concepts import (
    compute_concept_version_id,
    derive_concept_artifact_id,
)
from propstore.families.identity.logical_ids import (
    normalize_identity_namespace,
    normalize_logical_value,
)
from propstore.families.forms.stages import FormDefinition
from propstore.opinion import Opinion


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


def make_test_context_commit_entry(
    context_id: str = TEST_CONTEXT_ID,
) -> tuple[str, bytes]:
    import yaml

    return (
        f"contexts/{context_id}.yaml",
        yaml.dump(
            {"id": context_id, "name": "Test context"}, default_flow_style=False
        ).encode("utf-8"),
    )


settings.register_profile("default", deadline=None)
settings.register_profile("overnight", deadline=None, max_examples=1000)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))


def pytest_collection_modifyitems(config, items) -> None:
    for item in items:
        test_obj = getattr(item, "obj", None)
        if getattr(test_obj, "hypothesis", None) is None:
            continue
        if item.get_closest_marker("property") is not None:
            continue
        warnings.warn(
            pytest.PytestWarning(
                f"Hypothesis test {item.nodeid} is missing @pytest.mark.property"
            ),
            stacklevel=2,
        )


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
        logical_ids.append(
            {"namespace": "propstore", "value": normalize_logical_value(local_id)}
        )
    return {
        "artifact_id": derive_concept_artifact_id("propstore", local_id),
        "logical_ids": logical_ids,
    }


def attach_concept_version_id(concept: dict) -> dict:
    """Return a concept dict with a correct version_id."""
    enriched = dict(concept)
    enriched["version_id"] = compute_concept_version_id(enriched)
    return enriched


def _normalize_claim_concept_fields(claim: dict) -> None:
    claim_type = str(claim.get("type", ""))
    singular_concept = claim.pop("concept", None)
    if singular_concept is not None:
        if claim_type in {"parameter", "algorithm"}:
            claim.setdefault(
                "output_concept", _canonical_concept_ref(str(singular_concept))
            )
        elif claim_type == "measurement":
            claim.setdefault(
                "target_concept", _canonical_concept_ref(str(singular_concept))
            )
        else:
            claim.setdefault(
                "concepts", [_canonical_concept_ref(str(singular_concept))]
            )

    output_concept = claim.get("output_concept")
    if isinstance(output_concept, str):
        claim["output_concept"] = _canonical_concept_ref(output_concept)

    target_concept = claim.get("target_concept")
    if isinstance(target_concept, str):
        claim["target_concept"] = _canonical_concept_ref(target_concept)

    concepts = claim.get("concepts")
    if isinstance(concepts, list):
        claim["concepts"] = [
            _canonical_concept_ref(value) if isinstance(value, str) else value
            for value in concepts
        ]

    for field in ("variables", "parameters"):
        bindings = claim.get(field)
        if not isinstance(bindings, list):
            continue
        rewritten_bindings = []
        for binding in bindings:
            if not isinstance(binding, dict):
                rewritten_bindings.append(binding)
                continue
            rewritten = dict(binding)
            concept = rewritten.get("concept")
            if isinstance(concept, str):
                rewritten["concept"] = _canonical_concept_ref(concept)
            rewritten_bindings.append(rewritten)
        claim[field] = rewritten_bindings


def create_argumentation_schema(conn: Connection) -> None:
    """Create minimal normalized claim/relation/conflict tables for testing."""
    conn.executescript("""
        CREATE TABLE claim_core (
            id TEXT PRIMARY KEY,
            primary_logical_id TEXT,
            logical_ids_json TEXT,
            version_id TEXT,
            type TEXT,
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

        CREATE TABLE claim_concept_link (
            claim_id TEXT NOT NULL,
            concept_id TEXT NOT NULL,
            role TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            binding_name TEXT,
            PRIMARY KEY (claim_id, role, ordinal, concept_id)
        );

        CREATE TABLE relation_edge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_kind TEXT NOT NULL,
            source_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            target_kind TEXT NOT NULL,
            target_id TEXT NOT NULL,
            perspective_source_claim_id TEXT,
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
            opinion TEXT
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


def insert_claim(
    conn: Connection,
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
            type, target_concept, seq,
            source_slug, source_paper, provenance_page, provenance_json, context_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            logical_id,
            json.dumps([{"namespace": "test", "value": claim_id}]),
            version_id,
            claim_type,
            target_concept,
            seq,
            resolved_source_slug,
            source_paper,
            provenance_page,
            None,
            None,
        ),
    )
    if concept_id is not None:
        conn.execute(
            """
            INSERT INTO claim_concept_link (
                claim_id, concept_id, role, ordinal, binding_name
            ) VALUES (?, ?, 'output', 0, NULL)
            """,
            (claim_id, concept_id),
        )
    if target_concept is not None:
        conn.execute(
            """
            INSERT INTO claim_concept_link (
                claim_id, concept_id, role, ordinal, binding_name
            ) VALUES (?, ?, 'target', 0, NULL)
            """,
            (claim_id, target_concept),
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
    conn: Connection,
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
    opinion: Opinion | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO relation_edge (
            source_kind, source_id, relation_type, target_kind, target_id,
            target_justification_id,
            strength, conditions_differ, note, resolution_method, resolution_model,
            embedding_model, embedding_distance, pass_number, confidence,
            opinion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            None if opinion is None else msgspec.json.encode(opinion).decode(),
        ),
    )


def insert_conflict(
    conn: Connection,
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


def make_parameter_claim(
    id, concept_id, value, unit="Hz", *, page=1, paper="test_paper", **kwargs
):
    """Build a minimal parameter claim dict for testing.

    Supports keyword-only extras via **kwargs (e.g. notes, conditions).
    """
    c = {
        **make_claim_identity(id, namespace=paper),
        "type": "parameter",
        "output_concept": _canonical_concept_ref(concept_id),
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
    concept_artifacts = normalize_concept_payloads(
        [
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
                "form_parameters": {
                    "values": ["speech", "singing", "whisper"],
                    "extensible": True,
                },
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
        ],
        default_domain="speech",
    )
    concepts = [
        concept_artifact_to_record_payload(concept) for concept in concept_artifacts
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


def make_compilation_context(
    registry: dict[str, dict] | None = None, *, claim_files=None, context_ids=None
):
    from propstore.cel_registry import build_canonical_cel_registry
    from propstore.compiler.context import (
        CompilationContext,
        build_compiler_claim_index,
    )
    from propstore.families.concepts.stages import (
        concept_reference_keys,
        parse_concept_record,
    )

    source_registry = make_concept_registry() if registry is None else registry
    concepts_by_id = {}
    form_registry = {}

    for key, payload in source_registry.items():
        if not isinstance(payload, dict):
            continue
        record = parse_concept_record(payload)
        artifact_id = str(record.artifact_id)
        concepts_by_id.setdefault(artifact_id, record)
        form_definition = payload.get("_form_definition")
        if isinstance(form_definition, FormDefinition):
            form_registry.setdefault(record.form, form_definition)

    concept_index = FamilyReferenceIndex.from_records(
        concepts_by_id.values(),
        family="concept",
        artifact_id=lambda record: str(record.artifact_id),
        keys=(concept_reference_keys,),
    )
    return CompilationContext(
        form_registry=MappingProxyType(dict(form_registry)),
        context_ids=frozenset(context_ids or set()),
        concepts_by_id=MappingProxyType(dict(concepts_by_id)),
        concept_index=concept_index,
        claim_index=(
            build_compiler_claim_index(())
            if claim_files is None
            else build_compiler_claim_index(list(claim_files))
        ),
        cel_registry=MappingProxyType(
            dict(build_canonical_cel_registry(concepts_by_id.values()))
        ),
    )


def make_cel_registry(registry: dict[str, dict] | None = None) -> dict[str, object]:
    return dict(make_compilation_context(registry).cel_registry)
