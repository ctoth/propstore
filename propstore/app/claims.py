from collections.abc import Callable
from dataclasses import dataclass
from typing import Mapping

from propstore.claims import ClaimComparisonError, ClaimEmbeddingModelError, ClaimSidecarMissingError, ClaimWorkflowError, UnknownClaimError, _algorithm_variables, _require_sidecar, _required_int, _required_stances_by_claim
from propstore.repository import Repository
from propstore.world import WorldModel


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
        raise ClaimSidecarMissingError(
            "Sidecar not found. Run 'pks build' first."
        ) from exc


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
        raise ClaimWorkflowError(
            "claim relate requires a git-backed repository."
        ) from exc
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