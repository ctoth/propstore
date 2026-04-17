"""Typed claim document loading and semantic access helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, TypeAlias

from propstore.artifacts.documents.claims import ClaimDocument, ClaimsFileDocument
from propstore.artifacts.schema import (
    convert_document_value,
    load_document,
    load_document_dir,
)
from propstore.knowledge_path import KnowledgePath
from propstore.loaded import LoadedDocument

if TYPE_CHECKING:
    from propstore.world import WorldModel

LoadedClaimsFile: TypeAlias = LoadedDocument[ClaimsFileDocument]


class ClaimWorkflowError(Exception):
    """Base class for expected claim workflow failures."""


class UnknownClaimError(ClaimWorkflowError):
    def __init__(self, claim_id: str) -> None:
        super().__init__(f"Claim '{claim_id}' not found.")
        self.claim_id = claim_id


class ClaimComparisonError(ClaimWorkflowError):
    pass


@dataclass(frozen=True)
class ClaimShowReport:
    logical_id: object
    artifact_id: object
    version_id: object
    concept_id: object
    claim_type: object
    value: object
    unit: str
    value_si: object
    canonical_unit: str
    lower_bound: object
    lower_bound_si: object
    upper_bound: object
    upper_bound_si: object
    uncertainty: object
    sample_size: object
    source_paper: object
    conditions_cel: object


@dataclass(frozen=True)
class ClaimCompareRequest:
    claim_a_id: str
    claim_b_id: str
    known_values: Mapping[str, float] | None = None


@dataclass(frozen=True)
class ClaimCompareReport:
    tier: object
    equivalent: object
    similarity: float
    details: object


def show_claim(
    world: WorldModel,
    claim_id: str,
) -> ClaimShowReport:
    from propstore.core.row_types import coerce_claim_row, coerce_concept_row

    claim_input = world.get_claim(claim_id)
    if claim_input is None:
        raise UnknownClaimError(claim_id)
    claim_data = coerce_claim_row(claim_input).to_dict()
    concept_id = claim_data.get("concept_id")
    canonical_unit = ""
    if isinstance(concept_id, str):
        concept = world.get_concept(concept_id)
        if concept is not None:
            canonical_unit = str(
                coerce_concept_row(concept).attributes.get("unit_symbol") or ""
            )
    return ClaimShowReport(
        logical_id=claim_data.get("logical_id") or claim_data.get("primary_logical_id"),
        artifact_id=claim_data.get("artifact_id"),
        version_id=claim_data.get("version_id"),
        concept_id=concept_id,
        claim_type=claim_data.get("type"),
        value=claim_data.get("value"),
        unit=str(claim_data.get("unit") or ""),
        value_si=claim_data.get("value_si"),
        canonical_unit=canonical_unit,
        lower_bound=claim_data.get("lower_bound"),
        lower_bound_si=claim_data.get("lower_bound_si"),
        upper_bound=claim_data.get("upper_bound"),
        upper_bound_si=claim_data.get("upper_bound_si"),
        uncertainty=claim_data.get("uncertainty"),
        sample_size=claim_data.get("sample_size"),
        source_paper=claim_data.get("source_paper"),
        conditions_cel=claim_data.get("conditions_cel"),
    )


def compare_algorithm_claims(
    world: WorldModel,
    request: ClaimCompareRequest,
) -> ClaimCompareReport:
    from ast_equiv import compare as ast_compare
    from propstore.core.row_types import coerce_claim_row

    claim_a_input = world.get_claim(request.claim_a_id)
    if claim_a_input is None:
        raise UnknownClaimError(request.claim_a_id)
    claim_b_input = world.get_claim(request.claim_b_id)
    if claim_b_input is None:
        raise UnknownClaimError(request.claim_b_id)

    claim_a = coerce_claim_row(claim_a_input).to_dict()
    claim_b = coerce_claim_row(claim_b_input).to_dict()
    body_a = claim_a.get("body")
    body_b = claim_b.get("body")
    if not body_a or not body_b:
        raise ClaimComparisonError(
            "Both claims must be algorithm claims with a body."
        )

    result = ast_compare(
        body_a,
        _algorithm_variables(claim_a),
        body_b,
        _algorithm_variables(claim_b),
        known_values=dict(request.known_values) if request.known_values else None,
    )
    return ClaimCompareReport(
        tier=result.tier,
        equivalent=result.equivalent,
        similarity=float(result.similarity),
        details=result.details,
    )


def _algorithm_variables(claim: Mapping[str, object]) -> dict[str, str]:
    variables_json = claim.get("variables_json")
    if not variables_json:
        return {}
    variables = json.loads(str(variables_json))
    if not isinstance(variables, list):
        raise ValueError("algorithm variables must be stored as a list of bindings")
    result: dict[str, str] = {}
    for variable in variables:
        if isinstance(variable, dict):
            name = variable.get("name") or variable.get("symbol")
            concept = variable.get("concept", "")
            if name:
                result[str(name)] = str(concept)
    return result


def load_claim_file(
    path: KnowledgePath | Path,
    *,
    knowledge_root: KnowledgePath | Path | None = None,
) -> LoadedClaimsFile:
    return load_document(
        path,
        ClaimsFileDocument,
        knowledge_root=knowledge_root,
    )


def load_claim_files(claims_dir: KnowledgePath | Path | None) -> list[LoadedClaimsFile]:
    """Load all direct child claim YAML files from a claims subtree."""

    return load_document_dir(claims_dir, ClaimsFileDocument)


def loaded_claim_file_from_payload(
    *,
    filename: str,
    source_path: KnowledgePath | Path | None,
    data: dict[str, Any],
    knowledge_root: KnowledgePath | Path | None = None,
) -> LoadedClaimsFile:
    label = filename if source_path is None else str(source_path)
    return LoadedDocument(
        filename=filename,
        source_path=source_path,
        knowledge_root=knowledge_root,
        document=convert_document_value(
            data,
            ClaimsFileDocument,
            source=label,
        ),
    )


def claim_file_claims(claim_file: LoadedClaimsFile) -> tuple[ClaimDocument, ...]:
    return claim_file.document.claims


def claim_file_source_paper(claim_file: LoadedClaimsFile) -> str:
    return claim_file.document.source.paper


def claim_file_stage(claim_file: LoadedClaimsFile) -> str | None:
    return claim_file.document.stage


def claim_file_payload(claim_file: LoadedClaimsFile) -> dict[str, Any]:
    return claim_file.document.to_payload()
