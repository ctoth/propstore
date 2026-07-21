"""Core semantic-kernel value types: reasoning, results, labels."""

from __future__ import annotations

import pytest

from propstore.core.labels import (
    EnvironmentKey,
    Label,
    SupportQuality,
)
from propstore.core.reasoning import (
    ArgumentationSemantics,
    ReasoningBackend,
    supported_argumentation_semantics,
    validate_backend_semantics,
)
from propstore.core.results import AnalyzerResult, ClaimProjection, ExtensionResult


# ── reasoning ────────────────────────────────────────────────────────


def test_validate_backend_semantics_accepts_supported_pair() -> None:
    assert validate_backend_semantics("aspic", "grounded") == (
        ReasoningBackend.ASPIC,
        ArgumentationSemantics.GROUNDED,
    )


def test_validate_backend_semantics_normalizes_alias() -> None:
    backend, semantics = validate_backend_semantics(
        ReasoningBackend.CLAIM_GRAPH, "bipolar_stable"
    )
    assert backend is ReasoningBackend.CLAIM_GRAPH
    assert semantics is ArgumentationSemantics.BIPOLAR_STABLE


def test_validate_backend_semantics_rejects_unsupported_pair() -> None:
    with pytest.raises(ValueError):
        validate_backend_semantics("atms", "stable")


def test_atms_only_supports_grounded() -> None:
    assert supported_argumentation_semantics(ReasoningBackend.ATMS) == frozenset(
        {ArgumentationSemantics.GROUNDED}
    )


# ── labels ───────────────────────────────────────────────────────────


def test_label_empty_is_unconditional_environment() -> None:
    assert Label.empty().environments == (EnvironmentKey(()),)


def test_support_quality_members() -> None:
    assert {quality.value for quality in SupportQuality} == {
        "exact",
        "mixed",
        "context_visible_only",
        "semantic_compatible",
    }


# ── results ──────────────────────────────────────────────────────────


def test_extension_result_normalizes_accepted_claim_ids() -> None:
    result = ExtensionResult(
        name="grounded",
        accepted_claim_ids=("b", "a", "a"),
    )
    assert result.accepted_claim_ids == ("a", "b")


def test_analyzer_result_carries_label_and_metadata() -> None:
    result = AnalyzerResult(
        backend="aspic",
        semantics="grounded",
        extensions=(ExtensionResult(name="grounded", accepted_claim_ids=("a",)),),
        projection=ClaimProjection(target_claim_ids=("a",), survivor_claim_ids=("a",)),
        support_label=Label.empty(),
        metadata=(("k", "v"),),
    )
    assert result.extensions[0].accepted_claim_ids == ("a",)
    assert result.projection is not None
    assert result.projection.survivor_claim_ids == ("a",)
    assert result.metadata == (("k", "v"),)
