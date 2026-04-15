"""Tests for the intervention-ranked fragility system."""

from __future__ import annotations

import json
from collections.abc import Mapping
from types import MappingProxyType
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.fragility import (
    AssumptionTarget,
    BridgeUndercutTarget,
    FragilityReport,
    GroundFactTarget,
    GroundedRuleTarget,
    InteractionType,
    InterventionFamily,
    InterventionKind,
    InterventionProvenance,
    InterventionTarget,
    MissingMeasurementTarget,
    RankedIntervention,
    RankingPolicy,
    combine_fragility,
    collect_assumption_interventions,
    collect_bridge_undercut_interventions,
    collect_conflict_interventions,
    collect_ground_fact_interventions,
    collect_grounded_rule_interventions,
    collect_missing_measurement_interventions,
    detect_interactions,
    rank_fragility,
    score_conflict,
    weighted_epistemic_score,
)


class TestInterventionModel:
    def test_empty_report_defaults(self) -> None:
        report = FragilityReport()
        assert report.interventions == ()
        assert report.world_fragility == 0.0
        assert report.analysis_scope == ""

    def test_target_is_immutable_and_hashable(self) -> None:
        target = InterventionTarget(
            intervention_id="assumption:q1",
            kind=InterventionKind.ASSUMPTION,
            family=InterventionFamily.ATMS,
            subject_id=None,
            description="Check x == 1",
            cost_tier=1,
            provenance=InterventionProvenance(
                family=InterventionFamily.ATMS,
                source_ids=("queryable:q1",),
                subject_concept_ids=("c1",),
            ),
            payload=AssumptionTarget(
                queryable_id="queryable:q1",
                cel="x == 1",
                stabilizes_concepts=("c1",),
                witness_count=1,
                consistent_future_count=2,
            ),
        )
        assert hash(target)
        with pytest.raises(AttributeError):
            target.description = "mutate"  # type: ignore[misc]

    def test_ranked_intervention_requires_explicit_policy(self) -> None:
        ranked = RankedIntervention(
            target=InterventionTarget(
                intervention_id="missing_measurement:viscosity",
                kind=InterventionKind.MISSING_MEASUREMENT,
                family=InterventionFamily.DISCOVERY,
                subject_id="viscosity",
                description="Measure viscosity",
                cost_tier=3,
                provenance=InterventionProvenance(
                    family=InterventionFamily.DISCOVERY,
                    source_ids=("density",),
                    subject_concept_ids=("density",),
                ),
                payload=MissingMeasurementTarget(
                    concept_id="viscosity",
                    discovered_from_parameterizations=("density",),
                    downstream_subjects=("density",),
                ),
            ),
            local_fragility=0.5,
            roi=0.5 / 3.0,
            ranking_policy=RankingPolicy.HEURISTIC_ROI,
            score_explanation="heuristic",
        )
        assert ranked.ranking_policy is RankingPolicy.HEURISTIC_ROI


class TestUtilityScores:
    def test_combine_fragility_bounds(self) -> None:
        assert combine_fragility(None, None, None) == 0.0
        assert combine_fragility(0.8, None, None) == 0.8
        assert combine_fragility(0.8, 0.6, 0.2, "top2") == pytest.approx(0.7)

    def test_score_conflict_symmetric(self) -> None:
        from propstore.dung import ArgumentationFramework

        framework = ArgumentationFramework(
            arguments=frozenset({"A", "B"}),
            defeats=frozenset({("A", "B"), ("B", "A")}),
        )
        assert score_conflict(framework, "A", "B") == score_conflict(framework, "B", "A")

    def test_weighted_epistemic_score_applies_out_sign_correction(self) -> None:
        witnesses = [{"future_idx": 0}, {"future_idx": 1}]
        assert weighted_epistemic_score(witnesses, 4, current_in_extension=True) == pytest.approx(0.5)
        assert weighted_epistemic_score(witnesses, 4, current_in_extension=False) == pytest.approx(0.5)
        assert weighted_epistemic_score([{"future_idx": 0}], 4, current_in_extension=False) == pytest.approx(0.75)


