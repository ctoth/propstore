"""Concept file validator for the propstore concept registry.

Loads all concepts/*.yaml files and runs structural validation via Python
code (required fields, valid types, cross-reference checks). There is no
JSON Schema validation in this module.

Reports errors (hard stop) and warnings separately.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from bridgman import mul_dims, div_dims, dims_equal, format_dims
from bridgman import verify_expr, dims_of_expr, DimensionalError

from propstore.cel_checker import (
    ConceptInfo,
    KindType,
    build_cel_registry_from_loaded,
    check_cel_expression,
)
from propstore.form_utils import kind_type_from_form_name, load_form_path

if TYPE_CHECKING:
    from propstore.cli.repository import Repository
    from propstore.knowledge_path import KnowledgePath

from propstore.knowledge_path import coerce_knowledge_path
from propstore.loaded import LoadedEntry


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def load_yaml_dir(directory: Path) -> list[tuple[str, Path, dict]]:
    """Load all .yaml files from a directory, sorted by filename.

    Returns a list of (stem, filepath, data) tuples.
    Empty YAML files produce an empty dict.
    """
    results: list[tuple[str, Path, dict]] = []
    for entry in sorted(directory.iterdir()):
        if entry.is_file() and entry.suffix == ".yaml":
            with open(entry, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            results.append((entry.stem, entry, data if data else {}))
    return results


def load_yaml_entries(root: KnowledgePath | Path | None) -> list[LoadedEntry]:
    """Load all YAML entries from a knowledge-tree subtree."""
    if root is None:
        return []
    subtree = coerce_knowledge_path(root)
    if not subtree.is_dir():
        return []
    results: list[LoadedEntry] = []
    for entry in subtree.iterdir():
        if entry.is_file() and entry.suffix == ".yaml":
            data = yaml.safe_load(entry.read_bytes())
            results.append(
                LoadedEntry(filename=entry.stem, source_path=entry, data=data if data else {})
            )
    return results


def load_concepts(concepts_root: KnowledgePath | Path | None) -> list[LoadedEntry]:
    """Load all concept YAML files from a concept subtree."""
    return load_yaml_entries(concepts_root)


_CONCEPT_ID_RE = re.compile(r'^concept\d+$')




VALID_RELATIONSHIP_TYPES = frozenset([
    "broader", "narrower", "related", "component_of",
    "derived_from", "contested_definition",
])


def _load_all_claim_ids(claims_dir: KnowledgePath | Path | None) -> set[str]:
    """Load all claim IDs from claim YAML files in the given directory."""
    claim_ids: set[str] = set()
    for claim_file in load_yaml_entries(claims_dir):
        data = claim_file.data
        if isinstance(data.get("claims"), list):
            for claim in data["claims"]:
                cid = claim.get("id")
                if cid:
                    claim_ids.add(cid)
    return claim_ids


def validate_concepts(
    concepts: list[LoadedEntry],
    claims_dir: KnowledgePath | Path | None = None,
    *,
    repo: Repository | None = None,
) -> ValidationResult:
    """Run all compiler contract validation checks.

    Args:
        concepts: Loaded concept data from YAML files.
        claims_dir: Optional path to claims directory. When provided,
            canonical_claim references on parameterizations are validated
            against the claim IDs found in claim files.
        repo: A Repository object. When provided, forms_dir is resolved
            from repo instead of inferred from concept file paths.
    """
    result = ValidationResult()
    id_to_concept: dict[str, LoadedEntry] = {}
    cel_registry = build_cel_registry_from_loaded(concepts)

    def _forms_dir(c: LoadedEntry) -> KnowledgePath:
        if repo is not None:
            return repo.tree() / "forms"
        if c.source_path is None:
            raise TypeError(
                "validate_concepts requires source paths when repo is not provided"
            )
        return c.source_path.parent.parent / "forms"

    def _effective_dims(form_def) -> dict[str, int] | None:
        if form_def.dimensions is not None:
            return dict(form_def.dimensions)
        return {} if form_def.is_dimensionless else None

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
            forms_dir = _forms_dir(c)
            form_file = forms_dir / f"{form}.yaml"
            if not form_file.exists():
                result.errors.append(
                    f"{c.filename}: form '{form}' has no matching file at forms/{form}.yaml")

        # Validate form_parameters if present
        form_params = data.get("form_parameters")
        if form_params is not None and not isinstance(form_params, dict):
            result.errors.append(f"{c.filename}: 'form_parameters' must be a mapping")

        # ── Form-aware parameter validation ──────────────────────
        if isinstance(form, str) and form:
            forms_dir = _forms_dir(c)
            form_def = load_form_path(forms_dir, form)
            if form_def is not None:
                # Category concepts must have values in form_parameters
                if form == "category":
                    fp = form_params if isinstance(form_params, dict) else {}
                    if not isinstance(fp.get("values"), list):
                        result.errors.append(
                            f"{c.filename}: category concept must have "
                            f"form_parameters with a 'values' list")

                # Check form_parameters keys against form's declared parameters
                if form_def.parameters and isinstance(form_params, dict):
                    declared_keys = set(form_def.parameters.keys())
                    provided_keys = set(form_params.keys())
                    unexpected = provided_keys - declared_keys
                    for key in sorted(unexpected):
                        result.warnings.append(
                            f"{c.filename}: form_parameter '{key}' is not "
                            f"declared in form '{form}' "
                            f"(expected: {sorted(declared_keys)})")

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

        # ── ID format ─────────────────────────────────────────────
        if cid and not _CONCEPT_ID_RE.match(cid):
            result.errors.append(
                f"{c.filename}: concept ID '{cid}' does not match required format conceptN (e.g. concept1, concept42)")

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
                if input_id == cid:
                    result.errors.append(
                        f"{c.filename}: parameterization input '{input_id}' "
                        f"cannot reference the concept being defined")
                    continue
                if input_id not in all_ids:
                    result.errors.append(
                        f"{c.filename}: parameterization input '{input_id}' not found in registry")
                else:
                    input_concept = id_to_concept[input_id]
                    input_kind = kind_type_from_form_name(input_concept.data.get("form"))
                    if input_kind and input_kind != KindType.QUANTITY:
                        result.errors.append(
                            f"{c.filename}: parameterization input '{input_id}' "
                            f"must be quantity kind (is {input_kind.value})")

            # ── Dimensional compatibility (bridgman) ─────────────
            forms_dir = _forms_dir(c)
            output_form_def = load_form_path(forms_dir, data.get("form"))
            if output_form_def is not None and len(inputs) >= 2:
                input_form_defs = []
                for inp_id in inputs:
                    inp_c = id_to_concept.get(inp_id)
                    if inp_c is not None:
                        inp_fd = load_form_path(forms_dir, inp_c.data.get("form"))
                        if inp_fd is not None:
                            input_form_defs.append(inp_fd)
                if len(input_form_defs) == len(inputs) and input_form_defs:
                    input_dims = [_effective_dims(fd) for fd in input_form_defs]
                    output_dims = _effective_dims(output_form_def)
                    concrete_input_dims = [dims for dims in input_dims if dims is not None]
                    if output_dims is not None and len(concrete_input_dims) == len(input_dims):
                        # ── Sympy-based dimensional verification ───────
                        # If the parameterization has a sympy expression,
                        # use bridgman's tree-walking verifier (handles
                        # powers, roots, and arbitrary expressions).
                        sympy_expr_str = param.get("sympy")
                        sympy_verified = False
                        if sympy_expr_str:
                            try:
                                import sympy as sp
                                parsed = sp.sympify(sympy_expr_str)
                                # Build dim_map: concept ID -> dimensions
                                dim_map: dict[str, dict[str, int]] = {}
                                # Output concept
                                dim_map[cid] = dict(output_dims)
                                # Input concepts
                                for inp_id, input_dims_map in zip(inputs, concrete_input_dims):
                                    dim_map[inp_id] = dict(input_dims_map)
                                if verify_expr(parsed, dim_map):
                                    sympy_verified = True
                                else:
                                    # Sympy says dimensions don't match
                                    input_strs = [
                                        f"'{fd.name}' {format_dims(fd.dimensions)}"
                                        for fd in input_form_defs
                                    ]
                                    result.warnings.append(
                                        f"{c.filename}: sympy dimensional verification "
                                        f"failed for '{sympy_expr_str}': inputs "
                                        f"[{', '.join(input_strs)}] → output "
                                        f"'{output_form_def.name}' {format_dims(output_dims)}")
                                    sympy_verified = True  # skip brute-force, sympy gave definitive answer
                            except (DimensionalError, KeyError, TypeError, SyntaxError):
                                pass  # fall through to brute-force check

                        if not sympy_verified:
                            # Brute-force: try all mul/div combinations
                            # for the N-1 operations between inputs
                            ops = [mul_dims, div_dims]
                            found_valid = False
                            for op_combo in product(ops, repeat=len(concrete_input_dims) - 1):
                                result_dims = concrete_input_dims[0]
                                for op, next_dims in zip(op_combo, concrete_input_dims[1:]):
                                    result_dims = op(result_dims, next_dims)
                                if dims_equal(result_dims, output_dims):
                                    found_valid = True
                                    break
                            if not found_valid:
                                input_strs = [
                                    f"'{fd.name}' {format_dims(fd.dimensions)}"
                                    for fd in input_form_defs
                                ]
                                result.warnings.append(
                                    f"{c.filename}: no combination of mul/div on inputs "
                                    f"[{', '.join(input_strs)}] produces output "
                                    f"'{output_form_def.name}' {format_dims(output_dims)} — "
                                    f"dimensional mismatch")
                    else:
                        # Fall back to name-based heuristic when dimensions
                        # are missing from any form
                        input_form_names = [fd.name for fd in input_form_defs]
                        unique_input_forms = set(input_form_names)
                        if (len(unique_input_forms) == 1
                                and input_form_names[0] != output_form_def.name):
                            result.warnings.append(
                                f"{c.filename}: all inputs share form '{input_form_names[0]}' "
                                f"but output has form '{output_form_def.name}' — "
                                f"possible dimensional mismatch")
                        elif (len(unique_input_forms) > 1
                              and not output_form_def.is_dimensionless):
                            result.warnings.append(
                                f"{c.filename}: inputs have mixed forms "
                                f"{sorted(unique_input_forms)} but output form "
                                f"'{output_form_def.name}' is not dimensionless — "
                                f"possible dimensional mismatch")

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
