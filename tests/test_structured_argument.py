from __future__ import annotations

import json

from click.testing import CliRunner

from propstore.cli import cli
from propstore.structured_argument import (
    SupportQuality,
    build_structured_projection,
)
from propstore.dung import ArgumentationFramework
from propstore.world.bound import BoundWorld
from propstore.world.labelled import Label, compile_environment_assumptions
from propstore.world.resolution import resolve
from propstore.world.types import Environment, ReasoningBackend, ResolutionStrategy
from propstore.worldline import WorldlineDefinition
from propstore.worldline_runner import run_worldline


class _ExactMatchSolver:
    def are_disjoint(self, left: list[str], right: list[str]) -> bool:
        return set(left).isdisjoint(right)


class _OverlapSolver:
    def are_disjoint(self, left: list[str], right: list[str]) -> bool:
        if "x == 1" in left and "x > 0" in right:
            return False
        if "x > 0" in left and "x == 1" in right:
            return False
        return set(left).isdisjoint(right)


class _LeafHierarchy:
    def ancestors(self, context_id: str) -> list[str]:
        return []


class _ProjectionStore:
    def __init__(
        self,
        *,
        claims: list[dict],
        stances: list[dict] | None = None,
        solver=None,
        has_stance_table: bool = True,
    ) -> None:
        self._claims = list(claims)
        self._stances = list(stances or [])
        self._solver = solver or _ExactMatchSolver()
        self._has_stance_table = has_stance_table

    def claims_for(self, concept_id: str | None) -> list[dict]:
        if concept_id is None:
            return list(self._claims)
        return [claim for claim in self._claims if claim.get("concept_id") == concept_id]

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, dict]:
        return {
            claim["id"]: claim
            for claim in self._claims
            if claim["id"] in claim_ids
        }

    def stances_between(self, claim_ids: set[str]) -> list[dict]:
        return [
            stance
            for stance in self._stances
            if stance["claim_id"] in claim_ids and stance["target_claim_id"] in claim_ids
        ]

    def has_table(self, name: str) -> bool:
        return name == "claim_stance" and self._has_stance_table

    def condition_solver(self):
        return self._solver

    def parameterizations_for(self, concept_id: str) -> list[dict]:
        return []

    def conflicts(self) -> list[dict]:
        return []

    def all_concepts(self) -> list[dict]:
        return []

    def explain(self, claim_id: str) -> list[dict]:
        return []

    def get_claim(self, claim_id: str) -> dict | None:
        return next((claim for claim in self._claims if claim["id"] == claim_id), None)


def _make_bound(
    store: _ProjectionStore,
    *,
    bindings: dict[str, object] | None = None,
    context_id: str | None = None,
    effective_assumptions: tuple[str, ...] = (),
    context_hierarchy=None,
) -> BoundWorld:
    bindings = bindings or {}
    environment = Environment(
        bindings=bindings,
        context_id=context_id,
        effective_assumptions=effective_assumptions,
        assumptions=compile_environment_assumptions(
            bindings=bindings,
            effective_assumptions=effective_assumptions,
            context_id=context_id,
        ),
    )
    return BoundWorld(
        store,
        environment=environment,
        context_hierarchy=context_hierarchy,
    )


def _support_metadata(bound: BoundWorld, active_claims: list[dict]) -> dict[str, tuple[Label | None, SupportQuality]]:
    return {
        claim["id"]: bound.claim_support(claim)
        for claim in active_claims
    }


def test_worldline_policy_accepts_structured_projection_backend() -> None:
    worldline = WorldlineDefinition.from_dict({
        "id": "structured_backend",
        "targets": ["force"],
        "policy": {"reasoning_backend": "structured_projection"},
    })

    assert worldline.policy.reasoning_backend == "structured_projection"


def test_structured_projection_uses_stable_argument_ids_and_exact_labels() -> None:
    store = _ProjectionStore(
        claims=[
            {
                "id": "claim_exact",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1"]),
            }
        ]
    )
    bound = _make_bound(store, bindings={"x": 1})
    active = bound.active_claims()

    projection = build_structured_projection(
        store,
        active,
        support_metadata=_support_metadata(bound, active),
    )

    assert tuple(argument.arg_id for argument in projection.arguments) == ("arg:claim_exact",)
    assert projection.arguments[0].support_quality == SupportQuality.EXACT
    assert projection.arguments[0].label == bound.value_of("concept1").label


