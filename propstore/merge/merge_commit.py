"""Merge commit creation for propstore knowledge repositories."""
from __future__ import annotations

import time
from collections import Counter
from typing import TYPE_CHECKING

from propstore.families.identity.claims import compute_claim_version_id
from propstore.families.registry import ClaimsFileRef, MergeManifestRef
from propstore.merge.merge_classifier import MergeArgument
from propstore.merge.merge_classifier import build_merge_framework
from propstore.merge.merge_report import semantic_candidate_details

if TYPE_CHECKING:
    from propstore.storage.snapshot import RepositorySnapshot


def _safe_ref_part(value: str) -> str:
    safe = "".join(character if character.isalnum() else "_" for character in value)
    return safe.strip("_") or "branch"


def _claims_ref_for_argument(argument: MergeArgument, *, has_rivals: bool) -> ClaimsFileRef:
    """Return the merge claim file ref.

    Clark et al. micropublications require rival assertions to remain separately
    citable. Branch-keyed files keep those rival bodies present without
    collapsing them into one canonical storage identity.
    """
    if not has_rivals:
        return ClaimsFileRef("merged")
    origin_key = "__".join(_safe_ref_part(origin) for origin in argument.branch_origins)
    return ClaimsFileRef(f"merged__{origin_key or 'unknown'}")


def _materialized_claim_payload(argument: MergeArgument, *, has_rivals: bool) -> dict:
    payload = argument.claim.to_payload()
    if has_rivals:
        # Clark et al. micropublications: each rival needs its own materialized
        # identity; the manifest keeps the shared canonical artifact_id.
        payload["artifact_id"] = argument.assertion_id
        provenance = payload.get("provenance")
        if isinstance(provenance, dict):
            provenance.pop("branch_origin", None)
        payload["version_id"] = compute_claim_version_id(payload)
    return payload


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
    for path, sha in right_entries.items():
        if not path.startswith("claims/"):
            merged_entries[path] = sha
    for path, sha in left_entries.items():
        if not path.startswith("claims/"):
            merged_entries[path] = sha

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
                "paper": "merged",
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
