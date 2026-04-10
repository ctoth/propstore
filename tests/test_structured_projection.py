from __future__ import annotations

import json

import pytest
from click.testing import CliRunner
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.cli import cli
from propstore.structured_projection import (
    StructuredProjection,
    SupportQuality,
    build_structured_projection,
    compute_structured_justified_arguments,
)
from propstore.dung import ArgumentationFramework, grounded_extension
from propstore.world.bound import BoundWorld
from propstore.core.labels import Label, compile_environment_assumptions
from propstore.world.resolution import resolve
from propstore.world.types import Environment, ReasoningBackend, ResolutionStrategy
from propstore.worldline import WorldlineDefinition, run_worldline


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
        return name == "relation_edge" and self._has_stance_table

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
        str(claim.claim_id): bound.claim_support(claim)
        for claim in active_claims
    }


@st.composite
def _frameworks_with_optional_attacks(draw):
    n_args = draw(st.integers(min_value=1, max_value=4))
    arguments = tuple(f"arg:{idx}" for idx in range(n_args))
    possible_edges = [
        (src, tgt)
        for src in arguments
        for tgt in arguments
        if src != tgt
    ]
    if possible_edges:
        defeats = frozenset(
            draw(
                st.sets(
                    st.sampled_from(possible_edges),
                    max_size=len(possible_edges),
                )
            )
        )
    else:
        defeats = frozenset()
    attacks_choice = draw(st.sampled_from(["none", "same", "arbitrary"]))
    if attacks_choice == "none":
        attacks = None
    elif attacks_choice == "same":
        attacks = defeats
    else:
        attacks = (
            frozenset(
                draw(
                    st.sets(
                        st.sampled_from(possible_edges),
                        max_size=len(possible_edges),
                    )
                )
            )
            if possible_edges
            else frozenset()
        )
    return ArgumentationFramework(
        arguments=frozenset(arguments),
        defeats=defeats,
        attacks=attacks,
    )


def test_worldline_policy_rejects_removed_structured_projection_alias() -> None:
    with pytest.raises(ValueError, match="Unknown reasoning_backend"):
        WorldlineDefinition.from_dict({
            "id": "structured_backend",
            "targets": ["force"],
            "policy": {"reasoning_backend": "structured_projection"},
        })


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

    # Exactly one argument for claim_exact (arg_id format is bridge-internal)
    assert len(projection.arguments) == 1
    assert projection.arguments[0].claim_id == "claim_exact"
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

    # Find the supporter's base argument ID (bridge uses sequential IDs)
    supporter_arg_ids = set(projection.claim_to_argument_ids.get("claim_supporter", ()))
    target_arg_ids = set(projection.claim_to_argument_ids.get("claim_target", ()))

    derived_attackers = [
        argument.arg_id
        for argument in projection.arguments
        if argument.claim_id == "claim_attacker"
        and argument.premise_claim_ids == ("claim_supporter",)
        and supporter_arg_ids & set(argument.subargument_ids)
    ]

    assert derived_attackers
    assert any(
        (arg_id, target_id) in projection.framework.defeats
        for arg_id in derived_attackers
        for target_id in target_arg_ids
    )


