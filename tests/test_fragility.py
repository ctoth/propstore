"""Tests for the intervention-ranked fragility system.

Porting notes (Phase 7b-3 rewrite):

* The semiring value objects (``ProvenanceNogood``/``ProvenancePolynomial``/…)
  come from ``provenance_semiring`` directly; ``propstore.provenance`` keeps only
  the lemon ``Provenance``/``ProvenanceStatus``. ``ProvenanceNogood`` is now the
  two-argument ``(variables, witness)`` form.
* ``Opinion`` is ``doxa.Opinion`` (no provenance field); ``imps_rev`` takes the
  canonical provenance-paired :class:`OpinionWithProvenance`, so the old
  "rejects a provenance-free opinion" case is now enforced by the type rather
  than a runtime check and is dropped.
* The grounding/bridge families consume the typed ``DefeasibleRule`` grounding
  surface directly. Undecorated section predicates retain the production
  positive-only decode until a complement encoder exists.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import gunray
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.core.graph_types import ParameterizationEdge
from propstore.families.rules import Atom, BodyLiteral, DefeasibleRule, Term
from propstore.fragility import (
    AssumptionTarget,
    FragilityReport,
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
    support_derivative_fragility,
    weighted_epistemic_score,
)
from propstore.fragility_contributors import _in_extension
from propstore.grounding.grounder import ground
from propstore.grounding.predicates import PredicateRegistry
from propstore.provenance import Provenance, ProvenanceStatus
from propstore.world.types import (
    ATMSConceptFutureStatusEntry,
    ATMSConceptStabilityReport,
    QueryableAssumption,
    ValueStatus,
)
from provenance_semiring import (
    NogoodWitness,
    ProvenanceNogood,
    ProvenancePolynomial,
    SourceVariableId,
    SupportEvidence,
    SupportQuality,
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

    def test_unknown_value_status_is_not_in_extension(self) -> None:
        with pytest.raises(ValueError, match="Unknown value status"):
            _in_extension("not-a-status")

    def test_target_rejects_payload_that_does_not_match_kind(self) -> None:
        with pytest.raises(TypeError, match="payload"):
            InterventionTarget(
                intervention_id="assumption:q1",
                kind=InterventionKind.ASSUMPTION,
                family=InterventionFamily.ATMS,
                subject_id="c1",
                description="Check x == 1",
                cost_tier=1,
                provenance=InterventionProvenance(
                    family=InterventionFamily.ATMS,
                    source_ids=("queryable:q1",),
                    subject_concept_ids=("c1",),
                ),
                payload=MissingMeasurementTarget(
                    concept_id="c1",
                    discovered_from_parameterizations=("p1",),
                    downstream_subjects=("c1",),
                ),
            )

    def test_target_rejects_family_provenance_mismatch(self) -> None:
        with pytest.raises(ValueError, match="provenance"):
            InterventionTarget(
                intervention_id="assumption:q1",
                kind=InterventionKind.ASSUMPTION,
                family=InterventionFamily.ATMS,
                subject_id="c1",
                description="Check x == 1",
                cost_tier=1,
                provenance=InterventionProvenance(
                    family=InterventionFamily.DISCOVERY,
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

    def test_target_rejects_non_positive_cost_tier(self) -> None:
        with pytest.raises(ValueError, match="cost_tier"):
            InterventionTarget(
                intervention_id="assumption:q1",
                kind=InterventionKind.ASSUMPTION,
                family=InterventionFamily.ATMS,
                subject_id="c1",
                description="Check x == 1",
                cost_tier=0,
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

    def test_ranked_intervention_rejects_fragility_out_of_bounds(self) -> None:
        target = InterventionTarget(
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
        )
        with pytest.raises(ValueError, match="local_fragility"):
            RankedIntervention(
                target=target,
                local_fragility=1.1,
                roi=1.1 / 3.0,
                ranking_policy=RankingPolicy.HEURISTIC_ROI,
                score_explanation="heuristic",
            )

    def test_ranked_intervention_rejects_negative_roi(self) -> None:
        target = InterventionTarget(
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
        )
        with pytest.raises(ValueError, match="roi"):
            RankedIntervention(
                target=target,
                local_fragility=0.5,
                roi=-0.1,
                ranking_policy=RankingPolicy.HEURISTIC_ROI,
                score_explanation="heuristic",
            )


class TestUtilityScores:
    def test_combine_fragility_bounds(self) -> None:
        assert combine_fragility(None, None, None) == 0.0
        assert combine_fragility(0.8, None, None) == 0.8
        assert combine_fragility(0.8, 0.6, 0.2, "top2") == pytest.approx(0.7)

    def test_score_conflict_symmetric(self) -> None:
        from argumentation.core.dung import ArgumentationFramework

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

    def test_support_derivative_fragility_uses_live_support(self) -> None:
        a = SourceVariableId("ps:source:assumption:a")
        b = SourceVariableId("ps:source:assumption:b")
        support = ProvenancePolynomial.variable(a) + (
            ProvenancePolynomial.variable(a) * ProvenancePolynomial.variable(b)
        )
        nogood = ProvenanceNogood(
            frozenset((a, b)),
            NogoodWitness("test", "dead joint witness"),
        )

        assert support_derivative_fragility(
            support,
            a,
            live_nogoods=(nogood,),
            total_worlds=4,
        ) == pytest.approx(0.25)
        assert support_derivative_fragility(
            support,
            b,
            live_nogoods=(nogood,),
            total_worlds=4,
        ) == 0.0

    def test_imps_rev_requires_explicit_probabilistic_inputs(self) -> None:
        from argumentation.core.dung import ArgumentationFramework

        from propstore.fragility import imps_rev

        framework = ArgumentationFramework(
            arguments=frozenset({"A", "B"}),
            defeats=frozenset({("A", "B")}),
        )

        with pytest.raises(TypeError):
            imps_rev(framework, {}, {"A": 1.0, "B": 0.0}, ("A", "B"))  # type: ignore[call-arg]

    def test_imps_rev_uses_supplied_opinions_without_fabricating_certainty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from argumentation.core.dung import ArgumentationFramework
        from doxa import Opinion

        from propstore.fragility import imps_rev
        from propstore.opinion_provenance import OpinionWithProvenance

        framework = ArgumentationFramework(
            arguments=frozenset({"A", "B"}),
            defeats=frozenset({("A", "B")}),
        )
        provenance = Provenance(status=ProvenanceStatus.VACUOUS, witnesses=())
        p_args = {
            "A": OpinionWithProvenance(opinion=Opinion.vacuous(0.5), provenance=provenance),
            "B": OpinionWithProvenance(opinion=Opinion.vacuous(0.5), provenance=provenance),
        }
        p_defeats = {
            ("A", "B"): OpinionWithProvenance(opinion=Opinion.vacuous(0.5), provenance=provenance)
        }
        seen: list[tuple[object, object, object]] = []

        def fake_dfquad(graph: object, *, base_scores: object, support_weights: object) -> object:
            seen.append((graph, base_scores, support_weights))

            class Result:
                strengths = {"A": 1.0, "B": 0.25 if len(seen) == 1 else 0.75}

            return Result()

        monkeypatch.setattr(
            "argumentation.gradual.dfquad.dfquad_strengths",
            fake_dfquad,
        )

        score = imps_rev(
            framework,
            {},
            {"A": 1.0, "B": 0.0},
            ("A", "B"),
            p_args=p_args,
            p_defeats=p_defeats,
        )

        assert score == pytest.approx(0.5)
        assert seen[0][0].initial_weights == {"A": 1.0, "B": 0.0}
        assert seen[0][0].attacks == frozenset({("A", "B")})
        assert seen[0][1] == {"A": 1.0, "B": 0.0}
        assert seen[1][0].initial_weights == {"A": 1.0, "B": 0.0}
        assert seen[1][0].attacks == frozenset()
        assert seen[1][1] == {"A": 1.0, "B": 0.0}


def _mock_bound_for_atms(queryable_order: list[str]) -> MagicMock:
    bound = MagicMock()
    bound.store.all_parameterizations.return_value = [
        ParameterizationEdge(
            output_concept_id="c1",
            input_concept_ids=("x",),
            conditions=tuple(queryable_order),
        )
    ]
    bound.active_claims.side_effect = (
        lambda concept_id=None: [{"claim_id": "claim1"}] if concept_id == "c1" else []
    )
    engine = MagicMock()
    queryables = [QueryableAssumption.from_cel(cel) for cel in queryable_order]
    engine.concept_stability.return_value = ATMSConceptStabilityReport(
        concept_id="c1",
        current_status=ValueStatus.DETERMINED,
        stable=False,
        limit=8,
        future_count=4,
        consistent_future_count=4,
        inconsistent_future_count=0,
        witnesses=tuple(
            ATMSConceptFutureStatusEntry(
                queryable_ids=(queryable.assumption_id,),
                queryable_cels=(queryable.cel,),
                environment=(queryable.assumption_id,),
                consistent=True,
                status=ValueStatus.DETERMINED,
                supported_claim_ids=("claim1",),
            )
            for queryable in queryables
        ),
    )
    bound.atms_engine.return_value = engine
    bound.conflicts.return_value = []
    return bound


class TestATMSInterventions:
    @pytest.mark.property
    @given(st.permutations(["x == 1", "y == 2"]))
    @settings(deadline=None)
    def test_queryable_order_does_not_change_assumption_ids(self, ordered_conditions: tuple[str, str]) -> None:
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

    def test_assumption_interventions_carry_derivative_support(self) -> None:
        bound = _mock_bound_for_atms(["x == 1", "y == 2"])
        ranked = collect_assumption_interventions(bound, ["c1"], None, atms_limit=8)

        assert ranked
        assert all(item.local_fragility == pytest.approx(0.25) for item in ranked)
        for item in ranked:
            support = item.target.provenance.support
            assert isinstance(support, SupportEvidence)
            assert support.quality is SupportQuality.EXACT
            assert support.polynomial != ProvenancePolynomial.zero()


class TestMissingMeasurementInterventions:
    @pytest.mark.property
    @given(st.permutations(["viscosity", "temperature"]))
    @settings(deadline=None)
    def test_parameterization_order_does_not_change_missing_measurement_ids(self, inputs: tuple[str, str]) -> None:
        bound = MagicMock()
        bound.store.all_parameterizations.return_value = [
            ParameterizationEdge(
                output_concept_id="density",
                input_concept_ids=tuple(inputs),
            )
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
        bound.active_graph = MagicMock()
        ranked = collect_conflict_interventions(bound, ["c1"])
        assert len(ranked) == 1
        assert ranked[0].target.intervention_id == "conflict:a:b"
        assert ranked[0].target.kind is InterventionKind.CONFLICT


def test_non_empty_grounding_bundle_drives_fragility_collectors() -> None:
    variable = Term(kind="var", name="X")
    bundle = ground(
        (
            DefeasibleRule(
                rule_id="rule:birds-fly",
                kind="defeasible",
                head=Atom(predicate="flies", terms=(variable,)),
                body=(
                    BodyLiteral(
                        kind="positive",
                        atom=Atom(predicate="bird", terms=(variable,)),
                    ),
                ),
            ),
            DefeasibleRule(
                rule_id="rule:penguins-do-not-fly",
                kind="proper_defeater",
                head=Atom(predicate="flies", terms=(variable,), negated=True),
                body=(
                    BodyLiteral(
                        kind="positive",
                        atom=Atom(predicate="penguin", terms=(variable,)),
                    ),
                ),
            ),
        ),
        (
            gunray.GroundAtom(predicate="bird", arguments=("tweety",)),
            gunray.GroundAtom(predicate="penguin", arguments=("tweety",)),
        ),
        PredicateRegistry.from_documents(()),
    )

    fact_interventions = collect_ground_fact_interventions(bundle)
    rule_interventions = collect_grounded_rule_interventions(bundle)
    bridge_interventions = collect_bridge_undercut_interventions(bundle, (), [], ())

    assert fact_interventions
    assert all(
        item.target.kind is InterventionKind.GROUND_FACT
        and item.target.family is InterventionFamily.GROUNDING
        for item in fact_interventions
    )
    assert rule_interventions
    assert all(
        item.target.kind is InterventionKind.GROUNDED_RULE
        and item.target.family is InterventionFamily.GROUNDING
        for item in rule_interventions
    )
    assert bridge_interventions
    assert all(
        item.target.kind is InterventionKind.BRIDGE_UNDERCUT
        and item.target.family is InterventionFamily.BRIDGE
        for item in bridge_interventions
    )


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

    def test_bound_world_does_not_own_fragility_adapter(self) -> None:
        from propstore.fragility import query_fragility
        from propstore.world.bound import BoundWorld

        assert callable(query_fragility)
        assert not hasattr(BoundWorld, "fragility")

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

    def test_family_local_only_relabels_items_and_sorts_within_family(self) -> None:
        from unittest.mock import patch

        bound = MagicMock()
        atms_low = RankedIntervention(
            target=InterventionTarget(
                intervention_id="assumption:low",
                kind=InterventionKind.ASSUMPTION,
                family=InterventionFamily.ATMS,
                subject_id="low",
                description="low",
                cost_tier=1,
                provenance=InterventionProvenance(
                    family=InterventionFamily.ATMS,
                    source_ids=("a-low",),
                    subject_concept_ids=("low",),
                ),
                payload=AssumptionTarget(
                    queryable_id="a-low",
                    cel="a_low == true",
                    stabilizes_concepts=("low",),
                    witness_count=1,
                    consistent_future_count=2,
                ),
            ),
            local_fragility=0.2,
            roi=0.2,
            ranking_policy=RankingPolicy.HEURISTIC_ROI,
            score_explanation="atms low",
        )
        atms_high = RankedIntervention(
            target=InterventionTarget(
                intervention_id="assumption:high",
                kind=InterventionKind.ASSUMPTION,
                family=InterventionFamily.ATMS,
                subject_id="high",
                description="high",
                cost_tier=1,
                provenance=InterventionProvenance(
                    family=InterventionFamily.ATMS,
                    source_ids=("a-high",),
                    subject_concept_ids=("high",),
                ),
                payload=AssumptionTarget(
                    queryable_id="a-high",
                    cel="a_high == true",
                    stabilizes_concepts=("high",),
                    witness_count=2,
                    consistent_future_count=2,
                ),
            ),
            local_fragility=0.9,
            roi=0.9,
            ranking_policy=RankingPolicy.HEURISTIC_ROI,
            score_explanation="atms high",
        )
        discovery = RankedIntervention(
            target=InterventionTarget(
                intervention_id="missing_measurement:zeta",
                kind=InterventionKind.MISSING_MEASUREMENT,
                family=InterventionFamily.DISCOVERY,
                subject_id="zeta",
                description="zeta",
                cost_tier=3,
                provenance=InterventionProvenance(
                    family=InterventionFamily.DISCOVERY,
                    source_ids=("zeta",),
                    subject_concept_ids=("zeta",),
                ),
                payload=MissingMeasurementTarget(
                    concept_id="zeta",
                    discovered_from_parameterizations=("zeta",),
                    downstream_subjects=("zeta",),
                ),
            ),
            local_fragility=0.8,
            roi=0.8 / 3.0,
            ranking_policy=RankingPolicy.HEURISTIC_ROI,
            score_explanation="discovery",
        )
        with patch("propstore.fragility.derive_scored_concepts", return_value=["c1"]), \
             patch("propstore.fragility.collect_assumption_interventions", return_value=(atms_low, atms_high)), \
             patch("propstore.fragility.collect_missing_measurement_interventions", return_value=(discovery,)), \
             patch("propstore.fragility.collect_conflict_interventions", return_value=()), \
             patch("propstore.fragility.collect_ground_fact_interventions", return_value=()), \
             patch("propstore.fragility.collect_grounded_rule_interventions", return_value=()), \
             patch("propstore.fragility.collect_bridge_undercut_interventions", return_value=()), \
             patch("propstore.fragility.build_bound_bridge_inputs", return_value=((), [], [])):
            report = rank_fragility(bound, ranking_policy=RankingPolicy.FAMILY_LOCAL_ONLY)
        assert [item.target.intervention_id for item in report.interventions] == [
            "assumption:high",
            "assumption:low",
            "missing_measurement:zeta",
        ]
        assert all(
            item.ranking_policy is RankingPolicy.FAMILY_LOCAL_ONLY
            for item in report.interventions
        )

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
        assert report.interventions[0].ranking_policy is RankingPolicy.PARETO
