"""Direct repository merge emission as a formal object.

The repository layer no longer emits claim-bucket classifications as its
public merge result. Instead it produces a provenance-bearing partial
argumentation framework over the claim alternatives that survive the merge.
"""
from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, replace
from enum import Enum
from itertools import product
from typing import Any

from propstore.merge.merge_claims import MergeClaim
from propstore.merge.witness import ProvenanceWitness
from argumentation.partial_af import PartialArgumentationFramework
from propstore.storage.snapshot import RepositorySnapshot
from propstore.core.conditions.solver import Z3TranslationError
from propstore.claims import claim_file_claims


class _DiffKind(Enum):
    COMPATIBLE = "compatible"
    CONFLICT = "conflict"
    PHI_NODE = "phi_node"
    UNKNOWN = "unknown"
    UNTRANSLATABLE = "untranslatable"

    @classmethod
    def from_conflict_class(cls, conflict_class: object) -> _DiffKind:
        from propstore.conflict_detector import ConflictClass

        if conflict_class in (
            ConflictClass.CONFLICT,
            ConflictClass.OVERLAP,
            ConflictClass.PARAM_CONFLICT,
        ):
            return cls.CONFLICT
        if conflict_class in (
            ConflictClass.PHI_NODE,
            ConflictClass.CONTEXT_PHI_NODE,
        ):
            return cls.PHI_NODE
        if conflict_class == ConflictClass.UNKNOWN:
            return cls.UNKNOWN
        return cls.COMPATIBLE


@dataclass(frozen=True)
class _IndexedClaim:
    claim: MergeClaim
    artifact_id: str
    logical_ids: tuple[str, ...]
    primary_logical_id: str | None
    concept_id: str


class MergeComparisonProvenanceError(ValueError):
    """Raised when a merge comparison lacks source provenance."""


class IntegrityConstraintViolation(ValueError):
    """Raised when a requested merge cannot satisfy its integrity constraint."""


@dataclass(frozen=True)
class IntegrityConstraint:
    required_artifact_ids: frozenset[str] = frozenset()
    forbidden_artifact_ids: frozenset[str] = frozenset()

    def accepts(self, argument: MergeArgument) -> bool:
        return argument.artifact_id not in self.forbidden_artifact_ids

    def assert_satisfied(self, arguments: Sequence[MergeArgument]) -> None:
        present = {argument.artifact_id for argument in arguments}
        missing = self.required_artifact_ids - present
        if missing:
            raise IntegrityConstraintViolation(
                f"merge candidates do not satisfy required artifact ids: {sorted(missing)!r}"
            )


@dataclass(frozen=True)
class MergeArgument:
    """A claim alternative emitted by the repository merge boundary."""

    assertion_id: str
    canonical_claim_id: str
    artifact_id: str
    logical_id: str | None
    concept_id: str
    claim: MergeClaim
    branch_origins: tuple[str, ...]
    witness_basis: tuple[ProvenanceWitness, ...]


@dataclass(frozen=True)
class RepositoryMergeFramework:
    """Repository-facing merge object with provenance and formal semantics."""

    branch_a: str
    branch_b: str
    arguments: tuple[MergeArgument, ...]
    framework: PartialArgumentationFramework
    semantic_candidates: tuple[tuple[str, ...], ...] = ()

    def argument_index(self) -> dict[str, MergeArgument]:
        return {argument.assertion_id: argument for argument in self.arguments}


def _annotate_provenance(claim: MergeClaim, branch_name: str) -> MergeClaim:
    return MergeClaim(document=claim.document, branch_origin=branch_name)


def _claim_artifact_id(claim: MergeClaim) -> str | None:
    return claim.artifact_id


def _claim_logical_ids(claim: MergeClaim) -> tuple[str, ...]:
    return tuple(sorted(claim.logical_ids))