def _mock_bound_for_atms(queryable_order: list[str]) -> MagicMock:
    bound = MagicMock()
    bound._store.all_parameterizations.return_value = [
        {
            "output_concept_id": "c1",
            "concept_ids": json.dumps(["x"]),
            "conditions_cel": json.dumps(queryable_order),
        }
    ]
    bound.active_claims.side_effect = lambda concept_id=None: [{"claim_id": "claim1"}] if concept_id == "c1" else []
    engine = MagicMock()
    engine.concept_stability.return_value = {
        "witnesses": [
            {"queryable_cels": [queryable_order[0]]},
            {"queryable_cels": [queryable_order[1]]},
        ],
        "consistent_future_count": 4,
        "stable": False,
        "current_status": "determined",
    }
    bound.atms_engine.return_value = engine
    bound.conflicts.return_value = []
    return bound


class TestATMSInterventions:
    @given(st.permutations(["x == 1", "y == 2"]))
    @settings(deadline=None)
    def test_queryable_order_does_not_change_assumption_ids(self, ordered_conditions: tuple[str, str]) -> None:
        from propstore.world.types import QueryableAssumption

        bound = _mock_bound_for_atms(list(ordered_conditions))
        ranked = collect_assumption_interventions(bound, ["c1"], None, atms_limit=8)
        assert {item.target.intervention_id for item in ranked} == {
            f"assumption:{QueryableAssumption.from_cel('x == 1').assumption_id}",
            f"assumption:{QueryableAssumption.from_cel('y == 2').assumption_id}",
        }
        assert all(item.target.kind is InterventionKind.ASSUMPTION for item in ranked)

    def test_rank_fragility_returns_assumption_interventions_not_concepts(self) -> None:
        bound = _mock_bound_for_atms(["x == 1", "y == 2"])
        report = rank_fragility(
            bound,
            include_atms=True,
            include_discovery=False,
            include_conflict=False,
            include_grounding=False,
            include_bridge=False,
        )
        assert report.interventions
        assert all(item.target.kind is InterventionKind.ASSUMPTION for item in report.interventions)


class TestMissingMeasurementInterventions:
    @given(st.permutations(["viscosity", "temperature"]))
    @settings(deadline=None)
    def test_parameterization_order_does_not_change_missing_measurement_ids(self, inputs: tuple[str, str]) -> None:
        bound = MagicMock()
        bound._store.all_parameterizations.return_value = [
            {
                "output_concept_id": "density",
                "concept_ids": json.dumps(list(inputs)),
                "sympy": "density",
            }
        ]
        bound.active_claims.return_value = []
        ranked = collect_missing_measurement_interventions(bound, ["density"])
        assert {item.target.intervention_id for item in ranked} == {
            "missing_measurement:temperature",
            "missing_measurement:viscosity",
        }
        assert all(item.target.kind is InterventionKind.MISSING_MEASUREMENT for item in ranked)


class TestConflictInterventions:
    def test_conflict_identity_is_symmetric(self) -> None:
        bound = MagicMock()
        bound.conflicts.return_value = [
            MagicMock(claim_a_id="b", claim_b_id="a", concept_id="c1"),
        ]
        bound._active_graph = MagicMock()
        ranked = collect_conflict_interventions(bound, ["c1"])
        assert len(ranked) == 1
        assert ranked[0].target.intervention_id == "conflict:a:b"
        assert ranked[0].target.kind is InterventionKind.CONFLICT


def _var(name: str):
    from propstore.artifacts.documents.rules import TermDocument

    return TermDocument(kind="var", name=name)


def _atom(predicate: str, terms=(), *, negated: bool = False):
    from propstore.artifacts.documents.rules import AtomDocument

    return AtomDocument(predicate=predicate, terms=tuple(terms), negated=negated)


