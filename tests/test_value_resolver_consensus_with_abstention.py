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

from propstore.core.claim_types import ClaimType
from propstore.world.types import ValueResultReason, ValueStatus
from propstore.world.value_resolver import ActiveClaimResolver


def _is_algorithm_claim(claim) -> bool:
    """True if this claim is an ALGORITHM claim — handles both dict inputs
    (pre-coercion) and ActiveClaim instances (post-coercion)."""
    claim_type = getattr(claim, "claim_type", None)
    if claim_type is not None:
        return claim_type is ClaimType.ALGORITHM
    if isinstance(claim, dict):
        return claim.get("type") == "algorithm"
    return False


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
        {"id": "direct_a", "type": "parameter", "value": 42.0},
        {"id": "direct_b", "type": "parameter", "value": 42.0},
        {
            "id": "algo_broken",
            "type": "algorithm",
            # Deliberately broken python — def signature not closed.
            "body": "def compute(x:\n    return x +",
            "variables_json": '[{"name":"x","concept":"input"}]',
        },
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
        {"id": "direct_a", "type": "parameter", "value": 42.0},
        {"id": "direct_b", "type": "parameter", "value": 42.0},
        {
            "id": "algo_disagree",
            "type": "algorithm",
            "body": "def compute(x):\n    return x * 2\n",
            "variables_json": '[{"name":"x","concept":"input"}]',
        },
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
        {"id": "direct_a", "type": "parameter", "value": 42.0},
        {"id": "direct_b", "type": "parameter", "value": 42.0},
        {
            "id": "algo_broken_1",
            "type": "algorithm",
            "body": "def compute(x:\n    return x +",
            "variables_json": '[{"name":"x","concept":"input"}]',
        },
        {
            "id": "algo_broken_2",
            "type": "algorithm",
            "body": "def compute(\n    !!!",
            "variables_json": '[{"name":"x","concept":"input"}]',
        },
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
        {"id": "direct_a", "type": "parameter", "value": 42.0},
        {"id": "direct_b", "type": "parameter", "value": 42.0},
        {
            "id": "algo_agree",
            "type": "algorithm",
            "body": "def compute(x):\n    return x * 2\n",
            "variables_json": '[{"name":"x","concept":"input"}]',
        },
        {
            "id": "algo_broken",
            "type": "algorithm",
            "body": "def compute(x:\n    return x +",
            "variables_json": '[{"name":"x","concept":"input"}]',
        },
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.DETERMINED
    assert result.reason is ValueResultReason.ALGORITHM_UNPARSEABLE
