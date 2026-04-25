"""Tests for the rule-authoring workflow and the ``pks rule`` CLI."""

from __future__ import annotations

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository
from propstore.app.rules import (
    RuleAddRequest,
    RuleFileNotFoundError,
    RuleNotFoundError,
    RuleReferencedError,
    RuleRemoveRequest,
    RuleWorkflowError,
    add_rule,
    list_rules,
    parse_atom,
    remove_rule,
    show_rule_file,
)


def _read_rule_file(repo: Repository, file: str) -> dict:
    return yaml.safe_load(repo.git.read_file(f"rules/{file}.yaml"))


def test_parse_atom_variables_and_negation() -> None:
    atom = parse_atom("~reduces_mi(X)")
    assert atom.predicate == "reduces_mi"
    assert atom.negated is True
    assert len(atom.terms) == 1
    assert atom.terms[0].kind == "var"
    assert atom.terms[0].name == "X"


def test_parse_atom_constant_and_quoted() -> None:
    atom = parse_atom('dose(X, "low")')
    assert atom.predicate == "dose"
    assert atom.negated is False
    assert len(atom.terms) == 2
    assert atom.terms[0].kind == "var"
    assert atom.terms[0].name == "X"
    assert atom.terms[1].kind == "const"
    assert atom.terms[1].value == "low"


def test_parse_atom_numeric_constant() -> None:
    atom = parse_atom("dose_mg(X, 100)")
    assert atom.terms[1].kind == "const"
    assert atom.terms[1].value == 100


def test_parse_atom_zero_arity() -> None:
    atom = parse_atom("raining")
    assert atom.predicate == "raining"
    assert atom.terms == ()