def test_structured_projection_builds_real_premises_and_subargument_graphs() -> None:
    store = _ProjectionStore(
        claims=[
            {"id": "claim_a", "concept_id": "concept1", "type": "parameter", "value": 1.0},
            {"id": "claim_b", "concept_id": "concept2", "type": "parameter", "value": 2.0},
            {"id": "claim_c", "concept_id": "concept3", "type": "parameter", "value": 3.0},
        ],
        stances=[
            {"claim_id": "claim_a", "target_claim_id": "claim_b", "stance_type": "supports"},
            {"claim_id": "claim_b", "target_claim_id": "claim_c", "stance_type": "explains"},
        ],
    )

    projection = build_structured_projection(store, store.claims_for(None))
    by_claim = {}
    for argument in projection.arguments:
        by_claim.setdefault(argument.claim_id, []).append(argument)

    # Look up base argument IDs by claim (bridge uses sequential IDs)
    claim_a_arg_ids = set(projection.claim_to_argument_ids.get("claim_a", ()))
    claim_b_arg_ids = set(projection.claim_to_argument_ids.get("claim_b", ()))

    claim_b_args = by_claim["claim_b"]
    claim_c_args = by_claim["claim_c"]

    assert any(argument.premise_claim_ids == ("claim_a",) for argument in claim_b_args)
    assert any(argument.subargument_ids for argument in claim_b_args)
    assert any(argument.premise_claim_ids == ("claim_b",) for argument in claim_c_args)
    # Check subargument relationships by claim_id, not hardcoded arg_id format
    assert any(
        claim_b_arg_ids & set(argument.subargument_ids) for argument in claim_c_args
    )
    assert any(
        claim_a_arg_ids & set(argument.subargument_ids) for argument in claim_c_args
    )
    assert any(argument.justification_id == "supports:claim_a->claim_b" for argument in claim_b_args)
    assert any(argument.justification_id == "explains:claim_b->claim_c" for argument in claim_c_args)


def test_structured_projection_undermines_target_premise_dependent_arguments_not_base_claims() -> None:
    store = _ProjectionStore(
        claims=[
            {"id": "claim_target", "concept_id": "concept1", "type": "parameter", "value": 1.0},
            {"id": "claim_premise", "concept_id": "concept2", "type": "parameter", "value": 2.0},
            {"id": "claim_attacker", "concept_id": "concept3", "type": "parameter", "value": 3.0},
        ],
        stances=[
            {"claim_id": "claim_premise", "target_claim_id": "claim_target", "stance_type": "supports"},
            {"claim_id": "claim_attacker", "target_claim_id": "claim_premise", "stance_type": "undermines"},
        ],
    )

    projection = build_structured_projection(store, store.claims_for(None))
    attacker_args = projection.claim_to_argument_ids["claim_attacker"]
    # Find base args for claim_target (reported_claim / base_claim)
    target_base_args = [
        argument.arg_id
        for argument in projection.arguments
        if argument.claim_id == "claim_target" and argument.attackable_kind == "base_claim"
    ]
    # Find inference-rule args for claim_target (derived via support)
    target_inference_args = [
        argument.arg_id
        for argument in projection.arguments
        if argument.claim_id == "claim_target" and argument.attackable_kind == "inference_rule"
    ]

    assert target_inference_args, "Expected inference-rule arguments for claim_target"
    # Undermines targets premise-dependent arguments, not base claims
    assert all(
        (source_arg, target_arg) not in projection.framework.defeats
        for source_arg in attacker_args
        for target_arg in target_base_args
    )
    assert any(
        (source_arg, target_arg) in projection.framework.defeats
        for source_arg in attacker_args
        for target_arg in target_inference_args
    )


def test_structured_projection_undercuts_target_inference_rules_not_base_claims() -> None:
    store = _ProjectionStore(
        claims=[
            {"id": "claim_target", "concept_id": "concept1", "type": "parameter", "value": 1.0},
            {"id": "claim_support", "concept_id": "concept2", "type": "parameter", "value": 2.0},
            {"id": "claim_attacker", "concept_id": "concept3", "type": "parameter", "value": 3.0},
        ],
        stances=[
            {"claim_id": "claim_support", "target_claim_id": "claim_target", "stance_type": "supports"},
            {"claim_id": "claim_attacker", "target_claim_id": "claim_target", "stance_type": "undercuts"},
        ],
    )

    projection = build_structured_projection(store, store.claims_for(None))
    attacker_args = projection.claim_to_argument_ids["claim_attacker"]
    # Find base args for claim_target (reported_claim / base_claim)
    target_base_args = [
        argument.arg_id
        for argument in projection.arguments
        if argument.claim_id == "claim_target" and argument.attackable_kind == "base_claim"
    ]
    # Find inference-rule args for claim_target (derived via support)
    target_inference_args = [
        argument.arg_id
        for argument in projection.arguments
        if argument.claim_id == "claim_target" and argument.attackable_kind == "inference_rule"
    ]

    assert target_inference_args, "Expected inference-rule arguments for claim_target"
    # Undercuts targets inference rules, not base claims
    assert all(
        (source_arg, target_arg) not in projection.framework.defeats
        for source_arg in attacker_args
        for target_arg in target_base_args
    )
    assert any(
        (source_arg, target_arg) in projection.framework.defeats
        for source_arg in attacker_args
        for target_arg in target_inference_args
    )


