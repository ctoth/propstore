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


def test_compile_claim_models_reports_same_logical_id_different_version() -> None:
    models = compile_claim_models(
        _bundle(
            _claim_entry("ps:claim:shared", version_id="sha256:first"),
            _claim_entry("ps:claim:shared", version_id="sha256:second"),
        ),
        concept_registry={},
    )

    assert [claim.version_id for claim in models.claims] == ["sha256:first"]
    assert [
        (diagnostic.artifact_id, diagnostic.diagnostic_kind)
        for diagnostic in models.quarantine_diagnostics
    ] == [("ps:claim:shared", "claim_version_conflict")]


def test_compile_claim_models_dedupes_duplicate_claim_concept_links() -> None:
    models = compile_claim_models(
        _bundle(
            _claim_entry("ps:claim:linked", version_id="sha256:same"),
            _claim_entry("ps:claim:linked", version_id="sha256:same"),
        ),
        concept_registry={},
    )

    assert [
        (link.claim_id, link.concept_id, link.role.value, link.ordinal)
        for link in models.concept_links
    ] == [("ps:claim:linked", "ps:concept:velocity", "about", 0)]
