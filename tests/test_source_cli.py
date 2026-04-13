from __future__ import annotations

import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.cli.repository import Repository
from propstore.repo.branch import create_branch, list_branches


def test_source_branch_kind_is_detected(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files({"seed.txt": b"ok\n"}, "seed")

    create_branch(repo.git, "source/test-source")

    branches = {branch.name: branch for branch in list_branches(repo.git)}
    assert branches["source/test-source"].kind == "source"


def test_source_init_creates_source_branch_and_source_yaml(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "init",
            "Halpin_2010_OwlSameAsIsntSame",
            "--kind",
            "academic_paper",
            "--origin-type",
            "doi",
            "--origin-value",
            "10.1007/978-3-642-17746-0_20",
        ],
    )

    assert result.exit_code == 0, result.output
    branch_tip = repo.git.branch_sha("source/Halpin_2010_OwlSameAsIsntSame")
    assert branch_tip is not None
    source_doc = yaml.safe_load(repo.git.read_file("source.yaml", commit=branch_tip))
    assert source_doc["kind"] == "academic_paper"
    assert source_doc["origin"]["type"] == "doi"
    assert source_doc["origin"]["value"] == "10.1007/978-3-642-17746-0_20"
    assert source_doc["id"].startswith("tag:")


def test_source_init_uses_repo_uri_authority_and_content_file(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.config_path.write_text("uri_authority: example.com,2026\n", encoding="utf-8")
    runner = CliRunner()
    content_file = tmp_path / "paper.pdf"
    content_file.write_bytes(b"%PDF-demo\n")

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "init",
            "demo",
            "--kind",
            "academic_paper",
            "--origin-type",
            "file",
            "--origin-value",
            "paper.pdf",
            "--content-file",
            str(content_file),
        ],
    )

    assert result.exit_code == 0, result.output
    branch_tip = repo.git.branch_sha("source/demo")
    assert branch_tip is not None
    source_doc = yaml.safe_load(repo.git.read_file("source.yaml", commit=branch_tip))
    assert source_doc["id"] == "tag:example.com,2026:source/demo"
    assert source_doc["origin"]["content_ref"].startswith("ni:///sha-256;")


def test_source_write_notes_commits_only_to_source_branch(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    notes_file = tmp_path / "notes.md"
    notes_file.write_text("# Notes\n\nA source note.\n", encoding="utf-8")

    init_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "init",
            "demo",
            "--kind",
            "academic_paper",
            "--origin-type",
            "manual",
            "--origin-value",
            "demo",
        ],
    )
    assert init_result.exit_code == 0, init_result.output

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "write-notes",
            "demo",
            "--file",
            str(notes_file),
        ],
    )

    assert result.exit_code == 0, result.output
    branch_tip = repo.git.branch_sha("source/demo")
    assert branch_tip is not None
    stored_notes = repo.git.read_file("notes.md", commit=branch_tip).decode("utf-8").replace("\r\n", "\n")
    assert stored_notes == notes_file.read_text(encoding="utf-8").replace("\r\n", "\n")
    try:
        repo.git.read_file("notes.md")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("notes.md should not be materialized on master")


def test_source_write_metadata_commits_json_to_source_branch(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    metadata_file = tmp_path / "metadata.json"
    metadata_file.write_text(
        json.dumps({"title": "Demo", "authors": ["A"], "year": "2026"}, indent=2),
        encoding="utf-8",
    )

    init_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "init",
            "demo-meta",
            "--kind",
            "academic_paper",
            "--origin-type",
            "manual",
            "--origin-value",
            "demo-meta",
        ],
    )
    assert init_result.exit_code == 0, init_result.output

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "write-metadata",
            "demo-meta",
            "--file",
            str(metadata_file),
        ],
    )

    assert result.exit_code == 0, result.output
    branch_tip = repo.git.branch_sha("source/demo-meta")
    assert branch_tip is not None
    loaded = json.loads(repo.git.read_file("metadata.json", commit=branch_tip))
    assert loaded["title"] == "Demo"
    assert loaded["authors"] == ["A"]


