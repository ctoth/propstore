"""Claim validation checks driven by claim-type contract declarations."""

from __future__ import annotations

import re
from typing import Any

import bridgman

from ast_equiv import parse_algorithm, extract_names, AlgorithmParseError, KNOWN_BUILTINS

from propstore.artifacts.documents.claims import (
    ClaimTypeContract,
    ClaimUnitPolicyDeclaration,
    ClaimValueGroupDeclaration,
    claim_type_contract_for,
)
from propstore.compiler.context import CompilationContext
from propstore.compiler.references import (
    concept_exists,
    concept_form_definition,
)
from propstore.diagnostics import SemanticDiagnostic
from propstore.dimensions import can_convert_unit_to
from propstore.form_utils import FormDefinition
from propstore.identity import (
    LOGICAL_NAMESPACE_RE,
    LOGICAL_VALUE_RE,
    format_logical_id,
)
from propstore.stances import VALID_STANCE_TYPES


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


def _record(
    diagnostics: list[SemanticDiagnostic],
    *,
    level: str = "error",
    message: str,
    filename: str,
    artifact_id: str | None = None,
) -> None:
    diagnostics.append(
        SemanticDiagnostic(
            level=level,
            message=message,
            filename=filename,
            artifact_id=artifact_id,
        )
    )


def _validate_logical_ids(
    logical_ids: object,
    *,
    filename: str,
    artifact_id: str,
    seen_logical_ids: dict[str, str],
    diagnostics: list[SemanticDiagnostic],
) -> set[str]:
    formatted_ids: set[str] = set()
    if not isinstance(logical_ids, list) or not logical_ids:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"claim '{artifact_id}' must define a non-empty logical_ids list",
            filename=filename,
            artifact_id=artifact_id,
        ))
        return formatted_ids

    for index, entry in enumerate(logical_ids, start=1):
        if not isinstance(entry, dict):
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=f"claim '{artifact_id}' logical_ids entry #{index} must be a mapping",
                filename=filename,
                artifact_id=artifact_id,
            ))
            continue

        namespace = entry.get("namespace")
        value = entry.get("value")
        if not isinstance(namespace, str) or not LOGICAL_NAMESPACE_RE.match(namespace):
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"claim '{artifact_id}' logical_ids entry #{index} "
                    f"uses invalid namespace {namespace!r}"
                ),
                filename=filename,
                artifact_id=artifact_id,
            ))
            continue
        if not isinstance(value, str) or not LOGICAL_VALUE_RE.match(value):
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"claim '{artifact_id}' logical_ids entry #{index} "
                    f"uses invalid value {value!r}"
                ),
                filename=filename,
                artifact_id=artifact_id,
            ))
            continue

        formatted = format_logical_id(entry)
        if formatted is None:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"claim '{artifact_id}' logical_ids entry #{index} "
                    "must serialize as namespace:value"
                ),
                filename=filename,
                artifact_id=artifact_id,
            ))
            continue
        if formatted in formatted_ids:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=f"claim '{artifact_id}' duplicates logical ID '{formatted}'",
                filename=filename,
                artifact_id=artifact_id,
            ))
            continue
        if formatted in seen_logical_ids:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"duplicate logical ID '{formatted}' "
                    f"(also in {seen_logical_ids[formatted]})"
                ),
                filename=filename,
                artifact_id=artifact_id,
            ))
            continue
        formatted_ids.add(formatted)
        seen_logical_ids[formatted] = filename

    return formatted_ids


