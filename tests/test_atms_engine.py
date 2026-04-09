from __future__ import annotations

import json

from click.testing import CliRunner

from propstore.cli import cli
from propstore.world import BoundWorld
from propstore.core.labels import (
    EnvironmentKey,
    Label,
    SupportQuality,
    cel_to_binding,
    compile_environment_assumptions,
)
from propstore.world.resolution import resolve
from propstore.world.types import (
    ATMSNodeStatus,
    ATMSOutKind,
    Environment,
    QueryableAssumption,
    ReasoningBackend,
    RenderPolicy,
    ResolutionStrategy,
)
from propstore.worldline import WorldlineDefinition, run_worldline

from tests.atms_helpers import _ExactMatchSolver, _LeafHierarchy, _OverlapSolver


class _ATMSStore:
    def __init__(
        self,
        *,
        claims: list[dict],
        parameterizations: list[dict] | None = None,
        conflicts: list[dict] | None = None,
        solver=None,
    ) -> None:
        self._claims = list(claims)
        self._parameterizations = list(parameterizations or [])
        self._conflicts = list(conflicts or [])
        self._solver = solver or _ExactMatchSolver()

    def claims_for(self, concept_id: str | None) -> list[dict]:
        if concept_id is None:
            return list(self._claims)
        return [claim for claim in self._claims if claim.get("concept_id") == concept_id]

    def parameterizations_for(self, concept_id: str) -> list[dict]:
        return [
            row for row in self._parameterizations
            if row.get("output_concept_id") == concept_id
        ]

    def all_parameterizations(self) -> list[dict]:
        return list(self._parameterizations)

    def condition_solver(self):
        return self._solver

    def conflicts(self) -> list[dict]:
        return list(self._conflicts)

    def all_concepts(self) -> list[dict]:
        return []

    def explain(self, claim_id: str) -> list[dict]:
        return []

    def get_claim(self, claim_id: str) -> dict | None:
        return next((claim for claim in self._claims if claim["id"] == claim_id), None)

    def has_table(self, name: str) -> bool:
        return False

    def stances_between(self, claim_ids: set[str]) -> list[dict]:
        return []

    def resolve_concept(self, name: str) -> str | None:
        for claim in self._claims:
            if claim.get("concept_id") == name:
                return name
        return name if name.startswith("concept") else None

    def get_concept(self, concept_id: str) -> dict | None:
        return {"id": concept_id, "canonical_name": concept_id}


def _make_bound(
    store: _ATMSStore,
    *,
    bindings: dict[str, object] | None = None,
    context_id: str | None = None,
    effective_assumptions: tuple[str, ...] = (),
    solver=None,
) -> BoundWorld:
    if solver is not None:
        store._solver = solver
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
        context_hierarchy=_LeafHierarchy() if context_id is not None else None,
        policy=RenderPolicy(reasoning_backend=ReasoningBackend.ATMS),
    )


class _GraphOnlyATMSRuntime:
    """ATMS runtime surface with no BoundWorld implementation details."""

    def __init__(self, bound: BoundWorld) -> None:
        from propstore.core.activation import activate_compiled_world_graph
        from propstore.core.graph_build import build_compiled_world_graph

        self.environment = bound._environment
        self.active_graph = (
            bound._active_graph
            if bound._active_graph is not None
            else activate_compiled_world_graph(
                build_compiled_world_graph(bound._store),
                environment=bound._environment,
                solver=bound._store.condition_solver(),
                context_hierarchy=bound._context_hierarchy,
            )
        )
        self._bound = bound

    @staticmethod
    def _claim_node_to_row(claim_node) -> dict:
        row = {
            "id": claim_node.claim_id,
            "concept_id": claim_node.concept_id,
            "type": claim_node.claim_type,
            "value": claim_node.scalar_value,
        }
        row.update(dict(claim_node.attributes))
        return row

    def is_parameterization_compatible(self, conditions: tuple[str, ...]) -> bool:
        if not conditions:
            return True
        return self._bound.is_param_compatible(json.dumps(list(conditions)))

    def active_claims(self) -> list[dict]:
        compiled_claims = {
            claim.claim_id: claim
            for claim in self.active_graph.compiled.claims
        }
        return [
            self._claim_node_to_row(compiled_claims[claim_id])
            for claim_id in self.active_graph.active_claim_ids
            if claim_id in compiled_claims
        ]

    def conflicts(self) -> list[dict]:
        active_ids = set(self.active_graph.active_claim_ids)
        return [
            {
                "claim_a_id": conflict.left_claim_id,
                "claim_b_id": conflict.right_claim_id,
                "warning_class": conflict.kind,
                **dict(conflict.details),
            }
            for conflict in self.active_graph.compiled.conflicts
            if conflict.left_claim_id in active_ids and conflict.right_claim_id in active_ids
        ]

    def all_parameterizations(self) -> list[dict]:
        return [
            {
                "output_concept_id": edge.output_concept_id,
                "concept_ids": json.dumps(list(edge.input_concept_ids)),
                "formula": edge.formula,
                "sympy": edge.sympy,
                "exactness": edge.exactness,
                "conditions_cel": (None if not edge.conditions else json.dumps(list(edge.conditions))),
            }
            for edge in self.active_graph.compiled.parameterizations
        ]

    def is_param_compatible(self, conditions_cel: str | None) -> bool:
        return self._bound.is_param_compatible(conditions_cel)

    def claim_support(self, claim_row: dict) -> tuple[Label | None, SupportQuality]:
        return self._bound.claim_support(claim_row)

    def concept_status(self, concept_id: str) -> str:
        return self._bound.value_of(concept_id).status

    def replay(self, queryables: tuple[QueryableAssumption, ...]):
        bindings = dict(self.environment.bindings)
        for queryable in queryables:
            parsed = cel_to_binding(queryable.cel)
            if parsed is None:
                continue
            key, value = parsed
            bindings[key] = value
        future_bound = _make_bound(
            self._bound._store,
            bindings=bindings,
            context_id=self.environment.context_id,
            effective_assumptions=tuple(self.environment.effective_assumptions),
        )
        return _GraphOnlyATMSRuntime(future_bound)

    def __getattr__(self, name: str):
        raise AssertionError(f"ATMS graph runtime should not access BoundWorld internals: {name}")


