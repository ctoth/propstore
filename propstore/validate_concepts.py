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
from typing import TYPE_CHECKING, Mapping

from bridgman import mul_dims, div_dims, dims_equal, format_dims
from bridgman import verify_expr, dims_of_expr, DimensionalError

from quire.documents import load_document_dir
from propstore.families.documents.claims import ClaimsFileDocument
from propstore.cel_checker import ConceptInfo, KindType, check_cel_expr
from propstore.cel_registry import build_canonical_cel_registry
from propstore.identity import normalize_canonical_concept_payload
from propstore.core.concept_status import ConceptStatus
from propstore.core.concept_relationship_types import (
    ConceptRelationshipType,
    VALID_CONCEPT_RELATIONSHIP_TYPES,
)
from propstore.form_utils import FormDefinition, kind_type_from_form_name, load_form_path
from propstore.identity import (
    CONCEPT_ARTIFACT_ID_RE,
    CONCEPT_VERSION_ID_RE,
    LOGICAL_NAMESPACE_RE,
    LOGICAL_VALUE_RE,
    compute_concept_version_id,
    format_logical_id,
)
from propstore.core.concepts import (
    LoadedConcept,
    concept_document_to_payload,
    load_concepts,
    normalize_loaded_concepts,
)
from propstore.compiler.references import build_claim_reference_lookup
from propstore.diagnostics import ValidationResult

if TYPE_CHECKING:
    from quire.tree_path import TreePath as KnowledgePath



VALID_RELATIONSHIP_TYPES = VALID_CONCEPT_RELATIONSHIP_TYPES
_QUALIA_ROLE_NAMES = ("formal", "constitutive", "telic", "agentive")
_TYPE_RELATIONSHIPS = {
    ConceptRelationshipType.IS_A,
    ConceptRelationshipType.KIND_OF,
}


def _concept_reference_keys(concept: LoadedConcept) -> set[str]:
    keys = set(concept.record.reference_keys())
    if concept.source_local_id:
        keys.add(concept.source_local_id)
    document = concept.document
    if document is not None:
        keys.add(document.ontology_reference.uri)
        for sense in document.lexical_entry.senses:
            keys.add(sense.reference.uri)
    return {key for key in keys if key}


def _concept_reference_index(concepts: list[LoadedConcept]) -> dict[str, LoadedConcept]:
    index: dict[str, LoadedConcept] = {}
    for concept in concepts:
        for key in _concept_reference_keys(concept):
            index.setdefault(key, concept)
    return index


def _concept_satisfies_type(
    concept: LoadedConcept,
    required_reference: str,
    reference_index: dict[str, LoadedConcept],
) -> bool:
    if required_reference in _concept_reference_keys(concept):
        return True
    for relationship in concept.record.relationships:
        if relationship.relationship_type not in _TYPE_RELATIONSHIPS:
            continue
        target = str(relationship.target)
        if target == required_reference:
            return True
        target_concept = reference_index.get(target)
        if target_concept is not None and required_reference in _concept_reference_keys(target_concept):
            return True
    return False


def _validate_reference_exists(
    concept: LoadedConcept,
    *,
    field: str,
    reference_uri: str,
    reference_index: dict[str, LoadedConcept],
    result: ValidationResult,
) -> LoadedConcept | None:
    target = reference_index.get(reference_uri)
    if target is None:
        result.errors.append(
            f"{concept.filename}: {field} reference '{reference_uri}' not found in registry"
        )
    return target


def _validate_phase3_lemon_references(
    concept: LoadedConcept,
    *,
    reference_index: dict[str, LoadedConcept],
    result: ValidationResult,
) -> None:
    document = concept.document
    if document is None:
        return

    for sense in document.lexical_entry.senses:
        qualia = sense.qualia
        if qualia is not None:
            for role_name in _QUALIA_ROLE_NAMES:
                for qualia_reference in getattr(qualia, role_name):
                    target = _validate_reference_exists(
                        concept,
                        field=f"qualia.{role_name}",
                        reference_uri=qualia_reference.reference.uri,
                        reference_index=reference_index,
                        result=result,
                    )
                    type_constraint = qualia_reference.type_constraint
                    if type_constraint is None:
                        continue
                    required_uri = type_constraint.reference.uri
                    required = _validate_reference_exists(
                        concept,
                        field=f"qualia.{role_name}.type_constraint",
                        reference_uri=required_uri,
                        reference_index=reference_index,
                        result=result,
                    )
                    if target is not None and required is not None and not _concept_satisfies_type(
                        target,
                        required_uri,
                        reference_index,
                    ):
                        result.errors.append(
                            f"{concept.filename}: qualia.{role_name} reference "
                            f"'{qualia_reference.reference.uri}' does not satisfy "
                            f"type constraint '{required_uri}'"
                        )

        description_kind = sense.description_kind
        if description_kind is None:
            continue
        _validate_reference_exists(
            concept,
            field="description_kind",
            reference_uri=description_kind.reference.uri,
            reference_index=reference_index,
            result=result,
        )
        for slot in description_kind.slots:
            _validate_reference_exists(
                concept,
                field=f"description_kind.slot.{slot.name}.type_constraint",
                reference_uri=slot.type_constraint.uri,
                reference_index=reference_index,
                result=result,
            )


