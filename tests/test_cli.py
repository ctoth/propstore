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

from propstore.cli import cli


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
        form_data: dict = {"name": form_name, "dimensionless": form_name in _dimensionless_forms}
        if form_name == "category":
            form_data["kind"] = "category"
            form_data["parameters"] = {
                "values": {"required": True, "note": "List of allowed category values"},
                "extensible": {"required": False, "note": "Whether new values can be added (default true)"},
            }
        (forms_dir / f"{form_name}.yaml").write_text(
            yaml.dump(form_data, default_flow_style=False))

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
        assert (tmp_path / "knowledge" / "forms" / "category.yaml").exists()

    def test_fresh_project_can_add_concept(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        init_result = runner.invoke(cli, ["init"])
        assert init_result.exit_code == 0, init_result.output

        add_result = runner.invoke(cli, [
            "-C", str(tmp_path / "knowledge"),
            "concept", "add",
            "--domain", "test",
            "--name", "test_structural",
            "--definition", "A test concept",
            "--form", "structural",
        ])
        assert add_result.exit_code == 0, add_result.output
        assert "Created" in add_result.output
        assert (tmp_path / "knowledge" / "concepts" / "test_structural.yaml").exists()


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

    def test_rejects_invalid_relationship_without_writing(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "link", "concept1", "contested_definition", "concept2",
        ])
        assert result.exit_code != 0
        assert "Validation failed" in result.output

        data = yaml.safe_load(
            (workspace / "knowledge" / "concepts" / "fundamental_frequency.yaml").read_text())
        assert not data.get("relationships")


# ── validate ─────────────────────────────────────────────────────────

class TestValidate:
    def test_passes_on_valid(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["validate"])
        assert result.exit_code == 0
        assert "passed" in result.output

    def test_accepts_valid_canonical_claim_reference(self, workspace: Path) -> None:
        concepts_dir = workspace / "knowledge" / "concepts"
        claims_dir = workspace / "knowledge" / "claims"

        _write_concept(concepts_dir, "subglottal_pressure", _make_concept(
            "subglottal_pressure", "concept3", "speech", form="pressure",
        ))
        concept_path = concepts_dir / "fundamental_frequency.yaml"
        concept_data = yaml.safe_load(concept_path.read_text())
        concept_data["parameterization_relationships"] = [{
            "formula": "fundamental_frequency = subglottal_pressure",
            "inputs": ["concept3"],
            "exactness": "approximate",
            "canonical_claim": "claim1",
            "sympy": "concept3",
        }]
        concept_path.write_text(yaml.dump(concept_data, default_flow_style=False, sort_keys=False))
        _write_claim_file(
            claims_dir,
            "paper.yaml",
            {
                "source": {"paper": "paper"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "parameter",
                        "concept": "concept3",
                        "value": 800.0,
                        "unit": "Pa",
                        "provenance": {"paper": "paper", "page": 1},
                    }
                ],
            },
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["validate"])
        assert result.exit_code == 0, result.output
        assert "Validation passed" in result.output

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

    def test_accepts_valid_canonical_claim_reference(self, workspace: Path) -> None:
        concepts_dir = workspace / "knowledge" / "concepts"
        claims_dir = workspace / "knowledge" / "claims"
        sidecar = workspace / "knowledge" / "sidecar" / "propstore.sqlite"

        _write_concept(concepts_dir, "subglottal_pressure", _make_concept(
            "subglottal_pressure", "concept3", "speech", form="pressure",
        ))
        concept_path = concepts_dir / "fundamental_frequency.yaml"
        concept_data = yaml.safe_load(concept_path.read_text())
        concept_data["parameterization_relationships"] = [{
            "formula": "fundamental_frequency = subglottal_pressure",
            "inputs": ["concept3"],
            "exactness": "approximate",
            "canonical_claim": "claim1",
            "sympy": "concept3",
        }]
        concept_path.write_text(yaml.dump(concept_data, default_flow_style=False, sort_keys=False))
        _write_claim_file(
            claims_dir,
            "paper.yaml",
            {
                "source": {"paper": "paper"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "parameter",
                        "concept": "concept3",
                        "value": 800.0,
                        "unit": "Pa",
                        "provenance": {"paper": "paper", "page": 1},
                    }
                ],
            },
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result.exit_code == 0, result.output
        assert sidecar.exists()

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


