"""Typed concept query and embedding workflows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING

from msgspec.structs import replace as replace_document
from quire.documents import LoadedDocument

if TYPE_CHECKING:
    from propstore.repository import Repository

from propstore.reporting import JsonReportMixin
from propstore.claims import (
    LoadedClaimsFile,
    claim_file_filename,
)
from propstore.canonical_namespaces import (
    assert_alias_does_not_target_reserved_namespace,
)
from propstore.compiler.context import (
    build_compiler_claim_index,
)
from propstore.families.identity.concepts import derive_concept_artifact_id
from propstore.families.concepts.types import VALID_CONCEPT_RELATIONSHIP_TYPES
from propstore.families.concepts.passes import (
    ConceptPipelineContext,
    run_concept_pipeline,
)
from propstore.families.concepts.stages import (
    normalize_loaded_concepts,
)
from propstore.families.claims.declaration import ClaimDocument
from propstore.families.concepts.declaration import (
    ConceptAliasDocument,
    ConceptDocument,
    ConceptFormParametersDocument,
    ConceptLogicalIdDocument,
    ConceptRelationshipDocument,
    LexicalEntryDocument,
    LexicalFormDocument,
    LexicalSenseDocument,
    OntologyReferenceDocument,
    ParameterizationRelationshipDocument,
)
from propstore.core.lemon.description_kinds import DescriptionKind, ParticipantSlot
from propstore.core.lemon.proto_roles import GradedEntailment, ProtoRoleBundle
from propstore.core.lemon.qualia import (
    QualiaReference,
    QualiaRole,
    QualiaStructure,
    TypeConstraint,
)
from propstore.core.lemon.references import OntologyReference
from propstore.families.registry import ClaimRef, ConceptFileRef
from propstore.families.forms.stages import FormDefinition, parse_form
from propstore.families.concepts.types import ConceptRelationshipType, ConceptStatus
from propstore.semantic_passes.types import PipelineResult
from propstore.app.repository_views import AppRepositoryViewRequest
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness

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
    repository_view: AppRepositoryViewRequest = field(
        default_factory=AppRepositoryViewRequest
    )


@dataclass(frozen=True)
class ConceptSearchHit:
    handle: str
    logical_id: str | None
    canonical_name: str
    definition: str
    status: str | None = None


@dataclass(frozen=True)
class ConceptSearchReport(JsonReportMixin):
    hits: tuple[ConceptSearchHit, ...]


@dataclass(frozen=True)
class ConceptListRequest:
    domain: str | None = None
    status: str | None = None
    limit: int = 200
    repository_view: AppRepositoryViewRequest = field(
        default_factory=AppRepositoryViewRequest
    )


@dataclass(frozen=True)
class ConceptListEntry:
    handle: str
    canonical_name: str
    status: str


@dataclass(frozen=True)
class ConceptListReport(JsonReportMixin):
    concepts_found: bool
    entries: tuple[ConceptListEntry, ...]


@dataclass(frozen=True)
class ConceptCategoryEntry:
    canonical_name: str
    values: tuple[str, ...]
    extensible: bool


@dataclass(frozen=True)
class ConceptCategoriesReport(JsonReportMixin):
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
class ConceptShowReport(JsonReportMixin):
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


def _serialized_concept_mutation(function):
    @wraps(function)
    def wrapper(repo: Repository, request, *args, **kwargs):
        if getattr(request, "dry_run", False):
            return function(repo, request, *args, **kwargs)
        with repo.mutation_guard():
            return function(repo, request, *args, **kwargs)

    return wrapper


def list_concepts(
    repo: Repository,
    request: ConceptListRequest,
) -> ConceptListReport:
    loaded_concepts = _loaded_concepts(repo)
    if not loaded_concepts:
        return ConceptListReport(concepts_found=False, entries=())

    entries: list[ConceptListEntry] = []
    for concept_entry in loaded_concepts:
        document = concept_entry.document
        concept_domain = document.domain or ""
        concept_status = document.status.value
        if request.domain and concept_domain != request.domain:
            continue
        if request.status and concept_status != request.status:
            continue
        entries.append(
            ConceptListEntry(
                handle=document.lexical_entry.canonical_form.written_rep,
                canonical_name=document.lexical_entry.canonical_form.written_rep,
                status=concept_status,
            )
        )
    return ConceptListReport(concepts_found=True, entries=tuple(entries))


def list_concept_categories(repo: Repository) -> ConceptCategoriesReport:
    entries: list[ConceptCategoryEntry] = []
    for concept_entry in _loaded_concepts(repo):
        document = concept_entry.document
        if document.lexical_entry.physical_dimension_form != "category":
            continue
        form_parameters = document.form_parameters
        values = (
            ()
            if form_parameters is None or form_parameters.values is None
            else form_parameters.values
        )
        extensible = (
            True
            if form_parameters is None or form_parameters.extensible is None
            else form_parameters.extensible
        )
        entries.append(
            ConceptCategoryEntry(
                canonical_name=document.lexical_entry.canonical_form.written_rep,
                values=values,
                extensible=extensible,
            )
        )
    return ConceptCategoriesReport(entries=tuple(entries))


def show_concept(
    repo: Repository,
    request: ConceptShowRequest,
) -> ConceptShowReport:
    from propstore.families.concepts.alignment import load_alignment_artifact

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
    return ConceptShowReport(
        rendered=repo.families.concepts.render(concept_entry.document)
    )


def build_concept_alignment(
    repo: Repository,
    request: ConceptAlignmentBuildRequest,
) -> ConceptAlignmentReport:
    from propstore.families.concepts.alignment import align_sources

    artifact = align_sources(repo, list(request.sources))
    return ConceptAlignmentReport(alignment_id=artifact.id)


def query_concept_alignment(
    repo: Repository,
    request: ConceptAlignmentQueryRequest,
) -> ConceptAlignmentQueryReport:
    from propstore.families.concepts.alignment import load_alignment_artifact

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
    from propstore.families.concepts.alignment import decide_alignment

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
    from propstore.families.concepts.alignment import promote_alignment

    updated = promote_alignment(repo, cluster_id)
    return ConceptAlignmentReport(alignment_id=updated.id)


def _require_sidecar(repo: Repository) -> Path:
    from propstore.compiler.workflows import build_repository_world_store

    handle, _rebuilt = build_repository_world_store(repo)
    if not handle.path.exists():
        raise ConceptSidecarMissingError("sidecar not found. Run 'pks build' first.")
    return handle.path


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
        repo.require_git().head_sha()
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
) -> tuple[Sequence[object], bool]:
    if not isinstance(conditions, Sequence) or isinstance(conditions, str):
        return (), False
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


def _rewrite_concept_conditions(
    document: ConceptDocument, old_name: str, new_name: str
) -> tuple[ConceptDocument, bool]:
    changed = False
    relationships: list[ConceptRelationshipDocument] = []
    for rel in document.relationships:
        rewritten, rel_changed = _rewrite_condition_list(
            rel.conditions, old_name, new_name
        )
        relationships.append(
            replace_document(rel, conditions=tuple(rewritten)) if rel_changed else rel
        )
        changed = changed or rel_changed
    parameterizations: list[ParameterizationRelationshipDocument] = []
    for param in document.parameterization_relationships:
        rewritten, param_changed = _rewrite_condition_list(
            param.conditions, old_name, new_name
        )
        parameterizations.append(
            replace_document(param, conditions=tuple(rewritten))
            if param_changed
            else param
        )
        changed = changed or param_changed
    if not changed:
        return document, False
    return (
        replace_document(
            document,
            relationships=tuple(relationships),
            parameterization_relationships=tuple(parameterizations),
        ),
        True,
    )


def _rewrite_claim_conditions(
    claim_file_data: dict, old_name: str, new_name: str
) -> bool:
    changed = False
    if "claims" not in claim_file_data:
        rewritten, claim_changed = _rewrite_condition_list(
            claim_file_data.get("conditions"), old_name, new_name
        )
        if claim_changed:
            claim_file_data["conditions"] = rewritten
        return claim_changed
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


def _concept_ref(concept_entry: LoadedDocument[ConceptDocument]) -> ConceptFileRef:
    return ConceptFileRef(concept_entry.filename)


def _claims_ref(claim_file: LoadedClaimsFile) -> ClaimRef:
    artifact_id = claim_file.document.artifact_id
    if not isinstance(artifact_id, str) or not artifact_id:
        artifact_id = claim_file_filename(claim_file)
    return ClaimRef(artifact_id)


def _claims_document(repo: Repository, ref: ClaimRef, data: dict) -> ClaimDocument:
    return repo.families.claims.coerce(
        data,
        source=repo.families.claims.address(ref).require_path(),
    )


def _find_concept_entry(
    repo: Repository, id_or_name: str
) -> LoadedDocument[ConceptDocument] | None:
    tree = repo.tree()
    concept_index = repo.families.concepts.reference_index()
    artifact_id = concept_index.resolve_id(id_or_name)
    if artifact_id is None:
        return None
    for handle in repo.families.concepts.iter_handles():
        if handle.document.artifact_id != artifact_id:
            continue
        return LoadedDocument(
            filename=handle.ref.name,
            artifact_path=tree / handle.address.require_path(),
            store_root=tree,
            document=handle.document,
        )
    return None


def _require_concept_entry(
    repo: Repository, handle: str, *, label: str = "Concept"
) -> LoadedDocument[ConceptDocument]:
    concept_entry = _find_concept_entry(repo, handle)
    if concept_entry is None:
        raise ConceptMutationError(f"{label} '{handle}' not found")
    return concept_entry


def _require_concept_artifact_id(repo: Repository, handle: str, *, label: str) -> str:
    concept_entry = _require_concept_entry(repo, handle, label=label)
    artifact_id = concept_entry.document.artifact_id
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ConceptMutationError(f"{label} '{handle}' does not have an artifact_id")
    return artifact_id


def _require_concept_reference(
    repo: Repository, handle: str, *, label: str
) -> OntologyReference:
    concept_entry = _require_concept_entry(repo, handle, label=label)
    document = concept_entry.document
    artifact_id = document.artifact_id
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ConceptMutationError(f"{label} '{handle}' does not have an artifact_id")
    canonical_name = document.lexical_entry.canonical_form.written_rep
    return OntologyReference(uri=artifact_id, label=canonical_name)


def _provenance_document(
    *,
    asserter: str,
    timestamp: str,
    source_artifact_code: str,
    method: str,
) -> Provenance:
    return Provenance(
        status=ProvenanceStatus.STATED,
        witnesses=(
            ProvenanceWitness(
                asserter=asserter,
                timestamp=timestamp,
                source_artifact_code=source_artifact_code,
                method=method,
            ),
        ),
    )


def _form_registry(repo: Repository) -> dict[str, FormDefinition]:
    return {
        document.name: parse_form(document.name, document)
        for handle in repo.families.forms.iter_handles()
        for document in (handle.document,)
    }


def _loaded_concepts(repo: Repository) -> list[LoadedDocument[ConceptDocument]]:
    tree = repo.tree()
    concepts: list[LoadedDocument[ConceptDocument]] = []
    for handle in repo.families.concepts.iter_handles():
        concepts.append(
            LoadedDocument(
                filename=handle.ref.name,
                artifact_path=tree / handle.address.require_path(),
                store_root=tree,
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
    concepts: list[LoadedDocument[ConceptDocument]],
) -> PipelineResult[object]:
    tree = repo.tree()
    claim_files = [
        LoadedClaimsFile(
            filename=handle.ref.artifact_id,
            artifact_path=tree / handle.address.require_path(),
            store_root=tree,
            document=handle.document,
        )
        for handle in repo.families.claims.iter_handles()
    ]
    return run_concept_pipeline(
        normalize_loaded_concepts(concepts),
        context=ConceptPipelineContext(
            form_registry=_form_registry(repo),
            claim_index=build_compiler_claim_index(claim_files),
        ),
    )


def _validate_updated_concept(
    repo: Repository,
    concept_entry: LoadedDocument[ConceptDocument],
    document: ConceptDocument,
) -> tuple[str, ...]:
    ref = _concept_ref(concept_entry)
    concepts = []
    tree = repo.tree()
    for handle in repo.families.concepts.iter_handles():
        loaded_ref = handle.ref
        if loaded_ref == ref:
            concepts.append(
                LoadedDocument(
                    filename=loaded_ref.name,
                    artifact_path=tree
                    / repo.families.concepts.address(ref).require_path(),
                    store_root=tree,
                    document=document,
                )
            )
            continue
        concepts.append(
            LoadedDocument(
                filename=loaded_ref.name,
                artifact_path=tree / handle.address.require_path(),
                store_root=tree,
                document=handle.document,
            )
        )

    validation = _run_concept_validation(repo, concepts)
    _raise_validation_failure(validation)
    return tuple(_render_diagnostic(warning) for warning in validation.warnings)


def _apply_proto_role_entailment(
    bundle: ProtoRoleBundle,
    *,
    role_kind: str,
    entailment: GradedEntailment,
) -> ProtoRoleBundle:
    if role_kind == "agent":
        return replace_document(
            bundle,
            proto_agent_entailments=(
                *bundle.proto_agent_entailments,
                entailment,
            ),
        )
    return replace_document(
        bundle,
        proto_patient_entailments=(
            *bundle.proto_patient_entailments,
            entailment,
        ),
    )


@_serialized_concept_mutation
def add_concept(repo: Repository, request: ConceptAddRequest) -> ConceptMutationReport:
    _require_snapshot(repo)
    ref = ConceptFileRef(request.name)
    filepath = repo.root / Path(repo.families.concepts.address(ref).require_path())
    semantic_path = repo.tree() / repo.families.concepts.address(ref).require_path()
    if semantic_path.exists():
        raise ConceptMutationError(f"Concept file '{filepath}' already exists")

    domain = request.domain or "propstore"
    artifact_id = derive_concept_artifact_id(domain, request.name)
    ontology_reference = OntologyReferenceDocument(
        uri=artifact_id,
        label=request.name,
    )
    form_parameters: ConceptFormParametersDocument | None = None

    if request.form_name == "category":
        if not request.values:
            raise ConceptMutationError("values are required when form is category")
        value_list = [value.strip() for value in request.values if value.strip()]
        if not value_list:
            raise ConceptMutationError("values must contain at least one value")
        form_parameters = ConceptFormParametersDocument(
            values=tuple(value_list),
            extensible=False if request.closed else None,
        )
    elif request.values:
        raise ConceptMutationError("values are only valid when form is category")
    elif request.closed:
        raise ConceptMutationError("closed categories require form category")

    document = ConceptDocument(
        status=ConceptStatus.PROPOSED,
        ontology_reference=ontology_reference,
        lexical_entry=LexicalEntryDocument(
            identifier=request.name,
            canonical_form=LexicalFormDocument(
                written_rep=request.name,
                language="en",
            ),
            senses=(
                LexicalSenseDocument(
                    reference=ontology_reference,
                    usage=request.definition,
                ),
            ),
            physical_dimension_form=request.form_name,
        ),
        artifact_id=artifact_id,
        logical_ids=(
            ConceptLogicalIdDocument(namespace=domain, value=request.name),
        ),
        created_date=str(date.today()),
        definition_source=request.definition,
        domain=request.domain,
        form_parameters=form_parameters,
    )
    label = document.lexical_entry.canonical_form.written_rep

    if request.dry_run:
        return ConceptMutationReport(
            lines=(
                f"Would create {filepath}",
                repo.families.concepts.render(document),
            )
        )

    concepts = _loaded_concepts(repo)
    concepts.append(
        LoadedDocument(
            filename=request.name,
            artifact_path=semantic_path,
            store_root=repo.tree(),
            document=document,
        )
    )

    result = _run_concept_validation(repo, concepts)
    _raise_validation_failure(result)
    warnings = tuple(_render_diagnostic(warning) for warning in result.warnings)

    repo.families.concepts.save(
        ref,
        document,
        message=f"Add concept: {request.name} ({label})",
    )
    return ConceptMutationReport(
        lines=(f"Created {filepath} with logical ID {label}",),
        warnings=warnings,
    )


@_serialized_concept_mutation
def add_concept_alias(
    repo: Repository, request: ConceptAliasRequest
) -> ConceptMutationReport:
    assert_alias_does_not_target_reserved_namespace(request.name)
    _require_snapshot(repo)
    concept_entry = _require_concept_entry(repo, request.concept_id)
    ref = _concept_ref(concept_entry)
    filepath = repo.root / Path(repo.families.concepts.address(ref).require_path())
    document = concept_entry.document

    warnings: list[str] = []
    for handle in repo.families.concepts.iter_handles():
        other_ref = handle.ref
        if other_ref == ref:
            continue
        other_document = handle.document
        if other_document.lexical_entry.canonical_form.written_rep == request.name:
            warnings.append(
                f"alias '{request.name}' matches canonical_name of "
                f"concept '{other_document.artifact_id}'"
            )

    new_alias = ConceptAliasDocument(
        name=request.name,
        source=request.source,
        note=request.note,
    )

    if request.dry_run:
        return ConceptMutationReport(
            lines=(f"Would add alias to {filepath}: {new_alias}",),
            warnings=tuple(warnings),
        )

    updated_document = replace_document(
        document,
        aliases=(*document.aliases, new_alias),
        last_modified=str(date.today()),
    )
    label = updated_document.lexical_entry.canonical_form.written_rep
    repo.families.concepts.save(
        ref,
        updated_document,
        message=f"Add alias '{request.name}' to {label}",
    )

    return ConceptMutationReport(
        lines=(
            f"Added alias '{request.name}' to {label} ({filepath.stem})",
        ),
        warnings=tuple(warnings),
    )


@_serialized_concept_mutation
def deprecate_concept(
    repo: Repository, request: ConceptDeprecateRequest
) -> ConceptMutationReport:
    _require_snapshot(repo)
    concept_entry = _require_concept_entry(repo, request.concept_id)
    ref = _concept_ref(concept_entry)
    filepath = repo.root / Path(repo.families.concepts.address(ref).require_path())

    replacement_entry = _require_concept_entry(
        repo, request.replaced_by, label="Replacement concept"
    )
    replacement_document = replacement_entry.document
    if replacement_document.status is ConceptStatus.DEPRECATED:
        raise ConceptMutationError(
            f"Replacement concept '{request.replaced_by}' is itself deprecated"
        )

    if request.dry_run:
        label = concept_entry.document.lexical_entry.canonical_form.written_rep
        replacement_label = (
            replacement_document.lexical_entry.canonical_form.written_rep
        )
        return ConceptMutationReport(
            lines=(
                f"Would deprecate {label} ({filepath.stem})",
                f"  replaced_by: {replacement_label}",
            )
        )

    replacement_artifact_id = replacement_document.artifact_id
    if not isinstance(replacement_artifact_id, str) or not replacement_artifact_id:
        raise ConceptMutationError(
            f"Replacement concept '{request.replaced_by}' does not have an artifact_id"
        )
    updated_document = replace_document(
        concept_entry.document,
        status=ConceptStatus.DEPRECATED,
        replaced_by=replacement_artifact_id,
        last_modified=str(date.today()),
    )
    label = updated_document.lexical_entry.canonical_form.written_rep
    replacement_label = replacement_document.lexical_entry.canonical_form.written_rep
    repo.families.concepts.save(
        ref,
        updated_document,
        message=(
            f"Deprecate {label}, replaced by {replacement_label}"
        ),
    )
    return ConceptMutationReport(
        lines=(
            f"Deprecated {label} ({filepath.stem}), "
            f"replaced by {replacement_label}",
        )
    )


@_serialized_concept_mutation
def link_concepts(
    repo: Repository, request: ConceptLinkRequest
) -> ConceptMutationReport:
    if request.rel_type not in RELATIONSHIP_TYPES:
        raise ConceptMutationError(f"invalid relationship type: {request.rel_type}")
    _require_snapshot(repo)
    concept_entry = _require_concept_entry(
        repo, request.source_id, label="Source concept"
    )
    ref = _concept_ref(concept_entry)
    filepath = repo.root / Path(repo.families.concepts.address(ref).require_path())

    target_entry = _require_concept_entry(
        repo, request.target_id, label="Target concept"
    )
    target_document = target_entry.document
    target_artifact_id = target_document.artifact_id
    if not isinstance(target_artifact_id, str) or not target_artifact_id:
        raise ConceptMutationError(
            f"Target concept '{request.target_id}' does not have an artifact_id"
        )

    relationship = ConceptRelationshipDocument(
        type=ConceptRelationshipType(request.rel_type),
        target=target_artifact_id,
        source=request.paper_source,
        note=request.note,
        conditions=(
            tuple(condition.strip() for condition in request.conditions.split(","))
            if request.conditions
            else ()
        ),
    )

    if request.dry_run:
        return ConceptMutationReport(
            lines=(f"Would add relationship to {filepath.stem}: {relationship}",)
        )

    updated_document = replace_document(
        concept_entry.document,
        relationships=(*concept_entry.document.relationships, relationship),
        last_modified=str(date.today()),
    )

    updated_concepts = []
    for loaded_document in _loaded_concepts(repo):
        concept_ref = _concept_ref(loaded_document)
        updated_concepts.append(
            LoadedDocument(
                filename=loaded_document.filename,
                artifact_path=repo.tree()
                / repo.families.concepts.address(concept_ref).require_path(),
                store_root=loaded_document.store_root,
                document=(
                    updated_document if concept_ref == ref else loaded_document.document
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
            "Link "
            f"{updated_document.lexical_entry.canonical_form.written_rep} "
            f"{request.rel_type} "
            f"{target_document.lexical_entry.canonical_form.written_rep}"
        ),
    )
    return ConceptMutationReport(
        lines=(
            f"Added {request.rel_type} -> "
            f"{target_document.lexical_entry.canonical_form.written_rep} "
            f"on {updated_document.lexical_entry.canonical_form.written_rep} "
            f"({filepath.stem})",
        ),
        warnings=warnings,
    )


@_serialized_concept_mutation
def add_concept_qualia(
    repo: Repository, request: ConceptQualiaAddRequest
) -> ConceptMutationReport:
    if request.role not in QUALIA_ROLES:
        raise ConceptMutationError(f"invalid qualia role: {request.role}")
    _require_snapshot(repo)
    concept_entry = _require_concept_entry(repo, request.concept_id)
    ref = _concept_ref(concept_entry)
    document = concept_entry.document
    senses = document.lexical_entry.senses
    if not senses:
        raise ConceptMutationError("concept lexical_entry requires at least one sense")
    sense = senses[0]

    qualia = sense.qualia or QualiaStructure()
    entry = QualiaReference(
        reference=_require_concept_reference(
            repo, request.target_concept, label="Target concept"
        ),
        provenance=_provenance_document(
            asserter=request.asserter,
            timestamp=request.timestamp,
            source_artifact_code=request.source_artifact_code,
            method=request.method,
        ),
        type_constraint=(
            TypeConstraint(
                reference=_require_concept_reference(
                    repo,
                    request.type_constraint,
                    label="Type constraint",
                )
            )
            if request.type_constraint is not None
            else None
        ),
    )
    role = QualiaRole(request.role)
    if role is QualiaRole.FORMAL:
        qualia = replace_document(qualia, formal=(*qualia.formal, entry))
    elif role is QualiaRole.CONSTITUTIVE:
        qualia = replace_document(
            qualia,
            constitutive=(*qualia.constitutive, entry),
        )
    elif role is QualiaRole.TELIC:
        qualia = replace_document(qualia, telic=(*qualia.telic, entry))
    else:
        qualia = replace_document(qualia, agentive=(*qualia.agentive, entry))

    updated_sense = replace_document(sense, qualia=qualia)
    updated_document = replace_document(
        document,
        lexical_entry=replace_document(
            document.lexical_entry,
            senses=(updated_sense, *senses[1:]),
        ),
        last_modified=str(date.today()),
    )

    if request.dry_run:
        return ConceptMutationReport(
            lines=(repo.families.concepts.render(updated_document),)
        )

    warnings = _validate_updated_concept(repo, concept_entry, updated_document)
    label = updated_document.lexical_entry.canonical_form.written_rep
    repo.families.concepts.save(
        ref,
        updated_document,
        message=f"Add {request.role} qualia to {label}",
    )
    return ConceptMutationReport(
        lines=(f"Added {request.role} qualia to {label}",),
        warnings=warnings,
    )


@_serialized_concept_mutation
def set_concept_description_kind(
    repo: Repository, request: ConceptDescriptionKindRequest
) -> ConceptMutationReport:
    _require_snapshot(repo)
    concept_entry = _require_concept_entry(repo, request.concept_id)
    ref = _concept_ref(concept_entry)
    document = concept_entry.document
    senses = document.lexical_entry.senses
    if not senses:
        raise ConceptMutationError("concept lexical_entry requires at least one sense")
    sense = senses[0]

    slots: list[ParticipantSlot] = []
    for raw_slot in request.slots:
        slot_name, separator, type_handle = raw_slot.partition("=")
        if not separator or not slot_name or not type_handle:
            raise ConceptMutationError("slot must use name=type-concept")
        slots.append(
            ParticipantSlot(
                name=slot_name,
                type_constraint=_require_concept_reference(
                    repo,
                    type_handle,
                    label=f"Slot '{slot_name}' type constraint",
                ),
            )
        )

    updated_sense = replace_document(
        sense,
        description_kind=DescriptionKind(
            name=request.name,
            reference=_require_concept_reference(
                repo,
                request.reference_handle,
                label="Description-kind reference",
            ),
            slots=tuple(slots),
        ),
    )
    updated_document = replace_document(
        document,
        lexical_entry=replace_document(
            document.lexical_entry,
            senses=(updated_sense, *senses[1:]),
        ),
        last_modified=str(date.today()),
    )

    if request.dry_run:
        return ConceptMutationReport(
            lines=(repo.families.concepts.render(updated_document),)
        )

    warnings = _validate_updated_concept(repo, concept_entry, updated_document)
    label = updated_document.lexical_entry.canonical_form.written_rep
    repo.families.concepts.save(
        ref,
        updated_document,
        message=f"Set description kind on {label}",
    )
    return ConceptMutationReport(
        lines=(f"Set description kind on {label}",),
        warnings=warnings,
    )


@_serialized_concept_mutation
def add_concept_proto_role(
    repo: Repository, request: ConceptProtoRoleRequest
) -> ConceptMutationReport:
    if request.role_kind not in PROTO_ROLE_KINDS:
        raise ConceptMutationError(f"invalid proto-role kind: {request.role_kind}")
    _require_snapshot(repo)
    concept_entry = _require_concept_entry(repo, request.concept_id)
    ref = _concept_ref(concept_entry)
    document = concept_entry.document
    senses = document.lexical_entry.senses
    if not senses:
        raise ConceptMutationError("concept lexical_entry requires at least one sense")
    sense = senses[0]

    entailment = GradedEntailment(
        property=request.property_name,
        value=request.value,
        provenance=_provenance_document(
            asserter=request.asserter,
            timestamp=request.timestamp,
            source_artifact_code=request.source_artifact_code,
            method=request.method,
        ),
    )
    role_bundles = dict(sense.role_bundles or {})
    bundle = role_bundles.get(request.role_name) or ProtoRoleBundle()
    role_bundles[request.role_name] = _apply_proto_role_entailment(
        bundle,
        role_kind=request.role_kind,
        entailment=entailment,
    )

    description_kind = sense.description_kind
    if description_kind is not None:
        slots: list[ParticipantSlot] = []
        for slot in description_kind.slots:
            if slot.name != request.role_name:
                slots.append(slot)
                continue
            slot_bundle = slot.proto_role_bundle or ProtoRoleBundle()
            slots.append(
                replace_document(
                    slot,
                    proto_role_bundle=_apply_proto_role_entailment(
                        slot_bundle,
                        role_kind=request.role_kind,
                        entailment=entailment,
                    ),
                )
            )
        description_kind = replace_document(description_kind, slots=tuple(slots))

    updated_sense = replace_document(
        sense,
        role_bundles=role_bundles,
        description_kind=description_kind,
    )
    updated_document = replace_document(
        document,
        lexical_entry=replace_document(
            document.lexical_entry,
            senses=(updated_sense, *senses[1:]),
        ),
        last_modified=str(date.today()),
    )

    if request.dry_run:
        return ConceptMutationReport(
            lines=(repo.families.concepts.render(updated_document),)
        )

    warnings = _validate_updated_concept(repo, concept_entry, updated_document)
    label = updated_document.lexical_entry.canonical_form.written_rep
    repo.families.concepts.save(
        ref,
        updated_document,
        message=(
            f"Add {request.role_kind} proto-role {request.property_name} "
            f"to {label}"
        ),
    )
    return ConceptMutationReport(
        lines=(
            f"Added {request.role_kind} proto-role {request.property_name} "
            f"to {label}",
        ),
        warnings=warnings,
    )


@_serialized_concept_mutation
def add_concept_value(
    repo: Repository, request: ConceptAddValueRequest
) -> ConceptMutationReport:
    _require_snapshot(repo)
    concept_entry = _require_concept_entry(repo, request.concept_name)
    ref = _concept_ref(concept_entry)
    document = concept_entry.document

    if document.lexical_entry.physical_dimension_form != "category":
        raise ConceptMutationError(
            f"'{request.concept_name}' is not a category concept "
            f"(form={document.lexical_entry.physical_dimension_form})"
        )

    form_parameters = document.form_parameters or ConceptFormParametersDocument()
    extensible = (
        True if form_parameters.extensible is None else form_parameters.extensible
    )
    if not extensible:
        raise ConceptMutationError(
            f"'{request.concept_name}' is not extensible - cannot add values"
        )

    values = form_parameters.values or ()
    if request.value in values:
        raise ConceptMutationError(
            f"Value '{request.value}' already exists in '{request.concept_name}'"
        )

    if request.dry_run:
        return ConceptMutationReport(
            lines=(
                f"Would add '{request.value}' to "
                f"{request.concept_name} values: {(*values, request.value)}",
            )
        )

    updated_values = (*values, request.value)
    updated_document = replace_document(
        document,
        form_parameters=replace_document(form_parameters, values=updated_values),
        last_modified=str(date.today()),
    )
    repo.families.concepts.save(
        ref,
        updated_document,
        message=f"Add value '{request.value}' to {request.concept_name}",
    )
    return ConceptMutationReport(
        lines=(
            f"Added '{request.value}' to "
            f"{request.concept_name} - values: {', '.join(str(value) for value in updated_values)}",
        )
    )
