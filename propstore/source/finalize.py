from __future__ import annotations

from typing import Any, cast

from quire.lifecycle import FamilyRecordWrite
from propstore.families.artifacts import stamp_source_artifacts
from propstore.families.claims.references import resolve_first_claim_reference_id
from propstore.families.identity.micropubs import (
    micropub_artifact_id,
    micropub_version_id,
)
from propstore.families.registry import SourceRef
from propstore.repository import Repository
from quire.documents import convert_document_value
from propstore.families.claims.declaration import (
    ProvenanceDocument,
    SourceClaimDocument,
    SourceJustificationDocument,
)
from propstore.families.contexts.declaration import ContextReferenceDocument

from .common import (
    normalize_source_slug,
    source_paper_slug,
    source_tag_uri,
)
from propstore.families.micropublications.declaration import (
    MicropublicationDocument,
    MicropublicationEvidenceDocument,
)
from propstore.families.sources.declaration import (
    SourceDocument,
    SourceFinalizeReportDocument,
)
from propstore.families.stances.declaration import SourceStanceEntryDocument
from .reference_indexes import (
    primary_claim_index as build_primary_claim_index,
    source_claim_index as build_source_claim_index,
)
from propstore.families.concepts.lifecycle import (
    preview_source_parameterization_group_merges,
)
from .stages import SourceFinalizePlan


def _finalize_write(
    family: str,
    source_name: str,
    record: object,
) -> FamilyRecordWrite:
    return FamilyRecordWrite(
        family=family,
        identity=source_name,
        state="source",
        record=record,
    )


def _save_finalize_write(transaction: Any, write: FamilyRecordWrite) -> None:
    ref = SourceRef(write.identity)
    if write.family == "source_documents":
        transaction.source_documents.save(ref, cast(SourceDocument, write.record))
        return
    if write.family == "source_claims":
        transaction.source_claims.save(
            ref,
            cast(tuple[SourceClaimDocument, ...], write.record),
        )
        return
    if write.family == "source_justifications":
        transaction.source_justifications.save(
            ref,
            cast(tuple[SourceJustificationDocument, ...], write.record),
        )
        return
    if write.family == "source_stances":
        transaction.source_stances.save(
            ref,
            cast(tuple[SourceStanceEntryDocument, ...], write.record),
        )
        return
    if write.family == "source_micropubs":
        transaction.source_micropubs.save(
            ref,
            cast(tuple[MicropublicationDocument, ...], write.record),
        )
        return
    if write.family == "source_finalize_reports":
        transaction.source_finalize_reports.save(
            ref,
            cast(SourceFinalizeReportDocument, write.record),
        )
        return
    raise ValueError(f"unknown source finalize write family: {write.family!r}")


def _with_micropub_identity(
    document: MicropublicationDocument,
) -> MicropublicationDocument:
    return MicropublicationDocument(
        artifact_id=micropub_artifact_id(document),
        context=document.context,
        claims=document.claims,
        version_id=micropub_version_id(document),
        evidence=document.evidence,
        assumptions=document.assumptions,
        stance=document.stance,
        provenance=document.provenance,
        source=document.source,
    )


def _compose_source_micropubs(
    *,
    source_id: str,
    source_slug: str,
    claims_doc: tuple[SourceClaimDocument, ...] | None,
) -> tuple[MicropublicationDocument, ...] | None:
    if claims_doc is None or not claims_doc:
        return None
    micropubs: list[MicropublicationDocument] = []
    for claim in claims_doc:
        if not isinstance(claim.artifact_id, str) or not claim.artifact_id:
            continue
        if not isinstance(claim.context, str) or not claim.context:
            raise ValueError(
                f"claim {claim.source_local_id or claim.id or claim.artifact_id!r} "
                "is missing required context"
            )
        evidence: list[MicropublicationEvidenceDocument] = []
        provenance: ProvenanceDocument | None = None
        if claim.provenance is not None:
            paper = claim.provenance.paper or source_slug
            if claim.provenance.page is not None:
                evidence.append(
                    MicropublicationEvidenceDocument(
                        kind="paper_page",
                        reference=f"{paper}:{claim.provenance.page}",
                    )
                )
                provenance = ProvenanceDocument(
                    paper=paper,
                    page=claim.provenance.page,
                )
        micropubs.append(
            _with_micropub_identity(
                MicropublicationDocument(
                    artifact_id="",
                    context=ContextReferenceDocument(id=claim.context),
                    claims=(claim.artifact_id,),
                    evidence=tuple(evidence),
                    assumptions=tuple(claim.conditions),
                    provenance=provenance,
                    source=source_id,
                )
            )
        )
    if not micropubs:
        return None
    return tuple(micropubs)


