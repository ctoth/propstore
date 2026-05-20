"""Claim semantic stage objects."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from propstore.claims import ClaimFileEntry
from propstore.compiler.context import CompilationContext
from propstore.compiler.ir import ClaimCompilationBundle

if TYPE_CHECKING:
    from quire.projections import ProjectionRow
    from propstore.families.diagnostics.declaration import QuarantineDiagnostic


class ClaimStage(StrEnum):
    AUTHORED = "claim.authored"
    CHECKED = "claim.checked"


@dataclass(frozen=True)
class ClaimAuthoredFiles:
    claim_files: tuple[ClaimFileEntry, ...]
    context: CompilationContext
    context_ids: frozenset[str] | None = None

    @classmethod
    def from_sequence(
        cls,
        claim_files: Sequence[ClaimFileEntry],
        context: CompilationContext,
        *,
        context_ids: set[str] | None = None,
    ) -> "ClaimAuthoredFiles":
        return cls(
            claim_files=tuple(claim_files),
            context=context,
            context_ids=None if context_ids is None else frozenset(context_ids),
        )


@dataclass(frozen=True)
class ClaimCheckedBundle:
    bundle: ClaimCompilationBundle
    raw_id_quarantine_records: tuple[RawIdQuarantineRecord, ...] = ()


@dataclass(frozen=True)
class ClaimSidecarRows:
    claim_core_rows: tuple["ProjectionRow", ...]
    numeric_payload_rows: tuple["ProjectionRow", ...]
    text_payload_rows: tuple["ProjectionRow", ...]
    algorithm_payload_rows: tuple["ProjectionRow", ...]
    claim_link_rows: tuple["ProjectionRow", ...]
    stance_rows: tuple["ProjectionRow", ...]
    quarantine_diagnostics: tuple["QuarantineDiagnostic", ...]


@dataclass(frozen=True)
class RawIdQuarantineSidecarRows:
    claim_rows: tuple["ProjectionRow", ...]
    diagnostic_rows: tuple[object, ...]


@dataclass(frozen=True)
class PromotionBlockedReason:
    kind: str
    detail: str


@dataclass(frozen=True)
class PromotionBlockedClaimFact:
    artifact_id: str
    source_branch: str
    source_paper: str
    raw_id: str
    reasons: tuple[PromotionBlockedReason, ...]

    @property
    def source_ref(self) -> str:
        return f"{self.source_branch}:{self.artifact_id}"


@dataclass(frozen=True)
class PromotionBlockedSidecarRows:
    claim_rows: tuple["ProjectionRow", ...]
    diagnostic_rows: tuple[object, ...]


@dataclass(frozen=True)
class RawIdQuarantineRecord:
    filename: str
    source_paper: str
    raw_id: str
    seq: int
    synthetic_id: str
    message: str

    @property
    def detail_json(self) -> str:
        return json.dumps(
            {
                "synthetic_id_basis": {
                    "scheme": "sha256(filename|raw_id|seq)",
                    "filename": self.filename,
                    "raw_id": self.raw_id,
                    "seq": self.seq,
                    "prefix": "quarantine:raw_id:",
                },
            },
            sort_keys=True,
        )
