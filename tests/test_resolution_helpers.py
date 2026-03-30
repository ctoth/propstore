from __future__ import annotations

from types import SimpleNamespace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.core.results import AnalyzerResult, ClaimProjection, ExtensionResult
from propstore.dung import ArgumentationFramework
from propstore.world.resolution import (
    _resolve_claim_graph_argumentation,
    _resolve_structured_argumentation,
    resolve,
)
from propstore.world.types import ReasoningBackend, RenderPolicy, ResolutionStrategy, ValueResult
from propstore.world.types import IntegrityConstraint, IntegrityConstraintKind


class _World:
    def has_table(self, name: str) -> bool:
        return name == "relation_edge"


class _View:
    pass


class _AspicView:
    def __init__(self) -> None:
        self._claims = [
            {"id": "claim_a", "concept_id": "concept1", "value": 1.0},
            {"id": "claim_b", "concept_id": "concept1", "value": 2.0},
        ]

    def value_of(self, concept_id: str):
        return ValueResult(
            concept_id=concept_id,
            status="conflicted",
            claims=list(self._claims),
        )

    def active_claims(self, concept_id: str | None = None):
        if concept_id is None:
            return list(self._claims)
        return [claim for claim in self._claims if claim["concept_id"] == concept_id]

    def claim_support(self, claim: dict):
        return None, None


class _ICMergeWorld:
    def __init__(self, *, lower: float, upper: float) -> None:
        self._concept = {
            "id": "concept1",
            "canonical_name": "concept1",
            "form": "quantity",
            "form_parameters": None,
            "range_min": lower,
            "range_max": upper,
        }

    def get_concept(self, concept_id: str) -> dict | None:
        if concept_id != "concept1":
            return None
        return dict(self._concept)


class _GlobalICMergeWorld:
    def __init__(self) -> None:
        self._concepts = {
            "concept1": {
                "id": "concept1",
                "canonical_name": "x",
                "form": "quantity",
                "form_parameters": None,
                "range_min": None,
                "range_max": None,
            },
            "concept2": {
                "id": "concept2",
                "canonical_name": "y",
                "form": "quantity",
                "form_parameters": None,
                "range_min": None,
                "range_max": None,
            },
        }

    def get_concept(self, concept_id: str) -> dict | None:
        concept = self._concepts.get(concept_id)
        return None if concept is None else dict(concept)


class _GlobalICMergeView:
    def __init__(self) -> None:
        self._claims = [
            {"id": "claim_ax", "concept_id": "concept1", "value": 1.0, "branch": "a"},
            {"id": "claim_ay", "concept_id": "concept2", "value": 0.0, "branch": "a"},
            {"id": "claim_bx", "concept_id": "concept1", "value": 1.0, "branch": "b"},
            {"id": "claim_by", "concept_id": "concept2", "value": 1.0, "branch": "b"},
            {"id": "claim_cx", "concept_id": "concept1", "value": 0.0, "branch": "c"},
            {"id": "claim_cy", "concept_id": "concept2", "value": 0.0, "branch": "c"},
        ]

    def value_of(self, concept_id: str):
        return ValueResult(
            concept_id=concept_id,
            status="conflicted",
            claims=[claim for claim in self._claims if claim["concept_id"] == concept_id],
        )

    def active_claims(self, concept_id: str | None = None):
        if concept_id is None:
            return list(self._claims)
        return [claim for claim in self._claims if claim["concept_id"] == concept_id]


class _DuplicateSourceICMergeView:
    def __init__(self) -> None:
        self._claims = [
            {"id": "claim_a1", "concept_id": "concept1", "value": 10.0, "branch": "a"},
            {"id": "claim_a2", "concept_id": "concept1", "value": 11.0, "branch": "a"},
            {"id": "claim_b1", "concept_id": "concept1", "value": 12.0, "branch": "b"},
        ]

    def value_of(self, concept_id: str):
        return ValueResult(
            concept_id=concept_id,
            status="conflicted",
            claims=[claim for claim in self._claims if claim["concept_id"] == concept_id],
        )

    def active_claims(self, concept_id: str | None = None):
        if concept_id is None:
            return list(self._claims)
        return [claim for claim in self._claims if claim["concept_id"] == concept_id]