class TestClaimValidate:
    def test_uses_concepts_dir_override(self, workspace: Path) -> None:
        alt_root = workspace / "alt_knowledge"
        alt_concepts = alt_root / "concepts"
        alt_forms = alt_root / "forms"
        alt_concepts.mkdir(parents=True)
        alt_forms.mkdir()

        _write_concept(alt_concepts, "fundamental_frequency", _make_concept(
            "fundamental_frequency", "concept1", "speech", form="frequency",
        ))
        _write_concept(alt_concepts, "other_task", _make_concept(
            "other_task", "concept9", "speech", form="category",
            form_parameters={"values": ["speech"], "extensible": True},
        ))
        (alt_forms / "frequency.yaml").write_text(
            yaml.dump({"name": "frequency", "dimensionless": False}, default_flow_style=False)
        )
        (alt_forms / "category.yaml").write_text(
            yaml.dump({"name": "category", "dimensionless": True}, default_flow_style=False)
        )

        _write_claim_file(
            workspace / "knowledge" / "claims",
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
                        "conditions": ["other_task == 'speech'"],
                        "provenance": {"paper": "paper", "page": 1},
                    }
                ],
            },
        )

        runner = CliRunner()
        result = runner.invoke(cli, [
            "claim", "validate",
            "--concepts-dir", str(alt_concepts),
        ])
        assert result.exit_code == 0, result.output
        assert "Validation passed" in result.output


class TestQuery:
    def test_query_returns_rows(self, workspace: Path) -> None:
        runner = CliRunner()
        build_result = runner.invoke(cli, ["build"])
        assert build_result.exit_code == 0, build_result.output

        query_result = runner.invoke(cli, ["query", "SELECT count(*) AS n FROM concept"])
        assert query_result.exit_code == 0, query_result.output
        assert "n" in query_result.output
        assert "2" in query_result.output


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
        assert imported["claims"][0]["id"] == "Smith_2024_TestPaper:claim1"

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
        assert imported["claims"][0]["id"] == "Author_2025_Title:claim1"
        assert imported["claims"][1]["id"] == "Author_2025_Title:claim2"


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


# ── Step 3: claim validate-file command ──────────────────────────────


class TestClaimValidateFile:
    def test_reports_errors_on_bad_file(self, workspace):
        """pks claim validate-file on a bad file exits nonzero with errors."""
        claims_dir = workspace / "knowledge" / "claims"
        bad_claim = {
            "source": {"paper": "test_paper"},
            "claims": [{
                "id": "claim1",
                "type": "parameter",
                "concept": "fundamental_frequency",
                "value": 440.0,
                "unit": "Hz",
                "provenance": {"paper": "test_paper"},  # missing page
            }],
        }
        filepath = _write_claim_file(claims_dir, "bad.yaml", bad_claim)

        runner = CliRunner()
        result = runner.invoke(cli, ["claim", "validate-file", str(filepath)])
        assert result.exit_code != 0
        assert "page" in result.output.lower()

    def test_clean_file_exits_zero(self, workspace):
        """pks claim validate-file on a valid file exits zero."""
        claims_dir = workspace / "knowledge" / "claims"
        good_claim = {
            "source": {"paper": "test_paper"},
            "claims": [{
                "id": "claim1",
                "type": "parameter",
                "concept": "fundamental_frequency",
                "value": 440.0,
                "unit": "Hz",
                "provenance": {"paper": "test_paper", "page": 1},
            }],
        }
        filepath = _write_claim_file(claims_dir, "good.yaml", good_claim)

        runner = CliRunner()
        result = runner.invoke(cli, ["claim", "validate-file", str(filepath)])
        assert result.exit_code == 0, f"Unexpected failure: {result.output}"


# ── Step 4: import-papers with source-prefixing ──────────────────────


