"""Claim semantic stage objects."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from propstore.claims import ClaimFileEntry
from propstore.compiler.context import CompilationContext
from propstore.compiler.ir import ClaimCompilationBundle


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
