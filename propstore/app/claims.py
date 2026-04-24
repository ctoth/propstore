from __future__ import annotations

import contextlib
from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Mapping

from propstore.repository import Repository
from propstore.sidecar.sqlite import connect_sidecar
from propstore.world import WorldModel
from quire.tree_path import TreePath as KnowledgePath


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


class ClaimPathError(ClaimWorkflowError):
    pass


class ClaimValidationDocumentError(ClaimWorkflowError):
    pass


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
class ClaimValidationRequest:
    claims_path: Path | None = None
    concepts_path: Path | None = None


@dataclass(frozen=True)
class ClaimValidateFileRequest:
    filepath: Path
    concepts_path: Path | None = None


@dataclass(frozen=True)
class ClaimValidationReport:
    file_count: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class ClaimConflictsRequest:
    concept: str | None = None
    warning_class: str | None = None


@dataclass(frozen=True)
class ClaimConflictLine:
    warning_class: str
    concept_id: str
    claim_a_id: str
    claim_b_id: str
    value_a: object
    value_b: object
    derivation_chain: object


@dataclass(frozen=True)
class ClaimConflictsReport:
    file_count: int
    conflicts: tuple[ClaimConflictLine, ...]


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
        raise ClaimComparisonError("Both claims must be algorithm claims with a body.")

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
        raise ClaimSidecarMissingError(
            "Sidecar not found. Run 'pks build' first."
        ) from exc


def validate_claim_files(
    repo: Repository,
    request: ClaimValidationRequest,
) -> ClaimValidationReport:
    from quire.documents import DocumentSchemaError, load_document_dir
    from quire.tree_path import coerce_tree_path as coerce_knowledge_path

    from propstore.compiler.context import (
        build_compilation_context_from_loaded,
        build_compilation_context_from_repo,
    )
    from propstore.families.claims.passes import validate_claims
    from propstore.families.concepts.stages import load_concepts
    from propstore.families.claims.documents import ClaimsFileDocument

    claims_root = (
        coerce_knowledge_path(request.claims_path)
        if request.claims_path is not None
        else None
    )
    concepts_root, forms_root = _concept_override_roots(request.concepts_path)

    if claims_root is not None and not claims_root.exists():
        raise ClaimPathError(
            f"Claims directory '{claims_root.as_posix()}' does not exist"
        )

    try:
        if claims_root is None:
            files = [
                repo.families.claims.require_handle(ref)
                for ref in repo.families.claims.iter()
            ]
        else:
            files = load_document_dir(claims_root, ClaimsFileDocument)
        if concepts_root is None:
            context = build_compilation_context_from_repo(repo, claim_files=files)
        else:
            context = build_compilation_context_from_loaded(
                load_concepts(concepts_root),
                forms_dir=forms_root,
                claim_files=files,
            )
    except DocumentSchemaError as exc:
        raise ClaimValidationDocumentError(str(exc)) from exc

    if not files:
        return ClaimValidationReport(file_count=0, warnings=(), errors=())

    result = validate_claims(files, context)
    return ClaimValidationReport(
        file_count=len(files),
        warnings=tuple(str(warning) for warning in result.warnings),
        errors=tuple(str(error) for error in result.errors),
    )


def validate_claim_file(
    repo: Repository,
    request: ClaimValidateFileRequest,
) -> ClaimValidationReport:
    from quire.documents import DocumentSchemaError

    from propstore.compiler.context import (
        build_compilation_context_from_loaded,
        build_compilation_context_from_repo,
    )
    from propstore.families.claims.passes import validate_single_claim_file
    from propstore.families.concepts.stages import load_concepts

    concepts_root, forms_root = _concept_override_roots(request.concepts_path)
    try:
        if concepts_root is None:
            context = build_compilation_context_from_repo(repo)
        else:
            context = build_compilation_context_from_loaded(
                load_concepts(concepts_root),
                forms_dir=forms_root,
            )
        result = validate_single_claim_file(request.filepath, context)
    except DocumentSchemaError as exc:
        raise ClaimValidationDocumentError(str(exc)) from exc

    return ClaimValidationReport(
        file_count=1,
        warnings=tuple(str(warning) for warning in result.warnings),
        errors=tuple(str(error) for error in result.errors),
    )


