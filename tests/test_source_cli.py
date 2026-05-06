from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository
from tests.conftest import normalize_concept_payloads


def test_source_branch_kind_is_detected(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files({"seed.txt": b"ok\n"}, "seed")

    repo.git.create_branch("source/test-source")

    branches = {branch.name: branch for branch in repo.snapshot.iter_branches()}
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
    repo.git.commit_files(
        {"propstore.yaml": b"uri_authority: example.com,2026\n"},
        "Set repository config",
    )
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
    existing_concept = normalize_concept_payloads(
        [
            {
                "id": "existing",
                "canonical_name": "existing",
                "status": "accepted",
                "definition": "Existing concept.",
                "domain": "source",
                "form": "structural",
            }
        ],
        default_domain="source",
    )[0]
    repo.git.commit_batch(
        adds={
            "concepts/existing.yaml": yaml.safe_dump(
                existing_concept,
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
    assert stored["concepts"][0]["registry_match"]["artifact_id"] == existing_concept["artifact_id"]
    assert stored["concepts"][0]["aliases"] == [{"name": "existing_alias"}]
    assert stored["concepts"][1]["status"] == "proposed"
    assert stored["concepts"][1]["parameterization_relationships"][0]["inputs"] == ["existing"]


def test_source_add_concepts_auto_finalize_runtime_error_propagates(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    concepts_file = tmp_path / "concepts.yaml"
    concepts_file.write_text("concepts: []\n", encoding="utf-8")

    with (
        patch("propstore.source.commit_source_concepts_batch"),
        patch(
            "propstore.source.finalize_source_branch",
            side_effect=RuntimeError("auto finalize boom"),
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "-C",
                str(repo.root),
                "source",
                "add-concepts",
                "demo",
                "--batch",
                str(concepts_file),
            ],
        )

    assert result.exit_code != 0
    assert "auto finalize boom" in result.output
    assert "Hint: rerun with --traceback" in result.output


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


def _seed_context(repo, context_id="ctx_test"):
    repo.git.commit_batch(
        adds={
            f"contexts/{context_id}.yaml": yaml.safe_dump(
                {
                    "id": context_id,
                    "name": context_id,
                    "description": "Test context",
                },
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        },
        deletes=[],
        message=f"Seed context {context_id}",
        branch="master",
    )


def _prepare_promoted_parameter_source(
    runner: CliRunner,
    repo: Repository,
    tmp_path: Path,
) -> str:
    content_file = tmp_path / "paper.pdf"
    content_file.write_bytes(b"%PDF-demo\n")
    _seed_forms(repo, ["scalar"])
    _seed_context(repo)

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
            "file",
            "--origin-value",
            "paper.pdf",
            "--content-file",
            str(content_file),
        ],
    )
    assert init_result.exit_code == 0, init_result.output

    propose_concept = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            "demo",
            "--concept-name",
            "boiling_point",
            "--definition",
            "Temperature at which water boils.",
            "--form",
            "scalar",
        ],
    )
    assert propose_concept.exit_code == 0, propose_concept.output

    propose_claim = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-claim",
            "demo",
            "--id",
            "param1",
            "--type",
            "parameter",
            "--concept",
            "boiling_point",
            "--value",
            "100.0",
            "--unit",
            "celsius",
            "--context",
            "ctx_test",
            "--page",
            "5",
        ],
    )
    assert propose_claim.exit_code == 0, propose_claim.output

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

    papers_dir = repo.root.parent / "papers" / "demo"
    papers_dir.mkdir(parents=True, exist_ok=True)
    (papers_dir / "paper.pdf").write_bytes(content_file.read_bytes())

    claims_doc = yaml.safe_load(repo.git.read_file("claims/demo.yaml"))
    return claims_doc["claims"][0]["artifact_id"]


