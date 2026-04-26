from __future__ import annotations

from argumentation.aspic import (
    ArgumentationSystem,
    ContrarinessFn,
    GroundAtom,
    KnowledgeBase,
    Literal,
    PreferenceConfig,
)
from argumentation.bipolar import BipolarArgumentationFramework
from argumentation.dung import ArgumentationFramework

from propstore.core.analyzers import SharedAnalyzerInput
from propstore.core.graph_types import ActiveWorldGraph, ClaimNode, CompiledWorldGraph
from propstore.core.results import AnalyzerResult, ClaimProjection
from propstore.merge.structured_merge import argumentation_evidence_from_projection
from propstore.probabilistic_relations import ClaimGraphRelations
from propstore.structured_projection import (
    StructuredProjection,
    claim_source_assertion_ids_from_active_graph,
    lift_analyzer_result_projection,
)
from propstore.world.types import (
    ArgumentationSemantics,
    ReasoningBackend,
    normalize_argumentation_semantics,
    supported_argumentation_semantics,
)


def _minimal_aspic_theory() -> tuple[
    ArgumentationSystem,
    KnowledgeBase,
    PreferenceConfig,
]:
    p = Literal(GroundAtom("p"))
    system = ArgumentationSystem(
        language=frozenset({p}),
        contrariness=ContrarinessFn(frozenset()),
        strict_rules=frozenset(),
        defeasible_rules=frozenset(),
    )
    kb = KnowledgeBase(axioms=frozenset(), premises=frozenset({p}))
    pref = PreferenceConfig(
        rule_order=frozenset(),
        premise_order=frozenset(),
        comparison="elitist",
        link="last",
    )
    return system, kb, pref


def test_track_e_package_semantics_are_exposed_by_propstore() -> None:
    assert (
        normalize_argumentation_semantics("praf-paper-td-complete")
        is ArgumentationSemantics.PRAF_PAPER_TD_COMPLETE
    )
    assert (
        normalize_argumentation_semantics("aspic-direct-grounded")
        is ArgumentationSemantics.ASPIC_DIRECT_GROUNDED
    )
    assert (
        normalize_argumentation_semantics("aspic-incomplete-grounded")
        is ArgumentationSemantics.ASPIC_INCOMPLETE_GROUNDED
    )

    assert (
        ArgumentationSemantics.PRAF_PAPER_TD_COMPLETE
        in supported_argumentation_semantics(ReasoningBackend.PRAF)
    )
    assert (
        ArgumentationSemantics.ASPIC_DIRECT_GROUNDED
        in supported_argumentation_semantics(ReasoningBackend.ASPIC)
    )
    assert (
        ArgumentationSemantics.ASPIC_INCOMPLETE_GROUNDED
        in supported_argumentation_semantics(ReasoningBackend.ASPIC)
    )


def test_track_e_projection_lift_preserves_situated_assertion_ids() -> None:
    active_graph = ActiveWorldGraph(
        compiled=CompiledWorldGraph(
            claims=(
                ClaimNode(
                    claim_id="claim_a",
                    claim_type="observation",
                    attributes={"source_assertion_ids": ("ps:assertion:a",)},
                ),
                ClaimNode(
                    claim_id="claim_b",
                    claim_type="observation",
                    attributes={"source_assertion_ids": ("ps:assertion:b",)},
                ),
            )
        ),
        active_claim_ids=("claim_a", "claim_b"),
    )
    result = AnalyzerResult(
        backend="praf",
        semantics="praf-paper-td-complete",
        projection=ClaimProjection(
            target_claim_ids=("claim_a", "claim_b"),
            survivor_claim_ids=("claim_a",),
            witness_claim_ids=("claim_a", "claim_b"),
        ),
    )

    lifted = lift_analyzer_result_projection(
        result,
        claim_source_assertion_ids_from_active_graph(active_graph),
    )

    assert lifted.backend == "praf"
    assert lifted.target_assertion_ids == ("ps:assertion:a", "ps:assertion:b")
    assert lifted.survivor_assertion_ids == ("ps:assertion:a",)
    assert lifted.witness_assertion_ids == ("ps:assertion:a", "ps:assertion:b")


def test_track_e_core_analyzer_reports_optional_aspic_backend_absence() -> None:
    from propstore.core.analyzers import analyze_aspic_backend

    system, kb, pref = _minimal_aspic_theory()

    result = analyze_aspic_backend(
        system,
        kb,
        pref,
        backend="clingo",
        semantics="grounded",
    )

    metadata = dict(result.metadata)
    assert result.backend == "aspic"
    assert result.semantics == "grounded"
    assert metadata["backend_requested"] == "clingo"
    assert metadata["package_status"] == "unavailable_backend"
    assert metadata["reason"] == "backend is not installed or registered"
    assert isinstance(metadata["encoding_signature"], str)
    assert result.extensions == ()


def test_track_e_praf_analyzer_can_use_paper_td_package_strategy() -> None:
    from propstore.core.analyzers import analyze_praf

    shared = SharedAnalyzerInput(
        active_graph=ActiveWorldGraph(
            compiled=CompiledWorldGraph(
                claims=(
                    ClaimNode(
                        claim_id="claim_a",
                        claim_type="observation",
                        attributes={"source_assertion_ids": ("ps:assertion:a",)},
                    ),
                )
            ),
            active_claim_ids=("claim_a",),
        ),
        comparison="elitist",
        claims_by_id={
            "claim_a": {
                "id": "claim_a",
                "source_prior_base_rate": 0.5,
            },
        },
        stance_rows=(),
        relations=ClaimGraphRelations(
            arguments=frozenset({"claim_a"}),
            attacks=frozenset(),
            direct_defeats=frozenset(),
            supports=frozenset(),
        ),
        argumentation_framework=ArgumentationFramework(
            arguments=frozenset({"claim_a"}),
            defeats=frozenset(),
            attacks=frozenset(),
        ),
        bipolar_framework=BipolarArgumentationFramework(
            arguments=frozenset({"claim_a"}),
            defeats=frozenset(),
            supports=frozenset(),
        ),
    )

    result = analyze_praf(
        shared,
        semantics="complete",
        strategy="paper_td",
        query_kind="extension_probability",
        inference_mode=None,
        queried_set=("claim_a",),
        target_claim_ids=("claim_a",),
    )

    metadata = dict(result.metadata)
    strategy_metadata = metadata["strategy_metadata"]
    assert metadata["strategy_used"] == "paper_td"
    assert metadata["extension_probability"] == 0.5
    assert strategy_metadata["paper_conformance"] == "popescu_wallner_2024_algorithm_1"
    assert result.projection is not None
    assert result.projection.survivor_claim_ids == ("claim_a",)


def test_track_e_merge_evidence_uses_argumentation_without_owning_policy() -> None:
    projection = StructuredProjection(
        arguments=(),
        framework=ArgumentationFramework(
            arguments=frozenset({"arg:a", "arg:b"}),
            defeats=frozenset({("arg:a", "arg:b")}),
            attacks=frozenset({("arg:a", "arg:b")}),
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

    evidence = argumentation_evidence_from_projection(
        branch="left",
        projection=projection,
        claim_assertion_ids={
            "claim_a": ("ps:assertion:a",),
            "claim_b": ("ps:assertion:b",),
        },
        semantics="grounded",
    )

    assert evidence.branch == "left"
    assert evidence.backend == "argumentation"
    assert evidence.semantics == "grounded"
    assert evidence.accepted_assertion_ids == ("ps:assertion:a",)
    assert evidence.decision_owner == "merge_policy"
