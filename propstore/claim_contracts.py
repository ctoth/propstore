"""Claim-type contracts and the claim-validate workflow.

Each :class:`~propstore.families.claims.ClaimType` carries a declarative
*contract*: which fields it requires, which must be non-empty, how its scalar/
list concept references are role-linked, its value-group and unit policy, and the
semantic checks it must pass. This is propstore's own claim semantics — it is NOT
condition machinery and stays propstore-side.

The validate workflow is non-committal (PLAN.md §12, CLAUDE.md): it never raises
or drops a claim. It returns a report of diagnostics; the caller (a later build
pass) decides to quarantine, never to abort. The sympy-generation semantic check
delegates to ``human-to-sympy`` directly (``generate_sympy_rhs_with_error``), and
algorithm parsing and free-variable analysis delegate to ``ast-equiv``.
Dimensional checks resolve checked forms and concept bindings, then delegate
the authored expression's algebra to Bridgman.
"""

from __future__ import annotations

import ast
from collections.abc import Sized
from dataclasses import dataclass
from enum import Enum
from tokenize import TokenError
from typing import TYPE_CHECKING

from ast_equiv import AlgorithmParseError, extract_free_variables, parse_algorithm
from condition_ir import ConceptInfo, KindType
from bridgman import DimensionalError, canonicalize_dims, verify_expr
from human_to_sympy import generate_sympy_rhs_with_error, parse_symbolic
from sympy import Eq, Symbol, SympifyError
from sympy.core.relational import Equality

from propstore.core.scalars import ScalarValue
from propstore.families.claims import Claim, ClaimType
from propstore.families.forms import FormDefinition

if TYPE_CHECKING:
    from propstore.compiler.context import CompilationContext


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
    """Check an equation against checked concept forms through Bridgman."""


@dataclass(frozen=True)
class AlgorithmParseCheck(ClaimSemanticCheck):
    """Check that an algorithm body parses through ast-equiv."""


@dataclass(frozen=True)
class AlgorithmUnboundNamesCheck(ClaimSemanticCheck):
    """Check that an algorithm's free names have declared concept bindings."""


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
        field="concepts",
        role=ClaimConceptLinkRole.ABOUT,
        source=ClaimConceptLinkSource.LIST,
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
    code: str = "claim.contract"


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


def validate_claim_value_fields(
    *,
    value: ScalarValue | None,
    lower_bound: float | None,
    upper_bound: float | None,
    form: FormDefinition,
    concept_info: ConceptInfo | None,
) -> tuple[ClaimValidationDiagnostic, ...]:
    """Validate Claim value fields against their form and concept semantics."""

    diagnostics: list[ClaimValidationDiagnostic] = []
    if form.kind in {KindType.QUANTITY, KindType.TIMEPOINT}:
        numeric_fields: tuple[tuple[str, int | float], ...] = tuple(
            (field, numeric)
            for field, numeric in (
                ("value", value),
                ("lower_bound", lower_bound),
                ("upper_bound", upper_bound),
            )
            if isinstance(numeric, int | float) and not isinstance(numeric, bool)
        )
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int | float)
        ):
            diagnostics.append(
                ClaimValidationDiagnostic(
                    field="value",
                    message=f"value must be numeric for form {form.name!r}",
                )
            )
        for field, numeric in numeric_fields:
            if form.min_value is not None and numeric < form.min_value:
                diagnostics.append(
                    ClaimValidationDiagnostic(
                        field=field,
                        message=(
                            f"{field}={numeric} is below form {form.name!r} "
                            f"min={form.min_value}"
                        ),
                    )
                )
            if form.max_value is not None and numeric > form.max_value:
                diagnostics.append(
                    ClaimValidationDiagnostic(
                        field=field,
                        message=(
                            f"{field}={numeric} is above form {form.name!r} "
                            f"max={form.max_value}"
                        ),
                    )
                )
        return tuple(diagnostics)

    if form.kind is KindType.STRUCTURAL:
        return ()

    for field, bound in (
        ("lower_bound", lower_bound),
        ("upper_bound", upper_bound),
    ):
        if bound is not None:
            diagnostics.append(
                ClaimValidationDiagnostic(
                    field=field,
                    message=f"{field} is not valid for {form.kind.value} form {form.name!r}",
                )
            )

    if form.kind is KindType.CATEGORY and value is not None:
        if not isinstance(value, str):
            diagnostics.append(
                ClaimValidationDiagnostic(
                    field="value",
                    message=f"value must be text for category form {form.name!r}",
                )
            )
        elif (
            concept_info is not None
            and not concept_info.category_extensible
            and value not in concept_info.category_values
        ):
            diagnostics.append(
                ClaimValidationDiagnostic(
                    field="value",
                    message=(
                        f"value {value!r} is outside the closed category vocabulary "
                        f"for concept {concept_info.canonical_name!r}"
                    ),
                )
            )
    elif (
        form.kind is KindType.BOOLEAN
        and value is not None
        and not isinstance(value, bool)
    ):
        diagnostics.append(
            ClaimValidationDiagnostic(
                field="value",
                message=f"value must be boolean for form {form.name!r}",
            )
        )
    return tuple(diagnostics)