class _ICMergeView:
    def __init__(self) -> None:
        self._claims = [
            {"id": "claim_a", "concept_id": "concept1", "value": 50.0},
            {"id": "claim_b", "concept_id": "concept1", "value": 10.0},
            {"id": "claim_c", "concept_id": "concept1", "value": 5.0},
        ]

    def value_of(self, concept_id: str):
        return ValueResult(
            concept_id=concept_id,
            status="conflicted",
            claims=list(self._claims),
        )

    def active_claims(self, concept_id: str | None = None):
        if concept_id is None:
            return list(self._claims)
        return [claim for claim in self._claims if claim["concept_id"] == concept_id]


def test_claim_graph_resolution_distinguishes_skeptical_failure(monkeypatch) -> None:
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
        [{"id": "claim_a"}, {"id": "claim_b"}],
        [{"id": "claim_a"}, {"id": "claim_b"}],
        _World(),
        semantics="preferred",
    )

    assert winner is None
    assert reason == "no skeptically accepted claim in preferred extensions"


def test_claim_graph_resolution_distinguishes_no_stable_extension(monkeypatch) -> None:
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
        [{"id": "claim_a"}, {"id": "claim_b"}],
        [{"id": "claim_a"}, {"id": "claim_b"}],
        _World(),
        semantics="stable",
    )

    assert winner is None
    assert reason == "no stable extensions"


def test_structured_resolution_distinguishes_skeptical_failure(monkeypatch) -> None:
    projection = SimpleNamespace(
        claim_to_argument_ids={
            "claim_a": ("arg:a",),
            "claim_b": ("arg:b",),
        },
        argument_to_claim_id={
            "arg:a": "claim_a",
            "arg:b": "claim_b",
        },
    )
    monkeypatch.setattr(
        "propstore.structured_argument.build_structured_projection",
        lambda *args, **kwargs: projection,
    )
    monkeypatch.setattr(
        "propstore.structured_argument.compute_structured_justified_arguments",
        lambda *args, **kwargs: [frozenset({"arg:a"}), frozenset({"arg:b"})],
    )

    winner, reason = _resolve_structured_argumentation(
        [{"id": "claim_a"}, {"id": "claim_b"}],
        [{"id": "claim_a"}, {"id": "claim_b"}],
        _View(),
        _World(),
        semantics="preferred",
    )

    assert winner is None
    assert reason == "no skeptically accepted claim in preferred ASPIC+ projection"


def test_aspic_resolution_threads_link_to_build_aspic_projection(monkeypatch) -> None:
    projection = SimpleNamespace(
        claim_to_argument_ids={
            "claim_a": ("arg:a",),
            "claim_b": ("arg:b",),
        },
        argument_to_claim_id={
            "arg:a": "claim_a",
            "arg:b": "claim_b",
        },
    )
    calls: list[dict] = []

    def fake_build_aspic_projection(*args, **kwargs):
        calls.append(kwargs)
        return projection

    monkeypatch.setattr(
        "propstore.aspic_bridge.build_aspic_projection",
        fake_build_aspic_projection,
    )
    monkeypatch.setattr(
        "propstore.structured_argument.compute_structured_justified_arguments",
        lambda *args, **kwargs: frozenset({"arg:a"}),
    )

    result = resolve(
        _AspicView(),
        "concept1",
        strategy=ResolutionStrategy.ARGUMENTATION,
        world=_World(),
        reasoning_backend=ReasoningBackend.ASPIC,
        policy=RenderPolicy(
            strategy=ResolutionStrategy.ARGUMENTATION,
            reasoning_backend=ReasoningBackend.ASPIC,
            link="weakest",
        ),
    )

    assert result.status == "resolved"
    assert calls
    assert calls[0]["link"] == "weakest"


@given(
    comparison=st.sampled_from(["elitist", "democratic"]),
    link=st.sampled_from(["last", "weakest"]),
)
@settings(max_examples=8, deadline=None)
def test_aspic_resolution_property_threads_selected_preference_config(
    comparison: str,
    link: str,
) -> None:
    projection = SimpleNamespace(
        claim_to_argument_ids={
            "claim_a": ("arg:a",),
            "claim_b": ("arg:b",),
        },
        argument_to_claim_id={
            "arg:a": "claim_a",
            "arg:b": "claim_b",
        },
    )
    calls: list[dict] = []

    def fake_build_aspic_projection(*args, **kwargs):
        calls.append(kwargs)
        return projection

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "propstore.aspic_bridge.build_aspic_projection",
            fake_build_aspic_projection,
        )
        monkeypatch.setattr(
            "propstore.structured_argument.compute_structured_justified_arguments",
            lambda *args, **kwargs: frozenset({"arg:a"}),
        )

        result = resolve(
            _AspicView(),
            "concept1",
            strategy=ResolutionStrategy.ARGUMENTATION,
            world=_World(),
            reasoning_backend=ReasoningBackend.ASPIC,
            policy=RenderPolicy(
                strategy=ResolutionStrategy.ARGUMENTATION,
                reasoning_backend=ReasoningBackend.ASPIC,
                comparison=comparison,
                link=link,
            ),
        )

    assert result.status == "resolved"
    assert calls
    assert calls[0]["comparison"] == comparison
    assert calls[0]["link"] == link