def test_atms_propagates_combined_support_to_derived_node() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_x",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_y",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["y == 2"]),
            },
        ],
        parameterizations=[
            {
                "output_concept_id": "concept3",
                "concept_ids": json.dumps(["concept1", "concept2"]),
                "sympy": "Eq(concept3, concept1 + concept2)",
                "formula": "z = x + y",
                "conditions_cel": None,
            }
        ],
    )
    bound = _make_bound(store, bindings={"x": 1, "y": 2})
    assumption_ids = {
        assumption.cel: assumption.assumption_id
        for assumption in bound._environment.assumptions
    }

    result = bound.derived_value("concept3")

    assert result.status == "derived"
    assert result.value == 5.0
    assert result.label == Label(
        (
            EnvironmentKey(
                (
                    assumption_ids["x == 1"],
                    assumption_ids["y == 2"],
                )
            ),
        )
    )


def test_atms_nogoods_prune_derived_environments() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_x",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_y",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["y == 2"]),
            },
        ],
        parameterizations=[
            {
                "output_concept_id": "concept3",
                "concept_ids": json.dumps(["concept1", "concept2"]),
                "sympy": "Eq(concept3, concept1 + concept2)",
                "formula": "z = x + y",
                "conditions_cel": None,
            }
        ],
        conflicts=[
            {"claim_a_id": "claim_x", "claim_b_id": "claim_y", "concept_id": None},
        ],
    )
    bound = _make_bound(store, bindings={"x": 1, "y": 2})

    result = bound.derived_value("concept3")

    assert result.status == "derived"
    assert result.value == 5.0
    assert result.label is None
    assert bound.atms_engine().nogoods.environments


def test_atms_label_propagation_is_order_independent() -> None:
    parameterizations = [
        {
            "output_concept_id": "concept3",
            "concept_ids": json.dumps(["concept1", "concept2"]),
            "sympy": "Eq(concept3, concept1 + concept2)",
            "formula": "z = x + y",
            "conditions_cel": None,
        }
    ]
    claims = [
        {
            "id": "claim_x",
            "concept_id": "concept1",
            "type": "parameter",
            "value": 2.0,
            "conditions_cel": json.dumps(["x == 1"]),
        },
        {
            "id": "claim_y",
            "concept_id": "concept2",
            "type": "parameter",
            "value": 3.0,
            "conditions_cel": json.dumps(["y == 2"]),
        },
    ]

    forward = _make_bound(
        _ATMSStore(claims=claims, parameterizations=parameterizations),
        bindings={"x": 1, "y": 2},
    )
    reverse = _make_bound(
        _ATMSStore(claims=list(reversed(claims)), parameterizations=list(reversed(parameterizations))),
        bindings={"x": 1, "y": 2},
    )

    assert forward.derived_value("concept3").label == reverse.derived_value("concept3").label


def test_atms_cycle_does_not_bootstrap_support() -> None:
    store = _ATMSStore(
        claims=[],
        parameterizations=[
            {
                "output_concept_id": "concept1",
                "concept_ids": json.dumps(["concept2"]),
                "sympy": "Eq(concept1, concept2)",
                "formula": "a = b",
                "conditions_cel": None,
            },
            {
                "output_concept_id": "concept2",
                "concept_ids": json.dumps(["concept1"]),
                "sympy": "Eq(concept2, concept1)",
                "formula": "b = a",
                "conditions_cel": None,
            },
        ],
    )
    bound = _make_bound(store)

    assert bound.derived_value("concept1").status == "underspecified"
    assert bound.atms_engine().derived_label("concept1", 1.0) is None
    assert bound.atms_engine().supported_claim_ids() == set()


def test_atms_supported_claims_are_subset_of_active_claims_and_ignore_semantic_overlap() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_exact",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_semantic",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x > 0"]),
            },
        ],
        solver=_OverlapSolver(),
    )
    bound = _make_bound(store, bindings={"x": 1})

    active_ids = {claim["id"] for claim in bound.active_claims("concept1")}
    supported_ids = bound.atms_engine().supported_claim_ids("concept1")

    assert supported_ids == {"claim_exact"}
    assert supported_ids < active_ids

    result = resolve(
        bound,
        "concept1",
        ResolutionStrategy.ARGUMENTATION,
        world=store,
        reasoning_backend=ReasoningBackend.ATMS,
    )
    assert result.status == "determined"
    assert [claim["id"] for claim in result.claims] == ["claim_exact"]


def test_atms_does_not_fabricate_exact_support_from_context_visibility() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_ctx",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 7.0,
                "context_id": "ctx_general",
                "conditions_cel": None,
            }
        ]
    )
    bound = _make_bound(
        store,
        context_id="ctx_general",
        effective_assumptions=("framework == 'general'",),
    )

    assert {claim["id"] for claim in bound.active_claims("concept1")} == {"claim_ctx"}
    assert bound.atms_engine().supported_claim_ids("concept1") == set()
    assert bound.value_of("concept1").status == "no_claims"
    assert bound.value_of("concept1").label is None


def test_atms_reconstructs_exact_support_for_context_scoped_claim_with_matching_assumption() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_ctx_exact",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 7.0,
                "context_id": "ctx_general",
                "conditions_cel": json.dumps(["framework == 'general'"]),
            }
        ]
    )
    bound = _make_bound(
        store,
        context_id="ctx_general",
        effective_assumptions=("framework == 'general'",),
    )
    assumption_id = next(
        assumption.assumption_id
        for assumption in bound._environment.assumptions
        if assumption.cel == "framework == 'general'"
    )

    assert {claim["id"] for claim in bound.active_claims("concept1")} == {"claim_ctx_exact"}
    assert bound.atms_engine().supported_claim_ids("concept1") == {"claim_ctx_exact"}
    assert bound.atms_engine().claim_label("claim_ctx_exact") == Label(
        (EnvironmentKey((assumption_id,)),)
    )
    assert bound.value_of("concept1").status == "determined"


def test_atms_node_status_partition_and_support_quality_honesty() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_true",
                "concept_id": "concept0",
                "type": "parameter",
                "value": 0.0,
                "conditions_cel": None,
            },
            {
                "id": "claim_exact",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_semantic",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x > 0"]),
            },
        ],
        solver=_OverlapSolver(),
    )
    bound = _make_bound(store, bindings={"x": 1})

    true_status = bound.claim_status("claim_true")
    exact_status = bound.claim_status("claim_exact")
    semantic_status = bound.claim_status("claim_semantic")

    assert true_status.status == ATMSNodeStatus.TRUE
    assert exact_status.status == ATMSNodeStatus.IN
    assert exact_status.support_quality == SupportQuality.EXACT
    assert semantic_status.status == ATMSNodeStatus.OUT
    assert semantic_status.support_quality == SupportQuality.SEMANTIC_COMPATIBLE
    assert "semantic compatibility" in semantic_status.reason


