"""Tests for the pks CLI.

Uses Click's CliRunner for isolated testing with temporary directories.
Each test gets a fresh concepts directory with known state.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import click
import pytest
import yaml
from click.testing import CliRunner

from propstore.app.claims import (
    ClaimCompareRequest,
    ClaimComparisonError,
    compare_algorithm_claims,
    show_claim,
)
from propstore.cli import cli
from propstore.fragility import FragilityRequest, query_fragility
from propstore.graph_export import GraphExportRequest, export_knowledge_graph
from propstore.form_utils import show_form
from propstore.repository import Repository
from propstore.sensitivity import SensitivityRequest, query_sensitivity
from propstore.families.identity.claims import compute_claim_version_id
from propstore.families.identity.concepts import derive_concept_artifact_id
from propstore.world import RenderPolicy, ResolutionStrategy, WorldModel
from propstore.world.consistency import (
    WorldConsistencyRequest,
    check_world_consistency,
)
from propstore.world.queries import (
    WorldBindConceptReport,
    WorldBindRequest,
    WorldChainRequest,
    WorldDeriveRequest,
    WorldExplainRequest,
    WorldAlgorithmsRequest,
    WorldHypotheticalRequest,
    WorldResolveRequest,
    derive_world_value,
    diff_hypothetical_world,
    explain_world_claim,
    list_world_algorithms,
    query_world_chain,
    query_bound_world,
    resolve_world_value,
)
from tests.conftest import normalize_claims_payload, normalize_concept_payloads, make_test_context_commit_entry


# ── Fixtures ─────────────────────────────────────────────────────────

def _make_concept(name: str, cid: str, domain: str, status: str = "accepted",
                  form: str = "frequency", **extra: object) -> dict:
    """Build a minimal valid concept dict."""
    data: dict = {
        "canonical_name": name,
        "status": status,
        "definition": f"Test definition for {name}.",
        "domain": domain,
        "created_date": "2026-03-15",
        "form": form,
    }
    data.update(extra)
    return normalize_concept_payloads([{"id": cid, **data}], default_domain=domain)[0]


def _concept_artifact(local_id: str) -> str:
    return derive_concept_artifact_id("propstore", local_id)


def _normalize_claim_concept_refs(data: dict) -> dict:
    normalized = normalize_claims_payload(data)
    for claim in normalized.get("claims", []):
        if not isinstance(claim, dict):
            continue
        concept = claim.get("concept")
        if isinstance(concept, str) and concept.startswith("concept") and ":" not in concept:
            claim["concept"] = _concept_artifact(concept)
        target_concept = claim.get("target_concept")
        if isinstance(target_concept, str) and target_concept.startswith("concept") and ":" not in target_concept:
            claim["target_concept"] = _concept_artifact(target_concept)
        concepts = claim.get("concepts")
        if isinstance(concepts, list):
            claim["concepts"] = [
                _concept_artifact(value) if isinstance(value, str) and value.startswith("concept") and ":" not in value else value
                for value in concepts
            ]
        variables = claim.get("variables")
        if isinstance(variables, list):
            for variable in variables:
                if not isinstance(variable, dict):
                    continue
                value = variable.get("concept")
                if isinstance(value, str) and value.startswith("concept") and ":" not in value:
                    variable["concept"] = _concept_artifact(value)
        parameters = claim.get("parameters")
        if isinstance(parameters, list):
            for parameter in parameters:
                if not isinstance(parameter, dict):
                    continue
                value = parameter.get("concept")
                if isinstance(value, str) and value.startswith("concept") and ":" not in value:
                    parameter["concept"] = _concept_artifact(value)
        claim["version_id"] = compute_claim_version_id(claim)
    return normalized


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


def _commit_workspace_paths(workspace: Path, relpaths: list[str], message: str = "Sync test changes") -> None:
    repo = Repository.find(workspace / "knowledge")
    adds = {
        relpath: (workspace / "knowledge" / Path(relpath)).read_bytes()
        for relpath in relpaths
    }
    repo.git.commit_files(adds, message)
    repo.git.sync_worktree()


class TestRootCli:
    def test_nested_help_literal_does_not_bypass_repo_attachment(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import propstore.cli.history_cmds as history_cmds

        calls: list[str] = []

        def fake_build_commit_show_report(repo, commit: str):
            calls.append(commit)
            return SimpleNamespace(
                sha="abcdef1234567890",
                author="Test Author",
                time="2026-04-20T00:00:00Z",
                message="literal help commit",
                changes=SimpleNamespace(added=(), modified=(), deleted=()),
            )

        monkeypatch.setattr("sys.argv", ["pks", "show", "--", "--help"])
        monkeypatch.setattr(
            history_cmds,
            "build_commit_show_report",
            fake_build_commit_show_report,
        )

        result = CliRunner().invoke(cli, ["show", "--", "--help"])

        assert result.exit_code == 0, result.output
        assert calls == ["--help"]



@pytest.fixture()
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up a temporary workspace with knowledge/ containing concepts, forms, etc."""
    monkeypatch.chdir(tmp_path)

    knowledge = tmp_path / "knowledge"
    repo = Repository.init(knowledge)

    # Create form definition files
    forms_dir = knowledge / "forms"
    _dimensionless_forms = {"duration_ratio", "amplitude_ratio", "level", "dimensionless_compound"}
    adds: dict[str, bytes] = {}
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
        adds[f"forms/{form_name}.yaml"] = yaml.dump(form_data, default_flow_style=False).encode("utf-8")

    # Write two concepts
    adds["concepts/fundamental_frequency.yaml"] = yaml.dump(
        _make_concept(
            "fundamental_frequency", "concept1", "speech",
            form="frequency",
            range=[50, 1000],
            aliases=[{"name": "F0", "source": "common"}],
        ),
        default_flow_style=False,
        sort_keys=False,
    ).encode("utf-8")
    adds["concepts/task.yaml"] = yaml.dump(
        _make_concept(
            "task", "concept2", "speech",
            form="category",
            form_parameters={"values": ["speech", "singing"], "extensible": True},
        ),
        default_flow_style=False,
        sort_keys=False,
    ).encode("utf-8")
    adds["concepts/.counters/global.next"] = b"3\n"
    context_path, context_body = make_test_context_commit_entry()
    adds[context_path] = context_body
    repo.git.commit_files(adds, "Seed test workspace")
    repo.git.sync_worktree()

    # Copy schema if it exists (for JSON Schema validation)
    schema_src = Path(__file__).parent.parent / "schema" / "generated" / "concept_registry.schema.json"
    if schema_src.exists():
        schema_dir = tmp_path / "schema" / "generated"
        schema_dir.mkdir(parents=True)
        (schema_dir / "concept_registry.schema.json").write_text(schema_src.read_text())

    return tmp_path


