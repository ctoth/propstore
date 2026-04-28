"""Structural pins for columns WorldModel requires at sidecar open time."""

from __future__ import annotations

from propstore.world.model import _REQUIRED_SCHEMA


def test_runtime_claim_core_columns_required_in_world_model_schema() -> None:
    required_columns = _REQUIRED_SCHEMA["claim_core"]
    missing = {
        "content_hash",
        "premise_kind",
        "build_status",
        "stage",
        "promotion_status",
    } - required_columns
    assert missing == set(), f"missing required claim_core columns: {sorted(missing)}"


def test_build_diagnostics_required_in_world_model_schema() -> None:
    assert "build_diagnostics" in _REQUIRED_SCHEMA
    assert _REQUIRED_SCHEMA["build_diagnostics"] >= {
        "id",
        "entity_type",
        "entity_id",
        "severity",
        "message",
    }
