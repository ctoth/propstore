"""The two-parent storage merge commit (Phase 9-2).

This wires the merge MATH (:mod:`propstore.merge.merge_classifier`, which operates
over plain per-branch claim sets) to storage: it reads the claim sets out of two
branch trees, builds the formal :class:`RepositoryMergeFramework`, materializes the
surviving rival claim alternatives plus a :class:`MergeManifest` record, and writes
a single two-parent git commit via quire's ``commit_flat_tree(parents=[left, right])``.

Non-commitment (CLAUDE.md) is load-bearing here: divergent versions of the same
``artifact_id`` are **not** collapsed into one winner. Each surviving rival is
materialized under a distinct storage id (its ``assertion_id``) so both land in the
merge tree, and the manifest records every argument. Resolution is a render-time
policy decision, never made here.

The git plumbing — building the tree, the two-parent commit, the CAS on the target
branch head — is quire's (``commit_flat_tree``); this module only computes the merged
entry set and the materialized blobs. The merge provenance rides on the commit /
manifest, never on claim identity.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

import msgspec

from propstore.families.claims import Claim
from propstore.families.merge_manifests import (
    MergeManifest,
    MergeManifestArgument,
    MergeManifestCandidate,
    MergeManifestWitness,
)
from propstore.merge.merge_classifier import (
    IntegrityConstraint,
    RepositoryMergeFramework,
    build_merge_framework,
)
from propstore.merge.merge_claims import MergeClaim

if TYPE_CHECKING:
    from quire.git_store import GitStore

    from propstore.repository import Repository

_CLAIM_STORAGE_ROOT = Claim.__charter__.family.storage_root()


@dataclass(frozen=True)
class NonClaimMergeConflict(RuntimeError):
    """A non-claim file diverged between the two branches and cannot be merged.

    Claim divergence is held as rival arguments (non-commitment); a non-claim file
    (a concept, a context, a form) that differs between the branches has no
    rival-alternative semantics, so the merge refuses rather than silently picking
    a side.
    """

    path: str
    family: str
    left_sha: str
    right_sha: str

    def __str__(self) -> str:
        return (
            f"non-claim merge conflict at {self.path!r} in family {self.family!r}: "
            f"{self.left_sha} != {self.right_sha}"
        )


def _family_for_path(path: str) -> str:
    return path.replace("\\", "/").split("/", 1)[0]


def _is_claim_path(path: str) -> bool:
    return path == _CLAIM_STORAGE_ROOT or path.startswith(f"{_CLAIM_STORAGE_ROOT}/")


def _read_branch_merge_claims(
    repo: Repository, branch: str, commit_sha: str
) -> list[MergeClaim]:
    """Read every authored claim at ``commit_sha`` as a branch-tagged merge claim.

    The rewrite ``Claim`` is provenance-free, so the merge-relevant source label is
    the branch the version came from; it is carried as the merge claim's ``paper``
    (the comparison source the conflict detector needs), never folded into identity.
    """

    merge_claims: list[MergeClaim] = []
    for handle in repo.families.claim.iter_handles(commit=commit_sha):
        document = handle.document
        if not isinstance(document, Claim):
            continue
        merge_claim = MergeClaim.from_claim(document, paper=branch)
        if merge_claim is not None:
            merge_claims.append(merge_claim)
    return merge_claims


def _read_base_merge_claims(
    repo: Repository, git: GitStore, branch_a: str, branch_b: str
) -> tuple[MergeClaim, ...]:
    """Read the merge-base claim set, or empty when the branches share no ancestor."""

    try:
        base_sha = git.merge_base(branch_a, branch_b)
    except ValueError:
        return ()
    return tuple(_read_branch_merge_claims(repo, branch_a, base_sha))


def build_repository_merge_framework(
    repo: Repository,
    branch_a: str,
    branch_b: str,
    *,
    integrity_constraint: IntegrityConstraint | None = None,
    additional_branches: Sequence[str] = (),
) -> RepositoryMergeFramework:
    """Read per-branch claim sets out of storage and build the formal merge object.

    The storage-facing companion to the pure
    :func:`~propstore.merge.merge_classifier.build_merge_framework`: it resolves each
    branch tip, reads its claims, computes the merge-base claim set, and delegates the
    classification math unchanged.
    """

    git = repo.require_git()
    branch_names = (branch_a, branch_b, *additional_branches)
    claim_sets: dict[str, Sequence[MergeClaim]] = {}
    for name in branch_names:
        commit_sha = git.branch_sha(name)
        if commit_sha is None:
            raise ValueError(f"Branch {name!r} does not exist")
        claim_sets[name] = _read_branch_merge_claims(repo, name, commit_sha)
    base_claims = _read_base_merge_claims(repo, git, branch_a, branch_b)
    return build_merge_framework(
        claim_sets,
        branch_a,
        branch_b,
        base_claims=base_claims,
        integrity_constraint=integrity_constraint,
        additional_branches=tuple(additional_branches),
    )


def _merge_non_claim_entries(
    left_entries: dict[str, str], right_entries: dict[str, str]
) -> dict[str, str]:
    """Union the two trees' non-claim files, refusing on a divergent shared file."""

    merged: dict[str, str] = {}
    for path in sorted(set(left_entries) | set(right_entries)):
        if _is_claim_path(path):
            continue
        left_blob = left_entries.get(path)
        right_blob = right_entries.get(path)
        if left_blob is not None and right_blob is not None:
            if left_blob != right_blob:
                raise NonClaimMergeConflict(
                    path=path,
                    family=_family_for_path(path),
                    left_sha=left_blob,
                    right_sha=right_blob,
                )
            merged[path] = left_blob
        elif left_blob is not None:
            merged[path] = left_blob
        elif right_blob is not None:
            merged[path] = right_blob
    return merged


