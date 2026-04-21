"""Quarantine writer for rule-5 sidecar gates.

The render-time filtering pattern in ``schema.py`` depends on refusing
less data at build time: rows with bad local payloads become blocking
``build_diagnostics`` entries instead of aborting the whole sidecar
build. This module packages that boundary so later gates share one
diagnostic-write path.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from propstore.sidecar.schema import create_build_diagnostics_table


@dataclass(frozen=True, slots=True)
class Written:
    artifact_id: str
    kind: str


@dataclass(frozen=True, slots=True)
class Quarantined:
    artifact_id: str
    kind: str
    diagnostic_id: int
    message: str


class QuarantinableWriter:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        create_build_diagnostics_table(conn)

    def try_write(
        self,
        *,
        artifact_id: str,
        kind: str,
        payload: object,
        write: Callable[[object], None] | None = None,
        diagnostic_kind: str | None = None,
        file: str | None = None,
    ) -> Written | Quarantined:
        """Write a payload or quarantine its failure as a diagnostic row."""
        try:
            if payload is None:
                raise ValueError("payload is None")
            if write is not None:
                write(payload)
        except Exception as exc:
            return self._quarantine(
                artifact_id=artifact_id,
                kind=kind,
                diagnostic_kind=diagnostic_kind or f"{kind}_quarantine",
                message=str(exc) or exc.__class__.__name__,
                file=file,
            )
        return Written(artifact_id=artifact_id, kind=kind)

    def quarantine(
        self,
        *,
        artifact_id: str,
        kind: str,
        diagnostic_kind: str,
        message: str,
        file: str | None = None,
    ) -> Quarantined:
        return self._quarantine(
            artifact_id=artifact_id,
            kind=kind,
            diagnostic_kind=diagnostic_kind,
            message=message,
            file=file,
        )

    def _quarantine(
        self,
        *,
        artifact_id: str,
        kind: str,
        diagnostic_kind: str,
        message: str,
        file: str | None,
    ) -> Quarantined:
        detail_json = json.dumps(
            {
                "artifact_id": artifact_id,
                "kind": kind,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        cursor = self._conn.execute(
            """
            INSERT INTO build_diagnostics (
                claim_id, source_kind, source_ref, diagnostic_kind,
                severity, blocking, message, file, detail_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id if kind == "claim" else None,
                kind,
                artifact_id,
                diagnostic_kind,
                "error",
                1,
                message,
                file,
                detail_json,
            ),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("build_diagnostics insert did not return a row id")
        return Quarantined(
            artifact_id=artifact_id,
            kind=kind,
            diagnostic_id=cursor.lastrowid,
            message=message,
        )
