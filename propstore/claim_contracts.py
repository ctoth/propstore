"""Claim-type contracts and the claim-validate workflow.

Each :class:`~propstore.families.claims.ClaimType` carries a declarative
*contract*: which fields it requires, which must be non-empty, how its scalar/
list concept references are role-linked, its value-group and unit policy, and the
semantic checks it must pass. This is propstore's own claim semantics — it is NOT
condition machinery and stays propstore-side.

The validate workflow is non-committal (PLAN.md §12, CLAUDE.md): it never raises
or drops a claim. It returns a report of diagnostics; the caller (a later build
pass) decides to quarantine, never to abort. The sympy-generation semantic check
delegates to ``human-to-sympy`` directly (``generate_sympy_rhs_with_error``);
propstore re-implements no NL->sympy logic. Dimensional and algorithm checks are
declared here but executed by later phases (they consume ``bridgman`` /
``ast-equiv``); the report names them explicitly under ``deferred_checks`` rather
than skipping them silently (honest ignorance).
"""

from __future__ import annotations

from collections.abc import Sized
from dataclasses import dataclass
from enum import Enum

from human_to_sympy import generate_sympy_rhs_with_error

from propstore.families.claims import Claim, ClaimType


class ClaimConceptLinkRole(str, Enum):
    """The role a concept plays relative to a claim."""

    OUTPUT = "output"
    INPUT = "input"
    TARGET = "target"
    ABOUT = "about"


class ClaimConceptLinkSource(str, Enum):
    """How a concept-link declaration reads its concept ids off the claim."""

    SCALAR = "scalar"
    LIST = "list"
    BINDINGS = "bindings"


@dataclass(frozen=True)
class ClaimConceptLinkDeclaration:
    """A declared role-link from a claim field to one or more concepts."""

    field: str
    role: ClaimConceptLinkRole
    source: ClaimConceptLinkSource = ClaimConceptLinkSource.SCALAR
    target_family: str = "concept"


@dataclass(frozen=True)
class ClaimValueGroupDeclaration:
    """The value/bounds/uncertainty field group of a quantitative claim."""

    value_field: str = "value"
    lower_bound_field: str = "lower_bound"
    upper_bound_field: str = "upper_bound"
    uncertainty_field: str = "uncertainty"
    uncertainty_type_field: str = "uncertainty_type"


@dataclass(frozen=True)
class ClaimUnitPolicyDeclaration:
    """Whether a unit is required and how a dimensionless default is supplied."""

    required: bool = True
    dimensionless_default_unit: str | None = None
    form_concept_field: str | None = None


@dataclass(frozen=True)
class ClaimSemanticCheck:
    """Base marker for a per-type semantic check.

    Subclasses are field-less markers dispatched by :func:`validate_claim`.
    """


@dataclass(frozen=True)
class UnitFormCompatibilityCheck(ClaimSemanticCheck):
    """Check that a claim's unit is compatible with its concept's form."""


@dataclass(frozen=True)
class SympyGenerationCheck(ClaimSemanticCheck):
    """Check that a claim's expression generates a sympy RHS (human-to-sympy)."""


@dataclass(frozen=True)
class DimensionalConsistencyCheck(ClaimSemanticCheck):
    """Check that an equation is dimensionally consistent (bridgman, later phase)."""


@dataclass(frozen=True)
class AlgorithmParseCheck(ClaimSemanticCheck):
    """Check that an algorithm body parses (ast-equiv, later phase)."""


@dataclass(frozen=True)
class AlgorithmUnboundNamesCheck(ClaimSemanticCheck):
    """Check that an algorithm body has no unbound names (ast-equiv, later phase)."""


@dataclass(frozen=True)
class ClaimTypeContract:
    """The authoring contract a claim of one type must satisfy."""

    claim_type: ClaimType
    required_fields: tuple[str, ...] = ()
    nonempty_fields: tuple[str, ...] = ()
    concept_links: tuple[ClaimConceptLinkDeclaration, ...] = ()
    value_group: ClaimValueGroupDeclaration | None = None
    unit_policy: ClaimUnitPolicyDeclaration | None = None
    semantic_checks: tuple[ClaimSemanticCheck, ...] = ()


# The four narrative claim types share one contract shape.
_NARRATIVE_LINKS: tuple[ClaimConceptLinkDeclaration, ...] = (
    ClaimConceptLinkDeclaration(
        field="concepts", role=ClaimConceptLinkRole.ABOUT, source=ClaimConceptLinkSource.LIST
    ),
)
_NARRATIVE_NONEMPTY: tuple[str, ...] = ("statement",)


def _narrative_contract(claim_type: ClaimType) -> ClaimTypeContract:
    return ClaimTypeContract(
        claim_type=claim_type,
        nonempty_fields=_NARRATIVE_NONEMPTY,
        concept_links=_NARRATIVE_LINKS,
    )


