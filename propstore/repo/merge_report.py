"""Repo-facing summaries for merge frameworks."""
from __future__ import annotations

from propstore.repo.merge_classifier import RepoMergeFramework
from propstore.repo.merge_framework import enumerate_paf_completions
from propstore.repo.paf_queries import (
    credulously_accepted_arguments,
    skeptically_accepted_arguments,
)


def summarize_merge_framework(
    merge: RepoMergeFramework,
    *,
    semantics: str = "grounded",
) -> dict:
    skeptical = sorted(skeptically_accepted_arguments(merge.framework, semantics=semantics))
    credulous = sorted(credulously_accepted_arguments(merge.framework, semantics=semantics))

    statuses = {}
    for argument in merge.arguments:
        statuses[argument.claim_id] = {
            "skeptically_accepted": argument.claim_id in skeptical,
            "credulously_accepted": argument.claim_id in credulous,
            "branch_origins": list(argument.branch_origins),
            "canonical_claim_id": argument.canonical_claim_id,
            "concept_id": argument.concept_id,
        }

    return {
        "branch_a": merge.branch_a,
        "branch_b": merge.branch_b,
        "semantics": semantics,
        "arguments": [argument.claim_id for argument in merge.arguments],
        "attacks": [list(pair) for pair in sorted(merge.framework.attacks)],
        "ignorance": [list(pair) for pair in sorted(merge.framework.ignorance)],
        "non_attacks": [list(pair) for pair in sorted(merge.framework.non_attacks)],
        "completion_count": len(enumerate_paf_completions(merge.framework)),
        "skeptical": skeptical,
        "credulous": credulous,
        "statuses": statuses,
    }


__all__ = ["summarize_merge_framework"]
