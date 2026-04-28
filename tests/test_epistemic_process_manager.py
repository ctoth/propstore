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
from tests.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_iterated import _history_sensitive_base


def test_investigation_plan_from_fragility_report_roundtrips_with_stable_identity() -> None:
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


def test_public_fragility_investigation_path_reuses_fragility_query(monkeypatch: pytest.MonkeyPatch) -> None:
    from propstore.epistemic_process import plan_fragility_investigation
    from propstore.fragility import FragilityRequest

    report = FragilityReport(
        interventions=(_ranked_intervention("assumption:temperature", "temperature == 300"),),
        world_fragility=0.4,
        analysis_scope="subject:enthalpy",
    )
    calls: list[object] = []

    def fake_query_fragility(world: object, request: object) -> FragilityReport:
        calls.append((world, request))
        return report

    monkeypatch.setattr("propstore.epistemic_process.query_fragility", fake_query_fragility)
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


def test_process_manager_queues_jobs_referencing_snapshots_policies_assertions_and_journal_entries() -> None:
    from propstore.epistemic_process import (
        EpistemicProcessManager,
        JobKind,
        ProcessJob,
    )

    snapshot, policy, journal_entry, atom_id = _snapshot_policy_journal_and_atom()
    plan = _investigation_plan()
    job = ProcessJob.for_plan(
        kind=JobKind.INVESTIGATION,
        plan=plan,
        snapshot=snapshot,
        policy=policy,
        assertion_ids=(atom_id,),
        journal_entries=(journal_entry,),
    )

    manager = EpistemicProcessManager().queue(job)
    payload = manager.to_dict()
    restored = EpistemicProcessManager.from_dict(payload)
    queued = restored.queued_jobs[job.job_id]

    assert queued.job.snapshot_hash == snapshot.content_hash
    assert queued.job.policy_id == policy.profile_id
    assert queued.job.policy_payload == policy.to_dict()
    assert queued.job.assertion_ids == (atom_id,)
    assert queued.job.journal_entry_hashes == (journal_entry.content_hash,)
    assert restored.replay().ok is True
    assert restored.content_hash == manager.content_hash


def test_intervention_revision_and_merge_jobs_are_first_class_process_jobs() -> None:
    from propstore.epistemic_process import InterventionPlan, JobKind, ProcessJob

    snapshot, policy, journal_entry, atom_id = _snapshot_policy_journal_and_atom()
    intervention_plan = InterventionPlan.from_atms_plan(
        _atms_plan(),
        objective="make claim_future in",
    )

    jobs = (
        ProcessJob.for_plan(
            kind=JobKind.INTERVENTION,
            plan=intervention_plan,
            snapshot=snapshot,
            policy=policy,
            assertion_ids=(atom_id,),
            journal_entries=(journal_entry,),
        ),
        ProcessJob.for_operation(
            kind=JobKind.REVISION,
            operation=TransitionOperation(
                name="iterated_revise",
                input_atom_id=atom_id,
                target_atom_ids=("ps:assertion:legacy",),
            ),
            snapshot=snapshot,
            policy=policy,
            assertion_ids=(atom_id,),
            journal_entries=(journal_entry,),
        ),
        ProcessJob.for_operation(
            kind=JobKind.MERGE,
            operation=TransitionOperation(
                name="worldline_merge",
                target_atom_ids=(atom_id, "ps:assertion:legacy"),
                parameters={"parents": ["main", "experiment"]},
            ),
            snapshot=snapshot,
            policy=policy,
            assertion_ids=(atom_id,),
            journal_entries=(journal_entry,),
        ),
    )

    assert {job.kind for job in jobs} == {
        JobKind.INTERVENTION,
        JobKind.REVISION,
        JobKind.MERGE,
    }
    assert all(job.snapshot_hash == snapshot.content_hash for job in jobs)
    assert all(job.policy_payload == policy.to_dict() for job in jobs)
    assert all(job.journal_entry_hashes == (journal_entry.content_hash,) for job in jobs)