def detect_claim_conflicts(
    repo: Repository,
    request: ClaimConflictsRequest,
) -> ClaimConflictsReport:
    from propstore.compiler.context import (
        build_compilation_context_from_repo,
        concept_registry_for_context,
    )
    from propstore.conflict_detector import ConflictClass, detect_conflicts
    from propstore.conflict_detector.collectors import conflict_claims_from_claim_files
    from propstore.families.contexts.stages import loaded_contexts_to_lifting_system

    files = [
        repo.families.claims.require_handle(ref)
        for ref in repo.families.claims.iter()
    ]
    if not files:
        return ClaimConflictsReport(file_count=0, conflicts=())

    context = build_compilation_context_from_repo(repo, claim_files=list(files))
    registry = concept_registry_for_context(context)
    contexts = [
        repo.families.contexts.require_handle(ref)
        for ref in repo.families.contexts.iter()
    ]
    lifting_system = (
        loaded_contexts_to_lifting_system(contexts)
        if contexts
        else None
    )
    records = detect_conflicts(
        conflict_claims_from_claim_files(files),
        registry,
        context.cel_registry,
        lifting_system=lifting_system,
    )
    if request.concept:
        records = [record for record in records if record.concept_id == request.concept]
    if request.warning_class:
        requested_class = ConflictClass(request.warning_class)
        records = [
            record for record in records if record.warning_class == requested_class
        ]
    return ClaimConflictsReport(
        file_count=len(files),
        conflicts=tuple(
            ClaimConflictLine(
                warning_class=record.warning_class.value,
                concept_id=str(record.concept_id),
                claim_a_id=str(record.claim_a_id),
                claim_b_id=str(record.claim_b_id),
                value_a=record.value_a,
                value_b=record.value_b,
                derivation_chain=record.derivation_chain,
            )
            for record in records
        ),
    )


def _concept_override_roots(
    concepts_path: Path | None,
) -> tuple[KnowledgePath | None, KnowledgePath | None]:
    from quire.tree_path import coerce_tree_path as coerce_knowledge_path

    if concepts_path is None:
        return None, None
    concepts_root = coerce_knowledge_path(concepts_path)
    if not concepts_root.exists():
        raise ClaimPathError(
            f"Concepts directory '{concepts_root.as_posix()}' does not exist"
        )
    forms_root = coerce_knowledge_path(concepts_path.parent / "forms")
    if not forms_root.exists():
        raise ClaimPathError(
            "Concepts override requires sibling forms directory "
            f"'{forms_root.as_posix()}'"
        )
    return concepts_root, forms_root


def _require_sidecar(repo: Repository) -> Path:
    sidecar = repo.sidecar_path
    if not sidecar.exists():
        raise ClaimSidecarMissingError("sidecar not found. Run 'pks build' first.")
    return sidecar


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
            raise ClaimWorkflowError(
                "expected stances_by_claim mapping of claim IDs to stance lists"
            )
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


def _claim_embed_model_report(
    model_name: str, result: Mapping[str, object]
) -> ClaimEmbedModelReport:
    return ClaimEmbedModelReport(
        model_name=model_name,
        embedded=_required_int(result, "embedded"),
        skipped=_required_int(result, "skipped"),
        errors=_required_int(result, "errors"),
    )


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
    conn = connect_sidecar(sidecar)
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
    conn = connect_sidecar(sidecar)
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
        raise ClaimWorkflowError(
            "claim relate requires a git-backed repository."
        ) from exc
    sidecar = _require_sidecar(repo)

    conn = connect_sidecar(sidecar)
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
