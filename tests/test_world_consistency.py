"""Phase 7a-world-C3: world-consistency owner API over a ``WorldStore``."""

from __future__ import annotations

from propstore.world.consistency import (
    WorldConsistencyRequest,
    check_world_consistency,
)

from tests.atms_feed import ClaimSpec, ConflictSpec, build_bound


def test_consistency_reports_direct_conflicts() -> None:
    store = build_bound(
        claims=(
            ClaimSpec(claim_id="a1", concept_id="A", value=2.0),
            ClaimSpec(claim_id="a2", concept_id="A", value=9.0),
        ),
        conflicts=(ConflictSpec(concept_id="A", claim_a_id="a1", claim_b_id="a2"),),
    ).store
    report = check_world_consistency(store, WorldConsistencyRequest(bindings={}))
    assert report.transitive is False
    pairs = {(line.claim_a_id, line.claim_b_id) for line in report.conflicts}
    assert ("a1", "a2") in pairs


def test_consistency_report_is_json_ready() -> None:
    store = build_bound(
        claims=(
            ClaimSpec(claim_id="a1", concept_id="A", value=2.0),
            ClaimSpec(claim_id="a2", concept_id="A", value=9.0),
        ),
        conflicts=(ConflictSpec(concept_id="A", claim_a_id="a1", claim_b_id="a2"),),
    ).store
    report = check_world_consistency(store, WorldConsistencyRequest(bindings={}))
    payload = report.to_json()
    assert payload["transitive"] is False
    assert isinstance(payload["conflicts"], list)


def test_consistency_clean_store_has_no_conflicts() -> None:
    store = build_bound(
        claims=(ClaimSpec(claim_id="a", concept_id="A", value=2.0),),
    ).store
    report = check_world_consistency(store, WorldConsistencyRequest(bindings={}))
    assert report.conflicts == ()
