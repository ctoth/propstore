"""Merge commit creation for propstore knowledge repositories.

Creates two-parent commits that preserve both sides of any conflict
with provenance annotation. This is the storage representation of
IC merging (Konieczny & Pino Perez 2002): both source belief bases
are preserved as parents.

The non-commitment principle governs: no conflict is resolved in storage.
Both sides persist with branch_origin provenance.
"""
from __future__ import annotations

import copy
import time
from typing import TYPE_CHECKING

import yaml
from dulwich.objects import Blob, Commit

from propstore.repo.branch import branch_head
from propstore.repo.git_backend import _DEFAULT_AUTHOR, _ref_get
from propstore.repo.merge_classifier import (
    MergeClassification,
    MergeItem,
    classify_merge,
)

if TYPE_CHECKING:
    from propstore.repo.git_backend import KnowledgeRepo


def _annotate_provenance(claim: dict, branch_name: str) -> dict:
    """Add branch_origin to a claim's provenance dict."""
    claim = copy.deepcopy(claim)
    prov = claim.get("provenance", {})
    prov["branch_origin"] = branch_name
    claim["provenance"] = prov
    return claim


def _disambiguate_id(claim_id: str, suffix: str) -> str:
    """Create a disambiguated claim ID for conflicting claims.

    Appends a branch-derived suffix so both versions can coexist
    in the same claim file without ID collision.
    """
    # Sanitize suffix: replace / with _ for branch names like paper/test
    safe_suffix = suffix.replace("/", "_").replace("-", "_")
    return f"{claim_id}__{safe_suffix}"


def create_merge_commit(
    kr: KnowledgeRepo,
    branch_a: str,
    branch_b: str,
    message: str = "",
    *,
    target_branch: str = "master",
) -> str:
    """Create a merge commit with two parents.

    Classifies all claims, then builds a merged tree containing
    both sides of any conflicts with provenance annotation.
    Returns the merge commit SHA.

    Per Konieczny & Pino Perez 2002: the merge operator takes multiple
    belief bases as input; the two-parent commit preserves this
    multi-source provenance.
    """
    from propstore.tree_reader import GitTreeReader
    from propstore.validate_claims import load_claim_files

    # Classify all claims
    items = classify_merge(kr, branch_a, branch_b)

    # Load the full trees from both branch tips
    left_sha = branch_head(kr, branch_a)
    right_sha = branch_head(kr, branch_b)

    left_entries: dict[str, bytes] = {}
    left_tree = kr._get_tree(left_sha)
    if left_tree is not None:
        kr._flatten_tree(left_tree, "", left_entries)

    right_entries: dict[str, bytes] = {}
    right_tree = kr._get_tree(right_sha)
    if right_tree is not None:
        kr._flatten_tree(right_tree, "", right_entries)

    # Merge non-claim files: take all from both sides (left wins on conflict)
    merged_entries: dict[str, bytes] = {}
    for path, sha in right_entries.items():
        if not path.startswith("claims/"):
            merged_entries[path] = sha
    for path, sha in left_entries.items():
        if not path.startswith("claims/"):
            merged_entries[path] = sha

    # Build merged claim set from classification results.
    # This replaces raw file copying — we rebuild claims from the
    # classified items so that conflict/phi_node claims get provenance
    # annotation and don't appear un-annotated.
    merged_claims: list[dict] = []
    for item in items:
        if item.classification == MergeClassification.IDENTICAL:
            # Use whichever version exists (they're equal)
            claim = item.left_value or item.right_value or item.base_value
            if claim is not None:
                merged_claims.append(copy.deepcopy(claim))
        elif item.classification in (MergeClassification.NOVEL_LEFT, MergeClassification.COMPATIBLE):
            # Include claim from whichever side has it
            if item.left_value is not None:
                merged_claims.append(copy.deepcopy(item.left_value))
            if item.right_value is not None and item.left_value is None:
                merged_claims.append(copy.deepcopy(item.right_value))
            # If both sides have it (COMPATIBLE with both present), include both
            if (item.classification == MergeClassification.COMPATIBLE
                    and item.left_value is not None and item.right_value is not None):
                merged_claims.append(copy.deepcopy(item.right_value))
        elif item.classification == MergeClassification.NOVEL_RIGHT:
            if item.right_value is not None:
                merged_claims.append(copy.deepcopy(item.right_value))
        elif item.classification in (MergeClassification.CONFLICT, MergeClassification.PHI_NODE):
            # Both versions preserved with branch_origin provenance
            if item.left_value is not None:
                left_annotated = _annotate_provenance(item.left_value, branch_a)
                left_annotated["id"] = _disambiguate_id(item.claim_id, branch_a)
                merged_claims.append(left_annotated)
            if item.right_value is not None:
                right_annotated = _annotate_provenance(item.right_value, branch_b)
                right_annotated["id"] = _disambiguate_id(item.claim_id, branch_b)
                merged_claims.append(right_annotated)

    # Serialize all merged claims into a single claim file
    if merged_claims:
        doc = {
            "source": {
                "paper": "merged",
                "extraction_model": "merge",
                "extraction_date": time.strftime("%Y-%m-%d"),
            },
            "claims": merged_claims,
        }
        content = yaml.dump(doc, sort_keys=False).encode("utf-8")
        blob = Blob.from_string(content)
        kr._repo.object_store.add_object(blob)
        # Remove all old claim files and replace with single merged file
        claim_paths = [p for p in merged_entries if p.startswith("claims/")]
        for p in claim_paths:
            del merged_entries[p]
        merged_entries["claims/merged.yaml"] = blob.id
    else:
        # No claims — remove any claim files from the tree
        claim_paths = [p for p in merged_entries if p.startswith("claims/")]
        for p in claim_paths:
            del merged_entries[p]

    # Build the tree and create the two-parent commit
    store = kr._repo.object_store
    root_tree = kr._build_tree_from_flat(merged_entries, store)

    commit = Commit()
    commit.tree = root_tree.id
    commit.author = _DEFAULT_AUTHOR
    commit.committer = _DEFAULT_AUTHOR
    commit.encoding = b"UTF-8"

    if not message:
        message = f"Merge {branch_a} and {branch_b}"
    commit.message = message.encode("utf-8")

    now = int(time.time())
    commit.commit_time = now
    commit.author_time = now
    commit.commit_timezone = 0
    commit.author_timezone = 0

    # Two parents: left tip, right tip
    commit.parents = [left_sha.encode("ascii"), right_sha.encode("ascii")]
    store.add_object(commit)

    # Update the target branch ref
    target_ref = f"refs/heads/{target_branch}".encode()
    kr._repo.refs[target_ref] = commit.id

    return commit.id.decode("ascii")