def _validate_stances(
    claim: dict,
    cid: str,
    filename: str,
    extant_claim_ids: set[str],
    diagnostics: list[SemanticDiagnostic],
) -> None:
    stances = claim.get("stances") or []
    if not isinstance(stances, list):
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"claim '{cid}' stances must be a list",
            filename=filename,
            artifact_id=cid,
        ))
        return

    for index, stance in enumerate(stances, start=1):
        if not isinstance(stance, dict):
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=f"claim '{cid}' stance #{index} must be a mapping",
                filename=filename,
                artifact_id=cid,
            ))
            continue

        stance_type = stance.get("type")
        target_claim_id = stance.get("target")

        if not stance_type:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=f"claim '{cid}' stance #{index} missing type",
                filename=filename,
                artifact_id=cid,
            ))
        elif stance_type not in VALID_STANCE_TYPES:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"claim '{cid}' stance #{index} uses unrecognized "
                    f"type '{stance_type}'"
                ),
                filename=filename,
                artifact_id=cid,
            ))

        if not target_claim_id:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=f"claim '{cid}' stance #{index} missing target",
                filename=filename,
                artifact_id=cid,
            ))
        elif target_claim_id not in extant_claim_ids:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"claim '{cid}' stance #{index} references "
                    f"nonexistent target claim '{target_claim_id}'"
                ),
                filename=filename,
                artifact_id=cid,
            ))

        target_justification_id = stance.get("target_justification_id")
        if target_justification_id is not None:
            if not isinstance(target_justification_id, str) or not target_justification_id:
                diagnostics.append(SemanticDiagnostic(
                    level="error",
                    message=(
                        f"claim '{cid}' stance #{index} "
                        "target_justification_id must be a non-empty string"
                    ),
                    filename=filename,
                    artifact_id=cid,
                ))

        conditions_differ = stance.get("conditions_differ")
        if conditions_differ is not None and not isinstance(conditions_differ, str):
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"claim '{cid}' stance #{index} "
                    "conditions_differ must be a string"
                ),
                filename=filename,
                artifact_id=cid,
            ))

        resolution = stance.get("resolution")
        if resolution is not None:
            if not isinstance(resolution, dict):
                diagnostics.append(SemanticDiagnostic(
                    level="error",
                    message=(
                        f"claim '{cid}' stance #{index} "
                        "resolution must be a mapping"
                    ),
                    filename=filename,
                    artifact_id=cid,
                ))
                continue

            method = resolution.get("method")
            if not isinstance(method, str) or not method:
                diagnostics.append(SemanticDiagnostic(
                    level="error",
                    message=(
                        f"claim '{cid}' stance #{index} "
                        "resolution.method must be a non-empty string"
                    ),
                    filename=filename,
                    artifact_id=cid,
                ))


def _validate_value_fields(
    claim: dict, cid: str, filename: str,
    label: str, diagnostics: list[SemanticDiagnostic],
    value_group: ClaimValueGroupDeclaration,
) -> None:
    """Validate value, bounds, and uncertainty fields shared by parameter and measurement claims."""
    value = claim.get(value_group.value_field)
    lower_bound = claim.get(value_group.lower_bound_field)
    upper_bound = claim.get(value_group.upper_bound_field)

    has_value = value is not None
    has_lower = lower_bound is not None
    has_upper = upper_bound is not None

    if not has_value and not has_lower and not has_upper:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=(
                f"{label} claim '{cid}' missing '{value_group.value_field}' "
                f"(must have {value_group.value_field} or "
                f"{value_group.lower_bound_field}+{value_group.upper_bound_field})"
            ),
            filename=filename,
            artifact_id=cid,
        ))

    if has_lower and not has_upper:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=(
                f"{label} claim '{cid}' has {value_group.lower_bound_field} "
                f"without {value_group.upper_bound_field}"
            ),
            filename=filename,
            artifact_id=cid,
        ))
    if has_upper and not has_lower:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=(
                f"{label} claim '{cid}' has {value_group.upper_bound_field} "
                f"without {value_group.lower_bound_field}"
            ),
            filename=filename,
            artifact_id=cid,
        ))

    if has_lower and has_upper:
        try:
            lb = float(lower_bound)
        except (TypeError, ValueError):
            lb = None
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"{label} claim '{cid}' has non-numeric "
                    f"{value_group.lower_bound_field}: {lower_bound!r}"
                ),
                filename=filename,
                artifact_id=cid,
            ))
        try:
            ub = float(upper_bound)
        except (TypeError, ValueError):
            ub = None
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"{label} claim '{cid}' has non-numeric "
                    f"{value_group.upper_bound_field}: {upper_bound!r}"
                ),
                filename=filename,
                artifact_id=cid,
            ))
        if lb is not None and ub is not None and lb > ub:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"{label} claim '{cid}' {value_group.lower_bound_field} "
                    f"> {value_group.upper_bound_field}"
                ),
                filename=filename,
                artifact_id=cid,
            ))

    uncertainty = claim.get(value_group.uncertainty_field)
    uncertainty_type = claim.get(value_group.uncertainty_type_field)
    has_uncertainty = uncertainty is not None
    has_uncertainty_type = uncertainty_type is not None

    if has_uncertainty_type and not has_uncertainty:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=(
                f"{label} claim '{cid}' has {value_group.uncertainty_type_field} "
                f"without {value_group.uncertainty_field}"
            ),
            filename=filename,
            artifact_id=cid,
        ))
    if has_uncertainty and not has_uncertainty_type:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=(
                f"{label} claim '{cid}' has {value_group.uncertainty_field} "
                f"without {value_group.uncertainty_type_field}"
            ),
            filename=filename,
            artifact_id=cid,
        ))

    if has_uncertainty:
        try:
            uval = float(uncertainty)
        except (TypeError, ValueError):
            uval = None
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"{label} claim '{cid}' has non-numeric "
                    f"{value_group.uncertainty_field}: {uncertainty!r}"
                ),
                filename=filename,
                artifact_id=cid,
            ))
        if uval is not None and uval < 0:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"{label} claim '{cid}' "
                    f"{value_group.uncertainty_field} must be >= 0"
                ),
                filename=filename,
                artifact_id=cid,
            ))


