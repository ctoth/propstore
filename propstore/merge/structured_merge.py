"""Branch-local structured projection and exact merge candidates."""
from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from propstore.core.id_types import ClaimId, JustificationId, to_claim_id, to_justification_id
from propstore.core.row_types import StanceRow
from propstore.stances import coerce_stance_type
from argumentation.dung import ArgumentationFramework
from propstore.claims import claim_file_claims
from propstore.merge.merge_claims import MergeClaim
from propstore.storage.snapshot import RepositorySnapshot
from propstore.structured_projection import StructuredProjection, build_structured_projection


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
    stance_rows: tuple[StanceRow, ...]
    projection: StructuredProjection


def _optional_string(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


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
        accepted_argument_ids = frozenset().union(*justified) if justified else frozenset()
        skeptical_argument_ids = (
            frozenset.intersection(*justified)
            if justified
            else frozenset()
        )
    accepted_assertion_ids: list[str] = []
    skeptical_assertion_ids: list[str] = []
    witness_assertion_ids: list[str] = []
    for argument_id in sorted(accepted_argument_ids):
        claim_id = projection.argument_to_claim_id.get(argument_id)
        if claim_id is None:
            continue
        accepted_assertion_ids.extend(str(value) for value in claim_assertion_ids.get(claim_id, ()))
    for argument_id in sorted(skeptical_argument_ids):
        claim_id = projection.argument_to_claim_id.get(argument_id)
        if claim_id is None:
            continue
        skeptical_assertion_ids.extend(str(value) for value in claim_assertion_ids.get(claim_id, ()))
    for claim_id in sorted(projection.claim_to_argument_ids):
        witness_assertion_ids.extend(str(value) for value in claim_assertion_ids.get(claim_id, ()))
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
) -> StanceRow | None:
    target = _optional_string(stance.get("target"))
    stance_type = _optional_string(stance.get("type"))
    if target is None or stance_type is None:
        return None

    attributes: dict[str, Any] = {}
    target_justification_id: JustificationId | None = None
    for key, value in stance.items():
        if key in {"target", "type"} or value is None:
            continue
        if key == "target_justification_id":
            target_justification_id = to_justification_id(value)
            continue
        attributes[str(key)] = value

    coerced_stance_type = coerce_stance_type(stance_type)
    if coerced_stance_type is None:
        return None

    return StanceRow(
        claim_id=source_claim_id,
        target_claim_id=to_claim_id(target),
        stance_type=coerced_stance_type,
        target_justification_id=target_justification_id,
        attributes=attributes,
    )


class _BranchSnapshotStore:
    def __init__(self, repo, commit: str | None, stance_rows: list[StanceRow]) -> None:
        self._repo = repo
        self._commit = commit
        self._stance_rows = list(stance_rows)
        self._grounding_bundle = None

    def stances_between(self, claim_ids: set[str]) -> list[StanceRow]:
        return [
            row
            for row in self._stance_rows
            if row.claim_id in claim_ids and row.target_claim_id in claim_ids
        ]

    def has_table(self, name: str) -> bool:
        return name == "relation_edge"

    def grounding_bundle(self):
        if self._grounding_bundle is None:
            self._grounding_bundle = _read_branch_grounding_bundle(
                self._repo,
                self._commit,
            )
        return self._grounding_bundle


def _read_branch_grounding_bundle(repo, commit: str | None):
    from propstore.sidecar.build import build_grounding_sidecar
    from propstore.sidecar.rules import read_grounded_bundle
    from propstore.sidecar.sqlite import connect_sidecar

    with tempfile.TemporaryDirectory(prefix="propstore-branch-sidecar-") as temp_dir:
        sidecar_path = Path(temp_dir) / "propstore.sqlite"
        build_grounding_sidecar(repo, sidecar_path, commit_hash=commit)
        conn = connect_sidecar(sidecar_path)
        try:
            return read_grounded_bundle(conn)
        finally:
            conn.close()


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


def _summary_claim_provenance(active_claims: list[MergeClaim]) -> dict[str, dict[str, Any]]:
    provenance: dict[str, dict[str, Any]] = {}
    for claim in active_claims:
        raw_provenance = claim.provenance_payload()
        provenance[claim.artifact_id] = {
                str(key): _normalize_for_signature(value)
                for key, value in sorted(raw_provenance.items(), key=lambda item: str(item[0]))
        }
    return provenance