def finalize_source_branch(
    repo: Repository,
    source_name: str,
    *,
    source_doc: SourceDocument | None = None,
) -> str:
    if source_doc is None:
        source_doc = repo.families.source_documents.require(SourceRef(source_name))
    if source_doc is None:
        raise ValueError(f"Source branch {source_name!r} does not exist")
    claims_doc = repo.families.source_claims.load(SourceRef(source_name))
    justifications_doc = repo.families.source_justifications.load(
        SourceRef(source_name)
    )
    stances_doc = repo.families.source_stances.load(SourceRef(source_name))
    concepts_doc = repo.families.source_concepts.load(SourceRef(source_name))

    source_claim_index = build_source_claim_index(repo, source_name)
    primary_claim_index = build_primary_claim_index(repo)

    claim_errors: list[str] = []
    micropub_coverage_errors: list[str] = []
    for claim in () if claims_doc is None else claims_doc:
        if not isinstance(claim.artifact_id, str):
            claim_errors.append(str(claim.id or "?"))
        if not isinstance(claim.context, str) or not claim.context:
            micropub_coverage_errors.append(
                str(claim.source_local_id or claim.id or claim.artifact_id or "?")
            )

    justification_errors: list[str] = []
    for justification in () if justifications_doc is None else justifications_doc:
        conclusion = justification.conclusion
        if not source_claim_index.exists(conclusion):
            justification_errors.append(str(conclusion))
        for premise in justification.premises:
            if not source_claim_index.exists(premise):
                justification_errors.append(str(premise))

    stance_errors: list[str] = []
    for stance in () if stances_doc is None else stances_doc:
        source_claim = stance.source_claim
        if not source_claim_index.exists(source_claim):
            stance_errors.append(str(source_claim))
        target = stance.target
        if not isinstance(target, str) or not target:
            stance_errors.append(str(target))
            continue
        if (
            resolve_first_claim_reference_id(
                target,
                source_claim_index,
                primary_claim_index,
            )
            is None
        ):
            stance_errors.append(target)

    concept_alignment_candidates = sorted(
        {
            f"align:{normalize_source_slug(str(entry.proposed_name or entry.local_name or 'concept'))}"
            for entry in (() if concepts_doc is None else concepts_doc)
            if entry.registry_match is None
        }
    )
    parameterization_group_merges = preview_source_parameterization_group_merges(
        repo, concepts_doc
    )

    derived_from = list(source_doc.trust.derived_from)
    covered = bool(derived_from)
    artifact_code_status = "incomplete"
    source_id = str(source_doc.id or source_tag_uri(repo, source_name))
    source_slug = source_paper_slug(source_name)
    micropubs_doc = (
        None
        if micropub_coverage_errors
        else _compose_source_micropubs(
            source_id=source_id,
            source_slug=source_slug,
            claims_doc=claims_doc,
        )
    )
    if micropub_coverage_errors:
        micropub_status = "blocked"
    else:
        micropub_status = "complete" if micropubs_doc is not None else "empty"
    branch = repo.families.source_documents.address(
        SourceRef(source_name)
    ).require_branch()
    ready = (
        not claim_errors
        and not micropub_coverage_errors
        and not justification_errors
        and not stance_errors
    )
    writes: list[FamilyRecordWrite] = []
    if ready:
        updated_source, updated_claims, updated_justifications, updated_stances = (
            stamp_source_artifacts(
                source_doc,
                claims_doc,
                justifications_doc,
                stances_doc,
            )
        )
        writes.append(_finalize_write("source_documents", source_name, updated_source))
        if updated_claims is not None and updated_claims:
            writes.append(_finalize_write("source_claims", source_name, updated_claims))
        if updated_justifications is not None and updated_justifications:
            writes.append(
                _finalize_write(
                    "source_justifications",
                    source_name,
                    updated_justifications,
                )
            )
        if updated_stances is not None and updated_stances:
            writes.append(
                _finalize_write("source_stances", source_name, updated_stances)
            )
        if micropubs_doc is not None:
            writes.append(
                _finalize_write("source_micropubs", source_name, micropubs_doc)
            )
        artifact_code_status = "complete"

    report = convert_document_value(
        {
            "kind": "source_finalize_report",
            "source": source_id,
            "status": "ready" if ready else "blocked",
            "claim_reference_errors": sorted(claim_errors),
            "micropub_coverage_errors": sorted(micropub_coverage_errors),
            "justification_reference_errors": sorted(justification_errors),
            "stance_reference_errors": sorted(stance_errors),
            "concept_alignment_candidates": concept_alignment_candidates,
            "parameterization_group_merges": parameterization_group_merges,
            "artifact_code_status": artifact_code_status,
            "micropub_status": micropub_status,
            "calibration": {
                "prior_base_rate_status": "covered" if covered else "fallback",
                "source_quality_status": "vacuous",
                "fallback_to_default_base_rate": not covered,
            },
        },
        SourceFinalizeReportDocument,
        source=f"{branch}:merge/finalize",
    )
    writes.append(_finalize_write("source_finalize_reports", source_name, report))
    finalize_plan = SourceFinalizePlan(
        source_name=source_name,
        source_branch=branch,
        writes=tuple(writes),
    )
    sha: str | None = None
    git = repo.git
    if git is None:
        raise ValueError("source finalize requires a git-backed repository")
    with git.head_bound_transaction(finalize_plan.source_branch) as head_txn:
        with head_txn.families_transact(
            repo.families, message=f"Finalize {source_slug}"
        ) as transaction:
            for write in finalize_plan.writes:
                _save_finalize_write(transaction, write)
        sha = head_txn.commit_sha
    if sha is None:
        raise ValueError("source finalize transaction did not produce a commit")
    return sha
