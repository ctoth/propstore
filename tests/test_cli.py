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
    """Write the global counter file (domain param kept for compat)."""
    counters = concepts_dir / ".counters"
    counters.mkdir(parents=True, exist_ok=True)
    (counters / "global.next").write_text(f"{value}\n")


def _read_counter(concepts_dir: Path, domain: str) -> int:
    return int((concepts_dir / ".counters" / "global.next").read_text().strip())


def _write_claim_file(claims_dir: Path, filename: str, data: dict) -> Path:
    claims_dir.mkdir(parents=True, exist_ok=True)
    path = claims_dir / filename
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
    return path



@pytest.fixture()
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up a temporary workspace with knowledge/ containing concepts, forms, etc."""
    monkeypatch.chdir(tmp_path)

    knowledge = tmp_path / "knowledge"
    concepts = knowledge / "concepts"
    concepts.mkdir(parents=True)

    # Create form definition files
    forms_dir = knowledge / "forms"
    forms_dir.mkdir()
    _dimensionless_forms = {"duration_ratio", "amplitude_ratio", "level", "dimensionless_compound"}
    for form_name in ("frequency", "category", "boolean", "structural",
                      "duration_ratio", "pressure", "level", "time",
                      "flow", "flow_derivative", "amplitude_ratio",
                      "dimensionless_compound"):
        (forms_dir / f"{form_name}.yaml").write_text(
            yaml.dump({"name": form_name, "dimensionless": form_name in _dimensionless_forms},
                      default_flow_style=False))

    # Write two concepts
    _write_concept(concepts, "fundamental_frequency", _make_concept(
        "fundamental_frequency", "concept1", "speech",
        form="frequency",
        range=[50, 1000],
        aliases=[{"name": "F0", "source": "common"}],
    ))
    _write_concept(concepts, "task", _make_concept(
        "task", "concept2", "speech",
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


class TestInit:
    def test_creates_forms_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output
        assert (tmp_path / "knowledge" / "forms").is_dir()
        assert (tmp_path / "knowledge" / "forms" / "pressure.yaml").exists()

    def test_fresh_project_can_add_concept(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        init_result = runner.invoke(cli, ["init"])
        assert init_result.exit_code == 0, init_result.output

        add_result = runner.invoke(cli, [
            "-C", str(tmp_path / "knowledge"),
            "concept", "add",
            "--domain", "speech",
            "--name", "test_pressure",
            "--definition", "A test concept",
            "--form", "pressure",
        ])
        assert add_result.exit_code == 0, add_result.output
        assert "Created" in add_result.output
        assert (tmp_path / "knowledge" / "concepts" / "test_pressure.yaml").exists()


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

        filepath = workspace / "knowledge" / "concepts" / "test_pressure.yaml"
        assert filepath.exists()
        data = yaml.safe_load(filepath.read_text())
        assert data["id"] == "concept3"
        assert data["canonical_name"] == "test_pressure"
        assert data["status"] == "proposed"
        assert data["form"] == "pressure"

    def test_created_concept_can_be_shown_by_id(self, workspace: Path) -> None:
        runner = CliRunner()
        add_result = runner.invoke(cli, [
            "concept", "add",
            "--domain", "speech",
            "--name", "test_pressure",
            "--definition", "A test concept",
            "--form", "pressure",
        ])
        assert add_result.exit_code == 0, add_result.output

        show_result = runner.invoke(cli, ["concept", "show", "concept3"])
        assert show_result.exit_code == 0, show_result.output
        assert "canonical_name: test_pressure" in show_result.output

    def test_increments_counter(self, workspace: Path) -> None:
        runner = CliRunner()
        runner.invoke(cli, [
            "concept", "add",
            "--domain", "speech", "--name", "c1",
            "--definition", "d1", "--form", "boolean",
        ])
        assert _read_counter(workspace / "knowledge" / "concepts", "speech") == 4

        runner.invoke(cli, [
            "concept", "add",
            "--domain", "speech", "--name", "c2",
            "--definition", "d2", "--form", "boolean",
        ])
        assert _read_counter(workspace / "knowledge" / "concepts", "speech") == 5

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
        assert not (workspace / "knowledge" / "concepts" / "ghost.yaml").exists()

    def test_validation_failure_does_not_advance_counter(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "add",
            "--domain", "speech",
            "--name", "bad_pressure",
            "--definition", "d",
            "--form", "missing_form",
        ])
        assert result.exit_code != 0
        assert not (workspace / "knowledge" / "concepts" / "bad_pressure.yaml").exists()
        assert _read_counter(workspace / "knowledge" / "concepts", "speech") == 3


# ── concept alias ────────────────────────────────────────────────────

class TestConceptAlias:
    def test_adds_alias(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "alias", "concept1",
            "--name", "f_zero", "--source", "Smith_2020",
        ])
        assert result.exit_code == 0, result.output
        assert "Added alias" in result.output

        data = yaml.safe_load(
            (workspace / "knowledge" / "concepts" / "fundamental_frequency.yaml").read_text())
        alias_names = [a["name"] for a in data["aliases"]]
        assert "f_zero" in alias_names

    def test_warns_on_name_collision(self, workspace: Path) -> None:
        runner = CliRunner()
        # "task" is a canonical_name of concept2
        result = runner.invoke(cli, [
            "concept", "alias", "concept1",
            "--name", "task", "--source", "test",
        ])
        assert result.exit_code == 0
        assert "WARNING" in result.output


# ── concept rename ───────────────────────────────────────────────────

class TestConceptRename:
    def test_renames_file_and_field(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "rename", "concept2",
            "--name", "vocal_task",
        ])
        assert result.exit_code == 0, result.output
        assert "task -> vocal_task" in result.output

        old_path = workspace / "knowledge" / "concepts" / "task.yaml"
        new_path = workspace / "knowledge" / "concepts" / "vocal_task.yaml"
        assert not old_path.exists()
        assert new_path.exists()

        data = yaml.safe_load(new_path.read_text())
        assert data["canonical_name"] == "vocal_task"
        assert data["id"] == "concept2"  # ID unchanged

    def test_updates_cel_references_in_concepts_and_claims(self, workspace: Path) -> None:
        concept_path = workspace / "knowledge" / "concepts" / "fundamental_frequency.yaml"
        concept_data = yaml.safe_load(concept_path.read_text())
        concept_data["relationships"] = [
            {"type": "related", "target": "concept2", "conditions": ["task == 'speech'"]}
        ]
        concept_path.write_text(yaml.dump(concept_data, default_flow_style=False, sort_keys=False))

        claims_dir = workspace / "knowledge" / "claims"
        _write_claim_file(
            claims_dir,
            "paper.yaml",
            {
                "source": {"paper": "paper"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "parameter",
                        "concept": "concept1",
                        "value": 200.0,
                        "unit": "Hz",
                        "conditions": ["task == 'speech'"],
                        "provenance": {"paper": "paper", "page": 1},
                    }
                ],
            },
        )

        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "rename", "concept2",
            "--name", "vocal_task",
        ])
        assert result.exit_code == 0, result.output

        renamed_concept = yaml.safe_load((workspace / "knowledge" / "concepts" / "fundamental_frequency.yaml").read_text())
        assert renamed_concept["relationships"][0]["conditions"] == ["vocal_task == 'speech'"]

        claim_data = yaml.safe_load((workspace / "knowledge" / "claims" / "paper.yaml").read_text())
        assert claim_data["claims"][0]["conditions"] == ["vocal_task == 'speech'"]


# ── concept deprecate ────────────────────────────────────────────────

class TestConceptDeprecate:
    def test_sets_fields(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "deprecate", "concept2",
            "--replaced-by", "concept1",
        ])
        assert result.exit_code == 0, result.output
        assert "Deprecated" in result.output

        data = yaml.safe_load(
            (workspace / "knowledge" / "concepts" / "task.yaml").read_text())
        assert data["status"] == "deprecated"
        assert data["replaced_by"] == "concept1"

    def test_rejects_nonexistent_replacement(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "deprecate", "concept2",
            "--replaced-by", "concept9999",
        ])
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_rejects_deprecated_replacement(self, workspace: Path) -> None:
        # First deprecate concept2
        data = yaml.safe_load(
            (workspace / "knowledge" / "concepts" / "task.yaml").read_text())
        data["status"] = "deprecated"
        data["replaced_by"] = "concept1"
        with open(workspace / "knowledge" / "concepts" / "task.yaml", "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "deprecate", "concept1",
            "--replaced-by", "concept2",
        ])
        assert result.exit_code != 0
        assert "deprecated" in result.output


# ── concept link ─────────────────────────────────────────────────────

class TestConceptLink:
    def test_adds_relationship(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "link", "concept1", "broader", "concept2",
        ])
        assert result.exit_code == 0, result.output
        assert "Added broader" in result.output

        data = yaml.safe_load(
            (workspace / "knowledge" / "concepts" / "fundamental_frequency.yaml").read_text())
        rels = data.get("relationships", [])
        assert any(r["type"] == "broader" and r["target"] == "concept2" for r in rels)


# ── validate ─────────────────────────────────────────────────────────

class TestValidate:
    def test_passes_on_valid(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["validate"])
        assert result.exit_code == 0
        assert "passed" in result.output

    def test_fails_on_invalid(self, workspace: Path) -> None:
        # Write a broken concept
        bad = workspace / "knowledge" / "concepts" / "broken.yaml"
        bad.write_text(yaml.dump({
            "id": "concept1",  # duplicate ID
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
        sidecar = workspace / "knowledge" / "sidecar" / "propstore.sqlite"
        result = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result.exit_code == 0, result.output
        assert sidecar.exists()
        assert "rebuilt" in result.output

        conn = sqlite3.connect(sidecar)
        count = conn.execute("SELECT count(*) FROM concept").fetchone()[0]
        conn.close()
        assert count == 2

    def test_refuses_on_validation_failure(self, workspace: Path) -> None:
        bad = workspace / "knowledge" / "concepts" / "broken.yaml"
        bad.write_text(yaml.dump({
            "id": "concept1",  # duplicate
            "canonical_name": "broken",
            "status": "accepted",
            "definition": "dup",
            "form": "frequency",
        }))
        runner = CliRunner()
        sidecar = workspace / "knowledge" / "sidecar" / "propstore.sqlite"
        result = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result.exit_code != 0
        assert not sidecar.exists()


class TestQuery:
    def test_query_returns_rows(self, workspace: Path) -> None:
        runner = CliRunner()
        build_result = runner.invoke(cli, ["build"])
        assert build_result.exit_code == 0, build_result.output

        query_result = runner.invoke(cli, ["query", "SELECT count(*) AS n FROM concept"])
        assert query_result.exit_code == 0, query_result.output
        assert "n" in query_result.output
        assert "2" in query_result.output


class TestWorkflow:
    def test_init_add_build_query_workflow(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        init_result = runner.invoke(cli, ["init"])
        assert init_result.exit_code == 0, init_result.output

        project_root = tmp_path / "knowledge"
        add_result = runner.invoke(
            cli,
            [
                "-C", str(project_root),
                "concept", "add",
                "--domain", "speech",
                "--name", "test_pressure",
                "--definition", "A test concept",
                "--form", "pressure",
            ],
        )
        assert add_result.exit_code == 0, add_result.output

        build_result = runner.invoke(cli, ["-C", str(project_root), "build"])
        assert build_result.exit_code == 0, build_result.output

        query_result = runner.invoke(
            cli,
            ["-C", str(project_root), "query", "SELECT canonical_name FROM concept ORDER BY canonical_name"],
        )
        assert query_result.exit_code == 0, query_result.output
        assert "canonical_name" in query_result.output
        assert "test_pressure" in query_result.output


class TestImportPapers:
    def test_imports_claims_from_papers_root(self, workspace: Path) -> None:
        papers_root = workspace / "plugin-papers"
        paper_dir = papers_root / "Smith_2024_TestPaper"
        paper_dir.mkdir(parents=True)
        (paper_dir / "claims.yaml").write_text(yaml.dump({
            "claims": [
                {
                    "id": "claim1",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 200.0,
                    "unit": "Hz",
                    "provenance": {"paper": "ignored_here", "page": 1},
                }
            ]
        }, default_flow_style=False, sort_keys=False))

        runner = CliRunner()
        result = runner.invoke(cli, [
            "import-papers",
            "--papers-root", str(papers_root),
        ])
        assert result.exit_code == 0, result.output
        imported = yaml.safe_load((workspace / "knowledge" / "claims" / "Smith_2024_TestPaper.yaml").read_text())
        assert imported["source"]["paper"] == "Smith_2024_TestPaper"
        assert imported["claims"][0]["id"] == "claim1"

    def test_import_papers_no_papers_dir(self, workspace: Path) -> None:
        """import-papers with nonexistent papers root should fail (Click path validation)."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "import-papers",
            "--papers-root", str(workspace / "nonexistent"),
        ])
        assert result.exit_code != 0

    def test_import_papers_no_yaml_files(self, workspace: Path) -> None:
        """import-papers with empty papers root should report no files found."""
        papers_root = workspace / "empty-papers"
        papers_root.mkdir()
        runner = CliRunner()
        result = runner.invoke(cli, [
            "import-papers",
            "--papers-root", str(papers_root),
        ])
        assert result.exit_code == 0
        assert "No claims.yaml" in result.output

    def test_import_papers_correct_claim_file_content(self, workspace: Path) -> None:
        """Imported claim file should have correct source.paper and all claims preserved."""
        papers_root = workspace / "plugin-papers"
        paper_dir = papers_root / "Author_2025_Title"
        paper_dir.mkdir(parents=True)
        (paper_dir / "claims.yaml").write_text(yaml.dump({
            "claims": [
                {
                    "id": "claim1",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 100.0,
                    "unit": "Hz",
                    "provenance": {"paper": "ignored", "page": 2},
                },
                {
                    "id": "claim2",
                    "type": "observation",
                    "statement": "F0 varies",
                    "concepts": ["concept1"],
                    "provenance": {"paper": "ignored", "page": 3},
                },
            ]
        }, default_flow_style=False, sort_keys=False))

        runner = CliRunner()
        result = runner.invoke(cli, [
            "import-papers",
            "--papers-root", str(papers_root),
        ])
        assert result.exit_code == 0, result.output

        imported = yaml.safe_load((workspace / "knowledge" / "claims" / "Author_2025_Title.yaml").read_text())
        assert imported["source"]["paper"] == "Author_2025_Title"
        assert len(imported["claims"]) == 2
        assert imported["claims"][0]["id"] == "claim1"
        assert imported["claims"][1]["id"] == "claim2"