def _has_concepts(context: CompilationContext) -> bool:
    return bool(context.concepts_by_id or context.concept_lookup)


def _concept_exists(concept_ref: object, context: CompilationContext) -> bool:
    return concept_exists(concept_ref, context)


def _concept_form_definition(
    concept_ref: object,
    context: CompilationContext,
) -> FormDefinition | None:
    return concept_form_definition(concept_ref, context)


def validate_claim_semantics(
    claim: dict,
    cid: str,
    filename: str,
    context: CompilationContext,
    diagnostics: list[SemanticDiagnostic],
) -> None:
    contract = claim_type_contract_for(claim.get("type"))
    if contract is None:
        _record(
            diagnostics,
            message=f"claim '{cid}' has unrecognized type '{claim.get('type')}'",
            filename=filename,
            artifact_id=cid,
        )
        return

    _validate_claim_contract(claim, cid, filename, context, diagnostics, contract)
    _run_claim_semantic_checks(claim, cid, filename, context, diagnostics, contract)


def _validate_claim_contract(
    claim: dict,
    cid: str,
    filename: str,
    context: CompilationContext,
    diagnostics: list[SemanticDiagnostic],
    contract: ClaimTypeContract,
) -> None:
    label = contract.claim_type.value

    for field in contract.required_fields:
        if not claim.get(field):
            _record(
                diagnostics,
                message=f"{label} claim '{cid}' missing '{field}'",
                filename=filename,
                artifact_id=cid,
            )

    for field in contract.nonempty_fields:
        value = claim.get(field)
        if not isinstance(value, list) or not value:
            _record(
                diagnostics,
                message=f"{label} claim '{cid}' missing '{field}' (at least one required)",
                filename=filename,
                artifact_id=cid,
            )

    if contract.value_group is not None:
        _validate_value_fields(
            claim,
            cid,
            filename,
            label,
            diagnostics,
            contract.value_group,
        )

    for reference in contract.concept_references:
        _validate_concept_reference_declaration(
            claim,
            cid,
            filename,
            context,
            diagnostics,
            label,
            field=reference.field,
            source=reference.source,
            message_subject=reference.message_subject,
        )

    if contract.unit_policy is not None:
        _validate_unit_policy(
            claim,
            cid,
            filename,
            context,
            diagnostics,
            label,
            contract.unit_policy,
        )


def _validate_concept_reference_declaration(
    claim: dict,
    cid: str,
    filename: str,
    context: CompilationContext,
    diagnostics: list[SemanticDiagnostic],
    label: str,
    *,
    field: str,
    source: str,
    message_subject: str | None,
) -> None:
    if source == "scalar":
        concept_ref = claim.get(field)
        if concept_ref and _has_concepts(context) and not _concept_exists(concept_ref, context):
            _record(
                diagnostics,
                message=f"{label} claim '{cid}' references nonexistent concept '{concept_ref}'",
                filename=filename,
                artifact_id=cid,
            )
        return

    if source == "list":
        values = claim.get(field)
        if not isinstance(values, list):
            return
        for concept_ref in values:
            if _has_concepts(context) and not _concept_exists(concept_ref, context):
                _record(
                    diagnostics,
                    message=(
                        f"{label} claim '{cid}' references "
                        f"nonexistent concept '{concept_ref}'"
                    ),
                    filename=filename,
                    artifact_id=cid,
                )
        return

    if source == "bindings":
        values = claim.get(field)
        if not isinstance(values, list):
            return
        for entry in values:
            if not isinstance(entry, dict):
                continue
            concept_ref = entry.get("concept")
            if concept_ref and _has_concepts(context) and not _concept_exists(concept_ref, context):
                subject = "" if message_subject is None else f" {message_subject}"
                _record(
                    diagnostics,
                    message=(
                        f"{label} claim '{cid}'{subject} references "
                        f"nonexistent concept '{concept_ref}'"
                    ),
                    filename=filename,
                    artifact_id=cid,
                )