def test_source_add_concepts_batch_preserves_inventory_fields(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    repo.git.commit_batch(
        adds={
            "concepts/existing.yaml": yaml.safe_dump(
                {
                    "canonical_name": "existing",
                    "status": "accepted",
                    "definition": "Existing concept.",
                    "domain": "source",
                    "form": "structural",
                    "artifact_id": "ps:concept:existing",
                    "logical_ids": [{"namespace": "propstore", "value": "existing"}],
                    "version_id": "version:existing",
                },
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        },
        deletes=[],
        message="Seed existing concept",
        branch="master",
    )

    init_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "init",
            "demo-concepts",
            "--kind",
            "academic_paper",
            "--origin-type",
            "manual",
            "--origin-value",
            "demo-concepts",
        ],
    )
    assert init_result.exit_code == 0, init_result.output

    concepts_file = tmp_path / "concepts.yaml"
    concepts_file.write_text(
        yaml.safe_dump(
            {
                "concepts": [
                    {
                        "local_name": "existing",
                        "definition": "Existing concept from source.",
                        "form": "structural",
                        "aliases": [{"name": "existing_alias"}],
                    },
                    {
                        "local_name": "bridge",
                        "proposed_name": "bridge",
                        "definition": "Bridges two concepts.",
                        "form": "scalar",
                        "parameterization_relationships": [
                            {"inputs": ["existing"], "formula": "f(existing)"}
                        ],
                    },
                ]
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-concepts",
            "demo-concepts",
            "--batch",
            str(concepts_file),
        ],
    )
    assert result.exit_code == 0, result.output

    branch_tip = repo.git.branch_sha("source/demo-concepts")
    assert branch_tip is not None
    stored = yaml.safe_load(repo.git.read_file("concepts.yaml", commit=branch_tip))
    assert stored["concepts"][0]["status"] == "linked"
    assert stored["concepts"][0]["registry_match"]["artifact_id"] == "ps:concept:existing"
    assert stored["concepts"][0]["aliases"] == [{"name": "existing_alias"}]
    assert stored["concepts"][1]["status"] == "proposed"
    assert stored["concepts"][1]["parameterization_relationships"][0]["inputs"] == ["existing"]


def test_source_sync_materializes_branch_to_papers_workspace(tmp_path: Path) -> None:
    repo_root = tmp_path / "project"
    repo = Repository.init(repo_root / "knowledge")
    runner = CliRunner()
    notes_file = tmp_path / "notes.md"
    notes_file.write_text("# Notes\n", encoding="utf-8")

    init_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "init",
            "demo-sync",
            "--kind",
            "academic_paper",
            "--origin-type",
            "manual",
            "--origin-value",
            "demo-sync",
        ],
    )
    assert init_result.exit_code == 0, init_result.output

    write_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "write-notes",
            "demo-sync",
            "--file",
            str(notes_file),
        ],
    )
    assert write_result.exit_code == 0, write_result.output

    sync_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "sync",
            "demo-sync",
        ],
    )
    assert sync_result.exit_code == 0, sync_result.output

    synced_notes = repo.root.parent / "papers" / "demo-sync" / "notes.md"
    assert synced_notes.exists()
    assert synced_notes.read_text(encoding="utf-8") == "# Notes\n"


def _init_source(runner, repo, name="demo"):
    """Helper: init a source branch and return the result."""
    return runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "init", name,
            "--kind", "academic_paper",
            "--origin-type", "manual",
            "--origin-value", name,
        ],
    )


def _seed_forms(repo, form_names):
    """Commit minimal form YAML files to master so form validation passes."""
    adds = {}
    dimensionless_forms = {"structural", "category", "scalar"}
    for form_name in form_names:
        adds[f"forms/{form_name}.yaml"] = yaml.safe_dump(
            {
                "name": form_name,
                "dimensionless": form_name in dimensionless_forms,
            },
            sort_keys=False,
            allow_unicode=True,
        ).encode("utf-8")
    repo.git.commit_batch(
        adds=adds, deletes=[], message="Seed forms", branch="master",
    )


def test_propose_concept_reports_linked_status(tmp_path: Path) -> None:
    """When a proposed concept matches one on master, CLI should print 'Linked'."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    # Seed a concept on master so propose-concept can link to it.
    _seed_forms(repo, ["structural"])
    repo.git.commit_batch(
        adds={
            "concepts/existing.yaml": yaml.safe_dump(
                {
                    "canonical_name": "existing",
                    "status": "accepted",
                    "definition": "Existing concept.",
                    "domain": "source",
                    "form": "structural",
                    "artifact_id": "ps:concept:existing",
                    "logical_ids": [{"namespace": "propstore", "value": "existing"}],
                    "version_id": "version:existing",
                },
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        },
        deletes=[],
        message="Seed existing concept",
        branch="master",
    )

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-concept", "demo",
            "--name", "existing",
            "--definition", "Existing concept from source.",
            "--form", "structural",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Linked" in result.output
    assert "existing" in result.output
    assert "ps:concept:existing" in result.output


def test_propose_concept_reports_proposed_status(tmp_path: Path) -> None:
    """When a proposed concept is new, CLI should print 'Proposed new concept'."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    _seed_forms(repo, ["structural"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-concept", "demo",
            "--name", "brand_new_thing",
            "--definition", "A brand new concept.",
            "--form", "structural",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Proposed new concept" in result.output
    assert "brand_new_thing" in result.output
    assert "structural" in result.output


