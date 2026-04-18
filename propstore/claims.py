"""Typed claim document loading and semantic access helpers."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING, Any, Mapping, TypeAlias

from quire.artifacts import ArtifactHandle
from propstore.artifacts.documents.claims import ClaimDocument, ClaimsFileDocument
from propstore.artifacts.refs import ClaimsFileRef
from quire.documents import (
    convert_document_value,
    load_document,
)
from quire.tree_path import TreePath as KnowledgePath
from quire.documents import LoadedDocument

if TYPE_CHECKING:
    from propstore.repository import Repository
    from propstore.world import WorldModel

LoadedClaimsFile: TypeAlias = LoadedDocument[ClaimsFileDocument]
ClaimFileEntry: TypeAlias = LoadedClaimsFile | ArtifactHandle[Any, ClaimsFileRef, ClaimsFileDocument]


class ClaimWorkflowError(Exception):
    """Base class for expected claim workflow failures."""


class UnknownClaimError(ClaimWorkflowError):
    def __init__(self, claim_id: str) -> None:
        super().__init__(f"Claim '{claim_id}' not found.")
        self.claim_id = claim_id


class ClaimComparisonError(ClaimWorkflowError):
    pass


class ClaimSidecarMissingError(ClaimWorkflowError):
    pass


class ClaimEmbeddingModelError(ClaimWorkflowError):
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


@dataclass(frozen=True)
class ClaimEmbedRequest:
    claim_id: str | None
    embed_all: bool
    model: str
    batch_size: int = 64


@dataclass(frozen=True)
class ClaimEmbedModelReport:
    model_name: str
    embedded: int
    skipped: int
    errors: int


@dataclass(frozen=True)
class ClaimEmbedReport:
    results: tuple[ClaimEmbedModelReport, ...]


@dataclass(frozen=True)
class ClaimSimilarRequest:
    claim_id: str
    model: str | None
    top_k: int
    agree: bool = False
    disagree: bool = False


@dataclass(frozen=True)
class ClaimSimilarHit:
    distance: float
    claim_id: str
    summary: str
    source_paper: str


@dataclass(frozen=True)
class ClaimSimilarReport:
    hits: tuple[ClaimSimilarHit, ...]


@dataclass(frozen=True)
class ClaimRelateRequest:
    claim_id: str | None
    relate_all: bool
    model: str
    embedding_model: str | None
    top_k: int
    concurrency: int = 20


@dataclass(frozen=True)
class ClaimRelateReport:
    branch: str
    stances: tuple[Mapping[str, object], ...] = ()
    commit_sha: str | None = None
    relpaths: tuple[str, ...] = ()
    claims_processed: int | None = None
    stances_found: int | None = None
    no_relation: int | None = None


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


def show_claim_from_repo(repo: Repository, claim_id: str) -> ClaimShowReport:
    from propstore.world import WorldModel

    try:
        with WorldModel(repo) as world:
            return show_claim(world, claim_id)
    except FileNotFoundError as exc:
        raise ClaimSidecarMissingError("Sidecar not found. Run 'pks build' first.") from exc


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


def compare_algorithm_claims_from_repo(
    repo: Repository,
    request: ClaimCompareRequest,
) -> ClaimCompareReport:
    from propstore.world import WorldModel

    try:
        with WorldModel(repo) as world:
            return compare_algorithm_claims(world, request)
    except FileNotFoundError as exc:
        raise ClaimSidecarMissingError("Sidecar not found. Run 'pks build' first.") from exc


def _require_sidecar(repo: Repository) -> Path:
    sidecar = repo.sidecar_path
    if not sidecar.exists():
        raise ClaimSidecarMissingError("sidecar not found. Run 'pks build' first.")
    return sidecar


def embed_claim_embeddings(
    repo: Repository,
    request: ClaimEmbedRequest,
    *,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> ClaimEmbedReport:
    if not request.claim_id and not request.embed_all:
        raise ClaimWorkflowError("provide a claim ID or use --all")

    from propstore.embed import _load_vec_extension, embed_claims, get_registered_models

    sidecar = _require_sidecar(repo)
    ids = [request.claim_id] if request.claim_id else None
    reports: list[ClaimEmbedModelReport] = []
    conn = sqlite3.connect(sidecar)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        _load_vec_extension(conn)
        if request.model == "all":
            models = get_registered_models(conn)
            if not models:
                raise ClaimEmbeddingModelError(
                    "no models registered. Run embed with a specific model first."
                )
            for model_row in models:
                model_name = str(model_row["model_name"])
                result = embed_claims(
                    conn,
                    model_name,
                    claim_ids=ids,
                    batch_size=request.batch_size,
                    on_progress=(
                        None
                        if on_progress is None
                        else lambda done, total, model_name=model_name: on_progress(
                            model_name,
                            done,
                            total,
                        )
                    ),
                )
                reports.append(_claim_embed_model_report(model_name, result))
        else:
            result = embed_claims(
                conn,
                request.model,
                claim_ids=ids,
                batch_size=request.batch_size,
                on_progress=(
                    None
                    if on_progress is None
                    else lambda done, total: on_progress(request.model, done, total)
                ),
            )
            reports.append(_claim_embed_model_report(request.model, result))
        conn.commit()
    return ClaimEmbedReport(results=tuple(reports))


def _claim_embed_model_report(model_name: str, result: Mapping[str, object]) -> ClaimEmbedModelReport:
    return ClaimEmbedModelReport(
        model_name=model_name,
        embedded=_required_int(result, "embedded"),
        skipped=_required_int(result, "skipped"),
        errors=_required_int(result, "errors"),
    )


def find_similar_claims(
    repo: Repository,
    request: ClaimSimilarRequest,
) -> ClaimSimilarReport:
    from propstore.embed import (
        _load_vec_extension,
        find_similar,
        find_similar_agree,
        find_similar_disagree,
        get_registered_models,
    )

    sidecar = _require_sidecar(repo)
    conn = sqlite3.connect(sidecar)
    conn.row_factory = sqlite3.Row
    _load_vec_extension(conn)
    try:
        if request.agree:
            rows = find_similar_agree(conn, request.claim_id, top_k=request.top_k)
        elif request.disagree:
            rows = find_similar_disagree(conn, request.claim_id, top_k=request.top_k)
        else:
            model = request.model
            if model is None:
                models = get_registered_models(conn)
                if not models:
                    raise ClaimEmbeddingModelError(
                        "no embeddings found. Run 'pks claim embed' first."
                    )
                model = str(models[0]["model_name"])
            rows = find_similar(conn, request.claim_id, model, top_k=request.top_k)
    except ValueError as exc:
        raise ClaimWorkflowError(str(exc)) from exc
    finally:
        conn.close()

    hits = tuple(
        ClaimSimilarHit(
            distance=float(row.get("distance", 0)),
            claim_id=str(row.get("id", "?")),
            summary=str(row.get("auto_summary") or row.get("statement") or ""),
            source_paper=str(row.get("source_paper", "")),
        )
        for row in rows
    )
    return ClaimSimilarReport(hits=hits)


def relate_claims(
    repo: Repository,
    request: ClaimRelateRequest,
    *,
    on_progress: Callable[[int, int], None] | None = None,
) -> ClaimRelateReport:
    from propstore.embed import _load_vec_extension
    from propstore.proposals import commit_stance_proposals, stance_proposal_branch
    from propstore.relate import relate_all as relate_all_fn
    from propstore.relate import relate_claim

    try:
        repo.snapshot.head_sha()
    except ValueError as exc:
        raise ClaimWorkflowError("claim relate requires a git-backed repository.") from exc
    sidecar = _require_sidecar(repo)

    conn = sqlite3.connect(sidecar)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        _load_vec_extension(conn)
        if request.claim_id and not request.relate_all:
            stances = tuple(
                relate_claim(
                    conn,
                    request.claim_id,
                    request.model,
                    request.embedding_model,
                    request.top_k,
                )
            )
            if not stances:
                return ClaimRelateReport(branch=stance_proposal_branch(repo))
            commit_sha, committed_relpaths = commit_stance_proposals(
                repo,
                {request.claim_id: list(stances)},
                request.model,
            )
            return ClaimRelateReport(
                branch=stance_proposal_branch(repo),
                stances=stances,
                commit_sha=commit_sha,
                relpaths=tuple(committed_relpaths),
            )
        if request.relate_all:
            result = relate_all_fn(
                conn,
                request.model,
                request.embedding_model,
                request.top_k,
                concurrency=request.concurrency,
                on_progress=on_progress,
            )
            stances_by_claim = _required_stances_by_claim(
                result.get("stances_by_claim", {})
            )
            commit_sha: str | None = None
            relpaths: tuple[str, ...] = ()
            if stances_by_claim:
                commit_sha, committed_relpaths = commit_stance_proposals(
                    repo,
                    stances_by_claim,
                    request.model,
                )
                relpaths = tuple(committed_relpaths)
            return ClaimRelateReport(
                branch=stance_proposal_branch(repo),
                commit_sha=commit_sha,
                relpaths=relpaths,
                claims_processed=_required_int(result, "claims_processed"),
                stances_found=_required_int(result, "stances_found"),
                no_relation=_required_int(result, "no_relation"),
            )
    raise ClaimWorkflowError("provide a claim ID or use --all")


def _required_int(result: Mapping[str, object], key: str) -> int:
    value = result[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ClaimWorkflowError(f"expected integer field '{key}'")
    return value


def _required_stances_by_claim(value: object) -> dict[str, list[dict[str, object]]]:
    if not isinstance(value, Mapping):
        raise ClaimWorkflowError("expected stances_by_claim mapping")
    stances_by_claim: dict[str, list[dict[str, object]]] = {}
    for claim_id, stances in value.items():
        if not isinstance(claim_id, str) or not isinstance(stances, list):
            raise ClaimWorkflowError("expected stances_by_claim mapping of claim IDs to stance lists")
        if not all(isinstance(stance, dict) for stance in stances):
            raise ClaimWorkflowError("expected stance entries to be mappings")
        stances_by_claim[claim_id] = stances
    return stances_by_claim


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


def claim_file_filename(claim_file: ClaimFileEntry) -> str:
    filename = getattr(claim_file, "filename", None)
    if isinstance(filename, str):
        return filename
    ref = getattr(claim_file, "ref", None)
    name = getattr(ref, "name", None)
    if isinstance(name, str):
        return name
    raise TypeError("claim file entry has no filename or ref name")


def claim_file_claims(claim_file: ClaimFileEntry) -> tuple[ClaimDocument, ...]:
    return claim_file.document.claims


def claim_file_source_paper(claim_file: ClaimFileEntry) -> str:
    return claim_file.document.source.paper


def claim_file_stage(claim_file: ClaimFileEntry) -> str | None:
    return claim_file.document.stage


def claim_file_payload(claim_file: ClaimFileEntry) -> dict[str, Any]:
    return claim_file.document.to_payload()