def _extract_concept(claim: MergeClaim) -> str:
    return claim.value_concept_id


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
        for claim in claim_file_claims(claim_file):
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
    artifact_ids_by_logical_id: dict[str, set[str]] = {}
    claims_by_artifact_id: dict[str, _IndexedClaim] = {}
    for index in indexes:
        for artifact_id, claim in index.items():
            claims_by_artifact_id.setdefault(artifact_id, claim)
            for logical_id in claim.logical_ids:
                artifact_ids_by_logical_id.setdefault(logical_id, set()).add(artifact_id)

    logical_id_counts = Counter(
        {
            logical_id: len(artifact_ids)
            for logical_id, artifact_ids in artifact_ids_by_logical_id.items()
        }
    )

    groups: dict[str, str] = {}
    for artifact_id, claim in claims_by_artifact_id.items():
        primary = claim.primary_logical_id
        if primary is not None and logical_id_counts[primary] == 1:
            groups[artifact_id] = primary
            continue
        groups[artifact_id] = artifact_id
    return groups


def _classify_pair(
    left_claim: MergeClaim,
    right_claim: MergeClaim,
) -> _DiffKind:
    """Classify disagreement between two concrete claim alternatives."""
    from propstore.conflict_detector import ConflictClass, detect_conflicts
    from propstore.conflict_detector.collectors import conflict_claim_from_payload

    left_conditions = sorted(left_claim.document.conditions)
    right_conditions = sorted(right_claim.document.conditions)
    if left_conditions != right_conditions:
        return _DiffKind.PHI_NODE

    comparison_source = (
        left_claim.provenance_payload().get("paper")
    )
    if not isinstance(comparison_source, str) or not comparison_source:
        comparison_source = (
            right_claim.provenance_payload().get("paper")
        )
    if not isinstance(comparison_source, str) or not comparison_source:
        raise MergeComparisonProvenanceError(
            "cannot classify merge pair without source-paper provenance"
        )

    left_conflict_claim = conflict_claim_from_payload(
        left_claim.to_payload(include_branch_origin=False),
        source_paper=comparison_source,
    )
    right_conflict_claim = conflict_claim_from_payload(
        right_claim.to_payload(include_branch_origin=False),
        source_paper=comparison_source,
    )
    if left_conflict_claim is None or right_conflict_claim is None:
        return _DiffKind.COMPATIBLE

    try:
        records = detect_conflicts(
            [left_conflict_claim, right_conflict_claim],
            concept_registry={},
            cel_registry={},
        )
    except (ValueError, Z3TranslationError):
        return _DiffKind.UNTRANSLATABLE

    for record in records:
        if _DiffKind.from_conflict_class(record.warning_class) == _DiffKind.CONFLICT:
            return _DiffKind.CONFLICT

    for record in records:
        if _DiffKind.from_conflict_class(record.warning_class) == _DiffKind.PHI_NODE:
            return _DiffKind.PHI_NODE

    for record in records:
        if _DiffKind.from_conflict_class(record.warning_class) == _DiffKind.UNKNOWN:
            return _DiffKind.UNKNOWN

    return _DiffKind.UNKNOWN


def _emit_argument(
    emitted: list[MergeArgument],
    *,
    claim: _IndexedClaim,
    canonical_claim_id: str,
    concept_id: str,
    branch_origins: tuple[str, ...],
    annotate_branch_origin: str | None = None,
) -> str:
    merged_claim = claim.claim
    if annotate_branch_origin is not None:
        merged_claim = _annotate_provenance(merged_claim, annotate_branch_origin)
    assertion_id = str(merged_claim.assertion_id)
    witness_basis = (ProvenanceWitness.from_merge_claim(merged_claim),)
    emitted.append(
        MergeArgument(
            assertion_id=assertion_id,
            canonical_claim_id=canonical_claim_id,
            artifact_id=claim.artifact_id,
            logical_id=claim.primary_logical_id,
            concept_id=concept_id,
            claim=merged_claim,
            branch_origins=branch_origins,
            witness_basis=witness_basis,
        )
    )
    return assertion_id


