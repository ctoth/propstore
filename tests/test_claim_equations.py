"""Phase 3 equation comparison for claims: propstore COMPOSES eq-equiv.

Ports the reference equation-conflict-status contract (equivalent orientations
agree, a proven difference differs, an undecidable pair stays unknown) onto the
direct eq-equiv consumption surface. propstore does not parse or compare
equations itself.
"""

from __future__ import annotations

from eq_equiv import EquationComparisonStatus, EquationSymbolBinding

from propstore.claim_equations import compare_claim_equations


def _bindings(*symbols: str) -> tuple[EquationSymbolBinding, ...]:
    return tuple(EquationSymbolBinding(symbol=s, concept_id=f"concept_{s}") for s in symbols)


def test_equivalent_orientations_agree() -> None:
    comparison = compare_claim_equations("y = x + z", "x + z = y", _bindings("x", "y", "z"))
    assert comparison.status is EquationComparisonStatus.EQUIVALENT


def test_proven_difference_is_different() -> None:
    comparison = compare_claim_equations("y = x + z", "y = 2*x + z", _bindings("x", "y", "z"))
    assert comparison.status is EquationComparisonStatus.DIFFERENT


def test_undecidable_pair_stays_unknown() -> None:
    comparison = compare_claim_equations(
        "q = log(x*z)", "q = log(x) + log(z)", _bindings("x", "z", "q")
    )
    assert comparison.status is EquationComparisonStatus.UNKNOWN
