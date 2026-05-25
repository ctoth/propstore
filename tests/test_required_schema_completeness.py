"""Structural pins for columns WorldQuery requires at sidecar open time."""

from __future__ import annotations

from propstore.families.registry import world_schema


def _required_columns_by_table() -> dict[str, frozenset[str]]:
    return {
        table_name: frozenset(table.c.keys())
        for table_name, table in world_schema().tables.items()
    }


def test_runtime_claim_core_columns_required_in_world_model_schema() -> None:
    required_columns = _required_columns_by_table()["claim_core"]
    missing = {
        "content_hash",
        "premise_kind",
        "build_status",
        "stage",
        "promotion_status",
    } - required_columns
    assert missing == set(), f"missing required claim_core columns: {sorted(missing)}"


def test_build_diagnostics_required_in_world_model_schema() -> None:
    required_columns = _required_columns_by_table()
    assert "build_diagnostics" in required_columns
    assert required_columns["build_diagnostics"] >= {
        "id",
        "claim_id",
        "source_kind",
        "source_ref",
        "diagnostic_kind",
        "severity",
        "message",
    }
