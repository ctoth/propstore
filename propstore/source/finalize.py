from __future__ import annotations

from typing import Any

import yaml

from propstore.artifact_codes import attach_source_artifact_codes
from propstore.cli.repository import Repository
from propstore.source_calibration import derive_source_trust

from .claims import load_primary_branch_claim_index, load_source_claim_index
from .common import load_branch_yaml, load_source_document, normalize_source_slug, source_branch_name, source_tag_uri
from .registry import preview_source_parameterization_group_merges


def finalize_source_branch(repo: Repository, source_name: str) -> str:
    source_doc = derive_source_trust(repo, load_source_document(repo, source_name))
    claims_doc = load_branch_yaml(repo, source_name, "claims.yaml") or {}
    justifications_doc = load_branch_yaml(repo, source_name, "justifications.yaml") or {}
    stances_doc = load_branch_yaml(repo, source_name, "stances.yaml") or {}
    concepts_doc = load_branch_yaml(repo, source_name, "concepts.yaml") or {}

    local_to_artifact, logical_to_artifact, local_artifact_ids = load_source_claim_index(repo, source_name)
    primary_logical_to_artifact, primary_artifact_ids = load_primary_branch_claim_index(repo)

    claims = claims_doc.get("claims", []) if isinstance(claims_doc, dict) else []
    claim_errors: list[str] = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        if not isinstance(claim.get("artifact_id"), str):
            claim_errors.append(str(claim.get("id") or "?"))

    justification_errors: list[str] = []
    for justification in justifications_doc.get("justifications", []) or []:
        if not isinstance(justification, dict):
            continue
        conclusion = justification.get("conclusion")
        if not isinstance(conclusion, str) or conclusion not in local_artifact_ids:
            justification_errors.append(str(conclusion))
        for premise in justification.get("premises") or []:
            if not isinstance(premise, str) or premise not in local_artifact_ids:
                justification_errors.append(str(premise))

    stance_errors: list[str] = []
    for stance in stances_doc.get("stances", []) or []:
        if not isinstance(stance, dict):
            continue
        source_claim = stance.get("source_claim")
        if not isinstance(source_claim, str) or source_claim not in local_artifact_ids:
            stance_errors.append(str(source_claim))
        target = stance.get("target")
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
            f"align:{normalize_source_slug(str(entry.get('proposed_name') or entry.get('local_name') or 'concept'))}"
            for entry in concepts_doc.get("concepts", []) or []
            if isinstance(entry, dict) and not isinstance(entry.get("registry_match"), dict)
        }
    )
    parameterization_group_merges = preview_source_parameterization_group_merges(repo, concepts_doc)

    trust = source_doc.get("trust") if isinstance(source_doc.get("trust"), dict) else {}
    derived_from = trust.get("derived_from") if isinstance(trust.get("derived_from"), list) else []
    covered = bool(derived_from)
    artifact_code_status = "incomplete"
    adds: dict[str, bytes] = {}
    if not claim_errors and not justification_errors and not stance_errors:
        source_doc, claims_doc, justifications_doc, stances_doc = attach_source_artifact_codes(
            source_doc,
            claims_doc,
            justifications_doc,
            stances_doc,
        )
        adds["source.yaml"] = yaml.safe_dump(source_doc, sort_keys=False, allow_unicode=True).encode("utf-8")
        if claims_doc.get("claims"):
            adds["claims.yaml"] = yaml.safe_dump(claims_doc, sort_keys=False, allow_unicode=True).encode("utf-8")
        if justifications_doc.get("justifications"):
            adds["justifications.yaml"] = yaml.safe_dump(
                justifications_doc,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        if stances_doc.get("stances"):
            adds["stances.yaml"] = yaml.safe_dump(stances_doc, sort_keys=False, allow_unicode=True).encode("utf-8")
        artifact_code_status = "complete"

    report: dict[str, Any] = {
        "kind": "source_finalize_report",
        "source": str(source_doc.get("id") or source_tag_uri(repo, source_name)),
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
    }
    slug = normalize_source_slug(source_name)
    adds[f"merge/finalize/{slug}.yaml"] = yaml.safe_dump(
        report,
        sort_keys=False,
        allow_unicode=True,
    ).encode("utf-8")
    return repo.git.commit_batch(
        adds=adds,
        deletes=[],
        message=f"Finalize {slug}",
        branch=source_branch_name(source_name),
    )
