from __future__ import annotations

import inspect
import importlib.util
from pathlib import Path

from quire.artifacts import ArtifactFamily
from quire.references import ForeignKeySpec

from propstore.artifacts.families import (
    PROPSTORE_FAMILY_REGISTRY,
    PropstoreFamily,
    semantic_address_path,
    semantic_family_by_name,
    semantic_family_by_root,
    semantic_family_for_path,
    semantic_family_names,
    semantic_foreign_keys,
    semantic_init_roots,
)
from propstore.compiler.references import iter_semantic_foreign_keys
from propstore.repository import Repository


def test_semantic_registry_declares_complete_canonical_family_set() -> None:
    assert set(semantic_family_names()) == {
        "claims",
        "concepts",
        "contexts",
        "forms",
        "predicates",
        "rules",
        "stances",
        "worldlines",
    }

    assert semantic_family_by_root("claims").name == "claims"
    assert semantic_family_by_root("rules").name == "rules"
    assert semantic_family_for_path("predicates/base.yaml").name == "predicates"


def test_semantic_registry_exposes_artifact_families_for_rules_and_predicates() -> None:
    rule = semantic_family_by_name(PropstoreFamily.RULES.value)
    predicate = semantic_family_by_name(PropstoreFamily.PREDICATES.value)

    assert isinstance(rule.artifact_family, ArtifactFamily)
    assert isinstance(predicate.artifact_family, ArtifactFamily)
    assert rule.artifact_family.placement.contract_body()["namespace"] == "rules"
    assert predicate.artifact_family.placement.contract_body()["namespace"] == "predicates"
    assert rule.metadata and rule.metadata["collection_field"] == "rules"
    assert predicate.metadata and predicate.metadata["collection_field"] == "predicates"


def test_semantic_family_contract_includes_path_schema() -> None:
    concept = semantic_family_by_name(PropstoreFamily.CONCEPTS.value)
    stance = semantic_family_by_name(PropstoreFamily.STANCES.value)

    concept_body = concept.contract_body()
    stance_body = stance.contract_body()
    concept_placement = concept_body["artifact_family_contract"]["placement"]
    stance_placement = stance_body["artifact_family_contract"]["placement"]

    assert concept_placement["namespace"] == "concepts"
    assert concept_placement["extension"] == ".yaml"
    assert concept_placement["branch"] == {"policy": "primary"}
    assert concept_placement["codec"] == "stem"
    assert stance_placement["codec"] == "colon_to_double_underscore"
    assert "root" not in concept_body
    assert "filename_codec" not in concept_body
    assert concept_body["artifact_family_contract"]["doc_type"].endswith(".ConceptDocument")


def test_canonical_artifact_path_helpers_are_deleted() -> None:
    import propstore.artifacts.families as artifact_families

    assert importlib.util.find_spec("propstore.artifacts.refs") is None

    families_source = inspect.getsource(artifact_families)
    joined = "_".join

    deleted_helpers = (
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
    for helper in deleted_helpers:
        assert f"def {helper}" not in families_source

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
    concept = semantic_family_by_name(PropstoreFamily.CONCEPTS.value)
    claim = semantic_family_by_name(PropstoreFamily.CLAIMS.value)
    stance = semantic_family_by_name(PropstoreFamily.STANCES.value)

    assert semantic_address_path(concept.name, repo, repo.families.concepts.ref_from_path("concepts/pitch.yaml")) == "concepts/pitch.yaml"
    assert repo.families.by_name(claim.name).ref_from_path("claims/paper.yaml").name == "paper"
    assert semantic_address_path(stance.name, repo, repo.families.stances.ref_from_path("stances/claim__a.yaml")) == "stances/claim__a.yaml"
    assert repo.families.by_name(stance.name).ref_from_path("stances/claim__a.yaml").source_claim == "claim:a"
    assert repo.families.concepts.ref_from_path("concepts/pitch.yaml").name == "pitch"
    assert repo.families.concepts.list() == []


def test_repository_init_semantic_roots_match_registry(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    for root in semantic_init_roots():
        assert (repo.root / root).is_dir()

    initialized_semantic_roots = {
        child.name
        for child in repo.root.iterdir()
        if child.is_dir() and child.name != "sidecar"
    }
    assert set(semantic_init_roots()) <= initialized_semantic_roots


def test_repository_import_module_has_no_local_semantic_root_dispatch() -> None:
    import propstore.storage.repository_import as repository_import

    source = inspect.getsource(repository_import)

    assert "SEMANTIC_ROOT_DIRS" not in source
    assert "if root == " not in source
    assert "path.startswith(\"claims/\")" not in source
    assert "path.startswith(\"concepts/\")" not in source
    assert "path.startswith(\"stances/\")" not in source


def test_compiler_foreign_keys_are_registry_derived() -> None:
    registry_specs = tuple(semantic_foreign_keys())
    compiler_specs = iter_semantic_foreign_keys()

    assert registry_specs
    assert compiler_specs == registry_specs
    assert all(isinstance(spec, ForeignKeySpec) for spec in compiler_specs)


def test_propstore_registry_is_the_semantic_schema_surface() -> None:
    concepts = PROPSTORE_FAMILY_REGISTRY.by_key(PropstoreFamily.CONCEPTS)

    assert concepts.name == "concepts"
    assert concepts.artifact_family.doc_type.__name__ == "ConceptDocument"
    assert concepts.metadata and concepts.metadata["semantic"] is True
