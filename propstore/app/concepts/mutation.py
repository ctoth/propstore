"""Typed concept sidecar query and embedding workflows."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from dataclasses import dataclass, field
from copy import deepcopy
from datetime import date
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from propstore.repository import Repository

from propstore.claims import (
    ClaimFileEntry,
    claim_file_filename,
    claim_file_payload,
    loaded_claim_file_from_payload,
)
from propstore.canonical_namespaces import assert_alias_does_not_target_reserved_namespace
from propstore.compiler.context import build_compilation_context_from_loaded
from propstore.families.claims.passes import validate_claims
from propstore.compiler.references import build_claim_reference_lookup
from propstore.concept_ids import candidate_concept_id_for_repo, reserve_concept_id_candidate
from propstore.core.concept_relationship_types import VALID_CONCEPT_RELATIONSHIP_TYPES
from propstore.families.concepts.passes import (
    ConceptPipelineContext,
    run_concept_pipeline,
)
from propstore.families.concepts.stages import (
    LoadedConcept,
    concept_document_to_payload,
    concept_document_to_record_payload,
    parse_concept_record,
    parse_concept_record_document,
)
from propstore.families.claims.documents import ClaimsFileDocument
from propstore.families.concepts.documents import ConceptDocument
from propstore.families.identity.claims import normalize_claim_file_payload
from propstore.families.identity.concepts import normalize_canonical_concept_payload
from propstore.families.identity.logical_ids import format_logical_id, primary_logical_id
from propstore.families.registry import ClaimsFileRef, ConceptFileRef
from propstore.families.forms.stages import FormDefinition, parse_form
from propstore.sidecar.sqlite import connect_sidecar
from propstore.semantic_passes.types import PipelineResult
from propstore.app.repository_views import AppRepositoryViewRequest

RELATIONSHIP_TYPES = tuple(sorted(VALID_CONCEPT_RELATIONSHIP_TYPES))
QUALIA_ROLES = ("formal", "constitutive", "telic", "agentive")
PROTO_ROLE_KINDS = ("agent", "patient")


class ConceptWorkflowError(Exception):
    """Base class for expected concept workflow failures."""


class ConceptSidecarMissingError(ConceptWorkflowError):
    pass


class ConceptEmbeddingModelError(ConceptWorkflowError):
    pass


class UnknownConceptError(ConceptWorkflowError):
    def __init__(self, concept_id: str) -> None:
        super().__init__(f"Concept '{concept_id}' not found")
        self.concept_id = concept_id


class ConceptMutationError(ConceptWorkflowError):
    pass


class ConceptValidationError(ConceptWorkflowError):
    def __init__(
        self,
        message: str,
        *,
        errors: tuple[str, ...],
        warnings: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message)
        self.errors = errors
        self.warnings = warnings


class ConceptDisplayError(ConceptWorkflowError):
    pass


@dataclass(frozen=True)
class ConceptSearchRequest:
    query: str
    limit: int = 20
    repository_view: AppRepositoryViewRequest = field(default_factory=AppRepositoryViewRequest)


@dataclass(frozen=True)
class ConceptSearchHit:
    handle: str
    logical_id: str | None
    canonical_name: str
    definition: str
    status: str | None = None


@dataclass(frozen=True)
class ConceptSearchReport:
    hits: tuple[ConceptSearchHit, ...]


@dataclass(frozen=True)
class ConceptListRequest:
    domain: str | None = None
    status: str | None = None
    limit: int = 200
    repository_view: AppRepositoryViewRequest = field(default_factory=AppRepositoryViewRequest)


@dataclass(frozen=True)
class ConceptListEntry:
    handle: str
    canonical_name: str
    status: str


@dataclass(frozen=True)
class ConceptListReport:
    concepts_found: bool
    entries: tuple[ConceptListEntry, ...]


@dataclass(frozen=True)
class ConceptCategoryEntry:
    canonical_name: str
    values: tuple[str, ...]
    extensible: bool


@dataclass(frozen=True)
class ConceptCategoriesReport:
    entries: tuple[ConceptCategoryEntry, ...]

    def as_dict(self) -> dict[str, dict[str, object]]:
        return {
            entry.canonical_name: {
                "values": list(entry.values),
                "extensible": entry.extensible,
            }
            for entry in self.entries
        }


@dataclass(frozen=True)
class ConceptShowRequest:
    concept_id_or_name: str


@dataclass(frozen=True)
class ConceptShowReport:
    rendered: str


@dataclass(frozen=True)
class ConceptAlignmentBuildRequest:
    sources: tuple[str, ...]


@dataclass(frozen=True)
class ConceptAlignmentQueryRequest:
    cluster_id: str
    mode: str = "credulous"
    operator: str | None = None


@dataclass(frozen=True)
class ConceptAlignmentDecisionRequest:
    cluster_id: str
    accepted: tuple[str, ...]
    rejected: tuple[str, ...]


@dataclass(frozen=True)
class ConceptAlignmentReport:
    alignment_id: str


@dataclass(frozen=True)
class ConceptAlignmentQueryScore:
    argument_id: str
    score: object


@dataclass(frozen=True)
class ConceptAlignmentQueryReport:
    accepted_argument_ids: tuple[str, ...] = ()
    scores: tuple[ConceptAlignmentQueryScore, ...] = ()


@dataclass(frozen=True)
class ConceptEmbedRequest:
    concept_id: str | None
    embed_all: bool
    model: str
    batch_size: int = 64


@dataclass(frozen=True)
class ConceptEmbedModelReport:
    model_name: str
    embedded: int
    skipped: int
    errors: int


@dataclass(frozen=True)
class ConceptEmbedReport:
    results: tuple[ConceptEmbedModelReport, ...]


@dataclass(frozen=True)
class ConceptSimilarRequest:
    concept_id: str
    model: str | None
    top_k: int
    agree: bool = False
    disagree: bool = False


@dataclass(frozen=True)
class ConceptSimilarHit:
    distance: float
    concept_id: str
    canonical_name: str
    definition: str


@dataclass(frozen=True)
class ConceptSimilarReport:
    hits: tuple[ConceptSimilarHit, ...]


@dataclass(frozen=True)
class ConceptMutationReport:
    lines: tuple[str, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConceptAddRequest:
    domain: str
    name: str
    definition: str
    form_name: str
    values: tuple[str, ...] = ()
    closed: bool = False
    dry_run: bool = False


@dataclass(frozen=True)
class ConceptAliasRequest:
    concept_id: str
    name: str
    source: str
    note: str | None = None
    dry_run: bool = False


@dataclass(frozen=True)
class ConceptRenameRequest:
    concept_id: str
    name: str
    dry_run: bool = False


@dataclass(frozen=True)
class ConceptDeprecateRequest:
    concept_id: str
    replaced_by: str
    dry_run: bool = False


@dataclass(frozen=True)
class ConceptLinkRequest:
    source_id: str
    rel_type: str
    target_id: str
    paper_source: str | None = None
    note: str | None = None
    conditions: str | None = None
    dry_run: bool = False


@dataclass(frozen=True)
class ConceptQualiaAddRequest:
    concept_id: str
    role: str
    target_concept: str
    type_constraint: str | None
    asserter: str
    timestamp: str
    source_artifact_code: str
    method: str
    dry_run: bool = False


@dataclass(frozen=True)
class ConceptDescriptionKindRequest:
    concept_id: str
    name: str
    reference_handle: str
    slots: tuple[str, ...]
    dry_run: bool = False


@dataclass(frozen=True)
class ConceptProtoRoleRequest:
    concept_id: str
    role_name: str
    role_kind: str
    property_name: str
    value: float
    asserter: str
    timestamp: str
    source_artifact_code: str
    method: str
    dry_run: bool = False


@dataclass(frozen=True)
class ConceptAddValueRequest:
    concept_name: str
    value: str
    dry_run: bool = False


def search_concepts(
    repo: Repository,
    request: ConceptSearchRequest,
) -> ConceptSearchReport:
    sidecar = _require_sidecar(repo)
    conn = connect_sidecar(sidecar)
    with contextlib.closing(conn):
        rows = conn.execute(
            "SELECT concept.primary_logical_id, concept_fts.canonical_name, concept_fts.definition "
            "FROM concept_fts JOIN concept ON concept.id = concept_fts.concept_id "
            "WHERE concept_fts MATCH ? LIMIT ?",
            (request.query, request.limit),
        ).fetchall()
    return ConceptSearchReport(
        hits=tuple(
            ConceptSearchHit(
                handle=str(row[0]),
                logical_id=str(row[0]),
                canonical_name=str(row[1]),
                definition=str(row[2] or ""),
            )
            for row in rows
        )
    )


def list_concepts(
    repo: Repository,
    request: ConceptListRequest,
) -> ConceptListReport:
    loaded_concepts = _loaded_concepts(repo)
    if not loaded_concepts:
        return ConceptListReport(concepts_found=False, entries=())

    entries: list[ConceptListEntry] = []
    for concept_entry in loaded_concepts:
        data = concept_entry.record.to_payload()
        concept_domain = str(data.get("domain", ""))
        concept_status = str(data.get("status", ""))
        if request.domain and concept_domain != request.domain:
            continue
        if request.status and concept_status != request.status:
            continue
        entries.append(
            ConceptListEntry(
                handle=_concept_display_handle(data),
                canonical_name=str(data.get("canonical_name", "?")),
                status=concept_status,
            )
        )
    return ConceptListReport(concepts_found=True, entries=tuple(entries))


def list_concept_categories(repo: Repository) -> ConceptCategoriesReport:
    entries: list[ConceptCategoryEntry] = []
    for concept_entry in _loaded_concepts(repo):
        data = concept_entry.record.to_payload()
        if data.get("form") != "category":
            continue
        raw_form_parameters = data.get("form_parameters")
        if raw_form_parameters is None:
            form_parameters: Mapping[str, object] = {}
        elif isinstance(raw_form_parameters, Mapping):
            form_parameters = raw_form_parameters
        else:
            raise ConceptDisplayError(
                f"'{data.get('canonical_name')}' form_parameters must be a mapping"
            )
        raw_values = form_parameters.get("values", [])
        values = (
            tuple(str(value) for value in raw_values)
            if isinstance(raw_values, list)
            else ()
        )
        entries.append(
            ConceptCategoryEntry(
                canonical_name=str(data["canonical_name"]),
                values=values,
                extensible=bool(form_parameters.get("extensible", True)),
            )
        )
    return ConceptCategoriesReport(entries=tuple(entries))


def show_concept(
    repo: Repository,
    request: ConceptShowRequest,
) -> ConceptShowReport:
    from propstore.source import load_alignment_artifact

    handle = request.concept_id_or_name
    if handle.startswith("align:"):
        try:
            _, artifact = load_alignment_artifact(repo, handle)
        except FileNotFoundError as exc:
            raise UnknownConceptError(handle) from exc
        return ConceptShowReport(
            rendered=repo.families.concept_alignments.render(artifact)
        )

    concept_entry = _find_concept_entry(repo, handle)
    if concept_entry is None:
        raise UnknownConceptError(handle)
    ref = _concept_ref(concept_entry)
    document = _concept_document(repo, ref, concept_entry.record.to_payload())
    return ConceptShowReport(rendered=repo.families.concepts.render(document))


def build_concept_alignment(
    repo: Repository,
    request: ConceptAlignmentBuildRequest,
) -> ConceptAlignmentReport:
    from propstore.source import align_sources

    artifact = align_sources(repo, list(request.sources))
    return ConceptAlignmentReport(alignment_id=artifact.id)


def query_concept_alignment(
    repo: Repository,
    request: ConceptAlignmentQueryRequest,
) -> ConceptAlignmentQueryReport:
    from propstore.source import load_alignment_artifact

    try:
        _, artifact = load_alignment_artifact(repo, request.cluster_id)
    except FileNotFoundError as exc:
        raise ConceptDisplayError(
            f"Concept alignment '{request.cluster_id}' not found"
        ) from exc
    if request.operator is not None:
        scores = artifact.queries.operator_scores.get(request.operator, {})
        return ConceptAlignmentQueryReport(
            scores=tuple(
                ConceptAlignmentQueryScore(argument_id=str(argument_id), score=score)
                for argument_id, score in sorted(scores.items())
            )
        )
    accepted = (
        artifact.queries.skeptical_acceptance
        if request.mode == "skeptical"
        else artifact.queries.credulous_acceptance
    )
    return ConceptAlignmentQueryReport(
        accepted_argument_ids=tuple(str(argument_id) for argument_id in accepted)
    )


def decide_concept_alignment(
    repo: Repository,
    request: ConceptAlignmentDecisionRequest,
) -> ConceptAlignmentReport:
    from propstore.source import decide_alignment

    updated = decide_alignment(
        repo,
        request.cluster_id,
        accept=list(request.accepted),
        reject=list(request.rejected),
    )
    return ConceptAlignmentReport(alignment_id=updated.id)


def promote_concept_alignment(
    repo: Repository,
    cluster_id: str,
) -> ConceptAlignmentReport:
    from propstore.source import promote_alignment

    updated = promote_alignment(repo, cluster_id)
    return ConceptAlignmentReport(alignment_id=updated.id)


def embed_concept_embeddings(
    repo: Repository,
    request: ConceptEmbedRequest,
    *,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> ConceptEmbedReport:
    if not request.concept_id and not request.embed_all:
        raise ConceptWorkflowError("provide a concept ID or request all concepts")

    from propstore.heuristic.embed import (
        _load_vec_extension,
        embed_concepts,
        get_registered_models,
    )

    sidecar = _require_sidecar(repo)
    reports: list[ConceptEmbedModelReport] = []
    conn = connect_sidecar(sidecar)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        _load_vec_extension(conn)
        ids = (
            [_resolve_sidecar_concept_id(conn, request.concept_id)]
            if request.concept_id
            else None
        )

        if request.model == "all":
            models = get_registered_models(conn)
            if not models:
                raise ConceptEmbeddingModelError(
                    "no models registered. Run embed with a specific model first."
                )
            for model_row in models:
                model_name = str(model_row["model_name"])
                result = embed_concepts(
                    conn,
                    model_name,
                    concept_ids=ids,
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
                reports.append(_concept_embed_model_report(model_name, result))
        else:
            result = embed_concepts(
                conn,
                request.model,
                concept_ids=ids,
                batch_size=request.batch_size,
                on_progress=(
                    None
                    if on_progress is None
                    else lambda done, total: on_progress(request.model, done, total)
                ),
            )
            reports.append(_concept_embed_model_report(request.model, result))
        conn.commit()
    return ConceptEmbedReport(results=tuple(reports))


def find_similar_concepts(
    repo: Repository,
    request: ConceptSimilarRequest,
) -> ConceptSimilarReport:
    from propstore.heuristic.embed import (
        _load_vec_extension,
        find_similar_concepts as find_similar_concepts_for_model,
        find_similar_concepts_agree,
        find_similar_concepts_disagree,
        get_registered_models,
    )

    sidecar = _require_sidecar(repo)
    conn = connect_sidecar(sidecar)
    conn.row_factory = sqlite3.Row
    _load_vec_extension(conn)

    try:
        resolved_id = _resolve_sidecar_concept_id(conn, request.concept_id)
        if request.agree:
            rows = find_similar_concepts_agree(conn, resolved_id, top_k=request.top_k)
        elif request.disagree:
            rows = find_similar_concepts_disagree(
                conn, resolved_id, top_k=request.top_k
            )
        else:
            model = request.model
            if model is None:
                models = get_registered_models(conn)
                if not models:
                    raise ConceptEmbeddingModelError(
                        "no embeddings found. Run 'pks concept embed' first."
                    )
                model = str(models[0]["model_name"])
            rows = find_similar_concepts_for_model(
                conn,
                resolved_id,
                model,
                top_k=request.top_k,
            )
    except ValueError as exc:
        raise ConceptWorkflowError(str(exc)) from exc
    finally:
        conn.close()

    return ConceptSimilarReport(
        hits=tuple(
            ConceptSimilarHit(
                distance=float(row.get("distance", 0)),
                concept_id=str(row.get("primary_logical_id") or row.get("id", "?")),
                canonical_name=str(row.get("canonical_name", "")),
                definition=str(row.get("definition") or ""),
            )
            for row in rows
        )
    )


def _resolve_sidecar_concept_id(conn: sqlite3.Connection, handle: str) -> str:
    conn.row_factory = sqlite3.Row
    direct = conn.execute("SELECT id FROM concept WHERE id = ?", (handle,)).fetchone()
    if direct is not None:
        return str(direct["id"])
    primary = conn.execute(
        "SELECT id FROM concept WHERE primary_logical_id = ?",
        (handle,),
    ).fetchone()
    if primary is not None:
        return str(primary["id"])
    canonical = conn.execute(
        "SELECT id FROM concept WHERE canonical_name = ?",
        (handle,),
    ).fetchone()
    if canonical is not None:
        return str(canonical["id"])
    alias = conn.execute(
        "SELECT concept_id FROM alias WHERE alias_name = ?",
        (handle,),
    ).fetchone()
    if alias is not None:
        return str(alias["concept_id"])
    raise UnknownConceptError(handle)


def _require_sidecar(repo: Repository) -> Path:
    sidecar = repo.sidecar_path
    if not sidecar.exists():
        raise ConceptSidecarMissingError("sidecar not found. Run 'pks build' first.")
    return sidecar


def _concept_embed_model_report(
    model_name: str,
    result: Mapping[str, object],
) -> ConceptEmbedModelReport:
    return ConceptEmbedModelReport(
        model_name=model_name,
        embedded=_required_int(result, "embedded"),
        skipped=_required_int(result, "skipped"),
        errors=_required_int(result, "errors"),
    )


def _required_int(result: Mapping[str, object], key: str) -> int:
    value = result[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConceptWorkflowError(f"expected integer field '{key}'")
    return value


def _require_snapshot(repo: Repository):
    try:
        repo.snapshot.head_sha()
    except ValueError as exc:
        raise ConceptMutationError(
            "concept mutations require a git-backed repository"
        ) from exc
    return repo.snapshot


def _rename_cel_identifier(expression: str, old_name: str, new_name: str) -> str:
    result: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(expression):
        ch = expression[i]
        if quote is not None:
            result.append(ch)
            if ch == quote and (i == 0 or expression[i - 1] != "\\"):
                quote = None
            i += 1
            continue

        if ch in ("'", '"'):
            quote = ch
            result.append(ch)
            i += 1
            continue

        if ch.isalpha() or ch == "_":
            j = i + 1
            while j < len(expression) and (
                expression[j].isalnum() or expression[j] == "_"
            ):
                j += 1
            token = expression[i:j]
            result.append(new_name if token == old_name else token)
            i = j
            continue

        result.append(ch)
        i += 1

    return "".join(result)


def _rewrite_condition_list(
    conditions: object,
    old_name: str,
    new_name: str,
) -> tuple[object, bool]:
    if not isinstance(conditions, list):
        return conditions, False
    changed = False
    rewritten: list[object] = []
    for condition in conditions:
        if isinstance(condition, str):
            new_condition = _rename_cel_identifier(condition, old_name, new_name)
            changed = changed or new_condition != condition
            rewritten.append(new_condition)
        else:
            rewritten.append(condition)
    return rewritten, changed


def _rewrite_concept_conditions(data: dict, old_name: str, new_name: str) -> bool:
    changed = False
    for rel in data.get("relationships", []) or []:
        rewritten, rel_changed = _rewrite_condition_list(
            rel.get("conditions"), old_name, new_name
        )
        if rel_changed:
            rel["conditions"] = rewritten
            changed = True
    for param in data.get("parameterization_relationships", []) or []:
        rewritten, param_changed = _rewrite_condition_list(
            param.get("conditions"), old_name, new_name
        )
        if param_changed:
            param["conditions"] = rewritten
            changed = True
    return changed


def _rewrite_claim_conditions(
    claim_file_data: dict, old_name: str, new_name: str
) -> bool:
    changed = False
    for claim in claim_file_data.get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        rewritten, claim_changed = _rewrite_condition_list(
            claim.get("conditions"), old_name, new_name
        )
        if claim_changed:
            claim["conditions"] = rewritten
            changed = True
    return changed


def _concept_ref(concept_entry: LoadedConcept) -> ConceptFileRef:
    return ConceptFileRef(concept_entry.filename)


def _claims_ref(claim_file: ClaimFileEntry) -> ClaimsFileRef:
    return ClaimsFileRef(claim_file_filename(claim_file))


def _normalize_concept_data(
    data: dict,
    *,
    canonical_name: str | None = None,
    domain: str | None = None,
    local_handle: str | None = None,
) -> dict:
    return normalize_canonical_concept_payload(
        deepcopy(data),
        canonical_name=canonical_name,
        domain=domain,
        local_handle=local_handle,
    )


def _concept_document(repo: Repository, ref: ConceptFileRef, data: dict) -> ConceptDocument:
    payload = _normalize_concept_data(data)
    return repo.families.concepts.coerce(
        payload,
        source=repo.families.concepts.address(ref).require_path(),
    )


def _canonical_concept_document(
    repo: Repository, ref: ConceptFileRef, data: dict
) -> ConceptDocument:
    document = _concept_document(repo, ref, data)
    return _concept_document(repo, ref, concept_document_to_payload(document))


def _claims_document(
    repo: Repository, ref: ClaimsFileRef, data: dict
) -> ClaimsFileDocument:
    return repo.families.claims.coerce(
        data,
        source=repo.families.claims.address(ref).require_path(),
    )


def _concept_artifact_payload(concept_entry: LoadedConcept) -> dict:
    if concept_entry.document is not None:
        return concept_document_to_payload(concept_entry.document)
    return _normalize_concept_data(concept_entry.record.to_payload())


def _concept_display_handle(data: dict) -> str:
    lexical_entry = data.get("lexical_entry")
    lexical_name = None
    if isinstance(lexical_entry, dict):
        canonical_form = lexical_entry.get("canonical_form")
        if isinstance(canonical_form, dict):
            lexical_name = canonical_form.get("written_rep")
    return (
        primary_logical_id(data)
        or data.get("canonical_name")
        or lexical_name
        or data.get("artifact_id")
        or "?"
    )


def _find_concept_entry(repo: Repository, id_or_name: str) -> LoadedConcept | None:
    tree = repo.tree()
    for handle in repo.families.concepts.iter_handles():
        concept = LoadedConcept(
            filename=handle.ref.name,
            source_path=tree / handle.address.require_path(),
            knowledge_root=tree,
            record=parse_concept_record_document(handle.document),
            document=handle.document,
        )
        if handle.ref.name == id_or_name:
            return concept
        data = concept.record.to_payload()
        if data.get("canonical_name") == id_or_name:
            return concept
        if data.get("artifact_id") == id_or_name:
            return concept
        logical_ids = data.get("logical_ids")
        if isinstance(logical_ids, list):
            for entry in logical_ids:
                if isinstance(entry, dict) and format_logical_id(entry) == id_or_name:
                    return concept
        aliases = data.get("aliases")
        if isinstance(aliases, list):
            for alias in aliases:
                if isinstance(alias, dict) and alias.get("name") == id_or_name:
                    return concept
    return None


def _require_concept_entry(
    repo: Repository, handle: str, *, label: str = "Concept"
) -> LoadedConcept:
    concept_entry = _find_concept_entry(repo, handle)
    if concept_entry is None:
        raise ConceptMutationError(f"{label} '{handle}' not found")
    return concept_entry


def _require_concept_artifact_id(repo: Repository, handle: str, *, label: str) -> str:
    concept_entry = _require_concept_entry(repo, handle, label=label)
    artifact_id = concept_entry.record.to_payload().get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ConceptMutationError(f"{label} '{handle}' does not have an artifact_id")
    return artifact_id


def _require_concept_reference(
    repo: Repository, handle: str, *, label: str
) -> dict[str, str]:
    concept_entry = _require_concept_entry(repo, handle, label=label)
    data = concept_entry.record.to_payload()
    artifact_id = data.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ConceptMutationError(f"{label} '{handle}' does not have an artifact_id")
    reference: dict[str, str] = {"uri": artifact_id}
    canonical_name = data.get("canonical_name")
    if isinstance(canonical_name, str) and canonical_name:
        reference["label"] = canonical_name
    return reference


def _provenance_payload(
    *,
    asserter: str,
    timestamp: str,
    source_artifact_code: str,
    method: str,
) -> dict[str, object]:
    return {
        "status": "stated",
        "witnesses": [
            {
                "asserter": asserter,
                "timestamp": timestamp,
                "source_artifact_code": source_artifact_code,
                "method": method,
            }
        ],
    }


def _first_lexical_sense(data: dict) -> dict:
    lexical_entry = data.get("lexical_entry")
    if not isinstance(lexical_entry, dict):
        raise ConceptMutationError("concept is missing lexical_entry")
    senses = lexical_entry.get("senses")
    if not isinstance(senses, list) or not senses or not isinstance(senses[0], dict):
        raise ConceptMutationError("concept lexical_entry requires at least one sense")
    return senses[0]


def _form_registry(repo: Repository) -> dict[str, FormDefinition]:
    return {
        document.name: parse_form(document.name, document)
        for handle in repo.families.forms.iter_handles()
        for document in (handle.document,)
    }


def _loaded_concepts(repo: Repository) -> list[LoadedConcept]:
    tree = repo.tree()
    concepts: list[LoadedConcept] = []
    for handle in repo.families.concepts.iter_handles():
        concepts.append(
            LoadedConcept(
                filename=handle.ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_concept_record_document(handle.document),
                document=handle.document,
            )
        )
    return concepts


def _raise_validation_failure(
    result,
    *,
    message: str = "Validation failed. No changes written.",
) -> None:
    if not result.ok:
        raise ConceptValidationError(
            message,
            errors=tuple(_render_diagnostic(error) for error in result.errors),
            warnings=tuple(_render_diagnostic(warning) for warning in result.warnings),
        )


def _render_diagnostic(diagnostic: object) -> str:
    render = getattr(diagnostic, "render", None)
    if callable(render):
        return str(render())
    return str(diagnostic)


def _run_concept_validation(
    repo: Repository,
    concepts: list[LoadedConcept],
) -> PipelineResult[object]:
    claim_files = [
        handle
        for handle in repo.families.claims.iter_handles()
    ]
    return run_concept_pipeline(
        concepts,
        context=ConceptPipelineContext(
            form_registry=_form_registry(repo),
            claim_reference_lookup=build_claim_reference_lookup(claim_files),
        ),
    )


def _validate_updated_concept(
    repo: Repository,
    concept_entry: LoadedConcept,
    document: ConceptDocument,
) -> tuple[str, ...]:
    ref = _concept_ref(concept_entry)
    concepts = []
    tree = repo.tree()
    for handle in repo.families.concepts.iter_handles():
        loaded_ref = handle.ref
        if loaded_ref == ref:
            concepts.append(
                LoadedConcept(
                    filename=loaded_ref.name,
                    source_path=tree / repo.families.concepts.address(ref).require_path(),
                    knowledge_root=tree,
                    record=parse_concept_record_document(document),
                    document=document,
                )
            )
            continue
        concepts.append(
            LoadedConcept(
                filename=loaded_ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_concept_record_document(handle.document),
                document=handle.document,
            )
        )

    validation = _run_concept_validation(repo, concepts)
    _raise_validation_failure(validation)
    return tuple(_render_diagnostic(warning) for warning in validation.warnings)


def _apply_proto_role_entailment(
    bundle: dict[str, object],
    *,
    role_kind: str,
    entailment: dict[str, object],
) -> None:
    key = (
        "proto_agent_entailments"
        if role_kind == "agent"
        else "proto_patient_entailments"
    )
    entailments = bundle.get(key)
    if not isinstance(entailments, list):
        entailments = []
    entailments.append(entailment)
    bundle[key] = entailments


def add_concept(repo: Repository, request: ConceptAddRequest) -> ConceptMutationReport:
    snapshot = _require_snapshot(repo)
    ref = ConceptFileRef(request.name)
    filepath = repo.root / Path(repo.families.concepts.address(ref).require_path())
    semantic_path = repo.tree() / repo.families.concepts.address(ref).require_path()
    if semantic_path.exists():
        raise ConceptMutationError(f"Concept file '{filepath}' already exists")

    data: dict[str, object] = {
        "canonical_name": request.name,
        "status": "proposed",
        "definition": request.definition,
        "domain": request.domain,
        "created_date": str(date.today()),
        "form": request.form_name,
    }

    if request.form_name == "category":
        if not request.values:
            raise ConceptMutationError("values are required when form is category")
        value_list = [value.strip() for value in request.values if value.strip()]
        if not value_list:
            raise ConceptMutationError("values must contain at least one value")
        form_parameters: dict[str, object] = {"values": value_list}
        if request.closed:
            form_parameters["extensible"] = False
        data["form_parameters"] = form_parameters
    elif request.values:
        raise ConceptMutationError("values are only valid when form is category")
    elif request.closed:
        raise ConceptMutationError("closed categories require form category")

    for _attempt in range(64):
        candidate = candidate_concept_id_for_repo(repo)
        document_data = _normalize_concept_data(
            dict(data),
            local_handle=f"concept{candidate.numeric_id}",
        )
        document = _concept_document(repo, ref, document_data)

        if request.dry_run:
            return ConceptMutationReport(
                lines=(f"Would create {filepath}", repo.families.concepts.render(document))
            )

        concepts = _loaded_concepts(repo)
        concepts.append(
            LoadedConcept(
                filename=request.name,
                source_path=semantic_path,
                knowledge_root=repo.tree(),
                record=parse_concept_record_document(document),
                document=document,
            )
        )

        result = _run_concept_validation(repo, concepts)
        _raise_validation_failure(result)
        warnings = tuple(_render_diagnostic(warning) for warning in result.warnings)

        if not reserve_concept_id_candidate(repo, candidate):
            continue

        repo.families.concepts.save(
            ref,
            document,
            message=(
                f"Add concept: {request.name} "
                f"({_concept_display_handle(concept_document_to_record_payload(document))})"
            ),
        )
        return ConceptMutationReport(
            lines=(
                "Created "
                f"{filepath} with logical ID "
                f"{_concept_display_handle(concept_document_to_record_payload(document))}",
            ),
            warnings=warnings,
        )

    raise ConceptMutationError("could not reserve concept ID after concurrent updates")


def add_concept_alias(
    repo: Repository, request: ConceptAliasRequest
) -> ConceptMutationReport:
    assert_alias_does_not_target_reserved_namespace(request.name)
    snapshot = _require_snapshot(repo)
    concept_entry = _require_concept_entry(repo, request.concept_id)
    ref = _concept_ref(concept_entry)
    filepath = repo.root / Path(repo.families.concepts.address(ref).require_path())
    data = deepcopy(concept_entry.record.to_payload())

    warnings: list[str] = []
    tree = repo.tree()
    for handle in repo.families.concepts.iter_handles():
        other_ref = handle.ref
        if other_ref == ref:
            continue
        other_document = handle.document
        other_entry = LoadedConcept(
            filename=other_ref.name,
            source_path=tree / handle.address.require_path(),
            knowledge_root=tree,
            record=parse_concept_record_document(other_document),
            document=other_document,
        )
        if other_entry.record.to_payload().get("canonical_name") == request.name:
            warnings.append(
                f"alias '{request.name}' matches canonical_name of "
                f"concept '{other_entry.record.artifact_id}'"
            )

    new_alias: dict[str, str] = {"name": request.name, "source": request.source}
    if request.note:
        new_alias["note"] = request.note

    if request.dry_run:
        return ConceptMutationReport(
            lines=(f"Would add alias to {filepath}: {new_alias}",),
            warnings=tuple(warnings),
        )

    aliases = data.get("aliases") or []
    aliases.append(new_alias)
    data["aliases"] = aliases
    data["last_modified"] = str(date.today())
    data = _normalize_concept_data(data)
    document = _concept_document(repo, ref, data)
    repo.families.concepts.save(
        ref,
        document,
        message=f"Add alias '{request.name}' to {_concept_display_handle(data)}",
    )

    return ConceptMutationReport(
        lines=(
            f"Added alias '{request.name}' to "
            f"{_concept_display_handle(data)} ({filepath.stem})",
        ),
        warnings=tuple(warnings),
    )


def rename_concept(
    repo: Repository, request: ConceptRenameRequest
) -> ConceptMutationReport:
    snapshot = _require_snapshot(repo)
    concept_entry = _require_concept_entry(repo, request.concept_id)
    old_ref = _concept_ref(concept_entry)
    new_ref = ConceptFileRef(request.name)

    filepath = repo.root / Path(repo.families.concepts.address(old_ref).require_path())
    data = deepcopy(concept_entry.record.to_payload())
    old_name = data.get("canonical_name", filepath.stem)
    new_path = repo.root / Path(repo.families.concepts.address(new_ref).require_path())
    new_semantic_path = (
        repo.tree() / repo.families.concepts.address(new_ref).require_path()
    )
    if old_name == request.name:
        return ConceptMutationReport(
            lines=(f"No change: concept already named '{request.name}'",)
        )
    if new_semantic_path.exists():
        raise ConceptMutationError(f"Concept file '{new_path}' already exists")

    if request.dry_run:
        return ConceptMutationReport(
            lines=(
                f"Would rename: {old_name} -> {request.name}",
                f"  {filepath} -> {new_path}",
            )
        )

    loaded_concepts = _loaded_concepts(repo)
    updated_concepts: list[tuple[ConceptFileRef, ConceptFileRef, LoadedConcept]] = []
    changed_concept_refs: set[ConceptFileRef] = set()
    for concept_record in loaded_concepts:
        concept_ref = _concept_ref(concept_record)
        concept_data = deepcopy(concept_record.record.to_payload())
        updated_ref = concept_ref
        if concept_ref == old_ref:
            concept_data["canonical_name"] = request.name
            concept_data["last_modified"] = str(date.today())
            updated_ref = new_ref
            changed_concept_refs.add(concept_ref)
        if _rewrite_concept_conditions(concept_data, str(old_name), request.name):
            changed_concept_refs.add(concept_ref)
        concept_data = _normalize_concept_data(concept_data)
        concept_document = _concept_document(repo, updated_ref, concept_data)
        updated_concepts.append(
            (
                concept_ref,
                updated_ref,
                LoadedConcept(
                    filename=(
                        request.name
                        if updated_ref == new_ref
                        else concept_record.filename
                    ),
                    source_path=repo.tree()
                    / repo.families.concepts.address(updated_ref).require_path(),
                    knowledge_root=concept_record.knowledge_root,
                    record=parse_concept_record_document(concept_document),
                    document=concept_document,
                ),
            )
        )

    claim_files = [
        handle
        for handle in repo.families.claims.iter_handles()
    ]
    concept_validation = _run_concept_validation(
        repo,
        [entry for _, _, entry in updated_concepts],
    )
    _raise_validation_failure(
        concept_validation,
        message="Rename validation failed. No changes written.",
    )
    warnings = [
        _render_diagnostic(warning)
        for warning in concept_validation.warnings
    ]

    updated_claim_files: list[tuple[ClaimsFileRef, ClaimFileEntry]] = []
    changed_claim_refs: set[ClaimsFileRef] = set()
    if claim_files:
        for claim_file in claim_files:
            claim_ref = _claims_ref(claim_file)
            claim_data = deepcopy(claim_file_payload(claim_file))
            if _rewrite_claim_conditions(claim_data, str(old_name), request.name):
                changed_claim_refs.add(claim_ref)
                claim_data, _ = normalize_claim_file_payload(claim_data)
            updated_claim_files.append(
                (
                    claim_ref,
                    loaded_claim_file_from_payload(
                        filename=claim_file_filename(claim_file),
                        source_path=repo.tree()
                        / repo.families.claims.address(claim_ref).require_path(),
                        knowledge_root=repo.tree(),
                        data=claim_data,
                    ),
                )
            )
        compilation_context = build_compilation_context_from_loaded(
            [entry for _, _, entry in updated_concepts],
            form_registry=_form_registry(repo),
            claim_files=[entry for _, entry in updated_claim_files],
        )
        claim_validation = validate_claims(
            [entry for _, entry in updated_claim_files],
            compilation_context,
        )
        _raise_validation_failure(
            claim_validation,
            message="Rename validation failed. No changes written.",
        )
        warnings.extend(str(warning) for warning in claim_validation.warnings)

    with repo.families.transact(
        message=f"Rename concept: {old_name} -> {request.name}"
    ) as transaction:
        for original_ref, updated_ref, updated_concept in updated_concepts:
            if original_ref == old_ref:
                transaction.concepts.move(
                    old_ref,
                    new_ref,
                    _concept_document(
                        repo,
                        updated_ref,
                        updated_concept.record.to_payload(),
                    ),
                )
                continue
            if original_ref in changed_concept_refs:
                transaction.concepts.save(
                    updated_ref,
                    _concept_document(
                        repo,
                        updated_ref,
                        updated_concept.record.to_payload(),
                    ),
                )

        for claim_ref, updated_claim_file in updated_claim_files:
            if claim_ref not in changed_claim_refs:
                continue
            transaction.claims.save(
                claim_ref,
                _claims_document(
                    repo,
                    claim_ref,
                    claim_file_payload(updated_claim_file),
                ),
            )

    renamed_entry = next(
        (entry for _, updated_ref, entry in updated_concepts if updated_ref == new_ref),
        None,
    )
    logical_id = (
        _concept_display_handle(renamed_entry.record.to_payload())
        if renamed_entry is not None
        else request.name
    )
    return ConceptMutationReport(
        lines=(
            f"{old_name} -> {request.name}",
            f"  {filepath} -> {new_path}",
            f"  Logical ID: {logical_id}",
        ),
        warnings=tuple(warnings),
    )


def deprecate_concept(
    repo: Repository, request: ConceptDeprecateRequest
) -> ConceptMutationReport:
    snapshot = _require_snapshot(repo)
    concept_entry = _require_concept_entry(repo, request.concept_id)
    ref = _concept_ref(concept_entry)
    filepath = repo.root / Path(repo.families.concepts.address(ref).require_path())

    replacement_entry = _require_concept_entry(
        repo, request.replaced_by, label="Replacement concept"
    )
    replacement_data = replacement_entry.record.to_payload()
    if replacement_data.get("status") == "deprecated":
        raise ConceptMutationError(
            f"Replacement concept '{request.replaced_by}' is itself deprecated"
        )

    data = deepcopy(concept_entry.record.to_payload())
    if request.dry_run:
        return ConceptMutationReport(
            lines=(
                f"Would deprecate {_concept_display_handle(data)} ({filepath.stem})",
                f"  replaced_by: {_concept_display_handle(replacement_data)}",
            )
        )

    data["status"] = "deprecated"
    replacement_artifact_id = replacement_data.get("artifact_id")
    if not isinstance(replacement_artifact_id, str) or not replacement_artifact_id:
        raise ConceptMutationError(
            f"Replacement concept '{request.replaced_by}' does not have an artifact_id"
        )
    data["replaced_by"] = replacement_artifact_id
    data["last_modified"] = str(date.today())
    data = _normalize_concept_data(data)
    repo.families.concepts.save(
        ref,
        _concept_document(repo, ref, data),
        message=(
            f"Deprecate {_concept_display_handle(data)}, replaced by "
            f"{_concept_display_handle(replacement_data)}"
        ),
    )
    return ConceptMutationReport(
        lines=(
            f"Deprecated {_concept_display_handle(data)} ({filepath.stem}), "
            f"replaced by {_concept_display_handle(replacement_data)}",
        )
    )


def link_concepts(repo: Repository, request: ConceptLinkRequest) -> ConceptMutationReport:
    if request.rel_type not in RELATIONSHIP_TYPES:
        raise ConceptMutationError(f"invalid relationship type: {request.rel_type}")
    snapshot = _require_snapshot(repo)
    concept_entry = _require_concept_entry(repo, request.source_id, label="Source concept")
    ref = _concept_ref(concept_entry)
    filepath = repo.root / Path(repo.families.concepts.address(ref).require_path())

    target_entry = _require_concept_entry(repo, request.target_id, label="Target concept")
    target_data = target_entry.record.to_payload()
    target_artifact_id = target_data.get("artifact_id")
    if not isinstance(target_artifact_id, str) or not target_artifact_id:
        raise ConceptMutationError(
            f"Target concept '{request.target_id}' does not have an artifact_id"
        )

    data = deepcopy(concept_entry.record.to_payload())
    relationship: dict[str, object] = {
        "type": request.rel_type,
        "target": target_artifact_id,
    }
    if request.paper_source:
        relationship["source"] = request.paper_source
    if request.note:
        relationship["note"] = request.note
    if request.conditions:
        relationship["conditions"] = [
            condition.strip() for condition in request.conditions.split(",")
        ]

    if request.dry_run:
        return ConceptMutationReport(
            lines=(
                f"Would add relationship to {filepath.stem}: {relationship}",
            )
        )

    relationships = data.get("relationships") or []
    relationships.append(relationship)
    data["relationships"] = relationships
    data["last_modified"] = str(date.today())
    data = _normalize_concept_data(data)
    updated_document = _concept_document(repo, ref, data)

    updated_concepts = []
    for concept_record in _loaded_concepts(repo):
        concept_ref = _concept_ref(concept_record)
        concept_path = repo.root / Path(
            repo.families.concepts.address(concept_ref).require_path()
        )
        updated_concepts.append(
            LoadedConcept(
                filename=concept_record.filename,
                source_path=repo.tree()
                / repo.families.concepts.address(concept_ref).require_path(),
                knowledge_root=concept_record.knowledge_root,
                record=parse_concept_record(
                    concept_document_to_record_payload(updated_document)
                    if concept_path == filepath
                    else concept_record.record.to_payload(),
                ),
                document=(
                    updated_document
                    if concept_path == filepath
                    else concept_record.document
                ),
            )
        )

    validation = _run_concept_validation(repo, updated_concepts)
    _raise_validation_failure(validation)
    warnings = tuple(_render_diagnostic(warning) for warning in validation.warnings)

    repo.families.concepts.save(
        ref,
        updated_document,
        message=(
            f"Link {_concept_display_handle(data)} {request.rel_type} "
            f"{_concept_display_handle(target_data)}"
        ),
    )
    return ConceptMutationReport(
        lines=(
            f"Added {request.rel_type} -> {_concept_display_handle(target_data)} "
            f"on {_concept_display_handle(data)} ({filepath.stem})",
        ),
        warnings=warnings,
    )


def add_concept_qualia(
    repo: Repository, request: ConceptQualiaAddRequest
) -> ConceptMutationReport:
    if request.role not in QUALIA_ROLES:
        raise ConceptMutationError(f"invalid qualia role: {request.role}")
    snapshot = _require_snapshot(repo)
    concept_entry = _require_concept_entry(repo, request.concept_id)
    ref = _concept_ref(concept_entry)
    data = _concept_artifact_payload(concept_entry)
    sense = _first_lexical_sense(data)

    qualia = sense.get("qualia")
    if not isinstance(qualia, dict):
        qualia = {}
    role_entries = qualia.get(request.role)
    if not isinstance(role_entries, list):
        role_entries = []
    entry: dict[str, object] = {
        "reference": _require_concept_reference(
            repo, request.target_concept, label="Target concept"
        ),
        "provenance": _provenance_payload(
            asserter=request.asserter,
            timestamp=request.timestamp,
            source_artifact_code=request.source_artifact_code,
            method=request.method,
        ),
    }
    if request.type_constraint is not None:
        entry["type_constraint"] = {
            "reference": _require_concept_reference(
                repo,
                request.type_constraint,
                label="Type constraint",
            )
        }
    role_entries.append(entry)
    qualia[request.role] = role_entries
    sense["qualia"] = qualia
    data["last_modified"] = str(date.today())
    document = _canonical_concept_document(repo, ref, data)
    data = concept_document_to_record_payload(document)

    if request.dry_run:
        return ConceptMutationReport(lines=(repo.families.concepts.render(document),))

    warnings = _validate_updated_concept(repo, concept_entry, document)
    repo.families.concepts.save(
        ref,
        document,
        message=f"Add {request.role} qualia to {_concept_display_handle(data)}",
    )
    return ConceptMutationReport(
        lines=(f"Added {request.role} qualia to {_concept_display_handle(data)}",),
        warnings=warnings,
    )


def set_concept_description_kind(
    repo: Repository, request: ConceptDescriptionKindRequest
) -> ConceptMutationReport:
    snapshot = _require_snapshot(repo)
    concept_entry = _require_concept_entry(repo, request.concept_id)
    ref = _concept_ref(concept_entry)
    data = _concept_artifact_payload(concept_entry)
    sense = _first_lexical_sense(data)

    slot_payloads: list[dict[str, object]] = []
    for raw_slot in request.slots:
        slot_name, separator, type_handle = raw_slot.partition("=")
        if not separator or not slot_name or not type_handle:
            raise ConceptMutationError("slot must use name=type-concept")
        slot_payloads.append(
            {
                "name": slot_name,
                "type_constraint": _require_concept_reference(
                    repo,
                    type_handle,
                    label=f"Slot '{slot_name}' type constraint",
                ),
            }
        )

    sense["description_kind"] = {
        "name": request.name,
        "reference": _require_concept_reference(
            repo, request.reference_handle, label="Description-kind reference"
        ),
        "slots": slot_payloads,
    }
    data["last_modified"] = str(date.today())
    document = _canonical_concept_document(repo, ref, data)
    data = concept_document_to_record_payload(document)

    if request.dry_run:
        return ConceptMutationReport(lines=(repo.families.concepts.render(document),))

    warnings = _validate_updated_concept(repo, concept_entry, document)
    repo.families.concepts.save(
        ref,
        document,
        message=f"Set description kind on {_concept_display_handle(data)}",
    )
    return ConceptMutationReport(
        lines=(f"Set description kind on {_concept_display_handle(data)}",),
        warnings=warnings,
    )


def add_concept_proto_role(
    repo: Repository, request: ConceptProtoRoleRequest
) -> ConceptMutationReport:
    if request.role_kind not in PROTO_ROLE_KINDS:
        raise ConceptMutationError(f"invalid proto-role kind: {request.role_kind}")
    snapshot = _require_snapshot(repo)
    concept_entry = _require_concept_entry(repo, request.concept_id)
    ref = _concept_ref(concept_entry)
    data = _concept_artifact_payload(concept_entry)
    sense = _first_lexical_sense(data)

    entailment = {
        "property": request.property_name,
        "value": request.value,
        "provenance": _provenance_payload(
            asserter=request.asserter,
            timestamp=request.timestamp,
            source_artifact_code=request.source_artifact_code,
            method=request.method,
        ),
    }
    role_bundles = sense.get("role_bundles")
    if not isinstance(role_bundles, dict):
        role_bundles = {}
    bundle = role_bundles.get(request.role_name)
    if not isinstance(bundle, dict):
        bundle = {}
    _apply_proto_role_entailment(
        bundle,
        role_kind=request.role_kind,
        entailment=entailment,
    )
    role_bundles[request.role_name] = bundle
    sense["role_bundles"] = role_bundles

    description_kind = sense.get("description_kind")
    if isinstance(description_kind, dict):
        slots = description_kind.get("slots")
        if isinstance(slots, list):
            for slot in slots:
                if not isinstance(slot, dict) or slot.get("name") != request.role_name:
                    continue
                slot_bundle = slot.get("proto_role_bundle")
                if not isinstance(slot_bundle, dict):
                    slot_bundle = {}
                _apply_proto_role_entailment(
                    slot_bundle,
                    role_kind=request.role_kind,
                    entailment=deepcopy(entailment),
                )
                slot["proto_role_bundle"] = slot_bundle
                break

    data["last_modified"] = str(date.today())
    document = _canonical_concept_document(repo, ref, data)
    data = concept_document_to_record_payload(document)

    if request.dry_run:
        return ConceptMutationReport(lines=(repo.families.concepts.render(document),))

    warnings = _validate_updated_concept(repo, concept_entry, document)
    repo.families.concepts.save(
        ref,
        document,
        message=(
            f"Add {request.role_kind} proto-role {request.property_name} "
            f"to {_concept_display_handle(data)}"
        ),
    )
    return ConceptMutationReport(
        lines=(
            f"Added {request.role_kind} proto-role {request.property_name} "
            f"to {_concept_display_handle(data)}",
        ),
        warnings=warnings,
    )


def add_concept_value(
    repo: Repository, request: ConceptAddValueRequest
) -> ConceptMutationReport:
    snapshot = _require_snapshot(repo)
    concept_entry = _require_concept_entry(repo, request.concept_name)
    ref = _concept_ref(concept_entry)

    data = deepcopy(concept_entry.record.to_payload())
    if data.get("form") != "category":
        raise ConceptMutationError(
            f"'{request.concept_name}' is not a category concept "
            f"(form={data.get('form')})"
        )

    raw_form_parameters = data.get("form_parameters")
    if raw_form_parameters is None:
        form_parameters: dict[str, object] = {}
    elif isinstance(raw_form_parameters, dict):
        form_parameters = raw_form_parameters
    else:
        raise ConceptMutationError(
            f"'{request.concept_name}' form_parameters must be a mapping"
        )
    extensible = form_parameters.get("extensible", True)
    if not extensible:
        raise ConceptMutationError(
            f"'{request.concept_name}' is not extensible - cannot add values"
        )

    raw_values = form_parameters.get("values", [])
    if not isinstance(raw_values, list):
        raise ConceptMutationError(
            f"'{request.concept_name}' form_parameters.values must be a list"
        )
    values = raw_values
    if request.value in values:
        raise ConceptMutationError(
            f"Value '{request.value}' already exists in '{request.concept_name}'"
        )

    if request.dry_run:
        return ConceptMutationReport(
            lines=(
                f"Would add '{request.value}' to "
                f"{request.concept_name} values: {values + [request.value]}",
            )
        )

    values.append(request.value)
    form_parameters["values"] = values
    data["form_parameters"] = form_parameters
    data["last_modified"] = str(date.today())
    data = _normalize_concept_data(data)
    repo.families.concepts.save(
        ref,
        _concept_document(repo, ref, data),
        message=f"Add value '{request.value}' to {request.concept_name}",
    )
    return ConceptMutationReport(
        lines=(
            f"Added '{request.value}' to "
            f"{request.concept_name} - values: {', '.join(str(value) for value in values)}",
        )
    )
