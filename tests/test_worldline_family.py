"""The worldline charter family — registration, placement, and persistence.

Slice W1: the worldline is a single canonical charter type
(:class:`~propstore.worldline.definition.WorldlineDefinition`) that IS the
persisted ``worldlines`` family document. These tests pin that it registers in
the one charter-derived registry (so the ``PropstoreFamily`` drift gate stays
green), that it round-trips through ``Repository`` storage, and — unlike every
semantic charter — that it lands on the caller's **current branch**, not a fixed
canonical branch.
"""

from __future__ import annotations

from pathlib import Path

from propstore.families.registry import (
    PROPSTORE_FAMILY_REGISTRY,
    PropstoreFamily,
    WorldlineRef,
    registered_family_names,
)
from propstore.repository import Repository
from propstore.world.types import Environment, RenderPolicy, ResolutionStrategy
from propstore.worldline.definition import (
    WORLDLINE_PLACEMENT,
    WorldlineDefinition,
)
from propstore.worldline.query import WorldlineInputs


def _definition(name: str) -> WorldlineDefinition:
    # Option B: the charter stores the render policy and environment as their
    # existing dict serialization; the compute forms are rebuilt one-way via
    # ``RenderPolicy.from_dict`` / ``Environment.from_dict`` at use time.
    return WorldlineDefinition(
        name=name,
        id=name,
        inputs=WorldlineInputs(environment=Environment()).to_dict(),
        policy=RenderPolicy(strategy=ResolutionStrategy.RECENCY).to_dict(),
        targets=["Speed"],
    )


def test_worldline_family_is_registered() -> None:
    assert "worldlines" in registered_family_names()
    family = PROPSTORE_FAMILY_REGISTRY.by_name("worldlines")
    assert family.name == "worldlines"


def test_worldline_enum_matches_registry_names() -> None:
    # Mirrors the drift gate in tests/test_semantic_passes.py: adding a charter
    # without its enum member (or vice versa) must fail loudly.
    assert {member.value for member in PropstoreFamily} == set(registered_family_names())
    assert PropstoreFamily.WORLDLINES.value == "worldlines"


def test_worldline_family_has_no_foreign_keys() -> None:
    # A worldline is authored/materialized record state; like the merge-manifest
    # and conflict record families it carries no cross-family foreign keys.
    family = PROPSTORE_FAMILY_REGISTRY.by_name("worldlines")
    assert family.foreign_keys == ()


def test_worldline_round_trips_through_repository(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    definition = _definition("wl1")

    repo.families.worldlines.save(WorldlineRef("wl1"), definition, message="add wl1")
    loaded = repo.families.worldlines.load(WorldlineRef("wl1"))

    assert loaded is not None
    assert loaded == definition
    assert loaded.targets == ["Speed"]
    # The stored policy is a mapping; the compile path reconstructs the policy.
    assert RenderPolicy.from_dict(loaded.policy).strategy is ResolutionStrategy.RECENCY


def test_worldline_places_on_the_current_branch(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    git = repo.require_git()

    # Seed one worldline so master has a commit to branch from.
    repo.families.worldlines.save(WorldlineRef("base"), _definition("base"), message="base")
    master_sha = git.branch_sha("master")
    assert master_sha is not None

    git.create_branch("feature", source_commit=master_sha)
    git.set_current_branch("feature")
    assert git.current_branch_name() == "feature"

    # No explicit branch -> the placement follows the current branch.
    address = WORLDLINE_PLACEMENT.address_for(repo, WorldlineRef("only_on_feature"))
    assert address.branch == "feature"

    repo.families.worldlines.save(
        WorldlineRef("only_on_feature"), _definition("only_on_feature"), message="on feature"
    )

    assert repo.families.worldlines.exists(WorldlineRef("only_on_feature"), branch="feature")
    assert not repo.families.worldlines.exists(
        WorldlineRef("only_on_feature"), branch="master"
    )


def test_worldline_is_mutable_on_the_current_branch(tmp_path: Path) -> None:
    # A worldline is mutable authored state: re-saving under the same ref updates
    # it in place (the non-commitment discipline is about the semantic corpus,
    # not this current-branch working artifact).
    repo = Repository.init(tmp_path / "knowledge")
    repo.families.worldlines.save(WorldlineRef("wl"), _definition("wl"), message="v1")

    updated = _definition("wl")
    updated.created = "2026-06-30"
    repo.families.worldlines.save(WorldlineRef("wl"), updated, message="v2")

    loaded = repo.families.worldlines.load(WorldlineRef("wl"))
    assert loaded is not None
    assert loaded.created == "2026-06-30"
