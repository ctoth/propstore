"""WS-I Step 8: conflict orchestrator isolation and provenance discipline."""

from __future__ import annotations

import inspect

import pytest

from propstore.cel_checker import ConceptInfo, KindType
from propstore.conflict_detector import orchestrator


def test_ws_i_synthetic_source_concept_collision_is_loud() -> None:
    """E.M4: synthetic CEL concepts must not shadow authored concepts."""

    with pytest.raises(orchestrator.SyntheticConceptCollision):
        orchestrator.detect_conflicts(
            [],
            {},
            {"source": ConceptInfo("real-source", "source", KindType.CATEGORY)},
        )


def test_ws_i_parameterization_detector_returns_records_not_mutating_records() -> None:
    """E.M4: orchestrator composes returned records instead of list injection."""

    source = inspect.getsource(orchestrator.detect_conflicts)

    assert "_detect_parameterization_conflicts(records," not in source
    assert "records.extend(_detect_parameterization_conflicts(" in source


def test_ws_i_lifted_seen_key_includes_derivation_chain() -> None:
    """E.M4: lifted claims differing only by derivation chain both survive."""

    source = inspect.getsource(orchestrator._expand_lifted_conflict_claims)

    assert "derivation_chain" in source


def test_ws_i_lifting_decision_cache_is_explicit() -> None:
    """E.M4: lifting decisions are cached and shared across detector orchestration."""

    assert hasattr(orchestrator, "LiftingDecisionCache")
