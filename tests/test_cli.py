"""Tests for the pks CLI.

Uses Click's CliRunner for isolated testing with temporary directories.
Each test gets a fresh concepts directory with known state.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from compiler.cli import cli


# ── Fixtures ─────────────────────────────────────────────────────────

def _make_concept(name: str, cid: str, domain: str, status: str = "accepted",
                  form: str = "frequency", **extra: object) -> dict:
    """Build a minimal valid concept dict."""
    data: dict = {
        "id": cid,
        "canonical_name": name,
        "status": status,
        "definition": f"Test definition for {name}.",
        "domain": domain,
        "created_date": "2026-03-15",
        "form": form,
    }
    data.update(extra)
    return data


def _write_concept(concepts_dir: Path, name: str, data: dict) -> Path:
    """Write a concept YAML file and return its path."""
    concepts_dir.mkdir(parents=True, exist_ok=True)
    p = concepts_dir / f"{name}.yaml"
    with open(p, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    return p


def _write_counter(concepts_dir: Path, domain: str, value: int) -> None:
    """Write a counter file."""
    counters = concepts_dir / ".counters"
    counters.mkdir(parents=True, exist_ok=True)
    (counters / f"{domain}.next").write_text(f"{value}\n")


def _read_counter(concepts_dir: Path, domain: str) -> int:
    return int((concepts_dir / ".counters" / f"{domain}.next").read_text().strip())



@pytest.fixture()
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up a temporary workspace with concepts and counters."""
    monkeypatch.chdir(tmp_path)

    concepts = tmp_path / "concepts"
    concepts.mkdir()

    # Create form definition files
    forms_dir = tmp_path / "forms"
    forms_dir.mkdir()
    for form_name in ("frequency", "category", "boolean", "structural",
                      "duration_ratio", "pressure", "level", "time",
                      "flow", "flow_derivative", "amplitude_ratio",
                      "dimensionless_compound"):
        (forms_dir / f"{form_name}.yaml").write_text(
            yaml.dump({"name": form_name}, default_flow_style=False))

    # Write two concepts
    _write_concept(concepts, "fundamental_frequency", _make_concept(
        "fundamental_frequency", "speech_0001", "speech",
        form="frequency",
        range=[50, 1000],
        aliases=[{"name": "F0", "source": "common"}],
    ))
    _write_concept(concepts, "task", _make_concept(
        "task", "speech_0002", "speech",
        form="category",
        form_parameters={"values": ["speech", "singing"], "extensible": True},
    ))

    _write_counter(concepts, "speech", 3)

    # Copy schema if it exists (for JSON Schema validation)
    schema_src = Path(__file__).parent.parent / "schema" / "generated" / "concept_registry.schema.json"
    if schema_src.exists():
        schema_dir = tmp_path / "schema" / "generated"
        schema_dir.mkdir(parents=True)
        (schema_dir / "concept_registry.schema.json").write_text(schema_src.read_text())

    return tmp_path


# ── concept add ──────────────────────────────────────────────────────

class TestConceptAdd:
    def test_creates_valid_file(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "add",
            "--domain", "speech",
            "--name", "test_pressure",
            "--definition", "A test concept",
            "--form", "pressure",
        ])
        assert result.exit_code == 0, result.output
        assert "Created" in result.output

        filepath = workspace / "concepts" / "test_pressure.yaml"
        assert filepath.exists()
        data = yaml.safe_load(filepath.read_text())
        assert data["id"] == "concept3"
        assert data["canonical_name"] == "test_pressure"
        assert data["status"] == "proposed"
        assert data["form"] == "pressure"

    def test_increments_counter(self, workspace: Path) -> None:
        runner = CliRunner()
        runner.invoke(cli, [
            "concept", "add",
            "--domain", "speech", "--name", "c1",
            "--definition", "d1", "--form", "boolean",
        ])
        assert _read_counter(workspace / "concepts", "speech") == 4

        runner.invoke(cli, [
            "concept", "add",
            "--domain", "speech", "--name", "c2",
            "--definition", "d2", "--form", "boolean",
        ])
        assert _read_counter(workspace / "concepts", "speech") == 5

    def test_dry_run_does_not_write(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "add",
            "--domain", "speech", "--name", "ghost",
            "--definition", "d", "--form", "boolean",
            "--dry-run",
        ])
        assert result.exit_code == 0
        assert "Would create" in result.output
        assert not (workspace / "concepts" / "ghost.yaml").exists()


# ── concept alias ────────────────────────────────────────────────────