@pytest.fixture()
def freq_workspace(workspace: Path) -> Path:
    """Workspace with a frequency concept, a kHz claim, and a built sidecar."""
    # Overwrite the minimal frequency form with a full definition including SI unit
    forms_dir = workspace / "knowledge" / "forms"
    freq_form = {
        "name": "frequency",
        "dimensionless": False,
        "unit_symbol": "Hz",
        "common_alternatives": [
            {"unit": "kHz", "type": "multiplicative", "multiplier": 1000},
            {"unit": "MHz", "type": "multiplicative", "multiplier": 1000000},
        ],
    }
    (forms_dir / "frequency.yaml").write_text(
        yaml.dump(freq_form, default_flow_style=False))

    claims_dir = workspace / "knowledge" / "claims"
    _write_claim_file(claims_dir, "freq_paper.yaml", {
        "source": {"paper": "freq_paper"},
        "claims": [
            {
                "id": "freq_claim1",
                "type": "parameter",
                "concept": "concept1",
                "value": 0.2,
                "unit": "kHz",
                "provenance": {"paper": "freq_paper", "page": 1},
            }
        ],
    })
    normalized_freq_claims = _normalize_claim_concept_refs(yaml.safe_load((claims_dir / "freq_paper.yaml").read_text()))
    (claims_dir / "freq_paper.yaml").write_text(yaml.dump(normalized_freq_claims, default_flow_style=False, sort_keys=False))
    _commit_workspace_paths(
        workspace,
        ["forms/frequency.yaml", "claims/freq_paper.yaml"],
        "Seed committed frequency workspace",
    )

    runner = CliRunner()
    sidecar = workspace / "knowledge" / "sidecar" / "propstore.sqlite"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    result = runner.invoke(cli, ["build", "-o", str(sidecar)])
    assert result.exit_code == 0, f"Build failed: {result.output}"
    return workspace


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
        assert data["artifact_id"] == _concept_artifact("concept3")
        assert data["lexical_entry"]["canonical_form"]["written_rep"] == "test_pressure"
        assert data["status"] == "proposed"
        assert data["lexical_entry"]["physical_dimension_form"] == "pressure"
        assert data["logical_ids"][0] == {"namespace": "speech", "value": "test_pressure"}
        assert {"namespace": "propstore", "value": "concept3"} in data["logical_ids"]
        assert data["version_id"].startswith("sha256:")

    def test_created_concept_can_be_shown_by_logical_id(self, workspace: Path) -> None:
        runner = CliRunner()
        add_result = runner.invoke(cli, [
            "concept", "add",
            "--domain", "speech",
            "--name", "test_pressure",
            "--definition", "A test concept",
            "--form", "pressure",
        ])
        assert add_result.exit_code == 0, add_result.output

        show_result = runner.invoke(cli, ["concept", "show", "speech:test_pressure"])
        assert show_result.exit_code == 0, show_result.output
        assert "written_rep: test_pressure" in show_result.output
        assert f"artifact_id: {_concept_artifact('concept3')}" in show_result.output

    def test_increments_counter(self, workspace: Path) -> None:
        runner = CliRunner()
        runner.invoke(cli, [
            "concept", "add",
            "--domain", "speech", "--name", "c1",
            "--definition", "d1", "--form", "boolean",
        ])
        c1_data = yaml.safe_load((workspace / "knowledge" / "concepts" / "c1.yaml").read_text())
        assert c1_data["artifact_id"] == _concept_artifact("concept3")

        runner.invoke(cli, [
            "concept", "add",
            "--domain", "speech", "--name", "c2",
            "--definition", "d2", "--form", "boolean",
        ])
        c2_data = yaml.safe_load((workspace / "knowledge" / "concepts" / "c2.yaml").read_text())
        assert c2_data["artifact_id"] == _concept_artifact("concept4")

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
            "concept", "alias", "speech:fundamental_frequency",
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
            "concept", "alias", "speech:fundamental_frequency",
            "--name", "task", "--source", "test",
        ])
        assert result.exit_code == 0
        assert "WARNING" in result.output


# ── concept rename ───────────────────────────────────────────────────

