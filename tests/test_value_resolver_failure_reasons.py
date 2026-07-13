"""Tests for typed failure-reason propagation in ActiveClaimResolver.

Covers the propagation of `ast_compare` parse failures via
`ValueResult.reason = ValueResultReason.ALGORITHM_UNPARSEABLE`, while ensuring
benign "cannot decide" cases (empty body, missing bindings, non-constant
direct value, incomplete known values) do NOT get tagged with the
unparseable reason.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

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
    """Parse failure in _algorithm_matches_direct_value must tag reason.

    Commit 5 update: when a direct-value consensus exists, an unparseable
    algorithm abstains — the status is now DETERMINED (consensus stands),
    and the ALGORITHM_UNPARSEABLE annotation survives as an abstention
    marker. Only parseable-disagreeing algorithms flip the status to
    CONFLICTED.
    """
    resolver = _make_resolver()
    active = [
        _param("direct", 10.0),
        # Deliberately broken python — def signature not closed.
        _algo("algo", "def compute(x:\n    return x +"),
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.DETERMINED
    assert result.reason is ValueResultReason.ALGORITHM_UNPARSEABLE


def test_benign_inconclusive_algorithm_has_no_reason_annotation():
    """Non-constant direct value makes the helper return None for a BENIGN
    reason (not a parse failure). The reason annotation must not leak."""
    resolver = _make_resolver()
    active = [
        # Two disagreeing direct values — len(direct_values) != 1.
        # This hits the CONFLICTED branch before any algorithm
        # comparison, so the helper is never called and no reason should
        # be attached.
        _param("direct1", 10.0),
        _param("direct2", 20.0),
        _algo("algo", "def compute(x):\n    return x * 2\n"),
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.CONFLICTED
    assert result.reason is None


def test_benign_missing_bindings_has_no_reason_annotation():
    """Algorithm helper returns None because bindings are empty.
    Not a parse failure — must not be tagged ALGORITHM_UNPARSEABLE."""
    resolver = _make_resolver(
        extract_bindings=lambda claim: {},  # no bindings → helper returns None
    )
    active = [
        _param("direct", 10.0),
        _algo("algo", "def compute(x):\n    return x * 2\n"),
    ]

    result = resolver.value_of_from_active(active, "target")

    # Unevaluable algorithm present → CONFLICTED but benign —
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
        _param("direct", 10.0),
        _algo("algo", "def compute(x):\n    return x * 2\n"),
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
        _algo("algo_ok", "def compute(x):\n    return x * 2\n"),
        # Deliberately broken body.
        _algo("algo_broken", "def compute(x:\n    return x +"),
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.CONFLICTED
    assert result.reason is ValueResultReason.ALGORITHM_UNPARSEABLE


def test_successful_algorithm_only_has_no_reason_annotation():
    """Happy path: two equivalent algorithms → DETERMINED, reason is None."""
    resolver = _make_resolver()
    active = [
        _algo("algo_a", "def compute(x):\n    return x * 2\n"),
        _algo("algo_b", "def compute(x):\n    return x * 2\n"),
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.DETERMINED
    assert result.reason is None


def test_runtime_error_from_algorithm_equivalence_propagates():
    resolver = _make_resolver()
    algo_claims = [
        ActiveClaim(claim_id="c1", body="x = 1"),
        ActiveClaim(claim_id="c2", body="x = 2"),
    ]

    with patch(
        "propstore.world.value_resolver.ast_compare",
        side_effect=RuntimeError("boom"),
    ):
        with pytest.raises(RuntimeError, match="boom"):
            resolver._all_algorithms_equivalent(algo_claims, known_values={})


def test_ast_compare_none_equivalence_is_benign_inconclusive():
    resolver = _make_resolver()
    claim = _algo("algo", "def compute(x):\n    return x * 2\n")

    class _Comparison:
        equivalent = None

    with patch(
        "propstore.world.value_resolver.ast_compare",
        return_value=_Comparison(),
    ):
        comparison = resolver._algorithm_matches_direct_value(claim, 10.0)

    assert comparison.equivalent is None
    assert comparison.parse_failed is False


def test_unparseable_override_value_raises():
    resolver = _make_resolver()

    with pytest.raises(ValueError, match="Invalid override value"):
        resolver._coerce_override_value({"input": "not-a-number"}, "input")