def _is_present(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, Sized):
        return len(value) > 0
    return True


def _check_equation_dimensions(
    claim: Claim, context: CompilationContext | None,
) -> tuple[ClaimValidationDiagnostic, ...]:
    """Resolve claim-owned bindings; the substrate owns all dimensional algebra."""
    problems: list[ClaimValidationDiagnostic] = []
    evidence: list[str] = []

    def problem(code: str, detail: str) -> None:
        problems.append(ClaimValidationDiagnostic("expression", detail, code))

    if context is None:
        problem("claim.dimension.context.missing", "dimensional evidence unavailable: no checked compilation context")
        return tuple(problems)

    def dimensions(concept_id: str | None, label: str) -> dict[str, int] | None:
        concept = context.concepts_by_id.get(concept_id or "")
        if concept is None:
            problem("claim.dimension.concept.missing", f"dimensional evidence unavailable: {label}, concept {concept_id!r} is missing")
            return None
        entry = concept.lexical_entry
        form_name = None if entry is None else entry.physical_dimension_form
        form = context.form_registry.registry.get(form_name or "")
        resolved = f"{label}, concept {concept_id!r}, form {form_name!r}"
        if form is None:
            problem("claim.dimension.form.missing", f"dimensional evidence unavailable: {resolved} is missing")
            return None
        if form.kind is not KindType.QUANTITY:
            problem("claim.dimension.kind.invalid", f"dimensional evidence unavailable: {resolved} has non-quantity kind {form.kind.value!r}")
            return None
        if form.dimensions is None and not form.is_dimensionless:
            problem("claim.dimension.signature.missing", f"dimensional evidence unavailable: {resolved} has no dimension signature")
            return None
        dims = canonicalize_dims(form.dimensions or {})
        evidence.append(f"{resolved}: dimensions {dims}")
        return dims

    try:
        parsed = parse_symbolic(
            claim.expression or "",
            symbol_names=tuple(variable.symbol for variable in claim.variables if variable.symbol),
        )
    except (SympifyError, TypeError, ValueError, SyntaxError, TokenError, RecursionError) as exc:
        problem("claim.dimension.expression.invalid", f"dimensional expression could not be checked: {exc}")
        return tuple(problems)

    dim_map: dict[str, dict[str, int]] = {}
    for symbol in sorted(parsed.free_symbols, key=str):
        bindings = [variable for variable in claim.variables if variable.symbol == symbol.name]
        if len(bindings) != 1:
            problem("claim.dimension.binding.unavailable", f"dimensional evidence unavailable: symbol {symbol.name!r} requires one concept binding; found {len(bindings)}")
            continue
        binding = bindings[0]
        dims = dimensions(binding.concept, f"symbol {symbol.name!r}, role {binding.role!r}")
        if dims is not None:
            dim_map[symbol.name] = dims

    if isinstance(parsed, Equality):
        if claim.output_concept is not None and not any(
            variable.concept == claim.output_concept
            and variable.symbol in dim_map
            for variable in claim.variables
        ):
            problem(
                "claim.dimension.output.binding.unavailable",
                f"dimensional evidence unavailable: output concept {claim.output_concept!r} has no used symbol binding in the equation",
            )
    else:
        output_dims = dimensions(claim.output_concept, "output")
        if output_dims is not None:
            output_name = "__claim_output__"
            while output_name in dim_map:
                output_name += "_"
            dim_map[output_name] = output_dims
            parsed = Eq(Symbol(output_name), parsed, evaluate=False)
    if problems:
        return tuple(problems)

    details = "; ".join(evidence)
    try:
        verified = verify_expr(parsed, dim_map)
    except (DimensionalError, KeyError, TypeError, ValueError, RecursionError) as exc:
        problem("claim.dimension.algebra.invalid", f"dimensional algebra failed: {exc}; {details}")
    else:
        if not verified:
            problem("claim.dimension.mismatch", f"dimensionally inconsistent equation {claim.expression!r}; {details}")
    return tuple(problems)


