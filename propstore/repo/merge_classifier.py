"""Direct repo emission of a formal merge object.

The repository layer no longer emits claim-bucket classifications as its
public merge result. Instead it produces a provenance-bearing partial
argumentation framework over the claim alternatives that survive the merge.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from itertools import product
from typing import TYPE_CHECKING, Any

from propstore.repo.branch import branch_head, merge_base
from propstore.repo.merge_framework import PartialArgumentationFramework

if TYPE_CHECKING:
    from propstore.repo.git_backend import KnowledgeRepo


class _DiffKind(Enum):
    COMPATIBLE = "compatible"
    CONFLICT = "conflict"
    PHI_NODE = "phi_node"


@dataclass(frozen=True)
class MergeArgument:
    """A claim alternative emitted by the repository merge boundary."""

    claim_id: str
    canonical_claim_id: str
    concept_id: str
    claim: dict[str, Any]
    branch_origins: tuple[str, ...]


@dataclass(frozen=True)
class RepoMergeFramework:
    """Repository-facing merge object with provenance and formal semantics."""

    branch_a: str
    branch_b: str
    arguments: tuple[MergeArgument, ...]
    framework: PartialArgumentationFramework

    def argument_index(self) -> dict[str, MergeArgument]:
        return {argument.claim_id: argument for argument in self.arguments}


def _annotate_provenance(claim: dict[str, Any], branch_name: str) -> dict[str, Any]:
    merged = copy.deepcopy(claim)
    provenance = dict(merged.get("provenance", {}))
    provenance["branch_origin"] = branch_name
    merged["provenance"] = provenance
    return merged


def _disambiguate_id(claim_id: str, suffix: str) -> str:
    safe_suffix = suffix.replace("/", "_").replace("-", "_")
    return f"{claim_id}__{safe_suffix}"


def _extract_concept(claim: dict[str, Any]) -> str:
    concept = claim.get("concept")
    if concept:
        return str(concept)
    concepts = claim.get("concepts", [])
    if concepts:
        return str(concepts[0])
    return ""


def _claim_semantic_key(claim: dict[str, Any]) -> dict[str, Any]:
    skip = {"provenance"}
    return {key: value for key, value in claim.items() if key not in skip}


def _claims_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return _claim_semantic_key(a) == _claim_semantic_key(b)


def _index_claims(claim_files) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for claim_file in claim_files:
        for claim in claim_file.data.get("claims", []):
            claim_id = claim.get("id")
            if claim_id:
                index[str(claim_id)] = claim
    return index


def _classify_pair(
    left_claim: dict[str, Any],
    right_claim: dict[str, Any],
) -> _DiffKind:
    """Classify disagreement between two concrete claim alternatives."""
    from propstore.conflict_detector import ConflictClass, detect_conflicts
    from propstore.validate_claims import LoadedClaimFile

    left_file = LoadedClaimFile(
        filename="_left",
        filepath=None,
        data={
            "source": {
                "paper": "merge_left",
                "extraction_model": "merge",
                "extraction_date": "2026-01-01",
            },
            "claims": [left_claim],
        },
    )
    right_file = LoadedClaimFile(
        filename="_right",
        filepath=None,
        data={
            "source": {
                "paper": "merge_right",
                "extraction_model": "merge",
                "extraction_date": "2026-01-01",
            },
            "claims": [right_claim],
        },
    )

    records = detect_conflicts([left_file, right_file], concept_registry={})

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
    claim: dict[str, Any],
    canonical_claim_id: str,
    concept_id: str,
    branch_origins: tuple[str, ...],
    emitted_claim_id: str | None = None,
    annotate_branch_origin: str | None = None,
) -> str:
    merged_claim = copy.deepcopy(claim)
    claim_id = emitted_claim_id or str(merged_claim.get("id", canonical_claim_id))
    merged_claim["id"] = claim_id
    if annotate_branch_origin is not None:
        merged_claim = _annotate_provenance(merged_claim, annotate_branch_origin)
    emitted.append(
        MergeArgument(
            claim_id=claim_id,
            canonical_claim_id=canonical_claim_id,
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
    from propstore.tree_reader import GitTreeReader
    from propstore.validate_claims import load_claim_files

    base_sha = merge_base(kr, branch_a, branch_b)
    left_sha = branch_head(kr, branch_a)
    right_sha = branch_head(kr, branch_b)

    base_reader = GitTreeReader(kr, commit=base_sha)
    left_reader = GitTreeReader(kr, commit=left_sha)
    right_reader = GitTreeReader(kr, commit=right_sha)

    base_idx = _index_claims(load_claim_files(None, reader=base_reader))
    left_idx = _index_claims(load_claim_files(None, reader=left_reader))
    right_idx = _index_claims(load_claim_files(None, reader=right_reader))

    all_ids = sorted(set(base_idx) | set(left_idx) | set(right_idx))
    emitted: list[MergeArgument] = []
    attacks: set[tuple[str, str]] = set()
    ignorance: set[tuple[str, str]] = set()

    for canonical_claim_id in all_ids:
        base_claim = base_idx.get(canonical_claim_id)
        left_claim = left_idx.get(canonical_claim_id)
        right_claim = right_idx.get(canonical_claim_id)

        concept_id = ""
        for candidate in (left_claim, right_claim, base_claim):
            if candidate is not None:
                concept_id = _extract_concept(candidate)
                break

        in_left = left_claim is not None
        in_right = right_claim is not None
        in_base = base_claim is not None

        if in_left and in_right:
            if _claims_equal(left_claim, right_claim):
                _emit_argument(
                    emitted,
                    claim=left_claim,
                    canonical_claim_id=canonical_claim_id,
                    concept_id=concept_id,
                    branch_origins=(branch_a, branch_b),
                )
                continue

            if in_base and _claims_equal(left_claim, base_claim):
                _emit_argument(
                    emitted,
                    claim=right_claim,
                    canonical_claim_id=canonical_claim_id,
                    concept_id=concept_id,
                    branch_origins=(branch_b,),
                )
                continue

            if in_base and _claims_equal(right_claim, base_claim):
                _emit_argument(
                    emitted,
                    claim=left_claim,
                    canonical_claim_id=canonical_claim_id,
                    concept_id=concept_id,
                    branch_origins=(branch_a,),
                )
                continue

            diff_kind = _classify_pair(left_claim, right_claim)
            left_claim_id = _emit_argument(
                emitted,
                claim=left_claim,
                canonical_claim_id=canonical_claim_id,
                concept_id=concept_id,
                branch_origins=(branch_a,),
                emitted_claim_id=_disambiguate_id(canonical_claim_id, branch_a),
                annotate_branch_origin=branch_a,
            )
            right_claim_id = _emit_argument(
                emitted,
                claim=right_claim,
                canonical_claim_id=canonical_claim_id,
                concept_id=concept_id,
                branch_origins=(branch_b,),
                emitted_claim_id=_disambiguate_id(canonical_claim_id, branch_b),
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
    )


__all__ = [
    "MergeArgument",
    "RepoMergeFramework",
    "build_merge_framework",
]
