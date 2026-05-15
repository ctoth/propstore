"""Typed source-branch status reports.

The source subsystem owns sidecar reads and promotion-status correlation. CLI
commands render these reports and map failures to Click errors.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from propstore.families.diagnostics.declaration import (
    has_build_diagnostics_table,
    select_source_status_diagnostic_rows,
)
from propstore.families.claims.declaration import select_source_promotion_claim_rows
from propstore.sidecar.sqlite import connect_sidecar
from propstore.source.common import source_branch_name


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


def inspect_source_status(store_path: Path, name: str) -> SourceStatusReport:
    branch = source_branch_name(name)

    conn = connect_sidecar(store_path)
    conn.row_factory = sqlite3.Row
    try:
        has_claim_core = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='claim_core'"
        ).fetchone() is not None
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
            claim_ids = [str(row["id"]) for row in claim_rows]
            diag_rows = select_source_status_diagnostic_rows(
                conn,
                claim_ids=claim_ids,
                like_pattern=like_pattern,
            )
            for diag in diag_rows:
                claim_id = diag["claim_id"]
                source_ref = diag["source_ref"]
                key = str(claim_id or str(source_ref or "").split(":", 1)[-1])
                diagnostics_by_claim.setdefault(key, []).append(
                    SourceStatusDiagnostic(
                        kind=str(diag["diagnostic_kind"]),
                        message=str(diag["message"]),
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
            claim_id=str(row["id"]),
            promotion_status=str(row["promotion_status"]),
            diagnostics=tuple(diagnostics_by_claim.get(str(row["id"]), ())),
        )
        for row in claim_rows
    )
    return SourceStatusReport(
        branch=branch,
        state=SourceStatusState.HAS_ROWS,
        rows=rows,
    )