def test_undercut_does_not_bleed_across_alternative_justifications_for_same_claim() -> None:
    store = _ProjectionStore(
        claims=[
            {"id": "claim_target", "concept_id": "concept1", "type": "parameter", "value": 1.0},
            {"id": "claim_support_a", "concept_id": "concept2", "type": "parameter", "value": 2.0},
            {"id": "claim_support_b", "concept_id": "concept3", "type": "parameter", "value": 3.0},
            {"id": "claim_attacker", "concept_id": "concept4", "type": "parameter", "value": 4.0},
        ],
        stances=[
            {"claim_id": "claim_support_a", "target_claim_id": "claim_target", "stance_type": "supports"},
            {"claim_id": "claim_support_b", "target_claim_id": "claim_target", "stance_type": "supports"},
            {
                "claim_id": "claim_attacker",
                "target_claim_id": "claim_target",
                "stance_type": "undercuts",
                "target_justification_id": "supports:claim_support_a->claim_target",
            },
        ],
    )

    projection = build_structured_projection(store, store.claims_for(None))
    attacker_args = projection.claim_to_argument_ids["claim_attacker"]
    target_support_a_args = [
        argument.arg_id
        for argument in projection.arguments
        if argument.claim_id == "claim_target"
        and argument.justification_id == "supports:claim_support_a->claim_target"
    ]
    target_support_b_args = [
        argument.arg_id
        for argument in projection.arguments
        if argument.claim_id == "claim_target"
        and argument.justification_id == "supports:claim_support_b->claim_target"
    ]

    assert target_support_a_args, "Expected an inference argument for support_a -> target"
    assert target_support_b_args, "Expected an inference argument for support_b -> target"
    assert any(
        (source_arg, target_arg) in projection.framework.defeats
        for source_arg in attacker_args
        for target_arg in target_support_a_args
    )
    assert all(
        (source_arg, target_arg) not in projection.framework.defeats
        for source_arg in attacker_args
        for target_arg in target_support_b_args
    )


@given(extra_support_count=st.integers(min_value=1, max_value=3))
@settings(deadline=None)
def test_named_undercut_property_only_defeats_the_selected_rule_arguments(
    extra_support_count: int,
) -> None:
    claims = [
        {"id": "claim_target", "concept_id": "concept1", "type": "parameter", "value": 1.0},
        {"id": "claim_attacker", "concept_id": "conceptX", "type": "parameter", "value": 9.0},
    ]
    stances = []
    targeted_justification_id = "supports:claim_support_0->claim_target"

    for idx in range(extra_support_count + 1):
        support_id = f"claim_support_{idx}"
        claims.append({
            "id": support_id,
            "concept_id": f"concept_support_{idx}",
            "type": "parameter",
            "value": float(idx + 2),
        })
        stances.append({
            "claim_id": support_id,
            "target_claim_id": "claim_target",
            "stance_type": "supports",
        })

    stances.append({
        "claim_id": "claim_attacker",
        "target_claim_id": "claim_target",
        "stance_type": "undercuts",
        "target_justification_id": targeted_justification_id,
    })

    projection = build_structured_projection(
        _ProjectionStore(claims=claims, stances=stances),
        claims,
    )
    attacker_args = projection.claim_to_argument_ids["claim_attacker"]

    for argument in projection.arguments:
        if argument.claim_id != "claim_target" or not argument.justification_id.startswith("supports:"):
            continue
        is_targeted = argument.justification_id == targeted_justification_id
        for attacker_arg in attacker_args:
            has_defeat = (attacker_arg, argument.arg_id) in projection.framework.defeats
            assert has_defeat is is_targeted


