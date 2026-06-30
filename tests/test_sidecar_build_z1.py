"""Z1 standing gate (PLAN.md §12.1): a build quarantines, it never aborts or drops.

The schema mechanism (advisory foreign keys) is pinned in
``test_sidecar_quarantine_z1``. This is the *build-level* gate: a full
``build_repository`` over a corpus carrying a blocked claim or a dangling
stance / justification / micropublication reference must PROCEED, project the
offending rows, and record a blocking ``build_diagnostic`` for each — never raise,
never abort, never drop.

The canonical family store enforces foreign keys on write, so a dangling reference
cannot be *authored* there; it only arises from a non-validating committed snapshot
(an import). Such writes are simulated here through the lower document store, the
way a repo-to-repo import (9-4) would land them.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


from propstore.compiler.workflows import build_repository
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.justifications import Justification
from propstore.families.micropublications import Micropublication
from propstore.families.relations import Stance
from propstore.repository import Repository
from propstore.stances import StanceType


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


def _diagnostics(path: str) -> list[tuple[str, str, int, str | None, str | None]]:
    conn = sqlite3.connect(path)
    try:
        return [
            (str(row[0]), str(row[1]), int(row[2]), row[3], row[4])
            for row in conn.execute(
                "SELECT source_kind, diagnostic_kind, blocking, source_ref, claim_id "
                "FROM build_diagnostic"
            ).fetchall()
        ]
    finally:
        conn.close()


def _rows(path: str, query: str) -> list[tuple[object, ...]]:
    conn = sqlite3.connect(path)
    try:
        return [tuple(row) for row in conn.execute(query).fetchall()]
    finally:
        conn.close()


def test_blocked_claim_quarantines_and_build_proceeds(tmp_path: Path) -> None:
    repo = _base_repo(tmp_path)
    # An unparseable CEL condition blocks the claim semantically.
    repo.families.claim.save(
        "bad",
        Claim(
            claim_id="bad",
            context_id="ctx1",
            claim_type=ClaimType.OBSERVATION,
            statement="bad",
            conditions=("totally bogus !! cel",),
        ),
        message="m",
    )
    report = build_repository(repo)  # must not raise
    assert report.sidecar_missing is False
    assert report.derived_store is not None
    path = report.derived_store.path
    # Quarantine, not drop: the blocked claim is still a row.
    assert ("bad",) in _rows(path, "SELECT claim_id FROM claim")
    blocking = [d for d in _diagnostics(path) if d[2] == 1 and d[4] == "bad"]
    assert blocking, "expected a blocking diagnostic for the blocked claim"


def test_dangling_stance_reference_quarantines(tmp_path: Path) -> None:
    repo = _base_repo(tmp_path)
    _save_unvalidated(
        repo,
        Stance(
            stance_id="sbad",
            source_claim_id="cl1",
            target_claim_id="GONE",
            stance_type=StanceType.REBUTS,
            confidence=0.5,
        ),
        "sbad",
    )
    report = build_repository(repo)  # must not raise
    path = report.derived_store.path if report.derived_store else ""
    # quarantine-then-insert: the dangling stance still lands as a row.
    assert ("sbad", "GONE") in _rows(
        path, "SELECT stance_id, target_claim_id FROM stance"
    )
    diags = _diagnostics(path)
    assert any(d[1] == "stance_validation" and d[2] == 1 for d in diags)


def test_dangling_justification_reference_quarantines(tmp_path: Path) -> None:
    repo = _base_repo(tmp_path)
    _save_unvalidated(
        repo,
        Justification(justification_id="jbad", conclusion="GONE", premises=("cl1",)),
        "jbad",
    )
    report = build_repository(repo)
    path = report.derived_store.path if report.derived_store else ""
    assert ("jbad",) in _rows(path, "SELECT justification_id FROM justification")
    diags = _diagnostics(path)
    assert any(d[1] == "justification_validation" and d[2] == 1 for d in diags)


def test_dangling_micropublication_reference_quarantines(tmp_path: Path) -> None:
    repo = _base_repo(tmp_path)
    _save_unvalidated(
        repo,
        Micropublication(artifact_id="mbad", context_id="ctx1", claims=("GONE",)),
        "mbad",
    )
    report = build_repository(repo)
    path = report.derived_store.path if report.derived_store else ""
    assert ("mbad",) in _rows(path, "SELECT artifact_id FROM micropublication")
    diags = _diagnostics(path)
    assert any(d[1] == "micropublication_validation" and d[2] == 1 for d in diags)