def test_propose_concept_reports_linked_status(tmp_path: Path) -> None:
    """When a proposed concept matches one on master, CLI should print 'Linked'."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    # Seed a concept on master so propose-concept can link to it.
    _seed_forms(repo, ["structural"])
    existing_concept = normalize_concept_payloads(
        [
            {
                "id": "existing",
                "canonical_name": "existing",
                "status": "accepted",
                "definition": "Existing concept.",
                "domain": "source",
                "form": "structural",
            }
        ],
        default_domain="source",
    )[0]
    repo.git.commit_batch(
        adds={
            "concepts/existing.yaml": yaml.safe_dump(
                existing_concept,
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
            "--concept-name", "existing",
            "--definition", "Existing concept from source.",
            "--form", "structural",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Linked" in result.output
    assert "existing" in result.output
    assert existing_concept["artifact_id"] in result.output


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
            "--concept-name", "brand_new_thing",
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
            "--concept-name", "some_concept",
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
            "--concept-name", "color",
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
            "--concept-name", "status",
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
            "--concept-name", "temperature",
            "--definition", "A temperature measurement.",
            "--form", "scalar",
            "--values", "hot,cold",
        ],
    )

    assert result.exit_code != 0, result.output
    assert "values are only valid when form is category" in result.output


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
            "--concept-name", "mood",
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
            "--concept-name", "severity",
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
    concept_files = list(repo.git.iter_dir("concepts", commit=master_tip))
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


@pytest.mark.e2e
def test_source_authoring_build_verify_and_worldline_flow(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    claim_id = _prepare_promoted_parameter_source(runner, repo, tmp_path)

    build_result = runner.invoke(
        cli,
        ["-C", str(repo.root), "build", "--force"],
    )
    assert build_result.exit_code == 0, build_result.output
    assert repo.sidecar_path.exists()

    verify_result = runner.invoke(
        cli,
        ["-C", str(repo.root), "verify", "tree", claim_id],
    )
    assert verify_result.exit_code == 0, verify_result.output
    verify_report = yaml.safe_load(verify_result.output)
    assert verify_report["status"] == "ok"
    assert verify_report["origin_verification"]["status"] == "matched"

    create_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "worldline",
            "create",
            "boiling_worldline",
            "--target",
            "boiling_point",
        ],
    )
    assert create_result.exit_code == 0, create_result.output

    rebuild_result = runner.invoke(
        cli,
        ["-C", str(repo.root), "build", "--force"],
    )
    assert rebuild_result.exit_code == 0, rebuild_result.output

    run_result = runner.invoke(
        cli,
        ["-C", str(repo.root), "worldline", "run", "boiling_worldline"],
    )
    assert run_result.exit_code == 0, run_result.output
    assert "boiling_point" in run_result.output
    assert "100.0" in run_result.output

    show_result = runner.invoke(
        cli,
        ["-C", str(repo.root), "worldline", "show", "boiling_worldline"],
    )
    assert show_result.exit_code == 0, show_result.output
    assert "boiling_worldline" in show_result.output
    assert "boiling_point" in show_result.output

    list_result = runner.invoke(
        cli,
        ["-C", str(repo.root), "worldline", "list"],
    )
    assert list_result.exit_code == 0, list_result.output
    assert "boiling_worldline" in list_result.output

    worldline_doc = yaml.safe_load(repo.git.read_file("worldlines/boiling_worldline.yaml"))
    value_record = worldline_doc["results"]["values"]["boiling_point"]
    assert value_record["status"] == "determined"
    assert value_record["value"] == 100.0


def test_source_add_claim_sees_source_branch_proposed_concepts_in_cel(tmp_path: Path) -> None:
    """Regression: CEL conditions referencing source-branch-proposed concepts must validate.

    Reproduces the bug where ``pks source add-claim`` rejected a claim whose
    ``conditions:`` referenced a concept that had just been proposed on the
    same source branch via ``pks source propose-concept``. The CEL checker
    used to read only master's canonical concepts; it now also layers the
    source branch's currently-proposed concepts.
    """
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_forms(repo, ["count"])
    _seed_context(repo)

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    propose_result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-concept", "demo",
            "--concept-name", "scheme_size",
            "--definition", "Number of slots in the scheme.",
            "--form", "count",
        ],
    )
    assert propose_result.exit_code == 0, propose_result.output

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "observation",
                        "context": "ctx_test",
                        "statement": "Claim referencing the source-branch concept.",
                        "conditions": ["scheme_size == 3"],
                        "provenance": {"page": 1},
                    },
                ],
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
            "source", "add-claim", "demo",
            "--batch", str(claims_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Undefined concept" not in result.output


def test_source_add_claim_rejects_unknown_concept_in_cel(tmp_path: Path) -> None:
    """Sanity: a CEL condition referencing a never-declared concept still errors.

    The fix for the source-proposed-concepts case must not turn the gate off
    entirely. A condition that names neither a master concept nor a
    source-proposed concept must still be rejected.
    """
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_forms(repo, ["count"])
    _seed_context(repo)

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    propose_result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-concept", "demo",
            "--concept-name", "scheme_size",
            "--definition", "Number of slots in the scheme.",
            "--form", "count",
        ],
    )
    assert propose_result.exit_code == 0, propose_result.output

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "observation",
                        "context": "ctx_test",
                        "statement": "Refers to nothing declared anywhere.",
                        "conditions": ["never_declared == 3"],
                        "provenance": {"page": 1},
                    },
                ],
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
            "source", "add-claim", "demo",
            "--batch", str(claims_file),
        ],
    )

    assert result.exit_code != 0
    assert "Undefined concept" in result.output
    assert "never_declared" in result.output


def _seed_bounded_forms(repo) -> None:
    """Seed master with the three bounded forms used by the bounds tests.

    Mirrors the production resource YAMLs (probability [0, 1], correlation
    [-1, 1], dimensionless unbounded). _seed_forms doesn't support bounds, so
    we write the YAMLs directly here.
    """
    adds = {
        "forms/probability.yaml": yaml.safe_dump(
            {
                "name": "probability",
                "kind": "quantity",
                "dimensionless": True,
                "min": 0.0,
                "max": 1.0,
            },
            sort_keys=False,
            allow_unicode=True,
        ).encode("utf-8"),
        "forms/correlation.yaml": yaml.safe_dump(
            {
                "name": "correlation",
                "kind": "quantity",
                "dimensionless": True,
                "min": -1.0,
                "max": 1.0,
            },
            sort_keys=False,
            allow_unicode=True,
        ).encode("utf-8"),
        "forms/dimensionless.yaml": yaml.safe_dump(
            {
                "name": "dimensionless",
                "kind": "quantity",
                "dimensionless": True,
            },
            sort_keys=False,
            allow_unicode=True,
        ).encode("utf-8"),
    }
    repo.git.commit_batch(
        adds=adds, deletes=[], message="Seed bounded forms", branch="master",
    )


def _add_claim_with_bounds(
    tmp_path: Path,
    *,
    form: str,
    concept_handle: str,
    value: float | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
):
    """Boilerplate: build a repo with bounded forms, propose a concept of the
    requested form, and add a parameter claim with the supplied numeric fields.
    Returns the CliRunner result."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_bounded_forms(repo)
    _seed_context(repo)

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    propose_result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-concept", "demo",
            "--concept-name", concept_handle,
            "--definition", f"Test concept of form {form}.",
            "--form", form,
        ],
    )
    assert propose_result.exit_code == 0, propose_result.output

    claim_payload: dict[str, object] = {
        "id": "claim1",
        "type": "parameter",
        "context": "ctx_test",
        "concept": concept_handle,
        "statement": f"Bounded {form} claim.",
        "provenance": {"page": 1},
    }
    if value is not None:
        claim_payload["value"] = value
    if lower_bound is not None:
        claim_payload["lower_bound"] = lower_bound
    if upper_bound is not None:
        claim_payload["upper_bound"] = upper_bound

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "claims": [claim_payload],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    return runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "add-claim", "demo",
            "--batch", str(claims_file),
        ],
    )