# ── build (extended) ────────────────────────────────────────────────

class TestBuildExtended:
    def test_sidecar_contains_expected_tables(self, workspace: Path) -> None:
        """Built sidecar should contain concept, alias, relationship, concept_fts tables."""
        runner = CliRunner()
        sidecar = workspace / "knowledge" / "sidecar" / "propstore.sqlite"
        result = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result.exit_code == 0, result.output

        conn = sqlite3.connect(sidecar)
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        conn.close()

        assert "concept" in tables
        assert "alias" in tables
        assert "relationship" in tables
        assert "concept_fts" in tables

    def test_sidecar_contains_concept_data(self, workspace: Path) -> None:
        """Built sidecar should have correct concept names and IDs."""
        runner = CliRunner()
        sidecar = workspace / "knowledge" / "sidecar" / "propstore.sqlite"
        result = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result.exit_code == 0, result.output

        conn = sqlite3.connect(sidecar)
        rows = conn.execute(
            "SELECT id, canonical_name FROM concept ORDER BY id"
        ).fetchall()
        conn.close()

        ids = [r[0] for r in rows]
        names = [r[1] for r in rows]
        assert "concept1" in ids
        assert "concept2" in ids
        assert "fundamental_frequency" in names
        assert "task" in names

    def test_sidecar_contains_aliases(self, workspace: Path) -> None:
        """Built sidecar should include alias data from concepts."""
        runner = CliRunner()
        sidecar = workspace / "knowledge" / "sidecar" / "propstore.sqlite"
        result = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result.exit_code == 0, result.output

        conn = sqlite3.connect(sidecar)
        aliases = conn.execute("SELECT alias_name FROM alias").fetchall()
        conn.close()

        alias_names = [r[0] for r in aliases]
        assert "F0" in alias_names

    def test_build_with_claims(self, workspace: Path) -> None:
        """Build with claim files should create claim table with data."""
        claims_dir = workspace / "knowledge" / "claims"
        _write_claim_file(claims_dir, "paper.yaml", {
            "source": {"paper": "paper"},
            "claims": [
                {
                    "id": "claim1",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 200.0,
                    "unit": "Hz",
                    "provenance": {"paper": "paper", "page": 1},
                }
            ],
        })

        runner = CliRunner()
        sidecar = workspace / "knowledge" / "sidecar" / "propstore.sqlite"
        result = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result.exit_code == 0, result.output

        conn = sqlite3.connect(sidecar)
        count = conn.execute("SELECT count(*) FROM claim").fetchone()[0]
        conn.close()
        assert count == 1

    def test_build_force_rebuilds(self, workspace: Path) -> None:
        """--force should trigger rebuild even when content hasn't changed."""
        runner = CliRunner()
        sidecar = workspace / "knowledge" / "sidecar" / "propstore.sqlite"

        # First build
        result1 = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result1.exit_code == 0, result1.output
        assert "rebuilt" in result1.output

        # Second build without force — should be unchanged
        result2 = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result2.exit_code == 0, result2.output
        assert "unchanged" in result2.output

        # Third build with --force — should rebuild
        result3 = runner.invoke(cli, ["build", "--force", "-o", str(sidecar)])
        assert result3.exit_code == 0, result3.output
        assert "rebuilt" in result3.output

    def test_build_skip_on_unchanged_content(self, workspace: Path) -> None:
        """Building twice without changes should skip on the second run."""
        runner = CliRunner()
        sidecar = workspace / "knowledge" / "sidecar" / "propstore.sqlite"

        result1 = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result1.exit_code == 0
        assert "rebuilt" in result1.output

        result2 = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result2.exit_code == 0
        assert "unchanged" in result2.output