def validate_claim(
    claim: Claim,
    *,
    form: FormDefinition | None = None,
    concept_info: ConceptInfo | None = None,
    context: CompilationContext | None = None,
) -> ClaimValidationReport:
    """Validate a claim against its type contract; return a report (never raises).

    Checks required/non-empty fields, then runs the semantic checks this phase
    wires: ``SympyGenerationCheck`` delegates to ``human-to-sympy`` and
    algorithm parsing/free-name checks delegate to ``ast-equiv``. Equation
    dimensions use the exact checked forms in ``context`` and Bridgman.
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
    if form is not None:
        diagnostics.extend(
            validate_claim_value_fields(
                value=claim.value,
                lower_bound=claim.lower_bound,
                upper_bound=claim.upper_bound,
                form=form,
                concept_info=concept_info,
            )
        )
    for name in contract.required_fields:
        if not _is_present(getattr(claim, name, None)):
            diagnostics.append(
                ClaimValidationDiagnostic(
                    field=name, message=f"required field {name!r} is missing"
                )
            )
    for name in contract.nonempty_fields:
        if not _is_present(getattr(claim, name, None)):
            diagnostics.append(
                ClaimValidationDiagnostic(
                    field=name, message=f"field {name!r} must be non-empty"
                )
            )

    sympy_generated: str | None = None
    sympy_error: str | None = None
    algorithm_tree: ast.Module | None = None
    deferred: list[str] = []
    for check in contract.semantic_checks:
        if isinstance(check, SympyGenerationCheck):
            result = generate_sympy_rhs_with_error(claim.expression)
            sympy_generated = result.expression
            sympy_error = result.error
            if result.error is not None:
                diagnostics.append(
                    ClaimValidationDiagnostic(
                        field="expression",
                        message=f"sympy generation failed: {result.error}",
                    )
                )
        elif isinstance(check, DimensionalConsistencyCheck):
            if sympy_error is None:
                diagnostics.extend(_check_equation_dimensions(claim, context))
        elif isinstance(check, AlgorithmParseCheck):
            try:
                algorithm_tree = parse_algorithm(claim.body or "")
            except (AlgorithmParseError, RecursionError) as exc:
                diagnostics.append(
                    ClaimValidationDiagnostic(
                        field="body", message=f"algorithm body parse error: {exc}"
                    )
                )
        elif isinstance(check, AlgorithmUnboundNamesCheck):
            if algorithm_tree is not None:
                declared_names = {
                    variable.name or variable.symbol
                    for variable in claim.variables
                    if variable.concept and (variable.name or variable.symbol)
                }
                try:
                    unbound_names = sorted(
                        extract_free_variables(algorithm_tree) - declared_names
                    )
                except (AlgorithmParseError, RecursionError) as exc:
                    diagnostics.append(
                        ClaimValidationDiagnostic(
                            field="body", message=f"algorithm body binding error: {exc}"
                        )
                    )
                    continue
                if unbound_names:
                    diagnostics.append(
                        ClaimValidationDiagnostic(
                            field="body",
                            message=(
                                "algorithm body has unbound names: "
                                + ", ".join(unbound_names)
                            ),
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
