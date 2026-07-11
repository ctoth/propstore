"""CLI-adapter tests for the Phase 10-1 advanced families.

These exercise the thin Click adapters (``import-repository``, ``grounding``,
``observatory``) end-to-end through :data:`propstore.cli.cli` with
``click.testing.CliRunner``. The owner-layer behavior they wrap is pinned in
``test_repository_import``, ``test_observatory``, and ``test_grounding_*``; here
we only check the adapter wiring and rendering.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from click.testing import CliRunner
from quire.documents import document_to_payload

from propstore.cli import cli
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.predicates import Predicate
from propstore.families.rules import Atom, BodyLiteral, DefeasibleRule, Term
from propstore.observatory import EvaluationScenario
from propstore.repository import Repository


# --- import-repository -------------------------------------------------------


def _seed_source(root: Path) -> Repository:
    source = Repository.init(root / "knowledge")
    source.families.concept.save(
        "concept:legacy",
        Concept(concept_id="concept:legacy", canonical_name="Mass"),
        message="author concept",
    )
    return source


def test_import_repository_cli_emits_result_yaml(tmp_path: Path) -> None:
    destination = Repository.init(tmp_path / "dest" / "knowledge")
    source = _seed_source(tmp_path / "repo-b")

    result = CliRunner().invoke(
        cli, ["-C", str(destination.root), "import-repository", str(source.root.parent)]
    )

    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["surface"] == "repository_import_commit"
    assert payload["source_repository"] == str(source.root)
    assert payload["target_branch"] == "import/repo-b"
    assert len(payload["commit_sha"]) == 40
    assert payload["deleted_paths"] == []
    # The import landed on the import branch, never on master.
    assert (
        destination.require_git().branch_sha("import/repo-b") == payload["commit_sha"]
    )


def test_import_repository_cli_target_branch_master(tmp_path: Path) -> None:
    destination = Repository.init(tmp_path / "dest" / "knowledge")
    source = _seed_source(tmp_path / "repo-b")

    result = CliRunner().invoke(
        cli,
        [
            "-C",
            str(destination.root),
            "import-repository",
            str(source.root.parent),
            "--target-branch",
            "master",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["target_branch"] == "master"


def test_import_repository_cli_plan_only_does_not_commit(tmp_path: Path) -> None:
    destination = Repository.init(tmp_path / "dest" / "knowledge")
    source = _seed_source(tmp_path / "repo-b")

    result = CliRunner().invoke(
        cli,
        [
            "-C",
            str(destination.root),
            "import-repository",
            str(source.root.parent),
            "--plan",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["surface"] == "repository_import_plan"
    assert payload["target_branch"] == "import/repo-b"
    assert any("concept" in path for path in payload["writes"])
    # Plan-only: nothing committed onto the import branch.
    assert destination.require_git().branch_sha("import/repo-b") is None


# --- grounding ---------------------------------------------------------------


def _seed_grounding_repo(root: Path) -> Repository:
    repo = Repository.init(root / "knowledge")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "cl1",
        Claim(
            claim_id="cl1", context_id="ctx1", claim_type=ClaimType.PARAMETER, value=1.0
        ),
        message="m",
    )
    repo.families.predicate.save(
        "has_value",
        Predicate(
            predicate_id="has_value",
            arity=1,
            arg_types=("Claim",),
            derived_from="claim.attribute:value",
        ),
        message="m",
    )
    repo.families.predicate.save(
        "important",
        Predicate(predicate_id="important", arity=1, arg_types=("Claim",)),
        message="m",
    )
    repo.families.defeasible_rule.save(
        "r1",
        DefeasibleRule(
            rule_id="r1",
            kind="defeasible",
            head=Atom(predicate="important", terms=(Term(kind="var", name="X"),)),
            body=(
                BodyLiteral(
                    kind="positive",
                    atom=Atom(
                        predicate="has_value", terms=(Term(kind="var", name="X"),)
                    ),
                ),
            ),
        ),
        message="m",
    )
    return repo


def _invoke_grounding(repo: Repository, *args: str):
    return CliRunner().invoke(cli, ["-C", str(repo.root), "grounding", *args])


def test_grounding_status_ready(tmp_path: Path) -> None:
    repo = _seed_grounding_repo(tmp_path / "kn")
    result = _invoke_grounding(repo, "status")
    assert result.exit_code == 0, result.output
    assert "Grounding surface: ready" in result.output
    assert "Facts:" in result.output


def test_grounding_status_none_for_bare_repo(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "kn" / "knowledge")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    result = _invoke_grounding(repo, "status")
    assert result.exit_code == 0, result.output
    assert "Grounding surface: none" in result.output


def test_grounding_status_invalid_for_rules_without_predicates(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "kn" / "knowledge")
    repo.families.defeasible_rule.save(
        "r1",
        DefeasibleRule(
            rule_id="r1",
            kind="defeasible",
            head=Atom(predicate="h", terms=(Term(kind="var", name="X"),)),
        ),
        message="m",
    )
    result = _invoke_grounding(repo, "status")
    assert result.exit_code == 0, result.output
    assert "Grounding surface: invalid" in result.output


def test_grounding_show_lists_facts_and_sections(tmp_path: Path) -> None:
    repo = _seed_grounding_repo(tmp_path / "kn")
    result = _invoke_grounding(repo, "show")
    assert result.exit_code == 0, result.output
    assert "Facts (" in result.output
    assert "has_value(cl1)" in result.output
    assert "Sections:" in result.output
    assert "important(cl1)" in result.output


def test_grounding_query_reports_matching_sections(tmp_path: Path) -> None:
    repo = _seed_grounding_repo(tmp_path / "kn")
    result = _invoke_grounding(repo, "query", 'important("cl1")')
    assert result.exit_code == 0, result.output
    assert "yes" in result.output


def test_grounding_query_absent_atom(tmp_path: Path) -> None:
    repo = _seed_grounding_repo(tmp_path / "kn")
    result = _invoke_grounding(repo, "query", 'important("missing")')
    assert result.exit_code == 0, result.output
    assert "status: absent" in result.output


def test_grounding_arguments_lists_arguments(tmp_path: Path) -> None:
    repo = _seed_grounding_repo(tmp_path / "kn")
    result = _invoke_grounding(repo, "arguments")
    assert result.exit_code == 0, result.output
    assert "Arguments (" in result.output


# --- observatory -------------------------------------------------------------


def _write_fixture(path: Path, *, falsified: bool) -> Path:
    scenario = EvaluationScenario(
        scenario_id="s1",
        operator_family="fam",
        policy_id="policy:p",
        replay_result_hash="replay:r",
        falsification_ids=("f1",) if falsified else (),
    )
    path.write_text(json.dumps(document_to_payload(scenario)), encoding="utf-8")
    return path


def test_observatory_run_json(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path / "s.json", falsified=True)
    result = CliRunner().invoke(
        cli, ["observatory", "run", "--fixture", str(fixture), "--format", "json"]
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["scenario_results"][0]["scenario_id"] == "s1"
    assert payload["operator_summaries"][0]["falsification_count"] == 1


def test_observatory_run_text(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path / "s.json", falsified=True)
    result = CliRunner().invoke(
        cli, ["observatory", "run", "--fixture", str(fixture), "--format", "text"]
    )
    assert result.exit_code == 0, result.output
    assert "observatory report: 1 scenarios" in result.output
    assert "fail: s1" in result.output


def test_observatory_run_rejects_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid", encoding="utf-8")
    result = CliRunner().invoke(cli, ["observatory", "run", "--fixture", str(bad)])
    assert result.exit_code != 0
    assert str(bad) in result.output


def test_observatory_run_rejects_yaml_syntax_in_json_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "scenario.json"
    fixture.write_text(
        "scenario_id: s1\n"
        "operator_family: family\n"
        "policy_id: policy\n"
        "replay_result_hash: replay\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["observatory", "run", "--fixture", str(fixture)],
    )

    assert result.exit_code != 0
    assert str(fixture) in result.output


def test_observatory_registered_lazily() -> None:
    text = Path("propstore/cli/__init__.py").read_text(encoding="utf-8")
    assert '"observatory": ("propstore.cli.observatory", "observatory"' in text
    assert "from propstore.cli.observatory" not in text
