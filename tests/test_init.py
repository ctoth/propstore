"""Tests for pks init."""
from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository


def _visible_paths(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if ".git" not in path.relative_to(root).parts
    }


@pytest.fixture()
def empty_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty temporary directory with no propstore structure."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestInit:
    def test_preference_import_does_not_require_world_layer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Kernel submodules should import without package root pulling in world machinery."""
        blocked = {
            "propstore.world.bound",
            "propstore.world.hypothetical",
            "propstore.world.model",
        }
        original_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in blocked:
                raise ImportError(f"blocked {name}")
            return original_import(name, globals, locals, fromlist, level)

        for module_name in list(sys.modules):
            if module_name == "propstore" or module_name.startswith("propstore.world"):
                monkeypatch.delitem(sys.modules, module_name, raising=False)
        monkeypatch.delitem(sys.modules, "propstore.preference", raising=False)
        monkeypatch.setattr(builtins, "__import__", guarded_import)

        preference = importlib.import_module("propstore.preference")

        assert preference.claim_strength(
            {"sample_size": 10, "uncertainty": 0.2, "confidence": 0.8}
        ).dimensions == (2.3978952727983707, 5.0, 0.8)

    def test_root_exports_still_resolve_lazily(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Public package-root exports should remain available after lazy-loading."""
        for module_name in list(sys.modules):
            if module_name == "propstore" or module_name.startswith("propstore.world"):
                monkeypatch.delitem(sys.modules, module_name, raising=False)

        propstore = importlib.import_module("propstore")

        assert propstore.RenderPolicy.__name__ == "RenderPolicy"
        assert propstore.WorldModel.__name__ == "WorldModel"

    def test_init_creates_store_only_repository(self, empty_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output
        assert "Initialized" in result.output

        root = empty_workspace / "knowledge"
        assert (root / ".git").is_dir()
        assert not (root / "concepts").exists()
        assert not (root / "forms").exists()
        assert not (root / "claims").exists()
        assert "concepts/measurement.yaml" in Repository.find(root).git.flat_tree_entries()
        assert "forms/frequency.yaml" in Repository.find(root).git.flat_tree_entries()
        assert _visible_paths(root) == set()

    def test_creates_at_custom_path(self, empty_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "myproject"])
        assert result.exit_code == 0, result.output
        assert "myproject" in result.output

        root = empty_workspace / "myproject"
        assert (root / ".git").is_dir()
        assert not (root / "concepts").exists()
        assert "concepts/measurement.yaml" in Repository.find(root).git.flat_tree_entries()

    def test_already_initialized(self, empty_workspace: Path) -> None:
        runner = CliRunner()
        # First init
        runner.invoke(cli, ["init", "proj"])
        # Second init — should skip
        result = runner.invoke(cli, ["init", "proj"])
        assert result.exit_code == 0
        assert "Already initialized" in result.output

    def test_validate_after_init(self, empty_workspace: Path) -> None:
        """After init, pks validate should succeed (empty but valid)."""
        runner = CliRunner()
        runner.invoke(cli, ["init", "proj"])

        # pks -C proj validate
        # Since -C requires exists=True and we use CliRunner,
        # we chdir manually and invoke validate directly.
        import os
        os.chdir(empty_workspace / "proj")
        result = runner.invoke(cli, ["validate"])
        assert result.exit_code == 0, result.output

    def test_init_seeds_phase3_description_kind_concepts_in_store(self, empty_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output

        repo = Repository.find(empty_workspace / "knowledge")
        required = {
            "observation",
            "measurement",
            "assertion",
            "decision",
            "reaction",
        }
        seeded = {
            Path(path).stem
            for path in repo.git.flat_tree_entries()
            if path.startswith("concepts/") and path.endswith(".yaml")
        }
        assert required <= seeded

        for name in required:
            data = yaml.safe_load(repo.git.read_file(f"concepts/{name}.yaml"))
            sense = data["lexical_entry"]["senses"][0]
            description_kind = sense["description_kind"]
            assert description_kind["reference"]["uri"] == data["artifact_id"]
            assert description_kind["slots"], f"{name} has no participant slots"
            assert all("type_constraint" in slot for slot in description_kind["slots"])

    def test_init_seeds_qualia_and_causal_connection_examples_in_store(self, empty_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output

        repo = Repository.find(empty_workspace / "knowledge")
        instrument = yaml.safe_load(repo.git.read_file("concepts/measurement_instrument.yaml"))
        measurement = yaml.safe_load(repo.git.read_file("concepts/measurement.yaml"))
        instrument_sense = instrument["lexical_entry"]["senses"][0]
        telic = instrument_sense["qualia"]["telic"][0]
        assert telic["reference"]["uri"] == measurement["artifact_id"]
        assert telic["type_constraint"]["reference"]["uri"] == measurement["artifact_id"]
        assert telic["provenance"]["status"] == "stated"

        causal = yaml.safe_load(repo.git.read_file("concepts/causal_connection.yaml"))
        causal_kind = causal["lexical_entry"]["senses"][0]["description_kind"]
        slot_names = {slot["name"] for slot in causal_kind["slots"]}
        assert {"cause-description", "effect-description", "account"} <= slot_names

    def test_init_with_directory_flag(self, empty_workspace: Path) -> None:
        """pks -C /some/path init should create knowledge/ inside that path."""
        subdir = empty_workspace / "parent"
        subdir.mkdir()

        runner = CliRunner()
        result = runner.invoke(cli, ["-C", str(subdir), "init"])
        assert result.exit_code == 0, result.output

        root = subdir / "knowledge"
        assert (root / ".git").is_dir()
        assert not (root / "concepts").exists()
        assert "forms/frequency.yaml" in Repository.find(root).git.flat_tree_entries()

    def test_init_directory_flag_accepts_new_path(self, empty_workspace: Path) -> None:
        """pks -C NEW init NEW should let init create the selected tree."""
        root = empty_workspace / "new_knowledge"

        result = CliRunner().invoke(cli, ["-C", str(root), "init", "new_knowledge"])

        assert result.exit_code == 0, result.output
        repo_root = root / "new_knowledge"
        assert (repo_root / ".git").is_dir()
        assert not (repo_root / "concepts").exists()
        assert "forms/frequency.yaml" in Repository.find(repo_root).git.flat_tree_entries()

    def test_seed_form_blobs_are_valid_yaml(self, empty_workspace: Path) -> None:
        """Generated form files should be valid YAML with at least a 'name' field."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output

        repo = Repository.find(empty_workspace / "knowledge")
        form_paths = [
            path
            for path in repo.git.flat_tree_entries()
            if path.startswith("forms/") and path.endswith(".yaml")
        ]
        assert len(form_paths) > 0, "No form files generated"

        for form_path in form_paths:
            data = yaml.safe_load(repo.git.read_file(form_path))
            stem = Path(form_path).stem
            assert isinstance(data, dict), f"{form_path} is not a YAML mapping"
            assert "name" in data, f"{form_path} missing 'name' field"
            assert data["name"] == stem, (
                f"{form_path}: name field '{data['name']}' != stem '{stem}'"
            )

    def test_init_does_not_materialize_semantic_directory_structure(self, empty_workspace: Path) -> None:
        """init should create the store, not a materialized knowledge tree."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output

        root = empty_workspace / "knowledge"
        semantic_roots = {
            "claims",
            "concepts",
            "contexts",
            "forms",
            "justifications",
            "predicates",
            "rules",
            "sources",
            "stances",
            "worldlines",
        }
        assert all(not (root / name).exists() for name in semantic_roots)
        assert _visible_paths(root) == set()

    def test_schema_dir_not_required(self, empty_workspace: Path) -> None:
        """init should not create a schema/ directory (schema is separate)."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output

        # schema/ is NOT part of the init structure
        root = empty_workspace / "knowledge"
        # Just verify init doesn't crash; schema/ is optional
        assert not (root / "schema").exists()
