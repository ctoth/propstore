"""Shared claim-side helpers for sidecar compilation."""

from __future__ import annotations

import copy
import json
import logging
import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

from ast_equiv import canonical_dump

from propstore.claims import LoadedClaimsFile, claim_file_claims, claim_file_source_paper
from propstore.core.algorithm_stage import AlgorithmStage, coerce_algorithm_stage
from propstore.core.claim_types import ClaimType
from propstore.dimensions import normalize_to_si
from propstore.form_utils import FormDefinition
from propstore.identity import (
    compute_claim_version_id,
    derive_claim_artifact_id,
    format_logical_id,
    normalize_identity_namespace,
    normalize_logical_value,
    primary_logical_id,
)
from propstore.sidecar.concept_utils import resolve_concept_reference
from propstore.stances import VALID_STANCE_TYPES

if TYPE_CHECKING:
    from propstore.compiler.ir import SemanticClaim


@dataclass(frozen=True)
class TypedClaimFields:
    concept_id: str | None = None
    statement: str | None = None
    expression: str | None = None
    name: str | None = None
    target_concept: str | None = None
    measure: str | None = None
    listener_population: str | None = None
    methodology: str | None = None
    value: float | None = None
    lower_bound: float | int | str | None = None
    upper_bound: float | int | str | None = None
    uncertainty: float | int | str | None = None
    uncertainty_type: str | None = None
    sample_size: int | None = None
    unit: str | None = None

    def __getitem__(self, key: str) -> object | None:
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_float_input(value: object) -> float | int | str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float | str):
        return value
    return None


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def claim_version_id(claim: dict) -> str | None:
    version_id = claim.get("version_id")
    if isinstance(version_id, str) and version_id:
        return version_id
    return None


def normalize_conditions_differ(value: object) -> object:
    if isinstance(value, list):
        return json.dumps(value)
    return value


def coerce_stance_resolution(
    resolution: object,
    owner: str,
) -> dict[str, object]:
    if resolution is None:
        return {}
    if not isinstance(resolution, dict):
        raise ValueError(f"{owner} resolution must be a mapping")
    return resolution


def resolution_opinion_columns(resolution: dict[str, object]) -> tuple[object, object, object, object]:
    opinion = resolution.get("opinion")
    if opinion is None:
        return None, None, None, None
    if not isinstance(opinion, dict):
        raise ValueError("resolution opinion must be a mapping")
    return (
        opinion.get("b"),
        opinion.get("d"),
        opinion.get("u"),
        opinion.get("a"),
    )