def _rule_doc(rule_id: str, kind: str, head, *, body=()):
    from propstore.artifacts.documents.rules import RuleDocument

    return RuleDocument(id=rule_id, kind=kind, head=head, body=tuple(body))


def _rule_file(rules):
    from propstore.artifacts.documents.rules import RuleSourceDocument, RulesFileDocument
    from propstore.loaded import LoadedDocument
    from propstore.rule_files import LoadedRuleFile

    file_doc = RulesFileDocument(
        source=RuleSourceDocument(paper="fragility-test"),
        rules=tuple(rules),
    )
    loaded = LoadedDocument(
        filename="generated.yaml",
        source_path=None,
        knowledge_root=None,
        document=file_doc,
    )
    return LoadedRuleFile.from_loaded_document(loaded)


def _bundle(
    *,
    rules=(),
    definitely: Mapping[str, frozenset[tuple]] | None = None,
    defeasibly: Mapping[str, frozenset[tuple]] | None = None,
    not_defeasibly: Mapping[str, frozenset[tuple]] | None = None,
    undecided: Mapping[str, frozenset[tuple]] | None = None,
):
    from propstore.grounding.bundle import GroundedRulesBundle

    def _freeze(section: Mapping[str, frozenset[tuple]] | None):
        if section is None:
            return MappingProxyType({})
        return MappingProxyType({key: frozenset(value) for key, value in section.items()})

    return GroundedRulesBundle(
        source_rules=tuple([_rule_file(rules)] if rules else []),
        source_facts=(),
        sections=MappingProxyType(
            {
                "definitely": _freeze(definitely),
                "defeasibly": _freeze(defeasibly),
                "not_defeasibly": _freeze(not_defeasibly),
                "undecided": _freeze(undecided),
            }
        ),
    )


class TestGroundFactInterventions:
    @given(st.permutations([("bird", ("tweety",)), ("bird", ("opus",))]))
    @settings(deadline=None)
    def test_ground_fact_identities_are_permutation_invariant(
        self,
        ordered_facts: tuple[tuple[str, tuple[str, ...]], tuple[str, tuple[str, ...]]],
    ) -> None:
        rows = frozenset(row for _pred, row in ordered_facts)
        bundle = _bundle(definitely={"bird": rows})
        ranked = collect_ground_fact_interventions(bundle)
        assert {item.target.intervention_id for item in ranked} == {
            'ground_fact:definitely:bird:[{"type":"str","value":"opus"}]',
            'ground_fact:definitely:bird:[{"type":"str","value":"tweety"}]',
        }
        assert all(item.target.kind is InterventionKind.GROUND_FACT for item in ranked)

    def test_ground_fact_score_reflects_dependency_count(self) -> None:
        rule = _rule_doc(
            "rule:birds-fly",
            "defeasible",
            _atom("flies", (_var("X"),)),
            body=(_atom("bird", (_var("X"),)),),
        )
        supporting_bundle = _bundle(
            rules=(rule,),
            definitely={"bird": frozenset({("tweety",)})},
        )
        unused_bundle = _bundle(
            definitely={"bird": frozenset({("tweety",)})},
        )
        supporting = collect_ground_fact_interventions(supporting_bundle)[0]
        unused = collect_ground_fact_interventions(unused_bundle)[0]
        assert supporting.local_fragility > unused.local_fragility
        assert "antecedent_dependency_count=1" in supporting.score_explanation
        assert "antecedent_dependency_count=0" in unused.score_explanation


