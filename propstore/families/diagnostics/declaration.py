"""Build diagnostic model helpers."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, CharterIndex, FamilyCharter, FamilyModel
from quire.families import FamilyDefinition
from sqlalchemy import delete, select

from quire.sqlalchemy_store import DerivedSession
from propstore.families.meta.declaration import _WORLD_CONTRACT_VERSION

if TYPE_CHECKING:
    from propstore.families.claims.stages import PromotionBlockedClaimFact
    from propstore.semantic_passes.types import PassDiagnostic


class BuildDiagnostic(FamilyModel):
    pass


DIAGNOSTICS_CHARTER: FamilyCharter = FamilyCharter(
        family=FamilyDefinition(
            key="build_diagnostics",
            name="build_diagnostics",
            contract_version=_WORLD_CONTRACT_VERSION,
            artifact_family=ArtifactFamily(
                name="propstore-world-build_diagnostics",
                contract_version=_WORLD_CONTRACT_VERSION,
                doc_type=BuildDiagnostic,
                placement=FlatYamlPlacement(".derived/build_diagnostics", str),
            ),
            identity_field="id",
        ),
        model=BuildDiagnostic,
        fields=(
            CharterField("id", int, primary_key=True, nullable=False),
            CharterField("claim_id", str),
            CharterField("source_kind", str, nullable=False),
            CharterField("source_ref", str),
            CharterField("diagnostic_kind", str, nullable=False),
            CharterField("severity", str, nullable=False),
            CharterField("blocking", int, nullable=False),
            CharterField("message", str, nullable=False),
            CharterField("file", str),
            CharterField("detail_json", str),
        ),
        indexes=(
            CharterIndex("idx_build_diagnostics_claim", ("claim_id",)),
            CharterIndex("idx_build_diagnostics_kind", ("diagnostic_kind",)),
            CharterIndex("idx_build_diagnostics_source", ("source_kind", "source_ref")),
        ),
        semantic_metadata={"semantic": "propstore.world"},
    )


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


def build_pass_diagnostics(
    diagnostics: tuple[PassDiagnostic, ...],
    *,
    kind: str,
    diagnostic_kind: str,
    prefer_filename: bool = False,
) -> tuple[BuildDiagnostic, ...]:
    records: list[BuildDiagnostic] = []
    for diagnostic in diagnostics:
        if not diagnostic.is_error:
            continue
        artifact_id = (
            diagnostic.filename or diagnostic.artifact_id or "unknown"
            if prefer_filename
            else diagnostic.artifact_id or diagnostic.filename or "unknown"
        )
        records.append(
            quarantine_diagnostic(
                artifact_id=artifact_id,
                kind=kind,
                diagnostic_kind=diagnostic_kind,
                message=diagnostic.render(),
                file=diagnostic.filename,
            )
        )
    return tuple(records)


def build_authoring_diagnostics(
    diagnostics: tuple[PassDiagnostic, ...],
) -> tuple[BuildDiagnostic, ...]:
    return tuple(
        BuildDiagnostic(
            claim_id=diagnostic.artifact_id,
            source_kind="authoring",
            source_ref=diagnostic.artifact_id or diagnostic.filename,
            diagnostic_kind=diagnostic.code,
            severity=diagnostic.level,
            blocking=1 if diagnostic.is_error else 0,
            message=diagnostic.render(),
            file=diagnostic.filename,
            detail_json=None,
        )
        for diagnostic in diagnostics
    )


def build_quarantine_diagnostics(
    diagnostics: tuple[object, ...],
) -> tuple[BuildDiagnostic, ...]:
    return tuple(
        quarantine_diagnostic(
            artifact_id=str(getattr(diagnostic, "artifact_id")),
            kind=str(getattr(diagnostic, "kind")),
            diagnostic_kind=str(getattr(diagnostic, "diagnostic_kind")),
            message=str(getattr(diagnostic, "message")),
            file=getattr(diagnostic, "file"),
        )
        for diagnostic in diagnostics
    )


def embedding_restore_diagnostic(exc: Exception) -> BuildDiagnostic:
    return BuildDiagnostic(
        claim_id=None,
        source_kind="embedding",
        source_ref="restore",
        diagnostic_kind="embedding_restore",
        severity="warning",
        blocking=0,
        message=f"embedding restore failed: {exc}",
        file=None,
        detail_json=None,
    )


def sidecar_build_exception_diagnostic(exc: Exception) -> BuildDiagnostic:
    return BuildDiagnostic(
        claim_id=None,
        source_kind="sidecar_build",
        source_ref=None,
        diagnostic_kind="build_exception",
        severity="error",
        blocking=1,
        message=str(exc),
        file=None,
        detail_json=None,
    )


def compile_promotion_blocked_diagnostics(
    facts: Sequence[PromotionBlockedClaimFact],
) -> tuple[BuildDiagnostic, ...]:
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
    table = derived.schema.table(DIAGNOSTICS_CHARTER.family.name)
    model = derived.schema.model(DIAGNOSTICS_CHARTER.family.name)
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
    table = derived.schema.table(DIAGNOSTICS_CHARTER.family.name)
    model = derived.schema.model(DIAGNOSTICS_CHARTER.family.name)
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
    table = derived.schema.table(DIAGNOSTICS_CHARTER.family.name)
    derived.session.execute(
        delete(table).where(
            table.c.claim_id == claim_id,
            table.c.diagnostic_kind == "promotion_blocked",
        )
    )
