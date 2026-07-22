"""Canonical grounding reconstruction from the charter-derived world sidecar."""

from __future__ import annotations

from pathlib import Path

from quire.sqlalchemy_store import readonly_session

from propstore.compiler.workflows import build_repository
from propstore.derived_schema import build_world_sidecar_schema
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.predicates import Predicate
from propstore.families.rules import Atom, BodyLiteral, DefeasibleRule, Term
from propstore.grounding.bundle import GroundedRulesBundle, GroundingStatus
from propstore.grounding.loading import (
    build_grounded_bundle,
    load_grounded_bundle_from_sidecar,
    load_grounding_repo,
)
from propstore.repository import Repository


def _load_sidecar_bundle(path: str) -> GroundedRulesBundle:
    schema = build_world_sidecar_schema()
    with readonly_session(Path(path), schema) as session:
        return load_grounded_bundle_from_sidecar(session)


def _seed_grounding_repo(path: Path) -> Repository:
    repo = Repository.init(path)
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "cl1",
        Claim(
            claim_id="cl1",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            value=1.0,
        ),
        message="m",
    )
    repo.families.predicate.save(
        "has_value",
        Predicate(
            predicate_id="has_value",
            arity=1,
            arg_types=("Claim",),
            derived_from="claim.attribute:value",
        ),
        message="m",
    )
    repo.families.predicate.save(
        "important",
        Predicate(predicate_id="important", arity=1, arg_types=("Claim",)),
        message="m",
    )
    repo.families.defeasible_rule.save(
        "r1",
        DefeasibleRule(
            rule_id="r1",
            kind="defeasible",
            head=Atom(predicate="important", terms=(Term(kind="var", name="X"),)),
            body=(
                BodyLiteral(
                    kind="positive",
                    atom=Atom(
                        predicate="has_value", terms=(Term(kind="var", name="X"),)
                    ),
                ),
            ),
        ),
        message="m",
    )
    repo.require_git().commit_files(
        {"propstore.yaml": b"grounding_max_arguments: 100\n"},
        "Set grounding budget",
    )
    return repo


def test_empty_grounding_sidecar_reconstructs_complete_bundle(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )

    report = build_repository(repo)

    assert report.derived_store is not None
    bundle = _load_sidecar_bundle(report.derived_store.path)
    assert bundle.status is GroundingStatus.COMPLETE
    assert bundle.max_arguments is None
    assert bundle.source_facts == ()
    assert bundle.arguments == ()


def test_sidecar_only_session_reconstructs_full_repository_bundle(
    tmp_path: Path,
) -> None:
    repo = _seed_grounding_repo(tmp_path / "kn")
    report = build_repository(repo)

    assert report.derived_store is not None
    sidecar_bundle = _load_sidecar_bundle(report.derived_store.path)
    repository_bundle = build_grounded_bundle(
        load_grounding_repo(repo, commit=report.derived_store.source_commit),
        return_arguments=True,
        max_arguments=100,
    )

    assert sidecar_bundle == repository_bundle
    assert sidecar_bundle.status is GroundingStatus.COMPLETE
    assert sidecar_bundle.max_arguments == 100
    assert ("cl1",) in sidecar_bundle.sections["yes"]["has_value"]
    assert ("cl1",) in sidecar_bundle.sections["yes"]["important"]
    assert sidecar_bundle.grounding_inspection is not None
    assert sidecar_bundle.arguments