class TestConceptRename:
    def test_renames_file_and_field(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "rename", "speech:task",
            "--name", "vocal_task",
        ])
        assert result.exit_code == 0, result.output
        assert "task -> vocal_task" in result.output

        old_path = workspace / "knowledge" / "concepts" / "task.yaml"
        new_path = workspace / "knowledge" / "concepts" / "vocal_task.yaml"
        assert not old_path.exists()
        assert new_path.exists()

        data = yaml.safe_load(new_path.read_text())
        assert data["lexical_entry"]["canonical_form"]["written_rep"] == "vocal_task"
        assert data["artifact_id"] == _concept_artifact("concept2")
        assert data["logical_ids"][0] == {"namespace": "speech", "value": "vocal_task"}
        assert {"namespace": "propstore", "value": "concept2"} in data["logical_ids"]

    def test_updates_cel_references_in_concepts_and_claims(self, workspace: Path) -> None:
        concept_path = workspace / "knowledge" / "concepts" / "fundamental_frequency.yaml"
        concept_data = yaml.safe_load(concept_path.read_text())
        concept_data["relationships"] = [
            {"type": "related", "target": _concept_artifact("concept2"), "conditions": ["task == 'speech'"]}
        ]
        concept_path.write_text(yaml.dump(concept_data, default_flow_style=False, sort_keys=False))
        _commit_workspace_paths(workspace, ["concepts/fundamental_frequency.yaml"], "Seed concept relationship edit")

        claims_dir = workspace / "knowledge" / "claims"
        _write_claim_file(
            claims_dir,
            "paper.yaml",
            _normalize_claim_concept_refs({
                "source": {"paper": "paper"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "parameter",
                        "concept": _concept_artifact("concept1"),
                        "value": 200.0,
                        "unit": "Hz",
                        "conditions": ["task == 'speech'"],
                        "provenance": {"paper": "paper", "page": 1},
                    }
                ],
            }),
        )
        _commit_workspace_paths(workspace, ["claims/paper.yaml"], "Seed claim conditions edit")

        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "rename", "speech:task",
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
            "concept", "deprecate", "speech:task",
            "--replaced-by", "speech:fundamental_frequency",
        ])
        assert result.exit_code == 0, result.output
        assert "Deprecated" in result.output

        data = yaml.safe_load(
            (workspace / "knowledge" / "concepts" / "task.yaml").read_text())
        assert data["status"] == "deprecated"
        assert data["replaced_by"] == _concept_artifact("concept1")

    def test_rejects_nonexistent_replacement(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "deprecate", "speech:task",
            "--replaced-by", "speech:missing_concept",
        ])
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_rejects_deprecated_replacement(self, workspace: Path) -> None:
        # First deprecate concept2
        data = yaml.safe_load(
            (workspace / "knowledge" / "concepts" / "task.yaml").read_text())
        data["status"] = "deprecated"
        data["replaced_by"] = _concept_artifact("concept1")
        with open(workspace / "knowledge" / "concepts" / "task.yaml", "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        _commit_workspace_paths(workspace, ["concepts/task.yaml"], "Seed deprecated replacement")

        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "deprecate", "speech:fundamental_frequency",
            "--replaced-by", "speech:task",
        ])
        assert result.exit_code != 0
        assert "deprecated" in result.output


# ── concept link ─────────────────────────────────────────────────────

class TestConceptLink:
    def test_adds_relationship(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "link", "speech:fundamental_frequency", "broader", "speech:task",
        ])
        assert result.exit_code == 0, result.output
        assert "Added broader" in result.output

        data = yaml.safe_load(
            (workspace / "knowledge" / "concepts" / "fundamental_frequency.yaml").read_text())
        rels = data.get("relationships", [])
        assert any(r["type"] == "broader" and r["target"] == _concept_artifact("concept2") for r in rels)

    def test_rejects_invalid_relationship_without_writing(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "link", "speech:fundamental_frequency", "contested_definition", "speech:task",
        ])
        assert result.exit_code != 0
        assert "Validation failed" in result.output

        data = yaml.safe_load(
            (workspace / "knowledge" / "concepts" / "fundamental_frequency.yaml").read_text())
        assert not data.get("relationships")


def _provenance_cli_options() -> list[str]:
    return [
        "--asserter", "tests",
        "--timestamp", "2026-04-17T00:00:00Z",
        "--source-artifact-code", "ps:test:concept-cli",
        "--method", "unit-test",
    ]


class TestConceptPhase3Semantics:
    def test_qualia_add_persists_typed_reference(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "qualia-add",
            "speech:fundamental_frequency",
            "telic",
            "speech:task",
            "--type-constraint", "speech:task",
            *_provenance_cli_options(),
        ])

        assert result.exit_code == 0, result.output
        data = yaml.safe_load(
            (workspace / "knowledge" / "concepts" / "fundamental_frequency.yaml").read_text()
        )
        telic = data["lexical_entry"]["senses"][0]["qualia"]["telic"][0]
        assert telic["reference"]["uri"] == _concept_artifact("concept2")
        assert telic["type_constraint"]["reference"]["uri"] == _concept_artifact("concept2")
        assert telic["provenance"]["status"] == "stated"
        assert telic["provenance"]["witnesses"][0]["method"] == "unit-test"

    def test_description_kind_adds_typed_slot(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "description-kind",
            "speech:task",
            "--name", "TaskDescription",
            "--reference", "speech:task",
            "--slot", "observer=speech:fundamental_frequency",
        ])

        assert result.exit_code == 0, result.output
        data = yaml.safe_load((workspace / "knowledge" / "concepts" / "task.yaml").read_text())
        description_kind = data["lexical_entry"]["senses"][0]["description_kind"]
        assert description_kind["name"] == "TaskDescription"
        assert description_kind["reference"]["uri"] == _concept_artifact("concept2")
        assert description_kind["slots"][0]["name"] == "observer"
        assert description_kind["slots"][0]["type_constraint"]["uri"] == _concept_artifact("concept1")

    def test_proto_role_adds_entailment_to_role_and_description_slot(self, workspace: Path) -> None:
        runner = CliRunner()
        kind_result = runner.invoke(cli, [
            "concept", "description-kind",
            "speech:task",
            "--name", "TaskDescription",
            "--reference", "speech:task",
            "--slot", "observer=speech:fundamental_frequency",
        ])
        assert kind_result.exit_code == 0, kind_result.output

        result = runner.invoke(cli, [
            "concept", "proto-role",
            "speech:task",
            "observer",
            "agent",
            "sentience",
            "0.75",
            *_provenance_cli_options(),
        ])

        assert result.exit_code == 0, result.output
        data = yaml.safe_load((workspace / "knowledge" / "concepts" / "task.yaml").read_text())
        bundle = data["lexical_entry"]["senses"][0]["role_bundles"]["observer"]
        entailment = bundle["proto_agent_entailments"][0]
        assert entailment["property"] == "sentience"
        assert entailment["value"] == 0.75
        slot_bundle = data["lexical_entry"]["senses"][0]["description_kind"]["slots"][0][
            "proto_role_bundle"
        ]
        assert slot_bundle["proto_agent_entailments"][0]["property"] == "sentience"


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
        _commit_workspace_paths(workspace, ["concepts/broken.yaml"], "Seed invalid concept for validate")
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

    def test_build_records_validation_failure_diagnostics(self, workspace: Path) -> None:
        bad = workspace / "knowledge" / "concepts" / "broken.yaml"
        bad.write_text(yaml.dump({
            "id": "concept1",  # duplicate
            "canonical_name": "broken",
            "status": "accepted",
            "definition": "dup",
            "form": "frequency",
        }))
        _commit_workspace_paths(workspace, ["concepts/broken.yaml"], "Seed invalid duplicate concept")
        runner = CliRunner()
        sidecar = workspace / "knowledge" / "sidecar" / "propstore.sqlite"
        result = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result.exit_code == 0, result.output
        assert sidecar.exists()
        conn = sqlite3.connect(sidecar)
        try:
            diagnostic_rows = conn.execute(
                """
                SELECT source_kind, source_ref, diagnostic_kind, severity, blocking, message
                FROM build_diagnostics
                WHERE diagnostic_kind = 'concept_validation'
                """
            ).fetchall()
        finally:
            conn.close()
        assert diagnostic_rows
        assert diagnostic_rows[0][:5] == (
            "concept",
            "broken",
            "concept_validation",
            "error",
            1,
        )
        assert "Object contains unknown field `canonical_name`" in diagnostic_rows[0][5]


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
            _normalize_claim_concept_refs({
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
            }),
        )
        _commit_workspace_paths(workspace, ["claims/paper.yaml"], "Seed committed claim validate override file")

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


