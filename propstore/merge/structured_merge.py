"""Branch-local structured projection and exact merge candidates."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


from propstore.core.id_types import (
    ClaimId,
    JustificationId,
)
from propstore.compiler.ir import (
    ClaimCompilationBundle,
    SemanticClaimFile,
)
from propstore.families.claims.declaration import Claim, compile_claim_models
from propstore.families.relations.declaration import Stance
from propstore.stances import coerce_stance_type
from argumentation.dung import ArgumentationFramework
from propstore.aspic_bridge import build_aspic_projection
from propstore.claims import LoadedClaimsFile
from propstore.merge.merge_claims import MergeClaim
from propstore.storage.snapshot import RepositorySnapshot
from propstore.structured_projection import StructuredProjection


@dataclass(frozen=True)
class BranchArgumentationEvidence:
    branch: str
    backend: str
    semantics: str
    accepted_assertion_ids: tuple[str, ...]
    witness_assertion_ids: tuple[str, ...]
    skeptical_assertion_ids: tuple[str, ...] = ()
    decision_owner: str = "merge_policy"


@dataclass(frozen=True)
class BranchStructuredSummary:
    branch: str
    assertion_ids: tuple[str, ...]
    claim_provenance: dict[str, dict[str, Any]]
    content_signature: str
    relation_surface: dict[str, str]
    lossiness: tuple[str, ...]
    active_claims: tuple[MergeClaim, ...]
    stance_rows: tuple[Stance, ...]
    projection: StructuredProjection


def _normalize_for_signature(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _normalize_for_signature(val)
            for key, val in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_normalize_for_signature(item) for item in value]
    return value


def _sorted_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(str(value) for value in values)))


def argumentation_evidence_from_projection(
    *,
    branch: str,
    projection: StructuredProjection,
    claim_assertion_ids: Mapping[str, Sequence[str]],
    semantics: str = "grounded",
) -> BranchArgumentationEvidence:
    from propstore.structured_projection import compute_structured_justified_arguments

    justified = compute_structured_justified_arguments(
        projection,
        semantics=semantics,
    )
    if isinstance(justified, frozenset):
        accepted_argument_ids = justified
        skeptical_argument_ids = justified
    else:
        accepted_argument_ids = (
            frozenset().union(*justified) if justified else frozenset()
        )
        skeptical_argument_ids = (
            frozenset.intersection(*justified) if justified else frozenset()
        )
    accepted_assertion_ids: list[str] = []
    skeptical_assertion_ids: list[str] = []
    witness_assertion_ids: list[str] = []
    for argument_id in sorted(accepted_argument_ids):
        claim_id = projection.argument_to_claim_id.get(argument_id)
        if claim_id is None:
            continue
        accepted_assertion_ids.extend(
            str(value) for value in claim_assertion_ids.get(claim_id, ())
        )
    for argument_id in sorted(skeptical_argument_ids):
        claim_id = projection.argument_to_claim_id.get(argument_id)
        if claim_id is None:
            continue
        skeptical_assertion_ids.extend(
            str(value) for value in claim_assertion_ids.get(claim_id, ())
        )
    for claim_id in sorted(projection.claim_to_argument_ids):
        witness_assertion_ids.extend(
            str(value) for value in claim_assertion_ids.get(claim_id, ())
        )
    return BranchArgumentationEvidence(
        branch=branch,
        backend="argumentation",
        semantics=semantics,
        accepted_assertion_ids=_sorted_unique(accepted_assertion_ids),
        skeptical_assertion_ids=_sorted_unique(skeptical_assertion_ids),
        witness_assertion_ids=_sorted_unique(witness_assertion_ids),
    )


def _stance_row_from_mapping(
    source_claim_id: ClaimId,
    stance: Mapping[str, Any],
) -> Stance | None:
    raw_target = stance.get("target")
    raw_stance_type = stance.get("type")
    target = raw_target if isinstance(raw_target, str) and raw_target else None
    stance_type = (
        raw_stance_type
        if isinstance(raw_stance_type, str) and raw_stance_type
        else None
    )
    if target is None or stance_type is None:
        return None

    target_justification_id: JustificationId | None = None
    if stance.get("target_justification_id") is not None:
        target_justification_id = JustificationId(stance["target_justification_id"])

    coerced_stance_type = coerce_stance_type(stance_type)
    if coerced_stance_type is None:
        return None

    return Stance(
        source_kind="claim",
        source_id=str(source_claim_id),
        relation_type=str(coerced_stance_type),
        target_kind="claim",
        target_id=str(ClaimId(target)),
        target_justification_id=(
            None if target_justification_id is None else str(target_justification_id)
        ),
        strength=(
            stance["strength"]
            if isinstance(stance.get("strength"), str) and stance["strength"]
            else None
        ),
        conditions_differ=(
            stance["conditions_differ"]
            if (
                isinstance(stance.get("conditions_differ"), str)
                and stance["conditions_differ"]
            )
            else None
        ),
        note=(
            stance["note"]
            if isinstance(stance.get("note"), str) and stance["note"]
            else None
        ),
    )


class _BranchSnapshotStore:
    def __init__(self, repo, commit: str | None, stance_rows: list[Stance]) -> None:
        self._repo = repo
        self._commit = commit
        self._stance_rows = list(stance_rows)
        self._grounding_bundle = None

    def stances_between(self, claim_ids: set[str]) -> list[Stance]:
        return [
            row
            for row in self._stance_rows
            if row.claim_id in claim_ids and row.target_claim_id in claim_ids
        ]

    def grounding_bundle(self):
        if self._grounding_bundle is None:
            self._grounding_bundle = _read_branch_grounding_bundle(
                self._repo,
                self._commit,
            )
        return self._grounding_bundle


def _read_branch_grounding_bundle(repo, commit: str | None):
    from propstore.families.rules.declaration import build_runtime_grounded_bundle

    return build_runtime_grounded_bundle(repo, commit_hash=commit)


def _empty_projection() -> StructuredProjection:
    return StructuredProjection(
        arguments=tuple(),
        framework=ArgumentationFramework(
            arguments=frozenset(),
            defeats=frozenset(),
            attacks=frozenset(),
        ),
        claim_to_argument_ids={},
        argument_to_claim_id={},
    )


def _summary_assertion_ids(active_claims: list[MergeClaim]) -> tuple[str, ...]:
    return tuple(sorted(str(claim.assertion_id) for claim in active_claims))


def _summary_relation_surface() -> dict[str, str]:
    return {
        "attack": "preserved_via_projection",
        "non_attack": "not_preserved_in_summary",
        "ignorance": "not_preserved_in_summary",
    }


def _summary_lossiness() -> tuple[str, ...]:
    return (
        "subargument_identity",
        "justification_identity",
        "preference_metadata",
        "support_metadata",
        "known_non_attack_relations",
        "ignorance_relations",
    )


def _canonical_stance_rows(
    active_claims: list[MergeClaim],
    stance_rows: list[Stance],
) -> list[Stance]:
    in_scope_claim_ids = {ClaimId(claim.artifact_id) for claim in active_claims}
    canonical_rows = [
        row
        for row in stance_rows
        if row.claim_id in in_scope_claim_ids
        and row.target_claim_id in in_scope_claim_ids
    ]
    canonical_rows.sort(
        key=lambda row: (
            str(row.claim_id),
            str(row.target_claim_id),
            row.stance_type,
            ""
            if row.target_justification_id is None
            else str(row.target_justification_id),
            json.dumps(
                _normalize_for_signature(row.attribute_mapping()), sort_keys=True
            ),
        )
    )
    return canonical_rows


def _load_branch_claims(
    snapshot: RepositorySnapshot, commit: str | None
) -> list[MergeClaim]:
    active_claims: list[MergeClaim] = []
    for claim_file in snapshot.repo.families.claims.iter_handles(commit=commit):
        active_claims.append(MergeClaim(document=claim_file.document))
    return active_claims


def _claim_entry(claim: MergeClaim) -> LoadedClaimsFile:
    return LoadedClaimsFile(
        filename=claim.artifact_id,
        artifact_path=None,
        store_root=None,
        document=claim.document,
    )


def _compiled_branch_claims(active_claims: list[MergeClaim]) -> tuple[Claim, ...]:
    entries = tuple(_claim_entry(claim) for claim in active_claims)
    semantic_files = tuple(
        SemanticClaimFile(
            loaded_entry=entry,
            normalized_entry=entry,
            claims=(_semantic_claim(claim, entry),),
        )
        for claim, entry in zip(active_claims, entries, strict=True)
    )
    bundle = ClaimCompilationBundle(
        context=None,
        normalized_claim_files=entries,
        semantic_files=semantic_files,
    )
    return compile_claim_models(bundle, concept_context=None).claims


def build_branch_structured_summary(
    snapshot: RepositorySnapshot, branch: str
) -> BranchStructuredSummary:
    commit = snapshot.git.branch_sha(branch)
    active_claims = _load_branch_claims(snapshot, commit)
    raw_stance_rows = _inline_stance_rows(active_claims) + _file_stance_rows(
        snapshot, commit
    )
    stance_rows = _canonical_stance_rows(active_claims, raw_stance_rows)
    assertion_ids = _summary_assertion_ids(active_claims)
    claim_provenance = _summary_claim_provenance(active_claims)
    content_signature = _summary_content_signature(active_claims, stance_rows)
    if active_claims:
        snapshot_store = _BranchSnapshotStore(snapshot.repo, commit, stance_rows)
        typed_claims = _compiled_branch_claims(active_claims)
        projection = build_aspic_projection(
            snapshot_store,
            typed_claims,
            bundle=snapshot_store.grounding_bundle(),
        )
    else:
        projection = _empty_projection()
    return BranchStructuredSummary(
        branch=branch,
        assertion_ids=assertion_ids,
        claim_provenance=claim_provenance,
        content_signature=content_signature,
        relation_surface=_summary_relation_surface(),
        lossiness=_summary_lossiness(),
        active_claims=tuple(active_claims),
        stance_rows=tuple(stance_rows),
        projection=projection,
    )


def build_structured_merge_candidates(
    snapshot: RepositorySnapshot,
    branch_a: str,
    branch_b: str,
    *,
    operator: str = "sum",
) -> list[ArgumentationFramework]:
    from argumentation.partial_af import (
        EnumerationExceeded,
        leximax_merge_frameworks,
        max_merge_frameworks,
        sum_merge_frameworks,
    )

    def require_candidates(
        result: list[ArgumentationFramework] | EnumerationExceeded,
    ) -> list[ArgumentationFramework]:
        if isinstance(result, EnumerationExceeded):
            raise RuntimeError(str(result))
        return result

    summaries = {
        branch_a: build_branch_structured_summary(snapshot, branch_a),
        branch_b: build_branch_structured_summary(snapshot, branch_b),
    }
    profile = {
        branch: summary.projection.framework for branch, summary in summaries.items()
    }
    if operator == "sum":
        return require_candidates(sum_merge_frameworks(profile))
    if operator == "max":
        return require_candidates(max_merge_frameworks(profile))
    if operator == "leximax":
        return require_candidates(leximax_merge_frameworks(profile))
    raise ValueError(f"Unknown structured merge operator: {operator}")


__all__ = [
    "BranchArgumentationEvidence",
    "BranchStructuredSummary",
    "argumentation_evidence_from_projection",
    "build_branch_structured_summary",
    "build_structured_merge_candidates",
]
