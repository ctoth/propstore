"""Tests for typed failure-reason propagation in ActiveClaimResolver.

Covers the propagation of `ast_compare` parse failures via
`ValueResult.reason = ValueResultReason.ALGORITHM_UNPARSEABLE`, while ensuring
benign "cannot decide" cases (empty body, missing bindings, non-constant
direct value, incomplete known values) do NOT get tagged with the
unparseable reason.
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
            else (lambda ids: {"input": 5.0})
        ),
        extract_bindings=(
            extract_bindings
            if extract_bindings is not None
            else (lambda claim: {"x": "input"})
        ),
    )


# ---------------------------------------------------------------------------
# Group 1: mixed direct + algorithm branch (_algorithm_matches_direct_value)
# ---------------------------------------------------------------------------


def test_unparseable_algorithm_records_failure_reason():
    """Parse failure in _algorithm_matches_direct_value must tag reason."""
    resolver = _make_resolver()
    active = [
        {"id": "direct", "type": "parameter", "value": 10.0},
        {
            "id": "algo",
            "type": "algorithm",
            # Deliberately broken python — def signature not closed.
            "body": "def compute(x:\n    return x +",
            "variables_json": '[{"name":"x","concept":"input"}]',
        },
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.CONFLICTED
    assert result.reason is ValueResultReason.ALGORITHM_UNPARSEABLE


def test_benign_inconclusive_algorithm_has_no_reason_annotation():
    """Non-constant direct value makes the helper return None for a BENIGN
    reason (not a parse failure). The reason annotation must not leak."""
    resolver = _make_resolver()
    active = [
        # Two disagreeing direct values — len(direct_values) != 1.
        # This hits the CONFLICTED branch at line 182 (before any algorithm
        # comparison), so the helper is never called and no reason should
        # be attached.
        {"id": "direct1", "type": "parameter", "value": 10.0},
        {"id": "direct2", "type": "parameter", "value": 20.0},
        {
            "id": "algo",
            "type": "algorithm",
            "body": "def compute(x):\n    return x * 2\n",
            "variables_json": '[{"name":"x","concept":"input"}]',
        },
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.CONFLICTED
    assert result.reason is None


def test_benign_missing_bindings_has_no_reason_annotation():
    """Algorithm helper returns None because bindings are empty (line 415).
    Not a parse failure — must not be tagged ALGORITHM_UNPARSEABLE."""
    resolver = _make_resolver(
        extract_bindings=lambda claim: {},  # no bindings → helper returns None
    )
    active = [
        {"id": "direct", "type": "parameter", "value": 10.0},
        {
            "id": "algo",
            "type": "algorithm",
            "body": "def compute(x):\n    return x * 2\n",
            "variables_json": '[{"name":"x","concept":"input"}]',
        },
    ]

    result = resolver.value_of_from_active(active, "target")

    # Unevaluable algorithm present → CONFLICTED (line 197) but benign —
    # no parse failure, so reason must stay None.
    assert result.status is ValueStatus.CONFLICTED
    assert result.reason is None


def test_successful_comparison_has_no_reason_annotation():
    """Happy path: algorithm evaluates and matches direct value → DETERMINED,
    reason stays None."""
    resolver = _make_resolver()
    # direct value 10 with known_values x=5, algorithm compute(x): return x*2
    # ⇒ 10 == 10. Should land as DETERMINED.
    active = [
        {"id": "direct", "type": "parameter", "value": 10.0},
        {
            "id": "algo",
            "type": "algorithm",
            "body": "def compute(x):\n    return x * 2\n",
            "variables_json": '[{"name":"x","concept":"input"}]',
        },
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.DETERMINED
    assert result.reason is None


# ---------------------------------------------------------------------------
# Group 2: algorithm-only branch (_all_algorithms_equivalent)
# ---------------------------------------------------------------------------


def test_unparseable_algorithm_only_records_failure_reason():
    """Parse failure in _all_algorithms_equivalent must tag reason."""
    resolver = _make_resolver()
    active = [
        {
            "id": "algo_ok",
            "type": "algorithm",
            "body": "def compute(x):\n    return x * 2\n",
            "variables_json": '[{"name":"x","concept":"input"}]',
        },
        {
            "id": "algo_broken",
            "type": "algorithm",
            # Deliberately broken body.
            "body": "def compute(x:\n    return x +",
            "variables_json": '[{"name":"x","concept":"input"}]',
        },
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.CONFLICTED
    assert result.reason is ValueResultReason.ALGORITHM_UNPARSEABLE


def test_successful_algorithm_only_has_no_reason_annotation():
    """Happy path: two equivalent algorithms → DETERMINED, reason is None."""
    resolver = _make_resolver()
    active = [
        {
            "id": "algo_a",
            "type": "algorithm",
            "body": "def compute(x):\n    return x * 2\n",
            "variables_json": '[{"name":"x","concept":"input"}]',
        },
        {
            "id": "algo_b",
            "type": "algorithm",
            "body": "def compute(x):\n    return x * 2\n",
            "variables_json": '[{"name":"x","concept":"input"}]',
        },
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.DETERMINED
    assert result.reason is None
