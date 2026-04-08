"""Branch-local structured projection and exact merge candidates."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import yaml

from propstore.aspic_bridge import build_aspic_projection
from propstore.core.id_types import ClaimId, JustificationId, to_claim_id, to_justification_id
from propstore.core.row_types import StanceRow
from propstore.dung import ArgumentationFramework
from propstore.knowledge_path import KnowledgePath
from propstore.structured_argument import StructuredProjection


@dataclass(frozen=True)
class BranchStructuredSummary:
    branch: str
    claim_ids: tuple[str, ...]
    claim_provenance: dict[str, dict[str, Any]]
    content_signature: str
    relation_surface: dict[str, str]
    lossiness: tuple[str, ...]
    active_claims: tuple[dict[str, Any], ...]
    stance_rows: tuple[StanceRow, ...]
    projection: StructuredProjection


@dataclass(frozen=True)
class _StructuredMergeClaimView:
    raw: dict[str, Any]
    claim_id: ClaimId
    stances: tuple[dict[str, Any], ...]


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


def _claim_view(claim: dict[str, Any]) -> _StructuredMergeClaimView | None:
    claim_id = _optional_string(claim.get("artifact_id"))
    if claim_id is None:
        return None
    raw_stances = claim.get("stances")
    if not isinstance(raw_stances, list):
        return _StructuredMergeClaimView(raw=claim, claim_id=to_claim_id(claim_id), stances=tuple())
    stances = tuple(stance for stance in raw_stances if isinstance(stance, dict))
    return _StructuredMergeClaimView(raw=claim, claim_id=to_claim_id(claim_id), stances=stances)


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

    return StanceRow(
        claim_id=source_claim_id,
        target_claim_id=to_claim_id(target),
        stance_type=stance_type,
        target_justification_id=target_justification_id,
        attributes=attributes,
    )


class _BranchSnapshotStore:
    def __init__(self, stance_rows: list[StanceRow]) -> None:
        self._stance_rows = list(stance_rows)

    def stances_between(self, claim_ids: set[str]) -> list[StanceRow]:
        return [
            row
            for row in self._stance_rows
            if row.claim_id in claim_ids and row.target_claim_id in claim_ids
        ]

    def has_table(self, name: str) -> bool:
        return name == "relation_edge"


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


def _summary_claim_ids(active_claims: list[dict[str, Any]]) -> tuple[str, ...]:
    claim_ids = [
        claim_view.claim_id
        for claim in active_claims
        if (claim_view := _claim_view(claim)) is not None
    ]
    return tuple(sorted(str(claim_id) for claim_id in claim_ids))


def _summary_claim_provenance(active_claims: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    provenance: dict[str, dict[str, Any]] = {}
    for claim in active_claims:
        claim_view = _claim_view(claim)
        if claim_view is None:
            continue
        raw_provenance = claim.get("provenance", {})
        if isinstance(raw_provenance, dict):
            provenance[str(claim_view.claim_id)] = {
                str(key): _normalize_for_signature(value)
                for key, value in sorted(raw_provenance.items(), key=lambda item: str(item[0]))
            }
        else:
            provenance[str(claim_view.claim_id)] = {}
    return provenance


def _summary_content_signature(
    active_claims: list[dict[str, Any]],
    stance_rows: list[StanceRow],
) -> str:
    claims_payload = []
    for claim in active_claims:
        claim_view = _claim_view(claim)
        if claim_view is None:
            continue
        claims_payload.append(
            _normalize_for_signature(claim_view.raw)
        )
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
    active_claims: list[dict[str, Any]],
    stance_rows: list[StanceRow],
) -> list[StanceRow]:
    in_scope_claim_ids = {
        to_claim_id(claim_id)
        for claim_id in _summary_claim_ids(active_claims)
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


def _load_branch_claims(claims_root: KnowledgePath) -> list[dict[str, Any]]:
    from propstore.validate_claims import load_claim_files

    active_claims: list[dict[str, Any]] = []
    for claim_file in load_claim_files(claims_root):
        for claim in claim_file.data.get("claims", []):
            if not isinstance(claim, dict):
                active_claims.append(claim)
                continue
            normalized = dict(claim)
            artifact_id = _optional_string(normalized.get("artifact_id"))
            if artifact_id is not None and "id" not in normalized:
                normalized["id"] = artifact_id
            active_claims.append(normalized)
    return active_claims


def _inline_stance_rows(active_claims: list[dict[str, Any]]) -> list[StanceRow]:
    rows: list[StanceRow] = []
    for claim in active_claims:
        claim_view = _claim_view(claim)
        if claim_view is None:
            continue
        for stance in claim_view.stances:
            row = _stance_row_from_mapping(claim_view.claim_id, stance)
            if row is not None:
                rows.append(row)
    return rows


def _file_stance_rows(stances_root: KnowledgePath) -> list[StanceRow]:
    rows: list[StanceRow] = []
    if not stances_root.is_dir():
        return rows
    for entry in stances_root.iterdir():
        if not entry.is_file() or entry.suffix != ".yaml":
            continue
        data = yaml.safe_load(entry.read_bytes()) or {}
        source_claim = _optional_string(data.get("source_claim"))
        if source_claim is None:
            continue
        for stance in data.get("stances", []) or []:
            if not isinstance(stance, dict):
                continue
            row = _stance_row_from_mapping(to_claim_id(source_claim), stance)
            if row is not None:
                rows.append(row)
    return rows


def build_branch_structured_summary(kr, branch: str) -> BranchStructuredSummary:
    from propstore.repo.branch import branch_head

    tree = kr.tree(commit=branch_head(kr, branch))
    active_claims = _load_branch_claims(tree / "claims")
    raw_stance_rows = _inline_stance_rows(active_claims) + _file_stance_rows(tree / "stances")
    stance_rows = _canonical_stance_rows(active_claims, raw_stance_rows)
    claim_ids = _summary_claim_ids(active_claims)
    claim_provenance = _summary_claim_provenance(active_claims)
    content_signature = _summary_content_signature(active_claims, stance_rows)
    if active_claims:
        projection = build_aspic_projection(_BranchSnapshotStore(stance_rows), active_claims)
    else:
        projection = _empty_projection()
    return BranchStructuredSummary(
        branch=branch,
        claim_ids=claim_ids,
        claim_provenance=claim_provenance,
        content_signature=content_signature,
        relation_surface=_summary_relation_surface(),
        lossiness=_summary_lossiness(),
        active_claims=tuple(active_claims),
        stance_rows=tuple(stance_rows),
        projection=projection,
    )


def build_structured_merge_candidates(
    kr,
    branch_a: str,
    branch_b: str,
    *,
    operator: str = "sum",
) -> list[ArgumentationFramework]:
    from propstore.repo.paf_merge import (
        leximax_merge_frameworks,
        max_merge_frameworks,
        sum_merge_frameworks,
    )

    summaries = {
        branch_a: build_branch_structured_summary(kr, branch_a),
        branch_b: build_branch_structured_summary(kr, branch_b),
    }
    profile = {
        branch: summary.projection.framework
        for branch, summary in summaries.items()
    }
    if operator == "sum":
        return sum_merge_frameworks(profile)
    if operator == "max":
        return max_merge_frameworks(profile)
    if operator == "leximax":
        return leximax_merge_frameworks(profile)
    raise ValueError(f"Unknown structured merge operator: {operator}")


__all__ = [
    "BranchStructuredSummary",
    "build_branch_structured_summary",
    "build_structured_merge_candidates",
]