def test_atms_essential_support_intersection_and_environment_queries_are_exact() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_x",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_y_a",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["y == 2"]),
            },
            {
                "id": "claim_y_b",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["z == 3"]),
            },
        ],
        parameterizations=[
            {
                "output_concept_id": "concept3",
                "concept_ids": json.dumps(["concept1", "concept2"]),
                "sympy": "Eq(concept3, concept1 + concept2)",
                "formula": "z = x + y",
                "conditions_cel": None,
            }
        ],
    )
    bound = _make_bound(store, bindings={"x": 1, "y": 2, "z": 3})
    engine = bound.atms_engine()
    derived = bound.derived_value("concept3")

    assert derived.status == "derived"

    assumption_ids = {
        assumption.cel: assumption.assumption_id
        for assumption in bound._environment.assumptions
    }
    derived_node_id = engine._derived_node_id("concept3", derived.value)
    essential_support = engine.essential_support(derived_node_id)

    assert essential_support == EnvironmentKey((assumption_ids["x == 1"],))

    visible_nodes = engine.nodes_in_environment(
        EnvironmentKey((
            assumption_ids["x == 1"],
            assumption_ids["y == 2"],
        ))
    )
    assert "claim:claim_x" in visible_nodes
    assert "claim:claim_y_a" in visible_nodes
    assert derived_node_id in visible_nodes
    assert "claim:claim_y_b" not in visible_nodes


def test_atms_explain_node_returns_real_justification_chains() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_x",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_y_a",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["y == 2"]),
            },
            {
                "id": "claim_y_b",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["z == 3"]),
            },
        ],
        parameterizations=[
            {
                "output_concept_id": "concept3",
                "concept_ids": json.dumps(["concept1", "concept2"]),
                "sympy": "Eq(concept3, concept1 + concept2)",
                "formula": "z = x + y",
                "conditions_cel": None,
            }
        ],
    )
    bound = _make_bound(store, bindings={"x": 1, "y": 2, "z": 3})
    engine = bound.atms_engine()
    derived = bound.derived_value("concept3")
    explanation = engine.explain_node(engine._derived_node_id("concept3", derived.value))

    assert explanation["status"] == "IN"
    assert explanation["traces"]
    assert any(
        trace["informant"] == "parameterization:0"
        and "claim:claim_x" in trace["antecedent_ids"]
        and any(
            antecedent.get("claim_id") == "claim_x"
            and antecedent["traces"]
            and antecedent["traces"][0]["informant"] == "claim:claim_x"
            for antecedent in trace["antecedents"]
        )
        for trace in explanation["traces"]
    )


def test_atms_preserves_nogood_pruned_vs_semantic_only_out_and_provenance() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_x",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_y",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["y == 2"]),
            },
            {
                "id": "claim_semantic",
                "concept_id": "concept4",
                "type": "parameter",
                "value": 9.0,
                "conditions_cel": json.dumps(["x > 0"]),
            },
        ],
        parameterizations=[
            {
                "output_concept_id": "concept3",
                "concept_ids": json.dumps(["concept1", "concept2"]),
                "sympy": "Eq(concept3, concept1 + concept2)",
                "formula": "z = x + y",
                "conditions_cel": None,
            }
        ],
        conflicts=[
            {"claim_a_id": "claim_x", "claim_b_id": "claim_y", "concept_id": "concept3"},
        ],
        solver=_OverlapSolver(),
    )
    bound = _make_bound(store, bindings={"x": 1, "y": 2})
    engine = bound.atms_engine()
    derived = bound.derived_value("concept3")

    derived_status = engine.node_status(engine._derived_node_id("concept3", derived.value))
    semantic_status = bound.claim_status("claim_semantic")
    nogood = next(iter(engine.nogoods.environments))
    nogood_details = engine.explain_nogood(nogood)

    assert derived_status.status == ATMSNodeStatus.OUT
    assert "nogood" in derived_status.reason
    assert semantic_status.status == ATMSNodeStatus.OUT
    assert semantic_status.support_quality == SupportQuality.SEMANTIC_COMPATIBLE
    assert "semantic compatibility" in semantic_status.reason
    assert nogood_details is not None
    assert nogood_details["provenance"]
    assert nogood_details["provenance"][0]["claim_a_id"] == "claim_x"
    assert nogood_details["provenance"][0]["claim_b_id"] == "claim_y"
    assert nogood_details["provenance"][0]["environment_a"]
    assert nogood_details["provenance"][0]["environment_b"]


def test_atms_verify_labels_reports_clean_fixpoint() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_exact",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
            }
        ]
    )
    bound = _make_bound(store, bindings={"x": 1})

    report = bound.atms_engine().verify_labels()

    assert report["ok"] is True
    assert report["consistency_errors"] == []
    assert report["minimality_errors"] == []
    assert report["soundness_errors"] == []
    assert report["completeness_errors"] == []


def test_phase8_graph_runtime_matches_boundworld_for_labels_and_nogoods() -> None:
    from propstore.world.atms import ATMSEngine

    store = _ATMSStore(
        claims=[
            {
                "id": "claim_x",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_y",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["y == 2"]),
            },
        ],
        parameterizations=[
            {
                "output_concept_id": "concept3",
                "concept_ids": json.dumps(["concept1", "concept2"]),
                "sympy": "Eq(concept3, concept1 + concept2)",
                "formula": "z = x + y",
                "conditions_cel": None,
            }
        ],
        conflicts=[
            {"claim_a_id": "claim_x", "claim_b_id": "claim_y", "concept_id": "concept3"},
        ],
    )
    bound = _make_bound(store, bindings={"x": 1, "y": 2})
    graph_engine = ATMSEngine(_GraphOnlyATMSRuntime(bound))
    bound_engine = bound.atms_engine()
    derived = bound.derived_value("concept3")

    assert graph_engine.claim_label("claim_x") == bound_engine.claim_label("claim_x")
    assert graph_engine.claim_label("claim_y") == bound_engine.claim_label("claim_y")
    assert graph_engine.derived_label("concept3", derived.value) == bound_engine.derived_label(
        "concept3",
        derived.value,
    )
    assert graph_engine.nogoods == bound_engine.nogoods


