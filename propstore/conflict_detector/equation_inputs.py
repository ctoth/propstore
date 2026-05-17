from __future__ import annotations

from eq_equiv import BoundEquation, EquationSymbolBinding

from .models import ConflictClaim


def bound_equation_from_conflict_claim(claim: ConflictClaim) -> BoundEquation:
    return BoundEquation(
        expression=claim.expression,
        sympy=claim.sympy,
        variables=tuple(
            EquationSymbolBinding(
                symbol=variable.symbol,
                concept_id=variable.concept_id,
                role=variable.role,
            )
            for variable in claim.variables
            if variable.symbol
        ),
    )