CLAIM_TYPE_CONTRACTS: dict[ClaimType, ClaimTypeContract] = {
    ClaimType.PARAMETER: ClaimTypeContract(
        claim_type=ClaimType.PARAMETER,
        required_fields=("output_concept",),
        concept_links=(
            ClaimConceptLinkDeclaration(
                field="output_concept", role=ClaimConceptLinkRole.OUTPUT
            ),
        ),
        value_group=ClaimValueGroupDeclaration(),
        unit_policy=ClaimUnitPolicyDeclaration(
            required=True,
            dimensionless_default_unit="1",
            form_concept_field="output_concept",
        ),
        semantic_checks=(UnitFormCompatibilityCheck(),),
    ),
    ClaimType.EQUATION: ClaimTypeContract(
        claim_type=ClaimType.EQUATION,
        required_fields=("expression",),
        concept_links=(
            ClaimConceptLinkDeclaration(
                field="output_concept", role=ClaimConceptLinkRole.OUTPUT
            ),
        ),
        semantic_checks=(SympyGenerationCheck(), DimensionalConsistencyCheck()),
    ),
    ClaimType.OBSERVATION: _narrative_contract(ClaimType.OBSERVATION),
    ClaimType.MECHANISM: _narrative_contract(ClaimType.MECHANISM),
    ClaimType.COMPARISON: _narrative_contract(ClaimType.COMPARISON),
    ClaimType.LIMITATION: _narrative_contract(ClaimType.LIMITATION),
    ClaimType.MODEL: ClaimTypeContract(claim_type=ClaimType.MODEL),
    ClaimType.MEASUREMENT: ClaimTypeContract(
        claim_type=ClaimType.MEASUREMENT,
        required_fields=("target_concept", "measure"),
        concept_links=(
            ClaimConceptLinkDeclaration(
                field="target_concept", role=ClaimConceptLinkRole.TARGET
            ),
        ),
    ),
    ClaimType.ALGORITHM: ClaimTypeContract(
        claim_type=ClaimType.ALGORITHM,
        required_fields=("body", "output_concept"),
        concept_links=(
            ClaimConceptLinkDeclaration(
                field="output_concept", role=ClaimConceptLinkRole.OUTPUT
            ),
        ),
        semantic_checks=(AlgorithmParseCheck(), AlgorithmUnboundNamesCheck()),
    ),
}


def claim_type_contract_for(claim_type: ClaimType | None) -> ClaimTypeContract | None:
    """Return the contract for ``claim_type``, or ``None`` (e.g. ``UNKNOWN``)."""

    if claim_type is None:
        return None
    return CLAIM_TYPE_CONTRACTS.get(claim_type)


def iter_claim_type_contracts() -> tuple[ClaimTypeContract, ...]:
    """Every declared claim-type contract (the runtime types; not ``UNKNOWN``)."""

    return tuple(CLAIM_TYPE_CONTRACTS.values())


@dataclass(frozen=True)
class ClaimValidationDiagnostic:
    """A non-committal record of a claim authoring problem."""

    field: str | None
    message: str


@dataclass(frozen=True)
class ClaimValidationReport:
    """The outcome of validating one claim against its type contract.

    Non-committal: ``diagnostics`` records problems but the claim is never dropped.
    ``deferred_checks`` names declared semantic checks this phase does not yet run.
    """

    diagnostics: tuple[ClaimValidationDiagnostic, ...] = ()
    sympy_generated: str | None = None
    sympy_error: str | None = None
    deferred_checks: tuple[str, ...] = ()


def _is_present(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, Sized):
        return len(value) > 0
    return True


def validate_claim(claim: Claim) -> ClaimValidationReport:
    """Validate a claim against its type contract; return a report (never raises).

    Checks required/non-empty fields, then runs the semantic checks this phase
    wires: ``SympyGenerationCheck`` delegates to ``human-to-sympy``. Dimensional
    and algorithm checks are named under ``deferred_checks`` (executed in later
    phases), not skipped silently.
    """

    contract = claim_type_contract_for(claim.claim_type)
    if contract is None:
        return ClaimValidationReport(
            diagnostics=(
                ClaimValidationDiagnostic(
                    field="claim_type",
                    message=f"no contract for claim type {claim.claim_type!r}",
                ),
            )
        )

    diagnostics: list[ClaimValidationDiagnostic] = []
    for name in contract.required_fields:
        if not _is_present(getattr(claim, name, None)):
            diagnostics.append(
                ClaimValidationDiagnostic(field=name, message=f"required field {name!r} is missing")
            )
    for name in contract.nonempty_fields:
        if not _is_present(getattr(claim, name, None)):
            diagnostics.append(
                ClaimValidationDiagnostic(field=name, message=f"field {name!r} must be non-empty")
            )

    sympy_generated: str | None = None
    sympy_error: str | None = None
    deferred: list[str] = []
    for check in contract.semantic_checks:
        if isinstance(check, SympyGenerationCheck):
            result = generate_sympy_rhs_with_error(claim.expression)
            sympy_generated = result.expression
            sympy_error = result.error
            if result.error is not None:
                diagnostics.append(
                    ClaimValidationDiagnostic(
                        field="expression", message=f"sympy generation failed: {result.error}"
                    )
                )
        else:
            deferred.append(type(check).__name__)

    return ClaimValidationReport(
        diagnostics=tuple(diagnostics),
        sympy_generated=sympy_generated,
        sympy_error=sympy_error,
        deferred_checks=tuple(deferred),
    )
