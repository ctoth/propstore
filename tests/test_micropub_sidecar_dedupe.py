"""WS-CM payload-identity dedupe in the charter-projection sidecar build.

Translated from the feature-peak ``test_micropub_identity_dedupe_shape`` /
``test_micropub_identity_consumes_wscm`` suites to the rewrite's charter
projection. In the reference tree a per-family ``populate_micropublications``
deduped pre-compiled rows; that mass folds into the one generic charter
projection, which dedupes first-writer-wins on the charter identity field.

A micropublication's ``artifact_id`` is the ``ni:`` content URI of its bundle
(:mod:`propstore.families.identity.micropubs`), so two micropub documents that
share an ``artifact_id`` carry definitionally identical content; deduping on it
collapses them to one sidecar row while distinct content is preserved.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from propstore.compiler.workflows import build_repository
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.micropublications import Micropublication
from propstore.repository import Repository


def _base_repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    repo.families.context.save("ctx1", Context(context_id="ctx1", name="ctx"), message="m")
    repo.families.claim.save(
        "cl1",
        Claim(claim_id="cl1", context_id="ctx1", claim_type=ClaimType.OBSERVATION, statement="x"),
        message="m",
    )
    return repo


def _save_unvalidated(repo: Repository, document: object, ref: str) -> None:
    """Write a document via the lower store, bypassing registry FK validation."""

    family = type(document).__charter__.family.artifact_family  # type: ignore[attr-defined]
    repo._family_store.save(family, ref, document, message="import")


def _rows(path: str, query: str) -> list[tuple[object, ...]]:
    conn = sqlite3.connect(path)
    try:
        return [tuple(row) for row in conn.execute(query).fetchall()]
    finally:
        conn.close()


def test_identical_payload_micropubs_dedupe_to_one_row(tmp_path: Path) -> None:
    repo = _base_repo(tmp_path)
    # Two micropub files carrying definitionally identical content: same
    # content-derived artifact_id, same bundle. (Authored under distinct refs the
    # way a repo-to-repo import might land them.)
    bundle = dict(artifact_id="ni:///sha-256;dup", context_id="ctx1", claims=("cl1",))
    _save_unvalidated(repo, Micropublication(**bundle), "m1")
    _save_unvalidated(repo, Micropublication(**bundle), "m2")
    # A distinct bundle (different content -> different id) must survive.
    _save_unvalidated(
        repo,
        Micropublication(artifact_id="ni:///sha-256;other", context_id="ctx1", claims=("cl1",)),
        "m3",
    )

    report = build_repository(repo)
    assert report.derived_store is not None
    path = report.derived_store.path

    artifact_ids = sorted(row[0] for row in _rows(path, "SELECT artifact_id FROM micropublication"))
    assert artifact_ids == ["ni:///sha-256;dup", "ni:///sha-256;other"]
