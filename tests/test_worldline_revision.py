from __future__ import annotations

from dataclasses import replace

from propstore.support_revision.snapshot_types import epistemic_state_snapshot
from propstore.support_revision.iterated import epistemic_state_payload, make_epistemic_state
from propstore.support_revision.operators import revise
from propstore.support_revision.state import RevisionScope
from tests.test_revision_iterated import _history_sensitive_base
from tests.test_revision_operators import _base_with_shared_support


def test_worldline_definition_roundtrip_preserves_revision_query_block() -> None:
    from propstore.worldline import WorldlineDefinition

    definition = WorldlineDefinition.from_dict({
        "id": "revision_wl",
        "targets": ["target"],
        "revision": {
            "operation": "revise",
            "atom": {"kind": "claim", "id": "synthetic", "value": 9.0},
            "conflicts": {"claim:synthetic": ["legacy"]},
        },
    })

    assert definition.revision is not None
    assert definition.revision.operation == "revise"
    assert definition.revision.atom is not None
    assert definition.revision.atom.to_dict() == {"kind": "claim", "id": "synthetic", "value": 9.0}
    assert definition.to_dict()["revision"]["conflicts"] == {"claim:synthetic": ["legacy"]}


def test_worldline_result_roundtrip_preserves_revision_payload() -> None:
    from propstore.worldline import WorldlineResult

    result = WorldlineResult.from_dict({
        "computed": "2026-03-29T00:00:00Z",
        "content_hash": "abc123",
        "values": {"target": {"status": "determined", "value": 1.0}},
        "steps": [],
        "dependencies": {"claims": [], "stances": [], "contexts": []},
        "revision": {
            "operation": "revise",
            "input_atom_id": "claim:synthetic",
            "target_atom_ids": ["claim:legacy"],
            "result": {
                "accepted_atom_ids": ["claim:synthetic"],
                "rejected_atom_ids": ["claim:legacy"],
                "incision_set": ["assumption:shared_weak"],
                "explanation": {
                    "accepted_atom_ids": ["claim:synthetic"],
                    "rejected_atom_ids": ["claim:legacy"],
                    "incision_set": ["assumption:shared_weak"],
                    "atoms": {
                        "claim:legacy": {
                            "status": "rejected",
                            "reason": "support_lost",
                        }
                    },
                },
            },
        },
    })

    assert result is not None
    assert result.revision is not None
    assert result.revision.operation == "revise"
    assert result.to_dict()["revision"]["result"]["rejected_atom_ids"] == ["claim:legacy"]


def test_compute_worldline_content_hash_changes_when_revision_payload_changes() -> None:
    from propstore.worldline import compute_worldline_content_hash
    from propstore.worldline.result_types import WorldlineDependencies, WorldlineTargetValue
    from propstore.worldline.revision_types import WorldlineRevisionResult, WorldlineRevisionState

    left = compute_worldline_content_hash(
        values={"target": WorldlineTargetValue(status="determined", value=1.0)},
        steps=(),
        dependencies=WorldlineDependencies(),
        sensitivity=None,
        argumentation=None,
        revision=WorldlineRevisionState(
            operation="revise",
            result=WorldlineRevisionResult(accepted_atom_ids=("claim:new",)),
        ),
    )
    right = compute_worldline_content_hash(
        values={"target": WorldlineTargetValue(status="determined", value=1.0)},
        steps=(),
        dependencies=WorldlineDependencies(),
        sensitivity=None,
        argumentation=None,
        revision=WorldlineRevisionState(
            operation="revise",
            result=WorldlineRevisionResult(accepted_atom_ids=("claim:other",)),
        ),
    )

    assert left != right


class _RevisionBound:
    def __init__(
        self,
        *,
        one_shot_result=None,
        one_shot_explanation=None,
        iterated_result=None,
        iterated_explanation=None,
        merge_error: Exception | None = None,
    ) -> None:
        self.one_shot_result = one_shot_result
        self.one_shot_explanation = one_shot_explanation
        self.iterated_result = iterated_result
        self.iterated_explanation = iterated_explanation
        self.merge_error = merge_error
        self.calls: list[tuple[str, object, object, object]] = []

    def revise(self, atom, *, conflicts=None):
        self.calls.append(("revise", atom, conflicts, None))
        return self.one_shot_result

    def iterated_revise(self, atom, *, conflicts=None, operator="restrained"):
        self.calls.append(("iterated_revise", atom, conflicts, operator))
        if self.merge_error is not None:
            raise self.merge_error
        return self.iterated_result

    def revision_explain(self, result):
        if result is self.one_shot_result:
            return self.one_shot_explanation
        if self.iterated_result is not None and result is self.iterated_result[0]:
            return self.iterated_explanation
        raise AssertionError("unexpected revision result")

    def revision_state_snapshot(self, state):
        return epistemic_state_snapshot(state)


class _RevisionWorld:
    def __init__(self, bound: _RevisionBound) -> None:
        self._bound = bound

    def bind(self, environment=None, *, policy=None, **conditions):
        return self._bound


