"""Shared test helpers for propstore tests.

Plain functions (not pytest fixtures) since callers invoke them directly.
"""

from __future__ import annotations

import os

import msgspec
from sqlite3 import Connection
import warnings

import pytest
from hypothesis import settings

from propstore.families.identity.claims import (
    derive_claim_artifact_id,
)
from propstore.families.identity.concepts import (
    derive_concept_artifact_id,
)
from propstore.families.claims.declaration import (
    AUTHORED_CLAIM_CHARTER,
    ClaimDocument,
)
from propstore.families.concepts.declaration import (
    AUTHORED_CONCEPT_CHARTER,
    ConceptDocument,
)
from propstore.families.identity.logical_ids import (
    normalize_identity_namespace,
    normalize_logical_value,
)
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
    document = AUTHORED_CLAIM_CHARTER.document_codec().convert(
        enriched,
        ClaimDocument,
        source="test claim",
    )
    enriched["version_id"] = AUTHORED_CLAIM_CHARTER.version_id(document)
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
    document = AUTHORED_CONCEPT_CHARTER.document_codec().convert(
        enriched,
        ConceptDocument,
        source="test concept",
    )
    enriched["version_id"] = AUTHORED_CONCEPT_CHARTER.version_id(document)
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


def make_cel_registry(registry: dict[str, dict] | None = None) -> dict[str, object]:
    return dict(make_compilation_context(registry).cel_registry)
