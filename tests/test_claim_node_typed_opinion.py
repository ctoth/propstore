from propstore.core.graph_types import ClaimNode
from propstore.opinion import Opinion
from propstore.provenance import Provenance, ProvenanceStatus


def _opinion(
    b: float,
    d: float,
    u: float,
    a: float,
    operation: str = "test",
) -> Opinion:
    return Opinion(
        b,
        d,
        u,
        a,
        Provenance(
            status=ProvenanceStatus.STATED,
            witnesses=(),
            operations=(operation,),
        ),
    )


def test_claim_node_accepts_typed_opinion_with_provenance() -> None:
    claim = ClaimNode(
        claim_id="claim-a",
        claim_type="observation",
        opinion=_opinion(0.6, 0.1, 0.3, 0.5),
    )

    assert claim.opinion is not None
    assert claim.opinion.b == 0.6
    assert claim.opinion.provenance is not None
    assert claim.opinion.provenance.status == ProvenanceStatus.STATED


def test_source_prior_opinion_round_trips_through_claim_node_dict() -> None:
    claim = ClaimNode(
        claim_id="claim-a",
        claim_type="observation",
        source_prior_opinion=_opinion(0.2, 0.3, 0.5, 0.4, "source_prior"),
    )

    reloaded = ClaimNode.from_dict(claim.to_dict())

    assert reloaded.source_prior_opinion is not None
    assert reloaded.source_prior_opinion.b == 0.2
    assert reloaded.source_prior_opinion.d == 0.3
    assert reloaded.source_prior_opinion.u == 0.5
    assert reloaded.source_prior_opinion.a == 0.4
    assert reloaded.source_prior_opinion.provenance is not None
    assert reloaded.source_prior_opinion.provenance.status == ProvenanceStatus.STATED


def test_claim_node_defaults_to_no_typed_opinion() -> None:
    claim = ClaimNode(claim_id="claim-a", claim_type="observation")

    assert claim.opinion is None


def test_opinion_fields_do_not_participate_in_claim_node_equality() -> None:
    left = ClaimNode(
        claim_id="claim-a",
        claim_type="observation",
        opinion=_opinion(0.6, 0.1, 0.3, 0.5, "left"),
    )
    right = ClaimNode(
        claim_id="claim-a",
        claim_type="observation",
        opinion=_opinion(0.2, 0.3, 0.5, 0.4, "right"),
    )

    assert left == right