def insert_claim_stance_row(conn: sqlite3.Connection, stance_row: tuple) -> None:
    conn.execute(
        """
        INSERT INTO relation_edge (
            source_kind, source_id, relation_type, target_kind, target_id,
            target_justification_id, strength, conditions_differ, note,
            resolution_method, resolution_model, embedding_model,
            embedding_distance, pass_number, confidence, opinion_belief,
            opinion_disbelief, opinion_uncertainty, opinion_base_rate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "claim",
            stance_row[0],
            stance_row[2],
            "claim",
            stance_row[1],
            stance_row[3],
            stance_row[4],
            normalize_conditions_differ(stance_row[5]),
            stance_row[6],
            stance_row[7],
            stance_row[8],
            stance_row[9],
            stance_row[10],
            stance_row[11],
            stance_row[12],
            stance_row[13],
            stance_row[14],
            stance_row[15],
            stance_row[16],
        ),
    )


def claim_reference_map_from_conn(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute(
        "SELECT id, primary_logical_id, logical_ids_json FROM claim_core"
    ).fetchall()
    reference_map: dict[str, str] = {}
    for row in rows:
        claim_id = row[0]
        if not isinstance(claim_id, str) or not claim_id:
            continue
        reference_map[claim_id] = claim_id
        primary_logical_id = row[1]
        if isinstance(primary_logical_id, str) and primary_logical_id:
            reference_map[primary_logical_id] = claim_id
            if ":" in primary_logical_id:
                reference_map[primary_logical_id.split(":", 1)[1]] = claim_id
        logical_ids_json = row[2]
        if not isinstance(logical_ids_json, str) or not logical_ids_json:
            continue
        try:
            logical_ids = json.loads(logical_ids_json)
        except json.JSONDecodeError:
            continue
        if not isinstance(logical_ids, list):
            continue
        for logical_id in logical_ids:
            if not isinstance(logical_id, dict):
                continue
            formatted = format_logical_id(logical_id)
            if formatted:
                reference_map[formatted] = claim_id
            value = logical_id.get("value")
            if isinstance(value, str) and value:
                reference_map[value] = claim_id
    return reference_map


def collect_claim_reference_map(claim_files: Sequence[LoadedClaimsFile]) -> dict[str, str]:
    claim_reference_map: dict[str, str] = {}
    for claim_file in claim_files:
        source_paper = claim_file_source_paper(claim_file) or claim_file.filename
        for claim in claim_file_claims(claim_file):
            claim_id = claim.artifact_id
            if not isinstance(claim_id, str) or not claim_id:
                raw_id = claim.id
                if isinstance(raw_id, str) and raw_id:
                    claim_id = derive_claim_artifact_id(
                        str(source_paper),
                        normalize_logical_value(raw_id),
                    )
            if isinstance(claim_id, str) and claim_id:
                claim_reference_map[claim_id] = claim_id

            raw_id = claim.id
            if isinstance(raw_id, str) and raw_id and isinstance(claim_id, str) and claim_id:
                claim_reference_map[raw_id] = claim_id
                claim_reference_map[
                    f"{normalize_identity_namespace(str(source_paper))}:{normalize_logical_value(raw_id)}"
                ] = claim_id

            for logical_id in claim.logical_ids:
                if isinstance(claim_id, str) and claim_id:
                    claim_reference_map[logical_id.formatted] = claim_id
                    claim_reference_map[logical_id.value] = claim_id
    return claim_reference_map


def resolve_claim_reference(
    claim_ref: object,
    claim_reference_map: dict[str, str],
    *,
    source_paper: str | None = None,
) -> str | None:
    if not isinstance(claim_ref, str) or not claim_ref:
        return None
    resolved = claim_reference_map.get(claim_ref)
    if isinstance(resolved, str) and resolved:
        return resolved
    if source_paper:
        derived = claim_reference_map.get(
            f"{normalize_identity_namespace(str(source_paper))}:{normalize_logical_value(claim_ref)}"
        )
        if isinstance(derived, str) and derived:
            return derived
    return claim_ref


def insert_claim_row(conn: sqlite3.Connection, row: dict[str, object]) -> None:
    """Insert a fully-populated claim row into claim_core + payload tables.

    Schema-v3 lifecycle columns (``build_status``, ``stage``,
    ``promotion_status``) are written when present in ``row``; otherwise
    they fall back to the schema defaults (``build_status='ingested'``;
    ``stage``/``promotion_status`` NULL). See
    ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``
    findings 3.1, 3.2, 3.3 for the render-layer semantics.
    """

    conn.execute(
        """
        INSERT INTO claim_core (
            id, primary_logical_id, logical_ids_json, version_id, seq, type,
            concept_id, target_concept, source_slug, source_paper,
            provenance_page, provenance_json, context_id, branch,
            build_status, stage, promotion_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["id"],
            row["primary_logical_id"],
            row["logical_ids_json"],
            row["version_id"],
            row["seq"],
            row["type"],
            row["concept_id"],
            row["target_concept"],
            row["source_slug"],
            row["source_paper"],
            row["provenance_page"],
            row["provenance_json"],
            row["context_id"],
            row.get("branch"),
            row.get("build_status") or "ingested",
            row.get("stage"),
            row.get("promotion_status"),
        ),
    )
    conn.execute(
        """
        INSERT INTO claim_numeric_payload (
            claim_id, value, lower_bound, upper_bound, uncertainty,
            uncertainty_type, sample_size, unit, value_si,
            lower_bound_si, upper_bound_si
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["id"],
            row["value"],
            row["lower_bound"],
            row["upper_bound"],
            row["uncertainty"],
            row["uncertainty_type"],
            row["sample_size"],
            row["unit"],
            row["value_si"],
            row["lower_bound_si"],
            row["upper_bound_si"],
        ),
    )
    conn.execute(
        """
        INSERT INTO claim_text_payload (
            claim_id, conditions_cel, statement, expression, sympy_generated,
            sympy_error, name, measure, listener_population, methodology,
            notes, description, auto_summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["id"],
            row["conditions_cel"],
            row["statement"],
            row["expression"],
            row["sympy_generated"],
            row["sympy_error"],
            row["name"],
            row["measure"],
            row["listener_population"],
            row["methodology"],
            row["notes"],
            row["description"],
            row["auto_summary"],
        ),
    )
    conn.execute(
        """
        INSERT INTO claim_algorithm_payload (
            claim_id, body, canonical_ast, variables_json, algorithm_stage
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            row["id"],
            row["body"],
            row["canonical_ast"],
            row["variables_json"],
            row["algorithm_stage"],
        ),
    )


def canonicalize_claim_for_storage(
    claim: dict,
    concept_registry: dict,
    *,
    source_paper: str,
) -> dict:
    normalized = dict(claim)
    artifact_id = normalized.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        raw_id = normalized.get("id")
        if isinstance(raw_id, str) and raw_id:
            logical_ids = normalized.get("logical_ids")
            if not isinstance(logical_ids, list) or not logical_ids:
                logical_ids = [{
                    "namespace": str(source_paper),
                    "value": normalize_logical_value(raw_id),
                }]
                normalized["logical_ids"] = logical_ids
            primary = primary_logical_id(normalized)
            if isinstance(primary, str) and ":" in primary:
                namespace, value = primary.split(":", 1)
            else:
                namespace, value = str(source_paper), normalize_logical_value(raw_id)
            artifact_id = derive_claim_artifact_id(namespace, value)
            normalized["artifact_id"] = artifact_id
            if not isinstance(normalized.get("version_id"), str) or not normalized.get("version_id"):
                normalized["version_id"] = compute_claim_version_id(normalized)

    if isinstance(artifact_id, str) and artifact_id:
        normalized["id"] = artifact_id

    normalized["concept"] = resolve_concept_reference(normalized.get("concept"), concept_registry)
    normalized["target_concept"] = resolve_concept_reference(normalized.get("target_concept"), concept_registry)

    concepts = normalized.get("concepts")
    if isinstance(concepts, list):
        normalized["concepts"] = [
            resolve_concept_reference(concept_ref, concept_registry)
            for concept_ref in concepts
        ]

    for field_name in ("variables", "parameters"):
        values = normalized.get(field_name)
        if isinstance(values, list):
            rewritten = []
            for value in values:
                if not isinstance(value, dict):
                    rewritten.append(value)
                    continue
                updated = dict(value)
                updated["concept"] = resolve_concept_reference(updated.get("concept"), concept_registry)
                rewritten.append(updated)
            normalized[field_name] = rewritten

    return normalized


def extract_numeric_claim_fields(claim: dict) -> TypedClaimFields:
    raw_value = claim.get("value")
    if raw_value is None:
        value = None
    else:
        try:
            value = float(raw_value)
        except ValueError:
            logging.getLogger(__name__).warning(
                "Cannot parse value %r as float, treating as None",
                raw_value,
            )
            value = None
    return TypedClaimFields(
        value=value,
        lower_bound=_optional_float_input(claim.get("lower_bound")),
        upper_bound=_optional_float_input(claim.get("upper_bound")),
        uncertainty=_optional_float_input(claim.get("uncertainty")),
        uncertainty_type=_optional_string(claim.get("uncertainty_type")),
        sample_size=_optional_int(claim.get("sample_size")),
        unit=_optional_string(claim.get("unit")),
    )


def extract_typed_claim_fields(claim: dict) -> TypedClaimFields:
    claim_type = claim.get("type")
    if claim_type == "parameter":
        numeric = extract_numeric_claim_fields(claim)
        return TypedClaimFields(
            concept_id=_optional_string(claim.get("concept")),
            value=numeric.value,
            lower_bound=numeric.lower_bound,
            upper_bound=numeric.upper_bound,
            uncertainty=numeric.uncertainty,
            uncertainty_type=numeric.uncertainty_type,
            sample_size=numeric.sample_size,
            unit=numeric.unit,
        )
    if claim_type == "measurement":
        numeric = extract_numeric_claim_fields(claim)
        return TypedClaimFields(
            target_concept=_optional_string(claim.get("target_concept")),
            measure=_optional_string(claim.get("measure")),
            listener_population=_optional_string(claim.get("listener_population")),
            methodology=_optional_string(claim.get("methodology")),
            value=numeric.value,
            lower_bound=numeric.lower_bound,
            upper_bound=numeric.upper_bound,
            uncertainty=numeric.uncertainty,
            uncertainty_type=numeric.uncertainty_type,
            sample_size=numeric.sample_size,
            unit=numeric.unit,
        )
    if claim_type == "observation":
        return TypedClaimFields(statement=_optional_string(claim.get("statement")))
    if claim_type == "equation":
        return TypedClaimFields(expression=_optional_string(claim.get("expression")))
    if claim_type == "model":
        return TypedClaimFields(name=_optional_string(claim.get("name")))
    if claim_type == "algorithm":
        return TypedClaimFields(concept_id=_optional_string(claim.get("concept")))
    return TypedClaimFields()


def resolve_equation_sympy(
    claim_type: str | None,
    expression: str | None,
    claim: dict,
) -> tuple[str | None, str | None]:
    if claim_type != "equation":
        return None, None
    explicit_sympy = claim.get("sympy")
    if explicit_sympy:
        return explicit_sympy, None
    if not expression:
        return None, None
    from propstore.sympy_generator import generate_sympy_with_error

    sympy_result = generate_sympy_with_error(expression)
    return sympy_result.expression, sympy_result.error


def resolve_algorithm_storage(
    claim: dict,
) -> tuple[str | None, str | None, str | None, AlgorithmStage | None]:
    if claim.get("type") != ClaimType.ALGORITHM.value:
        return None, None, None, None
    body = claim.get("body")
    algorithm_stage = coerce_algorithm_stage(claim.get("stage"))
    raw_vars = claim.get("variables")
    if raw_vars not in (None, []) and not isinstance(raw_vars, list):
        raise ValueError("algorithm claim variables must be a list of variable bindings")
    canonical_ast = None
    if body:
        variables = raw_vars or []
        bindings = {
            v["name"]: v.get("concept", "")
            for v in variables
            if isinstance(v, dict) and v.get("name")
        }
        canonical_ast = canonical_dump(body, bindings)
    variables_json = json.dumps(raw_vars) if raw_vars else None
    return body, canonical_ast, variables_json, algorithm_stage


def extract_deferred_stance_rows(
    claim: dict | SemanticClaim,
    claim_reference_map: dict[str, str],
    *,
    source_paper: str,
) -> list[tuple]:
    if hasattr(claim, "resolved_claim") and hasattr(claim, "stances"):
        semantic_claim = claim
        claim_data = semantic_claim.resolved_claim
        claim_id = (
            claim_data.get("artifact_id")
            if isinstance(claim_data.get("artifact_id"), str)
            else claim_data.get("id")
        )
        stance_inputs = [
            (
                stance.data,
                stance.target_ref.resolved_id or stance.target_ref.raw_text,
            )
            for stance in semantic_claim.stances
        ]
    else:
        claim_data = claim
        claim_id = resolve_claim_reference(
            claim_data.get("artifact_id") or claim_data.get("id"),
            claim_reference_map,
            source_paper=source_paper,
        )
        stance_inputs = []
        for stance in claim_data.get("stances", []) or []:
            if not isinstance(stance, dict):
                continue
            target_claim_id = resolve_claim_reference(
                stance.get("target"),
                claim_reference_map,
                source_paper=source_paper,
            )
            stance_inputs.append((stance, target_claim_id))

    rows: list[tuple] = []
    for stance, target_claim_id in stance_inputs:
        stance_type = stance.get("type")
        if not target_claim_id or not stance_type:
            continue
        if stance_type not in VALID_STANCE_TYPES:
            raise ValueError(f"claim '{claim_id}' uses unrecognized stance type '{stance_type}'")
        if target_claim_id not in claim_reference_map.values():
            raise sqlite3.IntegrityError(
                f"claim '{claim_id}' references nonexistent target claim '{target_claim_id}'"
            )
        resolution = coerce_stance_resolution(
            stance.get("resolution"),
            f"claim '{claim_id}' stance targeting '{target_claim_id}'",
        )
        opinion_columns = resolution_opinion_columns(resolution)
        rows.append((
            claim_id,
            target_claim_id,
            stance_type,
            stance.get("target_justification_id"),
            stance.get("strength"),
            normalize_conditions_differ(stance.get("conditions_differ")),
            stance.get("note"),
            resolution.get("method"),
            resolution.get("model"),
            resolution.get("embedding_model"),
            resolution.get("embedding_distance"),
            resolution.get("pass_number"),
            resolution.get("confidence"),
            opinion_columns[0],
            opinion_columns[1],
            opinion_columns[2],
            opinion_columns[3],
        ))
    return rows


def prepare_claim_insert_row(
    claim: dict | SemanticClaim,
    source_paper: str | None,
    *,
    claim_seq: int,
    concept_registry: dict | None = None,
    form_registry: dict[str, FormDefinition] | None = None,
) -> dict[str, object]:
    from propstore.description_generator import generate_description

    if hasattr(claim, "resolved_claim") and hasattr(claim, "source_paper"):
        semantic_claim = claim
        normalized_claim = copy.deepcopy(semantic_claim.resolved_claim)
        effective_source_paper = str(source_paper or semantic_claim.source_paper)
    else:
        effective_registry = {} if concept_registry is None else concept_registry
        normalized_claim = canonicalize_claim_for_storage(
            claim,
            effective_registry,
            source_paper=str(source_paper),
        )
        effective_source_paper = str(source_paper)
    claim_type = normalized_claim.get("type")
    provenance = normalized_claim.get("provenance", {})
    conditions = normalized_claim.get("conditions")
    typed_fields = extract_typed_claim_fields(normalized_claim)
    expression = typed_fields.expression
    sympy_generated, sympy_error = resolve_equation_sympy(
        claim_type,
        str(expression) if expression is not None else None,
        normalized_claim,
    )
    body, canonical_ast, variables_json, algorithm_stage = resolve_algorithm_storage(
        normalized_claim
    )

    value_si = typed_fields.value
    lower_bound_si = typed_fields.lower_bound
    upper_bound_si = typed_fields.upper_bound
    unit = typed_fields.unit

    form_def: FormDefinition | None = None
    if form_registry and concept_registry:
        concept_id = typed_fields.concept_id
        concept_data = concept_registry.get(concept_id) if concept_id else None
        if isinstance(concept_data, dict):
            form_name = concept_data.get("form")
            if isinstance(form_name, str):
                form_def = form_registry.get(form_name)

    if form_def is not None:
        try:
            if value_si is not None:
                value_si = normalize_to_si(float(value_si), unit, form_def)
            if lower_bound_si is not None:
                lower_bound_si = normalize_to_si(float(lower_bound_si), unit, form_def)
            if upper_bound_si is not None:
                upper_bound_si = normalize_to_si(float(upper_bound_si), unit, form_def)
        except (ValueError, TypeError):
            value_si = typed_fields.value
            lower_bound_si = typed_fields.lower_bound
            upper_bound_si = typed_fields.upper_bound

    raw_context = normalized_claim.get("context")
    context_id = raw_context.get("id") if isinstance(raw_context, dict) else raw_context

    return {
        "id": normalized_claim.get("artifact_id"),
        "primary_logical_id": primary_logical_id(normalized_claim),
        "logical_ids_json": json.dumps(normalized_claim.get("logical_ids") or []),
        "version_id": claim_version_id(normalized_claim),
        "seq": claim_seq,
        "type": claim_type,
        "concept_id": typed_fields.concept_id,
        "value": typed_fields.value,
        "lower_bound": typed_fields.lower_bound,
        "upper_bound": typed_fields.upper_bound,
        "uncertainty": typed_fields.uncertainty,
        "uncertainty_type": typed_fields.uncertainty_type,
        "sample_size": typed_fields.sample_size,
        "unit": typed_fields.unit,
        "value_si": value_si,
        "lower_bound_si": lower_bound_si,
        "upper_bound_si": upper_bound_si,
        "conditions_cel": json.dumps(conditions) if conditions else None,
        "statement": typed_fields.statement,
        "expression": typed_fields.expression,
        "sympy_generated": sympy_generated,
        "sympy_error": sympy_error,
        "name": typed_fields.name,
        "target_concept": typed_fields.target_concept,
        "measure": typed_fields.measure,
        "listener_population": typed_fields.listener_population,
        "methodology": typed_fields.methodology,
        "notes": normalized_claim.get("notes"),
        "description": normalized_claim.get("description"),
        "auto_summary": generate_description(
            normalized_claim,
            {} if concept_registry is None else concept_registry,
        ),
        "body": body,
        "canonical_ast": canonical_ast,
        "variables_json": variables_json,
        "algorithm_stage": algorithm_stage,
        "source_slug": effective_source_paper,
        "source_paper": provenance.get("paper", effective_source_paper),
        "provenance_page": provenance.get("page", 0),
        "provenance_json": json.dumps(provenance, sort_keys=True),
        "context_id": context_id,
        "branch": normalized_claim.get("branch"),
    }
