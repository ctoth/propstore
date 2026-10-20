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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import msgspec
from quire.charter_class import CharterDoc
from quire.family_transport import FamilyInstanceMap, FamilyReferenceImage
from quire.git_store import AmbiguousMergeBaseError
from quire.tree_merge import TreeMergeConflict, iter_merged_tree_entries

from propstore.families.claims import Claim
from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY
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
    from quire.artifacts import ArtifactHandle
    from quire.git_store import GitStore

    from propstore.repository import Repository

_CLAIM_STORAGE_ROOT = Claim.__charter__.family.storage_root()


@dataclass
class NonClaimMergeConflict(RuntimeError):
    """Competing ordinary changes or transported evidence cannot be combined.

    Claim divergence is held as rival arguments (non-commitment); a non-claim file
    (a concept, a context, a form) has no rival-alternative semantics. A change
    against an unchanged peer propagates; incompatible concurrent changes fail
    rather than selecting a side.
    """

    path: str
    family: str
    left_sha: str | None
    right_sha: str | None

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
    repo: Repository, git: GitStore, branch_a: str, left_sha: str, right_sha: str
) -> tuple[MergeClaim, ...]:
    """Read the merge-base claim set, or empty when the branches share no ancestor."""

    try:
        base_sha = git.merge_base(left_sha, right_sha)
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
    branch_commits: Mapping[str, str] | None = None,
) -> RepositoryMergeFramework:
    """Read per-branch claim sets out of storage and build the formal merge object.

    The storage-facing companion to the pure
    :func:`~propstore.merge.merge_classifier.build_merge_framework`: it resolves each
    branch tip, reads its claims, computes the merge-base claim set, and delegates the
    classification math unchanged. ``branch_commits`` supplies already captured
    tips for a write plan; all reads, including the merge base, use those commits.
    """

    git = repo.require_git()
    branch_names = (branch_a, branch_b, *additional_branches)
    commits: dict[str, str] = {}
    for name in branch_names:
        commit_sha = git.branch_sha(name) if branch_commits is None else branch_commits[name]
        if commit_sha is None:
            raise ValueError(f"Branch {name!r} does not exist")
        commits[name] = commit_sha
    claim_sets: dict[str, Sequence[MergeClaim]] = {}
    for name in branch_names:
        claim_sets[name] = _read_branch_merge_claims(repo, name, commits[name])
    base_claims = _read_base_merge_claims(repo, git, branch_a, commits[branch_a], commits[branch_b])
    return build_merge_framework(
        claim_sets,
        branch_a,
        branch_b,
        base_claims=base_claims,
        integrity_constraint=integrity_constraint,
        additional_branches=tuple(additional_branches),
    )


def _materialize_merge_arguments(
    repo: Repository,
    git: GitStore,
    merge: RepositoryMergeFramework,
    merged_entries: dict[str, str],
    target_branch: str,
    instances: dict[str, FamilyInstanceMap],
) -> tuple[Claim, ...]:
    """Write each surviving claim alternative as a blob into ``merged_entries``.

    Rival versions of one ``artifact_id`` are stored under distinct ids (each
    argument's ``assertion_id``) so they coexist in the tree — the merge does not
    pick a winner.
    """

    materialized_claims: list[Claim] = []
    artifact_counts = Counter(argument.artifact_id for argument in merge.arguments)
    for argument in merge.arguments:
        has_rivals = artifact_counts[argument.artifact_id] > 1
        storage_id = argument.assertion_id if has_rivals else argument.artifact_id
        materialized = msgspec.structs.replace(
            argument.claim.claim, claim_id=storage_id
        )
        prepared = repo.families.claim.prepare(
            storage_id, materialized, branch=target_branch
        )
        merged_entries[prepared.address.require_path()] = git.store_blob(
            prepared.content
        )
        materialized_claims.append(prepared.document)
        for branch in argument.branch_origins:
            instances[branch].assign("claim", argument.artifact_id, storage_id)
    return tuple(materialized_claims)