def _materialize_merge_arguments(
    repo: Repository,
    git: GitStore,
    merge: RepositoryMergeFramework,
    merged_entries: dict[str, str],
    target_branch: str,
) -> None:
    """Write each surviving claim alternative as a blob into ``merged_entries``.

    Rival versions of one ``artifact_id`` are stored under distinct ids (each
    argument's ``assertion_id``) so they coexist in the tree — the merge does not
    pick a winner.
    """

    artifact_counts = Counter(argument.artifact_id for argument in merge.arguments)
    for argument in merge.arguments:
        has_rivals = artifact_counts[argument.artifact_id] > 1
        storage_id = argument.assertion_id if has_rivals else argument.artifact_id
        materialized = msgspec.structs.replace(argument.claim.claim, claim_id=storage_id)
        prepared = repo.families.claim.prepare(
            storage_id, materialized, branch=target_branch
        )
        merged_entries[prepared.address.require_path()] = git.store_blob(prepared.content)


def _derive_manifest_id(
    branch_a: str, branch_b: str, arguments: tuple[MergeManifestArgument, ...]
) -> str:
    key = json.dumps(
        {
            "branch_a": branch_a,
            "branch_b": branch_b,
            "assertion_ids": sorted(argument.assertion_id for argument in arguments),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return f"ps:merge:{digest}"


def _build_manifest(
    merge: RepositoryMergeFramework, branch_a: str, branch_b: str
) -> MergeManifest:
    arguments = tuple(
        MergeManifestArgument(
            assertion_id=argument.assertion_id,
            canonical_claim_id=argument.canonical_claim_id,
            artifact_id=argument.artifact_id,
            branch_origins=tuple(argument.branch_origins),
            materialized=True,
            logical_id=argument.logical_id,
            witness_basis=tuple(
                MergeManifestWitness(
                    source_artifact_id=witness.source_artifact_id,
                    source_paper=witness.source_paper,
                    source_page=witness.source_page,
                    branch_origin=witness.branch_origin,
                )
                for witness in argument.witness_basis
            ),
        )
        for argument in sorted(merge.arguments, key=lambda argument: argument.assertion_id)
    )
    semantic_candidates = tuple(
        MergeManifestCandidate(assertion_ids=tuple(group))
        for group in merge.semantic_candidates
    )
    return MergeManifest(
        manifest_id=_derive_manifest_id(branch_a, branch_b, arguments),
        branch_a=branch_a,
        branch_b=branch_b,
        arguments=arguments,
        semantic_candidates=semantic_candidates,
    )


def create_merge_commit(
    repo: Repository,
    branch_a: str,
    branch_b: str,
    *,
    message: str = "",
    target_branch: str | None = None,
) -> str:
    """Create a two-parent storage merge commit from the formal merge object.

    Reads the claim sets out of both branch trees, builds the merge framework,
    materializes the surviving rival claim alternatives plus a ``MergeManifest``, and
    commits the merged entry set with ``parents=[left, right]`` onto ``target_branch``
    (default: the primary branch). Returns the merge commit sha. Raises
    :class:`NonClaimMergeConflict` when a non-claim file diverged between the branches.
    """

    git = repo.require_git()
    if target_branch is None:
        target_branch = git.primary_branch_name()
    target_expected_head = git.branch_sha(target_branch)

    left_sha = git.branch_sha(branch_a)
    right_sha = git.branch_sha(branch_b)
    if left_sha is None:
        raise ValueError(f"Branch {branch_a!r} does not exist")
    if right_sha is None:
        raise ValueError(f"Branch {branch_b!r} does not exist")

    merge = build_repository_merge_framework(repo, branch_a, branch_b)

    merged_entries = _merge_non_claim_entries(
        dict(git.iter_flat_tree_entries(left_sha)),
        dict(git.iter_flat_tree_entries(right_sha)),
    )
    _materialize_merge_arguments(repo, git, merge, merged_entries, target_branch)

    manifest = _build_manifest(merge, branch_a, branch_b)
    prepared_manifest = repo.families.merge_manifest.prepare(
        manifest.manifest_id, manifest, branch=target_branch
    )
    merged_entries[prepared_manifest.address.require_path()] = git.store_blob(
        prepared_manifest.content
    )

    return git.commit_flat_tree(
        merged_entries,
        message or f"Merge {branch_a} and {branch_b}",
        parents=[left_sha, right_sha],
        branch=target_branch,
        expected_head=target_expected_head,
    )


__all__ = [
    "NonClaimMergeConflict",
    "build_repository_merge_framework",
    "create_merge_commit",
]
