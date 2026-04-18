from __future__ import annotations

import inspect
from pathlib import Path

from quire.artifacts import ArtifactFamily
from quire.references import ForeignKeySpec

from propstore.artifacts.semantic_families import SEMANTIC_FAMILIES
from propstore.compiler.references import iter_semantic_foreign_keys
from propstore.repository import Repository


def test_semantic_registry_declares_complete_canonical_family_set() -> None:
    assert set(SEMANTIC_FAMILIES.names()) == {
        "claim",
        "concept",
        "context",
        "form",
        "predicate",
        "rule",
        "stance",
        "worldline",
    }

    assert SEMANTIC_FAMILIES.by_root("claims").name == "claim"
    assert SEMANTIC_FAMILIES.by_root("rules").name == "rule"
    assert SEMANTIC_FAMILIES.family_for_path("predicates/base.yaml").name == "predicate"


def test_semantic_registry_exposes_artifact_families_for_rules_and_predicates() -> None:
    rule = SEMANTIC_FAMILIES.by_name("rule")
    predicate = SEMANTIC_FAMILIES.by_name("predicate")

    assert isinstance(rule.artifact_family, ArtifactFamily)
    assert isinstance(predicate.artifact_family, ArtifactFamily)
    assert rule.root == "rules"
    assert predicate.root == "predicates"
    assert rule.collection_field == "rules"
    assert predicate.collection_field == "predicates"


def test_repository_init_semantic_roots_match_registry(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    for root in SEMANTIC_FAMILIES.init_roots():
        assert (repo.root / root).is_dir()

    initialized_semantic_roots = {
        child.name
        for child in repo.root.iterdir()
        if child.is_dir() and child.name != "sidecar"
    }
    assert set(SEMANTIC_FAMILIES.init_roots()) <= initialized_semantic_roots


def test_repository_import_module_has_no_local_semantic_root_dispatch() -> None:
    import propstore.storage.repository_import as repository_import

    source = inspect.getsource(repository_import)

    assert "SEMANTIC_ROOT_DIRS" not in source
    assert "if root == " not in source
    assert "path.startswith(\"claims/\")" not in source
    assert "path.startswith(\"concepts/\")" not in source
    assert "path.startswith(\"stances/\")" not in source


def test_compiler_foreign_keys_are_registry_derived() -> None:
    registry_specs = tuple(SEMANTIC_FAMILIES.foreign_keys())
    compiler_specs = iter_semantic_foreign_keys()

    assert registry_specs
    assert compiler_specs == registry_specs
    assert all(isinstance(spec, ForeignKeySpec) for spec in compiler_specs)