def _transport_family_occurrences(
    repo: Repository,
    git: GitStore,
    claims: tuple[Claim, ...],
    instances: dict[str, FamilyInstanceMap],
    merged_entries: dict[str, str],
    target_branch: str,
    parent_entries: Mapping[str, Mapping[str, str]],
) -> None:
    """Map real parent occurrences, keeping each parent's FK incidence.

    Only parent occurrences contributing the selected ordinary version enter
    transport. Equal selected parent bytes can still have distinct claim images;
    equal output bytes coalesce with commit-qualified witnesses retained.
    """
    records: dict[str, Sequence[CharterDoc]] = {"claim": claims}
    selected_entries = dict(merged_entries)
    for family in PROPSTORE_FAMILY_REGISTRY.families:
        if family.name == "claim" or family.identity_field is None:
            continue
        bound = repo.families.by_name(family.name)
        occurrences: list[tuple[ArtifactHandle[object, object, CharterDoc], CharterDoc]] = []
        for branch, instance in instances.items():
            handles = tuple(
                handle for handle in bound.iter_handles(commit=instance.source_commit)
                if parent_entries[branch][handle.address.require_path()]
                == selected_entries.get(handle.address.require_path())
            )
            documents = instance.transport_family(family, tuple(h.document for h in handles))
            occurrences.extend(zip(handles, documents, strict=True))
        outputs: dict[str, str] = {}
        prepared_records: dict[str, CharterDoc] = {}
        for handle, document in occurrences:
            if document is handle.document:
                path = handle.address.require_path()
                blob = selected_entries[path]
            else:
                prepared = bound.prepare(
                    family.ref_from_document(document),
                    document, branch=target_branch,
                )
                path = prepared.address.require_path()
                blob = git.store_blob(prepared.content)
                document = prepared.document
            previous = outputs.get(path)
            if previous is not None and previous != blob:
                raise NonClaimMergeConflict(path, family.name, previous, blob)
            outputs[path] = blob
            prepared_records[path] = document
        for handle, _ in occurrences:
            merged_entries.pop(handle.address.require_path(), None)
        merged_entries.update(outputs)
        records[family.name] = tuple(prepared_records.values())
    PROPSTORE_FAMILY_REGISTRY.validate_records(records)