class TestSourceCutover:
    def test_import_papers_command_removed(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["import-papers"])
        assert result.exit_code != 0
        assert "No such command 'import-papers'" in result.output


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
        assert _concept_artifact("concept1") in ids
        assert _concept_artifact("concept2") in ids
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
        _write_claim_file(claims_dir, "paper.yaml", _normalize_claim_concept_refs({
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
        }))
        _commit_workspace_paths(workspace, ["claims/paper.yaml"], "Seed committed claim file")

        runner = CliRunner()
        sidecar = workspace / "knowledge" / "sidecar" / "propstore.sqlite"
        result = runner.invoke(cli, ["build", "-o", str(sidecar)])
        assert result.exit_code == 0, result.output

        conn = sqlite3.connect(sidecar)
        count = conn.execute("SELECT count(*) FROM claim_core").fetchone()[0]
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
        assert data["F0"]["logical_id"] == "speech:fundamental_frequency"
        assert data["F0"]["name"] == "fundamental_frequency"

    def test_export_aliases_text(self, workspace: Path) -> None:
        """export-aliases in text mode should show alias -> concept mappings."""
        runner = CliRunner()
        result = runner.invoke(cli, ["export-aliases"])
        assert result.exit_code == 0, result.output
        assert "F0" in result.output
        assert "speech:fundamental_frequency" in result.output


# ── concept search ──────────────────────────────────────────────────

class TestConceptList:
    def test_list_shows_logical_ids_not_artifact_ids(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["concept", "list"])
        assert result.exit_code == 0, result.output
        assert "speech:fundamental_frequency" in result.output
        assert _concept_artifact("concept1") not in result.output


class TestConceptSearch:
    def test_search_requires_sidecar(self, workspace: Path) -> None:
        """concept search should require a built sidecar."""
        runner = CliRunner()
        result = runner.invoke(cli, ["concept", "search", "fundamental"])
        assert result.exit_code != 0
        assert "requires a built sidecar" in result.output

    def test_search_no_matches(self, workspace: Path) -> None:
        """concept search with no matches should report no matches."""
        runner = CliRunner()
        build_result = runner.invoke(cli, ["build"])
        assert build_result.exit_code == 0, build_result.output

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
        assert "speech:fundamental_frequency" in result.output
        assert "fundamental_frequency" in result.output

    def test_search_by_definition_with_fts(self, workspace: Path) -> None:
        """concept search should find concepts by definition text via FTS."""
        runner = CliRunner()
        build_result = runner.invoke(cli, ["build"])
        assert build_result.exit_code == 0, build_result.output

        result = runner.invoke(cli, ["concept", "search", "definition"])
        assert result.exit_code == 0, result.output
        assert "speech:fundamental_frequency" in result.output


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
        filepath = _write_claim_file(claims_dir, "bad.yaml", _normalize_claim_concept_refs(bad_claim))

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
        filepath = _write_claim_file(claims_dir, "good.yaml", _normalize_claim_concept_refs(good_claim))

        runner = CliRunner()
        result = runner.invoke(cli, ["claim", "validate-file", str(filepath)])
        assert result.exit_code == 0, f"Unexpected failure: {result.output}"


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
        assert data["lexical_entry"]["physical_dimension_form"] == "category"
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

    def test_add_category_closed_sets_extensible_false(self, workspace: Path) -> None:
        """pks concept add --form category --closed writes extensible: false in form_parameters."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "add",
            "--domain", "general",
            "--name", "closed_cat",
            "--definition", "A closed category",
            "--form", "category",
            "--values", "a,b,c",
            "--closed",
        ])
        assert result.exit_code == 0, result.output
        filepath = workspace / "knowledge" / "concepts" / "closed_cat.yaml"
        data = yaml.safe_load(filepath.read_text())
        assert data["lexical_entry"]["physical_dimension_form"] == "category"
        assert data["form_parameters"]["values"] == ["a", "b", "c"]
        assert data["form_parameters"]["extensible"] is False

    def test_add_category_without_closed_omits_extensible(self, workspace: Path) -> None:
        """Without --closed, extensible key is not written (defaults to true at read time)."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "add",
            "--domain", "general",
            "--name", "open_cat",
            "--definition", "An open category",
            "--form", "category",
            "--values", "x,y",
        ])
        assert result.exit_code == 0, result.output
        filepath = workspace / "knowledge" / "concepts" / "open_cat.yaml"
        data = yaml.safe_load(filepath.read_text())
        assert "extensible" not in data.get("form_parameters", {})

    def test_closed_on_non_category_fails(self, workspace: Path) -> None:
        """--closed on a non-category form is an error."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "add",
            "--domain", "speech",
            "--name", "test_freq2",
            "--definition", "A frequency",
            "--form", "frequency",
            "--closed",
        ])
        assert result.exit_code != 0
        assert "closed" in result.output.lower() or "category" in result.output.lower()


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
        repo = Repository.init(knowledge)
        concepts = knowledge / "concepts"
        forms = knowledge / "forms"
        (forms / "structural.yaml").write_text("name: structural\n")

        _write_concept(concepts, "only_struct", _make_concept(
            "only_struct", "concept1", "test", form="structural"))
        _write_counter(concepts, "test", 2)
        repo.git.commit_files(
            {
                "forms/structural.yaml": (forms / "structural.yaml").read_bytes(),
                "concepts/only_struct.yaml": (concepts / "only_struct.yaml").read_bytes(),
                "concepts/.counters/global.next": (concepts / ".counters" / "global.next").read_bytes(),
            },
            "Seed non-category-only workspace",
        )
        repo.git.sync_worktree()

        runner = CliRunner()
        result = runner.invoke(cli, ["concept", "categories"])
        assert result.exit_code == 0
        # Either says "No category concepts" or outputs nothing
        assert "No category concepts" in result.output or result.output.strip() == ""


# ── concept add-value ────────────────────────────────────────────────

class TestConceptAddValue:
    def test_add_value_appends_to_category(self, workspace: Path) -> None:
        """pks concept add-value appends a new value to the category's values list."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "add-value", "task", "--value", "reading",
        ])
        assert result.exit_code == 0, result.output

        data = yaml.safe_load(
            (workspace / "knowledge" / "concepts" / "task.yaml").read_text())
        assert "reading" in data["form_parameters"]["values"]
        # Original values preserved
        assert "speech" in data["form_parameters"]["values"]
        assert "singing" in data["form_parameters"]["values"]

    def test_add_value_rejects_duplicate(self, workspace: Path) -> None:
        """Adding an already-present value is rejected."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "add-value", "task", "--value", "speech",
        ])
        assert result.exit_code != 0
        assert "already" in result.output.lower()

    def test_add_value_to_non_category_fails(self, workspace: Path) -> None:
        """add-value on a non-category concept fails."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "add-value", "fundamental_frequency", "--value", "nope",
        ])
        assert result.exit_code != 0
        assert "category" in result.output.lower()

    def test_add_value_to_non_extensible_fails(self, workspace: Path) -> None:
        """add-value on a non-extensible category fails."""
        # Create a non-extensible category concept
        _write_concept(
            workspace / "knowledge" / "concepts", "fixed_cat",
            _make_concept("fixed_cat", "concept99", "test", form="category",
                          form_parameters={"values": ["a", "b"], "extensible": False}))
        _commit_workspace_paths(workspace, ["concepts/fixed_cat.yaml"], "Seed non-extensible category")

        runner = CliRunner()
        result = runner.invoke(cli, [
            "concept", "add-value", "fixed_cat", "--value", "c",
        ])
        assert result.exit_code != 0
        assert "extensible" in result.output.lower()


