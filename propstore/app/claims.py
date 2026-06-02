from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Mapping

from propstore.families.claims.sidecar_runtime import (
    embed_claims_for_request,
    relate_all_from_sidecar,
    relate_claim_from_sidecar,
)
from propstore.claims import LoadedClaimsFile
from propstore.repository import Repository
from quire.tree_path import TreePath as KnowledgePath

if TYPE_CHECKING:
    from quire.derived_store import DerivedStoreHandle

    from propstore.world.model import WorldQuery


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


def compare_algorithm_claims_from_repo(
    repo: Repository,
    request: ClaimCompareRequest,
) -> ClaimCompareReport:
    from propstore.world.model import WorldQuery

    try:
        with WorldQuery(repo) as world:
            return compare_algorithm_claims(world, request)
    except FileNotFoundError as exc:
        raise ClaimSidecarMissingError(
            "Sidecar not found. Run 'pks build' first."
        ) from exc


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
    from quire.documents import LoadedDocument

    tree = repo.tree()
    files = [
        LoadedClaimsFile(
            filename=handle.ref.artifact_id,
            artifact_path=tree / handle.address.require_path(),
            store_root=tree,
            document=handle.document,
        )
        for handle in repo.families.claims.iter_handles()
    ]
    if not files:
        return ClaimConflictsReport(file_count=0, conflicts=())

    context = build_compilation_context_from_repo(repo, claim_files=list(files))
    registry = concept_registry_for_context(context)
    tree = repo.tree()
    contexts = [
        LoadedDocument(
            filename=handle.ref.name,
            artifact_path=tree / handle.address.require_path(),
            store_root=tree,
            document=handle.document,
        )
        for handle in repo.families.contexts.iter_handles()
    ]
    lifting_system = loaded_contexts_to_lifting_system(contexts) if contexts else None
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


def _require_sidecar(repo: Repository) -> DerivedStoreHandle:
    from propstore.compiler.workflows import build_repository_world_store

    handle, _rebuilt = build_repository_world_store(repo)
    if not handle.path.exists():
        raise ClaimSidecarMissingError("sidecar not found. Run 'pks build' first.")
    return handle


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
        raise ClaimWorkflowError("provide a claim ID or request all claims")

    sidecar = _require_sidecar(repo)
    try:
        results = embed_claims_for_request(
            sidecar,
            claim_id=request.claim_id,
            embed_all=request.embed_all,
            model=request.model,
            batch_size=request.batch_size,
            on_progress=on_progress,
        )
    except LookupError as exc:
        raise ClaimEmbeddingModelError(
            "no models registered. Run embed with a specific model first."
        ) from exc
    reports = [
        _claim_embed_model_report(model_name, result) for model_name, result in results
    ]
    return ClaimEmbedReport(results=tuple(reports))


def find_similar_claims(
    repo: Repository,
    request: ClaimSimilarRequest,
) -> ClaimSimilarReport:
    sidecar = _require_sidecar(repo)
    try:
        if request.agree:
            from propstore.families.embeddings.declaration import find_similar_agree

            similarity_hits = find_similar_agree(
                sidecar,
                request.claim_id,
                top_k=request.top_k,
            )
        elif request.disagree:
            from propstore.families.embeddings.declaration import find_similar_disagree

            similarity_hits = find_similar_disagree(
                sidecar,
                request.claim_id,
                top_k=request.top_k,
            )
        else:
            from propstore.world.model import WorldQuery

            with WorldQuery(derived_store=sidecar) as world:
                similarity_hits = world.similar_claims(
                    request.claim_id,
                    request.model,
                    top_k=request.top_k,
                )
    except LookupError as exc:
        raise ClaimEmbeddingModelError(
            "no embeddings found. Run 'pks claim embed' first."
        ) from exc
    except ValueError as exc:
        raise ClaimWorkflowError(str(exc)) from exc

    report_hits = tuple(
        ClaimSimilarHit(
            distance=hit.distance,
            claim_id=str(hit.claim_id),
            summary=hit.auto_summary or hit.statement or "",
            source_paper=hit.source_paper or "",
        )
        for hit in similarity_hits
    )
    return ClaimSimilarReport(hits=report_hits)


def relate_claims(
    repo: Repository,
    request: ClaimRelateRequest,
    *,
    on_progress: Callable[[int, int], None] | None = None,
) -> ClaimRelateReport:
    from propstore.families.stances.lifecycle import (
        commit_stance_proposals,
        stance_proposal_branch,
    )

    try:
        repo.require_git().head_sha()
    except ValueError as exc:
        raise ClaimWorkflowError(
            "claim relate requires a git-backed repository."
        ) from exc
    sidecar = _require_sidecar(repo)

    if request.claim_id and not request.relate_all:
        stances = tuple(
            relate_claim_from_sidecar(
                sidecar,
                request.claim_id,
                request.model,
                request.embedding_model,
                request.top_k,
            )
        )
        commit_sha, committed_relpaths = commit_stance_proposals(
            repo,
            {request.claim_id: list(stances)} if stances else {},
            request.model,
        )
        return ClaimRelateReport(
            branch=stance_proposal_branch(),
            stances=stances,
            commit_sha=commit_sha,
            relpaths=tuple(committed_relpaths),
        )
    if request.relate_all:
        result = relate_all_from_sidecar(
            sidecar,
            request.model,
            request.embedding_model,
            request.top_k,
            concurrency=request.concurrency,
            on_progress=on_progress,
        )
        stances_by_claim = _required_stances_by_claim(
            result.get("stances_by_claim", {})
        )
        commit_sha, committed_relpaths = commit_stance_proposals(
            repo,
            stances_by_claim,
            request.model,
        )
        return ClaimRelateReport(
            branch=stance_proposal_branch(),
            commit_sha=commit_sha,
            relpaths=tuple(committed_relpaths),
            claims_processed=_required_int(result, "claims_processed"),
            stances_found=_required_int(result, "stances_found"),
            no_relation=_required_int(result, "no_relation"),
        )
    raise ClaimWorkflowError("provide a claim ID or request all claims")
