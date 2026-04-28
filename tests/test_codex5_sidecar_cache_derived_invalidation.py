from __future__ import annotations

from propstore.sidecar import build as build_module


def test_sidecar_cache_key_document_contains_derived_inputs() -> None:
    key_inputs = build_module._sidecar_cache_key_inputs("rev-a")

    assert key_inputs["source_revision"] == "rev-a"
    assert isinstance(key_inputs["sidecar_schema_version"], int)
    assert key_inputs["generated_schema_version"]
    assert {
        "family": "claims",
        "name": "claim.compile",
        "input_stage": "authored",
        "output_stage": "checked",
        "version": "1",
    } in key_inputs["passes"]
    assert "claims_file" in key_inputs["family_contract_versions"]
    assert "concepts" in key_inputs["family_contract_versions"]
    assert "quire" in key_inputs["dependency_pins"]
    assert "build_time_config" in key_inputs


def test_sidecar_content_hash_changes_on_manual_cache_bust(monkeypatch) -> None:
    first = build_module._sidecar_content_hash("rev-a")

    monkeypatch.setenv("PROPSTORE_SIDECAR_CACHE_BUST", "force-2026-04-28")

    assert build_module._sidecar_content_hash("rev-a") != first
