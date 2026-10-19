"""Only proven conflict classifications license ATMS nogoods."""

from pathlib import Path

import pytest

from propstore.conflict_detector.models import ConflictClass
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.repository import Repository
from propstore.world import WorldQuery
from propstore.world.types import QueryableAssumption
from tests.atms_feed import ClaimSpec, ConflictSpec, build_bound


@pytest.mark.parametrize("classification", list(ConflictClass))
def test_only_proven_conflicts_make_nogoods(classification: ConflictClass) -> None:
    bound = build_bound(
        claims=[ClaimSpec("a", "x", value=1), ClaimSpec("b", "x", value=2)],
        conflicts=[ConflictSpec("x", "a", "b", warning_class=classification)],
    )
    engine = bound.atms_engine()
    assert bool(engine.nogoods.environments) == (
        classification
        in {ConflictClass.CONFLICT, ConflictClass.OVERLAP, ConflictClass.PARAM_CONFLICT}
    )
    assert bound.store.conflicts()[0].warning_class is classification


def test_repository_context_separation_does_not_make_nogood(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.families.concept.save(
        "x", Concept(concept_id="x", canonical_name="x"), message="concept"
    )
    for context_id, value in (("a", 1), ("b", 2)):
        repo.families.context.save(
            context_id,
            Context(context_id=context_id, name=context_id),
            message="context",
        )
        repo.families.claim.save(
            context_id,
            Claim(
                claim_id=context_id,
                claim_type=ClaimType.PARAMETER,
                context_id=context_id,
                output_concept="x",
                value=value,
            ),
            message="claim",
        )
    with WorldQuery(repo) as world:
        conflicts = world.conflicts()
        assert conflicts
        assert all(
            conflict.warning_class is ConflictClass.CONTEXT_PHI_NODE
            for conflict in conflicts
        )
        bound = world.bind()
        engine = bound.atms_engine()
        label_a = engine.claim_label("a")
        label_b = engine.claim_label("b")
        assert label_a is not None and label_a.environments
        assert label_b is not None and label_b.environments
        assert not engine.nogoods.environments
        futures = engine.future_environments(
            (QueryableAssumption.from_cel("x == 1"),), limit=None
        )
        assert futures and all(entry.consistent for entry in futures)