def test_phase8_graph_runtime_replays_future_status_and_interventions_without_boundworld_introspection() -> None:
    from propstore.world.atms import ATMSEngine

    store = _ATMSStore(
        claims=[
            {
                "id": "claim_now",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_future",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1", "y == 2"]),
            },
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})
    runtime_engine = ATMSEngine(_GraphOnlyATMSRuntime(bound))
    queryables = [QueryableAssumption.from_cel("y == 2")]

    future_statuses = runtime_engine.claim_future_statuses("claim_future", queryables, limit=8)
    relevance = runtime_engine.claim_relevance("claim_future", queryables, limit=8)
    plans = runtime_engine.claim_interventions("claim_future", queryables, "IN", limit=8)

    assert future_statuses["could_become_in"] is True
    assert [entry["queryable_cels"] for entry in future_statuses["futures"]] == [["y == 2"]]
    assert relevance["relevant_queryables"] == ["y == 2"]
    assert [plan["queryable_cels"] for plan in plans] == [["y == 2"]]


def test_worldline_policy_accepts_atms_backend_and_capture_uses_atms_state() -> None:
    class WorldWithBind(_ATMSStore):
        def bind(self, environment=None, *, policy=None, **conditions):
            bindings = dict(environment.bindings) if environment is not None else dict(conditions)
            context_id = environment.context_id if environment is not None else None
            return BoundWorld(
                self,
                environment=Environment(
                    bindings=bindings,
                    context_id=context_id,
                    assumptions=compile_environment_assumptions(
                        bindings=bindings,
                        context_id=context_id,
                    ),
                ),
                context_hierarchy=_LeafHierarchy() if context_id is not None else None,
                policy=policy,
            )

        def resolve_concept(self, name: str) -> str | None:
            return "concept1" if name == "target" else None

        def get_concept(self, concept_id: str) -> dict | None:
            if concept_id == "concept1":
                return {"id": concept_id, "canonical_name": "target"}
            return None

    worldline = WorldlineDefinition.from_dict({
        "id": "atms_worldline",
        "targets": ["target"],
        "inputs": {"bindings": {"x": 1}},
        "policy": {"strategy": "argumentation", "reasoning_backend": "atms"},
    })
    world = WorldWithBind(
        claims=[
            {
                "id": "claim_exact",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
            }
        ]
    )

    result = run_worldline(worldline, world)

    assert worldline.policy.reasoning_backend == ReasoningBackend.ATMS
    assert result.argumentation is not None
    assert result.argumentation["backend"] == "atms"
    assert result.argumentation["supported"] == ["claim_exact"]
    assert result.argumentation["node_statuses"] == {"claim:claim_exact": "IN"}
    assert result.argumentation["support_quality"] == {"claim_exact": "exact"}
    assert result.argumentation["essential_support"]["claim_exact"]
    assert result.argumentation["nogood_details"] == []
    assert "claim_exact" in result.argumentation["status_reasons"]


def test_atms_cli_surfaces_status_context_and_verify(monkeypatch) -> None:
    class FakeRepo:
        pass

    class _StringOverlapSolver:
        def are_disjoint(self, left: list[str], right: list[str]) -> bool:
            if "x == '1'" in left and "x != '0'" in right:
                return False
            if "x != '0'" in left and "x == '1'" in right:
                return False
            return set(left).isdisjoint(right)

    class FakeWorldModel(_ATMSStore):
        def __init__(self, repo) -> None:
            super().__init__(
                claims=[
                    {
                        "id": "claim_exact",
                        "concept_id": "concept1",
                        "type": "parameter",
                        "value": 1.0,
                        "conditions_cel": json.dumps(["x == '1'"]),
                    },
                    {
                        "id": "claim_semantic",
                        "concept_id": "concept1",
                        "type": "parameter",
                        "value": 2.0,
                        "conditions_cel": json.dumps(["x != '0'"]),
                    },
                ],
                solver=_StringOverlapSolver(),
            )

        def bind(self, environment=None, *, policy=None, **conditions):
            bindings = dict(environment.bindings) if environment is not None else dict(conditions)
            context_id = environment.context_id if environment is not None else None
            return BoundWorld(
                self,
                environment=Environment(
                    bindings=bindings,
                    context_id=context_id,
                    assumptions=compile_environment_assumptions(
                        bindings=bindings,
                        context_id=context_id,
                    ),
                ),
                context_hierarchy=_LeafHierarchy() if context_id is not None else None,
                policy=policy,
            )

        def close(self) -> None:
            return None

    monkeypatch.setattr("propstore.cli.Repository.find", lambda start=None: FakeRepo())
    monkeypatch.setattr("propstore.world.WorldModel", FakeWorldModel)

    runner = CliRunner()

    status_result = runner.invoke(cli, ["world", "atms-status", "x=1"])
    assert status_result.exit_code == 0, status_result.output
    assert "claim_exact: status=IN support_quality=exact" in status_result.output
    assert "claim_semantic: status=OUT support_quality=semantic_compatible" in status_result.output

    context_result = runner.invoke(cli, ["world", "atms-context", "x=1"])
    assert context_result.exit_code == 0, context_result.output
    assert "claim_exact: status=IN" in context_result.output
    assert "claim_semantic" not in context_result.output

    verify_result = runner.invoke(cli, ["world", "atms-verify", "x=1"])
    assert verify_result.exit_code == 0, verify_result.output
    assert "ATMS labels verified." in verify_result.output


def test_world_extensions_cli_rejects_atms_backend_explicitly(monkeypatch) -> None:
    class FakeRepo:
        pass

    class FakeBound:
        def active_claims(self, concept_id: str | None = None) -> list[dict]:
            return [{"id": "claim_exact", "concept_id": "concept1", "type": "parameter", "value": 1.0}]

    class FakeWorldModel:
        def __init__(self, repo) -> None:
            self.repo = repo

        def bind(self, environment=None, **conditions):
            return FakeBound()

        def close(self) -> None:
            return None

    monkeypatch.setattr("propstore.cli.Repository.find", lambda start=None: FakeRepo())
    monkeypatch.setattr("propstore.world.WorldModel", FakeWorldModel)

    runner = CliRunner()
    result = runner.invoke(cli, ["world", "extensions", "--backend", "atms"])

    assert result.exit_code != 0
    assert "does not expose Dung extensions" in result.output