class TestGroundedRuleInterventions:
    def test_rule_with_n_substitutions_emits_n_grounded_rule_ids(self) -> None:
        rule = _rule_doc(
            "rule:birds-fly",
            "defeasible",
            _atom("flies", (_var("X"),)),
            body=(_atom("bird", (_var("X"),)),),
        )
        bundle = _bundle(
            rules=(rule,),
            definitely={"bird": frozenset({("tweety",), ("opus",)})},
        )
        ranked = collect_grounded_rule_interventions(bundle)
        assert len(ranked) == 2
        ids = {item.target.intervention_id for item in ranked}
        assert any("tweety" in intervention_id for intervention_id in ids)
        assert any("opus" in intervention_id for intervention_id in ids)
        assert all(item.target.kind is InterventionKind.GROUNDED_RULE for item in ranked)

    def test_grounded_rule_score_increases_when_undercuttable(self) -> None:
        target_rule = _rule_doc(
            "rule:birds-fly",
            "defeasible",
            _atom("flies", (_var("X"),)),
            body=(_atom("bird", (_var("X"),)),),
        )
        defeater_rule = _rule_doc(
            "rule:broken-wing",
            "defeater",
            _atom("flies", (_var("X"),), negated=True),
            body=(_atom("broken_wing", (_var("X"),)),),
        )
        defended_bundle = _bundle(
            rules=(target_rule,),
            definitely={"bird": frozenset({("tweety",)})},
        )
        undercut_bundle = _bundle(
            rules=(target_rule, defeater_rule),
            definitely={
                "bird": frozenset({("tweety",)}),
                "broken_wing": frozenset({("tweety",)}),
            },
        )
        defended = collect_grounded_rule_interventions(defended_bundle)[0]
        undercut = next(
            item for item in collect_grounded_rule_interventions(undercut_bundle)
            if item.target.payload.rule_name.startswith("rule:birds-fly#")
        )
        assert undercut.local_fragility > defended.local_fragility
        assert "undercut_count=1" in undercut.score_explanation


class TestBridgeUndercutInterventions:
    def test_bridge_undercut_identities_stable_across_rebuilds(self) -> None:
        target_rule = _rule_doc(
            "rule:birds-fly",
            "defeasible",
            _atom("flies", (_var("X"),)),
            body=(_atom("bird", (_var("X"),)),),
        )
        defeater_rule = _rule_doc(
            "rule:broken-wing",
            "defeater",
            _atom("flies", (_var("X"),), negated=True),
            body=(_atom("broken_wing", (_var("X"),)),),
        )
        bundle = _bundle(
            rules=(target_rule, defeater_rule),
            definitely={
                "bird": frozenset({("tweety",)}),
                "broken_wing": frozenset({("tweety",)}),
            },
        )
        first = collect_bridge_undercut_interventions(bundle, (), [], ())
        second = collect_bridge_undercut_interventions(bundle, (), [], ())
        assert {item.target.intervention_id for item in first} == {
            'bridge_undercut:rule:broken-wing#{"X":{"type":"str","value":"tweety"}}->rule:birds-fly#{"X":{"type":"str","value":"tweety"}}'
        }
        assert {item.target.intervention_id for item in first} == {
            item.target.intervention_id for item in second
        }
        assert all(item.target.kind is InterventionKind.BRIDGE_UNDERCUT for item in first)

    def test_bridge_undercut_score_tracks_attack_and_defeat_counts(self) -> None:
        target_rule = _rule_doc(
            "rule:birds-fly",
            "defeasible",
            _atom("flies", (_var("X"),)),
            body=(_atom("bird", (_var("X"),)),),
        )
        defeater_rule = _rule_doc(
            "rule:broken-wing",
            "defeater",
            _atom("flies", (_var("X"),), negated=True),
            body=(_atom("broken_wing", (_var("X"),)),),
        )
        bundle = _bundle(
            rules=(target_rule, defeater_rule),
            definitely={
                "bird": frozenset({("tweety",)}),
                "broken_wing": frozenset({("tweety",)}),
            },
        )
        ranked = collect_bridge_undercut_interventions(bundle, (), [], ())
        assert len(ranked) == 1
        assert ranked[0].local_fragility > 0.3
        assert "attack_count=" in ranked[0].score_explanation
        assert "defeat_count=" in ranked[0].score_explanation


