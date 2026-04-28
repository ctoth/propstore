from __future__ import annotations

from propstore.artifact_codes import attach_source_artifact_codes
from propstore.claim_references import (
    ClaimReferenceResolver,
    load_primary_branch_claim_reference_index,
    load_source_claim_reference_index,
)
from propstore.families.identity.micropubs import (
    micropub_artifact_id,
    micropub_version_id,
)
from propstore.families.registry import SourceRef
from propstore.repository import Repository
from quire.documents import convert_document_value

from .common import (
    load_source_claims_document,
    load_source_concepts_document,
    load_source_document,
    load_source_justifications_document,
    load_source_stances_document,
    normalize_source_slug,
    source_branch_name,
    source_paper_slug,
    source_tag_uri,
)
from propstore.families.documents.sources import (
    SourceClaimsDocument,
    SourceDocument,
    SourceFinalizeReportDocument,
    SourceJustificationsDocument,
    SourceStancesDocument,
)
from propstore.families.documents.micropubs import (
    MicropublicationDocument,
    MicropublicationsFileDocument,
)
from .registry import preview_source_parameterization_group_merges


def _stamp_micropub_identity(payload: dict[str, object]) -> dict[str, object]:
    document = convert_document_value(
        {**payload, "artifact_id": ""},
        MicropublicationDocument,
        source="source-finalize:micropub-identity",
    )
    stamped = dict(payload)
    stamped["artifact_id"] = micropub_artifact_id(document)
    stamped["version_id"] = micropub_version_id(document)
    return stamped


def _compose_source_micropubs(
    *,
    source_id: str,
    source_slug: str,
    claims_doc: SourceClaimsDocument | None,
) -> MicropublicationsFileDocument | None:
    if claims_doc is None or not claims_doc.claims:
        return None
    micropubs: list[dict[str, object]] = []
    for claim in claims_doc.claims:
        if not isinstance(claim.artifact_id, str) or not claim.artifact_id:
            continue
        if not isinstance(claim.context, str) or not claim.context:
            continue
        evidence: list[dict[str, str]] = []
        provenance_payload: dict[str, object] | None = None
        if claim.provenance is not None:
            paper = claim.provenance.paper or source_slug
            if claim.provenance.page is not None:
                evidence.append({
                    "kind": "paper_page",
                    "reference": f"{paper}:{claim.provenance.page}",
                })
                provenance_payload = {
                    "paper": paper,
                    "page": claim.provenance.page,
                }
        payload: dict[str, object] = {
            "context": {"id": claim.context},
            "claims": [claim.artifact_id],
            "source": source_id,
        }
        if evidence:
            payload["evidence"] = evidence
        if claim.conditions:
            payload["assumptions"] = list(claim.conditions)
        if provenance_payload is not None:
            payload["provenance"] = provenance_payload
        micropubs.append(_stamp_micropub_identity(payload))
    if not micropubs:
        return None
    return convert_document_value(
        {
            "source": {"paper": source_slug},
            "micropubs": micropubs,
        },
        MicropublicationsFileDocument,
        source=f"{source_branch_name(source_slug)}:micropubs.yaml",
    )


