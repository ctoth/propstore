"""Render-time resolution strategies (Phase 7a-world-C2).

Exercises ``propstore.world.resolution.resolve`` and its strategy helpers over
in-memory belief-space doubles. The ARGUMENTATION backends reuse the built
analyzers (claim-graph / ASPIC+ / structured / PrAF) and are driven here through
monkeypatched analyzer entry points so the dispatch logic is tested in isolation
from a concrete store. The ATMS strategy and any BoundWorld/concrete-store path
are deferred to later world-layer slices (see the skip markers below).
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from propstore.core.active_claims import ActiveClaim
from propstore.core.results import AnalyzerResult, ClaimProjection, ExtensionResult
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.world.resolution import (
    _resolve_claim_graph_argumentation,
    _resolve_recency,
    _resolve_sample_size,
    _resolve_structured_argumentation,
    resolve,
)
from propstore.world.types import (
    IntegrityConstraint,
    IntegrityConstraintKind,
    ReasoningBackend,
    RenderPolicy,
    ResolutionStrategy,
    ValueResult,
    ValueStatus,
)


def _claim(
    claim_id: str,
    *,
    concept_id: str = "concept1",
    value: float | None = 1.0,
    branch: str | None = None,
    date: str | None = None,
    sample_size: int | None = None,
) -> ActiveClaim:
    return ActiveClaim(
        claim_id=claim_id,
        concept_id=concept_id,
        value=value,
        branch=branch,
        date=date,
        sample_size=None if sample_size is None else float(sample_size),
    )


class _ConflictedView:
    """A belief-space double whose concept is always CONFLICTED."""

    def __init__(self, claims: list[ActiveClaim]) -> None:
        self._claims = claims

    def value_of(self, concept_id: str) -> ValueResult:
        return ValueResult(
            concept_id=concept_id,
            status=ValueStatus.CONFLICTED,
            claims=[
                claim for claim in self._claims if claim.concept_id == concept_id
            ],
        )

    def active_claims(self, concept_id: str | None = None) -> list[ActiveClaim]:
        if concept_id is None:
            return list(self._claims)
        return [claim for claim in self._claims if claim.concept_id == concept_id]


class _DeterminedView:
    def value_of(self, concept_id: str) -> ValueResult:
        return ValueResult(
            concept_id=concept_id,
            status=ValueStatus.DETERMINED,
            claims=[_claim("only", value=7.0)],
        )

    def active_claims(self, concept_id: str | None = None) -> list[ActiveClaim]:
        return [_claim("only", value=7.0)]


class _NoClaimsView:
    def value_of(self, concept_id: str) -> ValueResult:
        return ValueResult(concept_id=concept_id, status=ValueStatus.NO_CLAIMS)

    def active_claims(self, concept_id: str | None = None) -> list[ActiveClaim]:
        return []


class _ArgumentationWorld:
    """A minimal store double for the argumentation backends.

    ``stances_between`` returns a non-empty placeholder so the structured backend
    clears its "no stance data" guard and reaches the (monkeypatched) projection
    builder; the placeholder is never actually consumed because the builder is
    patched in every structured test.
    """

    def grounding_bundle(self) -> GroundedRulesBundle:
        return GroundedRulesBundle.empty()

    def stances_between(self, claim_ids: set[str]) -> tuple[object, ...]:
        return (object(),)


# --- RECENCY ---------------------------------------------------------------


def test_recency_helper_picks_newest_date() -> None:
    winner, reason = _resolve_recency(
        [
            _claim("old", date="2024-01-01"),
            _claim("new", date="2026-06-01"),
        ]
    )
    assert winner == "new"
    assert reason == "most recent: 2026-06-01"


def test_recency_helper_ties_are_conflicted() -> None:
    winner, reason = _resolve_recency(
        [
            _claim("a", date="2026-06-01"),
            _claim("b", date="2026-06-01"),
        ]
    )
    assert winner is None
    assert reason is not None
    assert reason.startswith("tied recency (2026-06-01)")


def test_recency_helper_no_dates_is_conflicted() -> None:
    winner, reason = _resolve_recency([_claim("a"), _claim("b")])
    assert winner is None
    assert reason == "no dates in provenance"


def test_recency_reads_typed_date_field() -> None:
    claim = _claim("p", date="2025-05-05")
    winner, reason = _resolve_recency([claim])
    assert winner == "p"
    assert reason == "most recent: 2025-05-05"


def test_recency_resolves_through_resolve() -> None:
    view = _ConflictedView(
        [
            _claim("old", value=1.0, date="2024-01-01"),
            _claim("new", value=2.0, date="2026-06-01"),
        ]
    )
    result = resolve(view, "concept1", strategy=ResolutionStrategy.RECENCY)
    assert result.status is ValueStatus.RESOLVED
    assert result.winning_claim_id == "new"
    assert result.value == 2.0


# --- SAMPLE_SIZE -----------------------------------------------------------


def test_sample_size_helper_picks_largest() -> None:
    winner, reason = _resolve_sample_size(
        [
            _claim("small", sample_size=10),
            _claim("big", sample_size=100),
        ]
    )
    assert winner == "big"
    assert reason == "largest sample_size: 100"


def test_sample_size_helper_ties_are_conflicted() -> None:
    winner, reason = _resolve_sample_size(
        [
            _claim("a", sample_size=50),
            _claim("b", sample_size=50),
        ]
    )
    assert winner is None
    assert reason is not None
    assert reason.startswith("tied sample_size (50)")


def test_sample_size_helper_no_values_is_conflicted() -> None:
    winner, reason = _resolve_sample_size([_claim("a"), _claim("b")])
    assert winner is None
    assert reason == "no sample_size values"


def test_sample_size_resolves_through_resolve() -> None:
    view = _ConflictedView(
        [
            _claim("small", value=1.0, sample_size=10),
            _claim("big", value=2.0, sample_size=100),
        ]
    )
    result = resolve(view, "concept1", strategy=ResolutionStrategy.SAMPLE_SIZE)
    assert result.status is ValueStatus.RESOLVED
    assert result.winning_claim_id == "big"
    assert result.value == 2.0


# --- OVERRIDE / status passthrough / no-strategy ---------------------------


def test_override_selects_named_claim() -> None:
    view = _ConflictedView(
        [_claim("a", value=1.0), _claim("b", value=2.0)]
    )
    result = resolve(
        view,
        "concept1",
        strategy=ResolutionStrategy.OVERRIDE,
        policy=RenderPolicy(
            strategy=ResolutionStrategy.OVERRIDE, overrides={"concept1": "b"}
        ),
    )
    assert result.status is ValueStatus.RESOLVED
    assert result.winning_claim_id == "b"
    assert result.value == 2.0


def test_override_to_inactive_claim_raises() -> None:
    view = _ConflictedView([_claim("a", value=1.0)])
    with pytest.raises(ValueError, match="not an active claim"):
        resolve(
            view,
            "concept1",
            strategy=ResolutionStrategy.OVERRIDE,
            overrides={"concept1": "ghost"},
        )


def test_determined_passes_through() -> None:
    result = resolve(_DeterminedView(), "concept1", strategy=ResolutionStrategy.RECENCY)
    assert result.status is ValueStatus.DETERMINED
    assert result.value == 7.0


def test_no_claims_passes_through() -> None:
    result = resolve(_NoClaimsView(), "concept1", strategy=ResolutionStrategy.RECENCY)
    assert result.status is ValueStatus.NO_CLAIMS


def test_no_strategy_stays_conflicted() -> None:
    view = _ConflictedView(
        [_claim("a", value=1.0), _claim("b", value=2.0)]
    )
    result = resolve(view, "concept1")
    assert result.status is ValueStatus.CONFLICTED
    assert result.reason == "no resolution strategy configured"


# --- ARGUMENTATION: claim-graph backend ------------------------------------


def test_claim_graph_resolution_distinguishes_skeptical_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "propstore.core.analyzers.shared_analyzer_input_from_store",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        "propstore.core.analyzers.analyze_claim_graph",
        lambda *args, **kwargs: AnalyzerResult(
            backend="claim_graph",
            semantics="preferred",
            extensions=(
                ExtensionResult(name="preferred:1", accepted_claim_ids=("claim_a",)),
                ExtensionResult(name="preferred:2", accepted_claim_ids=("claim_b",)),
            ),
            projection=ClaimProjection(
                target_claim_ids=("claim_a", "claim_b"),
                survivor_claim_ids=(),
                witness_claim_ids=("claim_a", "claim_b"),
            ),
        ),
    )

    winner, reason = _resolve_claim_graph_argumentation(
        [_claim("claim_a"), _claim("claim_b", value=2.0)],
        [_claim("claim_a"), _claim("claim_b", value=2.0)],
        _ArgumentationWorld(),
        semantics="preferred",
    )

    assert winner is None
    assert reason == "no skeptically accepted claim in preferred extensions"


def test_claim_graph_resolution_distinguishes_no_stable_extension(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "propstore.core.analyzers.shared_analyzer_input_from_store",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        "propstore.core.analyzers.analyze_claim_graph",
        lambda *args, **kwargs: AnalyzerResult(
            backend="claim_graph",
            semantics="stable",
            extensions=(),
        ),
    )

    winner, reason = _resolve_claim_graph_argumentation(
        [_claim("claim_a"), _claim("claim_b", value=2.0)],
        [_claim("claim_a"), _claim("claim_b", value=2.0)],
        _ArgumentationWorld(),
        semantics="stable",
    )

    assert winner is None
    assert reason == "no stable extensions"


def test_claim_graph_resolution_sole_survivor_wins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "propstore.core.analyzers.shared_analyzer_input_from_store",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        "propstore.core.analyzers.analyze_claim_graph",
        lambda *args, **kwargs: AnalyzerResult(
            backend="claim_graph",
            semantics="grounded",
            extensions=(
                ExtensionResult(name="grounded", accepted_claim_ids=("claim_a",)),
            ),
            projection=ClaimProjection(
                target_claim_ids=("claim_a", "claim_b"),
                survivor_claim_ids=("claim_a",),
                witness_claim_ids=("claim_a",),
            ),
        ),
    )

    result = resolve(
        _ConflictedView(
            [_claim("claim_a", value=1.0), _claim("claim_b", value=2.0)]
        ),
        "concept1",
        strategy=ResolutionStrategy.ARGUMENTATION,
        world=_ArgumentationWorld(),
        reasoning_backend=ReasoningBackend.CLAIM_GRAPH,
    )
    assert result.status is ValueStatus.RESOLVED
    assert result.winning_claim_id == "claim_a"


def test_argumentation_without_store_stays_conflicted() -> None:
    view = _ConflictedView(
        [_claim("a", value=1.0), _claim("b", value=2.0)]
    )
    result = resolve(
        view,
        "concept1",
        strategy=ResolutionStrategy.ARGUMENTATION,
        reasoning_backend=ReasoningBackend.CLAIM_GRAPH,
    )
    assert result.status is ValueStatus.CONFLICTED
    assert result.reason == "argumentation strategy requires an explicit artifact store"


# --- ARGUMENTATION: structured / ASPIC+ backend ----------------------------


def test_structured_resolution_distinguishes_skeptical_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection = SimpleNamespace(
        claim_to_argument_ids={"claim_a": ("arg:a",), "claim_b": ("arg:b",)},
        argument_to_claim_id={"arg:a": "claim_a", "arg:b": "claim_b"},
    )
    monkeypatch.setattr(
        "propstore.aspic_bridge.build_aspic_projection",
        lambda *args, **kwargs: projection,
    )
    monkeypatch.setattr(
        "propstore.structured_projection.compute_structured_justified_arguments",
        lambda *args, **kwargs: [frozenset({"arg:a"}), frozenset({"arg:b"})],
    )

    winner, reason = _resolve_structured_argumentation(
        [_claim("claim_a"), _claim("claim_b", value=2.0)],
        [_claim("claim_a"), _claim("claim_b", value=2.0)],
        SimpleNamespace(),
        _ArgumentationWorld(),
        semantics="preferred",
    )

    assert winner is None
    assert reason == "no skeptically accepted claim in preferred ASPIC+ projection"


def test_aspic_resolution_threads_link_to_build_aspic_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection = SimpleNamespace(
        claim_to_argument_ids={"claim_a": ("arg:a",), "claim_b": ("arg:b",)},
        argument_to_claim_id={"arg:a": "claim_a", "arg:b": "claim_b"},
    )
    calls: list[dict[str, Any]] = []

    def fake_build_aspic_projection(*args: Any, **kwargs: Any) -> SimpleNamespace:
        calls.append(kwargs)
        return projection

    monkeypatch.setattr(
        "propstore.aspic_bridge.build_aspic_projection", fake_build_aspic_projection
    )
    monkeypatch.setattr(
        "propstore.structured_projection.compute_structured_justified_arguments",
        lambda *args, **kwargs: frozenset({"arg:a"}),
    )

    result = resolve(
        _ConflictedView(
            [_claim("claim_a", value=1.0), _claim("claim_b", value=2.0)]
        ),
        "concept1",
        strategy=ResolutionStrategy.ARGUMENTATION,
        world=_ArgumentationWorld(),
        reasoning_backend=ReasoningBackend.ASPIC,
        policy=RenderPolicy(
            strategy=ResolutionStrategy.ARGUMENTATION,
            reasoning_backend=ReasoningBackend.ASPIC,
            link="weakest",
        ),
    )

    assert result.status is ValueStatus.RESOLVED
    assert calls
    assert calls[0]["link"] == "weakest"


# --- ARGUMENTATION: PrAF backend -------------------------------------------


def test_praf_resolution_picks_highest_acceptance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "propstore.core.analyzers.shared_analyzer_input_from_store",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        "propstore.core.analyzers.analyze_praf",
        lambda *args, **kwargs: AnalyzerResult(
            backend="praf",
            semantics="grounded",
            projection=ClaimProjection(
                target_claim_ids=("claim_a", "claim_b"),
                survivor_claim_ids=("claim_a",),
                witness_claim_ids=("claim_a",),
            ),
            metadata={
                "acceptance_probs": {"claim_a": 0.9, "claim_b": 0.2},
                "strategy_used": "exact",
            },
        ),
    )

    result = resolve(
        _ConflictedView(
            [_claim("claim_a", value=1.0), _claim("claim_b", value=2.0)]
        ),
        "concept1",
        strategy=ResolutionStrategy.ARGUMENTATION,
        world=_ArgumentationWorld(),
        reasoning_backend=ReasoningBackend.PRAF,
    )
    assert result.status is ValueStatus.RESOLVED
    assert result.winning_claim_id == "claim_a"
    assert result.acceptance_probs == {"claim_a": 0.9, "claim_b": 0.2}


# --- ASSIGNMENT_SELECTION_MERGE --------------------------------------------


def test_assignment_selection_merge_filters_with_explicit_range_constraint() -> None:
    """The explicit RANGE constraint excludes the out-of-range claim and the
    distance-minimising merge selects the in-range consensus.

    The concept-derived auto-constraint path the reference used is not portable
    yet (the rewrite ``Concept`` charter carries no range/form); the strategy is
    exercised here through a self-describing explicit policy constraint instead.
    """
    view = _ConflictedView(
        [
            _claim("claim_a", value=50.0),
            _claim("claim_b", value=10.0),
            _claim("claim_c", value=5.0),
        ]
    )
    result = resolve(
        view,
        "concept1",
        strategy=ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE,
        policy=RenderPolicy(
            strategy=ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE,
            integrity_constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.RANGE,
                    concept_ids=("concept1",),
                    metadata={"lower": 0.0, "upper": 20.0},
                ),
            ),
        ),
    )
    assert result.status is ValueStatus.RESOLVED
    assert result.winning_claim_id == "claim_b"
    assert result.value == 10.0


def test_assignment_selection_merge_reports_duplicate_source() -> None:
    view = _ConflictedView(
        [
            _claim("claim_a1", value=10.0, branch="a"),
            _claim("claim_a2", value=11.0, branch="a"),
        ]
    )
    result = resolve(
        view,
        "concept1",
        strategy=ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE,
        policy=RenderPolicy(strategy=ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE),
    )
    assert result.status is ValueStatus.CONFLICTED
    assert result.reason == "source 'a' has multiple active claims for concept 'concept1'"


def test_assignment_selection_merge_branch_filter_narrows_sources() -> None:
    view = _ConflictedView(
        [
            _claim("claim_a", value=10.0, branch="a"),
            _claim("claim_b", value=5.0, branch="b"),
        ]
    )
    result = resolve(
        view,
        "concept1",
        strategy=ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE,
        policy=RenderPolicy(
            strategy=ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE,
            branch_filter=("a",),
        ),
    )
    # Only branch "a" survives the filter, leaving a single source whose value is
    # the merge consensus.
    assert result.status is ValueStatus.RESOLVED
    assert result.value == 10.0


# --- ATMS strategy (deferred to 7a-world-B2) --------------------------------


@pytest.mark.skip(reason="ATMS engine lands in 7a-world-B2")
def test_atms_support_resolution() -> None:  # pragma: no cover - deferred
    raise NotImplementedError
