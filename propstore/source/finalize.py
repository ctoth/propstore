"""Source-branch finalize: the promotability precondition + micropub compose.

``finalize_source_branch`` is the workflow gate a source branch must pass before
it can be promoted into ``master``. It records (it does not collapse):

* a **micropublication-coverage** check — every authored claim must carry a
  context so a Clark micropublication can be composed for it (Clark, Ciccarese &
  Goble 2014); a claim with no context cannot be bundled and blocks the finalize;
* a **reference-integrity** check — every justification premise/conclusion and
  every stance source/target must resolve through the source (then primary)
  claim reference index (the source-local→canonical lowering surface);
* **artifact-code stamping** — a deterministic content hash on each artifact;
* **micropublication composition** — the Clark bundles, each with its own ``ni:``
  content identity.

A finalize either succeeds (``status="ready"`` — the branch is promotable) or
records what is missing (``status="blocked"`` plus the per-kind error lists),
and writes everything atomically through one head-bound multi-family transaction.
This is a precondition on the source branch, not a render-time truth gate over the
canonical corpus: it rejects an *incomplete* finalize, it never drops a rival
claim (that would violate the non-commitment discipline).
"""

from __future__ import annotations

import msgspec

from propstore.artifact_codes import stamp_source_artifact_codes
from propstore.families.identity.micropubs import (
    micropub_artifact_id,
    micropub_version_id,
)
from propstore.families.micropublications import MicropublicationEvidence
from propstore.families.registry import SourceRef
from propstore.families.sources import (
    ClaimSourceDocument,
    SourceClaimsDocument,
    SourceDocument,
    SourceFinalizeCalibrationDocument,
    SourceFinalizeReportDocument,
    SourceMicropublicationDocument,
    SourceMicropublicationsDocument,
    SourceProvenanceDocument,
)
from propstore.repository import Repository

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
from .reference_indexes import (
    primary_claim_index as build_primary_claim_index,
    resolve_source_or_primary_claim_id,
    source_claim_index as build_source_claim_index,
)


def _with_micropub_identity(
    document: SourceMicropublicationDocument,
) -> SourceMicropublicationDocument:
    return msgspec.structs.replace(
        document,
        artifact_id=micropub_artifact_id(document),
        version_id=micropub_version_id(document),
    )