class TestImportPapersSourcePrefix:
    def _make_papers_dir(self, tmp_path):
        """Create a fake papers/ directory with two papers."""
        papers = tmp_path / "papers"
        paper_a = papers / "PaperA_2020_Foo"
        paper_b = papers / "PaperB_2021_Bar"
        paper_a.mkdir(parents=True)
        paper_b.mkdir(parents=True)

        claim_a = {
            "source": {"paper": "PaperA_2020_Foo"},
            "claims": [{
                "id": "claim1",
                "type": "observation",
                "statement": "A observes X.",
                "concepts": ["fundamental_frequency"],
                "provenance": {"paper": "PaperA_2020_Foo", "page": 1},
            }],
        }
        claim_b = {
            "source": {"paper": "PaperB_2021_Bar"},
            "claims": [{
                "id": "claim1",
                "type": "observation",
                "statement": "B observes Y.",
                "concepts": ["fundamental_frequency"],
                "provenance": {"paper": "PaperB_2021_Bar", "page": 5},
            }],
        }
        (paper_a / "claims.yaml").write_text(
            yaml.dump(claim_a, default_flow_style=False))
        (paper_b / "claims.yaml").write_text(
            yaml.dump(claim_b, default_flow_style=False))
        return papers

    def test_prefixes_claim_ids(self, workspace):
        """Claims imported from PaperA/ get IDs prefixed with 'PaperA_2020_Foo:'."""
        papers = self._make_papers_dir(workspace)
        runner = CliRunner()
        result = runner.invoke(cli, ["import-papers", "--papers-root", str(papers)])
        assert result.exit_code == 0, f"Import failed: {result.output}"

        claims_dir = workspace / "knowledge" / "claims"
        with open(claims_dir / "PaperA_2020_Foo.yaml") as f:
            data = yaml.safe_load(f)
        assert data["claims"][0]["id"] == "PaperA_2020_Foo:claim1"

    def test_no_collisions(self, workspace):
        """Two papers both having claim1 produce distinct prefixed IDs."""
        papers = self._make_papers_dir(workspace)
        runner = CliRunner()
        result = runner.invoke(cli, ["import-papers", "--papers-root", str(papers)])
        assert result.exit_code == 0, f"Import failed: {result.output}"

        claims_dir = workspace / "knowledge" / "claims"
        with open(claims_dir / "PaperA_2020_Foo.yaml") as f:
            data_a = yaml.safe_load(f)
        with open(claims_dir / "PaperB_2021_Bar.yaml") as f:
            data_b = yaml.safe_load(f)

        id_a = data_a["claims"][0]["id"]
        id_b = data_b["claims"][0]["id"]
        assert id_a != id_b
        assert id_a == "PaperA_2020_Foo:claim1"
        assert id_b == "PaperB_2021_Bar:claim1"

    def test_prefixes_inline_stance_targets(self, workspace):
        """Inline stance targets also get prefixed."""
        papers = workspace / "papers"
        paper = papers / "PaperC_2022_Baz"
        paper.mkdir(parents=True)
        claim_data = {
            "source": {"paper": "PaperC_2022_Baz"},
            "claims": [{
                "id": "claim1",
                "type": "observation",
                "statement": "C rebuts A.",
                "concepts": ["fundamental_frequency"],
                "provenance": {"paper": "PaperC_2022_Baz", "page": 2},
                "stances": [{"type": "rebuts", "target": "claim2"}],
            }, {
                "id": "claim2",
                "type": "observation",
                "statement": "C observes Z.",
                "concepts": ["fundamental_frequency"],
                "provenance": {"paper": "PaperC_2022_Baz", "page": 3},
            }],
        }
        (paper / "claims.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False))

        runner = CliRunner()
        result = runner.invoke(cli, ["import-papers", "--papers-root", str(papers)])
        assert result.exit_code == 0, f"Import failed: {result.output}"

        claims_dir = workspace / "knowledge" / "claims"
        with open(claims_dir / "PaperC_2022_Baz.yaml") as f:
            data = yaml.safe_load(f)
        stance = data["claims"][0]["stances"][0]
        assert stance["target"] == "PaperC_2022_Baz:claim2"


class TestConceptCategoryValues:
    def test_add_category_with_values(self, workspace: Path) -> None:
        """pks concept add --form category --values creates valid concept with form_parameters."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "add",
            "--domain", "general",
            "--name", "dataset",
            "--definition", "The benchmark dataset",
            "--form", "category",
            "--values", "ActivityNet,YouCook2,Charades",
        ])
        assert result.exit_code == 0, result.output
        assert "Created" in result.output

        filepath = workspace / "knowledge" / "concepts" / "dataset.yaml"
        data = yaml.safe_load(filepath.read_text())
        assert data["form"] == "category"
        assert data["form_parameters"]["values"] == ["ActivityNet", "YouCook2", "Charades"]

    def test_add_category_without_values_fails(self, workspace: Path) -> None:
        """pks concept add --form category without --values fails before writing file."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "add",
            "--domain", "general",
            "--name", "dataset",
            "--definition", "The benchmark dataset",
            "--form", "category",
        ])
        assert result.exit_code != 0
        assert "values" in result.output.lower()
        assert not (workspace / "knowledge" / "concepts" / "dataset.yaml").exists()
        # Counter must not advance
        assert _read_counter(workspace / "knowledge" / "concepts", "general") == 3

    def test_add_category_values_strips_whitespace(self, workspace: Path) -> None:
        """Whitespace around comma-separated values is stripped."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "add",
            "--domain", "general",
            "--name", "metric",
            "--definition", "Evaluation metric",
            "--form", "category",
            "--values", " CIDEr , METEOR , BLEU ",
        ])
        assert result.exit_code == 0, result.output
        data = yaml.safe_load(
            (workspace / "knowledge" / "concepts" / "metric.yaml").read_text())
        assert data["form_parameters"]["values"] == ["CIDEr", "METEOR", "BLEU"]

    def test_add_non_category_with_values_fails(self, workspace: Path) -> None:
        """--values on a non-category form is an error."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "add",
            "--domain", "speech",
            "--name", "test_freq",
            "--definition", "A frequency",
            "--form", "frequency",
            "--values", "a,b",
        ])
        assert result.exit_code != 0
        assert not (workspace / "knowledge" / "concepts" / "test_freq.yaml").exists()