def _derive_manifest_id(
    branch_a: str, branch_b: str, arguments: tuple[MergeManifestArgument, ...],
    reference_images: tuple[FamilyReferenceImage, ...],
) -> str:
    key = json.dumps(
        {
            "branch_a": branch_a,
            "branch_b": branch_b,
            "assertion_ids": sorted(argument.assertion_id for argument in arguments),
            "reference_images": msgspec.to_builtins(reference_images),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return f"ps:merge:{digest}"


def _build_manifest(
    merge: RepositoryMergeFramework, branch_a: str, branch_b: str,
    reference_images: tuple[FamilyReferenceImage, ...],
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
        for argument in sorted(
            merge.arguments, key=lambda argument: argument.assertion_id
        )
    )
    semantic_candidates = tuple(
        MergeManifestCandidate(assertion_ids=tuple(group))
        for group in merge.semantic_candidates
    )
    return MergeManifest(
        manifest_id=_derive_manifest_id(branch_a, branch_b, arguments, reference_images),
        branch_a=branch_a,
        branch_b=branch_b,
        arguments=arguments,
        semantic_candidates=semantic_candidates,
        reference_images=reference_images,
    )


@dataclass
class DivergentMergeTargetError(ValueError):
    """The observed target history is absent from both proposed parents."""

    target_branch: str
    target_sha: str
    left_sha: str
    right_sha: str

    def __str__(self) -> str:
        return (
            f"Merge target {self.target_branch!r} at {self.target_sha} is not an "
            f"ancestor of either parent ({self.left_sha}, {self.right_sha})"
        )


@dataclass(frozen=True)
class MergeCommitPlan:
    """Pinned, admitted inputs to a two-parent publication.

    Construct with :func:`plan_merge_commit`. Absence is represented by a None
    target SHA and remains an absence lease at publication, not permission to
    overwrite a branch that subsequently appears.
    """

    branch_a: str
    branch_b: str
    left_sha: str
    right_sha: str
    target_branch: str
    target_sha: str | None
    base_sha: str | None

    @property
    def target_admission(self) -> Literal["absent", "contained"]:
        return "absent" if self.target_sha is None else "contained"

    @property
    def branch_commits(self) -> dict[str, str]:
        return {self.branch_a: self.left_sha, self.branch_b: self.right_sha}

    @property
    def expected_heads(self) -> dict[str, str | None]:
        return {**self.branch_commits, self.target_branch: self.target_sha}

    def commit(self, repo: Repository, *, message: str = "") -> str:
        """Publish this exact plan, retaining Quire's expected-head CAS.

        Ordinary conflicts raise NonClaimMergeConflict; family/FK admission may
        also refuse the combined instance. A changed input or target raises
        Quire's HeadMismatchError. None of these failures advances the target.
        """
        git = repo.require_git()
        branch_a, branch_b = self.branch_a, self.branch_b
        target_branch = self.target_branch
        left_sha, right_sha = self.left_sha, self.right_sha
        merge = build_repository_merge_framework(
            repo, branch_a, branch_b, branch_commits=self.branch_commits
        )
        parent_entries = {
            branch: dict(git.iter_flat_tree_entries(commit))
            for branch, commit in ((branch_a, left_sha), (branch_b, right_sha))
        }
        base_entries = dict(git.iter_flat_tree_entries(self.base_sha)) if self.base_sha else {}
        base_ordinary, left_ordinary, right_ordinary = (
            {path: blob for path, blob in entries.items() if not _is_claim_path(path)}
            for entries in (base_entries, parent_entries[branch_a], parent_entries[branch_b])
        )
        try:
            merged_entries = dict(iter_merged_tree_entries(base_ordinary, left_ordinary, right_ordinary))
        except TreeMergeConflict as conflict:
            raise NonClaimMergeConflict(
                conflict.path, _family_for_path(conflict.path),
                conflict.left_sha, conflict.right_sha,
            ) from conflict
        instances = {
            branch: FamilyInstanceMap(commit, {
                family.name: repo.families.by_name(family.name).reference_index(commit=commit)
                for family in PROPSTORE_FAMILY_REGISTRY.families
                if family.identity_field is not None
            })
            for branch, commit in ((branch_a, left_sha), (branch_b, right_sha))
        }
        claims = _materialize_merge_arguments(
            repo, git, merge, merged_entries, target_branch, instances
        )
        _transport_family_occurrences(
            repo, git, claims, instances, merged_entries, target_branch, parent_entries
        )
        reference_images = tuple(sorted(
            {image for instance in instances.values() for image in instance.iter_images()},
            key=lambda image: (image.source_commit, image.family, image.source_id),
        ))
        manifest = _build_manifest(merge, branch_a, branch_b, reference_images)
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
            expected_heads=self.expected_heads,
        )


def plan_merge_commit(
    repo: Repository,
    branch_a: str,
    branch_b: str,
    *,
    target_branch: str | None = None,
) -> MergeCommitPlan:
    """Capture heads once and refuse an existing target outside both histories.

    Git's two-parent merge records the histories of the two tips. A target may
    advance to that commit only when its captured tip is reachable from a parent.
    This is graph reachability (git-merge-base --is-ancestor), not a timestamp or
    tree-equality test. Multiple best bases remain a separate typed refusal.
    """

    git = repo.require_git()
    if target_branch is None:
        target_branch = git.primary_branch_name()
    left_sha = git.branch_sha(branch_a)
    right_sha = left_sha if branch_a == branch_b else git.branch_sha(branch_b)
    if left_sha is None:
        raise ValueError(f"Branch {branch_a!r} does not exist")
    if right_sha is None:
        raise ValueError(f"Branch {branch_b!r} does not exist")

    target_sha = (
        left_sha if target_branch == branch_a else
        right_sha if target_branch == branch_b else git.branch_sha(target_branch)
    )
    if (
        target_sha is not None
        and target_sha not in (left_sha, right_sha)
        and target_sha not in git.ancestor_distances(left_sha)
        and target_sha not in git.ancestor_distances(right_sha)
    ):
        raise DivergentMergeTargetError(target_branch, target_sha, left_sha, right_sha)
    base_shas = tuple(git.iter_merge_bases(left_sha, right_sha))
    if len(base_shas) > 1:
        raise AmbiguousMergeBaseError(left_sha, right_sha, base_shas)
    return MergeCommitPlan(
        branch_a, branch_b, left_sha, right_sha, target_branch, target_sha,
        base_shas[0] if base_shas else None,
    )


def create_merge_commit(
    repo: Repository,
    branch_a: str,
    branch_b: str,
    *,
    message: str = "",
    target_branch: str | None = None,
) -> str:
    """Plan and publish a two-parent merge, refusing lost target history.

    DivergentMergeTargetError and Quire's AmbiguousMergeBaseError refuse unsafe
    planning before storage. Publication retains ordinary-conflict, family/FK,
    and exact-head CAS admission; failures never advance the target branch.
    """
    return plan_merge_commit(
        repo, branch_a, branch_b, target_branch=target_branch
    ).commit(repo, message=message)


__all__ = [
    "NonClaimMergeConflict",
    "DivergentMergeTargetError",
    "MergeCommitPlan",
    "build_repository_merge_framework",
    "create_merge_commit",
    "plan_merge_commit",
]