# ── query (SQL injection protection) ────────────────────────────────

class TestQueryReadOnly:
    """Verify that `pks query` enforces read-only mode on the sidecar."""

    @pytest.fixture()
    def built_workspace(self, workspace: Path) -> Path:
        """Build a sidecar so `pks query` has something to query."""
        runner = CliRunner()
        sidecar_dir = workspace / "knowledge" / "sidecar"
        sidecar_dir.mkdir(parents=True, exist_ok=True)
        result = runner.invoke(cli, ["build", "-o", str(sidecar_dir / "propstore.sqlite")])
        assert result.exit_code == 0, result.output
        return workspace

    def test_select_works(self, built_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["query", "SELECT count(*) FROM concept"])
        assert result.exit_code == 0, result.output

    def test_drop_table_rejected(self, built_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["query", "DROP TABLE IF EXISTS concept"])
        assert result.exit_code != 0

    def test_insert_rejected(self, built_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "query",
            "INSERT INTO concept (id, canonical_name, status, definition, domain, form) "
            "VALUES ('evil', 'evil', 'accepted', 'evil', 'evil', 'evil')",
        ])
        assert result.exit_code != 0

    def test_update_rejected(self, built_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "query",
            "UPDATE concept SET canonical_name='hacked' WHERE 1=1",
        ])
        assert result.exit_code != 0

    def test_delete_rejected(self, built_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "query",
            "DELETE FROM concept WHERE 1=1",
        ])
        assert result.exit_code != 0


# ── Resource leak tests ──────────────────────────────────────────────