def _compose_source_micropubs(
    *,
    source_id: str,
    source_slug: str,
    claims_doc: SourceClaimsDocument | None,
) -> SourceMicropublicationsDocument | None:
    """Compose one Clark micropublication bundle per contexted source claim."""

    if claims_doc is None or not claims_doc.claims:
        return None
    micropubs: list[SourceMicropublicationDocument] = []
    for claim in claims_doc.claims:
        if not isinstance(claim.artifact_id, str) or not claim.artifact_id:
            continue
        if not isinstance(claim.context, str) or not claim.context:
            raise ValueError(
                f"claim {claim.source_local_id or claim.id or claim.artifact_id!r} "
                "is missing required context"
            )
        evidence: list[MicropublicationEvidence] = []
        provenance: SourceProvenanceDocument | None = None
        if claim.provenance is not None:
            paper = claim.provenance.paper or source_slug
            if claim.provenance.page is not None:
                evidence.append(
                    MicropublicationEvidence(
                        kind="paper_page",
                        reference=f"{paper}:{claim.provenance.page}",
                    )
                )
                provenance = SourceProvenanceDocument(paper=paper, page=claim.provenance.page)
        micropubs.append(
            _with_micropub_identity(
                SourceMicropublicationDocument(
                    artifact_id="",
                    context_id=claim.context,
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
    return SourceMicropublicationsDocument(
        source=ClaimSourceDocument(paper=source_slug),
        micropubs=tuple(micropubs),
    )


def finalize_source_branch(
    repo: Repository,
    source_name: str,
    *,
    source_doc: SourceDocument | None = None,
) -> str:
    """Finalize a source branch; write the precondition report; return the sha."""

    if source_doc is None:
        source_doc = load_source_document(repo, source_name)
    claims_doc = load_source_claims_document(repo, source_name)
    justifications_doc = load_source_justifications_document(repo, source_name)
    stances_doc = load_source_stances_document(repo, source_name)
    concepts_doc = load_source_concepts_document(repo, source_name)

    source_claim_index = build_source_claim_index(repo, source_name)
    primary_claim_index = build_primary_claim_index(repo)

    claim_errors: list[str] = []
    micropub_coverage_errors: list[str] = []
    for claim in () if claims_doc is None else claims_doc.claims:
        if not isinstance(claim.artifact_id, str):
            claim_errors.append(str(claim.id or "?"))
        if not isinstance(claim.context, str) or not claim.context:
            micropub_coverage_errors.append(
                str(claim.source_local_id or claim.id or claim.artifact_id or "?")
            )

    justification_errors: list[str] = []
    for justification in () if justifications_doc is None else justifications_doc.justifications:
        conclusion = justification.conclusion
        if conclusion is None or not source_claim_index.exists(conclusion):
            justification_errors.append(str(conclusion))
        for premise in justification.premises:
            if not source_claim_index.exists(premise):
                justification_errors.append(str(premise))

    stance_errors: list[str] = []
    for stance in () if stances_doc is None else stances_doc.stances:
        source_claim = stance.source_claim
        if source_claim is None or not source_claim_index.exists(source_claim):
            stance_errors.append(str(source_claim))
        target = stance.target
        if not isinstance(target, str) or not target:
            stance_errors.append(str(target))
            continue
        if (
            resolve_source_or_primary_claim_id(
                target,
                source=source_claim_index,
                primary=primary_claim_index,
            )
            is None
        ):
            stance_errors.append(target)

    concept_alignment_candidates = sorted(
        {
            "align:"
            + normalize_source_slug(
                str(entry.proposed_name or entry.local_name or "concept")
            )
            for entry in (() if concepts_doc is None else concepts_doc.concepts)
            if entry.registry_match is None
        }
    )

    derived_from = list(source_doc.trust.derived_from)
    covered = bool(derived_from)
    source_id = source_doc.id or source_tag_uri(repo, source_name)
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

    ready = not (
        claim_errors or micropub_coverage_errors or justification_errors or stance_errors
    )
    artifact_code_status = "complete" if ready else "incomplete"

    branch = source_branch_name(source_name)
    git = repo.git
    if git is None:
        raise ValueError("source finalize requires a git-backed repository")

    report = SourceFinalizeReportDocument(
        kind="source_finalize_report",
        source=source_id,
        status="ready" if ready else "blocked",
        artifact_code_status=artifact_code_status,
        calibration=SourceFinalizeCalibrationDocument(
            prior_base_rate_status="covered" if covered else "fallback",
            source_quality_status="vacuous",
            fallback_to_default_base_rate=not covered,
        ),
        micropub_status=micropub_status,
        claim_reference_errors=tuple(sorted(claim_errors)),
        micropub_coverage_errors=tuple(sorted(micropub_coverage_errors)),
        justification_reference_errors=tuple(sorted(justification_errors)),
        stance_reference_errors=tuple(sorted(stance_errors)),
        concept_alignment_candidates=tuple(concept_alignment_candidates),
    )

    with git.head_bound_transaction(branch) as head_txn:
        with head_txn.families_transact(
            repo.families, message=f"Finalize {source_slug}"
        ) as transaction:
            ref = SourceRef(source_name)
            if ready:
                (
                    updated_source,
                    updated_claims,
                    updated_justifications,
                    updated_stances,
                ) = stamp_source_artifact_codes(
                    source_doc, claims_doc, justifications_doc, stances_doc
                )
                transaction.source_documents.save(ref, updated_source)
                if updated_claims is not None and updated_claims.claims:
                    transaction.source_claims.save(ref, updated_claims)
                if updated_justifications is not None and updated_justifications.justifications:
                    transaction.source_justifications.save(ref, updated_justifications)
                if updated_stances is not None and updated_stances.stances:
                    transaction.source_stances.save(ref, updated_stances)
                if micropubs_doc is not None:
                    transaction.source_micropubs.save(ref, micropubs_doc)
            transaction.source_finalize_reports.save(ref, report)
        sha = head_txn.commit_sha
    if sha is None:
        raise ValueError("source finalize transaction did not produce a commit")
    return sha
