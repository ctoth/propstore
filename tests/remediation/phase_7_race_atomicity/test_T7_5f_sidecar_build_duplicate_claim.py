"""Regression test for duplicate claim identities during claim compilation."""

from __future__ import annotations

from quire.documents import LoadedDocument

from propstore.compiler.ir import (
    ClaimCompilationBundle,
    SemanticClaimFile,
)
from propstore.families.claims.declaration import compile_claim_models
from propstore.families.claims.declaration import ClaimDocument


def _bundle(*entries: LoadedDocument[ClaimDocument]) -> ClaimCompilationBundle:
    return ClaimCompilationBundle(
        context=None,
        normalized_claim_files=tuple(entries),
        semantic_files=tuple(
            SemanticClaimFile(
                loaded_entry=entry,
                normalized_entry=entry,
                claims=(_semantic_claim(entry),),
            )
            for entry in entries
        ),
    )
