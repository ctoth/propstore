"""Repository merge emitted as a formal partial argumentation framework.

The merge boundary does not collapse disagreement into a single winning claim. It
emits a :class:`~argumentation.frameworks.partial_af.PartialArgumentationFramework`
over the claim alternatives that survive a three-way merge: pairs that genuinely
conflict become *attacks*, pairs whose relationship the system cannot establish
(φ-nodes, regime splits, untranslatable conditions, unknown) become *ignorance*,
and everything else is a *non-attack*. The rival normalizations are held, never
resolved here — resolution is a render-time policy decision (CLAUDE.md).

This is the merge MATH over plain claim inputs: the per-branch claim sets are passed
in directly as ``Mapping[branch -> Sequence[MergeClaim]]`` plus an optional merge-base
set. The two-parent storage commit and the ``Repository`` facade that would read those
sets out of git land in Phase 9; this module never touches a store.

Pair classification reuses :func:`propstore.conflict_detector.detect_conflicts`
(Phase 6a): ``CONFLICT``/``OVERLAP``/``PARAM_CONFLICT`` → attack; ``PHI_NODE``/
``CONTEXT_PHI_NODE``/``UNKNOWN`` and any untranslatable comparison → ignorance;
``COMPATIBLE`` → non-attack.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum
from itertools import product

from condition_ir import Z3TranslationError

from propstore.conflict_detector import ConflictClass, detect_conflicts
from propstore.conflict_detector.models import ConflictClaim
from propstore.merge.merge_claims import MergeClaim
from propstore.merge.witness import ProvenanceWitness
from argumentation.frameworks.partial_af import PartialArgumentationFramework


class _DiffKind(Enum):
    COMPATIBLE = "compatible"
    CONFLICT = "conflict"
    PHI_NODE = "phi_node"
    UNKNOWN = "unknown"
    UNTRANSLATABLE = "untranslatable"

    @classmethod
    def from_conflict_class(cls, conflict_class: ConflictClass) -> _DiffKind:
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


class MergeComparisonProvenanceError(ValueError):
    """Raised when a merge comparison lacks source-paper provenance."""


class IntegrityConstraintViolation(ValueError):
    """Raised when a requested merge cannot satisfy its integrity constraint."""


@dataclass(frozen=True)
class IntegrityConstraint:
    """A merge-side integrity constraint over emitted arguments.

    Distinct from the model-theoretic IC merge in ``propstore.belief_set.ic_merge``:
    this one filters out forbidden source artifacts and asserts that all required
    artifacts survive the merge. It is a hard precondition on the candidate set, not
    a belief-revision operator.
    """

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


def _index_claims(claims: Sequence[MergeClaim]) -> dict[str, MergeClaim]:
    index: dict[str, MergeClaim] = {}
    for claim in claims:
        index[claim.artifact_id] = claim
    return index


def _canonical_claim_groups(*indexes: dict[str, MergeClaim]) -> dict[str, str]:
    """Map each artifact id to its canonical claim id.

    In the provenance-free charter the claim's storage id *is* its logical identity,
    so an artifact's canonical id is its own ``claim_id``. The shape mirrors the
    reference's logical-id grouping so semantic-candidate clustering can ask whether
    two arguments belong to different canonical claims.
    """

    canonical: dict[str, str] = {}
    counts: Counter[str] = Counter()
    for index in indexes:
        for artifact_id in index:
            counts[artifact_id] += 1
    for index in indexes:
        for artifact_id in index:
            canonical.setdefault(artifact_id, artifact_id)
    return canonical


def _claims_equal(left: MergeClaim, right: MergeClaim) -> bool:
    return left.semantic_key() == right.semantic_key()


def _conflict_claim(claim: MergeClaim, *, source_paper: str) -> ConflictClaim:
    """The conflict-detector view of a merge claim, with its source folded in."""

    return ConflictClaim.from_claim(
        claim.claim, source_paper=source_paper
    ).with_source_condition()


def _classify_pair(left_claim: MergeClaim, right_claim: MergeClaim) -> _DiffKind:
    """Classify disagreement between two concrete claim alternatives."""

    comparison_source = left_claim.paper or right_claim.paper
    if not comparison_source:
        raise MergeComparisonProvenanceError(
            "cannot classify merge pair without source-paper provenance"
        )

    left_conflict = _conflict_claim(left_claim, source_paper=comparison_source)
    right_conflict = _conflict_claim(right_claim, source_paper=comparison_source)

    try:
        records = detect_conflicts([left_conflict, right_conflict], {}, {})
    except (ValueError, Z3TranslationError):
        return _DiffKind.UNTRANSLATABLE

    if sorted(left_claim.conditions) != sorted(right_claim.conditions):
        return _DiffKind.PHI_NODE

    kinds = [_DiffKind.from_conflict_class(record.warning_class) for record in records]
    if _DiffKind.CONFLICT in kinds:
        return _DiffKind.CONFLICT
    if _DiffKind.PHI_NODE in kinds:
        return _DiffKind.PHI_NODE
    return _DiffKind.UNKNOWN


def _emit_argument(
    emitted: list[MergeArgument],
    *,
    claim: MergeClaim,
    canonical_claim_id: str,
    concept_id: str,
    branch_origins: tuple[str, ...],
    annotate_branch_origin: str | None = None,
) -> str:
    merged_claim = claim
    if annotate_branch_origin is not None:
        merged_claim = replace(claim, branch_origin=annotate_branch_origin)
    assertion_id = merged_claim.assertion_id
    emitted.append(
        MergeArgument(
            assertion_id=assertion_id,
            canonical_claim_id=canonical_claim_id,
            artifact_id=merged_claim.artifact_id,
            logical_id=merged_claim.artifact_id,
            concept_id=concept_id,
            claim=merged_claim,
            branch_origins=branch_origins,
            witness_basis=(ProvenanceWitness.from_merge_claim(merged_claim),),
        )
    )
    return assertion_id


def _deduplicate_arguments(arguments: list[MergeArgument]) -> list[MergeArgument]:
    by_assertion_id: dict[str, MergeArgument] = {}
    for argument in arguments:
        existing = by_assertion_id.get(argument.assertion_id)
        if existing is None:
            by_assertion_id[argument.assertion_id] = argument
            continue
        merged_witnesses = tuple(
            dict.fromkeys((*existing.witness_basis, *argument.witness_basis))
        )
        by_assertion_id[argument.assertion_id] = replace(
            existing,
            branch_origins=tuple(
                sorted(set(existing.branch_origins) | set(argument.branch_origins))
            ),
            witness_basis=merged_witnesses,
        )
    return list(by_assertion_id.values())


def _concept_for_artifact(
    branch_claims: Sequence[tuple[str, MergeClaim]],
    base_claim: MergeClaim | None,
) -> str:
    for _, claim in branch_claims:
        concept_id = claim.value_concept_id
        if concept_id:
            return concept_id
    if base_claim is not None and base_claim.value_concept_id:
        return base_claim.value_concept_id
    return ""


def build_merge_framework(
    claim_sets_per_branch: Mapping[str, Sequence[MergeClaim]],
    branch_a: str,
    branch_b: str,
    *,
    base_claims: Sequence[MergeClaim] = (),
    integrity_constraint: IntegrityConstraint | None = None,
    additional_branches: Sequence[str] = (),
) -> RepositoryMergeFramework:
    """Build the direct repository merge object over plain per-branch claim sets."""

    branch_names = (branch_a, branch_b, *additional_branches)
    base_idx = _index_claims(base_claims)
    branch_indexes = {
        branch_name: _index_claims(claim_sets_per_branch.get(branch_name, ()))
        for branch_name in branch_names
    }
    canonical_groups = _canonical_claim_groups(base_idx, *branch_indexes.values())

    all_ids = sorted(
        set(base_idx).union(*(set(index) for index in branch_indexes.values()))
    )
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

        concept_id = _concept_for_artifact(branch_claims, base_claim)

        if len(branch_claims) == 1:
            branch_name, claim = branch_claims[0]
            _emit_argument(
                emitted,
                claim=claim,
                canonical_claim_id=canonical_claim_id,
                concept_id=concept_id,
                branch_origins=(branch_name,),
            )
            continue

        first_claim = branch_claims[0][1]
        if all(_claims_equal(first_claim, claim) for _, claim in branch_claims[1:]):
            _emit_argument(
                emitted,
                claim=first_claim,
                canonical_claim_id=canonical_claim_id,
                concept_id=concept_id,
                branch_origins=tuple(name for name, _ in branch_claims),
            )
            continue

        changed_claims = branch_claims
        if base_claim is not None:
            changed_claims = tuple(
                (branch_name, claim)
                for branch_name, claim in branch_claims
                if not _claims_equal(claim, base_claim)
            )
            if len(changed_claims) == 1:
                branch_name, claim = changed_claims[0]
                _emit_argument(
                    emitted,
                    claim=claim,
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
                    branch_origins=tuple(name for name, _ in branch_claims),
                )
                continue

        emitted_for_artifact: list[tuple[str, str, MergeClaim]] = []
        for branch_name, claim in changed_claims:
            assertion_id = _emit_argument(
                emitted,
                claim=claim,
                canonical_claim_id=canonical_claim_id,
                concept_id=concept_id,
                branch_origins=(branch_name,),
                annotate_branch_origin=branch_name,
            )
            emitted_for_artifact.append((branch_name, assertion_id, claim))
        for left, right in product(emitted_for_artifact, emitted_for_artifact):
            if left[0] >= right[0]:
                continue
            diff_kind = _classify_pair(left[2], right[2])
            _record_pair(attacks, ignorance, left[1], right[1], diff_kind)

    emitted = _deduplicate_arguments(emitted)
    if integrity_constraint is not None:
        emitted = [
            argument for argument in emitted if integrity_constraint.accepts(argument)
        ]
        integrity_constraint.assert_satisfied(emitted)
    emitted.sort(key=lambda argument: (argument.canonical_claim_id, argument.assertion_id))
    argument_index = {argument.assertion_id: argument for argument in emitted}

    _classify_cross_branch_pairs(
        emitted,
        branch_a=branch_a,
        branch_b=branch_b,
        attacks=attacks,
        ignorance=ignorance,
    )

    semantic_candidates = _semantic_candidates(emitted, argument_index)

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


def _record_pair(
    attacks: set[tuple[str, str]],
    ignorance: set[tuple[str, str]],
    left_id: str,
    right_id: str,
    diff_kind: _DiffKind,
) -> None:
    pair = (left_id, right_id)
    reverse_pair = (right_id, left_id)
    if diff_kind == _DiffKind.CONFLICT:
        attacks.add(pair)
        attacks.add(reverse_pair)
    elif diff_kind in (_DiffKind.PHI_NODE, _DiffKind.UNKNOWN, _DiffKind.UNTRANSLATABLE):
        ignorance.add(pair)
        ignorance.add(reverse_pair)


def _classify_cross_branch_pairs(
    emitted: Sequence[MergeArgument],
    *,
    branch_a: str,
    branch_b: str,
    attacks: set[tuple[str, str]],
    ignorance: set[tuple[str, str]],
) -> None:
    emitted_groups: dict[str, list[MergeArgument]] = {}
    for argument in emitted:
        emitted_groups.setdefault(argument.canonical_claim_id, []).append(argument)

    for arguments in emitted_groups.values():
        if len(arguments) < 2:
            continue
        left_arguments = [a for a in arguments if a.branch_origins == (branch_a,)]
        right_arguments = [a for a in arguments if a.branch_origins == (branch_b,)]
        for left_argument, right_argument in product(left_arguments, right_arguments):
            pair = (left_argument.assertion_id, right_argument.assertion_id)
            reverse_pair = (right_argument.assertion_id, left_argument.assertion_id)
            if (
                pair in attacks
                or pair in ignorance
                or reverse_pair in attacks
                or reverse_pair in ignorance
            ):
                continue
            if _claims_equal(left_argument.claim, right_argument.claim):
                continue
            diff_kind = _classify_pair(left_argument.claim, right_argument.claim)
            _record_pair(
                attacks,
                ignorance,
                left_argument.assertion_id,
                right_argument.assertion_id,
                diff_kind,
            )


def _semantic_candidates(
    emitted: Sequence[MergeArgument],
    argument_index: Mapping[str, MergeArgument],
) -> tuple[tuple[str, ...], ...]:
    candidate_map: dict[str, list[str]] = {}
    for argument in emitted:
        key = json.dumps(argument.claim.candidate_key(), sort_keys=True, default=str)
        candidate_map.setdefault(key, []).append(argument.assertion_id)
    return tuple(
        tuple(sorted(assertion_ids))
        for assertion_ids in sorted(
            candidate_map.values(), key=lambda ids: tuple(sorted(ids))
        )
        if len(assertion_ids) > 1
        and len({argument_index[a].canonical_claim_id for a in assertion_ids}) > 1
    )


__all__ = [
    "IntegrityConstraint",
    "IntegrityConstraintViolation",
    "MergeArgument",
    "MergeComparisonProvenanceError",
    "RepositoryMergeFramework",
    "build_merge_framework",
]
