"""The Repository knowledge-repository facade."""

from __future__ import annotations

from pathlib import Path

import pytest

from quire.git_store import GitStore

from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.claims import Claim
from propstore.families.micropublications import Micropublication, MicropublicationEvidence
from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY
from propstore.repository import (
    PROPSTORE_REPOSITORY_FORMAT_VERSION,
    Repository,
    RepositoryNotFound,
)
from propstore.storage.git_policy import PROPSTORE_GIT_POLICY
from propstore.uri import DEFAULT_URI_AUTHORITY


def test_init_creates_git_backed_propstore_repo(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    assert repo.root == tmp_path
    assert repo.git is not None
    assert Repository.is_propstore_repo(tmp_path)


def test_bootstrap_manifest_records_format_and_contract(tmp_path: Path) -> None:
    Repository.init(tmp_path)
    git = GitStore.open(tmp_path, policy=PROPSTORE_GIT_POLICY)
    from propstore.repository import PROPSTORE_BOOTSTRAP_REF, _read_bootstrap_manifest

    manifest = _read_bootstrap_manifest(git)
    assert manifest is not None
    assert manifest["repository_format_version"] == PROPSTORE_REPOSITORY_FORMAT_VERSION
    assert manifest["primary_branch"] == "master"
    assert PROPSTORE_BOOTSTRAP_REF.value == "refs/propstore/bootstrap"


def test_plain_git_repo_is_not_a_propstore_repo(tmp_path: Path) -> None:
    GitStore.init(tmp_path, policy=PROPSTORE_GIT_POLICY)
    assert not Repository.is_propstore_repo(tmp_path)


def test_find_locates_repo_at_root(tmp_path: Path) -> None:
    Repository.init(tmp_path)
    found = Repository.find(start=tmp_path)
    assert found.root == tmp_path


def test_find_walks_up_to_knowledge_directory(tmp_path: Path) -> None:
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    Repository.init(knowledge)
    found = Repository.find(start=tmp_path)
    assert found.root == knowledge


def test_find_raises_when_no_propstore_repo(tmp_path: Path) -> None:
    with pytest.raises(RepositoryNotFound):
        Repository.find(start=tmp_path)


def test_families_bind_to_the_registry(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    assert repo.families.registry is PROPSTORE_FAMILY_REGISTRY


def test_concept_round_trips_through_repo_families(tmp_path: Path) -> None:
    # The canonical authoring path: author + load via the bound family registry.
    repo = Repository.init(tmp_path)
    concept = Concept(concept_id="concept:mass", canonical_name="mass")
    repo.families.concept.save("concept:mass", concept, message="author mass")
    loaded = repo.families.concept.load("concept:mass")
    assert loaded == concept


def test_micropublication_round_trips_with_resolved_references(tmp_path: Path) -> None:
    # A multi-family round-trip: a json-blob-heavy micropublication whose context
    # and claim references resolve saves and loads through one bound store, and
    # the registry's foreign-key validation accepts the resolved references.
    repo = Repository.init(tmp_path)
    repo.families.context.save("ctx1", Context(context_id="ctx1", name="C"), message="m")
    repo.families.claim.save("cl1", Claim(claim_id="cl1"), message="m")
    micropub = Micropublication(
        artifact_id="mp1",
        context_id="ctx1",
        claims=("cl1",),
        evidence=(MicropublicationEvidence(kind="figure", reference="fig1"),),
        assumptions=("a1",),
        source="src:test",
    )
    repo.families.micropublication.save("mp1", micropub, message="author mp")
    loaded = repo.families.micropublication.load("mp1")
    assert loaded == micropub


def test_uri_authority_defaults_without_config(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    assert repo.uri_authority is DEFAULT_URI_AUTHORITY


def test_snapshot_lists_the_primary_branch(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    branches = {info.name for info in repo.snapshot.iter_branches()}
    assert "master" in branches


def test_tree_returns_a_path_for_a_git_repo(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    assert repo.tree() is not None


def test_mutation_guard_requires_git(tmp_path: Path) -> None:
    repo = Repository(tmp_path)  # no init -> not git-backed
    with pytest.raises(ValueError, match="git-backed"):
        with repo.mutation_guard():
            pass


def test_mutation_guard_runs_on_git_repo(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    with repo.mutation_guard():
        pass
