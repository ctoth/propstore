from __future__ import annotations

import yaml

from propstore.app.predicates import PredicateAddRequest, add_predicate
from propstore.app.rules import (
    RuleAddRequest,
    RuleNotFoundError,
    RuleRemoveRequest,
    add_rule,
    list_rules,
    remove_rule,
    show_rule,
)
from propstore.families.registry import RuleRef
from propstore.repository import Repository


def _declare_rule_predicates(repo: Repository, group: str = "ikeda_2014") -> None:
    for predicate_id, arity in (
        ("reduces_mi", 1),
        ("aspirin_user", 1),
        ("safe", 1),
    ):
        add_predicate(
            repo,
            PredicateAddRequest(
                file=group,
                predicate_id=predicate_id,
                arity=arity,
            ),
        )


def _read_rule_artifact(repo: Repository, rule_id: str) -> dict:
    return yaml.safe_load(repo.git.read_file(f"rules/{rule_id}.yaml"))


def test_add_rule_writes_one_artifact_per_rule(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _declare_rule_predicates(repo)

    first = add_rule(
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
    second = add_rule(
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

    assert first.created is True
    assert second.created is True
    assert _read_rule_artifact(repo, "r_mi")["id"] == "r_mi"
    assert _read_rule_artifact(repo, "r_mi")["authoring_group"] == "ikeda_2014"
    assert _read_rule_artifact(repo, "r_mi")["source"]["paper"] == "Ikeda_2014"
    assert _read_rule_artifact(repo, "r_bleed")["id"] == "r_bleed"
    assert repo.families.rules.require(RuleRef("r_mi")).id == "r_mi"


def test_rule_list_show_remove_operate_on_artifacts(tmp_path) -> None:
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

    assert [(item.authoring_group, item.rule_id) for item in list_rules(repo)] == [
        ("ikeda_2014", "r_mi")
    ]
    assert "id: r_mi" in show_rule(repo, "r_mi").rendered

    removed = remove_rule(repo, RuleRemoveRequest(rule_id="r_mi"))
    assert removed.removed is True
    assert repo.families.rules.load(RuleRef("r_mi")) is None

    try:
        show_rule(repo, "r_mi")
    except RuleNotFoundError as exc:
        assert "r_mi" in str(exc)
    else:
        raise AssertionError("expected missing rule artifact failure")