def _validate_unit_policy(
    claim: dict,
    cid: str,
    filename: str,
    context: CompilationContext,
    diagnostics: list[SemanticDiagnostic],
    label: str,
    unit_policy: ClaimUnitPolicyDeclaration,
) -> None:
    concept_ref = (
        claim.get(unit_policy.form_concept_field)
        if unit_policy.form_concept_field is not None
        else None
    )
    form_def = (
        _concept_form_definition(concept_ref, context)
        if unit_policy.form_concept_field is not None
        else None
    )
    unit = claim.get("unit")
    if not unit:
        if (
            unit_policy.dimensionless_default_unit is not None
            and form_def is not None
            and form_def.is_dimensionless
        ):
            claim["unit"] = unit_policy.dimensionless_default_unit
            unit = unit_policy.dimensionless_default_unit
        elif unit_policy.required:
            _record(
                diagnostics,
                message=f"{label} claim '{cid}' missing 'unit'",
                filename=filename,
                artifact_id=cid,
            )

    if (
        unit
        and unit_policy.form_concept_field is not None
        and _concept_exists(concept_ref, context)
    ):
        if form_def is None:
            _record(
                diagnostics,
                message=(
                    f"{label} claim '{cid}' concept '{concept_ref}' "
                    "is missing a loaded form definition"
                ),
                filename=filename,
                artifact_id=cid,
            )
            return
        _validate_unit_against_form(unit, form_def, cid, concept_ref or "", filename, diagnostics)


def _run_claim_semantic_checks(
    claim: dict,
    cid: str,
    filename: str,
    context: CompilationContext,
    diagnostics: list[SemanticDiagnostic],
    contract: ClaimTypeContract,
) -> None:
    algorithm_tree: Any = None
    for check in contract.semantic_checks:
        if check == "sympy_generation":
            _validate_equation_sympy_generation(claim, cid, filename, diagnostics)
        elif check == "dimensional_consistency":
            _validate_equation_dimensional_consistency(
                claim,
                cid,
                filename,
                context,
                diagnostics,
            )
        elif check == "algorithm_parse":
            algorithm_tree = _validate_algorithm_parse(
                claim,
                cid,
                filename,
                diagnostics,
            )
        elif check == "algorithm_unbound_names":
            _validate_algorithm_unbound_names(
                claim,
                cid,
                filename,
                context,
                diagnostics,
                algorithm_tree,
            )


def _validate_equation_sympy_generation(
    claim: dict,
    cid: str,
    filename: str,
    diagnostics: list[SemanticDiagnostic],
) -> None:
    from propstore.sympy_generator import generate_sympy_with_error

    expression = claim.get("expression")
    sympy_field = claim.get("sympy")
    if sympy_field:
        sympy_result = generate_sympy_with_error(sympy_field)
        if sympy_result.expression is None:
            _record(
                diagnostics,
                message=(
                    f"equation claim '{cid}' has invalid 'sympy' field: "
                    f"cannot parse '{sympy_field}'"
                    f" ({sympy_result.error})"
                ),
                filename=filename,
                artifact_id=cid,
            )
    elif expression:
        generated = generate_sympy_with_error(expression)
        if generated.expression is None:
            _record(
                diagnostics,
                level="warning",
                message=(
                    f"equation claim '{cid}' could not auto-generate sympy "
                    f"from expression '{expression}'"
                    f" ({generated.error})"
                ),
                filename=filename,
                artifact_id=cid,
            )