class TestConnectionClosedOnError:
    """Verify sqlite3 connections are closed even when CLI commands raise."""

    @staticmethod
    def _make_repo_with_sidecar(tmp_path: Path) -> Path:
        """Create minimal repo structure with a sidecar file."""
        knowledge = tmp_path / "knowledge"
        Repository.init(knowledge)
        sidecar_dir = knowledge / "sidecar"
        sidecar = sidecar_dir / "propstore.sqlite"
        sidecar.touch()
        return tmp_path

    def test_claim_embed_closes_conn_on_error(self, tmp_path: Path) -> None:
        """claim embed must close its sqlite3 connection if embed_claims raises."""
        from unittest.mock import patch, MagicMock

        self._make_repo_with_sidecar(tmp_path)

        mock_conn = MagicMock()
        mock_conn.row_factory = None

        with (
            patch("sqlite3.connect", return_value=mock_conn),
            patch("propstore.embed._load_vec_extension"),
            patch("propstore.embed.embed_claims", side_effect=RuntimeError("boom")),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, [
                "-C", str(tmp_path),
                "claim", "embed", "--model", "test-model", "--all",
            ])

        # The command should have failed (non-zero or exception output)
        assert result.exit_code != 0 or "boom" in (result.output or "")
        # The connection MUST have been closed despite the error
        mock_conn.close.assert_called()

    def test_claim_embed_all_progress_reports_final_partial_batch(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """claim embed --model all reports final partial progress on its own line."""
        from propstore.app.claims import ClaimEmbedModelReport, ClaimEmbedReport
        import propstore.cli.claim as claim_cli

        self._make_repo_with_sidecar(tmp_path)

        def fake_embed_claim_embeddings(repo, request, *, on_progress=None):
            assert request.model == "all"
            assert request.batch_size == 64
            assert on_progress is not None
            for done in (64, 128, 130):
                on_progress("model-a", done, 130)
            return ClaimEmbedReport(
                results=(
                    ClaimEmbedModelReport(
                        model_name="model-a",
                        embedded=130,
                        skipped=0,
                        errors=0,
                    ),
                ),
            )

        monkeypatch.setattr(
            claim_cli,
            "embed_claim_embeddings",
            fake_embed_claim_embeddings,
        )

        result = CliRunner().invoke(
            cli,
            [
                "-C",
                str(tmp_path),
                "claim",
                "embed",
                "--all",
                "--model",
                "all",
                "--batch-size",
                "64",
            ],
        )

        assert result.exit_code == 0
        assert "  130/130\nEmbedding with model-a..." in result.output


class TestClaimRelateCli:
    def test_claim_relate_rejects_all_with_claim_id(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import propstore.cli.claim as claim_cli

        owner_called = False

        def fake_relate_claims(*args, **kwargs):
            nonlocal owner_called
            owner_called = True
            from propstore.app.claims import ClaimRelateReport

            return ClaimRelateReport(branch="stance-proposals")

        monkeypatch.setattr(claim_cli, "relate_claims", fake_relate_claims)

        result = CliRunner().invoke(
            cli,
            [
                "-C",
                str(tmp_path),
                "claim",
                "relate",
                "claim-a",
                "--all",
                "--model",
                "model-a",
            ],
        )

        assert result.exit_code == 2
        assert "--all cannot be used with a claim ID" in result.output
        assert owner_called is False


# ── claim show ──────────────────────────────────────────────────────

class TestClaimShow:
    def test_owner_show_claim_reports_si_value(
        self,
        freq_workspace: Path,
    ) -> None:
        repo = Repository.find(freq_workspace)
        with WorldModel(repo) as wm:
            report = show_claim(wm, "freq_paper:freq_claim1")

        assert report.logical_id == "freq_paper:freq_claim1"
        assert report.value == 0.2
        assert report.value_si == 200
        assert report.unit == "kHz"

    def test_owner_compare_rejects_non_algorithm_claims(
        self,
        freq_workspace: Path,
    ) -> None:
        repo = Repository.find(freq_workspace)
        with WorldModel(repo) as wm:
            with pytest.raises(ClaimComparisonError):
                compare_algorithm_claims(
                    wm,
                    ClaimCompareRequest(
                        "freq_paper:freq_claim1",
                        "freq_paper:freq_claim1",
                    ),
                )

    def test_claim_show_exists(self, freq_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["claim", "show", "freq_paper:freq_claim1"])
        assert result.exit_code == 0, result.output
        assert "Logical ID: freq_paper:freq_claim1" in result.output

    def test_claim_show_displays_si_values(self, freq_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["claim", "show", "freq_paper:freq_claim1"])
        assert result.exit_code == 0, result.output
        assert "0.2" in result.output
        assert "200" in result.output
        assert "kHz" in result.output

    def test_claim_show_not_found(self, freq_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["claim", "show", "nonexistent_claim"])
        assert result.exit_code != 0 or "not found" in result.output.lower()


# ── world owner reports ─────────────────────────────────────────────

class TestWorldOwnerReports:
    def test_owner_explain_reports_claim_without_stances(
        self,
        freq_workspace: Path,
    ) -> None:
        repo = Repository.find(freq_workspace)
        with WorldModel(repo) as wm:
            report = explain_world_claim(
                wm,
                WorldExplainRequest(claim_id="freq_paper:freq_claim1"),
            )

        assert report.claim_display_id == "freq_paper:freq_claim1"
        assert report.concept_display_id == "speech:fundamental_frequency"
        assert report.stances == ()

    def test_owner_algorithms_report_empty_when_none(
        self,
        freq_workspace: Path,
    ) -> None:
        repo = Repository.find(freq_workspace)
        with WorldModel(repo) as wm:
            report = list_world_algorithms(wm, WorldAlgorithmsRequest())

        assert report.algorithms == ()

    def test_world_explain_cli_reports_claim_without_stances(
        self,
        freq_workspace: Path,
    ) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["world", "explain", "freq_paper:freq_claim1"])

        assert result.exit_code == 0, result.output
        assert "freq_paper:freq_claim1:" in result.output
        assert "concept=speech:fundamental_frequency" in result.output
        assert "  (no stances)" in result.output

    def test_world_algorithms_cli_reports_empty_inventory(
        self,
        freq_workspace: Path,
    ) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["world", "algorithms"])

        assert result.exit_code == 0, result.output
        assert "No algorithm claims found." in result.output

    def test_owner_derive_reports_value_status(
        self,
        freq_workspace: Path,
    ) -> None:
        repo = Repository.find(freq_workspace)
        with WorldModel(repo) as wm:
            expected_concept_id = wm.resolve_concept("speech:fundamental_frequency")
            report = derive_world_value(
                wm,
                WorldDeriveRequest(
                    concept_id="speech:fundamental_frequency",
                    bindings={},
                    policy=RenderPolicy(),
                ),
            )

        assert report.concept_id == expected_concept_id
        assert str(report.status) == "no_relationship"

    def test_owner_hypothetical_reports_removed_claim_change(
        self,
        freq_workspace: Path,
    ) -> None:
        repo = Repository.find(freq_workspace)
        with WorldModel(repo) as wm:
            report = diff_hypothetical_world(
                wm,
                WorldHypotheticalRequest(
                    bindings={},
                    remove_claim_ids=("freq_paper:freq_claim1",),
                ),
            )

        assert len(report.changes) == 1
        change = report.changes[0]
        assert change.concept_display_id == "speech:fundamental_frequency"
        assert str(change.base_status) == "determined"
        assert str(change.hypothetical_status) == "no_claims"

    def test_owner_resolve_reports_winner_display_id(
        self,
        freq_workspace: Path,
    ) -> None:
        repo = Repository.find(freq_workspace)
        with WorldModel(repo) as wm:
            report = resolve_world_value(
                wm,
                WorldResolveRequest(
                    concept_id="speech:fundamental_frequency",
                    bindings={},
                    policy=RenderPolicy(strategy=ResolutionStrategy.RECENCY),
                ),
            )

        assert report.concept_display_id == "speech:fundamental_frequency"
        assert str(report.status) == "determined"
        assert report.value == 0.2
        assert report.winning_claim_display_id is None

    def test_owner_chain_reports_direct_claim_step(
        self,
        freq_workspace: Path,
    ) -> None:
        repo = Repository.find(freq_workspace)
        with WorldModel(repo) as wm:
            report = query_world_chain(
                wm,
                WorldChainRequest(
                    concept_id="speech:fundamental_frequency",
                    bindings={},
                ),
            )

        assert report.target.display_id == "speech:fundamental_frequency"
        assert report.target.canonical_name == "fundamental_frequency"
        assert str(report.status) == "determined"
        assert len(report.steps) == 1
        step = report.steps[0]
        assert step.concept.display_id == "speech:fundamental_frequency"
        assert step.value == 0.2
        assert step.source == "claim"

    def test_owner_graph_export_returns_graph_report(
        self,
        freq_workspace: Path,
    ) -> None:
        repo = Repository.find(freq_workspace)
        with WorldModel(repo) as wm:
            report = export_knowledge_graph(
                wm,
                GraphExportRequest(bindings={}),
            )

        assert report.graph.nodes
        assert report.graph.edges
        assert "nodes" in report.graph.to_json()
        assert "edges" in report.graph.to_json()

    def test_owner_consistency_reports_no_bound_conflicts(
        self,
        freq_workspace: Path,
    ) -> None:
        repo = Repository.find(freq_workspace)
        with WorldModel(repo) as wm:
            report = check_world_consistency(
                repo,
                wm,
                WorldConsistencyRequest(bindings={}),
            )

        assert report.transitive is False
        assert report.conflicts == ()

    def test_owner_consistency_reports_no_transitive_conflicts(
        self,
        freq_workspace: Path,
    ) -> None:
        repo = Repository.find(freq_workspace)
        with WorldModel(repo) as wm:
            report = check_world_consistency(
                repo,
                wm,
                WorldConsistencyRequest(bindings={}, transitive=True),
            )

        assert report.transitive is True
        assert report.conflicts == ()

    def test_owner_sensitivity_reports_unavailable_analysis(
        self,
        freq_workspace: Path,
    ) -> None:
        repo = Repository.find(freq_workspace)
        with WorldModel(repo) as wm:
            expected_concept_id = wm.resolve_concept("speech:fundamental_frequency")
            report = query_sensitivity(
                wm,
                SensitivityRequest(
                    concept_id="speech:fundamental_frequency",
                    bindings={},
                ),
            )

        assert report.concept_id == expected_concept_id
        assert report.result is None

    def test_owner_fragility_reports_empty_when_all_families_skipped(
        self,
        freq_workspace: Path,
    ) -> None:
        repo = Repository.find(freq_workspace)
        with WorldModel(repo) as wm:
            report = query_fragility(
                wm,
                FragilityRequest(
                    bindings={},
                    include_atms=False,
                    include_discovery=False,
                    include_conflict=False,
                    include_grounding=False,
                    include_bridge=False,
                ),
            )

        assert report.world_fragility == 0.0
        assert report.analysis_scope == "all"
        assert report.interventions == ()


