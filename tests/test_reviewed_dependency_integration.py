"""Reviewed substrate fixes through Propstore's existing domain boundaries."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import msgspec
import pytest
from assignment_selection import Assignment, SourceAssignment
from condition_ir import KindType
from doxa import Opinion
from quire.references import ForeignKeyValidationError

from propstore.families.claims import Claim
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition
from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY
from propstore.families.relations import Stance
from propstore.opinion_provenance import OpinionWithProvenance
from propstore.praf.engine import p_relation_from_stance
from propstore.repository import Repository
from propstore.world.assignment_selection_merge import (
    AssignmentSelectionRequest,
    solve_assignment_selection_merge,
)
from propstore.world.types import DecisionValueSource, apply_decision_criterion


def _repository(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "knowledge")
    with repo.families.transact(message="Seed integration graph") as transaction:
        transaction.concept.save("mass", Concept("mass", "Mass"))
        transaction.claim.save("old", Claim("old", output_concept="mass"))
    return repo


@pytest.mark.parametrize("direction", ["incoming", "outgoing"])
def test_moves_reject_dangling_propstore_references(
    tmp_path: Path, direction: str
) -> None:
    repo = _repository(tmp_path)
    head = repo.require_git().head_sha()

    with pytest.raises(ForeignKeyValidationError, match="does not resolve"):
        if direction == "incoming":
            repo.families.concept.move(
                "mass", "weight", Concept("weight", "Weight"), message="Move concept"
            )
        else:
            repo.families.claim.move(
                "old",
                "new",
                Claim("new", output_concept="missing"),
                message="Move claim",
            )

    assert repo.require_git().head_sha() == head
    assert repo.families.claim.require("old").output_concept == "mass"
    assert repo.families.concept.require("mass").canonical_name == "Mass"
    assert repo.families.claim.load("new") is None
    assert repo.families.concept.load("weight") is None


@pytest.mark.parametrize("transactional", [False, True])
@pytest.mark.parametrize("normalized_target", ["mass", "missing"])
def test_moves_validate_the_normalized_propstore_claim(
    tmp_path: Path, transactional: bool, normalized_target: str
) -> None:
    repo = _repository(tmp_path)
    calls: list[str | None] = []

    def normalize(context, document: Claim, store) -> Claim:
        calls.append(document.output_concept)
        return msgspec.structs.replace(document, output_concept=normalized_target)

    # Exercise Quire's normalization hook with the real Propstore charter and
    # complete FK registry, retaining the repository's normal store and backend.
    registry = replace(
        PROPSTORE_FAMILY_REGISTRY,
        families=tuple(
            replace(
                definition,
                artifact_family=replace(
                    definition.artifact_family, normalize_for_write=normalize
                ),
            )
            if definition.name == "claim"
            else definition
            for definition in PROPSTORE_FAMILY_REGISTRY.families
        ),
    )
    families = registry.bind(repo, repo.families.store)
    authored_target = "missing" if normalized_target == "mass" else "mass"
    replacement = Claim("new", output_concept=authored_target)
    head = repo.require_git().head_sha()

    def move() -> None:
        if transactional:
            with families.transact(message="Move normalized claim") as transaction:
                transaction.claim.move("old", "new", replacement)
        else:
            families.claim.move(
                "old", "new", replacement, message="Move normalized claim"
            )

    if normalized_target == "mass":
        move()
        assert repo.families.claim.load("old") is None
        assert repo.families.claim.require("new").output_concept == "mass"
    else:
        with pytest.raises(ForeignKeyValidationError, match="does not resolve"):
            move()
        assert repo.require_git().head_sha() == head
        assert repo.families.claim.require("old").output_concept == "mass"
        assert repo.families.claim.load("new") is None
    assert calls == [authored_target]


def test_form_parameter_nulls_survive_git_storage(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    form = FormDefinition(
        name="category",
        kind=KindType.CATEGORY,
        parameters={"unknown": None, "nested": {"unknown": None}, "items": [None]},
    )
    repo.families.form.save("category", form, message="Store explicit unknowns")

    loaded = repo.families.form.require("category")
    assert loaded.parameters == form.parameters
    assert "unknown" in loaded.parameters
    assert loaded.parameters["unknown"] is None


@pytest.mark.parametrize("copies", [8, 200])
@pytest.mark.parametrize("method", ["fuse", "wbf", "ccf"])
def test_multisource_fusion_reaches_stance_storage_and_rendering(
    tmp_path: Path, copies: int, method: str
) -> None:
    repo = _repository(tmp_path)
    with repo.families.transact(message="Store source opinions") as transaction:
        for stance_id, belief, uncertainty in (("a", 0.6, 0.1), ("b", 0.4, 0.3)):
            transaction.stance.save(
                stance_id,
                Stance(
                    stance_id=stance_id,
                    source_claim_id="old",
                    target_claim_id="old",
                    opinion_belief=belief,
                    opinion_disbelief=0.3,
                    opinion_uncertainty=uncertainty,
                    opinion_base_rate=0.5,
                ),
            )
    inputs = [
        p_relation_from_stance(repo.families.stance.require(key)) for key in ("a", "b")
    ]
    assert all(isinstance(pairing, OpinionWithProvenance) for pairing in inputs)
    pool = [pairing.opinion for pairing in inputs] * copies
    fused = getattr(Opinion, method)(*pool)
    if method == "ccf":
        uncertainty = 0.03**copies
        expected = (0.7 - uncertainty, 0.3, uncertainty, 0.5)
    else:
        expected = (19 / 34, 0.3, 12 / 85, 0.5)
    assert (fused.b, fused.d, fused.u, fused.a) == pytest.approx(expected)

    repo.families.stance.save(
        "fused",
        Stance(
            stance_id="fused",
            source_claim_id="old",
            target_claim_id="old",
            opinion_belief=fused.b,
            opinion_disbelief=fused.d,
            opinion_uncertainty=fused.u,
            opinion_base_rate=fused.a,
        ),
        message="Store fused opinion",
    )
    paired = p_relation_from_stance(repo.families.stance.require("fused"))
    assert isinstance(paired, OpinionWithProvenance)
    assert paired.expectation() == pytest.approx(expected[0] + 0.5 * expected[2])
    rendered = apply_decision_criterion(
        paired.opinion.b,
        paired.opinion.d,
        paired.opinion.u,
        paired.opinion.a,
        confidence=None,
        criterion="projected_probability",
    )
    assert rendered.source is DecisionValueSource.OPINION
    assert rendered.value == pytest.approx(expected[0] + 0.5 * expected[2])


@pytest.mark.parametrize("majority", [2**53, -(2**63)])
def test_assignment_adapter_distinguishes_adjacent_large_integers(
    majority: int,
) -> None:
    minority = majority + 1
    request = AssignmentSelectionRequest(
        concept_ids=("mass",),
        sources=tuple(
            SourceAssignment(str(index), Assignment({"mass": value}))
            for index, value in enumerate((majority, majority, minority))
        ),
    )
    result = solve_assignment_selection_merge(request)

    assert tuple(winner.value_for("mass") for winner in result.winners) == (majority,)
    assert tuple(
        (candidate.assignment.value_for("mass"), candidate.score)
        for candidate in result.scored_candidates
    ) == ((majority, 1.0), (minority, 2.0))
