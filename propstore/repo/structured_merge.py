"""Branch-local structured projection and exact merge candidates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml

from propstore.aspic_bridge import build_aspic_projection
from propstore.core.row_types import StanceRow
from propstore.dung import ArgumentationFramework
from propstore.structured_argument import StructuredProjection


@dataclass(frozen=True)
class BranchStructuredSummary:
    branch: str
    active_claims: tuple[dict[str, Any], ...]
    stance_rows: tuple[StanceRow, ...]
    projection: StructuredProjection


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


def _load_branch_claims(reader) -> list[dict[str, Any]]:
    from propstore.validate_claims import load_claim_files

    active_claims: list[dict[str, Any]] = []
    for claim_file in load_claim_files(None, reader=reader):
        active_claims.extend(claim_file.data.get("claims", []))
    return active_claims


def _inline_stance_rows(active_claims: list[dict[str, Any]]) -> list[StanceRow]:
    rows: list[StanceRow] = []
    for claim in active_claims:
        claim_id = claim.get("id")
        if not claim_id:
            continue
        for stance in claim.get("stances", []) or []:
            if not isinstance(stance, dict):
                continue
            target = stance.get("target")
            stance_type = stance.get("type")
            if not target or not stance_type:
                continue
            attributes: dict[str, Any] = {}
            target_justification_id: str | None = None
            for key, value in stance.items():
                if key in {"target", "type"} or value is None:
                    continue
                if key == "target_justification_id":
                    target_justification_id = str(value)
                    continue
                attributes[key] = value
            rows.append(
                StanceRow(
                    claim_id=str(claim_id),
                    target_claim_id=str(target),
                    stance_type=str(stance_type),
                    target_justification_id=target_justification_id,
                    attributes=attributes,
                )
            )
    return rows


def _file_stance_rows(reader) -> list[StanceRow]:
    rows: list[StanceRow] = []
    for _stem, raw in reader.list_yaml("stances"):
        data = yaml.safe_load(raw) or {}
        source_claim = data.get("source_claim")
        if not source_claim:
            continue
        for stance in data.get("stances", []) or []:
            if not isinstance(stance, dict):
                continue
            target = stance.get("target")
            stance_type = stance.get("type")
            if not target or not stance_type:
                continue
            attributes: dict[str, Any] = {}
            target_justification_id: str | None = None
            for key, value in stance.items():
                if key in {"target", "type"} or value is None:
                    continue
                if key == "target_justification_id":
                    target_justification_id = str(value)
                    continue
                attributes[key] = value
            rows.append(
                StanceRow(
                    claim_id=str(source_claim),
                    target_claim_id=str(target),
                    stance_type=str(stance_type),
                    target_justification_id=target_justification_id,
                    attributes=attributes,
                )
            )
    return rows


def build_branch_structured_summary(kr, branch: str) -> BranchStructuredSummary:
    from propstore.repo.branch import branch_head
    from propstore.tree_reader import GitTreeReader

    reader = GitTreeReader(kr, commit=branch_head(kr, branch))
    active_claims = _load_branch_claims(reader)
    stance_rows = _inline_stance_rows(active_claims) + _file_stance_rows(reader)
    if active_claims:
        projection = build_aspic_projection(_BranchSnapshotStore(stance_rows), active_claims)
    else:
        projection = _empty_projection()
    return BranchStructuredSummary(
        branch=branch,
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
