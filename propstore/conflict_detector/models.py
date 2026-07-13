"""Shared conflict detector models.

A :class:`ConflictClaim` is the field-subset VIEW of the one canonical
:class:`~propstore.families.claims.Claim` charter document that the detectors
compare (the view the claim charter's docstring promises).
:meth:`ConflictClaim.from_claim` is attribute access plus the single
package-owned lowering at the boundary — authored CEL condition strings become
condition-ir ``CelExpr`` via ``to_cel_exprs``. There is no payload dict, no
``from_payload``, and no second spelling of the claim or its variable bindings.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum

from condition_ir import CelExpr, to_cel_expr, to_cel_exprs

from propstore.families.claims import Claim, ClaimType, ClaimVariable


@dataclass(frozen=True)
class ConflictClaim:
    claim_id: str
    claim_type: ClaimType | None = None
    output_concept_id: str | None = None
    target_concept_id: str | None = None
    measure: str | None = None
    value: float | None = None
    lower_bound: float | int | None = None
    upper_bound: float | int | None = None
    unit: str | None = None
    expression: str | None = None
    sympy: str | None = None
    body: str | None = None
    source_paper: str | None = None
    context_id: str | None = None
    conditions: tuple[CelExpr, ...] = field(default_factory=tuple)
    variables: tuple[ClaimVariable, ...] = ()

    @classmethod
    def from_claim(
        cls, claim: Claim, *, source_paper: str | None = None
    ) -> ConflictClaim:
        """The detector view of *claim*.

        ``source_paper`` is supplied by the caller because the charter is
        provenance-free: the sidecar build derives it from the micropublication
        bundling the claim; the merge boundary carries it on ``MergeClaim``.
        """

        return cls(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            output_concept_id=claim.output_concept,
            target_concept_id=claim.target_concept,
            measure=claim.measure,
            value=claim.value,
            lower_bound=claim.lower_bound,
            upper_bound=claim.upper_bound,
            unit=claim.unit,
            expression=claim.expression,
            sympy=claim.sympy,
            body=claim.body,
            source_paper=source_paper,
            context_id=claim.context_id,
            conditions=to_cel_exprs(claim.conditions),
            variables=claim.variables,
        )

    def with_source_condition(self) -> ConflictClaim:
        if not self.source_paper:
            return self
        source_condition = to_cel_expr(f"source == '{self.source_paper}'")
        if source_condition in self.conditions:
            return self
        return replace(self, conditions=(*self.conditions, source_condition))


class ConflictClass(Enum):
    COMPATIBLE = "COMPATIBLE"
    UNKNOWN = "UNKNOWN"
    PHI_NODE = "PHI_NODE"
    CONFLICT = "CONFLICT"
    OVERLAP = "OVERLAP"
    PARAM_CONFLICT = "PARAM_CONFLICT"
    CONTEXT_PHI_NODE = "CONTEXT_PHI_NODE"


def coerce_conflict_class(value: object | None) -> ConflictClass | None:
    if value is None:
        return None
    if isinstance(value, ConflictClass):
        return value
    raw_value = str(value)
    try:
        return ConflictClass(raw_value)
    except ValueError:
        return ConflictClass(raw_value.upper())


@dataclass
class ConflictRecord:
    concept_id: str
    claim_a_id: str
    claim_b_id: str
    warning_class: ConflictClass
    conditions_a: list[CelExpr]
    conditions_b: list[CelExpr]
    value_a: str
    value_b: str
    derivation_chain: str | None = None
