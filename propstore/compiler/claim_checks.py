"""Per-type claim validators emitting SemanticDiagnostic directly.

Moved from propstore/validate_claims.py in phase 6 of the validation
pipeline migration.  Every function here appends to a
``list[SemanticDiagnostic]`` instead of mutating a ``ValidationResult``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import jsonschema
import bridgman

from ast_equiv import parse_algorithm, extract_names, AlgorithmParseError, KNOWN_BUILTINS

from propstore.cel_checker import (
    ConceptInfo,
    KindType,
    check_cel_expression,
)
from propstore.artifacts.identity import normalize_claim_file_payload
from propstore.core.concepts import LoadedConcept
from propstore.diagnostics import SemanticDiagnostic, ValidationResult
from propstore.dimensions import can_convert_unit_to
from propstore.form_utils import (
    FormDefinition,
    json_safe,
    load_form_path,
)
from propstore.identity import (
    CLAIM_ARTIFACT_ID_RE,
    CLAIM_VERSION_ID_RE,
    LOGICAL_NAMESPACE_RE,
    LOGICAL_VALUE_RE,
    compute_claim_version_id,
    format_logical_id,
)
from propstore.resources import load_resource_json
from propstore.stances import VALID_STANCE_TYPES


# ---------------------------------------------------------------------------
# Schema cache
# ---------------------------------------------------------------------------

_claim_schema_cache: dict | None = None


_SCHEMA_FLOAT_FIELDS = frozenset({
    "value",
    "lower_bound",
    "upper_bound",
    "uncertainty",
})


def _load_claim_schema() -> dict:
    """Load the packaged claim JSON Schema, caching the result."""
    global _claim_schema_cache
    if _claim_schema_cache is None:
        schema = load_resource_json("schemas/claim.schema.json")
        if not isinstance(schema, dict):
            raise TypeError("schemas/claim.schema.json must decode to a JSON object")
        _claim_schema_cache = schema
    return _claim_schema_cache


def _coerce_schema_numeric_strings(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _coerce_schema_numeric_strings(
                _maybe_schema_float(item) if key in _SCHEMA_FLOAT_FIELDS else item
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_coerce_schema_numeric_strings(item) for item in value]
    return value


def _maybe_schema_float(value: object) -> object:
    if not isinstance(value, str):
        return value
    try:
        return float(value)
    except ValueError:
        return value


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


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
) -> None:
    """Validate value, bounds, and uncertainty fields shared by parameter and measurement claims."""
    value = claim.get("value")
    lower_bound = claim.get("lower_bound")
    upper_bound = claim.get("upper_bound")

    has_value = value is not None
    has_lower = lower_bound is not None
    has_upper = upper_bound is not None

    if not has_value and not has_lower and not has_upper:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=(
                f"{label} claim '{cid}' missing 'value' "
                f"(must have value or lower_bound+upper_bound)"
            ),
            filename=filename,
            artifact_id=cid,
        ))

    if has_lower and not has_upper:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"{label} claim '{cid}' has lower_bound without upper_bound",
            filename=filename,
            artifact_id=cid,
        ))
    if has_upper and not has_lower:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"{label} claim '{cid}' has upper_bound without lower_bound",
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
                message=f"{label} claim '{cid}' has non-numeric lower_bound: {lower_bound!r}",
                filename=filename,
                artifact_id=cid,
            ))
        try:
            ub = float(upper_bound)
        except (TypeError, ValueError):
            ub = None
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=f"{label} claim '{cid}' has non-numeric upper_bound: {upper_bound!r}",
                filename=filename,
                artifact_id=cid,
            ))
        if lb is not None and ub is not None and lb > ub:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=f"{label} claim '{cid}' lower_bound > upper_bound",
                filename=filename,
                artifact_id=cid,
            ))

    uncertainty = claim.get("uncertainty")
    uncertainty_type = claim.get("uncertainty_type")
    has_uncertainty = uncertainty is not None
    has_uncertainty_type = uncertainty_type is not None

    if has_uncertainty_type and not has_uncertainty:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"{label} claim '{cid}' has uncertainty_type without uncertainty",
            filename=filename,
            artifact_id=cid,
        ))
    if has_uncertainty and not has_uncertainty_type:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"{label} claim '{cid}' has uncertainty without uncertainty_type",
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
                message=f"{label} claim '{cid}' has non-numeric uncertainty: {uncertainty!r}",
                filename=filename,
                artifact_id=cid,
            ))
        if uval is not None and uval < 0:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=f"{label} claim '{cid}' uncertainty must be >= 0",
                filename=filename,
                artifact_id=cid,
            ))


def _validate_parameter(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], diagnostics: list[SemanticDiagnostic],
) -> None:
    concept_data: dict[str, Any] | None = None
    concept = claim.get("concept")
    if not concept:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"parameter claim '{cid}' missing 'concept'",
            filename=filename,
            artifact_id=cid,
        ))
    elif concept_registry and concept not in concept_registry:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"parameter claim '{cid}' references nonexistent concept '{concept}'",
            filename=filename,
            artifact_id=cid,
        ))
    else:
        concept_data = concept_registry.get(concept) if concept_registry else None

    _validate_value_fields(claim, cid, filename, "parameter", diagnostics)

    # Look up form definition before checking unit so we can auto-fill dimensionless.
    form_def: FormDefinition | None = None
    if concept_data is not None:
        form_def = concept_data.get("_form_definition")

    unit = claim.get("unit")
    if not unit:
        if form_def is not None and form_def.is_dimensionless:
            claim["unit"] = "1"
            unit = "1"
        else:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=f"parameter claim '{cid}' missing 'unit'",
                filename=filename,
                artifact_id=cid,
            ))
    if unit and concept_data is not None:
        if form_def is None:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"parameter claim '{cid}' concept '{concept}' "
                    "is missing a loaded form definition"
                ),
                filename=filename,
                artifact_id=cid,
            ))
            return
        _validate_unit_against_form(unit, form_def, cid, concept or "", filename, diagnostics)


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


def _validate_equation(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], diagnostics: list[SemanticDiagnostic],
) -> None:
    expression = claim.get("expression")
    if not expression:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"equation claim '{cid}' missing 'expression'",
            filename=filename,
            artifact_id=cid,
        ))

    # Validate explicit sympy field if provided; warn if auto-generation fails when absent
    from propstore.sympy_generator import generate_sympy_with_error
    sympy_field = claim.get("sympy")
    if sympy_field:
        sympy_result = generate_sympy_with_error(sympy_field)
        if sympy_result.expression is None:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=(
                    f"equation claim '{cid}' has invalid 'sympy' field: "
                    f"cannot parse '{sympy_field}'"
                    f" ({sympy_result.error})"
                ),
                filename=filename,
                artifact_id=cid,
            ))
    elif expression:
        generated = generate_sympy_with_error(expression)
        if generated.expression is None:
            diagnostics.append(SemanticDiagnostic(
                level="warning",
                message=(
                    f"equation claim '{cid}' could not auto-generate sympy "
                    f"from expression '{expression}'"
                    f" ({generated.error})"
                ),
                filename=filename,
                artifact_id=cid,
            ))

    variables = claim.get("variables")
    if not variables or not isinstance(variables, list) or len(variables) == 0:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"equation claim '{cid}' missing 'variables' (at least one required)",
            filename=filename,
            artifact_id=cid,
        ))
    elif isinstance(variables, list):
        for var in variables:
            if isinstance(var, dict):
                var_concept = var.get("concept")
                if var_concept and var_concept not in concept_registry and concept_registry:
                    diagnostics.append(SemanticDiagnostic(
                        level="error",
                        message=(
                            f"equation claim '{cid}' variable references "
                            f"nonexistent concept '{var_concept}'"
                        ),
                        filename=filename,
                        artifact_id=cid,
                    ))

    # ── Dimensional consistency (bridgman) ────────────────────
    sympy_str = claim.get("sympy")
    if sympy_str and isinstance(variables, list):
        try:
            import sympy as sp

            # Build dim_map: map both symbol names and concept IDs to dimensions
            dim_map: dict[str, dict[str, int]] = {}
            for var in variables:
                if not isinstance(var, dict):
                    continue
                var_concept = var.get("concept")
                var_symbol = var.get("symbol")
                if not var_concept or not concept_registry or var_concept not in concept_registry:
                    continue
                concept_data = concept_registry[var_concept]
                form_def = concept_data.get("_form_definition")
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

            # Also scan sympy for concept IDs not declared in variables
            for cid_ref in re.findall(r'concept\d+', sympy_str):
                if cid_ref not in dim_map and cid_ref in concept_registry:
                    concept_data = concept_registry[cid_ref]
                    form_def = concept_data.get("_form_definition")
                    if form_def is not None:
                        if form_def.dimensions is not None:
                            dim_map[cid_ref] = dict(form_def.dimensions)
                        elif form_def.is_dimensionless:
                            dim_map[cid_ref] = {}

            if dim_map:
                parsed = sp.sympify(sympy_str)
                if isinstance(parsed, sp.Eq):
                    if not bridgman.verify_expr(parsed, dim_map):
                        diagnostics.append(SemanticDiagnostic(
                            level="warning",
                            message=(
                                f"equation claim '{cid}' dimensional verification "
                                f"failed for sympy '{sympy_str}'"
                            ),
                            filename=filename,
                            artifact_id=cid,
                        ))
                else:
                    diagnostics.append(SemanticDiagnostic(
                        level="warning",
                        message=(
                            f"equation claim '{cid}' sympy '{sympy_str}' "
                            f"is not an Eq() — cannot verify dimensional consistency. "
                            f"Wrap as Eq(lhs, rhs)."
                        ),
                        filename=filename,
                        artifact_id=cid,
                    ))
        except (KeyError, SyntaxError, bridgman.DimensionalError, TypeError):
            pass  # missing concept, unparseable sympy, dim errors, or type issues — skip


def _validate_observation(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], diagnostics: list[SemanticDiagnostic],
    claim_type: str = "observation",
) -> None:
    statement = claim.get("statement")
    if not statement:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"{claim_type} claim '{cid}' missing 'statement'",
            filename=filename,
            artifact_id=cid,
        ))

    concepts = claim.get("concepts")
    if not concepts or not isinstance(concepts, list) or len(concepts) == 0:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"{claim_type} claim '{cid}' missing 'concepts' (at least one required)",
            filename=filename,
            artifact_id=cid,
        ))
    elif isinstance(concepts, list):
        for concept_id in concepts:
            if concept_id not in concept_registry and concept_registry:
                diagnostics.append(SemanticDiagnostic(
                    level="error",
                    message=(
                        f"{claim_type} claim '{cid}' references "
                        f"nonexistent concept '{concept_id}'"
                    ),
                    filename=filename,
                    artifact_id=cid,
                ))


def _validate_model(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], diagnostics: list[SemanticDiagnostic],
) -> None:
    name = claim.get("name")
    if not name:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"model claim '{cid}' missing 'name'",
            filename=filename,
            artifact_id=cid,
        ))

    equations = claim.get("equations")
    if not equations or not isinstance(equations, list) or len(equations) == 0:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"model claim '{cid}' missing 'equations' (at least one required)",
            filename=filename,
            artifact_id=cid,
        ))

    parameters = claim.get("parameters")
    if not parameters or not isinstance(parameters, list) or len(parameters) == 0:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"model claim '{cid}' missing 'parameters' (at least one required)",
            filename=filename,
            artifact_id=cid,
        ))
    elif isinstance(parameters, list):
        for param in parameters:
            if isinstance(param, dict):
                param_concept = param.get("concept")
                if param_concept and param_concept not in concept_registry and concept_registry:
                    diagnostics.append(SemanticDiagnostic(
                        level="error",
                        message=(
                            f"model claim '{cid}' parameter references "
                            f"nonexistent concept '{param_concept}'"
                        ),
                        filename=filename,
                        artifact_id=cid,
                    ))


def _validate_measurement(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], diagnostics: list[SemanticDiagnostic],
) -> None:
    target_concept = claim.get("target_concept")
    if not target_concept:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"measurement claim '{cid}' missing 'target_concept'",
            filename=filename,
            artifact_id=cid,
        ))
    elif target_concept not in concept_registry and concept_registry:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"measurement claim '{cid}' references nonexistent concept '{target_concept}'",
            filename=filename,
            artifact_id=cid,
        ))

    measure = claim.get("measure")
    if not measure:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"measurement claim '{cid}' missing 'measure'",
            filename=filename,
            artifact_id=cid,
        ))

    _validate_value_fields(claim, cid, filename, "measurement", diagnostics)

    unit = claim.get("unit")
    if not unit:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"measurement claim '{cid}' missing 'unit'",
            filename=filename,
            artifact_id=cid,
        ))


def _validate_algorithm(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], diagnostics: list[SemanticDiagnostic],
) -> None:
    body = claim.get("body")
    tree = None
    if not body:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"algorithm claim '{cid}' missing 'body'",
            filename=filename,
            artifact_id=cid,
        ))
    else:
        try:
            tree = parse_algorithm(body)
        except AlgorithmParseError as e:
            diagnostics.append(SemanticDiagnostic(
                level="error",
                message=f"algorithm claim '{cid}' body parse error: {e}",
                filename=filename,
                artifact_id=cid,
            ))
            tree = None

    variables = claim.get("variables")
    if not variables:
        diagnostics.append(SemanticDiagnostic(
            level="error",
            message=f"algorithm claim '{cid}' missing 'variables' (at least one required)",
            filename=filename,
            artifact_id=cid,
        ))
    elif isinstance(variables, list):
        declared_names: set[str] = set()
        for var in variables:
            if isinstance(var, dict):
                var_concept = var.get("concept")
                if var_concept and var_concept not in concept_registry and concept_registry:
                    diagnostics.append(SemanticDiagnostic(
                        level="error",
                        message=(
                            f"algorithm claim '{cid}' variable references "
                            f"nonexistent concept '{var_concept}'"
                        ),
                        filename=filename,
                        artifact_id=cid,
                    ))
                var_name = var.get("name") or var.get("symbol")
                if var_name:
                    declared_names.add(var_name)

        # Cross-check: warn about unbound names in body AST
        if body and tree is not None:
            ast_names = extract_names(tree)
            unbound = ast_names - KNOWN_BUILTINS - declared_names
            for name in sorted(unbound):
                diagnostics.append(SemanticDiagnostic(
                    level="warning",
                    message=(
                        f"algorithm claim '{cid}' body references "
                        f"name '{name}' not declared in variables"
                    ),
                    filename=filename,
                    artifact_id=cid,
                ))