def test_atms_future_queryables_can_activate_exact_support_without_fabricating_current_support() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_now",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_future",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1", "y == 2"]),
            },
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})
    engine = bound.atms_engine()
    queryables = [QueryableAssumption.from_cel("y == 2")]

    current = bound.claim_status("claim_future")
    future_statuses = bound.claim_future_statuses("claim_future", queryables, limit=4)
    why_out = engine.why_out(current.node_id, queryables=queryables, limit=4)
    future_in = engine.could_become_in(current.node_id, queryables, limit=4)

    assert current.status == ATMSNodeStatus.OUT
    assert current.out_kind == ATMSOutKind.MISSING_SUPPORT
    assert engine.claim_label("claim_future") is None
    assert future_statuses["could_become_in"] is True
    assert future_statuses["current"].status == ATMSNodeStatus.OUT
    assert future_statuses["futures"][0]["queryable_cels"] == ["y == 2"]
    assert future_statuses["futures"][0]["status"] == ATMSNodeStatus.IN
    assert why_out["out_kind"] == ATMSOutKind.MISSING_SUPPORT
    assert why_out["future_activatable"] is True
    assert why_out["candidate_queryable_cels"] == [["y == 2"]]
    assert future_in[0]["queryable_cels"] == ["y == 2"]
    assert future_in[0]["status"] == ATMSNodeStatus.IN


def test_run5_future_audit_pins_rebuilt_bound_world_substrate() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_future",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1", "y == 2"]),
            },
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})
    engine = bound.atms_engine()
    queryable = QueryableAssumption.from_cel("y == 2")

    future_engine = engine._future_engine((queryable,))
    future_report = engine.future_environments([queryable], limit=4)[0]

    assert isinstance(future_report, dict)
    assert future_engine is not engine
    assert future_engine._bound is not bound
    assert any(
        assumption.assumption_id == queryable.assumption_id
        for assumption in future_engine._bound._environment.assumptions
    )
    assert future_report["queryable_ids"] == [queryable.assumption_id]
    assert future_report["queryable_cels"] == ["y == 2"]
    assert future_report["environment"]
    assert future_report["consistent"] is True


def test_future_engine_includes_queryable_bindings_in_environment() -> None:
    """Future engine must propagate queryable CEL bindings into environment.bindings."""
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_future",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1", "y == 2"]),
            },
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})
    engine = bound.atms_engine()
    queryable = QueryableAssumption.from_cel("y == 2")

    future_engine = engine._future_engine((queryable,))
    future_bindings = future_engine._bound._environment.bindings

    # The original binding must survive
    assert future_bindings.get("x") == 1
    # The queryable's binding must be present
    assert "y" in future_bindings, (
        f"queryable binding 'y' missing from future environment.bindings: {dict(future_bindings)}"
    )
    assert future_bindings["y"] == 2


def test_run7_future_audit_queryables_are_additive_only() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_future",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1", "y == 2"]),
            },
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})
    futures = bound.atms_engine().future_environments(
        [
            QueryableAssumption.from_cel("x == 1"),
            QueryableAssumption.from_cel("y == 2"),
        ],
        limit=4,
    )
    current_assumption_ids = {
        assumption.cel: assumption.assumption_id
        for assumption in bound._environment.assumptions
    }
    future_queryable = QueryableAssumption.from_cel("y == 2")

    assert [future["queryable_cels"] for future in futures] == [["y == 2"]]
    assert any(current_assumption_ids["x == 1"] in future["environment"] for future in futures)
    assert any(future_queryable.assumption_id in future["environment"] for future in futures)


def test_run5_future_audit_surfaces_missing_support_nogood_and_future_activation() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_x",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_y",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["y == 2"]),
            },
            {
                "id": "claim_future",
                "concept_id": "concept3",
                "type": "parameter",
                "value": 4.0,
                "conditions_cel": json.dumps(["x == 1", "z == 3"]),
            },
        ],
        parameterizations=[
            {
                "output_concept_id": "concept4",
                "concept_ids": json.dumps(["concept1", "concept2"]),
                "sympy": "Eq(concept4, concept1 + concept2)",
                "formula": "w = x + y",
                "conditions_cel": None,
            }
        ],
        conflicts=[
            {"claim_a_id": "claim_x", "claim_b_id": "claim_y", "concept_id": "concept4"},
        ],
    )
    bound = _make_bound(store, bindings={"x": 1, "y": 2})
    engine = bound.atms_engine()
    queryables = [QueryableAssumption.from_cel("z == 3")]
    derived = bound.derived_value("concept4")

    derived_why_out = engine.why_out(engine._derived_node_id("concept4", derived.value), limit=4)
    future_why_out = engine.why_out("claim:claim_future", queryables=queryables, limit=4)

    assert derived_why_out["out_kind"] == ATMSOutKind.NOGOOD_PRUNED
    assert derived_why_out["future_activatable"] is False
    assert future_why_out["out_kind"] == ATMSOutKind.MISSING_SUPPORT
    assert future_why_out["future_activatable"] is True


def test_atms_future_queryables_respect_limit_and_enumerate_deterministically() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_future_a",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["a == 1"]),
            },
            {
                "id": "claim_future_b",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["b == 2"]),
            },
        ],
    )
    bound = _make_bound(store)
    engine = bound.atms_engine()
    queryables = [
        QueryableAssumption.from_cel("b == 2"),
        QueryableAssumption.from_cel("a == 1"),
    ]

    futures = engine.future_environments(queryables, limit=2)

    assert [entry["queryable_cels"] for entry in futures] == [["a == 1"], ["b == 2"]]
    assert all(entry["queryable_cels"] != ["a == 1", "b == 2"] for entry in futures)
    assert engine.claim_label("claim_future_a") is None
    assert engine.claim_label("claim_future_b") is None


def test_atms_future_queryables_can_be_insufficient() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_future",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 5.0,
                "conditions_cel": json.dumps(["x == 1", "y == 2"]),
            }
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})
    queryables = [QueryableAssumption.from_cel("z == 3")]

    future_statuses = bound.claim_future_statuses("claim_future", queryables, limit=4)
    why_out = bound.atms_engine().why_out("claim:claim_future", queryables=queryables, limit=4)

    assert future_statuses["could_become_in"] is False
    assert future_statuses["futures"][0]["status"] == ATMSNodeStatus.OUT
    assert future_statuses["futures"][0]["out_kind"] == ATMSOutKind.MISSING_SUPPORT
    assert why_out["future_activatable"] is False
    assert why_out["candidate_queryable_cels"] == []