def _summary_content_signature(
    active_claims: list[MergeClaim],
    stance_rows: list[StanceRow],
) -> str:
    claims_payload = []
    for claim in active_claims:
        claims_payload.append(_normalize_for_signature(claim.to_payload()))
    claims_payload.sort(
        key=lambda payload: str(payload.get("artifact_id", ""))
    )

    stances_payload = [
        {
            "claim_id": str(row.claim_id),
            "target_claim_id": str(row.target_claim_id),
            "stance_type": row.stance_type,
            "target_justification_id": (
                None if row.target_justification_id is None else str(row.target_justification_id)
            ),
            "attributes": _normalize_for_signature(dict(row.attributes)),
        }
        for row in stance_rows
    ]
    stances_payload.sort(
        key=lambda payload: (
            payload["claim_id"],
            payload["target_claim_id"],
            payload["stance_type"],
            payload["target_justification_id"] or "",
            json.dumps(payload["attributes"], sort_keys=True),
        )
    )

    payload = {
        "claims": claims_payload,
        "stances": stances_payload,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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
    stance_rows: list[StanceRow],
) -> list[StanceRow]:
    in_scope_claim_ids = {
        to_claim_id(claim.artifact_id)
        for claim in active_claims
    }
    canonical_rows = [
        row
        for row in stance_rows
        if row.claim_id in in_scope_claim_ids and row.target_claim_id in in_scope_claim_ids
    ]
    canonical_rows.sort(
        key=lambda row: (
            str(row.claim_id),
            str(row.target_claim_id),
            row.stance_type,
            "" if row.target_justification_id is None else str(row.target_justification_id),
            json.dumps(_normalize_for_signature(dict(row.attributes)), sort_keys=True),
        )
    )
    return canonical_rows


def _load_branch_claims(snapshot: RepositorySnapshot, commit: str | None) -> list[MergeClaim]:
    active_claims: list[MergeClaim] = []
    for claim_file in snapshot.repo.families.claims.iter_handles(commit=commit):
        for claim in claim_file_claims(claim_file):
            merge_claim = MergeClaim.from_document(claim)
            if merge_claim is not None:
                active_claims.append(merge_claim)
    return active_claims


def _inline_stance_rows(active_claims: list[MergeClaim]) -> list[StanceRow]:
    rows: list[StanceRow] = []
    for claim in active_claims:
        for stance in claim.document.stances:
            row = _stance_row_from_mapping(to_claim_id(claim.artifact_id), stance.to_payload())
            if row is not None:
                rows.append(row)
    return rows


def _file_stance_rows(snapshot: RepositorySnapshot, commit: str | None) -> list[StanceRow]:
    rows: list[StanceRow] = []
    for handle in snapshot.repo.families.stances.iter_handles(commit=commit):
        data = handle.document
        source_claim = _optional_string(data.source_claim)
        if source_claim is None:
            continue
        for stance in data.stances:
            row = _stance_row_from_mapping(to_claim_id(source_claim), stance.to_payload())
            if row is not None:
                rows.append(row)
    return rows


def build_branch_structured_summary(snapshot: RepositorySnapshot, branch: str) -> BranchStructuredSummary:
    commit = snapshot.branch_head(branch)
    active_claims = _load_branch_claims(snapshot, commit)
    raw_stance_rows = _inline_stance_rows(active_claims) + _file_stance_rows(snapshot, commit)
    stance_rows = _canonical_stance_rows(active_claims, raw_stance_rows)
    assertion_ids = _summary_assertion_ids(active_claims)
    claim_provenance = _summary_claim_provenance(active_claims)
    content_signature = _summary_content_signature(active_claims, stance_rows)
    if active_claims:
        snapshot_store = _BranchSnapshotStore(snapshot.repo, commit, stance_rows)
        projection = build_structured_projection(
            snapshot_store,
            [claim.to_payload(include_id_alias=True) for claim in active_claims],
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
        branch: summary.projection.framework
        for branch, summary in summaries.items()
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