def test_structured_projection_defaults_unconditional_claim_to_exact_empty_label() -> None:
    store = _ProjectionStore(
        claims=[
            {"id": "claim_unconditional", "concept_id": "concept1", "type": "parameter", "value": 1.0}
        ]
    )

    projection = build_structured_projection(store, store.claims_for(None))

    assert projection.arguments[0].label == Label.empty()
    assert projection.arguments[0].support_quality == SupportQuality.EXACT


def test_build_structured_projection_threads_link_to_aspic_bridge(monkeypatch) -> None:
    calls: list[dict] = []

    def fake_build_aspic_projection(*args, **kwargs):
        calls.append(kwargs)
        return type(
            "FakeProjection",
            (),
            {
                "arguments": (),
                "framework": ArgumentationFramework(
                    arguments=frozenset(),
                    defeats=frozenset(),
                    attacks=frozenset(),
                ),
                "claim_to_argument_ids": {},
                "argument_to_claim_id": {},
            },
        )()

    monkeypatch.setattr(
        "propstore.aspic_bridge.build_aspic_projection",
        fake_build_aspic_projection,
    )

    store = _ProjectionStore(
        claims=[{"id": "claim_a", "concept_id": "concept1", "type": "parameter", "value": 1.0}]
    )

    build_structured_projection(
        store,
        store.claims_for(None),
        comparison="democratic",
        link="weakest",
    )

    assert calls
    assert calls[0]["comparison"] == "democratic"
    assert calls[0]["link"] == "weakest"


@given(
    comparison=st.sampled_from(["elitist", "democratic"]),
    link=st.sampled_from(["last", "weakest"]),
)
@settings(deadline=None)
def test_build_structured_projection_property_threads_selected_preference_config(
    comparison: str,
    link: str,
) -> None:
    calls: list[dict] = []

    def fake_build_aspic_projection(*args, **kwargs):
        calls.append(kwargs)
        return type(
            "FakeProjection",
            (),
            {
                "arguments": (),
                "framework": ArgumentationFramework(
                    arguments=frozenset(),
                    defeats=frozenset(),
                    attacks=frozenset(),
                ),
                "claim_to_argument_ids": {},
                "argument_to_claim_id": {},
            },
        )()

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "propstore.aspic_bridge.build_aspic_projection",
            fake_build_aspic_projection,
        )

        store = _ProjectionStore(
            claims=[{"id": "claim_a", "concept_id": "concept1", "type": "parameter", "value": 1.0}]
        )

        build_structured_projection(
            store,
            store.claims_for(None),
            comparison=comparison,
            link=link,
        )

    assert calls
    assert calls[0]["comparison"] == comparison
    assert calls[0]["link"] == link


def test_grounded_semantics_uses_plain_dung_grounded_even_when_attacks_exist() -> None:
    projection = StructuredProjection(
        arguments=(),
        framework=ArgumentationFramework(
            arguments=frozenset({"arg:a", "arg:b"}),
            defeats=frozenset(),
            attacks=frozenset({
                ("arg:a", "arg:b"),
                ("arg:b", "arg:a"),
            }),
        ),
        claim_to_argument_ids={},
        argument_to_claim_id={},
    )

    justified = compute_structured_justified_arguments(
        projection,
        semantics="grounded",
    )

    assert justified == frozenset({"arg:a", "arg:b"})


def test_grounded_semantics_has_single_canonical_meaning() -> None:
    projection = StructuredProjection(
        arguments=(),
        framework=ArgumentationFramework(
            arguments=frozenset({"arg:a", "arg:b"}),
            defeats=frozenset(),
            attacks=frozenset({
                ("arg:a", "arg:b"),
                ("arg:b", "arg:a"),
            }),
        ),
        claim_to_argument_ids={},
        argument_to_claim_id={},
    )

    grounded = compute_structured_justified_arguments(
        projection,
        semantics="grounded",
    )

    assert grounded == frozenset({"arg:a", "arg:b"})


