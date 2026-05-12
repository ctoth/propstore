from __future__ import annotations

from click.testing import CliRunner

from propstore.app.predicates import PredicateAddRequest, add_predicate
from propstore.app.rules import (
    RuleAddRequest,
    RuleSuperiorityAddRequest,
    RuleSuperiorityRemoveRequest,
    RuleWorkflowError,
    add_rule,
    add_rule_superiority,
    list_rule_superiority,
    remove_rule_superiority,
)
from propstore.cli import cli
from propstore.families.documents.rules import RuleSuperiorityDocument
from propstore.families.registry import RuleSuperiorityRef
from propstore.repository import Repository


def _declare_predicates(repo: Repository) -> None:
    for predicate_id in ("a", "b", "c", "bird", "penguin", "flies"):
        add_predicate(
            repo,
            PredicateAddRequest(file="test", predicate_id=predicate_id, arity=0),
        )


def _declare_rules(repo: Repository) -> None:
    _declare_predicates(repo)
    add_rule(repo, RuleAddRequest(file="test", paper="Paper", rule_id="r_a", kind="defeasible", head="a"))
    add_rule(repo, RuleAddRequest(file="test", paper="Paper", rule_id="r_b", kind="defeasible", head="b"))
    add_rule(repo, RuleAddRequest(file="test", paper="Paper", rule_id="r_c", kind="blocking_defeater", head="c"))
    add_rule(repo, RuleAddRequest(file="test", paper="Paper", rule_id="r_strict", kind="strict", head="a"))


def test_add_rule_superiority_writes_one_artifact(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _declare_rules(repo)

    report = add_rule_superiority(
        repo,
        RuleSuperiorityAddRequest(
            file="paper-group",
            superior_rule_id="r_b",
            inferior_rule_id="r_a",
        ),
    )

    assert report.superior_rule_id == "r_b"
    assert report.inferior_rule_id == "r_a"
    document = repo.families.rule_superiority.require(RuleSuperiorityRef("r_b__gt__r_a"))
    assert document.superior_rule_id == "r_b"
    assert document.inferior_rule_id == "r_a"
    assert document.authoring_group == "paper-group"
    assert repo.families.rules.ref_from_path("rules/r_b.yaml").rule_id == "r_b"


def test_list_and_remove_rule_superiority_operate_on_artifacts(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _declare_rules(repo)
    add_rule_superiority(
        repo,
        RuleSuperiorityAddRequest(file=None, superior_rule_id="r_c", inferior_rule_id="r_a"),
    )

    items = list_rule_superiority(repo)
    assert [(item.superior_rule_id, item.inferior_rule_id) for item in items] == [("r_c", "r_a")]

    report = remove_rule_superiority(
        repo,
        RuleSuperiorityRemoveRequest(file=None, superior_rule_id="r_c", inferior_rule_id="r_a"),
    )
    assert report.superior_rule_id == "r_c"
    assert repo.families.rule_superiority.load(RuleSuperiorityRef("r_c__gt__r_a")) is None


def test_rule_superiority_rejects_unknown_and_strict_rules(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _declare_rules(repo)

    for superior, inferior, message in (
        ("missing", "r_a", "not found"),
        ("r_b", "missing", "not found"),
        ("r_b", "r_strict", "strict"),
        ("r_strict", "r_b", "strict"),
    ):
        try:
            add_rule_superiority(
                repo,
                RuleSuperiorityAddRequest(
                    file=None,
                    superior_rule_id=superior,
                    inferior_rule_id=inferior,
                ),
            )
        except RuleWorkflowError as exc:
            assert message in str(exc)
        else:
            raise AssertionError("expected superiority validation failure")


def test_rule_superiority_rejects_cycles_across_artifacts(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _declare_rules(repo)
    add_rule_superiority(
        repo,
        RuleSuperiorityAddRequest(file=None, superior_rule_id="r_b", inferior_rule_id="r_a"),
    )
    add_rule_superiority(
        repo,
        RuleSuperiorityAddRequest(file=None, superior_rule_id="r_c", inferior_rule_id="r_b"),
    )

    try:
        add_rule_superiority(
            repo,
            RuleSuperiorityAddRequest(file=None, superior_rule_id="r_a", inferior_rule_id="r_c"),
        )
    except RuleWorkflowError as exc:
        assert "acyclic" in str(exc)
    else:
        raise AssertionError("expected cycle failure")


def test_rule_superiority_cli_add_list_remove(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _declare_rules(repo)
    runner = CliRunner()

    added = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "rule",
            "superiority",
            "add",
            "--file",
            "paper-group",
            "--superior",
            "r_b",
            "--inferior",
            "r_a",
        ],
    )
    listed = runner.invoke(cli, ["-C", str(repo.root), "rule", "superiority", "list"])
    removed = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "rule",
            "superiority",
            "remove",
            "--superior",
            "r_b",
            "--inferior",
            "r_a",
        ],
    )

    assert added.exit_code == 0, added.output
    assert listed.exit_code == 0, listed.output
    assert "r_b" in listed.output
    assert "r_a" in listed.output
    assert removed.exit_code == 0, removed.output
    assert repo.families.rule_superiority.load(RuleSuperiorityRef("r_b__gt__r_a")) is None


def test_translate_to_theory_consumes_rule_superiority_artifacts() -> None:
    from propstore.families.documents.rules import AtomDocument, RuleDocument
    from propstore.grounding.predicates import PredicateRegistry
    from propstore.grounding.translator import translate_to_theory

    generic = RuleDocument(
        id="r1",
        kind="defeasible",
        head=AtomDocument(predicate="flies"),
    )
    specific = RuleDocument(
        id="r2",
        kind="defeasible",
        head=AtomDocument(predicate="flies", negated=True),
    )
    superiority = RuleSuperiorityDocument(
        superior_rule_id="r2",
        inferior_rule_id="r1",
    )

    theory = translate_to_theory((generic, specific), (), PredicateRegistry(()), superiority=(superiority,))

    assert theory.superiority == (("r2", "r1"),)


def test_grounding_inputs_load_rule_superiority_artifacts(tmp_path) -> None:
    from propstore.grounding.loading import load_grounding_inputs

    repo = Repository.init(tmp_path / "knowledge")
    _declare_rules(repo)
    add_rule_superiority(
        repo,
        RuleSuperiorityAddRequest(file=None, superior_rule_id="r_b", inferior_rule_id="r_a"),
    )

    inputs = load_grounding_inputs(repo)

    assert [(item.superior_rule_id, item.inferior_rule_id) for item in inputs.superiority] == [
        ("r_b", "r_a")
    ]
