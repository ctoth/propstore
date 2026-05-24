from __future__ import annotations

from propstore.compiler import workflows as build_module
from propstore.repository import Repository


def test_sidecar_cache_key_document_contains_derived_inputs() -> None:
    key_inputs = {
        "source_revision": "rev-a",
        "sidecar_schema_version": build_module.PROPSTORE_WORLD_SCHEMA_VERSION,
        "generated_schema_version": build_module.world_sqlalchemy_schema().catalog_hash,
        "passes": build_module._semantic_pass_versions(),
        "family_contract_versions": build_module._family_contract_versions(),
        "dependency_pins": build_module.read_dependency_pins(
            build_module._repo_root() / "uv.lock",
            build_module._WORLD_STORE_CACHE_DEPENDENCIES,
        ),
        "build_time_config": {"PROPSTORE_SIDECAR_CACHE_BUST": ""},
    }

    assert key_inputs["source_revision"] == "rev-a"
    assert isinstance(key_inputs["sidecar_schema_version"], int)
    assert key_inputs["generated_schema_version"]
    assert {
        "family": "claims",
        "name": "claim.compile",
        "input_stage": "claim.authored",
        "output_stage": "claim.checked",
        "version": "1",
    } in key_inputs["passes"]
    assert "claim" in key_inputs["family_contract_versions"]
    assert "concepts" in key_inputs["family_contract_versions"]
    assert "quire" in key_inputs["dependency_pins"]
    assert "build_time_config" in key_inputs


def test_world_store_content_hash_changes_on_manual_cache_bust(tmp_path, monkeypatch) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    first = build_module._world_store_content_hash(repo, "rev-a")

    monkeypatch.setenv("PROPSTORE_SIDECAR_CACHE_BUST", "force-2026-04-28")

    assert build_module._world_store_content_hash(repo, "rev-a") != first
