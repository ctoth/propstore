"""Executable epistemic process manager tests."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.fragility import (
    AssumptionTarget,
    FragilityReport,
    InterventionFamily,
    InterventionKind,
    InterventionProvenance,
    InterventionTarget,
    RankedIntervention,
    RankingPolicy,
)
from propstore.policies import PolicyProfile, default_policy_profile
from propstore.support_revision.history import (
    EpistemicSnapshot,
    JournalOperator,
    TransitionJournalEntry,
    TransitionOperation,
)
from propstore.support_revision.iterated import iterated_revise, make_epistemic_state
from propstore.support_revision.snapshot_types import belief_atom_to_canonical_dict
from propstore.world.types import (
    ATMSNodeInterventionPlan,
    ATMSNodeStatus,
)
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_iterated import _history_sensitive_base


def test_investigation_plan_from_fragility_report_roundtrips_with_stable_identity() -> (
    None
):
    from propstore.epistemic_process import InvestigationPlan

    report = FragilityReport(
        interventions=(
            _ranked_intervention("assumption:temperature", "temperature == 300"),
            _ranked_intervention("assumption:pressure", "pressure == 2"),
        ),
        world_fragility=0.4,
        analysis_scope="subject:enthalpy",
    )

    plan = InvestigationPlan.from_fragility_report(
        report,
        objective="stabilize-fragile-world",
    )
    restored = InvestigationPlan.from_dict(plan.to_dict())

    assert plan.plan_id.startswith("urn:propstore:investigation-plan:")
    assert plan.intervention_ids == ("assumption:temperature", "assumption:pressure")
    assert plan.objective == "stabilize-fragile-world"
    assert restored == plan
    assert restored.content_hash == plan.content_hash


def test_public_fragility_investigation_path_reuses_fragility_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from propstore.epistemic_process import plan_fragility_investigation
    from propstore.fragility import FragilityRequest

    report = FragilityReport(
        interventions=(
            _ranked_intervention("assumption:temperature", "temperature == 300"),
        ),
        world_fragility=0.4,
        analysis_scope="subject:enthalpy",
    )
    calls: list[object] = []

    def fake_query_fragility(world: object, request: object) -> FragilityReport:
        calls.append((world, request))
        return report

    monkeypatch.setattr(
        "propstore.epistemic_process.query_fragility", fake_query_fragility
    )
    world = MagicMock()
    request = FragilityRequest(bindings={"sample": "s1"}, concept_id="enthalpy")

    plan = plan_fragility_investigation(
        world,
        request,
        objective="stabilize enthalpy",
    )

    assert calls == [(world, request)]
    assert plan.analysis_scope == "subject:enthalpy"
    assert plan.intervention_ids == ("assumption:temperature",)
    assert plan.objective == "stabilize enthalpy"


def _investigation_plan():
    from propstore.epistemic_process import InvestigationPlan

    return InvestigationPlan.from_fragility_report(
        FragilityReport(
            interventions=(
                _ranked_intervention("assumption:temperature", "temperature == 300"),
            ),
            world_fragility=0.4,
            analysis_scope="subject:enthalpy",
        ),
        objective="stabilize",
    )


def _atms_plan() -> ATMSNodeInterventionPlan:
    return ATMSNodeInterventionPlan(
        target="ps:assertion:claim_future",
        node_id="ps:assertion:claim_future",
        claim_id="claim_future",
        current_status=ATMSNodeStatus.OUT,
        target_status=ATMSNodeStatus.IN,
        queryable_ids=("ps:assumption:y",),
        queryable_cels=("y == 2",),
        environment=("ps:assumption:x", "ps:assumption:y"),
        consistent=True,
        result_status=ATMSNodeStatus.IN,
        result_out_kind=None,
        minimality_basis="set_inclusion_over_queryable_ids",
    )