def finalize_source_branch(
    repo: Repository,
    source_name: str,
    *,
    source_doc: SourceDocument | None = None,
) -> str:
    if source_doc is None:
        source_doc = load_source_document(repo, source_name)
    claims_doc = load_source_claims_document(repo, source_name)
    justifications_doc = load_source_justifications_document(repo, source_name)
    stances_doc = load_source_stances_document(repo, source_name)
    concepts_doc = load_source_concepts_document(repo, source_name)

    source_claim_index = load_source_claim_reference_index(repo, source_name)
    primary_claim_index = load_primary_branch_claim_reference_index(repo)
    resolver = ClaimReferenceResolver(
        source=source_claim_index,
        primary=primary_claim_index,
    )

    claim_errors: list[str] = []
    for claim in (() if claims_doc is None else claims_doc.claims):
        if not isinstance(claim.artifact_id, str):
            claim_errors.append(str(claim.id or "?"))

    justification_errors: list[str] = []
    for justification in (() if justifications_doc is None else justifications_doc.justifications):
        conclusion = justification.conclusion
        if not source_claim_index.has_artifact(conclusion):
            justification_errors.append(str(conclusion))
        for premise in justification.premises:
            if not source_claim_index.has_artifact(premise):
                justification_errors.append(str(premise))

    stance_errors: list[str] = []
    for stance in (() if stances_doc is None else stances_doc.stances):
        source_claim = stance.source_claim
        if not source_claim_index.has_artifact(source_claim):
            stance_errors.append(str(source_claim))
        target = stance.target
        if not isinstance(target, str) or not target:
            stance_errors.append(str(target))
            continue
        if not resolver.target_is_known(target):
            stance_errors.append(target)

    concept_alignment_candidates = sorted(
        {
            f"align:{normalize_source_slug(str(entry.proposed_name or entry.local_name or 'concept'))}"
            for entry in (() if concepts_doc is None else concepts_doc.concepts)
            if entry.registry_match is None
        }
    )
    parameterization_group_merges = preview_source_parameterization_group_merges(repo, concepts_doc)

    derived_from = list(source_doc.trust.derived_from)
    covered = bool(derived_from)
    artifact_code_status = "incomplete"
    source_id = str(source_doc.id or source_tag_uri(repo, source_name))
    source_slug = source_paper_slug(source_name)
    micropubs_doc = _compose_source_micropubs(
        source_id=source_id,
        source_slug=source_slug,
        claims_doc=claims_doc,
    )
    micropub_status = "complete" if micropubs_doc is not None else "empty"
    with repo.families.transact(
        message=f"Finalize {source_slug}",
        branch=source_branch_name(source_name),
    ) as transaction:
        ref = SourceRef(source_name)
        if not claim_errors and not justification_errors and not stance_errors:
            updated_source, updated_claims, updated_justifications, updated_stances = attach_source_artifact_codes(
                source_doc.to_payload(),
                None if claims_doc is None else claims_doc.to_payload(),
                None if justifications_doc is None else justifications_doc.to_payload(),
                None if stances_doc is None else stances_doc.to_payload(),
            )
            transaction.source_documents.save(
                ref,
                convert_document_value(
                    updated_source,
                    type(source_doc),
                    source=f"{source_branch_name(source_name)}:source.yaml",
                ),
            )
            if updated_claims.get("claims"):
                transaction.source_claims.save(
                    ref,
                    convert_document_value(
                        updated_claims,
                        SourceClaimsDocument,
                        source=f"{source_branch_name(source_name)}:claims.yaml",
                    ),
                )
            if updated_justifications.get("justifications"):
                transaction.source_justifications.save(
                    ref,
                    convert_document_value(
                        updated_justifications,
                        SourceJustificationsDocument,
                        source=f"{source_branch_name(source_name)}:justifications.yaml",
                    ),
                )
            if updated_stances.get("stances"):
                transaction.source_stances.save(
                    ref,
                    convert_document_value(
                        updated_stances,
                        SourceStancesDocument,
                        source=f"{source_branch_name(source_name)}:stances.yaml",
                    ),
                )
            if micropubs_doc is not None:
                transaction.source_micropubs.save(
                    ref,
                    micropubs_doc,
                )
            artifact_code_status = "complete"

        report = convert_document_value(
            {
                "kind": "source_finalize_report",
                "source": source_id,
                "status": "ready"
                if not claim_errors and not justification_errors and not stance_errors
                else "blocked",
                "claim_reference_errors": sorted(claim_errors),
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
            source=f"{source_branch_name(source_name)}:merge/finalize",
        )
        transaction.source_finalize_reports.save(ref, report)
    if transaction.commit_sha is None:
        raise ValueError("source finalize transaction did not produce a commit")
    return transaction.commit_sha
