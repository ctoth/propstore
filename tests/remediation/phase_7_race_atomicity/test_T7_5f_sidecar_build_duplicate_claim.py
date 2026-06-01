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


def test_compile_claim_models_tolerates_duplicate_artifact_ids() -> None:
    models = compile_claim_models(
        _bundle(
            _make_claim_entry("ps:claim:shared0001", "paper-alpha"),
            _make_claim_entry("ps:claim:shared0001", "paper-alpha-variant"),
        ),
        concept_registry={},
    )

    assert [claim.id for claim in models.claims] == ["ps:claim:shared0001"]
    assert [payload.claim_id for payload in models.numeric_payloads] == [
        "ps:claim:shared0001"
    ]
    assert [payload.claim_id for payload in models.text_payloads] == [
        "ps:claim:shared0001"
    ]
    assert [payload.claim_id for payload in models.algorithm_payloads] == [
        "ps:claim:shared0001"
    ]