def test_structured_resolution_grounded_uses_plain_grounded_extension(monkeypatch) -> None:
    projection = SimpleNamespace(
        framework=ArgumentationFramework(
            arguments=frozenset({"arg:a", "arg:b"}),
            defeats=frozenset(),
            attacks=frozenset({
                ("arg:a", "arg:b"),
                ("arg:b", "arg:a"),
            }),
        ),
        claim_to_argument_ids={
            "claim_a": ("arg:a",),
            "claim_b": ("arg:b",),
        },
        argument_to_claim_id={
            "arg:a": "claim_a",
            "arg:b": "claim_b",
        },
    )
    monkeypatch.setattr(
        "propstore.structured_argument.build_structured_projection",
        lambda *args, **kwargs: projection,
    )

    winner, reason = _resolve_structured_argumentation(
        [{"id": "claim_a"}],
        [{"id": "claim_a"}, {"id": "claim_b"}],
        _View(),
        _World(),
        semantics="grounded",
    )

    assert winner == "claim_a"
    assert reason == "sole ASPIC+ survivor in grounded extension"


def test_ic_merge_resolution_filters_with_range_mu() -> None:
    result = resolve(
        _ICMergeView(),
        "concept1",
        strategy=ResolutionStrategy.IC_MERGE,
        world=_ICMergeWorld(lower=0.0, upper=20.0),
        policy=RenderPolicy(strategy=ResolutionStrategy.IC_MERGE),
    )

    assert result.status == "resolved"
    assert result.winning_claim_id == "claim_b"
    assert result.value == 10.0


def test_ic_merge_resolution_reports_no_admissible_assignments() -> None:
    result = resolve(
        _ICMergeView(),
        "concept1",
        strategy=ResolutionStrategy.IC_MERGE,
        world=_ICMergeWorld(lower=0.0, upper=4.0),
        policy=RenderPolicy(strategy=ResolutionStrategy.IC_MERGE),
    )

    assert result.status == "conflicted"
    assert result.reason == "no admissible assignments"


def test_global_ic_merge_resolution_reads_target_from_global_assignment() -> None:
    result = resolve(
        _GlobalICMergeView(),
        "concept1",
        strategy=ResolutionStrategy.IC_MERGE,
        world=_GlobalICMergeWorld(),
        policy=RenderPolicy(
            strategy=ResolutionStrategy.IC_MERGE,
            integrity_constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CEL,
                    concept_ids=("concept1", "concept2"),
                    cel="x + y <= 0",
                ),
            ),
        ),
    )

    assert result.status == "resolved"
    assert result.winning_claim_id == "claim_cx"
    assert result.value == 0.0


def test_global_ic_merge_branch_filter_changes_sources_not_projection_logic() -> None:
    result = resolve(
        _GlobalICMergeView(),
        "concept1",
        strategy=ResolutionStrategy.IC_MERGE,
        world=_GlobalICMergeWorld(),
        policy=RenderPolicy(
            strategy=ResolutionStrategy.IC_MERGE,
            branch_filter=("a", "b"),
            integrity_constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CEL,
                    concept_ids=("concept1", "concept2"),
                    cel="x + y <= 0",
                ),
            ),
        ),
    )

    assert result.status == "conflicted"
    assert result.reason == "no admissible assignments"


def test_global_ic_merge_reports_duplicate_claims_per_source_explicitly() -> None:
    result = resolve(
        _DuplicateSourceICMergeView(),
        "concept1",
        strategy=ResolutionStrategy.IC_MERGE,
        world=_ICMergeWorld(lower=0.0, upper=20.0),
        policy=RenderPolicy(strategy=ResolutionStrategy.IC_MERGE),
    )

    assert result.status == "conflicted"
    assert result.reason == "source 'a' has multiple active claims for concept 'concept1'"
