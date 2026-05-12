"""Diagnostics for dimensionless invariants backed by Bridgman."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from bridgman import (
    Dimensions as BridgmanDimensions,
    PiError,
    count_pi_groups,
    is_dimensionless_product,
)


Dimensions = Mapping[str, int]


@dataclass(frozen=True)
class PiDiagnostic:
    ok: bool
    value: bool | int | None
    error: str | None = None


def _bridgman_quantities(
    quantities: Mapping[str, Dimensions],
) -> dict[str, BridgmanDimensions]:
    return {name: dict(dimensions) for name, dimensions in quantities.items()}


def count_dimensionless_groups(
    quantities: Mapping[str, Dimensions],
) -> PiDiagnostic:
    """Return a Propstore diagnostic for the Buckingham Pi group count."""
    try:
        return PiDiagnostic(
            ok=True,
            value=count_pi_groups(_bridgman_quantities(quantities)),
        )
    except (PiError, TypeError, ValueError) as exc:
        return PiDiagnostic(ok=False, value=None, error=str(exc))


def check_dimensionless_product(
    quantities: Mapping[str, Dimensions],
    exponents: Mapping[str, int],
) -> PiDiagnostic:
    """Return a Propstore diagnostic for an authored dimensionless product."""
    try:
        return PiDiagnostic(
            ok=True,
            value=is_dimensionless_product(
                _bridgman_quantities(quantities),
                exponents,
            ),
        )
    except (PiError, TypeError, ValueError) as exc:
        return PiDiagnostic(ok=False, value=None, error=str(exc))


__all__ = [
    "PiDiagnostic",
    "check_dimensionless_product",
    "count_dimensionless_groups",
]