class TestConceptAlias:
    def test_adds_alias(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "alias", "speech_0001",
            "--name", "f_zero", "--source", "Smith_2020",
        ])
        assert result.exit_code == 0, result.output
        assert "Added alias" in result.output

        data = yaml.safe_load(
            (workspace / "concepts" / "fundamental_frequency.yaml").read_text())
        alias_names = [a["name"] for a in data["aliases"]]
        assert "f_zero" in alias_names

    def test_warns_on_name_collision(self, workspace: Path) -> None:
        runner = CliRunner()
        # "task" is a canonical_name of speech_0002
        result = runner.invoke(cli, [
            "concept", "alias", "speech_0001",
            "--name", "task", "--source", "test",
        ])
        assert result.exit_code == 0
        assert "WARNING" in result.output


# ── concept rename ───────────────────────────────────────────────────

class TestConceptRename:
    def test_renames_file_and_field(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "rename", "speech_0002",
            "--name", "vocal_task",
        ])
        assert result.exit_code == 0, result.output
        assert "task -> vocal_task" in result.output

        old_path = workspace / "concepts" / "task.yaml"
        new_path = workspace / "concepts" / "vocal_task.yaml"
        assert not old_path.exists()
        assert new_path.exists()

        data = yaml.safe_load(new_path.read_text())
        assert data["canonical_name"] == "vocal_task"
        assert data["id"] == "speech_0002"  # ID unchanged


# ── concept deprecate ────────────────────────────────────────────────

class TestConceptDeprecate:
    def test_sets_fields(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "deprecate", "speech_0002",
            "--replaced-by", "speech_0001",
        ])
        assert result.exit_code == 0, result.output
        assert "Deprecated" in result.output

        data = yaml.safe_load(
            (workspace / "concepts" / "task.yaml").read_text())
        assert data["status"] == "deprecated"
        assert data["replaced_by"] == "speech_0001"

    def test_rejects_nonexistent_replacement(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "deprecate", "speech_0002",
            "--replaced-by", "speech_9999",
        ])
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_rejects_deprecated_replacement(self, workspace: Path) -> None:
        # First deprecate speech_0002
        data = yaml.safe_load(
            (workspace / "concepts" / "task.yaml").read_text())
        data["status"] = "deprecated"
        data["replaced_by"] = "speech_0001"
        with open(workspace / "concepts" / "task.yaml", "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "deprecate", "speech_0001",
            "--replaced-by", "speech_0002",
        ])
        assert result.exit_code != 0
        assert "deprecated" in result.output


# ── concept link ─────────────────────────────────────────────────────

class TestConceptLink:
    def test_adds_relationship(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "link", "speech_0001", "broader", "speech_0002",
        ])
        assert result.exit_code == 0, result.output
        assert "Added broader" in result.output

        data = yaml.safe_load(
            (workspace / "concepts" / "fundamental_frequency.yaml").read_text())
        rels = data.get("relationships", [])
        assert any(r["type"] == "broader" and r["target"] == "speech_0002" for r in rels)


# ── validate ─────────────────────────────────────────────────────────

class TestValidate:
    def test_passes_on_valid(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["validate"])
        assert result.exit_code == 0
        assert "passed" in result.output

    def test_fails_on_invalid(self, workspace: Path) -> None:
        # Write a broken concept
        bad = workspace / "concepts" / "broken.yaml"
        bad.write_text(yaml.dump({
            "id": "speech_0001",  # duplicate ID
            "canonical_name": "broken",
            "status": "accepted",
            "definition": "dup",
            "form": "frequency",
        }))
        runner = CliRunner()
        result = runner.invoke(cli, ["validate"])
        assert result.exit_code != 0
        assert "FAILED" in result.output


# ── build ────────────────────────────────────────────────────────────

class TestBuild:
    def test_produces_sidecar(self, workspace: Path) -> None:
        runner = CliRunner()
        sidecar = workspace / "sidecar" / "propstore.sqlite"
        result = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result.exit_code == 0, result.output
        assert sidecar.exists()
        assert "rebuilt" in result.output

        conn = sqlite3.connect(sidecar)
        count = conn.execute("SELECT count(*) FROM concept").fetchone()[0]
        conn.close()
        assert count == 2

    def test_refuses_on_validation_failure(self, workspace: Path) -> None:
        bad = workspace / "concepts" / "broken.yaml"
        bad.write_text(yaml.dump({
            "id": "speech_0001",  # duplicate
            "canonical_name": "broken",
            "status": "accepted",
            "definition": "dup",
            "form": "frequency",
        }))
        runner = CliRunner()
        sidecar = workspace / "sidecar" / "propstore.sqlite"
        result = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result.exit_code != 0
        assert not sidecar.exists()
