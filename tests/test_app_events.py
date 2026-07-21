"""App-layer coreference resolution: policy-dependence, honest gaps, claim scope.

The proof that coreference is decided at RENDER time and never stored: the SAME
stored rival merge arguments yield ``()`` clusters under sceptical grounded
semantics and rival clusters under credulous preferred semantics. An unsupported
semantics returns a typed failure, never a silent grounded fallback.
"""

from __future__ import annotations

from pathlib import Path

from propstore.app.events import (
    CoreferenceClustersReport,
    UnknownCoreferenceArgument,
    UnsupportedCoreferenceSemantics,
    coreference_clusters,
    coreference_clusters_for_claim,
    propose_coreference_merge_argument,
    record_coreference_attack,
)
from propstore.core.reasoning import ArgumentationSemantics
from propstore.core.render_policy import RenderPolicy
from propstore.provenance import ProvenanceStatus
from propstore.repository import Repository


def _policy(semantics: ArgumentationSemantics) -> RenderPolicy:
    return RenderPolicy(semantics=semantics)


def _seed_rivals(repo: Repository) -> tuple[str, str]:
    """Two mutually-attacking rival merges sharing claim_b."""

    first = propose_coreference_merge_argument(
        repo, supports=("claim_a", "claim_b")
    ).argument_id
    second = propose_coreference_merge_argument(
        repo, supports=("claim_b", "claim_c")
    ).argument_id
    record_coreference_attack(repo, attacker_id=first, target_id=second)
    record_coreference_attack(repo, attacker_id=second, target_id=first)
    return first, second


def _cluster_claim_sets(report: CoreferenceClustersReport) -> set[frozenset[str]]:
    return {frozenset(view.claim_ids) for view in report.clusters}


def test_rivals_give_no_grounded_cluster_but_rival_preferred_clusters(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path)
    _seed_rivals(repo)

    grounded = coreference_clusters(repo, _policy(ArgumentationSemantics.GROUNDED))
    assert isinstance(grounded, CoreferenceClustersReport)
    assert grounded.clusters == ()

    preferred = coreference_clusters(repo, _policy(ArgumentationSemantics.PREFERRED))
    assert isinstance(preferred, CoreferenceClustersReport)
    assert _cluster_claim_sets(preferred) == {
        frozenset({"claim_a", "claim_b"}),
        frozenset({"claim_b", "claim_c"}),
    }


def test_unattacked_argument_clusters_under_both_semantics(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    propose_coreference_merge_argument(repo, supports=("claim_x", "claim_y"))

    for semantics in (ArgumentationSemantics.GROUNDED, ArgumentationSemantics.PREFERRED):
        report = coreference_clusters(repo, _policy(semantics))
        assert isinstance(report, CoreferenceClustersReport)
        assert _cluster_claim_sets(report) == {frozenset({"claim_x", "claim_y"})}


def test_supporting_arguments_carry_provenance_for_drilldown(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    propose_coreference_merge_argument(repo, supports=("claim_x", "claim_y"))

    report = coreference_clusters(repo, _policy(ArgumentationSemantics.GROUNDED))
    assert isinstance(report, CoreferenceClustersReport)
    (view,) = report.clusters
    (argument,) = view.supporting_arguments
    assert argument.supports == ("claim_x", "claim_y")
    assert argument.provenance.status is ProvenanceStatus.STATED


def test_unsupported_semantics_is_typed_failure_not_fallback(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _seed_rivals(repo)

    result = coreference_clusters(repo, _policy(ArgumentationSemantics.STABLE))
    assert isinstance(result, UnsupportedCoreferenceSemantics)
    assert result.requested is ArgumentationSemantics.STABLE
    assert set(result.supported) == {
        ArgumentationSemantics.GROUNDED,
        ArgumentationSemantics.PREFERRED,
    }
    assert "stable" in result.message()


def test_claim_scoped_returns_all_rival_clusters_under_preferred(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _seed_rivals(repo)

    preferred = coreference_clusters_for_claim(
        repo, "claim_b", _policy(ArgumentationSemantics.PREFERRED)
    )
    assert isinstance(preferred, CoreferenceClustersReport)
    # claim_b sits in BOTH rival clusters; both are returned, never one picked.
    assert _cluster_claim_sets(preferred) == {
        frozenset({"claim_a", "claim_b"}),
        frozenset({"claim_b", "claim_c"}),
    }

    # claim_a is only in the first rival cluster.
    only_a = coreference_clusters_for_claim(
        repo, "claim_a", _policy(ArgumentationSemantics.PREFERRED)
    )
    assert isinstance(only_a, CoreferenceClustersReport)
    assert _cluster_claim_sets(only_a) == {frozenset({"claim_a", "claim_b"})}


def test_claim_scoped_grounded_rivals_yield_empty(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _seed_rivals(repo)

    grounded = coreference_clusters_for_claim(
        repo, "claim_b", _policy(ArgumentationSemantics.GROUNDED)
    )
    assert isinstance(grounded, CoreferenceClustersReport)
    assert grounded.clusters == ()


def test_attack_on_unknown_argument_raises(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    known = propose_coreference_merge_argument(
        repo, supports=("claim_a", "claim_b")
    ).argument_id

    for attacker, target in ((known, "cma:missing"), ("cma:missing", known)):
        try:
            record_coreference_attack(repo, attacker_id=attacker, target_id=target)
        except UnknownCoreferenceArgument as exc:
            assert exc.argument_id == "cma:missing"
        else:  # pragma: no cover - defensive
            raise AssertionError("expected UnknownCoreferenceArgument")