def test_atms_bounded_stability_and_relevance_are_honest_for_claims_and_concepts() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_now",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_future",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1", "y == 2"]),
            },
            {
                "id": "claim_stable_out",
                "concept_id": "concept3",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["x == 1", "w == 4"]),
            },
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})
    queryables = [
        QueryableAssumption.from_cel("y == 2"),
        QueryableAssumption.from_cel("z == 3"),
    ]

    stable_in = bound.claim_stability("claim_now", queryables, limit=8)
    unstable_out = bound.claim_stability("claim_future", queryables, limit=8)
    stable_out = bound.claim_stability("claim_stable_out", queryables, limit=8)
    claim_relevance = bound.claim_relevance("claim_future", queryables, limit=8)
    concept_stability = bound.concept_stability("concept2", queryables, limit=8)
    concept_relevance = bound.concept_relevance("concept2", queryables, limit=8)

    assert stable_in["stable"] is True
    assert stable_in["witnesses"] == []
    assert bound.claim_is_stable("claim_now", queryables, limit=8) is True

    assert unstable_out["stable"] is False
    assert [witness["queryable_cels"] for witness in unstable_out["witnesses"]] == [["y == 2"]]
    assert unstable_out["witnesses"][0]["status"] == ATMSNodeStatus.IN
    assert bound.atms_engine().status_flip_witnesses("claim:claim_future", queryables, limit=8) == unstable_out["witnesses"]
    assert bound.claim_is_stable("claim_future", queryables, limit=8) is False

    assert stable_out["stable"] is True
    assert stable_out["witnesses"] == []

    assert claim_relevance["relevant_queryables"] == ["y == 2"]
    assert claim_relevance["irrelevant_queryables"] == ["z == 3"]
    assert claim_relevance["witness_pairs"]["y == 2"][0]["without"]["status"] == ATMSNodeStatus.OUT
    assert claim_relevance["witness_pairs"]["y == 2"][0]["with"]["status"] == ATMSNodeStatus.IN
    assert bound.claim_relevant_queryables("claim_future", queryables, limit=8) == ["y == 2"]

    assert concept_stability["stable"] is False
    assert [witness["queryable_cels"] for witness in concept_stability["witnesses"]] == [["y == 2"]]
    assert concept_stability["witnesses"][0]["status"] == "determined"
    assert bound.concept_is_stable("concept2", queryables, limit=8) is False
    assert concept_relevance["relevant_queryables"] == ["y == 2"]
    assert bound.concept_relevant_queryables("concept2", queryables, limit=8) == ["y == 2"]


def test_atms_future_queryables_do_not_fabricate_future_out_transitions_without_revision() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_future",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1", "y == 2"]),
            },
            {
                "id": "claim_future_conflict",
                "concept_id": "concept3",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["x == 1", "y == 2", "z == 3"]),
            },
        ],
        conflicts=[
            {"claim_a_id": "claim_future", "claim_b_id": "claim_future_conflict", "concept_id": "concept2"},
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})
    queryables = [
        QueryableAssumption.from_cel("y == 2"),
        QueryableAssumption.from_cel("z == 3"),
    ]

    future_statuses = bound.claim_future_statuses("claim_future", queryables, limit=4)
    future_out = bound.atms_engine().could_become_out("claim:claim_future", queryables, limit=4)

    assert bound.claim_status("claim_future").status == ATMSNodeStatus.OUT
    assert future_statuses["could_become_in"] is True
    assert future_statuses["could_become_out"] is False
    assert future_out == []


def test_atms_claim_interventions_and_next_queries_are_minimal() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_future",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1", "y == 2"]),
            },
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})
    queryables = [
        QueryableAssumption.from_cel("z == 3"),
        QueryableAssumption.from_cel("y == 2"),
    ]

    plans = bound.claim_interventions("claim_future", queryables, "IN", limit=8)
    suggestions = bound.claim_next_queryables("claim_future", queryables, "IN", limit=8)
    current_assumption_ids = {
        assumption.cel: assumption.assumption_id
        for assumption in bound._environment.assumptions
    }
    future_queryable = QueryableAssumption.from_cel("y == 2")

    assert len(plans) == 1
    assert plans[0]["current_status"] == ATMSNodeStatus.OUT
    assert plans[0]["target_status"] == ATMSNodeStatus.IN
    assert plans[0]["result_status"] == ATMSNodeStatus.IN
    assert plans[0]["queryable_cels"] == ["y == 2"]
    assert current_assumption_ids["x == 1"] in plans[0]["environment"]
    assert future_queryable.assumption_id in plans[0]["environment"]
    assert plans[0]["minimality_basis"] == "set_inclusion_over_queryable_ids"
    assert all(cel in {"y == 2", "z == 3"} for cel in plans[0]["queryable_cels"])
    assert [entry["queryable_cel"] for entry in suggestions] == ["y == 2"]
    assert suggestions[0]["plan_count"] == 1
    assert suggestions[0]["smallest_plan_size"] == 1
    assert suggestions[0]["plan_queryable_cels"] == [["y == 2"]]


def test_atms_claim_interventions_to_out_require_consistent_nogood_pruned_future() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_future",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1", "y == 2"]),
            },
            {
                "id": "claim_conflict",
                "concept_id": "concept3",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["y == 2"]),
            },
        ],
        conflicts=[
            {"claim_a_id": "claim_future", "claim_b_id": "claim_conflict", "concept_id": "concept2"},
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})
    queryables = [QueryableAssumption.from_cel("y == 2")]

    future_out = bound.atms_engine().could_become_out("claim:claim_future", queryables, limit=8)
    plans = bound.claim_interventions("claim_future", queryables, "OUT", limit=8)

    assert [future["queryable_cels"] for future in future_out] == [["y == 2"]]
    assert future_out[0]["out_kind"] == ATMSOutKind.NOGOOD_PRUNED
    assert future_out[0]["consistent"] is False
    assert plans == []


