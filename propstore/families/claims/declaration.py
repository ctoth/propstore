"""Claim-side compilation helpers for the sidecar.

Raw-id quarantine path (``reviews/2026-04-16-code-review/workstreams/
ws-z-render-gates.md`` axis-1 finding 3.1): claims whose raw ``id`` never
canonicalized are still given a ``claim_core`` row with a synthetic id
and ``build_status='blocked'``, plus a ``build_diagnostics`` row
describing why. This implements discipline rule 5 (filter at render, not
at build) — no data is refused; the render layer decides what to show.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from quire.references import FamilyReferenceIndex
from quire.projections import ProjectionRow
from propstore.claims import (
    ClaimFileEntry,
    claim_file_filename,
    claim_file_stage,
)
from propstore.conflict_detector import detect_conflicts, detect_transitive_conflicts
from propstore.conflict_detector.collectors import conflict_claims_from_claim_files
from propstore.cel_types import CelExpr, to_cel_exprs
from propstore.compiler.ir import ClaimCompilationBundle
from propstore.core.algorithm_stage import AlgorithmStage
from propstore.core.claim_types import ClaimType, coerce_claim_type
from propstore.core.conditions import (
    CheckedConditionSet,
    checked_condition_set_from_json,
    checked_condition_set_to_json,
)
from propstore.core.id_types import (
    ClaimId,
    to_claim_id,
    to_justification_id,
)
from propstore.core.relations import ClaimConceptLinkRole
from propstore.families.claims.references import (
    ClaimReferenceRecord,
    build_claim_file_reference_index,
)
from propstore.families.claims.storage import (
    extract_deferred_stance_rows_with_diagnostics,
    prepare_claim_concept_link_rows,
)
from propstore.families.claims.stages import (
    ClaimAlgorithmVariable,
    claim_algorithm_variable_payload,
    PromotionBlockedClaimFact,
    RawIdQuarantineRecord,
    parse_claim_algorithm_variables,
)
from propstore.families.diagnostics.declaration import (
    QuarantineDiagnostic,
    compile_promotion_blocked_diagnostics,
)
from propstore.families.documents.justifications import JustificationDocument
from propstore.families.relations.declaration import (
    CLAIM_STANCE_DISCRIMINATORS,
    CLAIM_STANCE_STORAGE_MODEL,
    CONFLICT_WITNESS_TABLE,
    RELATION_EDGE_TABLE,
    StanceRow,
)
from propstore.stances import coerce_stance_type

if TYPE_CHECKING:
    from propstore.core.graph_types import ProvenanceRecord
    from propstore.core.justifications import CanonicalJustification


def _require_claim_type(value: object) -> ClaimType:
    claim_type = coerce_claim_type(value)
    if claim_type is None:
        raise KeyError('claim_type')
    return claim_type


class Claim:
    id: str
    primary_logical_id: str
    logical_ids_json: str
    version_id: str
    content_hash: str
    seq: int
    type: ClaimType
    target_concept: str | None
    source_slug: str | None
    source_paper: str
    provenance_page: int
    provenance_json: str | None
    context_id: str | None
    premise_kind: str
    branch: str | None
    build_status: str
    stage: str | None
    promotion_status: str | None
    concept_links: list["ClaimConceptLink"]
    numeric_payload: "ClaimNumericPayload | None"
    text_payload: "ClaimTextPayload | None"
    algorithm_payload: "ClaimAlgorithmPayload | None"
    source_assertions: list["ClaimSourceAssertion"]

    def concept_ids_for_role(self, role: ClaimConceptLinkRole) -> tuple[str, ...]:
        return tuple(
            str(link.concept_id)
            for link in self.concept_links
            if link.role is role
        )

    @property
    def logical_ids(self) -> tuple[Mapping[str, object], ...]:
        if not self.logical_ids_json:
            return ()
        loaded = json.loads(self.logical_ids_json)
        if not isinstance(loaded, list):
            raise ValueError("claim logical_ids_json must decode to a list")
        entries: list[Mapping[str, object]] = []
        for entry in loaded:
            if not isinstance(entry, Mapping):
                raise ValueError("claim logical_ids_json entries must be mappings")
            entries.append(entry)
        return tuple(entries)

    @property
    def output_concept_id(self) -> str | None:
        concept_ids = self.concept_ids_for_role(ClaimConceptLinkRole.OUTPUT)
        return concept_ids[0] if concept_ids else None

    @property
    def value_concept_id(self) -> str | None:
        return self.output_concept_id or self.target_concept

    @property
    def about_concept_ids(self) -> tuple[str, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.ABOUT)

    @property
    def input_concept_ids(self) -> tuple[str, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.INPUT)

    @property
    def target_concept_ids(self) -> tuple[str, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.TARGET)

    @property
    def checked_conditions(self) -> CheckedConditionSet | None:
        text_payload = self.text_payload
        if text_payload is None or not text_payload.conditions_ir:
            return None
        loaded = json.loads(text_payload.conditions_ir)
        if not isinstance(loaded, Mapping):
            raise ValueError("claim conditions_ir must decode to a mapping")
        return checked_condition_set_from_json(loaded)

    @property
    def conditions(self) -> tuple[CelExpr, ...]:
        checked_conditions = self.checked_conditions
        if checked_conditions is not None:
            return to_cel_exprs(checked_conditions.sources)
        text_payload = self.text_payload
        if text_payload is None or not text_payload.conditions_cel:
            return ()
        loaded = json.loads(text_payload.conditions_cel)
        if not isinstance(loaded, list):
            raise ValueError("claim conditions_cel must decode to a list")
        return to_cel_exprs(str(item) for item in loaded)

    @property
    def variables(self) -> tuple[ClaimAlgorithmVariable, ...]:
        algorithm_payload = self.algorithm_payload
        if algorithm_payload is None:
            return ()
        return parse_claim_algorithm_variables(algorithm_payload.variables_json)

    def variable_bindings(self) -> dict[str, str]:
        bindings: dict[str, str] = {}
        for variable in self.variables:
            if variable.concept_id is None:
                continue
            name = variable.name or variable.symbol
            if name:
                bindings[name] = str(variable.concept_id)
        return bindings

    def variable_concept_ids(self) -> tuple[str, ...]:
        return tuple(
            str(variable.concept_id)
            for variable in self.variables
            if variable.concept_id is not None
        )

    def variable_payload(self) -> list[dict[str, Any]] | None:
        if not self.variables:
            return None
        return [claim_algorithm_variable_payload(variable) for variable in self.variables]

    def to_source_claim_payload(self) -> dict[str, Any]:
        numeric_payload = self.numeric_payload
        text_payload = self.text_payload
        algorithm_payload = self.algorithm_payload
        source: dict[str, Any] = {
            "id": self.id,
            "type": self.type.value,
            "target_concept": self.target_concept,
            "context": {"id": self.context_id},
            "source_paper": self.source_paper,
            "provenance": json.loads(self.provenance_json)
            if self.provenance_json
            else None,
        }
        if self.type is ClaimType.PARAMETER and self.output_concept_id is not None:
            source["output_concept"] = self.output_concept_id
        if (
            self.type is ClaimType.MEASUREMENT
            and self.output_concept_id is not None
            and self.target_concept is None
        ):
            source["target_concept"] = self.output_concept_id
        if self.type is ClaimType.ALGORITHM and self.output_concept_id is not None:
            source["output_concept"] = self.output_concept_id
        if numeric_payload is not None:
            source.update(
                value=numeric_payload.value,
                lower_bound=numeric_payload.lower_bound,
                upper_bound=numeric_payload.upper_bound,
                uncertainty=numeric_payload.uncertainty,
                uncertainty_type=numeric_payload.uncertainty_type,
                sample_size=numeric_payload.sample_size,
                unit=numeric_payload.unit,
            )
        if text_payload is not None:
            source.update(
                conditions=json.loads(text_payload.conditions_cel)
                if text_payload.conditions_cel
                else [],
                statement=text_payload.statement,
                expression=text_payload.expression,
                sympy=text_payload.sympy_generated,
                name=text_payload.name,
                measure=text_payload.measure,
                listener_population=text_payload.listener_population,
                methodology=text_payload.methodology,
                notes=text_payload.notes,
            )
        if algorithm_payload is not None:
            source.update(
                body=algorithm_payload.body,
                stage=algorithm_payload.algorithm_stage,
            )
            variable_payload = self.variable_payload()
            if variable_payload is not None:
                source["variables"] = variable_payload
        return {key: value for key, value in source.items() if value is not None}


class ClaimConceptLink:
    claim_id: str
    concept_id: str
    role: ClaimConceptLinkRole
    ordinal: int
    binding_name: str | None
    claim: Claim | None

    def __init__(
        self,
        claim_id: str,
        concept_id: str,
        role: ClaimConceptLinkRole,
        ordinal: int,
        binding_name: str | None = None,
    ) -> None:
        self.claim_id = claim_id
        self.concept_id = concept_id
        self.role = role
        self.ordinal = ordinal
        self.binding_name = binding_name
        self.claim = None


class ClaimNumericPayload:
    claim_id: str
    value: float | None
    lower_bound: float | None
    upper_bound: float | None
    uncertainty: float | None
    uncertainty_type: str | None
    sample_size: int | None
    unit: str | None
    value_si: float | None
    lower_bound_si: float | None
    upper_bound_si: float | None
    claim: Claim | None


class ClaimTextPayload:
    claim_id: str
    conditions_cel: str | None
    conditions_ir: str | None
    statement: str | None
    expression: str | None
    sympy_generated: str | None
    sympy_error: str | None
    name: str | None
    measure: str | None
    listener_population: str | None
    methodology: str | None
    notes: str | None
    description: str | None
    auto_summary: str | None
    claim: Claim | None


class ClaimAlgorithmPayload:
    claim_id: str
    body: str | None
    canonical_ast: str | None
    variables_json: str | None
    algorithm_stage: AlgorithmStage | None
    claim: Claim | None


class ClaimSourceAssertion:
    claim_id: str
    source_assertion_id: str
    ordinal: int
    claim: Claim | None

    def __init__(
        self,
        claim_id: str,
        source_assertion_id: str,
        ordinal: int,
    ) -> None:
        self.claim_id = claim_id
        self.source_assertion_id = source_assertion_id
        self.ordinal = ordinal
        self.claim = None


@dataclass(frozen=True)
class ClaimWriteModels:
    claims: tuple[Claim, ...]
    numeric_payloads: tuple[ClaimNumericPayload, ...]
    text_payloads: tuple[ClaimTextPayload, ...]
    algorithm_payloads: tuple[ClaimAlgorithmPayload, ...]
    source_assertions: tuple[ClaimSourceAssertion, ...]
    concept_links: tuple[ClaimConceptLink, ...]
    stance_rows: tuple[ProjectionRow, ...]
    quarantine_diagnostics: tuple[QuarantineDiagnostic, ...]


@dataclass(frozen=True)
class RawIdQuarantineModels:
    claims: tuple[Claim, ...]
    diagnostics: tuple[BuildDiagnostic, ...]


@dataclass(frozen=True)
class PromotionBlockedModels:
    claims: tuple[Claim, ...]
    diagnostics: tuple[BuildDiagnostic, ...]


from propstore.families.claims.projection_model import (  # noqa: E402
    JUSTIFICATION_TABLE,
)
from propstore.families.world_charters import BuildDiagnostic, world_record


def count_claims(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM claim_core").fetchone()[0])


def select_authored_justifications(
    conn: sqlite3.Connection,
) -> tuple[CanonicalJustification, ...]:
    rows = conn.execute(
        """
        SELECT id, justification_kind, conclusion_claim_id,
               premise_claim_ids, source_relation_type, source_claim_id,
               provenance_json, rule_strength
        FROM justification
        ORDER BY id
        """
    ).fetchall()
    return tuple(_canonical_justification_from_row(row) for row in rows)


def count_authored_justifications(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM justification").fetchone()[0])


def _canonical_justification_from_row(
    row: sqlite3.Row,
) -> CanonicalJustification:
    from propstore.core.justifications import CanonicalJustification

    justification_id = str(row["id"])
    premise_claim_ids = _decode_justification_premises(
        row["premise_claim_ids"],
        justification_id=justification_id,
    )
    provenance = _decode_justification_provenance(
        row["provenance_json"],
        justification_id=justification_id,
    )
    attributes = tuple(
        (key, row[key])
        for key in ("source_relation_type", "source_claim_id")
        if row[key] is not None
    )
    return CanonicalJustification(
        justification_id=justification_id,
        conclusion_claim_id=str(row["conclusion_claim_id"]),
        premise_claim_ids=premise_claim_ids,
        rule_kind=str(row["justification_kind"]),
        rule_strength=str(row["rule_strength"] or "defeasible"),
        provenance=provenance,
        attributes=attributes,
    )


def _decode_justification_premises(
    value: object,
    *,
    justification_id: str,
) -> tuple[str, ...]:
    if not isinstance(value, str):
        raise ValueError(
            f"justification {justification_id!r} premise_claim_ids must be JSON text"
        )
    loaded = json.loads(value)
    if not isinstance(loaded, list):
        raise ValueError(
            f"justification {justification_id!r} premise_claim_ids must decode to a list"
        )
    return tuple(str(item) for item in loaded)


def _decode_justification_provenance(
    value: object,
    *,
    justification_id: str,
) -> ProvenanceRecord | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(
            f"justification {justification_id!r} provenance_json must be JSON text"
        )
    loaded = json.loads(value)
    if not isinstance(loaded, Mapping):
        raise ValueError(
            f"justification {justification_id!r} provenance_json must decode to a mapping"
        )
    from propstore.core.graph_types import ProvenanceRecord

    return ProvenanceRecord.from_json_payload(loaded)


def has_claim_core_table(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='claim_core'"
    ).fetchone()
    return row is not None


def delete_claim_core_row(conn: sqlite3.Connection, claim_id: str) -> None:
    conn.execute("DELETE FROM claim_core WHERE id = ?", (claim_id,))


def select_claim_text(conn: sqlite3.Connection, claim_id: str) -> dict[str, Any] | None:
    rows = select_claim_texts(conn, [claim_id])
    return rows.get(claim_id)


def select_claim_texts(
    conn: sqlite3.Connection,
    claim_ids: Sequence[str],
) -> dict[str, dict[str, Any]]:
    if not claim_ids:
        return {}
    placeholders = ",".join("?" for _ in claim_ids)
    rows = conn.execute(
        f"""
        SELECT core.id, txt.auto_summary, txt.statement, txt.expression, core.source_paper
        FROM claim_core AS core
        LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
        WHERE core.id IN ({placeholders})
        """,
        tuple(claim_ids),
    ).fetchall()
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        decoded = dict(row)
        decoded["text"] = (
            decoded.get("auto_summary")
            or decoded.get("statement")
            or decoded.get("expression")
            or decoded["id"]
        )
        result[str(decoded["id"])] = decoded
    return result


def select_all_claim_ids(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT id FROM claim_core").fetchall()
    return [str(row["id"]) for row in rows]


def select_source_promotion_claim_rows(
    conn: sqlite3.Connection,
    branch: str,
) -> tuple[tuple[str, str], ...]:
    rows = conn.execute(
        """
        SELECT id, promotion_status
        FROM claim_core
        WHERE branch = ? AND promotion_status IS NOT NULL
        ORDER BY id
        """,
        (branch,),
    ).fetchall()
    return tuple((str(row[0]), str(row[1])) for row in rows)


def compile_claim_models(
    claim_bundle: ClaimCompilationBundle,
    concept_registry: dict,
    *,
    form_registry: dict | None = None,
) -> ClaimWriteModels:
    claim_seq = 0
    claim_models: list[Claim] = []
    numeric_payloads: list[ClaimNumericPayload] = []
    text_payloads: list[ClaimTextPayload] = []
    algorithm_payloads: list[ClaimAlgorithmPayload] = []
    source_assertions: list[ClaimSourceAssertion] = []
    claim_links: list[ClaimConceptLink] = []
    stance_rows: list[ProjectionRow] = []
    quarantine_diagnostics: list[QuarantineDiagnostic] = []
    seen_claim_versions: dict[str, str] = {}
    emitted_version_conflicts: set[tuple[str, str, str]] = set()
    seen_claim_link_keys: set[tuple[str, ClaimConceptLinkRole, int, str]] = set()
    claim_index = build_claim_file_reference_index(
        claim_bundle.normalized_claim_files
    )
    file_stage_by_filename: dict[str, str | None] = {
        claim_file_filename(claim_file): claim_file_stage(claim_file)
        for claim_file in claim_bundle.normalized_claim_files
    }

    for semantic_file in claim_bundle.semantic_files:
        file_stage = file_stage_by_filename.get(
            claim_file_filename(semantic_file.normalized_entry)
        )
        for semantic_claim in semantic_file.claims:
            claim_seq += 1
            claim_doc = semantic_claim.resolved_claim
            provenance = claim_doc.provenance
            provenance_payload = None if provenance is None else provenance.to_payload()
            conditions_ir = (
                json.dumps(
                    checked_condition_set_to_json(semantic_claim.checked_conditions),
                    sort_keys=True,
                )
                if semantic_claim.checked_conditions is not None
                else None
            )
            logical_ids_payload = [
                logical_id.to_payload()
                for logical_id in claim_doc.logical_ids
            ]
            claim_values: dict[str, object] = {
                "id": semantic_claim.artifact_id or claim_doc.artifact_id,
                "primary_logical_id": claim_doc.primary_logical_id or "",
                "logical_ids_json": json.dumps(logical_ids_payload),
                "version_id": claim_doc.version_id or "",
                "seq": claim_seq,
                "type": claim_doc.type,
                "target_concept": claim_doc.target_concept,
                "source_slug": semantic_claim.source_paper,
                "source_paper": (
                    semantic_claim.source_paper
                    if provenance is None or provenance.paper is None
                    else provenance.paper
                ),
                "provenance_page": 0 if provenance is None else provenance.page,
                "provenance_json": (
                    None
                    if provenance_payload is None
                    else json.dumps(provenance_payload, sort_keys=True)
                ),
                "context_id": claim_doc.context.id,
                "premise_kind": "ordinary",
                "branch": None,
                "build_status": "ingested",
                "stage": file_stage,
                "promotion_status": None,
            }
            if file_stage is not None:
                claim_values["stage"] = file_stage
            claim_id = claim_values.get("id")
            if not isinstance(claim_id, str) or not claim_id:
                raise TypeError("compiled claim id must be a non-empty string")
            version_id = claim_values.get("version_id")
            if not isinstance(version_id, str):
                raise TypeError("compiled claim version_id must be a string")
            if claim_id in seen_claim_versions:
                existing_version = seen_claim_versions[claim_id]
                if existing_version == version_id:
                    continue
                conflict_key = (claim_id, existing_version, version_id)
                if conflict_key not in emitted_version_conflicts:
                    quarantine_diagnostics.append(
                        QuarantineDiagnostic(
                            artifact_id=claim_id,
                            kind="claim",
                            diagnostic_kind="claim_version_conflict",
                            message=(
                                f"Claim logical id {claim_id!r} appears with "
                                "multiple version_id values"
                            ),
                            file=semantic_claim.filename,
                        )
                    )
                    emitted_version_conflicts.add(conflict_key)
                continue
            numeric_values = {
                "claim_id": claim_id,
                "value": claim_doc.value,
                "lower_bound": claim_doc.lower_bound,
                "upper_bound": claim_doc.upper_bound,
                "uncertainty": claim_doc.uncertainty,
                "uncertainty_type": claim_doc.uncertainty_type,
                "sample_size": claim_doc.sample_size,
                "unit": claim_doc.unit,
                "value_si": claim_doc.value,
                "lower_bound_si": claim_doc.lower_bound,
                "upper_bound_si": claim_doc.upper_bound,
            }
            text_values = {
                "claim_id": claim_id,
                "conditions_cel": (
                    json.dumps(list(claim_doc.conditions))
                    if claim_doc.conditions
                    else None
                ),
                "conditions_ir": conditions_ir,
                "statement": claim_doc.statement,
                "expression": claim_doc.expression,
                "sympy_generated": claim_doc.sympy,
                "sympy_error": None,
                "name": claim_doc.name,
                "measure": claim_doc.measure,
                "listener_population": claim_doc.listener_population,
                "methodology": claim_doc.methodology,
                "notes": claim_doc.notes,
                "description": None,
                "auto_summary": None,
            }
            algorithm_values = {
                "claim_id": claim_id,
                "body": claim_doc.body,
                "canonical_ast": None,
                "variables_json": (
                    json.dumps([
                        variable.to_payload()
                        for variable in claim_doc.variables
                    ])
                    if claim_doc.variables
                    else None
                ),
                "algorithm_stage": claim_doc.stage,
            }
            claim_model = world_record("claim_core", claim_values)
            numeric_payload = world_record("claim_numeric_payload", numeric_values)
            text_payload = world_record("claim_text_payload", text_values)
            algorithm_payload = world_record("claim_algorithm_payload", algorithm_values)
            source_assertion = ClaimSourceAssertion(
                claim_id=claim_id,
                source_assertion_id=f"ps:assertion:{claim_id}",
                ordinal=0,
            )
            claim_model.numeric_payload = numeric_payload
            claim_model.text_payload = text_payload
            claim_model.algorithm_payload = algorithm_payload
            claim_model.concept_links = []
            claim_model.source_assertions = [source_assertion]
            numeric_payload.claim = claim_model
            text_payload.claim = claim_model
            algorithm_payload.claim = claim_model
            source_assertion.claim = claim_model
            claim_models.append(claim_model)
            numeric_payloads.append(numeric_payload)
            text_payloads.append(text_payload)
            algorithm_payloads.append(algorithm_payload)
            source_assertions.append(source_assertion)
            seen_claim_versions[claim_id] = version_id
            for values in prepare_claim_concept_link_rows(semantic_claim):
                role = values[2]
                if not isinstance(role, ClaimConceptLinkRole):
                    raise TypeError("compiled claim concept-link role must be typed")
                link_key = (values[0], role, values[3], values[1])
                if link_key in seen_claim_link_keys:
                    continue
                seen_claim_link_keys.add(link_key)
                link = ClaimConceptLink(
                    claim_id=values[0],
                    concept_id=values[1],
                    role=role,
                    ordinal=values[3],
                    binding_name=values[4],
                )
                link.claim = claim_model
                claim_model.concept_links.append(link)
                claim_links.append(link)
            deferred_stance_rows, deferred_stance_diagnostics = (
                extract_deferred_stance_rows_with_diagnostics(
                    semantic_claim,
                    claim_index,
                )
            )
            for values in deferred_stance_rows:
                stance_type = coerce_stance_type(values[2])
                if stance_type is None:
                    raise ValueError("deferred stance row requires a stance type")
                stance = StanceRow(
                    claim_id=to_claim_id(values[0]),
                    target_claim_id=to_claim_id(values[1]),
                    stance_type=stance_type,
                    target_justification_id=(
                        None if values[3] is None else to_justification_id(values[3])
                    ),
                    strength=None if values[4] is None else str(values[4]),
                    conditions_differ=(
                        None
                        if values[5] is None
                        else str(
                            json.dumps(values[5])
                            if isinstance(values[5], list)
                            else values[5]
                        )
                    ),
                    note=None if values[6] is None else str(values[6]),
                    resolution_method=None if values[7] is None else str(values[7]),
                    resolution_model=None if values[8] is None else str(values[8]),
                    embedding_model=None if values[9] is None else str(values[9]),
                    embedding_distance=(
                        None if values[10] is None else float(values[10])
                    ),
                    pass_number=None if values[11] is None else int(values[11]),
                    confidence=None if values[12] is None else float(values[12]),
                    opinion_belief=None if values[13] is None else float(values[13]),
                    opinion_disbelief=(
                        None if values[14] is None else float(values[14])
                    ),
                    opinion_uncertainty=(
                        None if values[15] is None else float(values[15])
                    ),
                    opinion_base_rate=(
                        None if values[16] is None else float(values[16])
                    ),
                    perspective_source_claim_id=(
                        None if values[17] is None else to_claim_id(values[17])
                    ),
                )
                row_values: dict[str, object] = {}
                for discriminator in CLAIM_STANCE_DISCRIMINATORS:
                    row_values.update(discriminator.row_values())
                row_values.update(CLAIM_STANCE_STORAGE_MODEL.to_row(stance))
                stance_rows.append(RELATION_EDGE_TABLE.row(**row_values))
            quarantine_diagnostics.extend(deferred_stance_diagnostics)

    return ClaimWriteModels(
        claims=tuple(claim_models),
        numeric_payloads=tuple(numeric_payloads),
        text_payloads=tuple(text_payloads),
        algorithm_payloads=tuple(algorithm_payloads),
        source_assertions=tuple(source_assertions),
        concept_links=tuple(claim_links),
        stance_rows=tuple(stance_rows),
        quarantine_diagnostics=tuple(quarantine_diagnostics),
    )


def compile_authored_justification_sidecar_rows(
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[ProjectionRow, ...]:
    rows, diagnostics = compile_authored_justification_sidecar_rows_with_diagnostics(
        justification_entries,
        claim_index,
    )
    if diagnostics:
        raise sqlite3.IntegrityError(diagnostics[0].message)
    return rows


def compile_authored_justification_sidecar_rows_with_diagnostics(
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[tuple[ProjectionRow, ...], tuple[QuarantineDiagnostic, ...]]:
    valid_claims = set(claim_index.ids())
    rows: list[ProjectionRow] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, justification in justification_entries:
        justification_payload = justification.to_payload()
        justification_id = justification.id
        conclusion = claim_index.resolve_id(justification.conclusion)
        if not isinstance(justification_id, str) or not justification_id:
            raise ValueError(
                f"justification artifact {filename} missing id"
            )
        if not isinstance(conclusion, str) or conclusion not in valid_claims:
            message = (
                f"justification artifact {filename} references "
                f"nonexistent conclusion '{conclusion}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=conclusion or justification.conclusion or filename,
                    kind="justification",
                    diagnostic_kind="justification_validation",
                    message=message,
                    file=filename,
                )
            )
            continue
        resolved_premises: list[str] = []
        missing_premise_ref: str | None = None
        for premise in justification.premises:
            resolved_premise = claim_index.resolve_id(premise)
            if (
                not isinstance(resolved_premise, str)
                or resolved_premise not in valid_claims
            ):
                if isinstance(resolved_premise, str) and resolved_premise:
                    missing_premise_ref = resolved_premise
                elif isinstance(premise, str) and premise:
                    missing_premise_ref = premise
                else:
                    missing_premise_ref = filename
                break
            resolved_premises.append(resolved_premise)
        if missing_premise_ref is not None:
            message = (
                f"justification artifact {filename} references "
                f"nonexistent premise '{missing_premise_ref}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=missing_premise_ref,
                    kind="justification",
                    diagnostic_kind="justification_validation",
                    message=message,
                    file=filename,
                )
            )
            continue

        provenance = justification_payload.get("provenance")
        attack_target = justification_payload.get("attack_target")
        provenance_payload: dict[str, object] = {}
        if isinstance(provenance, dict):
            provenance_payload.update(provenance)
        if isinstance(attack_target, dict):
            provenance_payload["attack_target"] = attack_target

        rows.append(
            JUSTIFICATION_TABLE.row(
                id=justification_id,
                justification_kind=str(justification.rule_kind or "reported_claim"),
                conclusion_claim_id=conclusion,
                premise_claim_ids=json.dumps(resolved_premises),
                source_relation_type=None,
                source_claim_id=None,
                provenance_json=json.dumps(provenance_payload)
                if provenance_payload
                else None,
                rule_strength=str(justification.rule_strength or "defeasible"),
            )
        )
    return tuple(rows), tuple(diagnostics)


def compile_raw_id_quarantine_models(
    records: Sequence[RawIdQuarantineRecord],
) -> RawIdQuarantineModels:
    diagnostics: list[BuildDiagnostic] = []

    for record in records:
        diagnostics.append(
            BuildDiagnostic(
                claim_id=record.synthetic_id,
                source_kind="claim",
                source_ref=record.raw_id,
                diagnostic_kind="raw_id_input",
                severity="error",
                blocking=1,
                message=record.message,
                file=record.filename,
                detail_json=record.detail_json,
            )
        )

    return RawIdQuarantineModels(
        claims=(),
        diagnostics=tuple(diagnostics),
    )


def compile_promotion_blocked_models(
    facts: Sequence[PromotionBlockedClaimFact],
) -> PromotionBlockedModels:
    return PromotionBlockedModels(
        claims=(),
        diagnostics=compile_promotion_blocked_diagnostics(facts),
    )


def compile_conflict_sidecar_rows(
    claim_files: Sequence[ClaimFileEntry],
    concept_registry: dict,
    cel_registry: dict,
    lifting_system=None,
) -> tuple[ProjectionRow, ...]:
    conflict_claims = conflict_claims_from_claim_files(claim_files)
    records = detect_conflicts(
        conflict_claims,
        concept_registry,
        cel_registry,
        lifting_system=lifting_system,
    )
    records.extend(
        detect_transitive_conflicts(
            conflict_claims,
            concept_registry,
            lifting_system=lifting_system,
        )
    )
    return tuple(
        CONFLICT_WITNESS_TABLE.row(
            concept_id=record.concept_id,
            claim_a_id=record.claim_a_id,
            claim_b_id=record.claim_b_id,
            warning_class=record.warning_class.value,
            conditions_a=json.dumps(record.conditions_a),
            conditions_b=json.dumps(record.conditions_b),
            value_a=record.value_a,
            value_b=record.value_b,
            derivation_chain=record.derivation_chain,
        )
        for record in records
    )


def populate_stances(
    conn: sqlite3.Connection,
    rows: Sequence[ProjectionRow],
) -> None:
    from propstore.families.relations.declaration import RELATION_EDGE_TABLE

    RELATION_EDGE_TABLE.insert_rows(conn, (row.values for row in rows))


def populate_authored_justifications(
    conn: sqlite3.Connection,
    rows: Sequence[ProjectionRow],
) -> None:
    JUSTIFICATION_TABLE.insert_rows(conn, rows, or_ignore=True)


def populate_conflicts(
    conn: sqlite3.Connection,
    rows: Sequence[ProjectionRow],
) -> None:
    CONFLICT_WITNESS_TABLE.insert_rows(conn, rows)