# ── world query/bind SI values ──────────────────────────────────────

class TestWorldQuerySIValues:
    def test_world_query_shows_si_value(self, freq_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["world", "query", "speech:fundamental_frequency"])
        assert result.exit_code == 0, result.output
        assert "0.2" in result.output
        assert "kHz" in result.output
        assert "200" in result.output

    def test_world_query_accepts_canonical_name(self, freq_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["world", "query", "fundamental_frequency"])
        assert result.exit_code == 0, result.output
        assert "fundamental_frequency (speech:fundamental_frequency)" in result.output

    def test_owner_world_bind_report_shows_si_value(self, freq_workspace: Path) -> None:
        repo = Repository.find(freq_workspace)
        with WorldModel(repo) as wm:
            report = query_bound_world(
                wm,
                WorldBindRequest(bindings={}, target="speech:fundamental_frequency"),
            )

        assert isinstance(report, WorldBindConceptReport)
        assert report.concept_display_id == "speech:fundamental_frequency"
        assert report.status == "determined"
        assert report.claims
        assert "0.2" in report.claims[0].value_display
        assert "200" in report.claims[0].value_display

    def test_world_bind_shows_si_value(self, freq_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["world", "bind", "speech:fundamental_frequency"])
        assert result.exit_code == 0, result.output
        assert "0.2" in result.output
        assert "200" in result.output

    def test_world_bind_accepts_canonical_name(self, freq_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["world", "bind", "fundamental_frequency"])
        assert result.exit_code == 0, result.output
        assert "speech:fundamental_frequency: determined" in result.output


class TestWorldCommandsKeepConnectionOpen:
    @pytest.mark.parametrize(
        ("args", "expected_substrings"),
        [
            (["world", "resolve", "speech:fundamental_frequency", "--strategy", "recency"], ["speech:fundamental_frequency: determined"]),
            (["world", "derive", "speech:fundamental_frequency"], [": no_relationship"]),
            (["world", "chain", "speech:fundamental_frequency"], ["Target: speech:fundamental_frequency (fundamental_frequency)", "Result: determined", "0.2 (claim)"]),
            (["world", "extensions", "--semantics", "grounded"], ["Backend: claim_graph", "Accepted (1 claims):"]),
            (["world", "hypothetical", "--remove", "freq_paper:freq_claim1"], ["speech:fundamental_frequency:", "no_claims"]),
            (["world", "export-graph", "--format", "json"], ['"nodes"', '"edges"']),
            (["world", "check-consistency"], ["No conflicts under current bindings."]),
            (["world", "check-consistency", "--transitive"], ["No transitive conflicts found."]),
            (["world", "sensitivity", "speech:fundamental_frequency"], ["No sensitivity analysis available for "]),
        ],
    )
    def test_world_commands_do_not_use_closed_world_model(
        self,
        freq_workspace: Path,
        args: list[str],
        expected_substrings: list[str],
    ) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, args)
        assert result.exit_code == 0, result.output
        for expected in expected_substrings:
            assert expected in result.output


