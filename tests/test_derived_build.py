"""World-sidecar materialize: content-hash cache key, rebuild-on-change, projection.

These pin the 9-0-rest-B build spine:

* ``materialize_world_sidecar`` returns ``built=True`` on the first build and
  ``built=False`` on an unchanged rebuild — quire owns rebuild-on-change, propstore
  only supplies the content hash (``TestRebuildSkipping`` analog);
* the content hash is sensitive to the source revision and the
  ``PROPSTORE_SIDECAR_CACHE_BUST`` knob (``test_codex5_sidecar_cache`` analog);
* ``_build_sidecar_file`` populates the charter-derived schema directly via
  ``session.add_family`` (the projection IS the charter).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from propstore.derived_build import (
    materialize_world_sidecar,
    world_sidecar_hash,
    world_sidecar_hash_inputs,
)
from propstore.derived_schema import build_world_sidecar_schema
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.repository import Repository


def _repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "cl1",
        Claim(
            claim_id="cl1",
            context_id="ctx1",
            claim_type=ClaimType.OBSERVATION,
            statement="x",
        ),
        message="m",
    )
    return repo


def test_first_build_builds_then_unchanged_rebuild_skips(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    handle, built = materialize_world_sidecar(repo)
    assert built is True
    assert Path(handle.path).is_file()

    handle2, built2 = materialize_world_sidecar(repo)
    assert built2 is False
    assert handle2.path == handle.path


def test_force_rebuilds_even_when_unchanged(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    materialize_world_sidecar(repo)
    _, built = materialize_world_sidecar(repo, force=True)
    assert built is True


def test_source_change_invalidates_cache_and_rebuilds(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    materialize_world_sidecar(repo)
    # A new authored claim moves the head sha, changing the content hash.
    repo.families.claim.save(
        "cl2",
        Claim(
            claim_id="cl2",
            context_id="ctx1",
            claim_type=ClaimType.OBSERVATION,
            statement="y",
        ),
        message="m",
    )
    _, built = materialize_world_sidecar(repo)
    assert built is True


def test_cache_bust_env_changes_content_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    schema = build_world_sidecar_schema()
    monkeypatch.delenv("PROPSTORE_SIDECAR_CACHE_BUST", raising=False)
    base = world_sidecar_hash("rev", schema_hash=schema.catalog_hash)
    monkeypatch.setenv("PROPSTORE_SIDECAR_CACHE_BUST", "bust")
    busted = world_sidecar_hash("rev", schema_hash=schema.catalog_hash)
    assert base != busted


def test_hash_inputs_carry_the_expected_keys() -> None:
    schema = build_world_sidecar_schema()
    inputs = world_sidecar_hash_inputs("rev", schema_hash=schema.catalog_hash)
    assert inputs["source_revision"] == "rev"
    assert inputs["schema_hash"] == schema.catalog_hash
    assert "passes" in inputs
    assert "family_contract_versions" in inputs
    assert "dependency_pins" in inputs
    assert "build_time_config" in inputs


def test_hash_changes_with_source_revision() -> None:
    schema = build_world_sidecar_schema()
    a = world_sidecar_hash("rev-a", schema_hash=schema.catalog_hash)
    b = world_sidecar_hash("rev-b", schema_hash=schema.catalog_hash)
    assert a != b


def test_build_projects_charter_families_into_sidecar(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    handle, _ = materialize_world_sidecar(repo)
    conn = sqlite3.connect(handle.path)
    try:
        assert conn.execute("SELECT concept_id FROM concept").fetchall() == [("c1",)]
        assert conn.execute("SELECT claim_id FROM claim").fetchall() == [("cl1",)]
        assert conn.execute("SELECT context_id FROM context").fetchall() == [("ctx1",)]
        # The raw grounded-fact table exists even with no rules authored.
        assert conn.execute("SELECT count(*) FROM grounded_fact").fetchone() == (0,)
    finally:
        conn.close()
