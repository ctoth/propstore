from __future__ import annotations

from dataclasses import replace

from propstore.revision.iterated import epistemic_state_payload, make_epistemic_state
from propstore.revision.operators import revise
from propstore.revision.state import BeliefAtom, RevisionScope
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
    assert definition.revision.atom == {"kind": "claim", "id": "synthetic", "value": 9.0}
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
                "explanation": {"claim:legacy": {"reason": "support_lost"}},
            },
        },
    })

    assert result is not None
    assert result.revision is not None
    assert result.revision["operation"] == "revise"
    assert result.to_dict()["revision"]["result"]["rejected_atom_ids"] == ["claim:legacy"]


def test_compute_worldline_content_hash_changes_when_revision_payload_changes() -> None:
    from propstore.worldline import compute_worldline_content_hash

    left = compute_worldline_content_hash(
        values={"target": {"status": "determined", "value": 1.0}},
        steps=[],
        dependencies={"claims": [], "stances": [], "contexts": []},
        sensitivity=None,
        argumentation=None,
        revision={
            "operation": "revise",
            "result": {"accepted_atom_ids": ["claim:new"]},
        },
    )
    right = compute_worldline_content_hash(
        values={"target": {"status": "determined", "value": 1.0}},
        steps=[],
        dependencies={"claims": [], "stances": [], "contexts": []},
        sensitivity=None,
        argumentation=None,
        revision={
            "operation": "revise",
            "result": {"accepted_atom_ids": ["claim:other"]},
        },
    )

    assert left != right


class _RevisionBound:
    def __init__(self, *, one_shot_result=None, iterated_result=None, merge_error: Exception | None = None) -> None:
        self.one_shot_result = one_shot_result
        self.iterated_result = iterated_result
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


class _RevisionWorld:
    def __init__(self, bound: _RevisionBound) -> None:
        self._bound = bound

    def bind(self, environment=None, *, policy=None, **conditions):
        return self._bound


def test_run_worldline_captures_one_shot_revision_payload(monkeypatch) -> None:
    from propstore.worldline import WorldlineDefinition
    from propstore.worldline_runner import run_worldline

    base, entrenchment = _base_with_shared_support()
    one_shot_result = revise(
        base,
        {"kind": "claim", "id": "synthetic", "value": 9.0},
        entrenchment=entrenchment,
        conflicts={"claim:synthetic": ("claim:legacy",)},
    )
    bound = _RevisionBound(one_shot_result=one_shot_result)

    monkeypatch.setattr("propstore.worldline_runner._resolve_concept_name", lambda *args, **kwargs: "concept:target")
    monkeypatch.setattr(
        "propstore.worldline_runner._resolve_target",
        lambda *args, **kwargs: {"status": "determined", "value": 1.0},
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
    assert result.revision["operation"] == "revise"
    assert result.revision["result"]["accepted_atom_ids"] == list(one_shot_result.accepted_atom_ids)
    assert result.revision["result"]["rejected_atom_ids"] == list(one_shot_result.rejected_atom_ids)
    assert bound.calls == [
        (
            "revise",
            {"kind": "claim", "id": "synthetic", "value": 9.0},
            {"claim:synthetic": ["claim:legacy"]},
            None,
        )
    ]


def test_run_worldline_captures_iterated_revision_state_payload(monkeypatch) -> None:
    from propstore.worldline import WorldlineDefinition
    from propstore.worldline_runner import run_worldline

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
    bound = _RevisionBound(iterated_result=iterated_result)

    monkeypatch.setattr("propstore.worldline_runner._resolve_concept_name", lambda *args, **kwargs: "concept:target")
    monkeypatch.setattr(
        "propstore.worldline_runner._resolve_target",
        lambda *args, **kwargs: {"status": "determined", "value": 1.0},
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
    assert result.revision["operation"] == "iterated_revise"
    assert result.revision["state"] == epistemic_state_payload(iterated_result[1])
    assert bound.calls == [
        (
            "iterated_revise",
            {"kind": "claim", "id": "new", "value": 9.0},
            {"claim:new": ["claim:legacy"]},
            "restrained",
        )
    ]


def test_run_worldline_revision_merge_point_refusal_is_explicit(monkeypatch) -> None:
    from propstore.worldline import WorldlineDefinition
    from propstore.worldline_runner import run_worldline

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

    monkeypatch.setattr("propstore.worldline_runner._resolve_concept_name", lambda *args, **kwargs: "concept:target")
    monkeypatch.setattr(
        "propstore.worldline_runner._resolve_target",
        lambda *args, **kwargs: {"status": "determined", "value": 1.0},
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
    assert "merge point" in result.revision["error"]