# ── export-aliases ──────────────────────────────────────────────────

class TestExportAliases:
    def test_export_aliases_json(self, workspace: Path) -> None:
        """export-aliases --format json should produce valid JSON with alias data."""
        import json as _json
        runner = CliRunner()
        result = runner.invoke(cli, ["export-aliases", "--format", "json"])
        assert result.exit_code == 0, result.output

        data = _json.loads(result.output)
        assert isinstance(data, dict)
        assert "F0" in data
        assert data["F0"]["id"] == "concept1"
        assert data["F0"]["name"] == "fundamental_frequency"

    def test_export_aliases_text(self, workspace: Path) -> None:
        """export-aliases in text mode should show alias -> concept mappings."""
        runner = CliRunner()
        result = runner.invoke(cli, ["export-aliases"])
        assert result.exit_code == 0, result.output
        assert "F0" in result.output
        assert "concept1" in result.output


# ── concept search ──────────────────────────────────────────────────

class TestConceptSearch:
    def test_search_by_name_yaml_fallback(self, workspace: Path) -> None:
        """concept search should find concepts by name via YAML grep fallback."""
        runner = CliRunner()
        result = runner.invoke(cli, ["concept", "search", "fundamental"])
        assert result.exit_code == 0, result.output
        assert "concept1" in result.output
        assert "fundamental_frequency" in result.output

    def test_search_by_definition_yaml_fallback(self, workspace: Path) -> None:
        """concept search should find concepts by definition text."""
        runner = CliRunner()
        result = runner.invoke(cli, ["concept", "search", "definition"])
        assert result.exit_code == 0, result.output
        # Both concepts have "Test definition for X" in their definition
        assert "concept1" in result.output

    def test_search_no_matches(self, workspace: Path) -> None:
        """concept search with no matches should report no matches."""
        runner = CliRunner()
        result = runner.invoke(cli, ["concept", "search", "zzz_nonexistent_zzz"])
        assert result.exit_code == 0
        assert "No matches" in result.output

    def test_search_uses_fts_when_sidecar_exists(self, workspace: Path) -> None:
        """concept search should use FTS when sidecar is available."""
        runner = CliRunner()
        # Build sidecar first
        build_result = runner.invoke(cli, ["build"])
        assert build_result.exit_code == 0, build_result.output

        # Search using FTS
        result = runner.invoke(cli, ["concept", "search", "fundamental"])
        assert result.exit_code == 0, result.output
        assert "concept1" in result.output
        assert "fundamental_frequency" in result.output