def test_structured_projection_keeps_semantic_overlap_unlabeled() -> None:
    store = _ProjectionStore(
        claims=[
            {
                "id": "claim_overlap",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x > 0"]),
            }
        ],
        solver=_OverlapSolver(),
    )
    bound = _make_bound(store, bindings={"x": 1})
    active = bound.active_claims()

    projection = build_structured_projection(
        store,
        active,
        support_metadata=_support_metadata(bound, active),
    )

    assert projection.arguments[0].label is None
    assert projection.arguments[0].support_quality == SupportQuality.SEMANTIC_COMPATIBLE


def test_structured_projection_does_not_treat_context_scope_as_unconditional() -> None:
    store = _ProjectionStore(
        claims=[
            {
                "id": "claim_ctx",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": None,
                "context_id": "ctx_general",
            }
        ]
    )
    bound = _make_bound(
        store,
        context_id="ctx_general",
        effective_assumptions=("framework == 'general'",),
        context_hierarchy=_LeafHierarchy(),
    )
    active = bound.active_claims()

    projection = build_structured_projection(
        store,
        active,
        support_metadata=_support_metadata(bound, active),
    )

    assert projection.arguments[0].label is None
    assert projection.arguments[0].support_quality == SupportQuality.CONTEXT_VISIBLE_ONLY


def test_structured_projection_support_induces_additional_defeat_path() -> None:
    store = _ProjectionStore(
        claims=[
            {"id": "claim_target", "concept_id": "concept1", "type": "parameter", "value": 1.0},
            {"id": "claim_attacker", "concept_id": "concept2", "type": "parameter", "value": 2.0},
            {"id": "claim_supporter", "concept_id": "concept3", "type": "parameter", "value": 3.0},
        ],
        stances=[
            {"claim_id": "claim_attacker", "target_claim_id": "claim_target", "stance_type": "supersedes"},
            {"claim_id": "claim_supporter", "target_claim_id": "claim_attacker", "stance_type": "supports"},
        ],
    )

    projection = build_structured_projection(store, store.claims_for(None))

    assert ("arg:claim_supporter", "arg:claim_target") in projection.framework.defeats


def test_structured_projection_defaults_unconditional_claim_to_exact_empty_label() -> None:
    store = _ProjectionStore(
        claims=[
            {"id": "claim_unconditional", "concept_id": "concept1", "type": "parameter", "value": 1.0}
        ]
    )

    projection = build_structured_projection(store, store.claims_for(None))

    assert projection.arguments[0].label == Label.empty()
    assert projection.arguments[0].support_quality == SupportQuality.EXACT


def test_structured_resolution_reports_no_stance_data_like_claim_graph() -> None:
    store = _ProjectionStore(
        claims=[
            {"id": "target_a", "concept_id": "concept1", "type": "parameter", "value": 1.0},
            {"id": "target_b", "concept_id": "concept1", "type": "parameter", "value": 2.0},
        ],
        has_stance_table=False,
    )
    bound = _make_bound(store)

    result = resolve(
        bound,
        "concept1",
        ResolutionStrategy.ARGUMENTATION,
        world=store,
        reasoning_backend=ReasoningBackend.STRUCTURED_PROJECTION,
    )

    assert result.status == "conflicted"
    assert result.reason == "no stance data"


def test_structured_backend_matches_claim_graph_on_simple_deterministic_case() -> None:
    store = _ProjectionStore(
        claims=[
            {
                "id": "target_a",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["task == 'speech'"]),
            },
            {
                "id": "target_b",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["task == 'speech'"]),
            },
            {
                "id": "external_c",
                "concept_id": "concept2",
                "type": "observation",
                "statement": "External evidence defeats target_b.",
                "conditions_cel": json.dumps(["task == 'speech'"]),
            },
        ],
        stances=[
            {"claim_id": "target_b", "target_claim_id": "target_a", "stance_type": "supersedes"},
            {"claim_id": "external_c", "target_claim_id": "target_b", "stance_type": "supersedes"},
        ],
    )
    bound = _make_bound(store, bindings={"task": "speech"})

    claim_graph = resolve(
        bound,
        "concept1",
        ResolutionStrategy.ARGUMENTATION,
        world=store,
        reasoning_backend=ReasoningBackend.CLAIM_GRAPH,
    )
    structured = resolve(
        bound,
        "concept1",
        ResolutionStrategy.ARGUMENTATION,
        world=store,
        reasoning_backend=ReasoningBackend.STRUCTURED_PROJECTION,
    )

    assert claim_graph.status == "resolved"
    assert claim_graph.winning_claim_id == "target_a"
    assert structured.status == "resolved"
    assert structured.winning_claim_id == "target_a"


