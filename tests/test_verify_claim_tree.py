"""Canonical claim-tree integrity verification (:mod:`propstore.verify`).

verify_claim_tree is the post-hoc, non-raising counterpart of the commit-time
foreign-key gate. It walks the charter-derived foreign-key graph and reports
resolved / dangling / quarantined references over an arbitrary repository state.

The commit-time gate rejects a dangling reference outright, so to exercise the
auditor on a *broken* state these tests write through a registry-unbound
:class:`~quire.families.BoundFamily` — the same way an import, a merge, or a
historical commit can leave a reference unresolved. Verify's whole reason for
existing is to audit states the live gate would never have written.
"""

from __future__ import annotations

from pathlib import Path

from quire.families import BoundFamily

from propstore.families.claims import Claim, ClaimStatus
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.repository import Repository
from propstore.verify import ClaimTreeIntegrityReport, verify_claim_tree


def _raw_claim_family(repo: Repository) -> BoundFamily[object, str, Claim]:
    """A claim family with no registry definition — writes skip FK validation."""

    return BoundFamily(repo.families.store, Claim.__charter__.family.artifact_family)


def test_empty_repo_verifies_ok(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    report = verify_claim_tree(repo)
    assert isinstance(report, ClaimTreeIntegrityReport)
    assert report.ok
    assert report.dangling == ()
    assert report.quarantined == ()
    assert report.malformed_identity == ()


def test_clean_claim_tree_verifies_ok(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    repo.families.concept.save(
        "concept:mass", Concept(concept_id="concept:mass", canonical_name="mass"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="C"), message="m"
    )
    repo.families.claim.save(
        "cl:ok",
        Claim(
            claim_id="cl:ok",
            context_id="ctx1",
            output_concept="concept:mass",
            concepts=("concept:mass",),
        ),
        message="author claim",
    )

    report = verify_claim_tree(repo)

    assert report.ok
    assert report.dangling == ()
    assert report.quarantined == ()
    resolved_keys = {(r.foreign_key, r.source_id) for r in report.resolved}
    assert ("claim_context", "cl:ok") in resolved_keys
    assert ("claim_output_concept", "cl:ok") in resolved_keys
    assert ("claim_concepts", "cl:ok") in resolved_keys
    # The resolution carries the canonical target id, not a re-spelling of it.
    output = next(r for r in report.resolved if r.foreign_key == "claim_output_concept")
    assert output.target_family == "concept"
    assert output.resolved_ids == ("concept:mass",)


def test_dangling_reference_is_reported(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    # An authored claim whose concept reference points at a concept that is not
    # present. The live commit gate would reject this; we write it raw to model
    # the broken state verify exists to surface.
    _raw_claim_family(repo).save(
        "cl:dangling",
        Claim(claim_id="cl:dangling", output_concept="concept:ghost"),
        message="raw dangling claim",
    )

    report = verify_claim_tree(repo)

    assert not report.ok
    assert len(report.dangling) == 1
    failure = report.dangling[0]
    assert failure.foreign_key == "claim_output_concept"
    assert failure.source_id == "cl:dangling"
    assert failure.target_family == "concept"
    assert failure.resolved_ids == ()
    assert failure.detail is not None
    # Non-commitment: verify reports, it does not drop. The broken row is still
    # present in storage after verification.
    assert repo.families.claim.load("cl:dangling") is not None


def test_quarantined_record_is_not_a_hard_failure(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    # A BLOCKED (quarantined) claim with the same unresolved reference. Quarantine
    # is a valid present-but-filtered state, so the unresolved reference must be
    # reported as quarantined, NOT counted as a dangling hard failure.
    _raw_claim_family(repo).save(
        "cl:blocked",
        Claim(
            claim_id="cl:blocked",
            status=ClaimStatus.BLOCKED,
            output_concept="concept:ghost",
        ),
        message="raw blocked claim",
    )

    report = verify_claim_tree(repo)

    assert report.dangling == ()
    assert report.ok
    assert len(report.quarantined) == 1
    record = report.quarantined[0]
    assert record.family == "claim"
    assert record.artifact_id == "cl:blocked"
    assert record.status == "blocked"
    assert len(record.unresolved) == 1
    assert record.unresolved[0].foreign_key == "claim_output_concept"


def test_authored_and_quarantined_refs_are_bucketed_separately(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    raw = _raw_claim_family(repo)
    raw.save(
        "cl:dangling",
        Claim(claim_id="cl:dangling", output_concept="concept:ghost"),
        message="raw dangling claim",
    )
    raw.save(
        "cl:blocked",
        Claim(
            claim_id="cl:blocked",
            status=ClaimStatus.BLOCKED,
            output_concept="concept:ghost",
        ),
        message="raw blocked claim",
    )

    report = verify_claim_tree(repo)

    assert {f.source_id for f in report.dangling} == {"cl:dangling"}
    assert {q.artifact_id for q in report.quarantined} == {"cl:blocked"}
    assert not report.ok  # the authored dangling ref still fails the tree


def test_verify_is_read_only(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _raw_claim_family(repo).save(
        "cl:dangling",
        Claim(claim_id="cl:dangling", output_concept="concept:ghost"),
        message="raw dangling claim",
    )
    git = repo.require_git()
    before = git.branch_sha("master")

    verify_claim_tree(repo)

    assert git.branch_sha("master") == before
