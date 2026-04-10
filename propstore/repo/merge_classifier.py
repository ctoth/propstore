"""Direct repo emission of a formal merge object.

The repository layer no longer emits claim-bucket classifications as its
public merge result. Instead it produces a provenance-bearing partial
argumentation framework over the claim alternatives that survive the merge.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from itertools import product
from typing import TYPE_CHECKING, Any

from propstore.repo.merge_claims import MergeClaim
from propstore.repo.branch import branch_head, merge_base
from propstore.repo.merge_framework import PartialArgumentationFramework

if TYPE_CHECKING:
    from propstore.repo.git_backend import KnowledgeRepo


class _DiffKind(Enum):
    COMPATIBLE = "compatible"
    CONFLICT = "conflict"
    PHI_NODE = "phi_node"


@dataclass(frozen=True)
class _IndexedClaim:
    claim: MergeClaim
    artifact_id: str
    logical_ids: tuple[str, ...]
    primary_logical_id: str | None
    concept_id: str


@dataclass(frozen=True)
class MergeArgument:
    """A claim alternative emitted by the repository merge boundary."""

    claim_id: str
    canonical_claim_id: str
    artifact_id: str
    logical_id: str | None
    concept_id: str
    claim: MergeClaim
    branch_origins: tuple[str, ...]


@dataclass(frozen=True)
class RepoMergeFramework:
    """Repository-facing merge object with provenance and formal semantics."""

    branch_a: str
    branch_b: str
    arguments: tuple[MergeArgument, ...]
    framework: PartialArgumentationFramework
    semantic_candidates: tuple[tuple[str, ...], ...] = ()

    def argument_index(self) -> dict[str, MergeArgument]:
        return {argument.claim_id: argument for argument in self.arguments}


def _annotate_provenance(claim: MergeClaim, branch_name: str) -> MergeClaim:
    return MergeClaim(document=claim.document, branch_origin=branch_name)


def _claim_artifact_id(claim: MergeClaim) -> str | None:
    return claim.artifact_id


def _claim_logical_ids(claim: MergeClaim) -> tuple[str, ...]:
    return tuple(sorted(claim.logical_ids))


def _disambiguate_id(claim_id: str, suffix: str) -> str:
    safe_suffix = suffix.replace("/", "_").replace("-", "_")
    return f"{claim_id}__{safe_suffix}"


def _extract_concept(claim: MergeClaim) -> str:
    return claim.concept_id


def _indexed_claim(claim: MergeClaim) -> _IndexedClaim | None:
    artifact_id = _claim_artifact_id(claim)
    if artifact_id is None:
        return None
    return _IndexedClaim(
        claim=claim,
        artifact_id=artifact_id,
        logical_ids=_claim_logical_ids(claim),
        primary_logical_id=claim.primary_logical_id,
        concept_id=_extract_concept(claim),
    )


def _claim_semantic_key(claim: MergeClaim) -> dict[str, Any]:
    skip = {"artifact_id", "version_id", "provenance"}
    payload = claim.to_payload(include_branch_origin=False)
    return {key: value for key, value in payload.items() if key not in skip}


def _claims_equal(a: MergeClaim, b: MergeClaim) -> bool:
    return _claim_semantic_key(a) == _claim_semantic_key(b)


def _claim_candidate_key(claim: MergeClaim) -> dict[str, Any]:
    skip = {"id", "artifact_id", "version_id", "provenance", "logical_ids"}
    payload = claim.to_payload(include_branch_origin=False)
    return {key: value for key, value in payload.items() if key not in skip}


def _index_claims(claim_files) -> dict[str, _IndexedClaim]:
    index: dict[str, _IndexedClaim] = {}
    for claim_file in claim_files:
        for claim in claim_file.claims:
            merge_claim = MergeClaim.from_document(claim)
            if merge_claim is None:
                continue
            indexed = _indexed_claim(merge_claim)
            if indexed is not None:
                index[indexed.artifact_id] = indexed
    return index


def _canonical_claim_groups(
    *indexes: dict[str, _IndexedClaim],
) -> dict[str, str]:
    parent: dict[str, str] = {}

    def _find(artifact_id: str) -> str:
        root = parent.setdefault(artifact_id, artifact_id)
        while parent[root] != root:
            parent[root] = parent[parent[root]]
            root = parent[root]
        return root

    def _union(left: str, right: str) -> None:
        left_root = _find(left)
        right_root = _find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    logical_to_artifacts: dict[str, set[str]] = {}
    all_artifacts: set[str] = set()
    for index in indexes:
        for artifact_id, claim in index.items():
            all_artifacts.add(artifact_id)
            parent.setdefault(artifact_id, artifact_id)
            for logical_id in claim.logical_ids:
                logical_to_artifacts.setdefault(logical_id, set()).add(artifact_id)

    for artifact_ids in logical_to_artifacts.values():
        ordered = sorted(artifact_ids)
        if not ordered:
            continue
        first = ordered[0]
        for other in ordered[1:]:
            _union(first, other)

    component_members: dict[str, list[str]] = {}
    for artifact_id in all_artifacts:
        component_members.setdefault(_find(artifact_id), []).append(artifact_id)

    component_label: dict[str, str] = {}
    for root, artifact_ids in component_members.items():
        logical_candidates = sorted(
            {
                logical_id
                for artifact_id in artifact_ids
                for index in indexes
                if artifact_id in index
                for logical_id in index[artifact_id].logical_ids
            }
        )
        component_label[root] = logical_candidates[0] if logical_candidates else sorted(artifact_ids)[0]

    return {
        artifact_id: component_label[_find(artifact_id)]
        for artifact_id in all_artifacts
    }


def _classify_pair(
    left_claim: MergeClaim,
    right_claim: MergeClaim,
) -> _DiffKind:
    """Classify disagreement between two concrete claim alternatives."""
    from propstore.conflict_detector import ConflictClass, detect_conflicts
    from propstore.loaded import LoadedEntry

    comparison_source = (
        left_claim.provenance_payload().get("paper")
    )
    if not isinstance(comparison_source, str) or not comparison_source:
        comparison_source = (
            right_claim.provenance_payload().get("paper")
        )
    if not isinstance(comparison_source, str) or not comparison_source:
        comparison_source = "merge_comparison"

    left_file = LoadedEntry(
        filename="_left",
        source_path=None,
        data={
            "source": {
                "paper": comparison_source,
                "extraction_model": "merge",
                "extraction_date": "2026-01-01",
            },
            "claims": [left_claim.to_payload(include_branch_origin=False)],
        },
    )
    right_file = LoadedEntry(
        filename="_right",
        source_path=None,
        data={
            "source": {
                "paper": comparison_source,
                "extraction_model": "merge",
                "extraction_date": "2026-01-01",
            },
            "claims": [right_claim.to_payload(include_branch_origin=False)],
        },
    )

    try:
        records = detect_conflicts([left_file, right_file], concept_registry={})
    except Exception as exc:
        from propstore.z3_conditions import Z3TranslationError

        if isinstance(exc, Z3TranslationError):
            left_conditions = sorted(left_claim.document.conditions)
            right_conditions = sorted(right_claim.document.conditions)
            if left_conditions != right_conditions:
                return _DiffKind.PHI_NODE
        raise

    for record in records:
        if record.warning_class in (
            ConflictClass.CONFLICT,
            ConflictClass.OVERLAP,
            ConflictClass.PARAM_CONFLICT,
        ):
            return _DiffKind.CONFLICT

    for record in records:
        if record.warning_class in (
            ConflictClass.PHI_NODE,
            ConflictClass.CONTEXT_PHI_NODE,
        ):
            return _DiffKind.PHI_NODE

    if _extract_concept(left_claim) != _extract_concept(right_claim):
        return _DiffKind.COMPATIBLE
    return _DiffKind.CONFLICT


def _emit_argument(
    emitted: list[MergeArgument],
    *,
    claim: _IndexedClaim,
    canonical_claim_id: str,
    concept_id: str,
    branch_origins: tuple[str, ...],
    emitted_claim_id: str | None = None,
    annotate_branch_origin: str | None = None,
) -> str:
    merged_claim = claim.claim
    claim_id = emitted_claim_id or claim.artifact_id
    if annotate_branch_origin is not None:
        merged_claim = _annotate_provenance(merged_claim, annotate_branch_origin)
    emitted.append(
        MergeArgument(
            claim_id=claim_id,
            canonical_claim_id=canonical_claim_id,
            artifact_id=claim.artifact_id,
            logical_id=claim.primary_logical_id,
            concept_id=concept_id,
            claim=merged_claim,
            branch_origins=branch_origins,
        )
    )
    return claim_id


def build_merge_framework(
    kr: KnowledgeRepo,
    branch_a: str,
    branch_b: str,
) -> RepoMergeFramework:
    """Build the direct repository merge object for two branches."""
    from propstore.validate_claims import load_claim_files

    base_sha = merge_base(kr, branch_a, branch_b)
    left_sha = branch_head(kr, branch_a)
    right_sha = branch_head(kr, branch_b)

    base_claims_root = kr.tree(commit=base_sha) / "claims"
    left_claims_root = kr.tree(commit=left_sha) / "claims"
    right_claims_root = kr.tree(commit=right_sha) / "claims"

    base_idx = _index_claims(load_claim_files(base_claims_root))
    left_idx = _index_claims(load_claim_files(left_claims_root))
    right_idx = _index_claims(load_claim_files(right_claims_root))
    canonical_groups = _canonical_claim_groups(base_idx, left_idx, right_idx)

    all_ids = sorted(set(base_idx) | set(left_idx) | set(right_idx))
    emitted: list[MergeArgument] = []
    attacks: set[tuple[str, str]] = set()
    ignorance: set[tuple[str, str]] = set()

    for artifact_id in all_ids:
        canonical_claim_id = canonical_groups.get(artifact_id, artifact_id)
        base_claim = base_idx.get(artifact_id)
        left_claim = left_idx.get(artifact_id)
        right_claim = right_idx.get(artifact_id)

        concept_id = ""
        for candidate in (left_claim, right_claim, base_claim):
            if candidate is not None:
                concept_id = candidate.concept_id
                break

        in_left = left_claim is not None
        in_right = right_claim is not None
        in_base = base_claim is not None

        if in_left and in_right:
            if _claims_equal(left_claim.claim, right_claim.claim):
                _emit_argument(
                    emitted,
                    claim=left_claim,
                    canonical_claim_id=canonical_claim_id,
                    concept_id=concept_id,
                    branch_origins=(branch_a, branch_b),
                )
                continue

            if in_base and _claims_equal(left_claim.claim, base_claim.claim):
                _emit_argument(
                    emitted,
                    claim=right_claim,
                    canonical_claim_id=canonical_claim_id,
                    concept_id=concept_id,
                    branch_origins=(branch_b,),
                )
                continue

            if in_base and _claims_equal(right_claim.claim, base_claim.claim):
                _emit_argument(
                    emitted,
                    claim=left_claim,
                    canonical_claim_id=canonical_claim_id,
                    concept_id=concept_id,
                    branch_origins=(branch_a,),
                )
                continue

            diff_kind = _classify_pair(left_claim.claim, right_claim.claim)
            left_claim_id = _emit_argument(
                emitted,
                claim=left_claim,
                canonical_claim_id=canonical_claim_id,
                concept_id=concept_id,
                branch_origins=(branch_a,),
                emitted_claim_id=_disambiguate_id(artifact_id, branch_a),
                annotate_branch_origin=branch_a,
            )
            right_claim_id = _emit_argument(
                emitted,
                claim=right_claim,
                canonical_claim_id=canonical_claim_id,
                concept_id=concept_id,
                branch_origins=(branch_b,),
                emitted_claim_id=_disambiguate_id(artifact_id, branch_b),
                annotate_branch_origin=branch_b,
            )
            if diff_kind == _DiffKind.CONFLICT:
                attacks.add((left_claim_id, right_claim_id))
                attacks.add((right_claim_id, left_claim_id))
            elif diff_kind == _DiffKind.PHI_NODE:
                ignorance.add((left_claim_id, right_claim_id))
                ignorance.add((right_claim_id, left_claim_id))
            continue

        if in_left:
            _emit_argument(
                emitted,
                claim=left_claim,
                canonical_claim_id=canonical_claim_id,
                concept_id=concept_id,
                branch_origins=(branch_a,),
            )
            continue

        if in_right:
            _emit_argument(
                emitted,
                claim=right_claim,
                canonical_claim_id=canonical_claim_id,
                concept_id=concept_id,
                branch_origins=(branch_b,),
            )

    emitted.sort(key=lambda argument: (argument.canonical_claim_id, argument.claim_id))
    argument_index = {argument.claim_id: argument for argument in emitted}

    canonical_groups: dict[str, list[MergeArgument]] = {}
    for argument in emitted:
        canonical_groups.setdefault(argument.canonical_claim_id, []).append(argument)

    for arguments in canonical_groups.values():
        if len(arguments) < 2:
            continue
        left_arguments = [
            argument
            for argument in arguments
            if argument.branch_origins == (branch_a,)
        ]
        right_arguments = [
            argument
            for argument in arguments
            if argument.branch_origins == (branch_b,)
        ]
        for left_argument, right_argument in product(left_arguments, right_arguments):
            pair = (left_argument.claim_id, right_argument.claim_id)
            reverse_pair = (right_argument.claim_id, left_argument.claim_id)
            if pair in attacks or pair in ignorance or reverse_pair in attacks or reverse_pair in ignorance:
                continue
            if _claims_equal(left_argument.claim, right_argument.claim):
                continue
            diff_kind = _classify_pair(left_argument.claim, right_argument.claim)
            if diff_kind == _DiffKind.CONFLICT:
                attacks.add(pair)
                attacks.add(reverse_pair)
            elif diff_kind == _DiffKind.PHI_NODE:
                ignorance.add(pair)
                ignorance.add(reverse_pair)

    semantic_candidate_map: dict[str, list[str]] = {}
    for argument in emitted:
        semantic_key = json.dumps(_claim_candidate_key(argument.claim), sort_keys=True)
        semantic_candidate_map.setdefault(semantic_key, []).append(argument.claim_id)
    semantic_candidates = tuple(
        tuple(sorted(claim_ids))
        for claim_ids in sorted(
            semantic_candidate_map.values(),
            key=lambda claim_ids: tuple(sorted(claim_ids)),
        )
        if len(claim_ids) > 1
        and len({argument_index[claim_id].canonical_claim_id for claim_id in claim_ids}) > 1
    )

    argument_ids = frozenset(argument.claim_id for argument in emitted)
    ordered_pairs = frozenset(product(argument_ids, argument_ids))
    framework = PartialArgumentationFramework(
        arguments=argument_ids,
        attacks=frozenset(attacks),
        ignorance=frozenset(ignorance),
        non_attacks=ordered_pairs - frozenset(attacks) - frozenset(ignorance),
    )
    return RepoMergeFramework(
        branch_a=branch_a,
        branch_b=branch_b,
        arguments=tuple(emitted),
        framework=framework,
        semantic_candidates=semantic_candidates,
    )


__all__ = [
    "MergeArgument",
    "RepoMergeFramework",
    "build_merge_framework",
]
