"""Application-layer source authoring and lifecycle workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from propstore.provenance import ProvenanceStatus
from propstore.repository import Repository
from propstore.source import SourceStatusState, source_branch_name


class SourceAppError(Exception):
    """Base class for expected app-layer source failures."""


@dataclass(frozen=True)
class SourceInitRequest:
    name: str
    kind: str
    origin_type: str
    origin_value: str
    content_file: Path | None = None


@dataclass(frozen=True)
class SourceNamedRequest:
    name: str


@dataclass(frozen=True)
class SourcePromoteRequest:
    name: str
    strict: bool = False


@dataclass(frozen=True)
class SourceSyncRequest:
    name: str
    output_dir: Path | None = None


@dataclass(frozen=True)
class SourceStampProvenanceRequest:
    file_path: Path
    agent: str
    skill_name: str
    status: ProvenanceStatus
    plugin_version: str | None = None


@dataclass(frozen=True)
class SourceBatchRequest:
    name: str
    batch_file: Path
    reader: str | None = None
    method: str | None = None


@dataclass(frozen=True)
class SourceConceptProposalRequest:
    source_name: str
    concept_name: str
    definition: str
    form_name: str
    values: str | None = None
    closed: bool = False


@dataclass(frozen=True)
class SourceClaimProposalRequest:
    source_name: str
    claim_id: str
    claim_type: str
    statement: str | None
    concept: str | None
    value: float | None
    unit: str | None
    context: str
    page: int | None


@dataclass(frozen=True)
class SourceJustificationProposalRequest:
    source_name: str
    justification_id: str
    conclusion: str
    premises: str
    rule_kind: str
    page: int | None = None


@dataclass(frozen=True)
class SourceStanceProposalRequest:
    source_name: str
    source_claim: str
    target: str
    stance_type: str
    strength: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class SourceBranchReport:
    branch: str


@dataclass(frozen=True)
class SourcePromoteReport:
    branch: str
    total_claims: int
    promoted_count: int
    blocked_count: int


@dataclass(frozen=True)
class SourceSyncReport:
    branch: str
    destination: Path


@dataclass(frozen=True)
class SourceBatchReport:
    branch: str
    auto_finalized_branch: str


@dataclass(frozen=True)
class SourceConceptProposalReport:
    concept_name: str
    form_name: str
    status: str
    linked_canonical_name: str | None = None
    linked_artifact_id: str | None = None


@dataclass(frozen=True)
class SourceClaimProposalReport:
    claim_id: str
    claim_type: str
    artifact_id: str


@dataclass(frozen=True)
class SourceJustificationProposalReport:
    justification_id: str
    rule_kind: str
    premises: tuple[str, ...]
    conclusion: str


@dataclass(frozen=True)
class SourceStanceProposalReport:
    source_claim: str
    stance_type: str
    target: str


def init_source(repo: Repository, request: SourceInitRequest) -> SourceBranchReport:
    from propstore.core.source_types import (
        coerce_source_kind,
        coerce_source_origin_type,
    )
    from propstore.source import init_source_branch

    branch = init_source_branch(
        repo,
        request.name,
        kind=coerce_source_kind(request.kind),
        origin_type=coerce_source_origin_type(request.origin_type),
        origin_value=request.origin_value,
        content_file=request.content_file,
    )
    return SourceBranchReport(branch=branch)


def finalize_source(repo: Repository, request: SourceNamedRequest) -> SourceBranchReport:
    from propstore.heuristic.source_trust import derive_source_document_trust
    from propstore.source import finalize_source_branch
    from propstore.source.common import load_source_document

    source_doc = load_source_document(repo, request.name)
    finalize_source_branch(
        repo,
        request.name,
        source_doc=derive_source_document_trust(repo, source_doc),
    )
    return SourceBranchReport(branch=source_branch_name(request.name))


def promote_source(
    repo: Repository,
    request: SourcePromoteRequest,
) -> SourcePromoteReport:
    from propstore.source import promote_source_branch
    from propstore.source.common import (
        load_source_claims_document,
        load_source_finalize_report,
    )

    promote_source_branch(repo, request.name, strict=request.strict)
    claims_doc = load_source_claims_document(repo, request.name)
    report = load_source_finalize_report(repo, request.name)
    total_claims = len(claims_doc.claims) if claims_doc is not None else 0
    blocked_count = 0
    if report is not None:
        blocked_count = (
            len(report.claim_reference_errors)
            + len(report.justification_reference_errors)
            + len(report.stance_reference_errors)
        )
        blocked_count = min(blocked_count, total_claims)
    promoted_count = max(0, total_claims - blocked_count)
    return SourcePromoteReport(
        branch=source_branch_name(request.name),
        total_claims=total_claims,
        promoted_count=promoted_count,
        blocked_count=blocked_count,
    )


def inspect_source(repo: Repository, request: SourceNamedRequest):
    from propstore.source import inspect_source_status

    return inspect_source_status(repo, request.name)


def sync_source(repo: Repository, request: SourceSyncRequest) -> SourceSyncReport:
    from propstore.source import sync_source_branch

    destination = sync_source_branch(
        repo,
        request.name,
        output_dir=request.output_dir,
    )
    return SourceSyncReport(
        branch=source_branch_name(request.name),
        destination=destination,
    )


def stamp_source_provenance(request: SourceStampProvenanceRequest) -> Path:
    from propstore.provenance import stamp_file

    stamp_file(
        request.file_path,
        agent=request.agent,
        skill=request.skill_name,
        status=request.status,
        plugin_version=request.plugin_version,
    )
    return request.file_path


def write_source_notes(
    repo: Repository,
    request: SourceBatchRequest,
) -> SourceBranchReport:
    from propstore.source import commit_source_notes

    commit_source_notes(repo, request.name, request.batch_file)
    return SourceBranchReport(branch=source_branch_name(request.name))


def write_source_metadata(
    repo: Repository,
    request: SourceBatchRequest,
) -> SourceBranchReport:
    from propstore.source import commit_source_metadata

    commit_source_metadata(repo, request.name, request.batch_file)
    return SourceBranchReport(branch=source_branch_name(request.name))


def add_source_concepts_batch(
    repo: Repository,
    request: SourceBatchRequest,
) -> SourceBatchReport:
    from propstore.source import commit_source_concepts_batch

    commit_source_concepts_batch(repo, request.name, request.batch_file)
    return _auto_finalize_source(repo, request.name)


def add_source_claims_batch(
    repo: Repository,
    request: SourceBatchRequest,
) -> SourceBatchReport:
    from propstore.source import commit_source_claims_batch

    commit_source_claims_batch(
        repo,
        request.name,
        request.batch_file,
        reader=request.reader,
        method=request.method,
    )
    return _auto_finalize_source(repo, request.name)


def add_source_justifications_batch(
    repo: Repository,
    request: SourceBatchRequest,
) -> SourceBatchReport:
    from propstore.source import commit_source_justifications_batch

    commit_source_justifications_batch(
        repo,
        request.name,
        request.batch_file,
        reader=request.reader,
        method=request.method,
    )
    return _auto_finalize_source(repo, request.name)


def add_source_stances_batch(
    repo: Repository,
    request: SourceBatchRequest,
) -> SourceBatchReport:
    from propstore.source import commit_source_stances_batch

    commit_source_stances_batch(
        repo,
        request.name,
        request.batch_file,
        reader=request.reader,
        method=request.method,
    )
    return _auto_finalize_source(repo, request.name)


def propose_source_concept(
    repo: Repository,
    request: SourceConceptProposalRequest,
) -> SourceConceptProposalReport:
    from propstore.families.documents.sources import SourceConceptFormParametersDocument
    from propstore.source import commit_source_concept_proposal

    if request.closed and request.form_name != "category":
        raise SourceAppError("--closed is only valid with --form=category")
    if request.values is not None and request.form_name != "category":
        raise SourceAppError("--values is only valid with --form=category")

    form_parameters: SourceConceptFormParametersDocument | None = None
    if request.values is not None:
        value_list = tuple(
            value.strip() for value in request.values.split(",") if value.strip()
        )
        form_parameters = SourceConceptFormParametersDocument(
            values=value_list,
            extensible=False if request.closed else None,
        )
    elif request.closed:
        form_parameters = SourceConceptFormParametersDocument(extensible=False)

    info = commit_source_concept_proposal(
        repo,
        request.source_name,
        local_name=request.concept_name,
        definition=request.definition,
        form=request.form_name,
        form_parameters=form_parameters,
    )
    match = info.registry_match
    return SourceConceptProposalReport(
        concept_name=request.concept_name,
        form_name=info.form or request.form_name,
        status=info.status or "proposed",
        linked_canonical_name=(
            None if match is None else match.canonical_name or request.concept_name
        ),
        linked_artifact_id=None if match is None else match.artifact_id,
    )


def propose_source_claim(
    repo: Repository,
    request: SourceClaimProposalRequest,
) -> SourceClaimProposalReport:
    from propstore.core.claim_types import coerce_claim_type
    from propstore.source import commit_source_claim_proposal

    typed_claim_type = coerce_claim_type(request.claim_type)
    if typed_claim_type is None:
        raise SourceAppError("claim type is required")
    entry = commit_source_claim_proposal(
        repo,
        request.source_name,
        claim_id=request.claim_id,
        claim_type=typed_claim_type,
        statement=request.statement,
        concept=request.concept,
        value=request.value,
        unit=request.unit,
        context=request.context,
        page=request.page,
    )
    return SourceClaimProposalReport(
        claim_id=request.claim_id,
        claim_type=typed_claim_type.value,
        artifact_id="" if entry.artifact_id is None else entry.artifact_id,
    )


def propose_source_justification(
    repo: Repository,
    request: SourceJustificationProposalRequest,
) -> SourceJustificationProposalReport:
    from propstore.source import commit_source_justification_proposal

    premises_list = tuple(
        premise.strip() for premise in request.premises.split(",") if premise.strip()
    )
    entry = commit_source_justification_proposal(
        repo,
        request.source_name,
        just_id=request.justification_id,
        conclusion=request.conclusion,
        premises=list(premises_list),
        rule_kind=request.rule_kind,
        page=request.page,
    )
    return SourceJustificationProposalReport(
        justification_id=request.justification_id,
        rule_kind=request.rule_kind,
        premises=entry.premises or premises_list,
        conclusion=entry.conclusion or request.conclusion,
    )


def propose_source_stance(
    repo: Repository,
    request: SourceStanceProposalRequest,
) -> SourceStanceProposalReport:
    from propstore.source import commit_source_stance_proposal
    from propstore.stances import coerce_stance_type

    typed_stance_type = coerce_stance_type(request.stance_type)
    if typed_stance_type is None:
        raise SourceAppError("stance type is required")
    entry = commit_source_stance_proposal(
        repo,
        request.source_name,
        source_claim=request.source_claim,
        target=request.target,
        stance_type=typed_stance_type,
        strength=request.strength,
        note=request.note,
    )
    return SourceStanceProposalReport(
        source_claim=request.source_claim,
        stance_type=typed_stance_type.value,
        target=request.target,
    )


def _auto_finalize_source(repo: Repository, name: str) -> SourceBatchReport:
    from propstore.heuristic.source_trust import derive_source_document_trust
    from propstore.source import finalize_source_branch
    from propstore.source.common import load_source_document

    source_doc = load_source_document(repo, name)
    finalize_source_branch(
        repo,
        name,
        source_doc=derive_source_document_trust(repo, source_doc),
    )
    branch = source_branch_name(name)
    return SourceBatchReport(branch=branch, auto_finalized_branch=branch)