def test_run_worldline_captures_one_shot_revision_payload(monkeypatch) -> None:
    from propstore.support_revision.explain import build_revision_explanation
    from propstore.worldline import WorldlineDefinition, run_worldline
    from propstore.worldline.result_types import WorldlineTargetValue

    base, entrenchment = _base_with_shared_support()
    one_shot_result = revise(
        base,
        {"kind": "claim", "id": "synthetic", "value": 9.0},
        entrenchment=entrenchment,
        conflicts={"claim:synthetic": ("claim:legacy",)},
    )
    bound = _RevisionBound(
        one_shot_result=one_shot_result,
        one_shot_explanation=build_revision_explanation(one_shot_result, entrenchment=entrenchment),
    )

    monkeypatch.setattr("propstore.worldline.runner._resolve_concept_name", lambda *args, **kwargs: "concept:target")
    monkeypatch.setattr(
        "propstore.worldline.runner._resolve_target",
        lambda *args, **kwargs: WorldlineTargetValue(status="determined", value=1.0),
    )

    result = run_worldline(
        WorldlineDefinition.from_dict({
            "id": "revision_capture",
            "targets": ["target"],
            "revision": {
                "operation": "revise",
                "atom": {"kind": "claim", "id": "synthetic", "value": 9.0},
                "conflicts": {"claim:synthetic": ["claim:legacy"]},
            },
        }),
        _RevisionWorld(bound),
    )

    assert result.revision is not None
    assert result.revision.operation == "revise"
    assert result.revision.result is not None
    assert result.revision.result.accepted_atom_ids == one_shot_result.accepted_atom_ids
    assert result.revision.result.rejected_atom_ids == one_shot_result.rejected_atom_ids
    assert len(bound.calls) == 1
    call_operation, call_atom, call_conflicts, call_operator = bound.calls[0]
    assert call_operation == "revise"
    assert call_atom == {
        "kind": "claim",
        "id": "synthetic",
        "claim_id": "synthetic",
        "value": 9.0,
    }
    assert call_conflicts == {"claim:synthetic": ("claim:legacy",)}
    assert call_operator is None


def test_run_worldline_captures_iterated_revision_state_payload(monkeypatch) -> None:
    from propstore.support_revision.explain import build_revision_explanation
    from propstore.worldline import WorldlineDefinition, run_worldline
    from propstore.worldline.result_types import WorldlineTargetValue

    base, entrenchment, _ = _history_sensitive_base()
    state = make_epistemic_state(base, entrenchment)
    iterated_result = (
        revise(
            base,
            {"kind": "claim", "id": "new", "value": 9.0},
            entrenchment=entrenchment,
            conflicts={"claim:new": ("claim:legacy",)},
        ),
        replace(
            state,
            accepted_atom_ids=("claim:new", "claim:left_dependent"),
            ranked_atom_ids=("claim:new", "claim:left_dependent"),
            ranking={"claim:new": 0, "claim:left_dependent": 1},
        ),
    )
    bound = _RevisionBound(
        iterated_result=iterated_result,
        iterated_explanation=build_revision_explanation(iterated_result[0], entrenchment=entrenchment),
    )

    monkeypatch.setattr("propstore.worldline.runner._resolve_concept_name", lambda *args, **kwargs: "concept:target")
    monkeypatch.setattr(
        "propstore.worldline.runner._resolve_target",
        lambda *args, **kwargs: WorldlineTargetValue(status="determined", value=1.0),
    )

    result = run_worldline(
        WorldlineDefinition.from_dict({
            "id": "iterated_revision_capture",
            "targets": ["target"],
            "revision": {
                "operation": "iterated_revise",
                "atom": {"kind": "claim", "id": "new", "value": 9.0},
                "conflicts": {"claim:new": ["claim:legacy"]},
                "operator": "restrained",
            },
        }),
        _RevisionWorld(bound),
    )

    assert result.revision is not None
    assert result.revision.operation == "iterated_revise"
    assert result.revision.state is not None
    assert result.revision.state.to_dict() == epistemic_state_payload(iterated_result[1])
    assert len(bound.calls) == 1
    call_operation, call_atom, call_conflicts, call_operator = bound.calls[0]
    assert call_operation == "iterated_revise"
    assert call_atom == {
        "kind": "claim",
        "id": "new",
        "claim_id": "new",
        "value": 9.0,
    }
    assert call_conflicts == {"claim:new": ("claim:legacy",)}
    assert call_operator == "restrained"


def test_run_worldline_revision_merge_point_refusal_is_explicit(monkeypatch) -> None:
    from propstore.worldline import WorldlineDefinition, run_worldline
    from propstore.worldline.result_types import WorldlineTargetValue

    base, entrenchment, _ = _history_sensitive_base()
    merge_state = make_epistemic_state(
        replace(
            base,
            scope=RevisionScope(bindings={}, branch="topic", merge_parent_commits=("abc", "def")),
        ),
        entrenchment,
    )
    bound = _RevisionBound(
        iterated_result=(None, merge_state),
        merge_error=ValueError("iterated revision is undefined at a merge point; use an explicit merge path"),
    )

    monkeypatch.setattr("propstore.worldline.runner._resolve_concept_name", lambda *args, **kwargs: "concept:target")
    monkeypatch.setattr(
        "propstore.worldline.runner._resolve_target",
        lambda *args, **kwargs: WorldlineTargetValue(status="determined", value=1.0),
    )

    result = run_worldline(
        WorldlineDefinition.from_dict({
            "id": "iterated_revision_merge_refusal",
            "targets": ["target"],
            "revision": {
                "operation": "iterated_revise",
                "atom": {"kind": "claim", "id": "new", "value": 9.0},
                "conflicts": {"claim:new": ["claim:legacy"]},
                "operator": "restrained",
            },
        }),
        _RevisionWorld(bound),
    )

    assert result.revision is not None
    assert result.revision.error is not None
    assert "merge point" in result.revision.error