def _validate_equation_dimensional_consistency(
    claim: dict,
    cid: str,
    filename: str,
    context: CompilationContext,
    diagnostics: list[SemanticDiagnostic],
) -> None:
    sympy_str = claim.get("sympy")
    variables = claim.get("variables")
    if not sympy_str or not isinstance(variables, list):
        return

    try:
        import sympy as sp

        dim_map: dict[str, dict[str, int]] = {}
        for var in variables:
            if not isinstance(var, dict):
                continue
            var_concept = var.get("concept")
            var_symbol = var.get("symbol")
            if not var_concept or not _has_concepts(context) or not _concept_exists(var_concept, context):
                continue
            form_def = _concept_form_definition(var_concept, context)
            if form_def is None:
                continue
            if form_def.dimensions is not None:
                dims = dict(form_def.dimensions)
            elif form_def.is_dimensionless:
                dims = {}
            else:
                continue
            if var_symbol:
                dim_map[var_symbol] = dims
            dim_map[var_concept] = dims

        for cid_ref in re.findall(r"concept\d+", sympy_str):
            if cid_ref not in dim_map and _concept_exists(cid_ref, context):
                form_def = _concept_form_definition(cid_ref, context)
                if form_def is not None:
                    if form_def.dimensions is not None:
                        dim_map[cid_ref] = dict(form_def.dimensions)
                    elif form_def.is_dimensionless:
                        dim_map[cid_ref] = {}

        if not dim_map:
            return

        parsed = sp.sympify(sympy_str)
        if isinstance(parsed, sp.Eq):
            if not bridgman.verify_expr(parsed, dim_map):
                _record(
                    diagnostics,
                    level="warning",
                    message=(
                        f"equation claim '{cid}' dimensional verification "
                        f"failed for sympy '{sympy_str}'"
                    ),
                    filename=filename,
                    artifact_id=cid,
                )
        else:
            _record(
                diagnostics,
                level="warning",
                message=(
                    f"equation claim '{cid}' sympy '{sympy_str}' "
                    "is not an Eq() - cannot verify dimensional consistency. "
                    "Wrap as Eq(lhs, rhs)."
                ),
                filename=filename,
                artifact_id=cid,
            )
    except (KeyError, SyntaxError, bridgman.DimensionalError, TypeError):
        pass


def _validate_algorithm_parse(
    claim: dict,
    cid: str,
    filename: str,
    diagnostics: list[SemanticDiagnostic],
) -> Any:
    body = claim.get("body")
    if not body:
        return None
    try:
        return parse_algorithm(body)
    except AlgorithmParseError as exc:
        _record(
            diagnostics,
            message=f"algorithm claim '{cid}' body parse error: {exc}",
            filename=filename,
            artifact_id=cid,
        )
        return None


def _validate_algorithm_unbound_names(
    claim: dict,
    cid: str,
    filename: str,
    context: CompilationContext,
    diagnostics: list[SemanticDiagnostic],
    tree: Any,
) -> None:
    variables = claim.get("variables")
    if not isinstance(variables, list):
        return

    declared_names: set[str] = set()
    for var in variables:
        if isinstance(var, dict):
            var_name = var.get("name") or var.get("symbol")
            if var_name:
                declared_names.add(var_name)

    body = claim.get("body")
    if body and tree is not None:
        ast_names = extract_names(tree)
        unbound = ast_names - KNOWN_BUILTINS - declared_names
        for name in sorted(unbound):
            _record(
                diagnostics,
                level="warning",
                message=(
                    f"algorithm claim '{cid}' body references "
                    f"name '{name}' not declared in variables"
                ),
                filename=filename,
                artifact_id=cid,
            )


def _validate_unit_against_form(
    unit: str, form_def: FormDefinition, cid: str, concept: str,
    filename: str, diagnostics: list[SemanticDiagnostic],
) -> None:
    """Check a claim unit against the concept's form definition.

    Uses dimensional analysis via physgen's unit table:
    1. Resolve the unit string to SI dimensions
    2. Compare against the form's declared dimensions
    3. Check the form's declared unit whitelist if dimensional lookup fails
    """
    from propstore.unit_dimensions import resolve_unit_dimensions, dimensions_compatible

    form_dims = form_def.dimensions

    # If the form has dimensions declared, use dimensional analysis
    if form_dims is not None:
        unit_dims = resolve_unit_dimensions(unit)
        if unit_dims is not None:
            if not dimensions_compatible(unit_dims, form_dims):
                diagnostics.append(SemanticDiagnostic(
                    level="error",
                    message=(
                        f"parameter claim '{cid}' unit '{unit}' has dimensions "
                        f"{unit_dims or 'dimensionless'} but concept '{concept}' expects "
                        f"{form_dims or 'dimensionless'}"
                    ),
                    filename=filename,
                    artifact_id=cid,
                ))
            return  # dimensional check passed or errored — done
        # Unit not in lookup table — fall through to whitelist

    # Whitelist check: form declares its accepted units via unit_symbol,
    # common_alternatives, and extra_units. If none declared, skip.
    if form_def.allowed_units:
        if unit not in form_def.allowed_units:
            if can_convert_unit_to(unit, form_def.unit_symbol):
                return
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"parameter claim '{cid}' unit '{unit}' does not match "
                    f"concept '{concept}' allowed units {sorted(form_def.allowed_units)}"
                ),
                filename=filename,
                artifact_id=cid,
            ))