class TestWorldFragilityInterventions:
    def test_world_fragility_json_uses_interventions_key(self, freq_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "world",
                "fragility",
                "--format",
                "json",
                "--skip-atms",
                "--skip-discovery",
                "--skip-conflict",
                "--skip-grounding",
                "--skip-bridge",
            ],
        )
        assert result.exit_code == 0, result.output
        assert '"interventions"' in result.output
        assert '"interactions"' in result.output
        assert '"analysis_scope"' in result.output
        assert '"targets"' not in result.output

    def test_world_fragility_text_uses_intervention_header(self, freq_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "world",
                "fragility",
                "--skip-atms",
                "--skip-discovery",
                "--skip-conflict",
                "--skip-grounding",
                "--skip-bridge",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Intervention" in result.output
        assert "Family" in result.output
        assert "Target" not in result.output

    def test_world_fragility_accepts_ranking_policy(self, freq_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "world",
                "fragility",
                "--ranking-policy",
                "pareto",
                "--skip-atms",
                "--skip-discovery",
                "--skip-conflict",
                "--skip-grounding",
                "--skip-bridge",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "ranking=pareto" in result.output


# ── form show — unit conversions ─────────────────────────────────────

class TestFormShowConversions:
    """Tests for unit conversion display in `pks form show`."""

    def _write_form_with_conversions(self, workspace: Path, name: str, data: dict) -> None:
        forms_dir = workspace / "knowledge" / "forms"
        (forms_dir / f"{name}.yaml").write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False))
        _commit_workspace_paths(
            workspace,
            [f"forms/{name}.yaml"],
            f"Seed committed form {name}",
        )

    def test_form_show_displays_conversions(self, workspace: Path) -> None:
        self._write_form_with_conversions(workspace, "frequency", {
            "name": "frequency",
            "kind": "quantity",
            "dimensionless": False,
            "unit_symbol": "Hz",
            "dimensions": {"T": -1},
            "common_alternatives": [
                {"unit": "kHz", "type": "multiplicative", "multiplier": 1000},
                {"unit": "MHz", "type": "multiplicative", "multiplier": 1000000},
            ],
        })
        runner = CliRunner()
        result = runner.invoke(cli, ["form", "show", "frequency"])
        assert result.exit_code == 0, result.output
        assert "Unit Conversions" in result.output
        assert "kHz" in result.output

    def test_owner_form_show_reports_yaml_and_conversions(self, workspace: Path) -> None:
        self._write_form_with_conversions(workspace, "frequency", {
            "name": "frequency",
            "kind": "quantity",
            "dimensionless": False,
            "unit_symbol": "Hz",
            "dimensions": {"T": -1},
            "common_alternatives": [
                {"unit": "kHz", "type": "multiplicative", "multiplier": 1000},
            ],
        })
        repo = Repository.find(workspace)

        report = show_form(repo, "frequency")

        assert "name: frequency" in report.yaml_text
        assert report.form is not None
        assert "kHz" in report.form.conversions

    def test_form_show_no_conversions_for_category(self, workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["form", "show", "category"])
        assert result.exit_code == 0, result.output
        assert "Unit Conversions" not in result.output

    def test_form_show_affine_conversion(self, workspace: Path) -> None:
        self._write_form_with_conversions(workspace, "temperature", {
            "name": "temperature",
            "kind": "quantity",
            "dimensionless": False,
            "unit_symbol": "K",
            "dimensions": {"\u0398": 1},
            "common_alternatives": [
                {"unit": "\u00b0C", "type": "affine", "multiplier": 1.0, "offset": 273.15},
                {"unit": "\u00b0F", "type": "affine", "multiplier": 0.5556, "offset": 255.372},
            ],
        })
        runner = CliRunner()
        result = runner.invoke(cli, ["form", "show", "temperature"])
        assert result.exit_code == 0, result.output
        assert "Unit Conversions" in result.output
        # Check formatted affine conversion line (not just raw YAML keyword)
        assert "\u00b0C \u2192 K" in result.output or "degC \u2192 K" in result.output
        assert "affine" in result.output

    def test_form_show_logarithmic_conversion(self, workspace: Path) -> None:
        self._write_form_with_conversions(workspace, "sound_pressure_level", {
            "name": "sound_pressure_level",
            "kind": "quantity",
            "dimensionless": False,
            "unit_symbol": "Pa",
            "dimensions": {"M": 1, "L": -1, "T": -2},
            "common_alternatives": [
                {"unit": "dB_SPL", "type": "logarithmic", "base": 10, "divisor": 20, "reference": 0.00002},
            ],
        })
        runner = CliRunner()
        result = runner.invoke(cli, ["form", "show", "sound_pressure_level"])
        assert result.exit_code == 0, result.output
        assert "Unit Conversions" in result.output
        # Check formatted logarithmic conversion line (not just raw YAML keyword)
        assert "dB_SPL \u2192 Pa" in result.output
        assert "logarithmic" in result.output
        assert "ref=" in result.output


# ── Promote command (F17) ────────────────────────────────────────────

class TestPromoteCommandExists:
    """Bug F17: There is no 'pks promote' command to move proposal artifacts
    from proposals/ into knowledge/ (source-of-truth storage).  Without this
    command, heuristic output either goes directly to knowledge/ (violating
    the non-commitment principle) or stays in proposals/ with no path to
    acceptance."""

    def test_promote_is_registered_command(self):
        """The 'promote' command must be registered on the top-level CLI group."""
        command_names = cli.list_commands(click.Context(cli))
        assert "promote" in command_names, (
            f"'promote' not found in CLI commands: {sorted(command_names)}. "
            "A promote command is needed to move proposals into source-of-truth storage."
        )

    def test_promote_help_exits_cleanly(self, tmp_path: Path):
        """'pks promote --help' must exit 0 from an initialized git-backed repo."""
        Repository.init(tmp_path / "knowledge")
        runner = CliRunner()
        result = runner.invoke(cli, ["-C", str(tmp_path / "knowledge"), "promote", "--help"])
        assert result.exit_code == 0, (
            f"'pks promote --help' exited {result.exit_code}: {result.output}"
        )
