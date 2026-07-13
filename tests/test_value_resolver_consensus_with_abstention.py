"""Tests for Commit 5: unparseable algorithms abstain on direct consensus.

When direct-value claims collapse to a single agreed value, an unparseable
algorithm claim must NOT flip the status to CONFLICTED. Instead, the
algorithm abstains — consensus stands, status is DETERMINED, and the
``ValueResultReason.ALGORITHM_UNPARSEABLE`` annotation rides along to
signal that a third party could not be checked.

Parseable algorithms that genuinely disagree with the consensus still flip
to CONFLICTED — genuine disagreement is still dissent, only abstention is
absorbed.
"""

from __future__ import annotations

from propstore.core.active_claims import ActiveClaim
from propstore.families.claims import ClaimType
from propstore.world.types import ValueResultReason, ValueStatus
from propstore.world.value_resolver import ActiveClaimResolver


def _param(claim_id: str, value: float) -> ActiveClaim:
    return ActiveClaim(claim_id=claim_id, claim_type=ClaimType.PARAMETER, value=value)


def _algo(claim_id: str, body: str) -> ActiveClaim:
    return ActiveClaim(claim_id=claim_id, claim_type=ClaimType.ALGORITHM, body=body)


def _is_algorithm_claim(claim: ActiveClaim) -> bool:
    return claim.claim_type is ClaimType.ALGORITHM


def _make_resolver(
    *,
    extract_variable_concepts=None,
    collect_known_values=None,
    extract_bindings=None,
) -> ActiveClaimResolver:
    return ActiveClaimResolver(
        parameterizations_for=lambda cid: [],
        is_param_compatible=lambda conds: True,
        value_of=lambda cid: None,
        extract_variable_concepts=(
            extract_variable_concepts
            if extract_variable_concepts is not None
            else (lambda claim: ["input"] if _is_algorithm_claim(claim) else [])
        ),
        collect_known_values=(
            collect_known_values
            if collect_known_values is not None
            # Known value chosen so `compute(x): return x * 2` evaluates to
            # 42.0 (matching the direct consensus in these tests).
            else (lambda ids: {"input": 21.0})
        ),
        extract_bindings=(
            extract_bindings
            if extract_bindings is not None
            else (lambda claim: {"x": "input"})
        ),
    )


# ---------------------------------------------------------------------------
# Commit 5 core behavior: abstention on consensus
# ---------------------------------------------------------------------------


def test_unparseable_algo_abstains_when_direct_consensus_exists():
    """Two agreeing direct-value claims + one unparseable algorithm →
    DETERMINED with ALGORITHM_UNPARSEABLE annotation (abstention, not
    dissent). The algorithm claim is still recorded in the result.
    """
    resolver = _make_resolver()
    active = [
        _param("direct_a", 42.0),
        _param("direct_b", 42.0),
        # Deliberately broken python — def signature not closed.
        _algo("algo_broken", "def compute(x:\n    return x +"),
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.DETERMINED
    assert result.reason is ValueResultReason.ALGORITHM_UNPARSEABLE
    # All three claims survive in the record — the algorithm is not dropped,
    # only absorbed as abstention.
    assert len(result.claims) == 3
    claim_ids = {str(claim.claim_id) for claim in result.claims}
    assert claim_ids == {"direct_a", "direct_b", "algo_broken"}


def test_parseable_disagreeing_algorithm_still_conflicts_with_direct_consensus():
    """Regression guard: a parseable algorithm that genuinely disagrees with
    the direct consensus must still flip to CONFLICTED. Only abstention is
    absorbed — genuine disagreement is preserved as dissent.
    """
    # A collect_known_values returning x=50 makes `compute(x): return x*2`
    # evaluate to 100, which disagrees with the direct consensus of 42.
    resolver = _make_resolver(collect_known_values=lambda ids: {"input": 50.0})
    active = [
        _param("direct_a", 42.0),
        _param("direct_b", 42.0),
        _algo("algo_disagree", "def compute(x):\n    return x * 2\n"),
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.CONFLICTED
    assert result.reason is None


def test_all_algorithms_unparseable_with_direct_consensus_returns_determined():
    """Two agreeing direct-value claims + two unparseable algorithm claims →
    DETERMINED with the ALGORITHM_UNPARSEABLE annotation. Consensus survives
    even when every algorithm abstains.
    """
    resolver = _make_resolver()
    active = [
        _param("direct_a", 42.0),
        _param("direct_b", 42.0),
        _algo("algo_broken_1", "def compute(x:\n    return x +"),
        _algo("algo_broken_2", "def compute(\n    !!!"),
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.DETERMINED
    assert result.reason is ValueResultReason.ALGORITHM_UNPARSEABLE


def test_mixed_agreeing_and_unparseable_algorithms_with_direct_consensus():
    """Two agreeing direct-value claims + one parseable-and-matching algorithm
    + one unparseable algorithm → DETERMINED with ALGORITHM_UNPARSEABLE
    annotation. The abstention annotation survives even when another
    algorithm successfully agrees.
    """
    # collect_known_values returns x=21 so `compute(x): return x*2` evaluates
    # to 42, matching the direct consensus.
    resolver = _make_resolver(collect_known_values=lambda ids: {"input": 21.0})
    active = [
        _param("direct_a", 42.0),
        _param("direct_b", 42.0),
        _algo("algo_agree", "def compute(x):\n    return x * 2\n"),
        _algo("algo_broken", "def compute(x:\n    return x +"),
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.DETERMINED
    assert result.reason is ValueResultReason.ALGORITHM_UNPARSEABLE