def test_completion_recording_is_idempotent_but_rejects_conflicting_results() -> None:
    from propstore.epistemic_process import (
        EpistemicProcessManager,
        JobKind,
        ProcessJob,
    )

    snapshot, policy, journal_entry, atom_id = _snapshot_policy_journal_and_atom()
    job = ProcessJob.for_plan(
        kind=JobKind.INVESTIGATION,
        plan=_investigation_plan(),
        snapshot=snapshot,
        policy=policy,
        assertion_ids=(atom_id,),
        journal_entries=(journal_entry,),
    )
    manager = EpistemicProcessManager().queue(job)
    completed_once = manager.complete(
        job.job_id,
        snapshot=snapshot,
        journal_entries=(journal_entry,),
        result_payload={"decision": "queued-revision"},
    )
    completed_twice = completed_once.complete(
        job.job_id,
        snapshot=snapshot,
        journal_entries=(journal_entry,),
        result_payload={"decision": "queued-revision"},
    )

    assert completed_twice is completed_once
    assert tuple(completed_twice.completions) == (job.job_id,)
    with pytest.raises(ValueError, match="conflicting completion"):
        completed_once.complete(
            job.job_id,
            snapshot=snapshot,
            journal_entries=(journal_entry,),
            result_payload={"decision": "different"},
        )


@pytest.mark.property
@given(objective=st.text(min_size=1, max_size=40))
@settings(max_examples=16)
def test_process_manager_replay_is_deterministic_for_fixed_inputs(objective: str) -> None:
    from propstore.epistemic_process import (
        EpistemicProcessManager,
        JobKind,
        ProcessJob,
    )

    snapshot, policy, journal_entry, atom_id = _snapshot_policy_journal_and_atom()
    job = ProcessJob.for_plan(
        kind=JobKind.INVESTIGATION,
        plan=replace(_investigation_plan(), objective=objective),
        snapshot=snapshot,
        policy=policy,
        assertion_ids=(atom_id,),
        journal_entries=(journal_entry,),
    )
    first = EpistemicProcessManager().queue(job).complete(
        job.job_id,
        snapshot=snapshot,
        journal_entries=(journal_entry,),
        result_payload={"objective": objective},
    )
    second = EpistemicProcessManager.from_dict(first.to_dict())

    assert second.replay().ok is True
    assert second.content_hash == first.content_hash
    assert second.to_dict() == first.to_dict()


def _ranked_intervention(intervention_id: str, cel: str) -> RankedIntervention:
    return RankedIntervention(
        target=InterventionTarget(
            intervention_id=intervention_id,
            kind=InterventionKind.ASSUMPTION,
            family=InterventionFamily.ATMS,
            subject_id="enthalpy",
            description=f"Check {cel}",
            cost_tier=1,
            provenance=InterventionProvenance(
                family=InterventionFamily.ATMS,
                source_ids=(intervention_id,),
                subject_concept_ids=("enthalpy",),
            ),
            payload=AssumptionTarget(
                queryable_id=intervention_id.removeprefix("assumption:"),
                cel=cel,
                stabilizes_concepts=("enthalpy",),
                witness_count=1,
                consistent_future_count=2,
            ),
        ),
        local_fragility=0.4,
        roi=0.4,
        ranking_policy=RankingPolicy.HEURISTIC_ROI,
        score_explanation="test",
    )


def _investigation_plan():
    from propstore.epistemic_process import InvestigationPlan

    return InvestigationPlan.from_fragility_report(
        FragilityReport(
            interventions=(_ranked_intervention("assumption:temperature", "temperature == 300"),),
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


def _snapshot_policy_journal_and_atom() -> tuple[
    EpistemicSnapshot,
    PolicyProfile,
    TransitionJournalEntry,
    str,
]:
    base, entrenchment, _, ids = _history_sensitive_base()
    state_in = make_epistemic_state(base, entrenchment)
    atom = make_assertion_atom("process_new")
    result, state_out = iterated_revise(
        state_in,
        atom,
        conflicts={atom.atom_id: (ids["legacy"],)},
        operator="restrained",
    )
    policy = default_policy_profile()
    operation = TransitionOperation(
        name="iterated_revise",
        input_atom_id=atom.atom_id,
        target_atom_ids=(ids["legacy"],),
    )
    entry = TransitionJournalEntry.from_states(
        state_in=state_in,
        operation=operation,
        policy_id=policy.profile_id,
        policy_payload=policy.to_dict(),
        operator=JournalOperator.ITERATED_REVISE,
        operator_input={
            "formula": belief_atom_to_canonical_dict(atom),
            "revision_operator": "restrained",
            "targets": [ids["legacy"]],
        },
        version_policy_snapshot={
            "revision_policy_version": "revision.v1",
            "ranking_policy_version": "ranking.v1",
            "entrenchment_policy_version": "entrenchment.v1",
        },
        state_out=state_out,
        explanation=result.explanation,
    )
    return EpistemicSnapshot.from_state(state_in), policy, entry, atom.atom_id
