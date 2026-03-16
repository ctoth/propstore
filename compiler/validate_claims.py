"""Claim file validator for the propstore propositional knowledge store.

Loads all claims/*.yaml files, validates against the JSON Schema,
then runs the compiler contract checks that JSON Schema can't express.

Reports errors (hard stop) and warnings separately.
Exits nonzero on any error.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from compiler.cel_checker import (
    ConceptInfo,
    KindType,
    check_cel_expression,
)
from compiler.form_utils import (
    allowed_units_from_form_definition,
    json_safe,
    kind_type_from_form_name,
    load_form_definition,
)


@dataclass
class LoadedClaimFile:
    """A claim file loaded from YAML, with its source filename."""
    filename: str  # just the stem, no extension
    filepath: Path
    data: dict


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def load_claim_files(claims_dir: Path) -> list[LoadedClaimFile]:
    """Load all .yaml files from claims directory (excluding .counters)."""
    files = []
    for entry in sorted(claims_dir.iterdir()):
        if entry.is_file() and entry.suffix == ".yaml":
            with open(entry) as f:
                data = yaml.safe_load(f)
            files.append(LoadedClaimFile(
                filename=entry.stem,
                filepath=entry,
                data=data if data else {},
            ))
    return files


def _build_cel_registry_from_concepts(concept_registry: dict[str, dict]) -> dict[str, ConceptInfo]:
    """Build a CEL type-checking registry from concept data dicts.

    Maps canonical_name -> ConceptInfo, since CEL expressions use concept names.
    """
    registry: dict[str, ConceptInfo] = {}
    for cid, data in concept_registry.items():
        name = data.get("canonical_name", "")
        kind_type = kind_type_from_form_name(data.get("form"))
        if not name or kind_type is None:
            continue

        category_values: list[str] = []
        category_extensible = True
        if kind_type == KindType.CATEGORY:
            fp = data.get("form_parameters", {}) or {}
            if isinstance(fp.get("values"), list):
                category_values = fp["values"]
            ext = fp.get("extensible")
            category_extensible = ext if ext is not None else True

        registry[name] = ConceptInfo(
            id=cid,
            canonical_name=name,
            kind=kind_type,
            category_values=category_values,
            category_extensible=category_extensible,
        )
    return registry


_CLAIM_ID_RE = re.compile(r'^claim\d+$')


def validate_claims(
    claim_files: list[LoadedClaimFile],
    concept_registry: dict[str, dict],
) -> ValidationResult:
    """Validate claim files against schema and compiler contract.

    Args:
        claim_files: loaded claim YAML files
        concept_registry: mapping from concept ID to concept data dict
    """
    result = ValidationResult()
    cel_registry = _build_cel_registry_from_concepts(concept_registry)

    # JSON Schema validation
    schema_path = Path(__file__).parent.parent / "schema" / "generated" / "claim.schema.json"
    json_schema = None
    if schema_path.exists():
        with open(schema_path) as f:
            json_schema = json.load(f)

    seen_ids: dict[str, str] = {}  # claim_id -> filename

    for cf in claim_files:
        data = cf.data

        # JSON Schema validation
        if json_schema is not None:
            try:
                jsonschema.validate(json_safe(data), json_schema)
            except jsonschema.ValidationError as e:
                result.errors.append(f"{cf.filename}: JSON Schema error: {e.message}")

        claims = data.get("claims", [])
        if not isinstance(claims, list):
            result.errors.append(f"{cf.filename}: 'claims' must be a list")
            continue

        for claim in claims:
            if not isinstance(claim, dict):
                result.errors.append(f"{cf.filename}: claim must be a dict")
                continue

            cid = claim.get("id")
            ctype = claim.get("type")

            if not cid:
                result.errors.append(f"{cf.filename}: claim missing 'id'")
                continue

            # ── Claim ID format ──────────────────────────────
            if not _CLAIM_ID_RE.match(cid):
                result.errors.append(
                    f"{cf.filename}: claim ID '{cid}' does not match required format claimN (e.g. claim1, claim42)")

            # ── Claim ID uniqueness ──────────────────────────
            if cid in seen_ids:
                result.errors.append(
                    f"{cf.filename}: duplicate claim ID '{cid}' "
                    f"(also in {seen_ids[cid]})")
            else:
                seen_ids[cid] = cf.filename

            # ── Provenance ───────────────────────────────────
            prov = claim.get("provenance")
            if not prov or not isinstance(prov, dict):
                result.errors.append(f"{cf.filename}: claim '{cid}' missing provenance")
            else:
                if not prov.get("paper"):
                    result.errors.append(
                        f"{cf.filename}: claim '{cid}' provenance missing 'paper'")
                if prov.get("page") is None:
                    result.errors.append(
                        f"{cf.filename}: claim '{cid}' provenance missing 'page'")

            # ── CEL conditions ───────────────────────────────
            conditions = claim.get("conditions")
            if conditions and isinstance(conditions, list):
                for cel_expr in conditions:
                    if isinstance(cel_expr, str):
                        cel_errors = check_cel_expression(cel_expr, cel_registry)
                        for ce in cel_errors:
                            if ce.is_warning:
                                result.warnings.append(
                                    f"{cf.filename}: claim '{cid}' CEL warning: {ce.message}")
                            else:
                                result.errors.append(
                                    f"{cf.filename}: claim '{cid}' CEL error: {ce.message}")

            # ── Type-specific validation ─────────────────────
            if ctype == "parameter":
                _validate_parameter(claim, cid, cf.filename, concept_registry, result)
            elif ctype == "equation":
                _validate_equation(claim, cid, cf.filename, concept_registry, result)
            elif ctype == "observation":
                _validate_observation(claim, cid, cf.filename, concept_registry, result)
            elif ctype == "model":
                _validate_model(claim, cid, cf.filename, concept_registry, result)
            elif ctype == "measurement":
                _validate_measurement(claim, cid, cf.filename, concept_registry, result)

    return result


def _validate_parameter(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], result: ValidationResult,
) -> None:
    concept_data: dict[str, Any] | None = None
    concept = claim.get("concept")
    if not concept:
        result.errors.append(f"{filename}: parameter claim '{cid}' missing 'concept'")
    elif concept not in concept_registry:
        result.errors.append(
            f"{filename}: parameter claim '{cid}' references nonexistent concept '{concept}'")
    else:
        concept_data = concept_registry[concept]

    # Value semantics: at least one of value or lower_bound+upper_bound must be present
    value = claim.get("value")
    lower_bound = claim.get("lower_bound")
    upper_bound = claim.get("upper_bound")

    has_value = value is not None
    has_lower = lower_bound is not None
    has_upper = upper_bound is not None

    if not has_value and not has_lower and not has_upper:
        result.errors.append(
            f"{filename}: parameter claim '{cid}' missing 'value' "
            f"(must have value or lower_bound+upper_bound)")

    # Bounds must come in pairs
    if has_lower and not has_upper:
        result.errors.append(
            f"{filename}: parameter claim '{cid}' has lower_bound without upper_bound")
    if has_upper and not has_lower:
        result.errors.append(
            f"{filename}: parameter claim '{cid}' has upper_bound without lower_bound")

    # Bound ordering
    if has_lower and has_upper:
        try:
            if float(lower_bound) > float(upper_bound):
                result.errors.append(
                    f"{filename}: parameter claim '{cid}' lower_bound > upper_bound")
        except (TypeError, ValueError):
            pass

    # Uncertainty must come with type and vice versa
    uncertainty = claim.get("uncertainty")
    uncertainty_type = claim.get("uncertainty_type")
    has_uncertainty = uncertainty is not None
    has_uncertainty_type = uncertainty_type is not None

    if has_uncertainty_type and not has_uncertainty:
        result.errors.append(
            f"{filename}: parameter claim '{cid}' has uncertainty_type without uncertainty")
    if has_uncertainty and not has_uncertainty_type:
        result.errors.append(
            f"{filename}: parameter claim '{cid}' has uncertainty without uncertainty_type")

    # Uncertainty must be non-negative
    if has_uncertainty:
        try:
            if float(uncertainty) < 0:
                result.errors.append(
                    f"{filename}: parameter claim '{cid}' uncertainty must be >= 0")
        except (TypeError, ValueError):
            pass

    unit = claim.get("unit")
    if not unit:
        result.errors.append(f"{filename}: parameter claim '{cid}' missing 'unit'")
    elif concept_data is not None:
        allowed_units = concept_data.get("_allowed_units") or []
        if allowed_units and unit not in allowed_units:
            result.errors.append(
                f"{filename}: parameter claim '{cid}' unit '{unit}' does not match "
                f"concept '{concept}' allowed units {sorted(allowed_units)}")


def _validate_equation(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], result: ValidationResult,
) -> None:
    expression = claim.get("expression")
    if not expression:
        result.errors.append(f"{filename}: equation claim '{cid}' missing 'expression'")

    # Validate explicit sympy field if provided; warn if auto-generation fails when absent
    from compiler.sympy_generator import generate_sympy
    sympy_field = claim.get("sympy")
    if sympy_field:
        # Use generate_sympy for validation — it handles = and ^ preprocessing
        if generate_sympy(sympy_field) is None:
            result.errors.append(
                f"{filename}: equation claim '{cid}' has invalid 'sympy' field: "
                f"cannot parse '{sympy_field}'")
    elif expression:
        generated = generate_sympy(expression)
        if generated is None:
            result.warnings.append(
                f"{filename}: equation claim '{cid}' could not auto-generate sympy "
                f"from expression '{expression}'")

    variables = claim.get("variables")
    if not variables or not isinstance(variables, list) or len(variables) == 0:
        result.errors.append(f"{filename}: equation claim '{cid}' missing 'variables' (at least one required)")
    elif isinstance(variables, list):
        for var in variables:
            if isinstance(var, dict):
                var_concept = var.get("concept")
                if var_concept and var_concept not in concept_registry:
                    result.errors.append(
                        f"{filename}: equation claim '{cid}' variable references "
                        f"nonexistent concept '{var_concept}'")


def _validate_observation(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], result: ValidationResult,
) -> None:
    statement = claim.get("statement")
    if not statement:
        result.errors.append(f"{filename}: observation claim '{cid}' missing 'statement'")

    concepts = claim.get("concepts")
    if not concepts or not isinstance(concepts, list) or len(concepts) == 0:
        result.errors.append(f"{filename}: observation claim '{cid}' missing 'concepts' (at least one required)")
    elif isinstance(concepts, list):
        for concept_id in concepts:
            if concept_id not in concept_registry:
                result.errors.append(
                    f"{filename}: observation claim '{cid}' references "
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
                if param_concept and param_concept not in concept_registry:
                    result.errors.append(
                        f"{filename}: model claim '{cid}' parameter references "
                        f"nonexistent concept '{param_concept}'")


_VALID_MEASURE_TYPES = {
    "jnd_absolute", "jnd_relative", "discrimination_threshold",
    "preference_rating", "detection_threshold", "correlation", "effect_size",
}


def _validate_measurement(
    claim: dict, cid: str, filename: str,
    concept_registry: dict[str, dict], result: ValidationResult,
) -> None:
    target_concept = claim.get("target_concept")
    if not target_concept:
        result.errors.append(f"{filename}: measurement claim '{cid}' missing 'target_concept'")
    elif target_concept not in concept_registry:
        result.errors.append(
            f"{filename}: measurement claim '{cid}' references nonexistent concept '{target_concept}'")

    measure = claim.get("measure")
    if not measure:
        result.errors.append(f"{filename}: measurement claim '{cid}' missing 'measure'")
    elif measure not in _VALID_MEASURE_TYPES:
        result.errors.append(
            f"{filename}: measurement claim '{cid}' invalid measure type '{measure}'")

    # Value semantics: same as parameter claims
    value = claim.get("value")
    lower_bound = claim.get("lower_bound")
    upper_bound = claim.get("upper_bound")

    has_value = value is not None
    has_lower = lower_bound is not None
    has_upper = upper_bound is not None

    if not has_value and not has_lower and not has_upper:
        result.errors.append(
            f"{filename}: measurement claim '{cid}' missing 'value' "
            f"(must have value or lower_bound+upper_bound)")

    # Bounds must come in pairs
    if has_lower and not has_upper:
        result.errors.append(
            f"{filename}: measurement claim '{cid}' has lower_bound without upper_bound")
    if has_upper and not has_lower:
        result.errors.append(
            f"{filename}: measurement claim '{cid}' has upper_bound without lower_bound")

    # Bound ordering
    if has_lower and has_upper:
        try:
            if float(lower_bound) > float(upper_bound):
                result.errors.append(
                    f"{filename}: measurement claim '{cid}' lower_bound > upper_bound")
        except (TypeError, ValueError):
            pass

    # Uncertainty must come with type and vice versa
    uncertainty = claim.get("uncertainty")
    uncertainty_type = claim.get("uncertainty_type")
    has_uncertainty = uncertainty is not None
    has_uncertainty_type = uncertainty_type is not None

    if has_uncertainty_type and not has_uncertainty:
        result.errors.append(
            f"{filename}: measurement claim '{cid}' has uncertainty_type without uncertainty")
    if has_uncertainty and not has_uncertainty_type:
        result.errors.append(
            f"{filename}: measurement claim '{cid}' has uncertainty without uncertainty_type")

    # Uncertainty must be non-negative
    if has_uncertainty:
        try:
            if float(uncertainty) < 0:
                result.errors.append(
                    f"{filename}: measurement claim '{cid}' uncertainty must be >= 0")
        except (TypeError, ValueError):
            pass

    unit = claim.get("unit")
    if not unit:
        result.errors.append(f"{filename}: measurement claim '{cid}' missing 'unit'")


def build_concept_registry(concepts_dir: Path) -> dict[str, dict]:
    """Load concepts and build {concept_id: concept_data} mapping."""
    from compiler.validate import load_concepts
    forms_dir = concepts_dir.parent / "forms"
    concepts = load_concepts(concepts_dir)
    registry: dict[str, dict] = {}
    for concept in concepts:
        cid = concept.data.get("id")
        if not cid:
            continue
        enriched = dict(concept.data)
        form_definition = load_form_definition(forms_dir, enriched.get("form"))
        allowed_units = sorted(allowed_units_from_form_definition(form_definition))
        if allowed_units:
            enriched["_allowed_units"] = allowed_units
        registry[cid] = enriched
    return registry


def main():
    """CLI entry point: validate claim files."""
    import argparse
    parser = argparse.ArgumentParser(description="Validate propstore claim files")
    parser.add_argument("claims_dir", nargs="?", default="claims",
                        help="Path to claims directory")
    parser.add_argument("--concepts-dir", default="concepts",
                        help="Path to concepts directory (for reference checking)")
    args = parser.parse_args()

    claims_dir = Path(args.claims_dir)
    if not claims_dir.exists():
        print(f"ERROR: Claims directory '{claims_dir}' does not exist")
        sys.exit(1)

    concepts_dir = Path(args.concepts_dir)
    if not concepts_dir.exists():
        print(f"ERROR: Concepts directory '{concepts_dir}' does not exist")
        sys.exit(1)

    claim_files = load_claim_files(claims_dir)
    if not claim_files:
        print("No claim files found.")
        sys.exit(0)

    concept_registry = build_concept_registry(concepts_dir)

    # JSON Schema validation
    schema_path = Path(__file__).parent.parent / "schema" / "generated" / "claim.schema.json"
    if schema_path.exists():
        with open(schema_path) as f:
            json_schema = json.load(f)
        for cf in claim_files:
            try:
                jsonschema.validate(json_safe(cf.data), json_schema)
            except jsonschema.ValidationError as e:
                print(f"JSON Schema ERROR in {cf.filename}: {e.message}")

    result = validate_claims(claim_files, concept_registry)

    for w in result.warnings:
        print(f"WARNING: {w}")
    for e in result.errors:
        print(f"ERROR: {e}")

    if result.ok:
        print(f"\nValidation passed: {len(claim_files)} claim file(s), {len(result.warnings)} warning(s)")
    else:
        print(f"\nValidation FAILED: {len(result.errors)} error(s), {len(result.warnings)} warning(s)")

    sys.exit(0 if result.ok else 1)


if __name__ == "__main__":
    main()
