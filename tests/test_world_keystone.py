"""Phase 7a-keystone: the world-layer carrier types and prerequisite modules.

These cover the frozen graph carriers (round-trip ``to_dict``/``from_dict``), the
``GraphDelta`` hypothetical-edit primitive, the ``Environment`` frame, the
parameterization evaluator (built on ``human-to-sympy``, never raw sympy), the
small value/enum modules, and the layer rule that ``core`` never imports
``world``. The store family in ``core/environment`` is Protocols only; the test
asserts they are typed over the charter domain objects (``Claim`` / ``Concept`` /
``Stance``), not a resurrected ``*RowInput`` spelling.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from condition_ir import KindType

from propstore import claim_conditions as cc
from propstore.core.anytime import BudgetExhausted, EnumerationExceeded
from propstore.core.environment import (
    AssumptionRef,
    ClaimCatalogStore,
    ConceptCatalogStore,
    Environment,
    StanceStore,
    WorldStore,
)
from propstore.core.exactness_types import Exactness, coerce_exactness
from propstore.core.graph_relation_types import (
    GraphRelationType,
    coerce_graph_relation_type,
)
from propstore.core.graph_types import (
    ActiveWorldGraph,
    ClaimNode,
    CompiledWorldGraph,
    ConceptNode,
    ConflictWitness,
    GraphDelta,
    ParameterizationEdge,
    ProvenanceRecord,
    RelationEdge,
)
from propstore.core.id_types import (
    AssumptionId,
    QueryableId,
    to_assumption_id,
    to_assumption_ids,
    to_claim_ids,
    to_concept_ids,
    to_queryable_ids,
)
from propstore.core.micropublications import (
    ActiveMicropublication,
    coerce_active_micropublication,
)
from propstore.core.store_results import (
    ClaimSimilarityHit,
    ConceptSearchHit,
    ConceptSimilarityHit,
    WorldStoreStats,
)
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.propagation import (
    ParameterizationEvaluationStatus,
    evaluate_parameterization,
    rewrite_parameterization_symbols,
)
from propstore.provenance import ProvenanceStatus
from propstore.reporting import JsonReportMixin, json_ready


# --- id_types -------------------------------------------------------------


def test_id_type_coercers_brand_strings() -> None:
    assert to_assumption_id(5) == AssumptionId("5")
    assert to_assumption_ids([1, "a"]) == (AssumptionId("1"), AssumptionId("a"))
    assert to_queryable_ids(["q"]) == (QueryableId("q"),)
    assert to_concept_ids(("c1",)) == ("c1",)
    assert to_claim_ids(("k1", "k2")) == ("k1", "k2")


# --- enum coercers --------------------------------------------------------


def test_coerce_exactness_round_trips_and_allows_none() -> None:
    assert coerce_exactness("exact") is Exactness.EXACT
    assert coerce_exactness(Exactness.CONDITIONAL) is Exactness.CONDITIONAL
    assert coerce_exactness(None) is None


def test_coerce_graph_relation_type_validates() -> None:
    assert coerce_graph_relation_type("supports") is GraphRelationType.SUPPORTS
    assert coerce_graph_relation_type(GraphRelationType.IS_A) is GraphRelationType.IS_A
    with pytest.raises(ValueError):
        coerce_graph_relation_type("not_a_relation")
    with pytest.raises(TypeError):
        coerce_graph_relation_type(object())


# --- graph carrier round-trips -------------------------------------------


def test_concept_node_round_trip() -> None:
    node = ConceptNode(
        concept_id="c1",
        canonical_name="Frequency",
        status="authored",
        kind_type="QUANTITY",
        attributes={"definition": "cycles per second"},
    )
    assert ConceptNode.from_dict(node.to_dict()) == node


def test_claim_node_round_trip_with_conditions_label_and_provenance() -> None:
    freq = Concept(concept_id="freq", canonical_name="frequency")
    registry = cc.condition_registry([cc.lower_concept(freq, KindType.QUANTITY)])
    checked = cc.check_claim_conditions(
        Claim(claim_id="c1", conditions=("freq > 10",)), registry
    ).checked

    node = ClaimNode(
        claim_id="c1",
        claim_type=ClaimType.PARAMETER,
        value_concept_id="freq",
        scalar_value=42.0,
        checked_conditions=checked,
        provenance=ProvenanceRecord(source_table="claim", source_id="c1", paper="P", page=3),
        attributes={"unit": "Hz"},
    )
    rebuilt = ClaimNode.from_dict(node.to_dict())
    assert rebuilt == node
    # checked_conditions compare=False but must still survive the round-trip.
    assert rebuilt.checked_conditions is not None
    assert rebuilt.checked_conditions.sources == ("freq > 10",)


def test_claim_node_requires_claim_type_in_from_dict() -> None:
    with pytest.raises(ValueError):
        ClaimNode.from_dict({"claim_id": "c1"})


def test_relation_edge_round_trip() -> None:
    edge = RelationEdge(
        source_id="a",
        target_id="b",
        relation_type="supports",
        derived_from=(("x", "y"),),
        attributes={"weight": 1},
    )
    assert RelationEdge.from_dict(edge.to_dict()) == edge
    assert edge.relation_type is GraphRelationType.SUPPORTS


def test_parameterization_edge_round_trip() -> None:
    edge = ParameterizationEdge(
        output_concept_id="y",
        input_concept_ids=("a", "b"),
        formula="a + b",
        sympy="a + b",
        exactness="exact",
    )
    assert ParameterizationEdge.from_dict(edge.to_dict()) == edge
    assert edge.exactness is Exactness.EXACT


def test_conflict_witness_sorts_pair() -> None:
    witness = ConflictWitness(left_claim_id="z", right_claim_id="a", kind="CONFLICT")
    assert witness.left_claim_id == "a"
    assert witness.right_claim_id == "z"
    assert ConflictWitness.from_dict(witness.to_dict()) == witness


def test_compiled_world_graph_round_trip_and_sorts() -> None:
    graph = CompiledWorldGraph(
        concepts=(ConceptNode(concept_id="c1", canonical_name="One"),),
        claims=(
            ClaimNode(claim_id="k2", claim_type=ClaimType.PARAMETER),
            ClaimNode(claim_id="k1", claim_type=ClaimType.OBSERVATION),
        ),
    )
    assert tuple(c.claim_id for c in graph.claims) == ("k1", "k2")
    assert CompiledWorldGraph.from_dict(graph.to_dict()) == graph


# --- GraphDelta -----------------------------------------------------------


def test_graph_delta_apply_add_and_remove() -> None:
    base = CompiledWorldGraph(
        claims=(ClaimNode(claim_id="k1", claim_type=ClaimType.PARAMETER),)
    )
    added = ClaimNode(claim_id="k2", claim_type=ClaimType.OBSERVATION)
    delta = GraphDelta(add_claims=(added,), remove_claim_ids=("k1",))
    result = delta.apply(base)
    assert tuple(c.claim_id for c in result.claims) == ("k2",)


def test_graph_delta_is_identity_and_then() -> None:
    assert GraphDelta().is_identity is True
    add_a = GraphDelta(add_claims=(ClaimNode(claim_id="a", claim_type=ClaimType.MODEL),))
    add_b = GraphDelta(add_claims=(ClaimNode(claim_id="b", claim_type=ClaimType.MODEL),))
    composed = add_a.then(add_b)
    assert not composed.is_identity
    applied = composed.apply(CompiledWorldGraph())
    assert {c.claim_id for c in applied.claims} == {"a", "b"}


# --- Environment ----------------------------------------------------------


def test_environment_round_trip_with_assumptions() -> None:
    env = Environment(
        bindings={"setting": "lab"},
        context_id="ctx1",
        effective_assumptions=("setting == 'lab'",),
        assumptions=(
            AssumptionRef(
                assumption_id="a1", kind="binding", source="user", cel="setting == 'lab'"
            ),
        ),
    )
    rebuilt = Environment.from_dict(env.to_dict())
    assert rebuilt == env


def test_environment_from_dict_handles_empty_and_none() -> None:
    assert Environment.from_dict(None) == Environment()
    assert Environment.from_dict({}) == Environment()
    with pytest.raises(ValueError):
        Environment.from_dict("not a mapping")


def test_active_world_graph_round_trip() -> None:
    compiled = CompiledWorldGraph(
        claims=(ClaimNode(claim_id="k1", claim_type=ClaimType.PARAMETER),)
    )
    active = ActiveWorldGraph(
        compiled=compiled,
        environment=Environment(context_id="ctx"),
        active_claim_ids=("k1",),
    )
    assert ActiveWorldGraph.from_dict(active.to_dict()) == active


# --- propagation (human-to-sympy, never raw sympy) ------------------------


def test_evaluate_parameterization_bare_expression() -> None:
    result = evaluate_parameterization("a + b", {"a": 2.0, "b": 3.0}, "y")
    assert result.status is ParameterizationEvaluationStatus.VALUE
    assert result.value == 5.0


def test_evaluate_parameterization_equation_solves_for_output() -> None:
    result = evaluate_parameterization("Eq(y, a * 2)", {"a": 4.0}, "y")
    assert result.status is ParameterizationEvaluationStatus.VALUE
    assert result.value == 8.0


def test_evaluate_parameterization_missing_input() -> None:
    result = evaluate_parameterization("a + b", {"a": 1.0}, "y")
    assert result.status is ParameterizationEvaluationStatus.MISSING_INPUT


def test_evaluate_parameterization_invalid_expression() -> None:
    result = evaluate_parameterization("a +", {"a": 1.0}, "y")
    assert result.status is ParameterizationEvaluationStatus.INVALID_EXPRESSION


def test_rewrite_parameterization_symbols_aliases() -> None:
    rewritten = rewrite_parameterization_symbols(
        "ca + cb",
        symbol_aliases={"y": ("ca",), "x": ("cb",)},
        symbol_targets={"y": "out", "x": "inp"},
    )
    assert rewritten == "out + inp"


# --- micropublications ----------------------------------------------------


def test_micropublication_coerce_from_mapping() -> None:
    micropub = coerce_active_micropublication(
        {"artifact_id": "m1", "context_id": "ctx", "claim_ids": ["k1", "k2"]}
    )
    assert isinstance(micropub, ActiveMicropublication)
    assert micropub.claim_ids == ("k1", "k2")
    assert coerce_active_micropublication(micropub) is micropub


def test_micropublication_requires_claims() -> None:
    with pytest.raises(ValueError):
        ActiveMicropublication(artifact_id="m1", context_id="ctx", claim_ids=())


# --- store_results --------------------------------------------------------


def test_store_result_hits_from_mapping() -> None:
    assert ConceptSearchHit.from_mapping({"concept_id": "c1"}).concept_id == "c1"
    claim_hit = ClaimSimilarityHit.from_mapping({"id": "k1", "distance": 0.5})
    assert claim_hit.claim_id == "k1"
    assert claim_hit.distance == 0.5
    concept_hit = ConceptSimilarityHit.from_mapping({"id": "c1", "distance": 0.25})
    assert concept_hit.concept_id == "c1"
    assert WorldStoreStats(concepts=1, claims=2, conflicts=0).claims == 2


# --- anytime --------------------------------------------------------------


def test_anytime_sentinels_report_partial_state() -> None:
    enum_exc = EnumerationExceeded(partial_count=3, max_candidates=10)
    assert enum_exc.remainder_provenance is ProvenanceStatus.VACUOUS
    assert "10 candidates" in str(enum_exc)
    budget = BudgetExhausted(steps_taken=7, max_steps=5)
    assert "5 steps" in str(budget)


# --- reporting ------------------------------------------------------------


def test_json_report_mixin_lowers_dataclass() -> None:
    from dataclasses import dataclass

    @dataclass
    class _Report(JsonReportMixin):
        name: str
        status: ProvenanceStatus

    report = _Report(name="r", status=ProvenanceStatus.MEASURED)
    assert report.to_json() == {"name": "r", "status": "measured"}
    assert json_ready([ProvenanceStatus.VACUOUS]) == ["vacuous"]


# --- store protocols typed over charters ----------------------------------


class _CharterStore:
    """A minimal store satisfying the charter-typed catalog protocols."""

    def all_concepts(self) -> list[Concept]:
        return [Concept(concept_id="c1", canonical_name="One")]

    def claims_for(self, concept_id: str | None) -> list[Claim]:
        return [Claim(claim_id="k1")]

    def stances_between(self, claim_ids: set[str]) -> list[object]:
        return []


def test_store_protocols_are_runtime_checkable_over_charters() -> None:
    store = _CharterStore()
    assert isinstance(store, ConceptCatalogStore)
    assert isinstance(store, ClaimCatalogStore)
    assert isinstance(store, StanceStore)
    # The umbrella protocol needs the full surface, which the minimal store lacks.
    assert not isinstance(store, WorldStore)


def test_world_store_protocol_methods_are_typed_over_charters() -> None:
    """The catalog protocols return charter domain objects, not ``*RowInput``.

    The annotations are ``TYPE_CHECKING``-only (string forms under
    ``from __future__ import annotations``), so importing ``core.environment``
    pulls in no charter module at runtime; we inspect the raw strings.
    """

    concept_return = ConceptCatalogStore.all_concepts.__annotations__["return"]
    assert concept_return == "Sequence[Concept]"
    claim_return = ClaimCatalogStore.claims_for.__annotations__["return"]
    assert claim_return == "Sequence[Claim]"

    all_returns = "".join(
        method.__annotations__.get("return", "")
        for method in vars(WorldStore).values()
        if callable(method)
    )
    assert "RowInput" not in all_returns


# --- layer rule: core must not import world -------------------------------


def test_core_does_not_import_world() -> None:
    core_dir = Path("propstore/core")
    assert core_dir.exists()
    offenders: list[tuple[str, int, str]] = []
    for py_file in core_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "propstore.world" or node.module.startswith(
                    "propstore.world."
                ):
                    offenders.append((str(py_file), node.lineno, node.module))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "propstore.world" or alias.name.startswith(
                        "propstore.world."
                    ):
                        offenders.append((str(py_file), node.lineno, alias.name))
    assert offenders == [], f"core imports world (layer violation): {offenders}"


def test_propagation_uses_human_to_sympy_not_raw_sympy() -> None:
    """propstore's parameterization evaluator goes through human-to-sympy."""

    source = Path("propstore/propagation.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    assert "sympy" not in imported_modules
    assert any(mod == "human_to_sympy" for mod in imported_modules)