def build_merge_framework(
    snapshot: RepositorySnapshot,
    branch_a: str,
    branch_b: str,
    *,
    integrity_constraint: IntegrityConstraint | None = None,
    additional_branches: Sequence[str] = (),
) -> RepositoryMergeFramework:
    """Build the direct repository merge object for a branch profile."""
    base_sha = snapshot.merge_base(branch_a, branch_b)
    branch_names = (branch_a, branch_b, *tuple(additional_branches))
    branch_heads = {
        branch_name: snapshot.branch_head(branch_name)
        for branch_name in branch_names
    }

    base_idx = _index_claims(
        [
            handle
            for handle in snapshot.repo.families.claims.iter_handles(commit=base_sha)
        ]
    )
    branch_indexes = {
        branch_name: _index_claims(
            [
                handle
                for handle in snapshot.repo.families.claims.iter_handles(commit=commit)
            ]
        )
        for branch_name, commit in branch_heads.items()
    }
    canonical_groups = _canonical_claim_groups(base_idx, *branch_indexes.values())

    all_ids = sorted(set(base_idx).union(*(set(index) for index in branch_indexes.values())))
    emitted: list[MergeArgument] = []
    attacks: set[tuple[str, str]] = set()
    ignorance: set[tuple[str, str]] = set()

    for artifact_id in all_ids:
        canonical_claim_id = canonical_groups.get(artifact_id, artifact_id)
        base_claim = base_idx.get(artifact_id)
        branch_claims = tuple(
            (branch_name, index[artifact_id])
            for branch_name, index in branch_indexes.items()
            if artifact_id in index
        )
        if not branch_claims:
            continue

        concept_id = ""
        for candidate in (*[claim for _, claim in branch_claims], base_claim):
            if candidate is not None:
                concept_id = candidate.concept_id
                break

        if len(branch_claims) == 1:
            branch_name, indexed_claim = branch_claims[0]
            _emit_argument(
                emitted,
                claim=indexed_claim,
                canonical_claim_id=canonical_claim_id,
                concept_id=concept_id,
                branch_origins=(branch_name,),
            )
            continue

        first_claim = branch_claims[0][1]
        if all(_claims_equal(first_claim.claim, indexed.claim) for _, indexed in branch_claims[1:]):
            _emit_argument(
                emitted,
                claim=first_claim,
                canonical_claim_id=canonical_claim_id,
                concept_id=concept_id,
                branch_origins=tuple(branch_name for branch_name, _ in branch_claims),
            )
            continue

        changed_claims = branch_claims
        if base_claim is not None:
            changed_claims = tuple(
                (branch_name, indexed)
                for branch_name, indexed in branch_claims
                if not _claims_equal(indexed.claim, base_claim.claim)
            )
            if len(changed_claims) == 1:
                branch_name, indexed_claim = changed_claims[0]
                _emit_argument(
                    emitted,
                    claim=indexed_claim,
                    canonical_claim_id=canonical_claim_id,
                    concept_id=concept_id,
                    branch_origins=(branch_name,),
                )
                continue
            if not changed_claims:
                _emit_argument(
                    emitted,
                    claim=first_claim,
                    canonical_claim_id=canonical_claim_id,
                    concept_id=concept_id,
                    branch_origins=tuple(branch_name for branch_name, _ in branch_claims),
                )
                continue

        emitted_for_artifact: list[tuple[str, str, _IndexedClaim]] = []
        for branch_name, indexed_claim in changed_claims:
            assertion_id = _emit_argument(
                    emitted,
                    claim=indexed_claim,
                    canonical_claim_id=canonical_claim_id,
                    concept_id=concept_id,
                    branch_origins=(branch_name,),
                    annotate_branch_origin=branch_name,
            )
            emitted_for_artifact.append((branch_name, assertion_id, indexed_claim))
        for left, right in product(emitted_for_artifact, emitted_for_artifact):
            if left[0] >= right[0]:
                continue
            diff_kind = _classify_pair(left[2].claim, right[2].claim)
            pair = (left[1], right[1])
            reverse_pair = (right[1], left[1])
            if diff_kind == _DiffKind.CONFLICT:
                attacks.add(pair)
                attacks.add(reverse_pair)
            elif diff_kind in (_DiffKind.PHI_NODE, _DiffKind.UNKNOWN, _DiffKind.UNTRANSLATABLE):
                ignorance.add(pair)
                ignorance.add(reverse_pair)

    emitted = _deduplicate_arguments(emitted)
    if integrity_constraint is not None:
        emitted = [
            argument
            for argument in emitted
            if integrity_constraint.accepts(argument)
        ]
        integrity_constraint.assert_satisfied(emitted)
    emitted.sort(key=lambda argument: (argument.canonical_claim_id, argument.assertion_id))
    argument_index = {argument.assertion_id: argument for argument in emitted}

    emitted_groups: dict[str, list[MergeArgument]] = {}
    for argument in emitted:
        emitted_groups.setdefault(argument.canonical_claim_id, []).append(argument)

    for arguments in emitted_groups.values():
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
            pair = (left_argument.assertion_id, right_argument.assertion_id)
            reverse_pair = (right_argument.assertion_id, left_argument.assertion_id)
            if pair in attacks or pair in ignorance or reverse_pair in attacks or reverse_pair in ignorance:
                continue
            if _claims_equal(left_argument.claim, right_argument.claim):
                continue
            diff_kind = _classify_pair(left_argument.claim, right_argument.claim)
            if diff_kind == _DiffKind.CONFLICT:
                attacks.add(pair)
                attacks.add(reverse_pair)
            elif diff_kind in (_DiffKind.PHI_NODE, _DiffKind.UNKNOWN, _DiffKind.UNTRANSLATABLE):
                ignorance.add(pair)
                ignorance.add(reverse_pair)

    semantic_candidate_map: dict[str, list[str]] = {}
    for argument in emitted:
        semantic_key = json.dumps(_claim_candidate_key(argument.claim), sort_keys=True)
        semantic_candidate_map.setdefault(semantic_key, []).append(argument.assertion_id)
    semantic_candidates = tuple(
        tuple(sorted(claim_ids))
        for claim_ids in sorted(
            semantic_candidate_map.values(),
            key=lambda claim_ids: tuple(sorted(claim_ids)),
        )
        if len(claim_ids) > 1
        and len({argument_index[claim_id].canonical_claim_id for claim_id in claim_ids}) > 1
    )

    argument_ids = frozenset(argument.assertion_id for argument in emitted)
    ordered_pairs = frozenset(product(argument_ids, argument_ids))
    framework = PartialArgumentationFramework(
        arguments=argument_ids,
        attacks=frozenset(attacks),
        ignorance=frozenset(ignorance),
        non_attacks=ordered_pairs - frozenset(attacks) - frozenset(ignorance),
    )
    return RepositoryMergeFramework(
        branch_a=branch_a,
        branch_b=branch_b,
        arguments=tuple(emitted),
        framework=framework,
        semantic_candidates=semantic_candidates,
    )


def _deduplicate_arguments(arguments: list[MergeArgument]) -> list[MergeArgument]:
    by_assertion_id: dict[str, MergeArgument] = {}
    for argument in arguments:
        existing = by_assertion_id.get(argument.assertion_id)
        if existing is None:
            by_assertion_id[argument.assertion_id] = argument
            continue
        by_assertion_id[argument.assertion_id] = replace(
            existing,
            branch_origins=tuple(sorted(set(existing.branch_origins) | set(argument.branch_origins))),
            witness_basis=tuple(
                {
                    witness: None
                    for witness in (*existing.witness_basis, *argument.witness_basis)
                }
            ),
        )
    return list(by_assertion_id.values())


__all__ = [
    "MergeArgument",
    "IntegrityConstraint",
    "IntegrityConstraintViolation",
    "MergeComparisonProvenanceError",
    "RepositoryMergeFramework",
    "build_merge_framework",
]
