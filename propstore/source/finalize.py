from __future__ import annotations

import yaml

from propstore.artifact_codes import attach_source_artifact_codes
from propstore.cli.repository import Repository
from propstore.document_schema import convert_document_value
from propstore.source_calibration import derive_source_trust

from .claims import load_primary_branch_claim_index, load_source_claim_index
from .common import (
    load_source_claims_document,
    load_source_concepts_document,
    load_source_document,
    load_source_justifications_document,
    load_source_stances_document,
    normalize_source_slug,
    source_branch_name,
    source_tag_uri,
)
from propstore.source_documents import SourceFinalizeReportDocument
from .registry import preview_source_parameterization_group_merges


def finalize_source_branch(repo: Repository, source_name: str) -> str:
    source_doc = derive_source_trust(repo, load_source_document(repo, source_name))
    claims_doc = load_source_claims_document(repo, source_name)
    justifications_doc = load_source_justifications_document(repo, source_name)
    stances_doc = load_source_stances_document(repo, source_name)
    concepts_doc = load_source_concepts_document(repo, source_name)

    local_to_artifact, logical_to_artifact, local_artifact_ids = load_source_claim_index(repo, source_name)
    primary_logical_to_artifact, primary_artifact_ids = load_primary_branch_claim_index(repo)

    claim_errors: list[str] = []
    for claim in (() if claims_doc is None else claims_doc.claims):
        if not isinstance(claim.artifact_id, str):
            claim_errors.append(str(claim.id or "?"))

    justification_errors: list[str] = []
    for justification in (() if justifications_doc is None else justifications_doc.justifications):
        conclusion = justification.conclusion
        if not isinstance(conclusion, str) or conclusion not in local_artifact_ids:
            justification_errors.append(str(conclusion))
        for premise in justification.premises:
            if not isinstance(premise, str) or premise not in local_artifact_ids:
                justification_errors.append(str(premise))

    stance_errors: list[str] = []
    for stance in (() if stances_doc is None else stances_doc.stances):
        source_claim = stance.source_claim
        if not isinstance(source_claim, str) or source_claim not in local_artifact_ids:
            stance_errors.append(str(source_claim))
        target = stance.target
        if not isinstance(target, str) or not target:
            stance_errors.append(str(target))
            continue
        if target in local_artifact_ids or target in primary_artifact_ids:
            continue
        if target in logical_to_artifact or target in primary_logical_to_artifact:
            continue
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
    adds: dict[str, bytes] = {}
    if not claim_errors and not justification_errors and not stance_errors:
        updated_source, updated_claims, updated_justifications, updated_stances = attach_source_artifact_codes(
            source_doc.to_payload(),
            None if claims_doc is None else claims_doc.to_payload(),
            None if justifications_doc is None else justifications_doc.to_payload(),
            None if stances_doc is None else stances_doc.to_payload(),
        )
        adds["source.yaml"] = yaml.safe_dump(updated_source, sort_keys=False, allow_unicode=True).encode("utf-8")
        if updated_claims.get("claims"):
            adds["claims.yaml"] = yaml.safe_dump(updated_claims, sort_keys=False, allow_unicode=True).encode("utf-8")
        if updated_justifications.get("justifications"):
            adds["justifications.yaml"] = yaml.safe_dump(
                updated_justifications,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        if updated_stances.get("stances"):
            adds["stances.yaml"] = yaml.safe_dump(updated_stances, sort_keys=False, allow_unicode=True).encode("utf-8")
        artifact_code_status = "complete"

    report = convert_document_value(
        {
        "kind": "source_finalize_report",
        "source": str(source_doc.id or source_tag_uri(repo, source_name)),
        "status": "ready" if not claim_errors and not justification_errors and not stance_errors else "blocked",
        "claim_reference_errors": sorted(claim_errors),
        "justification_reference_errors": sorted(justification_errors),
        "stance_reference_errors": sorted(stance_errors),
        "concept_alignment_candidates": concept_alignment_candidates,
        "parameterization_group_merges": parameterization_group_merges,
        "artifact_code_status": artifact_code_status,
        "calibration": {
            "prior_base_rate_status": "covered" if covered else "fallback",
            "source_quality_status": "vacuous",
            "fallback_to_default_base_rate": not covered,
        },
        },
        SourceFinalizeReportDocument,
        source=f"{source_branch_name(source_name)}:merge/finalize",
    )
    slug = normalize_source_slug(source_name)
    adds[f"merge/finalize/{slug}.yaml"] = yaml.safe_dump(
        report.to_payload(),
        sort_keys=False,
        allow_unicode=True,
    ).encode("utf-8")
    return repo.git.commit_batch(
        adds=adds,
        deletes=[],
        message=f"Finalize {slug}",
        branch=source_branch_name(source_name),
    )