def test_atms_concept_interventions_use_replayed_value_statuses() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_future",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["y == 2"]),
            },
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})

    plans = bound.concept_interventions("concept2", ["y == 2"], "determined", limit=8)
    suggestions = bound.concept_next_queryables("concept2", ["y == 2"], "determined", limit=8)

    assert [plan["queryable_cels"] for plan in plans] == [["y == 2"]]
    assert plans[0]["current_status"] == "no_claims"
    assert plans[0]["result_status"] == "determined"
    assert [entry["queryable_cel"] for entry in suggestions] == ["y == 2"]


def test_atms_claim_interventions_return_no_plan_when_unreachable_and_respect_limit() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_future",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["a == 1", "b == 2"]),
            },
        ],
    )
    bound = _make_bound(store)

    assert bound.claim_interventions("claim_future", ["z == 3"], "IN", limit=8) == []
    assert bound.claim_interventions("claim_future", ["a == 1", "b == 2"], "IN", limit=1) == []
    assert [plan["queryable_cels"] for plan in bound.claim_interventions(
        "claim_future",
        ["b == 2", "a == 1"],
        "IN",
        limit=8,
    )] == [["a == 1", "b == 2"]]


def test_atms_why_out_distinguishes_missing_support_from_nogood_and_future_activation() -> None:
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_x",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_y",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["y == 2"]),
            },
            {
                "id": "claim_future",
                "concept_id": "concept3",
                "type": "parameter",
                "value": 4.0,
                "conditions_cel": json.dumps(["x == 1", "z == 3"]),
            },
        ],
        parameterizations=[
            {
                "output_concept_id": "concept4",
                "concept_ids": json.dumps(["concept1", "concept2"]),
                "sympy": "Eq(concept4, concept1 + concept2)",
                "formula": "w = x + y",
                "conditions_cel": None,
            }
        ],
        conflicts=[
            {"claim_a_id": "claim_x", "claim_b_id": "claim_y", "concept_id": "concept4"},
        ],
    )
    bound = _make_bound(store, bindings={"x": 1, "y": 2})
    engine = bound.atms_engine()
    queryables = [QueryableAssumption.from_cel("z == 3")]
    derived = bound.derived_value("concept4")

    derived_why_out = engine.why_out(engine._derived_node_id("concept4", derived.value), limit=4)
    future_why_out = engine.why_out("claim:claim_future", queryables=queryables, limit=4)

    assert derived_why_out["out_kind"] == ATMSOutKind.NOGOOD_PRUNED
    assert derived_why_out["future_activatable"] is False
    assert future_why_out["out_kind"] == ATMSOutKind.MISSING_SUPPORT
    assert future_why_out["future_activatable"] is True
    assert future_why_out["candidate_queryable_cels"] == [["z == 3"]]


def test_atms_worldline_future_capture_is_opt_in() -> None:
    class WorldWithBind(_ATMSStore):
        def bind(self, environment=None, *, policy=None, **conditions):
            bindings = dict(environment.bindings) if environment is not None else dict(conditions)
            context_id = environment.context_id if environment is not None else None
            effective_assumptions = tuple(environment.effective_assumptions) if environment is not None else ()
            assumptions = compile_environment_assumptions(
                bindings=bindings,
                effective_assumptions=effective_assumptions,
                context_id=context_id,
            )
            return BoundWorld(
                self,
                environment=Environment(
                    bindings=bindings,
                    context_id=context_id,
                    effective_assumptions=effective_assumptions,
                    assumptions=assumptions,
                ),
                context_hierarchy=_LeafHierarchy() if context_id is not None else None,
                policy=policy,
            )

        def resolve_concept(self, name: str) -> str | None:
            return "concept2" if name == "target" else None

        def get_concept(self, concept_id: str) -> dict | None:
            if concept_id == "concept2":
                return {"id": concept_id, "canonical_name": "target"}
            return None

        def has_table(self, name: str) -> bool:
            return False

    world = WorldWithBind(
        claims=[
            {
                "id": "claim_now",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_future",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1", "y == 2"]),
            },
        ]
    )
    plain_worldline = WorldlineDefinition.from_dict({
        "id": "atms_worldline_plain",
        "targets": ["target"],
        "inputs": {"bindings": {"x": 1}},
        "policy": {"strategy": "argumentation", "reasoning_backend": "atms"},
    })
    future_worldline = WorldlineDefinition.from_dict({
        "id": "atms_worldline_future",
        "targets": ["target"],
        "inputs": {"bindings": {"x": 1}},
        "policy": {
            "strategy": "argumentation",
            "reasoning_backend": "atms",
            "future_queryables": ["y == 2"],
            "future_limit": 4,
        },
    })

    plain_result = run_worldline(plain_worldline, world)
    future_result = run_worldline(future_worldline, world)

    assert "declared_queryables" not in plain_result.argumentation
    assert future_result.argumentation["declared_queryables"] == ["y == 2"]
    assert future_result.argumentation["future_statuses"]["claim_future"]["could_become_in"] is True
    assert future_result.argumentation["why_out"]["claim_future"]["candidate_queryable_cels"] == [["y == 2"]]
    assert future_result.argumentation["stability"]["claim_future"]["stable"] is False
    assert future_result.argumentation["relevance"]["claim_future"]["relevant_queryables"] == ["y == 2"]
    assert future_result.argumentation["witness_futures"]["claim_future"][0]["queryable_cels"] == ["y == 2"]


def test_was_pruned_by_nogood_detects_transitive_nogood_through_antecedent() -> None:
    """When a derived node is OUT because its antecedent was nogood-pruned,
    _was_pruned_by_nogood should report NOGOOD_PRUNED, not MISSING_SUPPORT.

    Setup: claim_a (concept1=2.0, x==1) conflicts with claim_b (concept1=3.0,
    unconditional). Nogood = {x==1}. claim_a is directly nogood-pruned.
    Parameterization concept2 = concept1 * 2 creates derived:concept2:4.0
    depending on claim_a. That derived node is transitively nogood-pruned.
    """
    store = _ATMSStore(
        claims=[
            {
                "id": "claim_a",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_b",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": None,
            },
        ],
        parameterizations=[
            {
                "output_concept_id": "concept2",
                "concept_ids": json.dumps(["concept1"]),
                "sympy": "Eq(concept2, concept1 * 2)",
                "formula": "concept2 = concept1 * 2",
                "conditions_cel": None,
            }
        ],
        conflicts=[
            {"claim_a_id": "claim_a", "claim_b_id": "claim_b", "concept_id": "concept1"},
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})
    engine = bound.atms_engine()

    # claim_a should be directly nogood-pruned (its assumption {x==1} is a nogood)
    claim_a_inspection = engine.node_status("claim:claim_a")
    assert claim_a_inspection.status == ATMSNodeStatus.OUT
    assert claim_a_inspection.out_kind == ATMSOutKind.NOGOOD_PRUNED

    # The derived node from claim_a should be transitively nogood-pruned
    derived_node_id = engine._derived_node_id("concept2", 4.0)
    derived_inspection = engine.node_status(derived_node_id)
    assert derived_inspection.status == ATMSNodeStatus.OUT
    assert derived_inspection.out_kind == ATMSOutKind.NOGOOD_PRUNED, (
        f"Expected NOGOOD_PRUNED for transitive nogood, got {derived_inspection.out_kind}"
    )


