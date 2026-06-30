"""The propstore git store policy."""

from __future__ import annotations

from propstore.storage import PROPSTORE_GIT_POLICY


def test_authoring_identity_and_primary_branch() -> None:
    assert PROPSTORE_GIT_POLICY.author == b"pks <pks@propstore>"
    assert PROPSTORE_GIT_POLICY.primary_branch == "master"


def test_gitignore_seeded() -> None:
    assert ".gitignore" in PROPSTORE_GIT_POLICY.initial_files


def test_ignores_derived_artifacts() -> None:
    assert PROPSTORE_GIT_POLICY.ignores_path("sidecar/concept.sqlite")
    assert PROPSTORE_GIT_POLICY.ignores_path("knowledge/x.sqlite")
    assert PROPSTORE_GIT_POLICY.ignores_path("a.provenance")


def test_does_not_ignore_source_documents() -> None:
    assert not PROPSTORE_GIT_POLICY.ignores_path("concept/mass.yaml")
    assert not PROPSTORE_GIT_POLICY.ignores_path("claim/c1.yaml")