def test_structured_worldline_argumentation_capture_uses_structured_backend(monkeypatch) -> None:
    class StructuredWorld(_ProjectionStore):
        def bind(self, environment=None, *, policy=None, **conditions):
            bindings = dict(environment.bindings) if environment is not None else dict(conditions)
            return _make_bound(self, bindings=bindings)

        def resolve_concept(self, name: str) -> str | None:
            return "concept1" if name == "target" else None

        def get_concept(self, concept_id: str) -> dict | None:
            if concept_id == "concept1":
                return {"id": "concept1", "canonical_name": "target"}
            return None

    world = StructuredWorld(
        claims=[
            {
                "id": "target_a",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["task == 'speech'"]),
            },
            {
                "id": "target_b",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["task == 'speech'"]),
            },
            {
                "id": "external_c",
                "concept_id": "concept2",
                "type": "observation",
                "statement": "External evidence defeats target_b.",
                "conditions_cel": json.dumps(["task == 'speech'"]),
            },
        ],
        stances=[
            {"claim_id": "target_b", "target_claim_id": "target_a", "stance_type": "supersedes"},
            {"claim_id": "external_c", "target_claim_id": "target_b", "stance_type": "supersedes"},
        ],
    )

    def _unexpected_claim_graph(*args, **kwargs):
        raise AssertionError("claim_graph capture should not run for structured_projection")

    monkeypatch.setattr(
        "propstore.argumentation.compute_claim_graph_justified_claims",
        _unexpected_claim_graph,
    )

    result = run_worldline(
        WorldlineDefinition.from_dict({
            "id": "structured_argumentation_capture",
            "targets": ["target"],
            "inputs": {"bindings": {"task": "speech"}},
            "policy": {
                "strategy": "argumentation",
                "reasoning_backend": "structured_projection",
            },
        }),
        world,
    )

    assert result.values["target"]["value"] == 1.0
    assert result.argumentation is not None
    assert result.argumentation["backend"] == "structured_projection"
    assert result.argumentation["justified"] == ["external_c", "target_a"]


def test_world_extensions_cli_accepts_structured_projection_backend(monkeypatch) -> None:
    class FakeRepo:
        pass

    class FakeBound:
        def active_claims(self, concept_id: str | None = None) -> list[dict]:
            return [
                {"id": "target_a", "concept_id": "concept1", "type": "parameter", "value": 1.0},
                {"id": "target_b", "concept_id": "concept1", "type": "parameter", "value": 2.0},
            ]

        def claim_support(self, claim: dict) -> tuple[Label | None, SupportQuality]:
            return Label.empty(), SupportQuality.EXACT

    class FakeWorldModel:
        def __init__(self, repo) -> None:
            self.repo = repo

        def bind(self, environment=None, **conditions):
            return FakeBound()

        def get_concept(self, concept_id: str) -> dict | None:
            if concept_id == "concept1":
                return {"id": "concept1", "canonical_name": "target"}
            return None

        def stances_between(self, claim_ids: set[str]) -> list[dict]:
            return []

        def close(self) -> None:
            return None

    class FakeProjection:
        framework = ArgumentationFramework(
            arguments=frozenset({"arg:target_a", "arg:target_b"}),
            defeats=frozenset({("arg:target_a", "arg:target_b")}),
            attacks=frozenset({("arg:target_a", "arg:target_b")}),
        )
        claim_to_argument_ids = {
            "target_a": ("arg:target_a",),
            "target_b": ("arg:target_b",),
        }
        argument_to_claim_id = {
            "arg:target_a": "target_a",
            "arg:target_b": "target_b",
        }

    def _unexpected_claim_graph(*args, **kwargs):
        raise AssertionError("claim_graph path should not run for --backend structured_projection")

    monkeypatch.setattr("propstore.cli.Repository.find", lambda start=None: FakeRepo())
    monkeypatch.setattr("propstore.world.WorldModel", FakeWorldModel)
    monkeypatch.setattr(
        "propstore.argumentation.compute_claim_graph_justified_claims",
        _unexpected_claim_graph,
    )
    monkeypatch.setattr(
        "propstore.argumentation.stance_summary",
        lambda *args, **kwargs: {
            "total_stances": 0,
            "included_as_attacks": 0,
            "excluded_by_threshold": 0,
            "excluded_non_attack": 0,
            "models": [],
        },
    )
    monkeypatch.setattr(
        "propstore.structured_argument.build_structured_projection",
        lambda *args, **kwargs: FakeProjection(),
    )
    monkeypatch.setattr(
        "propstore.structured_argument.compute_structured_justified_arguments",
        lambda projection, *, semantics="grounded": frozenset({"arg:target_a"}),
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["world", "extensions", "--backend", "structured_projection"])

    assert result.exit_code == 0
    assert "Backend: structured_projection" in result.output
    assert "Accepted (1 claims):" in result.output
    assert "target_a: target = 1.0" in result.output