class TestConceptCategories:
    def test_categories_lists_category_concepts(self, workspace: Path) -> None:
        """pks concept categories lists category concepts with their values."""
        runner = CliRunner()
        result = runner.invoke(cli, ["concept", "categories"])
        assert result.exit_code == 0, result.output
        # workspace fixture has 'task' as a category concept with values ["speech", "singing"]
        assert "task" in result.output
        assert "speech" in result.output
        assert "singing" in result.output
        # fundamental_frequency is form=frequency, must NOT appear
        assert "fundamental_frequency" not in result.output

    def test_categories_shows_extensible_flag(self, workspace: Path) -> None:
        """Extensible categories are marked in output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["concept", "categories"])
        assert result.exit_code == 0, result.output
        # 'task' is extensible: True
        assert "extensible" in result.output

    def test_categories_json_output(self, workspace: Path) -> None:
        """--json produces parseable JSON with correct structure."""
        import json
        runner = CliRunner()
        result = runner.invoke(cli, ["concept", "categories", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "task" in data
        assert data["task"]["values"] == ["speech", "singing"]
        assert data["task"]["extensible"] is True

    def test_categories_empty_when_no_category_concepts(self, tmp_path: Path, monkeypatch) -> None:
        """Returns cleanly when no category concepts exist."""
        monkeypatch.chdir(tmp_path)
        knowledge = tmp_path / "knowledge"
        concepts = knowledge / "concepts"
        concepts.mkdir(parents=True)
        forms = knowledge / "forms"
        forms.mkdir()
        (forms / "structural.yaml").write_text("name: structural\n")

        _write_concept(concepts, "only_struct", _make_concept(
            "only_struct", "concept1", "test", form="structural"))
        _write_counter(concepts, "test", 2)

        runner = CliRunner()
        result = runner.invoke(cli, ["concept", "categories"])
        assert result.exit_code == 0
        # Either says "No category concepts" or outputs nothing
        assert "No category concepts" in result.output or result.output.strip() == ""