def test_atms_cli_surfaces_future_analysis(monkeypatch) -> None:
    class FakeRepo:
        pass

    class FakeWorldModel(_ATMSStore):
        def __init__(self, repo) -> None:
            super().__init__(
                claims=[
                    {
                        "id": "claim_now",
                        "concept_id": "concept1",
                        "type": "parameter",
                        "value": 1.0,
                        "conditions_cel": json.dumps(["x == '1'"]),
                    },
                    {
                        "id": "claim_future",
                        "concept_id": "concept2",
                        "type": "parameter",
                        "value": 2.0,
                        "conditions_cel": json.dumps(["x == '1'", "y == '2'"]),
                    },
                ],
            )

        def bind(self, environment=None, *, policy=None, **conditions):
            bindings = dict(environment.bindings) if environment is not None else dict(conditions)
            context_id = environment.context_id if environment is not None else None
            effective_assumptions = tuple(environment.effective_assumptions) if environment is not None else ()
            assumptions = compile_environment_assumptions(
                bindings=bindings,
                effective_assumptions=effective_assumptions,
                context_id=context_id,
            )
            return BoundWorld(
                self,
                environment=Environment(
                    bindings=bindings,
                    context_id=context_id,
                    effective_assumptions=effective_assumptions,
                    assumptions=assumptions,
                ),
                context_hierarchy=_LeafHierarchy() if context_id is not None else None,
                policy=policy,
            )

        def close(self) -> None:
            return None

    monkeypatch.setattr("propstore.cli.Repository.find", lambda start=None: FakeRepo())
    monkeypatch.setattr("propstore.world.WorldModel", FakeWorldModel)

    runner = CliRunner()

    futures_result = runner.invoke(
        cli,
        ["world", "atms-futures", "claim_future", "x=1", "--queryable", "y=2"],
    )
    why_out_result = runner.invoke(
        cli,
        ["world", "atms-why-out", "claim_future", "x=1", "--queryable", "y=2"],
    )
    stability_result = runner.invoke(
        cli,
        ["world", "atms-stability", "claim_future", "x=1", "--queryable", "y=2", "--queryable", "z=3"],
    )
    relevance_result = runner.invoke(
        cli,
        ["world", "atms-relevance", "claim_future", "x=1", "--queryable", "y=2", "--queryable", "z=3"],
    )

    assert futures_result.exit_code == 0, futures_result.output
    assert "claim_future: current_status=OUT could_become_in=True" in futures_result.output
    assert "future [y == '2'] -> IN" in futures_result.output
    assert why_out_result.exit_code == 0, why_out_result.output
    assert "claim_future: out_kind=missing_support future_activatable=True" in why_out_result.output
    assert "candidate_queryables=[y == '2']" in why_out_result.output
    assert stability_result.exit_code == 0, stability_result.output
    assert "claim_future: status=OUT stable=False" in stability_result.output
    assert "witness [y == '2'] -> IN" in stability_result.output
    assert relevance_result.exit_code == 0, relevance_result.output
    assert "claim_future: current_status=OUT relevant_queryables=[y == '2']" in relevance_result.output
    assert "y == '2': [] -> OUT; [y == '2'] -> IN" in relevance_result.output


def test_atms_cli_surfaces_interventions_and_next_queries(monkeypatch) -> None:
    class FakeRepo:
        pass

    class FakeWorldModel(_ATMSStore):
        def __init__(self, repo) -> None:
            super().__init__(
                claims=[
                    {
                        "id": "claim_future",
                        "concept_id": "concept2",
                        "type": "parameter",
                        "value": 2.0,
                        "conditions_cel": json.dumps(["x == '1'", "y == '2'"]),
                    },
                ],
            )

        def bind(self, environment=None, *, policy=None, **conditions):
            bindings = dict(environment.bindings) if environment is not None else dict(conditions)
            context_id = environment.context_id if environment is not None else None
            effective_assumptions = tuple(environment.effective_assumptions) if environment is not None else ()
            assumptions = compile_environment_assumptions(
                bindings=bindings,
                effective_assumptions=effective_assumptions,
                context_id=context_id,
            )
            return BoundWorld(
                self,
                environment=Environment(
                    bindings=bindings,
                    context_id=context_id,
                    effective_assumptions=effective_assumptions,
                    assumptions=assumptions,
                ),
                context_hierarchy=_LeafHierarchy() if context_id is not None else None,
                policy=policy,
            )

        def close(self) -> None:
            return None

    monkeypatch.setattr("propstore.cli.Repository.find", lambda start=None: FakeRepo())
    monkeypatch.setattr("propstore.world.WorldModel", FakeWorldModel)

    runner = CliRunner()

    interventions_result = runner.invoke(
        cli,
        ["world", "atms-interventions", "claim_future", "x=1", "--target-status", "IN", "--queryable", "y=2", "--queryable", "z=3"],
    )
    next_query_result = runner.invoke(
        cli,
        ["world", "atms-next-query", "claim_future", "x=1", "--target-status", "IN", "--queryable", "y=2", "--queryable", "z=3"],
    )

    assert interventions_result.exit_code == 0, interventions_result.output
    assert "bounded additive plans over declared queryables" in interventions_result.output
    assert "not revision/contraction" in interventions_result.output
    assert "plan [y == '2'] -> IN" in interventions_result.output
    assert next_query_result.exit_code == 0, next_query_result.output
    assert "derived from bounded additive intervention plans" in next_query_result.output
    assert "y == '2': coverage=1 smallest_plan_size=1" in next_query_result.output
