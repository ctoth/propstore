"""Typed source-branch status reports.

The source subsystem owns sidecar reads and promotion-status correlation. CLI
commands render these reports and map failures to Click errors.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import Enum

from propstore.repository import Repository
from propstore.source.common import source_branch_name


class SourceStatusState(str, Enum):
    SIDECAR_MISSING = "sidecar_missing"
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


def inspect_source_status(repo: Repository, name: str) -> SourceStatusReport:
    branch = source_branch_name(name)
    if not repo.sidecar_path.exists():
        return SourceStatusReport(
            branch=branch,
            state=SourceStatusState.SIDECAR_MISSING,
        )

    conn = sqlite3.connect(repo.sidecar_path)
    conn.row_factory = sqlite3.Row
    try:
        has_claim_core = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='claim_core'"
        ).fetchone() is not None
        has_diagnostics = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='build_diagnostics'"
        ).fetchone() is not None
        if not has_claim_core:
            return SourceStatusReport(
                branch=branch,
                state=SourceStatusState.CLAIM_CORE_MISSING,
            )

        claim_rows = conn.execute(
            """
            SELECT id, promotion_status
            FROM claim_core
            WHERE branch = ? AND promotion_status IS NOT NULL
            ORDER BY id
            """,
            (branch,),
        ).fetchall()

        diagnostics_by_claim: dict[str, list[SourceStatusDiagnostic]] = {}
        if has_diagnostics:
            like_pattern = f"{branch}:%"
            diag_rows = conn.execute(
                """
                SELECT claim_id, source_ref, diagnostic_kind, blocking, message
                FROM build_diagnostics
                WHERE source_kind = 'claim'
                  AND (claim_id IN (
                    SELECT id FROM claim_core
                    WHERE branch = ? AND promotion_status IS NOT NULL
                  ) OR source_ref LIKE ?)
                ORDER BY id
                """,
                (branch, like_pattern),
            ).fetchall()
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
