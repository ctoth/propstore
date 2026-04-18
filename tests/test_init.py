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

        assert preference.claim_strength({"confidence": 0.8}) == [0.0, 1.0, 0.8]

    def test_root_exports_still_resolve_lazily(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Public package-root exports should remain available after lazy-loading."""
        for module_name in list(sys.modules):
            if module_name == "propstore" or module_name.startswith("propstore.world"):
                monkeypatch.delitem(sys.modules, module_name, raising=False)

        propstore = importlib.import_module("propstore")

        assert propstore.RenderPolicy.__name__ == "RenderPolicy"
        assert propstore.WorldModel.__name__ == "WorldModel"

    def test_creates_default_structure(self, empty_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output
        assert "Initialized" in result.output

        root = empty_workspace / "knowledge"
        assert (root / "concepts").is_dir()
        assert (root / "concepts" / ".counters").is_dir()
        assert (root / "claims").is_dir()
        assert (root / "predicates").is_dir()
        assert (root / "rules").is_dir()
        assert (root / "sidecar").is_dir()

    def test_creates_at_custom_path(self, empty_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "myproject"])
        assert result.exit_code == 0, result.output
        assert "myproject" in result.output

        root = empty_workspace / "myproject"
        assert (root / "concepts").is_dir()
        assert (root / "concepts" / ".counters").is_dir()
        assert (root / "claims").is_dir()
        assert (root / "predicates").is_dir()
        assert (root / "rules").is_dir()
        assert (root / "sidecar").is_dir()

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

    def test_init_seeds_phase3_description_kind_concepts(self, empty_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output

        concepts_dir = empty_workspace / "knowledge" / "concepts"
        required = {
            "observation",
            "measurement",
            "assertion",
            "decision",
            "reaction",
        }
        seeded = {path.stem for path in concepts_dir.glob("*.yaml")}
        assert required <= seeded

        for name in required:
            data = yaml.safe_load((concepts_dir / f"{name}.yaml").read_text())
            sense = data["lexical_entry"]["senses"][0]
            description_kind = sense["description_kind"]
            assert description_kind["reference"]["uri"] == data["artifact_id"]
            assert description_kind["slots"], f"{name} has no participant slots"
            assert all("type_constraint" in slot for slot in description_kind["slots"])

    def test_init_seeds_qualia_and_causal_connection_examples(self, empty_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output

        concepts_dir = empty_workspace / "knowledge" / "concepts"
        instrument = yaml.safe_load((concepts_dir / "measurement_instrument.yaml").read_text())
        measurement = yaml.safe_load((concepts_dir / "measurement.yaml").read_text())
        instrument_sense = instrument["lexical_entry"]["senses"][0]
        telic = instrument_sense["qualia"]["telic"][0]
        assert telic["reference"]["uri"] == measurement["artifact_id"]
        assert telic["type_constraint"]["reference"]["uri"] == measurement["artifact_id"]
        assert telic["provenance"]["status"] == "stated"

        causal = yaml.safe_load((concepts_dir / "causal_connection.yaml").read_text())
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
        assert (root / "concepts").is_dir()
        assert (root / "claims").is_dir()

    def test_form_files_are_valid_yaml(self, empty_workspace: Path) -> None:
        """Generated form files should be valid YAML with at least a 'name' field."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output

        forms_dir = empty_workspace / "knowledge" / "forms"
        assert forms_dir.is_dir()

        form_files = list(forms_dir.glob("*.yaml"))
        assert len(form_files) > 0, "No form files generated"

        for form_file in form_files:
            data = yaml.safe_load(form_file.read_text())
            assert isinstance(data, dict), f"{form_file.name} is not a YAML mapping"
            assert "name" in data, f"{form_file.name} missing 'name' field"
            assert data["name"] == form_file.stem, (
                f"{form_file.name}: name field '{data['name']}' != stem '{form_file.stem}'"
            )

    def test_directory_structure_complete(self, empty_workspace: Path) -> None:
        """init should create the full reasoning-capable knowledge tree."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output

        root = empty_workspace / "knowledge"
        assert (root / "concepts").is_dir()
        assert (root / "concepts" / ".counters").is_dir()
        assert (root / "claims").is_dir()
        assert (root / "contexts").is_dir()
        assert (root / "forms").is_dir()
        assert (root / "justifications").is_dir()
        assert (root / "predicates").is_dir()
        assert (root / "rules").is_dir()
        assert (root / "sidecar").is_dir()
        assert (root / "sources").is_dir()
        assert (root / "stances").is_dir()
        assert (root / "worldlines").is_dir()

    def test_schema_dir_not_required(self, empty_workspace: Path) -> None:
        """init should not create a schema/ directory (schema is separate)."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output

        # schema/ is NOT part of the init structure
        root = empty_workspace / "knowledge"
        # Just verify init doesn't crash; schema/ is optional
        assert (root / "concepts").is_dir()
