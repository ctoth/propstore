"""Phase 7a-world-C3: OverlayWorld graph-overlay semantics.

OverlayWorld adds/removes synthetic claims on top of a BoundWorld and lets the
ordinary parameterization + conflict machinery decide the overlaid world. These
exercise add / replace / remove / diff / conflict recomputation over the
in-memory charter feed. Overlay carries numeric claim values (the ``Claim``
charter's value column is numeric).
"""

from __future__ import annotations

from propstore.families.claims import ClaimType
from propstore.world.overlay import OverlayWorld
from propstore.world.types import SyntheticClaim, ValueStatus

from tests.atms_feed import ClaimSpec, ParamSpec, build_bound


def test_overlay_adds_synthetic_claim_for_new_concept() -> None:
    base = build_bound(claims=(ClaimSpec(claim_id="a", concept_id="A", value=2.0),))
    overlay = OverlayWorld(
        base,
        add=[
            SyntheticClaim(
                id="syn", concept_id="B", value=7.0, type=ClaimType.PARAMETER
            )
        ],
    )
    assert base.value_of("B").status is ValueStatus.NO_CLAIMS
    result = overlay.value_of("B")
    assert result.status is ValueStatus.DETERMINED
    assert result.claims[0].value == 7.0


def test_overlay_replaces_existing_claim_value() -> None:
    base = build_bound(claims=(ClaimSpec(claim_id="a", concept_id="A", value=2.0),))
    overlay = OverlayWorld(
        base,
        add=[
            SyntheticClaim(id="a", concept_id="A", value=9.0, type=ClaimType.PARAMETER)
        ],
    )
    assert overlay.value_of("A").claims[0].value == 9.0


def test_overlay_removes_claim() -> None:
    base = build_bound(claims=(ClaimSpec(claim_id="a", concept_id="A", value=2.0),))
    overlay = OverlayWorld(base, remove=["a"])
    assert base.value_of("A").status is ValueStatus.DETERMINED
    assert overlay.value_of("A").status is ValueStatus.NO_CLAIMS


def test_overlay_diff_reports_changed_concepts() -> None:
    base = build_bound(claims=(ClaimSpec(claim_id="a", concept_id="A", value=2.0),))
    overlay = OverlayWorld(
        base,
        add=[
            SyntheticClaim(id="a", concept_id="A", value=9.0, type=ClaimType.PARAMETER)
        ],
    )
    diff = overlay.diff()
    assert "A" in diff
    base_result, overlay_result = diff["A"]
    assert base_result.claims[0].value == 2.0
    assert overlay_result.claims[0].value == 9.0


def test_overlay_diff_empty_when_no_change() -> None:
    base = build_bound(claims=(ClaimSpec(claim_id="a", concept_id="A", value=2.0),))
    overlay = OverlayWorld(base, add=[])
    assert overlay.diff() == {}


def test_overlay_preserves_parameterization_derivation() -> None:
    base = build_bound(
        claims=(
            ClaimSpec(claim_id="a", concept_id="A", value=2.0),
            ClaimSpec(claim_id="b", concept_id="B", value=3.0),
        ),
        parameterizations=(ParamSpec(output="C", inputs=("A", "B"), sympy="A + B"),),
    )
    overlay = OverlayWorld(
        base,
        add=[
            SyntheticClaim(id="a", concept_id="A", value=10.0, type=ClaimType.PARAMETER)
        ],
    )
    derived = overlay.derived_value("C")
    assert derived.status is ValueStatus.DERIVED
    assert derived.value == 13.0


def test_overlay_recompute_conflicts_returns_records() -> None:
    base = build_bound(
        claims=(
            ClaimSpec(claim_id="a1", concept_id="A", value=2.0),
            ClaimSpec(claim_id="a2", concept_id="A", value=9.0),
        ),
    )
    overlay = OverlayWorld(base, add=[])
    pairs = {
        tuple(sorted((str(record.claim_a_id), str(record.claim_b_id))))
        for record in overlay.recompute_conflicts()
    }
    assert ("a1", "a2") in pairs
