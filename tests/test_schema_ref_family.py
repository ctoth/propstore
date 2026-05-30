"""Phase 1 gates for the ref-backed contract schema family.

The contract schema is materialized from Python into a git blob-ref
(``refs/propstore/schema``) at repository birth, loaded as a real family
(``repo.families.schema``), and is *not* a semantic family (so the sidecar
build sweep never touches it). These tests pin those properties plus the dev
compatibility guard.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
from click.testing import CliRunner
from quire.contracts import (
    ContractManifest,
    ContractManifestError,
    check_contract_manifest,
)
from quire.versions import VersionId

from propstore.cli import cli
from propstore.contracts import build_propstore_contract_manifest
from propstore.families.registry import (
    PROPSTORE_FAMILY_REGISTRY,
    PROPSTORE_SCHEMA_REF,
    SchemaRef,
    semantic_families,
)
from propstore.repository import Repository


def test_pks_init_writes_parseable_schema_ref(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["-C", str(tmp_path), "init", "knowledge"])
    assert result.exit_code == 0, result.output

    repo = Repository.find(tmp_path / "knowledge")
    raw = repo.require_git().read_blob_ref(PROPSTORE_SCHEMA_REF)
    assert raw is not None
    parsed = ContractManifest.from_yaml(raw)
    assert parsed == build_propstore_contract_manifest()


def test_repository_init_materializes_schema_ref(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    assert repo.read_schema_ref() == build_propstore_contract_manifest()


def test_schema_family_is_not_semantic() -> None:
    assert "schema" not in {family.name for family in semantic_families()}
    schema = PROPSTORE_FAMILY_REGISTRY.by_name("schema")
    assert schema.metadata_value("semantic") is not True


def test_schema_family_excluded_from_sidecar_build_sweep() -> None:
    # The sidecar build enumerates semantic families only; assert the schema
    # family is absent from that set rather than relying on a special case.
    semantic_names = {family.name for family in semantic_families()}
    assert "schema" not in semantic_names


def test_check_schema_compatibility_passes_for_fresh_repo(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    # The materialized ref equals a fresh build, so the oracle is satisfied.
    repo.check_schema_compatibility()


def _document_schema_index(manifest: ContractManifest) -> int:
    for index, entry in enumerate(manifest.contracts):
        if entry.kind == "document_schema":
            return index
    raise AssertionError("no document_schema entry in manifest")


def test_dev_guard_fires_on_charter_change_without_version_bump() -> None:
    previous = build_propstore_contract_manifest()
    index = _document_schema_index(previous)
    entries = list(previous.contracts)
    old = entries[index]
    altered_fields = list(old.body["fields"]) + [
        {"name": "_probe", "type": "builtins.str", "required": False}
    ]
    new_body = {**old.body, "fields": altered_fields}
    entries[index] = dataclasses.replace(old, body=new_body)
    current = dataclasses.replace(previous, contracts=tuple(entries))

    with pytest.raises(ContractManifestError):
        check_contract_manifest(previous, current)


def test_dev_guard_passes_on_charter_change_with_version_bump() -> None:
    previous = build_propstore_contract_manifest()
    index = _document_schema_index(previous)
    entries = list(previous.contracts)
    old = entries[index]
    altered_fields = list(old.body["fields"]) + [
        {"name": "_probe", "type": "builtins.str", "required": False}
    ]
    new_body = {**old.body, "fields": altered_fields}
    entries[index] = dataclasses.replace(
        old,
        body=new_body,
        contract_version=VersionId("2099.01.01"),
    )
    current = dataclasses.replace(previous, contracts=tuple(entries))

    # A body change accompanied by a version bump is accepted.
    check_contract_manifest(previous, current)


def test_schema_ref_loads_cold_without_a_branch(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    # Branchless cold load: the ref-backed family reads the loose blob with no
    # branch/commit pin, returning the materialized manifest.
    loaded = repo.families.schema.load(SchemaRef())
    assert loaded == build_propstore_contract_manifest()
