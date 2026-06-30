"""Phase 8-4: predicate proposal artifacts + the promote workflow.

Ports the owner-layer behaviour of the reference predicate-proposal suites
(test_proposal_predicates_family, test_promote_predicates_proposals) to the
rewrite charters, seeding proposals through :func:`propose_predicates` (the
recorder) rather than the LLM extraction heuristic. The LLM ``propose_*`` side
(propstore.heuristic.predicate_extraction), the app conflict layer, and the CLI
stay recorded in docs/rewrite/deferred-tests.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.families.predicates import (
    PredicateDeclaration,
    PredicateExtractionProvenance,
    PredicateProposal,
    PredicateProposalRef,
)
from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY
from propstore.proposal_promotion import UnknownProposalPath
from propstore.proposals_predicates import (
    PredicateProposalConflict,
    plan_predicate_proposal_promotion,
    predicate_proposal_branch,
    promote_predicate_proposals,
    propose_predicates,
)
from propstore.repository import Repository

PAPER = "Ioannidis_2005_WhyMostPublishedResearch"


def test_commit_planned_canonical_artifacts_uses_one_transaction() -> None:
    from propstore.proposal_promotion import (
        PlannedCanonicalArtifact,
        commit_planned_canonical_artifacts,
    )

    class _Writer:
        def __init__(self) -> None:
            self.saved: list[tuple[str, str]] = []

        def save(self, ref: str, document: str) -> None:
            self.saved.append((ref, document))

    class _Transaction:
        def __init__(self) -> None:
            self.writer = _Writer()

    class _Transact:
        def __init__(self) -> None:
            self.messages: list[str] = []
            self.entered = 0
            self.transaction = _Transaction()

        def __call__(self, *, message: str) -> _Transact:
            self.messages.append(message)
            return self

        def __enter__(self) -> _Transaction:
            self.entered += 1
            return self.transaction

        def __exit__(self, *_exc: object) -> None:
            return None

    transact = _Transact()
    count = commit_planned_canonical_artifacts(
        transact,
        message="Promote planned",
        family=lambda transaction: transaction.writer,
        artifacts=(
            PlannedCanonicalArtifact("ref-a", "doc-a"),
            PlannedCanonicalArtifact("ref-b", "doc-b"),
        ),
    )
    assert count == 2
    assert transact.entered == 1
    assert transact.transaction.writer.saved == [("ref-a", "doc-a"), ("ref-b", "doc-b")]


def test_commit_planned_canonical_artifacts_empty_is_noop() -> None:
    from propstore.proposal_promotion import commit_planned_canonical_artifacts

    class _Writer:
        def save(self, ref: str, document: str) -> None:  # pragma: no cover
            raise AssertionError("empty promotion must not save")

    class _Transact:
        def __init__(self) -> None:
            self.entered = 0
            self.writer = _Writer()

        def __call__(self, *, message: str) -> _Transact:
            return self

        def __enter__(self) -> _Transact:
            self.entered += 1
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

    transact = _Transact()
    count = commit_planned_canonical_artifacts(
        transact,
        message="nothing",
        family=lambda transaction: transaction.writer,
        artifacts=(),
    )
    assert count == 0
    assert transact.entered == 0


def _provenance() -> PredicateExtractionProvenance:
    return PredicateExtractionProvenance(
        operations=("predicate_extraction",),
        agent="test",
        model="test-model",
        prompt_sha="prompt",
        notes_sha="notes",
        status="stated",
    )


def _declarations() -> tuple[PredicateDeclaration, ...]:
    return (
        PredicateDeclaration(
            name="sample_size",
            arity=2,
            arg_types=("paper_id", "int"),
            description="Paper-level sample size.",
        ),
        PredicateDeclaration(
            name="statistical_power",
            arity=2,
            arg_types=("paper_id", "float"),
            description="Paper-level statistical power.",
        ),
    )


def _seed(repo: Repository, *, paper: str = PAPER) -> str:
    sha = propose_predicates(
        repo,
        source_paper=paper,
        declarations=_declarations(),
        extraction_provenance=_provenance(),
        extraction_date="2026-05-05",
    )
    assert sha is not None
    return sha


# --- charter / document typing -------------------------------------------------


def test_proposal_predicates_family_is_registered(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    ref = PredicateProposalRef(PAPER)
    assert repo.families.proposal_predicates.family is (
        PROPSTORE_FAMILY_REGISTRY.by_name("proposal_predicates").artifact_family
    )
    assert repo.families.proposal_predicates.address(ref).require_path() == (
        f"predicates/{PAPER}/declarations.yaml"
    )


def test_predicate_proposal_document_round_trips() -> None:
    codec = PredicateProposal.__charter__.document_codec()
    document = PredicateProposal(
        source_paper=PAPER,
        proposed_declarations=_declarations(),
        extraction_provenance=_provenance(),
        extraction_date="2026-05-05",
    )
    decoded = codec.decode(
        codec.encode(document), PredicateProposal, source="declarations.yaml"
    )
    assert decoded.source_paper == PAPER
    assert decoded.proposed_declarations[0].arg_types == ("paper_id", "int")


@pytest.mark.parametrize(
    "arg_type",
    ["paper_id", "int", "float", "str", "bool", "enum:hot|warm|cold"],
)
def test_predicate_arg_type_closed_set_accepts_known_tags(arg_type: str) -> None:
    declaration = PredicateDeclaration(
        name="typed", arity=1, arg_types=(arg_type,), description="t"
    )
    assert declaration.arg_types == (arg_type,)


def test_predicate_arg_type_rejects_unknown_tag() -> None:
    with pytest.raises(ValueError, match="unsupported predicate arg type"):
        PredicateDeclaration(
            name="bad", arity=1, arg_types=("callable",), description="t"
        )


def test_predicate_declaration_arity_must_match_arg_types() -> None:
    with pytest.raises(ValueError, match="does not match arity"):
        PredicateDeclaration(
            name="bad", arity=2, arg_types=("paper_id",), description="t"
        )


# --- propose / promote lifecycle ----------------------------------------------


def test_propose_predicates_writes_only_to_proposal_branch(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    sha = _seed(repo)

    assert sha == repo.require_git().branch_sha(predicate_proposal_branch())
    # Nothing canonical was written.
    assert list(repo.families.predicate.iter()) == []
    document = repo.families.proposal_predicates.require(
        PredicateProposalRef(PAPER), commit=sha
    )
    assert [d.name for d in document.proposed_declarations] == [
        "sample_size",
        "statistical_power",
    ]


def test_promote_writes_canonical_and_is_idempotent(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    proposal_sha = _seed(repo)

    plan = plan_predicate_proposal_promotion(repo, source_paper=PAPER)
    result = promote_predicate_proposals(repo, plan)
    assert result.moved == 2

    for predicate_id in ("sample_size", "statistical_power"):
        document = repo.families.predicate.require(predicate_id)
        assert document.predicate_id == predicate_id
        assert document.authoring_group == PAPER
        assert document.promoted_from_sha == proposal_sha

    # Re-planning after promotion yields nothing (idempotent).
    assert plan_predicate_proposal_promotion(repo, source_paper=PAPER).items == ()


def test_plan_unknown_paper_raises(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _seed(repo)
    with pytest.raises(UnknownProposalPath, match="does-not-exist"):
        plan_predicate_proposal_promotion(repo, source_paper="does-not-exist")


def test_plan_missing_branch_has_no_items(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    plan = plan_predicate_proposal_promotion(repo, source_paper=PAPER)
    assert plan.has_branch is False
    assert plan.items == ()


def test_promote_rejects_cross_group_duplicate(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    # An existing canonical predicate declared by a different group.
    from propstore.families.predicates import Predicate

    repo.families.predicate.save(
        "sample_size",
        Predicate(
            predicate_id="sample_size",
            arity=2,
            arg_types=("paper_id", "int"),
            description="Existing.",
            authoring_group="other_paper",
        ),
        message="seed canonical predicate",
    )
    git = repo.require_git()
    master_before = git.branch_sha(git.primary_branch_name())
    _seed(repo)

    plan = plan_predicate_proposal_promotion(repo, source_paper=PAPER)
    with pytest.raises(PredicateProposalConflict, match="already declared"):
        promote_predicate_proposals(repo, plan)

    # The canonical corpus is untouched: the rival is preserved, master unmoved.
    assert git.branch_sha(git.primary_branch_name()) == master_before
    assert repo.families.predicate.require("sample_size").authoring_group == "other_paper"