def test_structured_projection_rejects_claim_graph_only_semantics() -> None:
    projection = StructuredProjection(
        arguments=(),
        framework=ArgumentationFramework(
            arguments=frozenset({"arg:a", "arg:b"}),
            defeats=frozenset(),
            attacks=frozenset(),
        ),
        claim_to_argument_ids={},
        argument_to_claim_id={},
    )

    with pytest.raises(ValueError, match="does not support semantics"):
        compute_structured_justified_arguments(
            projection,
            semantics="d-preferred",
        )


@given(framework=_frameworks_with_optional_attacks())
@settings(deadline=None)
def test_grounded_semantics_property_matches_dung_grounded_extension(
    framework: ArgumentationFramework,
) -> None:
    projection = StructuredProjection(
        arguments=(),
        framework=framework,
        claim_to_argument_ids={},
        argument_to_claim_id={},
    )

    justified = compute_structured_justified_arguments(
        projection,
        semantics="grounded",
    )

    expected_framework = framework
    if framework.attacks is not None and framework.attacks != framework.defeats:
        expected_framework = ArgumentationFramework(
            arguments=framework.arguments,
            defeats=framework.defeats,
        )
    expected = grounded_extension(expected_framework)

    assert justified == expected


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
        reasoning_backend=ReasoningBackend.ASPIC,
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
        reasoning_backend=ReasoningBackend.ASPIC,
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
        raise AssertionError("claim_graph capture should not run for aspic")

    monkeypatch.setattr(
        "propstore.claim_graph.compute_claim_graph_justified_claims",
        _unexpected_claim_graph,
    )

    result = run_worldline(
        WorldlineDefinition.from_dict({
            "id": "structured_argumentation_capture",
            "targets": ["target"],
            "inputs": {"bindings": {"task": "speech"}},
            "policy": {
                "strategy": "argumentation",
                "reasoning_backend": "aspic",
            },
        }),
        world,
    )

    assert result.values["target"]["value"] == 1.0
    assert result.argumentation is not None
    assert result.argumentation["backend"] == "aspic"
    assert result.argumentation["justified"] == ["external_c", "target_a"]


def test_world_extensions_cli_accepts_aspic_backend(monkeypatch) -> None:
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
        raise AssertionError("claim_graph path should not run for --backend aspic")

    monkeypatch.setattr("propstore.cli.Repository.find", lambda start=None: FakeRepo())
    monkeypatch.setattr("propstore.world.WorldModel", FakeWorldModel)
    monkeypatch.setattr(
        "propstore.claim_graph.compute_claim_graph_justified_claims",
        _unexpected_claim_graph,
    )
    monkeypatch.setattr(
        "propstore.relation_analysis.stance_summary",
        lambda *args, **kwargs: {
            "total_stances": 0,
            "included_as_attacks": 0,
            "vacuous_count": 0,
            "excluded_non_attack": 0,
            "models": [],
        },
    )
    monkeypatch.setattr(
        "propstore.structured_projection.build_structured_projection",
        lambda *args, **kwargs: FakeProjection(),
    )
    monkeypatch.setattr(
        "propstore.structured_projection.compute_structured_justified_arguments",
        lambda projection, *, semantics="grounded", backend=None: frozenset({"arg:target_a"}),
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["world", "extensions", "--backend", "aspic"])

    assert result.exit_code == 0
    assert "Backend: aspic" in result.output
    assert "Accepted (1 claims):" in result.output
    assert "target_a: target = 1.0" in result.output


def test_world_extensions_cli_rejects_structured_projection_backend_name() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["world", "extensions", "--backend", "structured_projection"])

    assert result.exit_code != 0
    assert "Invalid value for '--backend'" in result.output
