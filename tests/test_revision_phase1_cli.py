from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository
from tests.conftest import normalize_claims_payload, normalize_concept_payloads, write_test_context


def _make_concept(name: str, cid: str, domain: str, status: str = "accepted",
                  form: str = "frequency", **extra: object) -> dict:
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


def _write_concept(concepts_dir: Path, name: str, data: dict) -> Path:
    concepts_dir.mkdir(parents=True, exist_ok=True)
    path = concepts_dir / f"{name}.yaml"
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
    return path


def _write_counter(concepts_dir: Path, value: int) -> None:
    counters = concepts_dir / ".counters"
    counters.mkdir(parents=True, exist_ok=True)
    (counters / "global.next").write_text(f"{value}\n")


def _write_claim_file(claims_dir: Path, filename: str, data: dict) -> Path:
    claims_dir.mkdir(parents=True, exist_ok=True)
    path = claims_dir / filename
    normalized = normalize_claims_payload(data)
    path.write_text(yaml.dump(normalized, default_flow_style=False, sort_keys=False))
    return path


@pytest.fixture()
def revision_cli_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)

    knowledge = tmp_path / "knowledge"
    repo = Repository.init(knowledge)
    write_test_context(knowledge)
    concepts = knowledge / "concepts"
    concepts.mkdir(parents=True, exist_ok=True)

    forms_dir = knowledge / "forms"
    forms_dir.mkdir(exist_ok=True)
    for form_name in ("frequency", "category", "boolean", "structural"):
        form_data: dict = {"name": form_name, "dimensionless": False}
        if form_name == "category":
            form_data["kind"] = "category"
            form_data["parameters"] = {
                "values": {"required": True},
                "extensible": {"required": False},
            }
        (forms_dir / f"{form_name}.yaml").write_text(
            yaml.dump(form_data, default_flow_style=False)
        )

    frequency_concept = _make_concept(
        "fundamental_frequency", "concept1", "speech", form="frequency"
    )
    _write_concept(concepts, "fundamental_frequency", frequency_concept)
    _write_concept(concepts, "speaker_sex", _make_concept(
        "speaker_sex",
        "concept2",
        "speech",
        form="category",
        form_parameters={"values": ["male", "female"], "extensible": True},
    ))
    _write_counter(concepts, 3)

    claims_dir = knowledge / "claims"
    _write_claim_file(claims_dir, "freq_paper.yaml", {
        "source": {"paper": "freq_paper"},
        "claims": [
            {
                "id": "freq_claim1",
                "type": "parameter",
                "concept": frequency_concept["artifact_id"],
                "value": 0.2,
                "unit": "kHz",
                "conditions": ["speaker_sex == 'male'"],
                "provenance": {"paper": "freq_paper", "page": 1},
            }
        ],
    })

    adds = {
        path.relative_to(knowledge).as_posix(): path.read_bytes()
        for path in knowledge.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }
    repo.git.commit_files(adds, "Seed revision CLI workspace")
    repo.git.sync_worktree()

    runner = CliRunner()
    sidecar = knowledge / "sidecar" / "propstore.sqlite"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    result = runner.invoke(cli, ["build", "-o", str(sidecar)])
    assert result.exit_code == 0, result.output
    return tmp_path


def test_world_revision_base_shows_exact_claim_atoms_and_assumptions(revision_cli_workspace: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["world", "revision-base", "--context", "ctx_test", "speaker_sex=male"],
    )

    assert result.exit_code == 0, result.output
    assert "claim:freq_claim1" in result.output
    assert "speaker_sex == 'male'" in result.output


def test_world_revision_entrenchment_shows_ranked_atoms(revision_cli_workspace: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["world", "revision-entrenchment", "--context", "ctx_test", "speaker_sex=male"],
    )

    assert result.exit_code == 0, result.output
    assert "claim:freq_claim1" in result.output
