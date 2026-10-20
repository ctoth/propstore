"""Canonical licences survive the real Git -> sidecar -> ASPIC boundary."""

from pathlib import Path

from argumentation.core.dung import grounded_extension
from condition_ir import KindType

from propstore.aspic_bridge.projection import build_aspic_projection
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.justifications import Justification
from propstore.families.contexts import Context
from propstore.families.forms import FormDefinition
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.core.graph_types import GraphDelta
from propstore.repository import Repository
from propstore.source.common import init_source_branch
from propstore.source.concepts import commit_source_concept_proposal
from propstore.source.claims import commit_source_claim_proposal
from propstore.source.relations import commit_source_justification_proposal
from propstore.source.finalize import finalize_source_branch
from propstore.source.promote import promote_source_branch
from propstore.world import WorldQuery, OverlayWorld


def _accepted(world: WorldQuery, remove: tuple[str, ...] = ()) -> set[str]:
    bound = world.bind()
    view = OverlayWorld(bound, remove=remove) if remove else bound
    projection = build_aspic_projection(
        view.store,
        view.active_claims(),
        bundle=world.grounding_bundle(),
        active_graph=None if remove else bound.active_graph,
    )
    accepted_arguments = grounded_extension(projection.framework)
    return {
        argument.claim_id
        for argument in projection.arguments
        if argument.arg_id in accepted_arguments
    }


def test_stored_inference_depends_on_premise_and_is_not_a_reported_fact(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.families.concept.save(
        "result",
        Concept(concept_id="result", canonical_name="result"),
        message="concept",
    )
    for claim_id in ("evidence", "conclusion"):
        repo.families.claim.save(
            claim_id,
            Claim(
                claim_id=claim_id,
                claim_type=ClaimType.OBSERVATION,
                concepts=("result",),
                statement=claim_id,
            ),
            message="claim",
        )
    licence = Justification(
        justification_id="inference",
        conclusion="conclusion",
        premises=("evidence",),
        rule_kind="empirical_support",
        rule_strength="defeasible",
    )
    repo.families.justification.save("inference", licence, message="inference")
    with WorldQuery(repo) as world:
        assert world.all_justifications() == [licence]
        assert world.compiled_graph().justifications == (licence,)
        assert GraphDelta(remove_claim_ids=("evidence",)).apply(
            world.compiled_graph()
        ).justifications == (licence,)
        assert _accepted(world) == {"evidence", "conclusion"}
        assert _accepted(world, ("evidence",)) == set()
        assert _accepted(world) == {"evidence", "conclusion"}


def test_explicit_independent_report_survives_loss_of_inference_support(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.families.concept.save(
        "result",
        Concept(concept_id="result", canonical_name="result"),
        message="concept",
    )
    for claim_id in ("evidence", "conclusion"):
        repo.families.claim.save(
            claim_id,
            Claim(
                claim_id=claim_id,
                claim_type=ClaimType.OBSERVATION,
                concepts=("result",),
                statement=claim_id,
            ),
            message="claim",
        )
    for licence in (
        Justification(
            justification_id="inference",
            conclusion="conclusion",
            premises=("evidence",),
            rule_kind="empirical_support",
            rule_strength="defeasible",
        ),
        Justification(
            justification_id="report",
            conclusion="conclusion",
            rule_kind="reported_claim",
        ),
    ):
        repo.families.justification.save(
            licence.justification_id, licence, message="licence"
        )
    with WorldQuery(repo) as world:
        assert _accepted(world, ("evidence",)) == {"conclusion"}


def test_promoted_source_justification_changes_real_argument_support(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.families.form.save(
        "dimensionless",
        FormDefinition(
            name="dimensionless", kind=KindType.QUANTITY, is_dimensionless=True
        ),
        message="form",
    )
    repo.families.context.save(
        "context", Context(context_id="context", name="context"), message="context"
    )
    source = "Method_Excerpt"
    init_source_branch(
        repo,
        source,
        kind=SourceKind.TECHNICAL_REPORT,
        origin_type=SourceOriginType.MANUAL,
        origin_value="regression fixture",
    )
    commit_source_concept_proposal(
        repo,
        source,
        local_name="result",
        definition="fixture result",
        form="dimensionless",
    )
    evidence = commit_source_claim_proposal(
        repo,
        source,
        claim_id="evidence",
        claim_type=ClaimType.OBSERVATION,
        context="context",
        concepts=("result",),
        statement="fixture evidence",
        page=1,
    )
    conclusion = commit_source_claim_proposal(
        repo,
        source,
        claim_id="conclusion",
        claim_type=ClaimType.OBSERVATION,
        context="context",
        concepts=("result",),
        statement="fixture inference",
        page=1,
    )
    commit_source_justification_proposal(
        repo,
        source,
        just_id="just1",
        conclusion="conclusion",
        premises=("evidence",),
        rule_kind="methodological_inference",
        rule_strength="defeasible",
        page=1,
    )
    finalize_source_branch(repo, source)
    promotion = promote_source_branch(repo, source)
    assert promotion.blocked_claims == ()
    assert evidence.artifact_id is not None and conclusion.artifact_id is not None
    with WorldQuery(repo) as world:
        stored = world.all_justifications()
        assert len(stored) == 1
        assert stored[0].conclusion == conclusion.artifact_id
        assert stored[0].premises == (evidence.artifact_id,)
        assert stored[0].justification_id.startswith("ps:justification:")
        assert conclusion.artifact_id in _accepted(world)
        assert conclusion.artifact_id not in _accepted(world, (evidence.artifact_id,))
