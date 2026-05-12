"""Tests for the rule-authoring workflow and the ``pks rule`` CLI."""

from __future__ import annotations

from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository
from propstore.app.predicates import PredicateAddRequest, add_predicate
from propstore.app.rules import (
    RuleAddRequest,
    RuleNotFoundError,
    RuleRemoveRequest,
    RuleWorkflowError,
    add_rule,
    list_rules,
    parse_atom,
    remove_rule,
    show_rule,
)
from propstore.families.registry import RuleRef


def _read_rule_artifact(repo: Repository, rule_id: str):
    return repo.families.rules.require(RuleRef(rule_id))


def _declare_rule_predicates(repo: Repository, file: str = "ikeda_2014") -> None:
    for predicate_id, arity in (
        ("a", 0),
        ("b", 0),
        ("reduces_mi", 1),
        ("aspirin_user", 1),
        ("safe", 1),
    ):
        add_predicate(
            repo,
            PredicateAddRequest(
                file=file,
                predicate_id=predicate_id,
                arity=arity,
            ),
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


def test_add_rule_creates_one_artifact_per_rule(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _declare_rule_predicates(repo)

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
    assert second.created is True
    mi = _read_rule_artifact(repo, "r_mi")
    bleed = _read_rule_artifact(repo, "r_bleed")
    assert mi.source is not None
    assert mi.source.paper == "Ikeda_2014_Low-doseAspirinPrimaryPrevention"
    assert mi.authoring_group == "ikeda_2014"
    assert bleed.head.negated is True
    assert bleed.head.predicate == "safe"


def test_add_rule_rejects_duplicate_id_with_different_paper(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _declare_rule_predicates(repo, "foo")
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
                rule_id="r1",
                kind="strict",
                head="b",
            ),
        )
    except RuleWorkflowError as exc:
        assert "already declared" in str(exc)
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
    _declare_rule_predicates(repo)
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
    artifact = _read_rule_artifact(repo, "r_mi")
    assert artifact.source is not None
    assert artifact.source.paper == "Ikeda_2014"
    assert artifact.id == "r_mi"
    assert artifact.kind == "defeasible"
    assert artifact.head.predicate == "reduces_mi"


def test_rule_owner_list_and_show(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _declare_rule_predicates(repo)
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
    shown = show_rule(repo, "r_mi")

    assert [(item.authoring_group, item.rule_id) for item in items] == [("ikeda_2014", "r_mi")]
    assert "id: r_mi" in shown.rendered

    try:
        show_rule(repo, "missing")
    except RuleNotFoundError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected missing rule file failure")


def test_rule_cli_list_and_show(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _declare_rule_predicates(repo)
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
    shown = runner.invoke(cli, ["-C", str(repo.root), "rule", "show", "r_mi"])

    assert listed.exit_code == 0, listed.output
    assert "ikeda_2014" in listed.output
    assert "r_mi" in listed.output
    assert shown.exit_code == 0, shown.output
    assert "id: r_mi" in shown.output


def test_remove_rule_rejects_missing_rule(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    try:
        remove_rule(
            repo,
            RuleRemoveRequest(rule_id="r_mi"),
        )
    except RuleNotFoundError as exc:
        assert "r_mi" in str(exc)
    else:
        raise AssertionError("expected missing-file failure")


def test_remove_rule_rejects_unknown_id(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _declare_rule_predicates(repo)
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
            RuleRemoveRequest(rule_id="r_nope"),
        )
    except RuleNotFoundError as exc:
        assert "r_nope" in str(exc)
    else:
        raise AssertionError("expected unknown-id failure")


def test_remove_rule_removes_and_preserves_others(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _declare_rule_predicates(repo)
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
        RuleRemoveRequest(rule_id="r_mi"),
    )
    assert report.removed is True

    assert repo.families.rules.load(RuleRef("r_mi")) is None
    assert repo.families.rules.load(RuleRef("r_bleed")) is not None


def test_rule_cli_remove(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _declare_rule_predicates(repo)
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
            "--id",
            "r_mi",
        ],
    )

    assert result.exit_code == 0, result.output
    assert repo.families.rules.load(RuleRef("r_mi")) is None
