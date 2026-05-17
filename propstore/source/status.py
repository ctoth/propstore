"""Typed source-branch status reports.

The source subsystem owns sidecar reads and promotion-status correlation. CLI
commands render these reports and map failures to Click errors.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from quire.derived_store import DerivedStoreHandle

from propstore.families.diagnostics.declaration import (
    has_build_diagnostics_table,
    select_source_status_diagnostic_rows,
)
from propstore.families.claims.declaration import (
    has_claim_core_table,
    select_source_promotion_claim_rows,
)
from propstore.families.registry import SOURCE_BRANCH, SourceRef


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

    conn = handle.open_readonly()
    try:
        has_claim_core = has_claim_core_table(conn)
        has_diagnostics = has_build_diagnostics_table(conn)
        if not has_claim_core:
            return SourceStatusReport(
                branch=branch,
                state=SourceStatusState.CLAIM_CORE_MISSING,
            )

        claim_rows = select_source_promotion_claim_rows(conn, branch)

        diagnostics_by_claim: dict[str, list[SourceStatusDiagnostic]] = {}
        if has_diagnostics and claim_rows:
            like_pattern = f"{_escape_sql_like(branch)}:%"
            claim_ids = [claim_id for claim_id, _promotion_status in claim_rows]
            diag_rows = select_source_status_diagnostic_rows(
                conn,
                claim_ids=claim_ids,
                like_pattern=like_pattern,
            )
            for diag in diag_rows:
                claim_id = diag.claim_id
                source_ref = diag.source_ref
                key = str(claim_id or str(source_ref or "").split(":", 1)[-1])
                diagnostics_by_claim.setdefault(key, []).append(
                    SourceStatusDiagnostic(
                        kind=diag.diagnostic_kind,
                        message=diag.message,
                    )
                )
    finally:
        conn.close()

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