class TestInteractions:
    def test_detect_interactions_returns_unknown_without_bound(self) -> None:
        interventions = [
            RankedIntervention(
                target=InterventionTarget(
                    intervention_id="assumption:q1",
                    kind=InterventionKind.ASSUMPTION,
                    family=InterventionFamily.ATMS,
                    subject_id=None,
                    description="A",
                    cost_tier=1,
                    provenance=InterventionProvenance(
                        family=InterventionFamily.ATMS,
                        source_ids=("q1",),
                        subject_concept_ids=("c1",),
                    ),
                    payload=AssumptionTarget(
                        queryable_id="q1",
                        cel="x == 1",
                        stabilizes_concepts=("c1",),
                        witness_count=1,
                        consistent_future_count=2,
                    ),
                ),
                local_fragility=0.5,
                roi=0.5,
                ranking_policy=RankingPolicy.HEURISTIC_ROI,
                score_explanation="heuristic",
            ),
            RankedIntervention(
                target=InterventionTarget(
                    intervention_id="assumption:q2",
                    kind=InterventionKind.ASSUMPTION,
                    family=InterventionFamily.ATMS,
                    subject_id=None,
                    description="B",
                    cost_tier=1,
                    provenance=InterventionProvenance(
                        family=InterventionFamily.ATMS,
                        source_ids=("q2",),
                        subject_concept_ids=("c1",),
                    ),
                    payload=AssumptionTarget(
                        queryable_id="q2",
                        cel="y == 2",
                        stabilizes_concepts=("c1",),
                        witness_count=1,
                        consistent_future_count=2,
                    ),
                ),
                local_fragility=0.4,
                roi=0.4,
                ranking_policy=RankingPolicy.HEURISTIC_ROI,
                score_explanation="heuristic",
            ),
        ]
        interactions = detect_interactions(interventions, None)
        assert len(interactions) == 1
        assert interactions[0].interaction_type is InteractionType.UNKNOWN


