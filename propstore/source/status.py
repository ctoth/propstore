"""Typed source-branch status reports.

The source subsystem owns sidecar reads and promotion-status correlation. CLI
commands render these reports and map failures to Click errors.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from importlib import import_module
from typing import Any
from quire.derived_store import DerivedStoreHandle

from propstore.families.claims.declaration import source_branch_promotion_status_rows
from propstore.families.registry import SOURCE_BRANCH, SourceRef, world_schema


class SourceStatusState(str, Enum):
    CLAIM_CORE_MISSING = "claim_core_missing"
    NO_ROWS = "no_rows"
    HAS_ROWS = "has_rows"


@dataclass(frozen=True)
class SourceStatusDiagnostic:
    kind: str
    message: str


@dataclass(frozen=True)
class SourceStatusRow:
    claim_id: str
    promotion_status: str
    diagnostics: tuple[SourceStatusDiagnostic, ...]


@dataclass(frozen=True)
class SourceStatusReport:
    branch: str
    state: SourceStatusState
    rows: tuple[SourceStatusRow, ...] = ()


def _source_status_diagnostics(*args: object, **kwargs: object) -> Iterable[Any]:
    diagnostics = import_module("propstore.families.diagnostics.declaration")
    return diagnostics.source_status_diagnostics(*args, **kwargs)


def _escape_sql_like(value: str) -> str:
    return value.replace("!", "!!").replace("%", "!%").replace("_", "!_")


def inspect_source_status(handle: DerivedStoreHandle, name: str) -> SourceStatusReport:
    branch = SOURCE_BRANCH.branch_name(handle, SourceRef(name))

    schema = world_schema()
    with handle.readonly_session(schema) as derived:
        claim_rows = source_branch_promotion_status_rows(
            derived,
            branch=branch,
        )
        diagnostics_by_claim: dict[str, list[SourceStatusDiagnostic]] = {}
        if claim_rows:
            like_pattern = f"{_escape_sql_like(branch)}:%"
            claim_ids = [row.claim_id for row in claim_rows]
            diag_rows = _source_status_diagnostics(
                derived,
                claim_ids=claim_ids,
                like_pattern=like_pattern,
            )
            for diag in diag_rows:
                claim_id = getattr(diag, "claim_id", None)
                source_ref = getattr(diag, "source_ref", None)
                key = str(claim_id or str(source_ref or "").split(":", 1)[-1])
                diagnostics_by_claim.setdefault(key, []).append(
                    SourceStatusDiagnostic(
                        kind=str(getattr(diag, "diagnostic_kind")),
                        message=str(getattr(diag, "message")),
                    )
                )

    if not claim_rows:
        return SourceStatusReport(
            branch=branch,
            state=SourceStatusState.NO_ROWS,
        )

    rows = tuple(
        SourceStatusRow(
            claim_id=row.claim_id,
            promotion_status=row.promotion_status,
            diagnostics=tuple(diagnostics_by_claim.get(row.claim_id, ())),
        )
        for row in claim_rows
    )
    return SourceStatusReport(
        branch=branch,
        state=SourceStatusState.HAS_ROWS,
        rows=rows,
    )
