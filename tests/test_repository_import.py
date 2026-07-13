"""Committed-snapshot repo-to-repo import (the canonical-snapshot path).

Authors *canonical* charter documents into a source repository, then imports its
committed snapshot onto a destination's ``import/<name>`` branch as defeasible
claims with honest provenance. The Click ``import-repository`` surface is Phase 10.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from propstore.families.claims import Claim, ClaimType, ClaimVariable
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.identity.claims import derive_claim_artifact_id
from propstore.families.identity.concepts import derive_concept_artifact_id
from propstore.families.identity.stances import derive_stance_artifact_id
from propstore.families.relations import Stance
from propstore.importing.repository_import import (
    commit_repository_import,
    plan_repository_import,
)
from propstore.provenance import ProvenanceStatus, read_provenance_note
from propstore.repository import Repository
from propstore.source.common import normalize_source_slug
from propstore.stances import StanceType


def _init(root: Path) -> Repository:
    return Repository.init(root / "knowledge")


def _imported_concept_id(repository_name: str, source_concept_id: str) -> str:
    return derive_concept_artifact_id(
        f"{normalize_source_slug(repository_name)}_"
        f"{normalize_source_slug(source_concept_id)}"
    )


def _read_yaml(repo: Repository, path: str, *, commit: str) -> dict[str, object]:
    return yaml.safe_load(repo.require_git().read_file(path, commit=commit))


def test_plan_requires_git_backed_source(tmp_path: Path) -> None:
    destination = _init(tmp_path / "dest")
    plain = tmp_path / "plain"
    (plain / "knowledge" / "concept").mkdir(parents=True)

    with pytest.raises(ValueError, match="git-backed"):
        plan_repository_import(destination, plain)


def test_plan_defaults_branch_and_name_from_source(tmp_path: Path) -> None:
    destination = _init(tmp_path / "dest")
    source = _init(tmp_path / "repo-b")
    source.families.concept.save(
        "concept:legacy", Concept(concept_id="concept:legacy", canonical_name="Mass"),
        message="author concept",
    )

    plan = plan_repository_import(destination, source.root.parent)

    assert plan.repository_name == "repo-b"
    assert plan.target_branch == "import/repo-b"
    assert plan.source_commit == source.require_git().head_sha()


def test_plan_uses_committed_head_not_worktree(tmp_path: Path) -> None:
    destination = _init(tmp_path / "dest")
    source = _init(tmp_path / "repo-b")
    source.families.concept.save(
        "concept:legacy", Concept(concept_id="concept:legacy", canonical_name="Mass"),
        message="author concept",
    )
    committed = source.require_git().head_sha()
    assert committed is not None

    plan = plan_repository_import(destination, source.root.parent)
    assert plan.source_commit == committed
    new_concept_path = f"concept/{_imported_concept_id('repo-b', 'concept:legacy')}.yaml"
    assert new_concept_path in plan.writes


def test_plan_limits_to_semantic_tree_and_excludes_non_semantic(tmp_path: Path) -> None:
    destination = _init(tmp_path / "dest")
    source = _init(tmp_path / "repo-b")
    source.families.concept.save(
        "concept:legacy", Concept(concept_id="concept:legacy", canonical_name="Mass"),
        message="author concept",
    )
    source.require_git().commit_files(
        {"sidecar/propstore.sqlite": b"sqlite", "notes.txt": b"not semantic"},
        "add non-semantic files",
    )

    plan = plan_repository_import(destination, source.root.parent)

    assert plan.touched_paths == [
        f"concept/{_imported_concept_id('repo-b', 'concept:legacy')}.yaml"
    ]
    assert all(
        path.split("/", 1)[0] not in {"sidecar", "notes.txt"}
        for path in plan.touched_paths
    )


def test_commit_writes_target_branch_and_reconciles_concept_refs(tmp_path: Path) -> None:
    destination = _init(tmp_path / "dest")
    destination_git = destination.require_git()
    master_before = destination_git.head_sha()

    source = _init(tmp_path / "repo-b")
    source.families.context.save(
        "ctx", Context(context_id="ctx", name="Import context"), message="ctx"
    )
    source.families.concept.save(
        "concept:legacy", Concept(concept_id="concept:legacy", canonical_name="Mass"),
        message="concept",
    )
    source.families.claim.save(
        "claim:obs",
        Claim(
            claim_id="claim:obs",
            claim_type=ClaimType.OBSERVATION,
            statement="mass observed",
            concepts=("concept:legacy",),
            variables=(ClaimVariable(concept="concept:legacy", symbol="m"),),
            context_id="ctx",
        ),
        message="claim",
    )

    result = commit_repository_import(
        destination, plan_repository_import(destination, source.root.parent)
    )

    assert result.surface == "repository_import_commit"
    assert result.source_repository == str(source.root)
    assert result.target_branch == "import/repo-b"
    assert result.deleted_paths == []
    # master is untouched: the import lands only on the import branch.
    assert destination_git.head_sha() == master_before
    assert destination_git.branch_sha("import/repo-b") == result.commit_sha

    new_concept_id = _imported_concept_id("repo-b", "concept:legacy")
    new_claim_id = derive_claim_artifact_id("repo-b", "claim:obs")
    imported_concept: Concept | None = destination.families.concept.load(
        new_concept_id, commit=result.commit_sha
    )
    imported_claim: Claim | None = destination.families.claim.load(
        new_claim_id, commit=result.commit_sha
    )
    assert imported_concept is not None
    assert imported_concept.concept_id == new_concept_id
    assert imported_concept.canonical_name == "Mass"
    assert imported_claim is not None
    assert imported_claim.claim_id == new_claim_id
    assert imported_claim.concepts == (new_concept_id,)
    assert imported_claim.variables == (
        ClaimVariable(concept=new_concept_id, symbol="m"),
    )
    assert imported_claim.context_id == "ctx"


def test_same_named_concepts_from_rival_repositories_keep_distinct_identity(
    tmp_path: Path,
) -> None:
    destination = _init(tmp_path / "dest")
    source_a = _init(tmp_path / "repo-a")
    source_b = _init(tmp_path / "repo-b")
    for source in (source_a, source_b):
        source.families.concept.save(
            "concept:mass",
            Concept(concept_id="concept:mass", canonical_name="Mass"),
            message="concept",
        )

    result_a = commit_repository_import(
        destination, plan_repository_import(destination, source_a.root.parent)
    )
    result_b = commit_repository_import(
        destination, plan_repository_import(destination, source_b.root.parent)
    )

    concept_a_id = _imported_concept_id("repo-a", "concept:mass")
    concept_b_id = _imported_concept_id("repo-b", "concept:mass")
    assert concept_a_id != concept_b_id
    assert destination.families.concept.pin(
        branch=result_a.target_branch,
        commit=result_a.commit_sha,
    ).require(concept_a_id).canonical_name == "Mass"
    assert destination.families.concept.pin(
        branch=result_b.target_branch,
        commit=result_b.commit_sha,
    ).require(concept_b_id).canonical_name == "Mass"


def test_commit_rewrites_stance_claim_refs(tmp_path: Path) -> None:
    destination = _init(tmp_path / "dest")
    source = _init(tmp_path / "repo-b")
    source.families.claim.save(
        "claim:a",
        Claim(claim_id="claim:a", claim_type=ClaimType.OBSERVATION, statement="A"),
        message="a",
    )
    source.families.claim.save(
        "claim:b",
        Claim(claim_id="claim:b", claim_type=ClaimType.OBSERVATION, statement="B"),
        message="b",
    )
    source.families.stance.save(
        "stance:ab",
        Stance(
            stance_id="stance:ab",
            source_claim_id="claim:a",
            target_claim_id="claim:b",
            stance_type=StanceType.REBUTS,
        ),
        message="stance",
    )

    result = commit_repository_import(
        destination, plan_repository_import(destination, source.root.parent)
    )

    new_a = derive_claim_artifact_id("repo-b", "claim:a")
    new_b = derive_claim_artifact_id("repo-b", "claim:b")
    new_stance = derive_stance_artifact_id(
        source_claim_id=new_a, target_claim_id=new_b, stance_type="rebuts"
    )
    imported = _read_yaml(
        destination, f"stance/{new_stance}.yaml", commit=result.commit_sha
    )
    assert imported["source_claim_id"] == new_a
    assert imported["target_claim_id"] == new_b
    assert imported["stance_type"] == "rebuts"


def test_commit_target_master_does_not_materialize_worktree(tmp_path: Path) -> None:
    destination = _init(tmp_path / "dest")
    source = _init(tmp_path / "repo-b")
    source.families.concept.save(
        "concept:legacy", Concept(concept_id="concept:legacy", canonical_name="Mass"),
        message="concept",
    )

    plan = plan_repository_import(destination, source.root.parent, target_branch="master")
    result = commit_repository_import(destination, plan)

    assert plan.target_branch == "master"
    imported_path = (
        f"concept/{_imported_concept_id('repo-b', 'concept:legacy')}.yaml"
    )
    # colon-bearing canonical paths are never materialized to the worktree.
    assert not (destination.root / Path(imported_path)).exists()
    imported = _read_yaml(destination, imported_path, commit=result.commit_sha)
    assert imported["canonical_name"] == "Mass"


def test_plan_deletes_paths_missing_from_latest_snapshot(tmp_path: Path) -> None:
    destination = _init(tmp_path / "dest")
    destination_git = destination.require_git()
    destination_git.create_branch("import/repo-b")
    stale_concept_id = _imported_concept_id("repo-b", "concept:stale")
    destination.families.concept.save(
        stale_concept_id,
        Concept(concept_id=stale_concept_id, canonical_name="Stale"),
        message="seed stale import branch",
        branch="import/repo-b",
    )

    source = _init(tmp_path / "repo-b")
    source.families.concept.save(
        "concept:fresh", Concept(concept_id="concept:fresh", canonical_name="Fresh"),
        message="fresh",
    )

    plan = plan_repository_import(destination, source.root.parent)

    stale_path = f"concept/{stale_concept_id}.yaml"
    fresh_path = f"concept/{_imported_concept_id('repo-b', 'concept:fresh')}.yaml"
    assert plan.deletes == [stale_path]
    assert plan.touched_paths == sorted([stale_path, fresh_path])

    result = commit_repository_import(destination, plan)
    assert result.deleted_paths == [stale_path]
    with pytest.raises(FileNotFoundError):
        destination_git.read_file(stale_path, commit=result.commit_sha)


def test_import_attaches_stated_provenance_note(tmp_path: Path) -> None:
    destination = _init(tmp_path / "dest")
    source = _init(tmp_path / "repo-b")
    source.families.concept.save(
        "concept:legacy", Concept(concept_id="concept:legacy", canonical_name="Mass"),
        message="concept",
    )

    result = commit_repository_import(
        destination, plan_repository_import(destination, source.root.parent)
    )

    provenance = read_provenance_note(destination.require_git().raw_repo, result.commit_sha)
    assert provenance is not None
    assert provenance.status is ProvenanceStatus.STATED
    assert provenance.operations == ("repository-import",)
    assert provenance.derived_from == (source.require_git().head_sha(),)
    assert provenance.witnesses[0].method == "repository-import"


def test_import_is_convergent_under_repeated_commits(tmp_path: Path) -> None:
    destination = _init(tmp_path / "dest")
    source = _init(tmp_path / "repo-b")
    source.families.concept.save(
        "concept:legacy", Concept(concept_id="concept:legacy", canonical_name="Mass"),
        message="concept",
    )
    source.families.claim.save(
        "claim:obs",
        Claim(
            claim_id="claim:obs",
            claim_type=ClaimType.OBSERVATION,
            statement="mass observed",
            concepts=("concept:legacy",),
        ),
        message="claim",
    )

    first = commit_repository_import(
        destination, plan_repository_import(destination, source.root.parent)
    )
    second = commit_repository_import(
        destination, plan_repository_import(destination, source.root.parent)
    )

    git = destination.require_git()
    assert dict(git.iter_flat_tree_entries(first.commit_sha)) == dict(
        git.iter_flat_tree_entries(second.commit_sha)
    )


def test_import_repository_exports_from_importing_surface() -> None:
    from propstore import importing

    assert hasattr(importing, "plan_repository_import")
    assert hasattr(importing, "commit_repository_import")