def test_source_add_claim_rejects_value_above_form_max(tmp_path: Path) -> None:
    result = _add_claim_with_bounds(
        tmp_path,
        form="probability",
        concept_handle="success_rate",
        value=1.5,
    )
    assert result.exit_code != 0, result.output
    assert "value" in result.output
    assert "1.5" in result.output
    assert "1.0" in result.output
    assert "probability" in result.output


def test_source_add_claim_rejects_value_below_form_min(tmp_path: Path) -> None:
    result = _add_claim_with_bounds(
        tmp_path,
        form="correlation",
        concept_handle="kappa_score",
        value=-1.5,
    )
    assert result.exit_code != 0, result.output
    assert "value" in result.output
    assert "-1.5" in result.output
    assert "-1.0" in result.output
    assert "correlation" in result.output


def test_source_add_claim_accepts_value_within_form_bounds(tmp_path: Path) -> None:
    result = _add_claim_with_bounds(
        tmp_path,
        form="probability",
        concept_handle="success_rate",
        value=0.5,
    )
    assert result.exit_code == 0, result.output


def test_source_add_claim_unbounded_form_accepts_any_value(tmp_path: Path) -> None:
    """The dimensionless escape hatch must accept any numeric value."""
    above = _add_claim_with_bounds(
        tmp_path,
        form="dimensionless",
        concept_handle="random_number",
        value=1.5,
    )
    assert above.exit_code == 0, above.output

    # Build a fresh repo for the second value (CliRunner reuse with
    # add-claim re-ingests against the same source branch — independent
    # repos give a clean exercise of the unbounded path).
    below = _add_claim_with_bounds(
        tmp_path / "second",
        form="dimensionless",
        concept_handle="random_number",
        value=-1.5,
    )
    assert below.exit_code == 0, below.output


def test_source_add_claim_rejects_lower_bound_outside_form_range(tmp_path: Path) -> None:
    result = _add_claim_with_bounds(
        tmp_path,
        form="probability",
        concept_handle="success_rate",
        lower_bound=-0.1,
        upper_bound=0.5,
    )
    assert result.exit_code != 0, result.output
    assert "lower_bound" in result.output
    assert "-0.1" in result.output
    assert "probability" in result.output
