"""Merge commit creation for propstore knowledge repositories."""
from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from propstore.families.registry import ClaimsFileRef, MergeManifestRef
from propstore.merge.merge_classifier import MergeArgument
from propstore.merge.merge_classifier import build_merge_framework
from propstore.merge.merge_report import semantic_candidate_details

if TYPE_CHECKING:
    from propstore.storage.snapshot import RepositorySnapshot


@dataclass(frozen=True)
class NonClaimMergeConflict(RuntimeError):
    path: str
    family: str
    left_sha: str
    right_sha: str

    def __str__(self) -> str:
        return (
            f"non-claim merge conflict at {self.path!r} in family {self.family!r}: "
            f"{self.left_sha} != {self.right_sha}"
        )


def _safe_ref_part(value: str) -> str:
    safe = "".join(character if character.isalnum() else "_" for character in value)
    return safe.strip("_") or "branch"


def _claims_ref_for_argument(argument: MergeArgument, *, has_rivals: bool) -> ClaimsFileRef:
    """Return the merge claim file ref.

    Clark et al. micropublications require rival assertions to remain separately
    citable. Branch-keyed files keep those rival bodies present without
    collapsing them into one canonical storage identity.
    """
    source_paper = _source_paper(argument) or "unknown"
    if not has_rivals:
        return ClaimsFileRef(f"merged__{_safe_ref_part(source_paper)}")
    origin_key = "__".join(_safe_ref_part(origin) for origin in argument.branch_origins)
    paper_key = _safe_ref_part(source_paper)
    return ClaimsFileRef(f"merged__{paper_key}__{origin_key or 'unknown'}")


def _materialized_claim_payload(argument: MergeArgument, *, has_rivals: bool) -> dict:
    payload = argument.claim.to_payload()
    provenance = payload.get("provenance")
    if isinstance(provenance, dict) and len(argument.branch_origins) == 1:
        provenance.setdefault("branch_origin", argument.branch_origins[0])
    return payload


def _source_paper(argument: MergeArgument) -> str | None:
    paper = argument.claim.provenance_payload().get("paper")
    if isinstance(paper, str) and paper:
        return paper
    return None


def _family_for_path(path: str) -> str:
    return path.replace("\\", "/").split("/", 1)[0]


def create_merge_commit(
    snapshot: RepositorySnapshot,
    branch_a: str,
    branch_b: str,
    message: str = "",
    *,
    target_branch: str | None = None,
) -> str:
    """Create a two-parent merge commit from the formal merge object."""
    kr = snapshot.git
    families = snapshot.repo.families
    if target_branch is None:
        target_branch = snapshot.primary_branch_name()
    target_expected_head = snapshot.branch_head(target_branch)
    merge = build_merge_framework(snapshot, branch_a, branch_b)

    left_sha = snapshot.branch_head(branch_a)
    right_sha = snapshot.branch_head(branch_b)
    if left_sha is None:
        raise ValueError(f"Branch {branch_a!r} does not exist")
    if right_sha is None:
        raise ValueError(f"Branch {branch_b!r} does not exist")

    left_entries = kr.flat_tree_entries(left_sha)
    right_entries = kr.flat_tree_entries(right_sha)

    merged_entries: dict[str, str] = {}
    for path in sorted(set(left_entries) | set(right_entries)):
        if path.startswith("claims/"):
            continue
        left_sha_for_path = left_entries.get(path)
        right_sha_for_path = right_entries.get(path)
        if left_sha_for_path is not None and right_sha_for_path is not None:
            if left_sha_for_path != right_sha_for_path:
                raise NonClaimMergeConflict(
                    path=path,
                    family=_family_for_path(path),
                    left_sha=left_sha_for_path,
                    right_sha=right_sha_for_path,
                )
            merged_entries[path] = left_sha_for_path
            continue
        if left_sha_for_path is not None:
            merged_entries[path] = left_sha_for_path
            continue
        if right_sha_for_path is not None:
            merged_entries[path] = right_sha_for_path

    sorted_arguments = sorted(merge.arguments, key=lambda argument: argument.assertion_id)
    artifact_counts = Counter(argument.artifact_id for argument in sorted_arguments)
    claim_payloads_by_ref: dict[ClaimsFileRef, list[dict]] = {}
    for argument in sorted_arguments:
        has_rivals = artifact_counts[argument.artifact_id] > 1
        claims_ref = _claims_ref_for_argument(argument, has_rivals=has_rivals)
        claim_payloads_by_ref.setdefault(claims_ref, []).append(
            _materialized_claim_payload(argument, has_rivals=has_rivals)
        )
    claim_paths = [path for path in merged_entries if path.startswith("claims/")]
    for path in claim_paths:
        del merged_entries[path]

    manifest_payload = {
        "merge": {
            "branch_a": branch_a,
            "branch_b": branch_b,
            "arguments": [
                {
                    "assertion_id": argument.assertion_id,
                    "canonical_claim_id": argument.canonical_claim_id,
                    "artifact_id": argument.artifact_id,
                    "logical_id": argument.logical_id,
                    "branch_origins": list(argument.branch_origins),
                    "witness_basis": [
                        witness.to_payload()
                        for witness in argument.witness_basis
                    ],
                    "materialized": True,
                }
                for argument in sorted_arguments
            ],
            "semantic_candidates": [list(group) for group in merge.semantic_candidates],
            "semantic_candidate_details": semantic_candidate_details(merge),
        }
    }
    manifest_ref = MergeManifestRef()
    manifest_document = families.merge_manifests.coerce(
        manifest_payload,
        source=families.merge_manifests.address(manifest_ref).require_path(),
    )

    prepared_claims = []
    for claims_ref, claims in sorted(
        claim_payloads_by_ref.items(),
        key=lambda item: item[0].name,
    ):
        claims_payload = {
            "source": {
                "paper": _source_paper_for_payloads(claims),
                "extraction_model": "merge",
                "extraction_date": time.strftime("%Y-%m-%d"),
            },
            "claims": claims,
        }
        claims_document = families.claims.coerce(
            claims_payload,
            source=families.claims.address(claims_ref).require_path(),
        )
        prepared_claims.append(
            families.claims.prepare(
                claims_ref,
                claims_document,
                branch=target_branch,
            )
        )
    prepared_manifest = families.merge_manifests.prepare(
        manifest_ref,
        manifest_document,
        branch=target_branch,
    )

    for prepared in (*prepared_claims, prepared_manifest):
        merged_entries[prepared.address.require_path()] = kr.store_blob(prepared.content)

    return kr.commit_flat_tree(
        merged_entries,
        message or f"Merge {branch_a} and {branch_b}",
        parents=[left_sha, right_sha],
        branch=target_branch,
        expected_head=target_expected_head,
    )


def _source_paper_for_payloads(claims: list[dict]) -> str:
    papers = sorted(
        {
            provenance["paper"]
            for claim in claims
            if isinstance((provenance := claim.get("provenance")), dict)
            and isinstance(provenance.get("paper"), str)
            and provenance.get("paper")
        }
    )
    if not papers:
        return "unknown"
    if len(papers) == 1:
        return papers[0]
    return "+".join(papers)
