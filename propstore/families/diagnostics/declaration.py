"""Build diagnostic model helpers."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select

from quire.sqlalchemy_store import DerivedSession

if TYPE_CHECKING:
    from propstore.families.claims.stages import PromotionBlockedClaimFact
    from propstore.families.world_charters import BuildDiagnostic


@dataclass(frozen=True)
class QuarantineDiagnostic:
    artifact_id: str
    kind: str
    diagnostic_kind: str
    message: str
    file: str | None = None


def quarantine_diagnostic(
    *,
    artifact_id: str,
    kind: str,
    diagnostic_kind: str,
    message: str,
    file: str | None = None,
) -> BuildDiagnostic:
    from propstore.families.world_charters import BuildDiagnostic

    return BuildDiagnostic(
        claim_id=artifact_id if kind == "claim" else None,
        source_kind=kind,
        source_ref=artifact_id,
        diagnostic_kind=diagnostic_kind,
        severity="error",
        blocking=1,
        message=message,
        file=file,
        detail_json=json.dumps(
            {
                "artifact_id": artifact_id,
                "kind": kind,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
    )


def compile_promotion_blocked_diagnostics(
    facts: Sequence[PromotionBlockedClaimFact],
) -> tuple[BuildDiagnostic, ...]:
    from propstore.families.world_charters import BuildDiagnostic

    diagnostics: list[BuildDiagnostic] = []
    for fact in facts:
        for reason in fact.reasons:
            diagnostics.append(
                BuildDiagnostic(
                    claim_id=fact.artifact_id,
                    source_kind="claim",
                    source_ref=fact.source_ref,
                    diagnostic_kind="promotion_blocked",
                    severity="error",
                    blocking=1,
                    message=reason.detail,
                    file=None,
                    detail_json=json.dumps(
                        {
                            "reason_kind": reason.kind,
                            "source_branch": fact.source_branch,
                        },
                        sort_keys=True,
                    ),
                )
            )
    return tuple(diagnostics)


def source_status_diagnostics(
    derived: DerivedSession,
    *,
    claim_ids: Sequence[str],
    like_pattern: str,
) -> tuple[BuildDiagnostic, ...]:
    if not claim_ids:
        return ()
    table = derived.schema.table("build_diagnostics")
    model = derived.schema.model("build_diagnostics")
    rows = derived.session.scalars(
        select(model)
        .where(table.c.source_kind == "claim")
        .where(
            (table.c.claim_id.in_(tuple(claim_ids)))
            | (table.c.source_ref.like(like_pattern, escape="!"))
        )
        .order_by(table.c.id)
    )
    return tuple(rows)


def build_diagnostics(derived: DerivedSession) -> list[dict[str, Any]]:
    table = derived.schema.table("build_diagnostics")
    model = derived.schema.model("build_diagnostics")
    rows = derived.session.scalars(select(model).order_by(table.c.id))
    return [
        {
            "id": row.id,
            "claim_id": row.claim_id,
            "source_kind": row.source_kind,
            "source_ref": row.source_ref,
            "diagnostic_kind": row.diagnostic_kind,
            "severity": row.severity,
            "blocking": row.blocking,
            "message": row.message,
            "file": row.file,
            "detail_json": row.detail_json,
        }
        for row in rows
    ]


def delete_promotion_blocked_diagnostics(
    derived: DerivedSession,
    claim_id: str,
) -> None:
    table = derived.schema.table("build_diagnostics")
    derived.session.execute(
        delete(table).where(
            table.c.claim_id == claim_id,
            table.c.diagnostic_kind == "promotion_blocked",
        )
    )