def test_propose_concept_rejects_invalid_form(tmp_path: Path) -> None:
    """propose-concept should reject a form name not in the repo's forms directory."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    _seed_forms(repo, ["structural", "scalar"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-concept", "demo",
            "--name", "some_concept",
            "--definition", "A concept.",
            "--form", "bogus_form",
        ],
    )

    assert result.exit_code != 0, result.output
    assert "Unknown form" in result.output
    assert "bogus_form" in result.output
    assert "structural" in result.output


def test_propose_concept_category_with_values(tmp_path: Path) -> None:
    """propose-concept --values should store values in form_parameters for category concepts."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    _seed_forms(repo, ["category"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-concept", "demo",
            "--name", "color",
            "--definition", "A color category.",
            "--form", "category",
            "--values", "red,green,blue",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Proposed new concept" in result.output

    branch_tip = repo.git.branch_sha("source/demo")
    stored = yaml.safe_load(repo.git.read_file("concepts.yaml", commit=branch_tip))
    concept = stored["concepts"][0]
    assert concept["local_name"] == "color"
    assert concept["form"] == "category"
    assert concept["form_parameters"]["values"] == ["red", "green", "blue"]


def test_propose_concept_category_with_values_and_closed(tmp_path: Path) -> None:
    """--values combined with --closed should set both values and extensible: false."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    _seed_forms(repo, ["category"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-concept", "demo",
            "--name", "status",
            "--definition", "A status category.",
            "--form", "category",
            "--values", "active,inactive",
            "--closed",
        ],
    )

    assert result.exit_code == 0, result.output

    branch_tip = repo.git.branch_sha("source/demo")
    stored = yaml.safe_load(repo.git.read_file("concepts.yaml", commit=branch_tip))
    concept = stored["concepts"][0]
    assert concept["form_parameters"]["values"] == ["active", "inactive"]
    assert concept["form_parameters"]["extensible"] is False


def test_propose_concept_values_rejected_for_non_category(tmp_path: Path) -> None:
    """--values on a non-category form should error."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    _seed_forms(repo, ["scalar"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-concept", "demo",
            "--name", "temperature",
            "--definition", "A temperature measurement.",
            "--form", "scalar",
            "--values", "hot,cold",
        ],
    )

    assert result.exit_code != 0, result.output
    assert "only valid with --form=category" in result.output


def test_propose_concept_category_without_values_still_works(tmp_path: Path) -> None:
    """Category concept without --values should still be accepted (backwards compatible)."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    _seed_forms(repo, ["category"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-concept", "demo",
            "--name", "mood",
            "--definition", "A mood category.",
            "--form", "category",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Proposed new concept" in result.output


def test_propose_concept_values_survive_finalize_and_promote(tmp_path: Path) -> None:
    """Values set via propose-concept should survive finalize and promote to master."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    _seed_forms(repo, ["category"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    propose_result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-concept", "demo",
            "--name", "severity",
            "--definition", "Severity levels.",
            "--form", "category",
            "--values", "low,medium,high",
            "--closed",
        ],
    )
    assert propose_result.exit_code == 0, propose_result.output

    finalize_result = runner.invoke(
        cli,
        ["-C", str(repo.root), "source", "finalize", "demo"],
    )
    assert finalize_result.exit_code == 0, finalize_result.output

    promote_result = runner.invoke(
        cli,
        ["-C", str(repo.root), "source", "promote", "demo"],
    )
    assert promote_result.exit_code == 0, promote_result.output

    # Check that the concept landed on master with values intact
    master_tip = repo.git.branch_sha("master")
    concept_files = repo.git.list_dir("concepts", commit=master_tip)
    severity_file = [f for f in concept_files if "severity" in f]
    assert severity_file, f"No severity concept file found on master. Files: {concept_files}"
    concept_data = yaml.safe_load(repo.git.read_file(f"concepts/{severity_file[0]}", commit=master_tip))
    assert "form_parameters" in concept_data
    assert concept_data["form_parameters"]["values"] == ["low", "medium", "high"]
    assert concept_data["form_parameters"]["extensible"] is False


def test_add_concepts_batch_rejects_invalid_form(tmp_path: Path) -> None:
    """add-concepts --batch should reject a YAML file with an invalid form name."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    _seed_forms(repo, ["structural", "scalar"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    concepts_file = tmp_path / "concepts.yaml"
    concepts_file.write_text(
        yaml.safe_dump(
            {
                "concepts": [
                    {
                        "local_name": "some_concept",
                        "definition": "A concept.",
                        "form": "bogus_form",
                    },
                ]
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "add-concepts", "demo",
            "--batch", str(concepts_file),
        ],
    )

    assert result.exit_code != 0, result.output
    assert "Unknown form" in result.output
    assert "bogus_form" in result.output
    assert "structural" in result.output
