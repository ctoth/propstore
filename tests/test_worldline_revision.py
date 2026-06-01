from __future__ import annotations

from dataclasses import replace

from propstore.families.concepts.declaration import Concept
from propstore.support_revision.history import EpistemicSnapshot
from propstore.support_revision.iterated import (
    epistemic_state_payload,
    make_epistemic_state,
)
from propstore.support_revision.state import RevisionScope
from tests.support_revision.formal_realization_helpers import revise_via_formal_decision
from tests.test_revision_iterated import _history_sensitive_base
from tests.test_revision_operators import _base_with_shared_support
from tests.support_revision.revision_assertion_helpers import make_assertion_atom


def test_worldline_definition_roundtrip_preserves_revision_query_block() -> None:
    from propstore.worldline import WorldlineDefinition

    synthetic = make_assertion_atom("synthetic", value=9.0)
    legacy = make_assertion_atom("legacy")
    definition = WorldlineDefinition.from_dict(
        {
            "id": "revision_wl",
            "targets": ["target"],
            "revision": {
                "operation": "revise",
                "atom": {"kind": "assertion", "id": synthetic.atom_id, "value": 9.0},
                "conflicts": {synthetic.atom_id: [legacy.atom_id]},
            },
        }
    )

    assert definition.revision is not None
    assert definition.revision.operation == "revise"
    assert definition.revision.atom is not None
    assert definition.revision.atom.to_dict() == {
        "kind": "assertion",
        "id": synthetic.atom_id,
        "value": 9.0,
    }
    assert definition.to_dict()["revision"]["conflicts"] == {
        synthetic.atom_id: [legacy.atom_id]
    }


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

    def revise(self, atom, *, conflicts=None, max_candidates):
        self.calls.append(("revise", atom, conflicts, None, max_candidates))
        return self.one_shot_result

    def iterated_revise(
        self, atom, *, conflicts=None, max_candidates, operator="restrained"
    ):
        self.calls.append(
            ("iterated_revise", atom, conflicts, operator, max_candidates)
        )
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
        return EpistemicSnapshot.from_state(state)


class _RevisionWorld:
    def __init__(self, bound: _RevisionBound) -> None:
        self._bound = bound

    def bind(self, environment=None, *, policy=None, **conditions):
        return self._bound

    def get_concept(self, concept_id: str) -> Concept | None:
        if concept_id in {"concept:target", "target"}:
            return Concept(id="concept:target", canonical_name="target")
        return None


def test_run_worldline_revision_merge_point_refusal_is_explicit(monkeypatch) -> None:
    from propstore.worldline import WorldlineDefinition, run_worldline
    from propstore.worldline.result_types import WorldlineTargetValue

    base, entrenchment, _, _ = _history_sensitive_base()
    merge_state = make_epistemic_state(
        replace(
            base,
            scope=RevisionScope(
                bindings={}, branch="topic", merge_parent_commits=("abc", "def")
            ),
        ),
        entrenchment,
    )
    bound = _RevisionBound(
        iterated_result=(None, merge_state),
        merge_error=ValueError(
            "iterated revision is undefined at a merge point; use an explicit merge path"
        ),
    )

    monkeypatch.setattr(
        "propstore.worldline.runner._resolve_target",
        lambda *args, **kwargs: WorldlineTargetValue(status="determined", value=1.0),
    )

    result = run_worldline(
        WorldlineDefinition.from_dict(
            {
                "id": "iterated_revision_merge_refusal",
                "targets": ["target"],
                "revision": {
                    "operation": "iterated_revise",
                    "atom": {
                        "kind": "assertion",
                        "id": make_assertion_atom("new", value=9.0).atom_id,
                        "value": 9.0,
                    },
                    "conflicts": {},
                    "operator": "restrained",
                },
            }
        ),
        _RevisionWorld(bound),
    )

    assert result.revision is not None
    assert result.revision.error is not None
    assert result.revision.error.value == "revision"