class TestRankFragility:
    def test_rank_fragility_supports_explicit_ranking_policy(self) -> None:
        import inspect

        sig = inspect.signature(rank_fragility)
        assert "ranking_policy" in sig.parameters

    def test_bound_world_still_exposes_fragility_method(self) -> None:
        from propstore.world.bound import BoundWorld

        assert hasattr(BoundWorld, "fragility")

    def test_heuristic_roi_policy_sorts_by_roi(self) -> None:
        from unittest.mock import patch

        bound = MagicMock()
        with patch("propstore.fragility.derive_scored_concepts", return_value=["c1"]), \
             patch("propstore.fragility.collect_assumption_interventions", return_value=()), \
             patch(
                 "propstore.fragility.collect_missing_measurement_interventions",
                 return_value=(
                     RankedIntervention(
                         target=InterventionTarget(
                             intervention_id="missing_measurement:expensive",
                             kind=InterventionKind.MISSING_MEASUREMENT,
                             family=InterventionFamily.DISCOVERY,
                             subject_id="expensive",
                             description="expensive",
                             cost_tier=3,
                             provenance=InterventionProvenance(
                                 family=InterventionFamily.DISCOVERY,
                                 source_ids=("x",),
                                 subject_concept_ids=("x",),
                             ),
                             payload=MissingMeasurementTarget(
                                 concept_id="expensive",
                                 discovered_from_parameterizations=("x",),
                                 downstream_subjects=("x",),
                             ),
                         ),
                         local_fragility=0.9,
                         roi=0.3,
                         ranking_policy=RankingPolicy.HEURISTIC_ROI,
                         score_explanation="expensive",
                     ),
                     RankedIntervention(
                         target=InterventionTarget(
                             intervention_id="missing_measurement:cheap",
                             kind=InterventionKind.MISSING_MEASUREMENT,
                             family=InterventionFamily.DISCOVERY,
                             subject_id="cheap",
                             description="cheap",
                             cost_tier=1,
                             provenance=InterventionProvenance(
                                 family=InterventionFamily.DISCOVERY,
                                 source_ids=("y",),
                                 subject_concept_ids=("y",),
                             ),
                             payload=MissingMeasurementTarget(
                                 concept_id="cheap",
                                 discovered_from_parameterizations=("y",),
                                 downstream_subjects=("y",),
                             ),
                         ),
                         local_fragility=0.6,
                         roi=0.6,
                         ranking_policy=RankingPolicy.HEURISTIC_ROI,
                         score_explanation="cheap",
                     ),
                 ),
             ), \
             patch("propstore.fragility.collect_conflict_interventions", return_value=()), \
             patch("propstore.fragility.collect_ground_fact_interventions", return_value=()), \
             patch("propstore.fragility.collect_grounded_rule_interventions", return_value=()), \
             patch("propstore.fragility.collect_bridge_undercut_interventions", return_value=()), \
             patch("propstore.fragility.build_bound_bridge_inputs", return_value=((), [], [])):
            report = rank_fragility(bound, ranking_policy=RankingPolicy.HEURISTIC_ROI)
        assert [item.target.subject_id for item in report.interventions] == ["cheap", "expensive"]

    def test_pareto_policy_drops_dominated_intervention(self) -> None:
        from unittest.mock import patch

        bound = MagicMock()
        dominated = RankedIntervention(
            target=InterventionTarget(
                intervention_id="missing_measurement:dominated",
                kind=InterventionKind.MISSING_MEASUREMENT,
                family=InterventionFamily.DISCOVERY,
                subject_id="dominated",
                description="dominated",
                cost_tier=3,
                provenance=InterventionProvenance(
                    family=InterventionFamily.DISCOVERY,
                    source_ids=("d",),
                    subject_concept_ids=("d",),
                ),
                payload=MissingMeasurementTarget(
                    concept_id="dominated",
                    discovered_from_parameterizations=("d",),
                    downstream_subjects=("d",),
                ),
            ),
            local_fragility=0.4,
            roi=0.4 / 3.0,
            ranking_policy=RankingPolicy.HEURISTIC_ROI,
            score_explanation="dominated",
        )
        dominant = RankedIntervention(
            target=InterventionTarget(
                intervention_id="missing_measurement:dominant",
                kind=InterventionKind.MISSING_MEASUREMENT,
                family=InterventionFamily.DISCOVERY,
                subject_id="dominant",
                description="dominant",
                cost_tier=2,
                provenance=InterventionProvenance(
                    family=InterventionFamily.DISCOVERY,
                    source_ids=("x",),
                    subject_concept_ids=("x",),
                ),
                payload=MissingMeasurementTarget(
                    concept_id="dominant",
                    discovered_from_parameterizations=("x",),
                    downstream_subjects=("x",),
                ),
            ),
            local_fragility=0.8,
            roi=0.4,
            ranking_policy=RankingPolicy.HEURISTIC_ROI,
            score_explanation="dominant",
        )
        with patch("propstore.fragility.derive_scored_concepts", return_value=["c1"]), \
             patch("propstore.fragility.collect_assumption_interventions", return_value=()), \
             patch("propstore.fragility.collect_missing_measurement_interventions", return_value=(dominated, dominant)), \
             patch("propstore.fragility.collect_conflict_interventions", return_value=()), \
             patch("propstore.fragility.collect_ground_fact_interventions", return_value=()), \
             patch("propstore.fragility.collect_grounded_rule_interventions", return_value=()), \
             patch("propstore.fragility.collect_bridge_undercut_interventions", return_value=()), \
             patch("propstore.fragility.build_bound_bridge_inputs", return_value=((), [], [])):
            report = rank_fragility(bound, ranking_policy=RankingPolicy.PARETO)
        assert [item.target.subject_id for item in report.interventions] == ["dominant"]
