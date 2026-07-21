"""Phase-6 analyzer math over typed semantic owners.

These exercise the store-free assembly: ``shared_analyzer_input_from_active_graph``
fed canonical claims, stances, and conflicts, then
``analyze_claim_graph`` / ``analyze_praf`` and the pure projection helpers. The
store/world readers that *produce* these payloads (``shared_analyzer_input_from_store``,
the ``_*_from_row`` converters, ``ActiveWorldGraph``) are deferred to the world
layer (Phase 7) and are intentionally not constructed here.
"""

from __future__ import annotations

from propstore.conflict_detector import ConflictClass, ConflictRecord
from propstore.core.analyzers import (
    SharedAnalyzerInput,
    analyze_claim_graph,
    analyze_praf,
    project_acceptance_result,
    project_extension_result,
    shared_analyzer_input_from_active_graph,
)
from propstore.core.results import ExtensionResult
from propstore.families.claims import Claim, ClaimType
from propstore.families.relations import Stance
from propstore.stances import StanceType


def _claim(claim_id: str, value: float) -> Claim:
    return Claim(
        claim_id=claim_id,
        output_concept="concept1",
        claim_type=ClaimType.PARAMETER,
        value=value,
        sample_size=30,
        confidence=1.0,
    )


def _conflict(kind: ConflictClass) -> ConflictRecord:
    return ConflictRecord(
        concept_id="concept1",
        claim_a_id="a",
        claim_b_id="b",
        warning_class=kind,
        conditions_a=[],
        conditions_b=[],
        value_a="1",
        value_b="2",
    )


def _shared_supersede() -> SharedAnalyzerInput:
    # ``b supersedes a`` is an unconditional attack → a direct defeat b -> a.
    return shared_analyzer_input_from_active_graph(
        {"a": _claim("a", 1.0), "b": _claim("b", 2.0)},
        [
            Stance(
                stance_id="s_ba",
                source_claim_id="b",
                target_claim_id="a",
                stance_type=StanceType.SUPERSEDES,
            )
        ],
        [],
        {"a", "b"},
    )


def test_supersede_builds_directed_defeat_and_grounded_winner() -> None:
    shared = _shared_supersede()

    assert ("b", "a") in shared.relations.direct_defeats
    assert ("b", "a") in shared.argumentation_framework.defeats

    result = analyze_claim_graph(shared, semantics="grounded")

    assert result.backend == "claim_graph"
    assert result.extensions[0].accepted_claim_ids == ("b",)


def test_conflict_row_invents_symmetric_rebuts() -> None:
    shared = shared_analyzer_input_from_active_graph(
        {"a": _claim("a", 1.0), "b": _claim("b", 2.0)},
        [],
        [_conflict(ConflictClass.CONFLICT)],
        {"a", "b"},
    )

    assert ("a", "b") in shared.relations.attacks
    assert ("b", "a") in shared.relations.attacks
    # Equal-strength rebuts succeed both ways → mutual defeat, empty grounded.
    assert ("a", "b") in shared.relations.direct_defeats
    assert ("b", "a") in shared.relations.direct_defeats
    grounded = analyze_claim_graph(shared, semantics="grounded")
    assert grounded.extensions[0].accepted_claim_ids == ()


def test_non_real_conflict_class_invents_no_rebuts() -> None:
    shared = shared_analyzer_input_from_active_graph(
        {"a": _claim("a", 1.0), "b": _claim("b", 2.0)},
        [],
        [_conflict(ConflictClass.PHI_NODE)],
        {"a", "b"},
    )
    assert shared.relations.attacks == frozenset()
    assert shared.stances == ()


def test_analyze_praf_returns_acceptance_projection() -> None:
    shared = _shared_supersede()

    result = analyze_praf(shared, target_claim_ids=("a", "b"))

    assert result.backend == "praf"
    assert result.projection is not None
    assert result.projection.target_claim_ids == ("a", "b")


def test_project_extension_result_intersects_targets() -> None:
    extensions = (ExtensionResult(name="grounded", accepted_claim_ids=("a", "c")),)
    projection = project_extension_result(extensions, target_claim_ids=("a", "b", "c"))
    assert projection.survivor_claim_ids == ("a", "c")
    assert projection.witness_claim_ids == ("a", "c")
    assert projection.target_claim_ids == ("a", "b", "c")


def test_project_acceptance_result_picks_best_probability() -> None:
    projection = project_acceptance_result(
        {"a": 0.9, "b": 0.1},
        target_claim_ids=("a", "b"),
    )
    assert projection.survivor_claim_ids == ("a",)
    assert projection.witness_claim_ids == ("a", "b")
