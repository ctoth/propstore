"""Typed source-branch status reports.

The source subsystem owns sidecar reads and promotion-status correlation. CLI
commands render these reports and map failures to Click errors.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from sqlalchemy import select
from quire.derived_store import DerivedStoreHandle

from propstore.families.diagnostics.declaration import (
    source_status_diagnostics,
)
from propstore.families.registry import SOURCE_BRANCH, SourceRef
from propstore.families.world_charters import world_sqlalchemy_schema


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


def _escape_sql_like(value: str) -> str:
    return value.replace("!", "!!").replace("%", "!%").replace("_", "!_")


def inspect_source_status(handle: DerivedStoreHandle, name: str) -> SourceStatusReport:
    branch = SOURCE_BRANCH.branch_name(handle, SourceRef(name))

    schema = world_sqlalchemy_schema()
    with handle.readonly_session(schema) as derived:
        claim_core = derived.schema.table("claim_core")
        claim_rows = tuple(
            (
                str(row.id),
                "ready" if row.promotion_status is None else str(row.promotion_status),
            )
            for row in derived.session.execute(
                select(claim_core.c.id, claim_core.c.promotion_status)
                .where(claim_core.c.branch == branch)
                .order_by(claim_core.c.seq, claim_core.c.id)
            )
        )
        diagnostics_by_claim: dict[str, list[SourceStatusDiagnostic]] = {}
        if claim_rows:
            like_pattern = f"{_escape_sql_like(branch)}:%"
            claim_ids = [claim_id for claim_id, _promotion_status in claim_rows]
            diag_rows = source_status_diagnostics(
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
            claim_id=claim_id,
            promotion_status=promotion_status,
            diagnostics=tuple(diagnostics_by_claim.get(claim_id, ())),
        )
        for claim_id, promotion_status in claim_rows
    )
    return SourceStatusReport(
        branch=branch,
        state=SourceStatusState.HAS_ROWS,
        rows=rows,
    )