def test_add_rule_creates_and_appends(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    first = add_rule(
        repo,
        RuleAddRequest(
            file="ikeda_2014",
            paper="Ikeda_2014_Low-doseAspirinPrimaryPrevention",
            rule_id="r_mi",
            kind="defeasible",
            head="reduces_mi(X)",
            body=("aspirin_user(X)",),
        ),
    )
    second = add_rule(
        repo,
        RuleAddRequest(
            file="ikeda_2014",
            paper="Ikeda_2014_Low-doseAspirinPrimaryPrevention",
            rule_id="r_bleed",
            kind="defeasible",
            head="~safe(X)",
            body=("aspirin_user(X)",),
        ),
    )

    assert first.created is True
    assert second.created is False
    data = _read_rule_file(repo, "ikeda_2014")
    assert data["source"]["paper"] == "Ikeda_2014_Low-doseAspirinPrimaryPrevention"
    ids = [entry["id"] for entry in data["rules"]]
    assert ids == ["r_mi", "r_bleed"]
    bleed = data["rules"][1]
    assert bleed["head"]["negated"] is True
    assert bleed["head"]["predicate"] == "safe"


def test_add_rule_rejects_mismatched_paper(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_rule(
        repo,
        RuleAddRequest(
            file="foo",
            paper="PaperA",
            rule_id="r1",
            kind="strict",
            head="a",
        ),
    )
    try:
        add_rule(
            repo,
            RuleAddRequest(
                file="foo",
                paper="PaperB",
                rule_id="r2",
                kind="strict",
                head="b",
            ),
        )
    except RuleWorkflowError as exc:
        assert "paper" in str(exc)
    else:
        raise AssertionError("expected paper-mismatch failure")


def test_add_rule_rejects_unknown_kind(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    try:
        add_rule(
            repo,
            RuleAddRequest(
                file="foo",
                paper="P",
                rule_id="r1",
                kind="bogus",
                head="a",
            ),
        )
    except RuleWorkflowError as exc:
        assert "kind" in str(exc)
    else:
        raise AssertionError("expected kind failure")


def test_rule_cli_add(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "rule",
            "add",
            "--file",
            "ikeda_2014",
            "--paper",
            "Ikeda_2014",
            "--id",
            "r_mi",
            "--kind",
            "defeasible",
            "--head",
            "reduces_mi(X)",
            "--body",
            "aspirin_user(X)",
        ],
    )

    assert result.exit_code == 0, result.output
    target = repo.root / "rules" / "ikeda_2014.yaml"
    assert not target.exists()
    data = _read_rule_file(repo, "ikeda_2014")
    assert data["source"]["paper"] == "Ikeda_2014"
    assert data["rules"][0]["id"] == "r_mi"
    assert data["rules"][0]["kind"] == "defeasible"
    assert data["rules"][0]["head"]["predicate"] == "reduces_mi"


def test_rule_owner_list_and_show(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_rule(
        repo,
        RuleAddRequest(
            file="ikeda_2014",
            paper="Ikeda_2014",
            rule_id="r_mi",
            kind="defeasible",
            head="reduces_mi(X)",
        ),
    )

    items = list_rules(repo)
    shown = show_rule_file(repo, "ikeda_2014")

    assert [(item.file, item.rule_id) for item in items] == [("ikeda_2014", "r_mi")]
    assert "rules:" in shown.rendered

    try:
        show_rule_file(repo, "missing")
    except RuleFileNotFoundError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected missing rule file failure")


def test_rule_cli_list_and_show(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_rule(
        repo,
        RuleAddRequest(
            file="ikeda_2014",
            paper="Ikeda_2014",
            rule_id="r_mi",
            kind="defeasible",
            head="reduces_mi(X)",
        ),
    )
    runner = CliRunner()

    listed = runner.invoke(cli, ["-C", str(repo.root), "rule", "list"])
    shown = runner.invoke(cli, ["-C", str(repo.root), "rule", "show", "ikeda_2014"])

    assert listed.exit_code == 0, listed.output
    assert "ikeda_2014" in listed.output
    assert "r_mi" in listed.output
    assert shown.exit_code == 0, shown.output
    assert "rules:" in shown.output


def test_remove_rule_rejects_missing_file(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    try:
        remove_rule(
            repo,
            RuleRemoveRequest(file="missing", rule_id="r_mi"),
        )
    except RuleFileNotFoundError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected missing-file failure")


def test_remove_rule_rejects_unknown_id(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_rule(
        repo,
        RuleAddRequest(
            file="ikeda_2014",
            paper="Ikeda_2014",
            rule_id="r_mi",
            kind="defeasible",
            head="reduces_mi(X)",
        ),
    )
    try:
        remove_rule(
            repo,
            RuleRemoveRequest(file="ikeda_2014", rule_id="r_nope"),
        )
    except RuleNotFoundError as exc:
        assert "r_nope" in str(exc)
        assert "ikeda_2014" in str(exc)
    else:
        raise AssertionError("expected unknown-id failure")


def test_remove_rule_removes_and_preserves_others(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_rule(
        repo,
        RuleAddRequest(
            file="ikeda_2014",
            paper="Ikeda_2014",
            rule_id="r_mi",
            kind="defeasible",
            head="reduces_mi(X)",
            body=("aspirin_user(X)",),
        ),
    )
    add_rule(
        repo,
        RuleAddRequest(
            file="ikeda_2014",
            paper="Ikeda_2014",
            rule_id="r_bleed",
            kind="defeasible",
            head="~safe(X)",
            body=("aspirin_user(X)",),
        ),
    )

    report = remove_rule(
        repo,
        RuleRemoveRequest(file="ikeda_2014", rule_id="r_mi"),
    )
    assert report.removed is True

    data = _read_rule_file(repo, "ikeda_2014")
    ids = [entry["id"] for entry in data["rules"]]
    assert ids == ["r_bleed"]
    assert data["source"]["paper"] == "Ikeda_2014"


def test_remove_rule_rejects_when_referenced_by_superiority(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_rule(
        repo,
        RuleAddRequest(
            file="ikeda_2014",
            paper="Ikeda_2014",
            rule_id="r_a",
            kind="defeasible",
            head="a",
        ),
    )
    add_rule(
        repo,
        RuleAddRequest(
            file="ikeda_2014",
            paper="Ikeda_2014",
            rule_id="r_b",
            kind="defeasible",
            head="b",
        ),
    )
    # Mutate the file to install a superiority pair.
    from propstore.families.documents.rules import RulesFileDocument
    from propstore.families.registry import RuleFileRef

    ref = RuleFileRef("ikeda_2014")
    document = repo.families.rules.require(ref)
    updated = RulesFileDocument(
        source=document.source,
        rules=document.rules,
        superiority=(("r_a", "r_b"),),
    )
    repo.families.rules.save(ref, updated, message="install superiority")
    repo.snapshot.sync_worktree()

    try:
        remove_rule(
            repo,
            RuleRemoveRequest(file="ikeda_2014", rule_id="r_a"),
        )
    except RuleReferencedError as exc:
        assert "r_a" in str(exc)
        assert "superiority" in str(exc)
    else:
        raise AssertionError("expected superiority-reference failure")


def test_rule_cli_remove(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_rule(
        repo,
        RuleAddRequest(
            file="ikeda_2014",
            paper="Ikeda_2014",
            rule_id="r_mi",
            kind="defeasible",
            head="reduces_mi(X)",
        ),
    )
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "rule",
            "remove",
            "--file",
            "ikeda_2014",
            "--id",
            "r_mi",
        ],
    )

    assert result.exit_code == 0, result.output
    data = _read_rule_file(repo, "ikeda_2014")
    assert data["rules"] == [] or data.get("rules") is None