def _validate_lemon_document(
    concept: LoadedConcept,
    *,
    result: ValidationResult,
) -> None:
    document = concept.document
    if document is None:
        return

    entry = document.lexical_entry
    ontology_uri = document.ontology_reference.uri
    sense_uris: set[str] = set()
    for sense in entry.senses:
        reference_uri = sense.reference.uri
        if reference_uri in sense_uris:
            result.errors.append(
                f"{concept.filename}: duplicate lexical sense reference '{reference_uri}'"
            )
        sense_uris.add(reference_uri)

    if ontology_uri not in sense_uris:
        result.errors.append(
            f"{concept.filename}: ontology_reference '{ontology_uri}' must have a matching lexical sense"
        )


def _load_claim_reference_lookup(
    claims_dir: KnowledgePath | None,
) -> Mapping[str, tuple[str, ...]]:
    """Load claim artifact and logical reference keys from claim YAML files."""
    if claims_dir is None:
        return {}
    return build_claim_reference_lookup(
        list(load_document_dir(claims_dir, ClaimsFileDocument))
    )


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
            f"{filename}: concept '{artifact_id}' must define a non-empty logical_ids list"
        )
        return formatted_ids

    for index, entry in enumerate(logical_ids, start=1):
        if not isinstance(entry, dict):
            result.errors.append(
                f"{filename}: concept '{artifact_id}' logical_ids entry #{index} must be a mapping"
            )
            continue

        namespace = entry.get("namespace")
        value = entry.get("value")
        if not isinstance(namespace, str) or not LOGICAL_NAMESPACE_RE.match(namespace):
            result.errors.append(
                f"{filename}: concept '{artifact_id}' logical_ids entry #{index} "
                f"uses invalid namespace {namespace!r}"
            )
            continue
        if not isinstance(value, str) or not LOGICAL_VALUE_RE.match(value):
            result.errors.append(
                f"{filename}: concept '{artifact_id}' logical_ids entry #{index} "
                f"uses invalid value {value!r}"
            )
            continue

        formatted = format_logical_id(entry)
        if formatted is None:
            result.errors.append(
                f"{filename}: concept '{artifact_id}' logical_ids entry #{index} "
                "must serialize as namespace:value"
            )
            continue
        if formatted in formatted_ids:
            result.errors.append(
                f"{filename}: concept '{artifact_id}' duplicates logical ID '{formatted}'"
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


def normalize_concept_record(data: dict) -> dict:
    from propstore.core.concepts import normalize_concept_payload

    return normalize_concept_payload(data)


def validate_concepts(
    concepts: list[LoadedConcept],
    claims_dir: KnowledgePath | None = None,
    *,
    forms_dir: KnowledgePath | None = None,
    form_registry: Mapping[str, FormDefinition] | None = None,
    claim_reference_lookup: Mapping[str, tuple[str, ...]] | None = None,
) -> ValidationResult:
    """Run all compiler contract validation checks.

    Args:
        concepts: Loaded concept data from YAML files.
        claims_dir: Optional path to claims directory. When provided,
            canonical_claim references on parameterizations are validated
            against the claim IDs found in claim files.
        form_registry: Preloaded form definitions. Repository workflows pass
            this instead of loading from a forms directory.
        claim_reference_lookup: Preloaded claim reference lookup. Repository
            workflows pass this instead of enumerating a claims directory.
        forms_dir: Optional explicit forms root. When omitted, concepts must
            carry ``knowledge_root`` metadata so the validator can resolve
            ``knowledge_root / "forms"`` without guessing from local paths.
    """
    result = ValidationResult()
    id_to_concept: dict[str, LoadedConcept] = {}
    seen_logical_ids: dict[str, str] = {}
    cel_registry: dict[str, ConceptInfo] | None = None

    def _forms_dir(c: LoadedConcept) -> KnowledgePath:
        if forms_dir is not None:
            return forms_dir
        if c.knowledge_root is None:
            raise TypeError(
                "validate_concepts requires forms_dir or knowledge_root metadata"
            )
        return c.knowledge_root / "forms"

    def _form_definition(c: LoadedConcept, form_name: object) -> FormDefinition | None:
        if not isinstance(form_name, str) or not form_name:
            return None
        if form_registry is not None:
            return form_registry.get(form_name)
        return load_form_path(_forms_dir(c), form_name)

    def _form_exists(c: LoadedConcept, form_name: object) -> bool:
        if not isinstance(form_name, str) or not form_name:
            return False
        if form_registry is not None:
            return form_name in form_registry
        forms_root = _forms_dir(c)
        return (forms_root / f"{form_name}.yaml").exists()

    def _effective_dims(form_def) -> dict[str, int] | None:
        if form_def.dimensions is not None:
            return dict(form_def.dimensions)
        return {} if form_def.is_dimensionless else None

    loaded_claim_reference_lookup = (
        _load_claim_reference_lookup(claims_dir)
        if claim_reference_lookup is None
        else claim_reference_lookup
    )

    for c in concepts:
        data = c.record.to_payload()
        _validate_lemon_document(c, result=result)

        # ── Required fields (basic) ─────────────────────────────
        cid = data.get("artifact_id")
        name = data.get("canonical_name")
        status = data.get("status")
        definition = data.get("definition")
        form = data.get("form")

        if not cid:
            result.errors.append(f"{c.filename}: missing required field 'artifact_id'")
            continue
        if not name:
            result.errors.append(f"{c.filename}: missing required field 'canonical_name'")
        if not status:
            result.errors.append(f"{c.filename}: missing required field 'status'")
        if not definition:
            result.errors.append(f"{c.filename}: missing required field 'definition'")
        _validate_logical_ids(
            data.get("logical_ids"),
            filename=c.filename,
            artifact_id=cid,
            seen_logical_ids=seen_logical_ids,
            result=result,
        )
        version_id = data.get("version_id")
        if not isinstance(version_id, str) or not CONCEPT_VERSION_ID_RE.match(version_id):
            result.errors.append(
                f"{c.filename}: concept '{cid}' version_id must match sha256:<64 hex chars>"
            )
        else:
            version_payload = (
                concept_document_to_payload(c.document)
                if c.document is not None
                else data
            )
            expected_version_id = compute_concept_version_id(
                normalize_canonical_concept_payload(version_payload)
            )
            if version_id != expected_version_id:
                result.errors.append(
                    f"{c.filename}: concept '{cid}' version_id mismatch "
                    f"(expected {expected_version_id})"
                )
        if not form:
            result.errors.append(f"{c.filename}: missing required field 'form'")
        elif not isinstance(form, str):
            result.errors.append(f"{c.filename}: 'form' must be a string")
        else:
            if not _form_exists(c, form):
                result.errors.append(
                    f"{c.filename}: form '{form}' has no matching file at forms/{form}.yaml")

        # Validate form_parameters if present
        form_params = data.get("form_parameters")
        if form_params is not None and not isinstance(form_params, dict):
            result.errors.append(f"{c.filename}: 'form_parameters' must be a mapping")

        # ── Form-aware parameter validation ──────────────────────
        if isinstance(form, str) and form:
            form_def = _form_definition(c, form)
            if form_def is not None:
                # Category concepts must have values in form_parameters
                if form == "category":
                    if isinstance(form_params, dict):
                        category_values = form_params.get("values")
                    else:
                        category_values = None
                    if not isinstance(category_values, list):
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
                f"{c.filename}: duplicate concept artifact_id '{cid}' "
                f"(also in {id_to_concept[cid].filename})")
        else:
            id_to_concept[cid] = c

        # ── Artifact ID format ───────────────────────────────────
        if cid and not CONCEPT_ARTIFACT_ID_RE.match(cid):
            result.errors.append(
                f"{c.filename}: concept artifact_id '{cid}' does not match required format "
                "ps:concept:<opaque-token>"
            )

        # ── Deprecated concepts must have replaced_by ───────────
        if status == ConceptStatus.DEPRECATED.value:
            replaced_by = data.get("replaced_by")
            if not replaced_by:
                result.errors.append(
                    f"{c.filename}: deprecated concept must have 'replaced_by'")

    all_ids = set(id_to_concept.keys())
    reference_index = _concept_reference_index(concepts)
    try:
        cel_registry = build_canonical_cel_registry(
            concept.record
            for concept in concepts
            if str(concept.record.artifact_id) in all_ids
        )
    except ValueError as exc:
        message = str(exc)
        if "duplicate canonical_name" in message:
            result.warnings.append(f"CEL registry skipped ambiguous lexical form: {message}")
        else:
            result.errors.append(f"CEL registry error: {message}")

    # ── Cross-concept checks (need all concepts loaded) ─────────

    for c in concepts:
        _validate_phase3_lemon_references(
            c,
            reference_index=reference_index,
            result=result,
        )
        data = c.record.to_payload()
        cid = data.get("artifact_id", "")
        status = data.get("status")

        # ── replaced_by target exists and isn't deprecated ──────
        if status == ConceptStatus.DEPRECATED.value:
            replaced_by = data.get("replaced_by")
            if replaced_by:
                if replaced_by not in all_ids:
                    result.errors.append(
                        f"{c.filename}: replaced_by target '{replaced_by}' not found in registry")
                else:
                    target = id_to_concept[replaced_by]
                    if target.record.status is ConceptStatus.DEPRECATED:
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
            if cel_registry is not None:
                for cel_expr in rel.get("conditions", []) or []:
                    try:
                        checked = check_cel_expr(cel_expr, cel_registry)
                    except ValueError as exc:
                        result.errors.append(f"{c.filename}: CEL error: {exc}")
                        continue
                    for warning in checked.warnings:
                        result.warnings.append(f"{c.filename}: CEL warning: {warning.message}")

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
                    input_kind = kind_type_from_form_name(input_concept.record.form)
                    if input_kind and input_kind != KindType.QUANTITY:
                        result.errors.append(
                            f"{c.filename}: parameterization input '{input_id}' "
                            f"must be quantity kind (is {input_kind.value})")

            # ── Dimensional compatibility (bridgman) ─────────────
            output_form_def = _form_definition(c, data.get("form"))
            if output_form_def is not None and len(inputs) >= 2:
                input_form_defs = []
                for inp_id in inputs:
                    inp_c = id_to_concept.get(inp_id)
                    if inp_c is not None:
                        inp_fd = _form_definition(c, inp_c.record.form)
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
            if cel_registry is not None:
                for cel_expr in param.get("conditions", []) or []:
                    try:
                        checked = check_cel_expr(cel_expr, cel_registry)
                    except ValueError as exc:
                        result.errors.append(f"{c.filename}: CEL error: {exc}")
                        continue
                    for warning in checked.warnings:
                        result.warnings.append(f"{c.filename}: CEL warning: {warning.message}")

            # canonical_claim must reference an existing claim
            canonical_claim = param.get("canonical_claim")
            if canonical_claim:
                if claim_reference_lookup is None and claims_dir is None:
                    # No claims_dir provided — can't validate, emit error
                    result.errors.append(
                        f"{c.filename}: canonical_claim '{canonical_claim}' "
                        f"cannot be validated (no claims directory provided)")
                else:
                    claim_candidates = loaded_claim_reference_lookup.get(str(canonical_claim), ())
                    if len(claim_candidates) == 0:
                        result.errors.append(
                            f"{c.filename}: canonical_claim '{canonical_claim}' "
                            f"not found in claim files")
                    elif len(claim_candidates) > 1:
                        result.errors.append(
                            f"{c.filename}: canonical_claim '{canonical_claim}' "
                            f"is ambiguous in claim files")

            # Warning: missing sympy
            if not param.get("sympy"):
                result.warnings.append(
                    f"{c.filename}: parameterization relationship missing sympy expression")

    # ── Circular deprecation chains ─────────────────────────────
    for c in concepts:
        if c.record.status is not ConceptStatus.DEPRECATED:
            continue
        visited = set()
        current_id = str(c.record.artifact_id)
        while current_id:
            if current_id in visited:
                result.errors.append(
                    f"{c.filename}: circular deprecation chain detected involving '{current_id}'")
                break
            visited.add(current_id)
            current_concept = id_to_concept.get(current_id)
            if not current_concept:
                break
            if current_concept.record.status is not ConceptStatus.DEPRECATED:
                break
            current_id = (
                None
                if current_concept.record.replaced_by is None
                else str(current_concept.record.replaced_by)
            )

    return result
