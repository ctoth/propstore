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


def test_semantic_family_contract_includes_path_schema() -> None:
    concept = SEMANTIC_FAMILIES.by_name("concept")
    stance = SEMANTIC_FAMILIES.by_name("stance")

    concept_body = concept.contract_body()
    stance_body = stance.contract_body()

    assert concept_body["root"] == "concepts"
    assert concept_body["extension"] == ".yaml"
    assert concept_body["branch_policy"] == "primary"
    assert concept_body["filename_codec"] == "stem"
    assert concept_body["ref_type"].endswith(".ConceptFileRef")
    assert stance_body["filename_codec"] == "colon_to_double_underscore"


def test_canonical_artifact_path_helpers_are_deleted() -> None:
    import propstore.artifacts.families as artifact_families
    import propstore.artifacts.refs as artifact_refs

    refs_source = inspect.getsource(artifact_refs)
    families_source = inspect.getsource(artifact_families)
    joined = "_".join

    deleted_ref_helpers = (
        "worldline_relpath",
        "canonical_source_relpath",
        joined(("claims", "file", "relpath")),
        "micropubs_file_relpath",
        joined(("concept", "file", "relpath")),
        "justifications_file_relpath",
        "predicate_file_relpath",
        "rule_file_relpath",
        "stance_file_relpath",
        "source_claim_from_stance_path",
    )
    for helper in deleted_ref_helpers:
        assert f"def {helper}" not in refs_source

    deleted_family_helpers = (
        "_context_artifact",
        "_form_artifact",
        "_worldline_artifact",
        "_claims_file_artifact",
        "_concept_file_artifact",
        "_predicate_file_artifact",
        "_rule_file_artifact",
        "_stance_file_artifact",
        joined(("_list", "yaml", "refs", "in", "directory")),
        "_list_stance_refs_in_directory",
        joined(("_yaml", "path", "ref")),
        "_claims_file_refs",
        "_claims_file_ref_from_path",
        "_claims_file_ref_from_loaded",
        "_concept_file_refs",
        "_concept_file_ref_from_path",
        "_concept_file_ref_from_loaded",
        "_predicate_file_refs",
        "_predicate_file_ref_from_path",
        "_predicate_file_ref_from_loaded",
        "_rule_file_refs",
        "_rule_file_ref_from_path",
        "_rule_file_ref_from_loaded",
        "_stance_file_ref_from_path",
        "_worldline_ref_from_path",
        "_worldline_refs",
    )
    for helper in deleted_family_helpers:
        assert f"def {helper}" not in families_source


def test_semantic_family_owns_path_ref_and_listing_behaviour(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    concept = SEMANTIC_FAMILIES.by_name("concept")
    claim = SEMANTIC_FAMILIES.by_name("claim")
    stance = SEMANTIC_FAMILIES.by_name("stance")

    assert concept.relpath(concept.ref_type("pitch")) == "concepts/pitch.yaml"
    assert claim.ref_from_path("claims/paper.yaml").name == "paper"
    assert stance.relpath(stance.ref_type("claim:a")) == "stances/claim__a.yaml"
    assert stance.ref_from_path(repo.root / "stances" / "claim__a.yaml").source_claim == "claim:a"
    assert repo.artifacts.ref_from_path(concept.artifact_family, "concepts/pitch.yaml").name == "pitch"
    assert repo.artifacts.list(concept.artifact_family) == []


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
