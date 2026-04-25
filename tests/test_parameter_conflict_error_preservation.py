"""Ensure parameter-conflict detection preserves underlying error text.

When ``detect_parameter_conflicts`` catches a ``Z3TranslationError`` or
``z3.Z3Exception`` from the solver, the resulting top-level
``RuntimeError`` must include the underlying message verbatim —
otherwise tooling that prints only ``str(exc)`` sees the bland
``"Z3 partitioning failed ..."`` header and loses the actual cause
(e.g. a CEL type-check rejection naming the offending concept).

Covers both wrap sites:
  * ``detect_parameter_conflicts`` → partition step (``parameter_claims.py:55``).
  * ``detect_parameter_conflicts`` → cross-class disjointness step
    (``parameter_claims.py:211``).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from propstore.conflict_detector.models import ConflictClaim
from propstore.conflict_detector.parameter_claims import detect_parameter_conflicts
from propstore.z3_conditions import Z3TranslationError


def _three_parameter_claims_on_concept() -> tuple[ConflictClaim, ...]:
    """Minimum shape that triggers ``partition_equivalence_classes``."""
    return tuple(
        ConflictClaim(
            claim_id=f"c{i}",
            claim_type="parameter",
            output_concept_id="outcome",
            value=float(i),
            unit="",
            conditions=("intention_to_treat == true",),
        )
        for i in range(3)
    )


def test_partitioning_runtime_error_includes_underlying_cause_text() -> None:
    stub = MagicMock()
    underlying = "Structural concept 'intention_to_treat' cannot appear in CEL expressions"
    stub.partition_equivalence_classes.side_effect = Z3TranslationError(underlying)

    with pytest.raises(RuntimeError) as info:
        detect_parameter_conflicts(
            _three_parameter_claims_on_concept(),
            cel_registry={},
            solver=stub,
        )

    top_message = str(info.value)
    assert "Z3 partitioning failed" in top_message
    assert underlying in top_message


def test_disjointness_runtime_error_includes_underlying_cause_text() -> None:
    """The cross-class disjointness wrap at parameter_claims.py:211 must
    also surface the underlying cause text."""
    # Three claims across two equivalence classes so the cross-class
    # disjointness check runs. We control what ``are_disjoint_result``
    # raises — partitioning itself succeeds here.
    stub = MagicMock()
    stub.partition_equivalence_classes.return_value = [[0], [1, 2]]
    underlying = "Structural concept 'intention_to_treat' cannot appear in CEL expressions"
    stub.are_disjoint_result.side_effect = Z3TranslationError(underlying)

    with pytest.raises(RuntimeError) as info:
        detect_parameter_conflicts(
            _three_parameter_claims_on_concept(),
            cel_registry={},
            solver=stub,
        )

    top_message = str(info.value)
    assert "Z3 disjointness check failed" in top_message
    assert underlying in top_message
