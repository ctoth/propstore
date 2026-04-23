"""Tests for the rule-authoring workflow and the ``pks rule`` CLI."""

from __future__ import annotations

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository
from propstore.rule_workflows import (
    RuleAddRequest,
    RuleWorkflowError,
    add_rule,
    parse_atom,
)


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
    data = yaml.safe_load(first.filepath.read_text(encoding="utf-8"))
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
    assert target.exists()
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert data["source"]["paper"] == "Ikeda_2014"
    assert data["rules"][0]["id"] == "r_mi"
    assert data["rules"][0]["kind"] == "defeasible"
    assert data["rules"][0]["head"]["predicate"] == "reduces_mi"
