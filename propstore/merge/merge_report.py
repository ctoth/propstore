"""Repository-facing summaries for merge frameworks."""
from __future__ import annotations

from collections import defaultdict

from propstore.merge.merge_classifier import RepositoryMergeFramework
from propstore.storage.merge_framework import enumerate_paf_completions
from propstore.storage.paf_queries import (
    credulously_accepted_arguments,
    skeptically_accepted_arguments,
)


def semantic_candidate_details(merge: RepositoryMergeFramework) -> list[dict]:
    argument_index = merge.argument_index()
    details: list[dict] = []
    for claim_ids in merge.semantic_candidates:
        arguments = [argument_index[claim_id] for claim_id in sorted(claim_ids)]
        details.append({
            "claim_ids": [argument.claim_id for argument in arguments],
            "logical_ids": [
                argument.logical_id
                for argument in arguments
                if isinstance(argument.logical_id, str) and argument.logical_id
            ],
            "artifact_ids": [argument.artifact_id for argument in arguments],
            "arguments": [
                {
                    "claim_id": argument.claim_id,
                    "logical_id": argument.logical_id,
                    "artifact_id": argument.artifact_id,
                    "branch_origins": list(argument.branch_origins),
                    "source_paper": argument.claim.provenance_payload().get("paper"),
                }
                for argument in arguments
            ],
        })
    return details


def summarize_merge_framework(
    merge: RepositoryMergeFramework,
    *,
    semantics: str = "grounded",
) -> dict:
    skeptical = sorted(skeptically_accepted_arguments(merge.framework, semantics=semantics))
    credulous = sorted(credulously_accepted_arguments(merge.framework, semantics=semantics))

    statuses = {}
    argument_details = []
    canonical_groups: dict[str, list[str]] = defaultdict(list)
    for argument in merge.arguments:
        detail = {
            "claim_id": argument.claim_id,
            "canonical_claim_id": argument.canonical_claim_id,
            "artifact_id": argument.artifact_id,
            "logical_id": argument.logical_id,
            "concept_id": argument.concept_id,
            "branch_origins": list(argument.branch_origins),
            "provenance": argument.claim.provenance_payload(),
            "skeptically_accepted": argument.claim_id in skeptical,
            "credulously_accepted": argument.claim_id in credulous,
        }
        statuses[argument.claim_id] = {
            "skeptically_accepted": detail["skeptically_accepted"],
            "credulously_accepted": detail["credulously_accepted"],
            "branch_origins": detail["branch_origins"],
            "canonical_claim_id": detail["canonical_claim_id"],
            "artifact_id": detail["artifact_id"],
            "logical_id": detail["logical_id"],
            "concept_id": detail["concept_id"],
        }
        argument_details.append(detail)
        canonical_groups[argument.canonical_claim_id].append(argument.claim_id)

    argument_details.sort(key=lambda detail: detail["claim_id"])
    canonical_groups_out = {
        canonical_id: sorted(claim_ids)
        for canonical_id, claim_ids in sorted(canonical_groups.items())
    }

    return {
        "surface": "formal_merge_report",
        "framework_type": "partial_argumentation_framework",
        "branch_a": merge.branch_a,
        "branch_b": merge.branch_b,
        "semantics": semantics,
        "arguments": [argument.claim_id for argument in merge.arguments],
        "attacks": [list(pair) for pair in sorted(merge.framework.attacks)],
        "ignorance": [list(pair) for pair in sorted(merge.framework.ignorance)],
        "non_attacks": [list(pair) for pair in sorted(merge.framework.non_attacks)],
        "relation_counts": {
            "attack": len(merge.framework.attacks),
            "ignorance": len(merge.framework.ignorance),
            "non_attack": len(merge.framework.non_attacks),
        },
        "completion_count": len(enumerate_paf_completions(merge.framework)),
        "skeptical": skeptical,
        "credulous": credulous,
        "semantic_candidates": [list(group) for group in merge.semantic_candidates],
        "semantic_candidate_details": semantic_candidate_details(merge),
        "canonical_groups": canonical_groups_out,
        "argument_details": argument_details,
        "statuses": statuses,
    }


__all__ = ["semantic_candidate_details", "summarize_merge_framework"]
