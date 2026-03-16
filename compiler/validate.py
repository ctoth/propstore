"""Concept file validator for the propstore concept registry.

Loads all concepts/*.yaml files, validates against the JSON Schema,
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

import jsonschema
import yaml

from compiler.cel_checker import (
    ConceptInfo,
    KindType,
    check_cel_expression,
)


@dataclass
class LoadedConcept:
    """A concept loaded from a YAML file, with its source filename."""
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


def load_concepts(concept_dir: Path) -> list[LoadedConcept]:
    """Load all .yaml files from the concept directory (excluding .counters)."""
    concepts = []
    for entry in sorted(concept_dir.iterdir()):
        if entry.is_file() and entry.suffix == ".yaml":
            with open(entry) as f:
                data = yaml.safe_load(f)
            concepts.append(LoadedConcept(
                filename=entry.stem,
                filepath=entry,
                data=data if data else {},
            ))
    return concepts


def _get_kind_type_from_form(concept_data: dict) -> KindType | None:
    """Derive the KindType from a concept's form field.

    Maps form names to KindType:
      - 'category' -> CATEGORY
      - 'structural' -> STRUCTURAL
      - 'boolean' -> BOOLEAN
      - everything else -> QUANTITY (measurable forms)
    """
    form = concept_data.get("form")
    if not form or not isinstance(form, str):
        return None
    if form == "category":
        return KindType.CATEGORY
    if form == "structural":
        return KindType.STRUCTURAL
    if form == "boolean":
        return KindType.BOOLEAN
    return KindType.QUANTITY


_CONCEPT_ID_RE = re.compile(r'^(?:concept\d+|[a-z]+_\d+)$')


def _get_id_prefix(concept_id: str) -> str | None:
    """Extract domain prefix from concept ID (e.g., 'speech' from 'speech_0012').

    Returns None for new-format IDs (concept1, concept42).
    """
    m = re.match(r'^([a-z]+)_\d+', concept_id)
    return m.group(1) if m else None


def _build_cel_registry(concepts: list[LoadedConcept]) -> dict[str, ConceptInfo]:
    """Build a concept registry for CEL type-checking from loaded concepts."""
    registry: dict[str, ConceptInfo] = {}
    for c in concepts:
        data = c.data
        cid = data.get("id", "")
        name = data.get("canonical_name", "")
        kind_type = _get_kind_type_from_form(data)
        if not name or kind_type is None:
            continue

        category_values: list[str] = []
        category_extensible = True
        if kind_type == KindType.CATEGORY:
            # Category values may be in form_parameters as structured data
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


VALID_RELATIONSHIP_TYPES = frozenset([
    "broader", "narrower", "related", "component_of",
    "derived_from", "contested_definition",
])


def _load_all_claim_ids(claims_dir: Path) -> set[str]:
    """Load all claim IDs from claim YAML files in the given directory."""
    claim_ids: set[str] = set()
    if not claims_dir.exists():
        return claim_ids
    for entry in sorted(claims_dir.iterdir()):
        if entry.is_file() and entry.suffix == ".yaml":
            with open(entry) as f:
                data = yaml.safe_load(f)
            if data and isinstance(data.get("claims"), list):
                for claim in data["claims"]:
                    cid = claim.get("id")
                    if cid:
                        claim_ids.add(cid)
    return claim_ids


def validate_concepts(
    concepts: list[LoadedConcept],
    claims_dir: Path | None = None,
) -> ValidationResult:
    """Run all compiler contract validation checks.

    Args:
        concepts: Loaded concept data from YAML files.
        claims_dir: Optional path to claims directory. When provided,
            canonical_claim references on parameterizations are validated
            against the claim IDs found in claim files.
    """
    result = ValidationResult()
    id_to_concept: dict[str, LoadedConcept] = {}
    cel_registry = _build_cel_registry(concepts)

    # Load claim IDs for canonical_claim validation
    all_claim_ids: set[str] = set()
    if claims_dir is not None:
        all_claim_ids = _load_all_claim_ids(claims_dir)

    for c in concepts:
        data = c.data

        # ── Required fields (basic) ─────────────────────────────
        cid = data.get("id")
        name = data.get("canonical_name")
        status = data.get("status")
        definition = data.get("definition")
        form = data.get("form")

        if not cid:
            result.errors.append(f"{c.filename}: missing required field 'id'")
            continue
        if not name:
            result.errors.append(f"{c.filename}: missing required field 'canonical_name'")
        if not status:
            result.errors.append(f"{c.filename}: missing required field 'status'")
        if not definition:
            result.errors.append(f"{c.filename}: missing required field 'definition'")
        if not form:
            result.errors.append(f"{c.filename}: missing required field 'form'")
        elif not isinstance(form, str):
            result.errors.append(f"{c.filename}: 'form' must be a string")
        else:
            # Check that a matching form file exists
            forms_dir = c.filepath.parent.parent / "forms"
            form_file = forms_dir / f"{form}.yaml"
            if not form_file.exists():
                result.errors.append(
                    f"{c.filename}: form '{form}' has no matching file at forms/{form}.yaml")

        # Validate form_parameters if present
        form_params = data.get("form_parameters")
        if form_params is not None and not isinstance(form_params, dict):
            result.errors.append(f"{c.filename}: 'form_parameters' must be a mapping")

        # Validate range if present
        range_val = data.get("range")
        if range_val is not None:
            if not isinstance(range_val, list):
                result.errors.append(f"{c.filename}: 'range' must be a list")
            elif not all(isinstance(v, (int, float)) for v in range_val):
                result.errors.append(f"{c.filename}: 'range' must contain only numbers")

        # ── ID uniqueness ───────────────────────────────────────
        if cid in id_to_concept:
            result.errors.append(
                f"{c.filename}: duplicate ID '{cid}' "
                f"(also in {id_to_concept[cid].filename})")
        else:
            id_to_concept[cid] = c

        # ── Canonical name matches filename ─────────────────────
        if name and name != c.filename:
            result.errors.append(
                f"{c.filename}: canonical_name '{name}' does not match filename '{c.filename}'")

        # ── ID prefix matches domain ────────────────────────────
        domain = data.get("domain")
        if domain and cid:
            prefix = _get_id_prefix(cid)
            if prefix and prefix != domain:
                result.errors.append(
                    f"{c.filename}: ID prefix '{prefix}' does not match domain '{domain}'")

        # ── Deprecated concepts must have replaced_by ───────────
        if status == "deprecated":
            replaced_by = data.get("replaced_by")
            if not replaced_by:
                result.errors.append(
                    f"{c.filename}: deprecated concept must have 'replaced_by'")

    # ── Cross-concept checks (need all concepts loaded) ─────────

    all_ids = set(id_to_concept.keys())

    for c in concepts:
        data = c.data
        cid = data.get("id", "")
        status = data.get("status")

        # ── replaced_by target exists and isn't deprecated ──────
        if status == "deprecated":
            replaced_by = data.get("replaced_by")
            if replaced_by:
                if replaced_by not in all_ids:
                    result.errors.append(
                        f"{c.filename}: replaced_by target '{replaced_by}' not found in registry")
                else:
                    target = id_to_concept[replaced_by]
                    if target.data.get("status") == "deprecated":
                        result.errors.append(
                            f"{c.filename}: replaced_by target '{replaced_by}' is itself deprecated")

        # ── Relationship targets exist ──────────────────────────
        for rel in data.get("relationships", []) or []:
            target = rel.get("target")

            # Validate relationship type
            rel_type = rel.get("type")
            if rel_type and rel_type not in VALID_RELATIONSHIP_TYPES:
                result.errors.append(
                    f"{c.filename}: invalid relationship type '{rel_type}'. "
                    f"Valid types: {', '.join(sorted(VALID_RELATIONSHIP_TYPES))}")

            if target and target not in all_ids:
                result.errors.append(
                    f"{c.filename}: relationship target '{target}' not found in registry")

            # contested_definition must have note
            if rel.get("type") == "contested_definition" and not rel.get("note"):
                result.errors.append(
                    f"{c.filename}: contested_definition relationship to '{target}' must have a note")

            # CEL conditions in relationships
            for cel_expr in rel.get("conditions", []) or []:
                cel_errors = check_cel_expression(cel_expr, cel_registry)
                for ce in cel_errors:
                    if ce.is_warning:
                        result.warnings.append(f"{c.filename}: CEL warning: {ce.message}")
                    else:
                        result.errors.append(f"{c.filename}: CEL error: {ce.message}")

        # ── Parameterization inputs ─────────────────────────────
        for param in data.get("parameterization_relationships", []) or []:
            inputs = param.get("inputs", [])
            for input_id in inputs:
                if input_id not in all_ids:
                    result.errors.append(
                        f"{c.filename}: parameterization input '{input_id}' not found in registry")
                else:
                    input_concept = id_to_concept[input_id]
                    input_kind = _get_kind_type_from_form(input_concept.data)
                    if input_kind and input_kind != KindType.QUANTITY:
                        result.errors.append(
                            f"{c.filename}: parameterization input '{input_id}' "
                            f"must be quantity kind (is {input_kind.value})")

            # conditional exactness must have conditions
            if param.get("exactness") == "conditional":
                conditions = param.get("conditions")
                if not conditions:
                    result.errors.append(
                        f"{c.filename}: parameterization with conditional exactness "
                        f"must have conditions")

            # CEL conditions in parameterizations
            for cel_expr in param.get("conditions", []) or []:
                cel_errors = check_cel_expression(cel_expr, cel_registry)
                for ce in cel_errors:
                    if ce.is_warning:
                        result.warnings.append(f"{c.filename}: CEL warning: {ce.message}")
                    else:
                        result.errors.append(f"{c.filename}: CEL error: {ce.message}")

            # canonical_claim must reference an existing claim
            canonical_claim = param.get("canonical_claim")
            if canonical_claim:
                if claims_dir is None:
                    # No claims_dir provided — can't validate, emit error
                    result.errors.append(
                        f"{c.filename}: canonical_claim '{canonical_claim}' "
                        f"cannot be validated (no claims directory provided)")
                elif canonical_claim not in all_claim_ids:
                    result.errors.append(
                        f"{c.filename}: canonical_claim '{canonical_claim}' "
                        f"not found in claim files")

            # Warning: missing sympy
            if not param.get("sympy"):
                result.warnings.append(
                    f"{c.filename}: parameterization relationship missing sympy expression")

    # ── Circular deprecation chains ─────────────────────────────
    for c in concepts:
        data = c.data
        if data.get("status") != "deprecated":
            continue
        visited = set()
        current_id = data.get("id")
        while current_id:
            if current_id in visited:
                result.errors.append(
                    f"{c.filename}: circular deprecation chain detected involving '{current_id}'")
                break
            visited.add(current_id)
            current_concept = id_to_concept.get(current_id)
            if not current_concept:
                break
            if current_concept.data.get("status") != "deprecated":
                break
            current_id = current_concept.data.get("replaced_by")

    return result


def _json_safe(obj):
    """Recursively convert date objects to ISO format strings for JSON Schema validation."""
    import datetime
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return obj


def main():
    """CLI entry point: validate concepts directory."""
    import argparse
    parser = argparse.ArgumentParser(description="Validate propstore concept files")
    parser.add_argument("concept_dir", nargs="?", default="concepts",
                        help="Path to concepts directory")
    args = parser.parse_args()

    concept_dir = Path(args.concept_dir)
    if not concept_dir.exists():
        print(f"ERROR: Concept directory '{concept_dir}' does not exist")
        sys.exit(1)

    concepts = load_concepts(concept_dir)
    if not concepts:
        print("No concept files found.")
        sys.exit(0)

    # Optionally validate against JSON Schema
    schema_path = Path(__file__).parent.parent / "schema" / "generated" / "concept_registry.schema.json"
    if schema_path.exists():
        with open(schema_path) as f:
            json_schema = json.load(f)
        for c in concepts:
            try:
                # Convert date objects to ISO strings for JSON Schema validation
                jsonschema.validate(_json_safe(c.data), json_schema)
            except jsonschema.ValidationError as e:
                print(f"JSON Schema ERROR in {c.filename}: {e.message}")

    result = validate_concepts(concepts)

    for w in result.warnings:
        print(f"WARNING: {w}")
    for e in result.errors:
        print(f"ERROR: {e}")

    if result.ok:
        print(f"\nValidation passed: {len(concepts)} concept(s), {len(result.warnings)} warning(s)")
    else:
        print(f"\nValidation FAILED: {len(result.errors)} error(s), {len(result.warnings)} warning(s)")

    sys.exit(0 if result.ok else 1)


if __name__ == "__main__":
    main()
