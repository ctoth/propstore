"""Claim file validator for the propstore propositional knowledge store.

Loads all claims/*.yaml files, validates against the JSON Schema,
then runs the compiler contract checks that JSON Schema can't express.

Reports errors (hard stop) and warnings separately.
Exits nonzero on any error.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from propstore.cli.repository import Repository
    from propstore.knowledge_path import KnowledgePath

import jsonschema
import yaml
import bridgman

from propstore.compiler.context import (
    CompilationContext,
    build_compilation_context_from_paths as build_claim_compilation_context_from_paths,
    build_compilation_context_from_repo as build_claim_compilation_context_from_repo,
    build_concept_registry_from_paths,
    compilation_context_from_concept_registry,
)
from propstore.compiler.passes import compile_claim_files
from propstore.resources import load_resource_json
from propstore.identity import (
    CLAIM_ARTIFACT_ID_RE,
    CLAIM_VERSION_ID_RE,
    LOGICAL_NAMESPACE_RE,
    LOGICAL_VALUE_RE,
    compute_claim_version_id,
    format_logical_id,
    normalize_claim_file_payload,
)
from propstore.knowledge_path import coerce_knowledge_path
from propstore.validate import (
    ValidationResult,
    load_concepts,
    load_yaml_dir,
    load_yaml_entries,
)

from ast_equiv import parse_algorithm, extract_names, AlgorithmParseError, KNOWN_BUILTINS

from propstore.cel_checker import (
    ConceptInfo,
    KindType,
    build_cel_registry,
    check_cel_expression,
)
from propstore.core.concepts import LoadedConcept, normalize_loaded_concepts
from propstore.form_utils import (
    FormDefinition,
    json_safe,
    load_form_path,
)
from propstore.stances import VALID_STANCE_TYPES


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


from propstore.loaded import LoadedEntry



def load_claim_files(claims_dir: KnowledgePath | None) -> list[LoadedEntry]:
    """Load all claim YAML files from a claims subtree."""
    return load_yaml_entries(claims_dir)




# Logical claim IDs are always namespaced ``namespace:value`` handles.
_LOGICAL_CLAIM_ID_RE = re.compile(
    r"^(?P<namespace>[A-Za-z0-9][A-Za-z0-9._-]*):(?P<value>[A-Za-z0-9][A-Za-z0-9._/-]*)$"
)


def parse_claim_id(cid: str) -> tuple[str | None, str]:
    """Split a logical claim ID into ``(namespace, local_id)``."""
    match = _LOGICAL_CLAIM_ID_RE.match(cid)
    if match is None:
        return None, cid
    return match.group("namespace"), match.group("value")


def _validate_logical_ids(
    logical_ids: object,
    *,
    filename: str,
    artifact_id: str,
    seen_logical_ids: dict[str, str],
    result: ValidationResult,
) -> set[str]:
    formatted_ids: set[str] = set()
    if not isinstance(logical_ids, list) or not logical_ids:
        result.errors.append(
            f"{filename}: claim '{artifact_id}' must define a non-empty logical_ids list"
        )
        return formatted_ids

    for index, entry in enumerate(logical_ids, start=1):
        if not isinstance(entry, dict):
            result.errors.append(
                f"{filename}: claim '{artifact_id}' logical_ids entry #{index} must be a mapping"
            )
            continue

        namespace = entry.get("namespace")
        value = entry.get("value")
        if not isinstance(namespace, str) or not LOGICAL_NAMESPACE_RE.match(namespace):
            result.errors.append(
                f"{filename}: claim '{artifact_id}' logical_ids entry #{index} "
                f"uses invalid namespace {namespace!r}"
            )
            continue
        if not isinstance(value, str) or not LOGICAL_VALUE_RE.match(value):
            result.errors.append(
                f"{filename}: claim '{artifact_id}' logical_ids entry #{index} "
                f"uses invalid value {value!r}"
            )
            continue

        formatted = format_logical_id(entry)
        if formatted is None:
            result.errors.append(
                f"{filename}: claim '{artifact_id}' logical_ids entry #{index} "
                "must serialize as namespace:value"
            )
            continue
        if formatted in formatted_ids:
            result.errors.append(
                f"{filename}: claim '{artifact_id}' duplicates logical ID '{formatted}'"
            )
            continue
        if formatted in seen_logical_ids:
            result.errors.append(
                f"{filename}: duplicate logical ID '{formatted}' "
                f"(also in {seen_logical_ids[formatted]})"
            )
            continue
        formatted_ids.add(formatted)
        seen_logical_ids[formatted] = filename

    return formatted_ids


def validate_single_claim_file(
    filepath: Path,
    concept_registry: dict[str, dict],
) -> ValidationResult:
    """Validate a single claims YAML file.

    Loads the file, wraps it in a LoadedEntry, and runs
    validate_claims on just that one file.
    """
    with open(filepath, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    loaded = LoadedEntry(
        filename=filepath.stem,
        source_path=coerce_knowledge_path(filepath),
        data=data if data else {},
    )
    return validate_claims([loaded], concept_registry)


def validate_claims(
    claim_files: list[LoadedEntry],
    concept_registry: dict[str, dict] | CompilationContext,
    context_ids: set[str] | None = None,
) -> ValidationResult:
    """Validate claim files against schema and compiler contract.

    Args:
        claim_files: loaded claim YAML files
        concept_registry: legacy concept registry or compilation context
        context_ids: set of valid context IDs (if None, skip context validation)
    """
    context = (
        concept_registry
        if isinstance(concept_registry, CompilationContext)
        else compilation_context_from_concept_registry(
            concept_registry,
            claim_files=claim_files,
            context_ids=context_ids,
        )
    )
    bundle = compile_claim_files(
        claim_files,
        context,
        context_ids=context_ids,
    )
    return bundle.to_validation_result()


def _validate_stances(
    claim: dict,
    cid: str,
    filename: str,
    extant_claim_ids: set[str],
    result: ValidationResult,
) -> None:
    stances = claim.get("stances") or []
    if not isinstance(stances, list):
        result.errors.append(f"{filename}: claim '{cid}' stances must be a list")
        return

    for index, stance in enumerate(stances, start=1):
        if not isinstance(stance, dict):
            result.errors.append(
                f"{filename}: claim '{cid}' stance #{index} must be a mapping"
            )
            continue

        stance_type = stance.get("type")
        target_claim_id = stance.get("target")

        if not stance_type:
            result.errors.append(
                f"{filename}: claim '{cid}' stance #{index} missing type"
            )
        elif stance_type not in VALID_STANCE_TYPES:
            result.errors.append(
                f"{filename}: claim '{cid}' stance #{index} uses unrecognized "
                f"type '{stance_type}'"
            )

        if not target_claim_id:
            result.errors.append(
                f"{filename}: claim '{cid}' stance #{index} missing target"
            )
        elif target_claim_id not in extant_claim_ids:
            result.errors.append(
                f"{filename}: claim '{cid}' stance #{index} references "
                f"nonexistent target claim '{target_claim_id}'"
            )

        target_justification_id = stance.get("target_justification_id")
        if target_justification_id is not None:
            if not isinstance(target_justification_id, str) or not target_justification_id:
                result.errors.append(
                    f"{filename}: claim '{cid}' stance #{index} "
                    "target_justification_id must be a non-empty string"
                )

        conditions_differ = stance.get("conditions_differ")
        if conditions_differ is not None and not isinstance(conditions_differ, str):
            result.errors.append(
                f"{filename}: claim '{cid}' stance #{index} "
                "conditions_differ must be a string"
            )

        resolution = stance.get("resolution")
        if resolution is not None:
            if not isinstance(resolution, dict):
                result.errors.append(
                    f"{filename}: claim '{cid}' stance #{index} "
                    "resolution must be a mapping"
                )
                continue

            method = resolution.get("method")
            if not isinstance(method, str) or not method:
                result.errors.append(
                    f"{filename}: claim '{cid}' stance #{index} "
                    "resolution.method must be a non-empty string"
                )


def _validate_value_fields(
    claim: dict, cid: str, filename: str,
    label: str, result: ValidationResult,
) -> None:
    """Validate value, bounds, and uncertainty fields shared by parameter and measurement claims."""
    value = claim.get("value")
    lower_bound = claim.get("lower_bound")
    upper_bound = claim.get("upper_bound")

    has_value = value is not None
    has_lower = lower_bound is not None
    has_upper = upper_bound is not None

    if not has_value and not has_lower and not has_upper:
        result.errors.append(
            f"{filename}: {label} claim '{cid}' missing 'value' "
            f"(must have value or lower_bound+upper_bound)")

    if has_lower and not has_upper:
        result.errors.append(
            f"{filename}: {label} claim '{cid}' has lower_bound without upper_bound")
    if has_upper and not has_lower:
        result.errors.append(
            f"{filename}: {label} claim '{cid}' has upper_bound without lower_bound")

    if has_lower and has_upper:
        try:
            lb = float(lower_bound)
        except (TypeError, ValueError):
            lb = None
            result.errors.append(
                f"{filename}: {label} claim '{cid}' has non-numeric lower_bound: {lower_bound!r}")
        try:
            ub = float(upper_bound)
        except (TypeError, ValueError):
            ub = None
            result.errors.append(
                f"{filename}: {label} claim '{cid}' has non-numeric upper_bound: {upper_bound!r}")
        if lb is not None and ub is not None and lb > ub:
            result.errors.append(
                f"{filename}: {label} claim '{cid}' lower_bound > upper_bound")

    uncertainty = claim.get("uncertainty")
    uncertainty_type = claim.get("uncertainty_type")
    has_uncertainty = uncertainty is not None
    has_uncertainty_type = uncertainty_type is not None

    if has_uncertainty_type and not has_uncertainty:
        result.errors.append(
            f"{filename}: {label} claim '{cid}' has uncertainty_type without uncertainty")
    if has_uncertainty and not has_uncertainty_type:
        result.errors.append(
            f"{filename}: {label} claim '{cid}' has uncertainty without uncertainty_type")

    if has_uncertainty:
        try:
            uval = float(uncertainty)
        except (TypeError, ValueError):
            uval = None
            result.errors.append(
                f"{filename}: {label} claim '{cid}' has non-numeric uncertainty: {uncertainty!r}")
        if uval is not None and uval < 0:
            result.errors.append(
                f"{filename}: {label} claim '{cid}' uncertainty must be >= 0")


def _validate_parameter(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], result: ValidationResult,
) -> None:
    concept_data: dict[str, Any] | None = None
    concept = claim.get("concept")
    if not concept:
        result.errors.append(f"{filename}: parameter claim '{cid}' missing 'concept'")
    elif concept_registry and concept not in concept_registry:
        result.errors.append(
            f"{filename}: parameter claim '{cid}' references nonexistent concept '{concept}'")
    else:
        concept_data = concept_registry.get(concept) if concept_registry else None

    _validate_value_fields(claim, cid, filename, "parameter", result)

    unit = claim.get("unit")
    if not unit:
        result.errors.append(f"{filename}: parameter claim '{cid}' missing 'unit'")
    elif concept_data is not None:
        form_def: FormDefinition | None = concept_data.get("_form_definition")
        if form_def is None:
            result.errors.append(
                f"{filename}: parameter claim '{cid}' concept '{concept}' "
                "is missing a loaded form definition"
            )
            return
        _validate_unit_against_form(unit, form_def, cid, concept or "", filename, result)


def _validate_unit_against_form(
    unit: str, form_def: FormDefinition, cid: str, concept: str,
    filename: str, result: ValidationResult,
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
                result.errors.append(
                    f"{filename}: parameter claim '{cid}' unit '{unit}' has dimensions "
                    f"{unit_dims or 'dimensionless'} but concept '{concept}' expects "
                    f"{form_dims or 'dimensionless'}")
            return  # dimensional check passed or errored — done
        # Unit not in lookup table — fall through to whitelist

    # Whitelist check: form declares its accepted units via unit_symbol,
    # common_alternatives, and extra_units. If none declared, skip.
    if form_def.allowed_units:
        if unit not in form_def.allowed_units:
            # Before rejecting, try pint dimensional compatibility.
            # This lets units like "years" pass for a time form even though
            # they aren't in the explicit whitelist — normalize_to_si()
            # handles the actual conversion at build time.
            try:
                from propstore.form_utils import ureg, _pint_unit
                src = ureg.Quantity(1, _pint_unit(unit))
                src.to(_pint_unit(form_def.unit_symbol))
                # Dimensionally compatible — accept it
                return
            except Exception:
                pass
            result.errors.append(
                f"{filename}: parameter claim '{cid}' unit '{unit}' does not match "
                f"concept '{concept}' allowed units {sorted(form_def.allowed_units)}")


def _validate_equation(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], result: ValidationResult,
) -> None:
    expression = claim.get("expression")
    if not expression:
        result.errors.append(f"{filename}: equation claim '{cid}' missing 'expression'")

    # Validate explicit sympy field if provided; warn if auto-generation fails when absent
    from propstore.sympy_generator import generate_sympy_with_error
    sympy_field = claim.get("sympy")
    if sympy_field:
        # Use generate_sympy for validation — it handles = and ^ preprocessing
        sympy_result = generate_sympy_with_error(sympy_field)
        if sympy_result.expression is None:
            result.errors.append(
                f"{filename}: equation claim '{cid}' has invalid 'sympy' field: "
                f"cannot parse '{sympy_field}'"
                f" ({sympy_result.error})")
    elif expression:
        generated = generate_sympy_with_error(expression)
        if generated.expression is None:
            result.warnings.append(
                f"{filename}: equation claim '{cid}' could not auto-generate sympy "
                f"from expression '{expression}'"
                f" ({generated.error})")

    variables = claim.get("variables")
    if not variables or not isinstance(variables, list) or len(variables) == 0:
        result.errors.append(f"{filename}: equation claim '{cid}' missing 'variables' (at least one required)")
    elif isinstance(variables, list):
        for var in variables:
            if isinstance(var, dict):
                var_concept = var.get("concept")
                if var_concept and var_concept not in concept_registry and concept_registry:
                    result.errors.append(
                        f"{filename}: equation claim '{cid}' variable references "
                        f"nonexistent concept '{var_concept}'")

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
                # Map by symbol (used in sympy expressions)
                if var_symbol:
                    dim_map[var_symbol] = dims
                # Also map by concept ID (some sympy fields use concept IDs)
                dim_map[var_concept] = dims

            # Also scan sympy for concept IDs not declared in variables
            import re
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
                        result.warnings.append(
                            f"{filename}: equation claim '{cid}' dimensional verification "
                            f"failed for sympy '{sympy_str}'")
                else:
                    # Non-Eq expression — can't verify dimensional consistency
                    # because there's no lhs=rhs to compare.
                    result.warnings.append(
                        f"{filename}: equation claim '{cid}' sympy '{sympy_str}' "
                        f"is not an Eq() — cannot verify dimensional consistency. "
                        f"Wrap as Eq(lhs, rhs).")
        except (KeyError, SyntaxError, bridgman.DimensionalError, TypeError):
            pass  # missing concept, unparseable sympy, dim errors, or type issues — skip


def _validate_observation(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], result: ValidationResult,
    claim_type: str = "observation",
) -> None:
    statement = claim.get("statement")
    if not statement:
        result.errors.append(f"{filename}: {claim_type} claim '{cid}' missing 'statement'")

    concepts = claim.get("concepts")
    if not concepts or not isinstance(concepts, list) or len(concepts) == 0:
        result.errors.append(f"{filename}: {claim_type} claim '{cid}' missing 'concepts' (at least one required)")
    elif isinstance(concepts, list):
        for concept_id in concepts:
            if concept_id not in concept_registry and concept_registry:
                result.errors.append(
                    f"{filename}: {claim_type} claim '{cid}' references "
                    f"nonexistent concept '{concept_id}'")


def _validate_model(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], result: ValidationResult,
) -> None:
    name = claim.get("name")
    if not name:
        result.errors.append(f"{filename}: model claim '{cid}' missing 'name'")

    equations = claim.get("equations")
    if not equations or not isinstance(equations, list) or len(equations) == 0:
        result.errors.append(f"{filename}: model claim '{cid}' missing 'equations' (at least one required)")

    parameters = claim.get("parameters")
    if not parameters or not isinstance(parameters, list) or len(parameters) == 0:
        result.errors.append(f"{filename}: model claim '{cid}' missing 'parameters' (at least one required)")
    elif isinstance(parameters, list):
        for param in parameters:
            if isinstance(param, dict):
                param_concept = param.get("concept")
                if param_concept and param_concept not in concept_registry and concept_registry:
                    result.errors.append(
                        f"{filename}: model claim '{cid}' parameter references "
                        f"nonexistent concept '{param_concept}'")


def _validate_measurement(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], result: ValidationResult,
) -> None:
    target_concept = claim.get("target_concept")
    if not target_concept:
        result.errors.append(f"{filename}: measurement claim '{cid}' missing 'target_concept'")
    elif target_concept not in concept_registry and concept_registry:
        result.errors.append(
            f"{filename}: measurement claim '{cid}' references nonexistent concept '{target_concept}'")

    measure = claim.get("measure")
    if not measure:
        result.errors.append(f"{filename}: measurement claim '{cid}' missing 'measure'")

    _validate_value_fields(claim, cid, filename, "measurement", result)

    unit = claim.get("unit")
    if not unit:
        result.errors.append(f"{filename}: measurement claim '{cid}' missing 'unit'")


def _validate_algorithm(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], result: ValidationResult,
) -> None:
    body = claim.get("body")
    tree = None
    if not body:
        result.errors.append(f"{filename}: algorithm claim '{cid}' missing 'body'")
    else:
        try:
            tree = parse_algorithm(body)
        except AlgorithmParseError as e:
            result.errors.append(
                f"{filename}: algorithm claim '{cid}' body parse error: {e}")
            tree = None

    variables = claim.get("variables")
    if not variables or not isinstance(variables, list) or len(variables) == 0:
        result.errors.append(f"{filename}: algorithm claim '{cid}' missing 'variables' (at least one required)")
    elif isinstance(variables, list):
        declared_names: set[str] = set()
        for var in variables:
            if isinstance(var, dict):
                var_concept = var.get("concept")
                if var_concept and var_concept not in concept_registry and concept_registry:
                    result.errors.append(
                        f"{filename}: algorithm claim '{cid}' variable references "
                        f"nonexistent concept '{var_concept}'")
                var_name = var.get("name") or var.get("symbol")
                if var_name:
                    declared_names.add(var_name)

        # Cross-check: warn about unbound names in body AST
        if body and tree is not None:
            ast_names = extract_names(tree)
            unbound = ast_names - KNOWN_BUILTINS - declared_names
            for name in sorted(unbound):
                result.warnings.append(
                    f"{filename}: algorithm claim '{cid}' body references "
                    f"name '{name}' not declared in variables")


def build_concept_registry_from_paths(
    concepts_dir: Path | KnowledgePath,
    forms_dir: Path | KnowledgePath,
) -> dict[str, dict]:
    """Load concepts and build a registry keyed by ID, canonical_name, and aliases.

    Claims can reference concepts by any of these keys.
    All keys point to the same enriched concept data dict.
    """
    concepts_root = coerce_knowledge_path(concepts_dir)
    forms_root = coerce_knowledge_path(forms_dir)
    concepts = load_concepts(concepts_root)
    return build_authored_concept_registry(concepts, forms_root)


def build_authored_concept_registry(
    concepts: list[LoadedEntry] | list[LoadedConcept],
    forms_dir: Path | KnowledgePath,
    *,
    require_form_definition: bool = True,
) -> dict[str, dict]:
    """Build the canonical authored-concept lookup used by validators/builders."""
    forms_root = coerce_knowledge_path(forms_dir)
    typed_concepts = (
        concepts
        if all(isinstance(concept, LoadedConcept) for concept in concepts)
        else normalize_loaded_concepts(concepts)
    )
    registry: dict[str, dict] = {}
    for concept in typed_concepts:
        record = concept.record
        enriched = record.to_payload()
        cid = str(record.artifact_id)
        enriched["_storage_id"] = cid
        # Load structured form definition
        form_def = load_form_path(forms_root, record.form)
        if record.form:
            if form_def is None:
                if require_form_definition:
                    raise ValueError(
                        f"concept '{cid}' references missing form definition '{record.form}'"
                    )
            else:
                enriched["_form_definition"] = form_def
        # Index by concept ID
        registry[cid] = enriched
        if concept.source_local_id and concept.source_local_id not in registry:
            registry[concept.source_local_id] = enriched
        # Index by canonical_name (claims can reference concepts by name)
        canonical = record.canonical_name
        if canonical not in registry:
            registry[canonical] = enriched
        for logical_id in record.logical_ids:
            if logical_id.formatted not in registry:
                registry[logical_id.formatted] = enriched
            if logical_id.value not in registry:
                registry[logical_id.value] = enriched
        # Index by aliases
        for alias in record.aliases:
            if alias.name not in registry:
                registry[alias.name] = enriched
    return registry


def build_concept_registry(repo: Repository | None) -> dict[str, dict]:
    """Load concepts and build {concept_id: concept_data} mapping.

    Args:
        repo: A Repository object providing the semantic tree.
    """
    if repo is None:
        return {}
    context = build_claim_compilation_context_from_repo(repo)
    from propstore.compiler.context import concept_registry_for_context

    return concept_registry_for_context(context)
