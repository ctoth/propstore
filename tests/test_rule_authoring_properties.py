from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.app.predicates import PredicateAddRequest, add_predicate
from propstore.app.rules import RuleAddRequest, RuleWorkflowError, add_rule
from propstore.families.registry import RuleFileRef
from propstore.repository import Repository


_NAME = st.from_regex(r"[a-z][a-z0-9_]{0,10}", fullmatch=True)


@pytest.mark.property
@given(rule_file=_NAME, predicate_id=_NAME)
@settings(deadline=None, max_examples=15)
def test_generated_rule_add_rejects_undeclared_predicates(
    rule_file: str,
    predicate_id: str,
) -> None:
    tmp_dir = tempfile.TemporaryDirectory()
    with tmp_dir:
        repo = Repository.init(Path(tmp_dir.name) / "knowledge")
        master_before = repo.snapshot.branch_head(repo.snapshot.primary_branch_name())

        with pytest.raises(RuleWorkflowError, match="undeclared predicate"):
            add_rule(
                repo,
                RuleAddRequest(
                    file=rule_file,
                    paper=rule_file,
                    rule_id="r1",
                    kind="defeasible",
                    head=f"{predicate_id}(P)",
                ),
            )

        assert repo.snapshot.branch_head(repo.snapshot.primary_branch_name()) == master_before
        assert repo.families.rules.load(RuleFileRef(rule_file)) is None


@pytest.mark.property
@given(rule_file=_NAME, predicate_id=_NAME)
@settings(deadline=None, max_examples=15)
def test_generated_rule_add_accepts_declared_predicate_arity(
    rule_file: str,
    predicate_id: str,
) -> None:
    tmp_dir = tempfile.TemporaryDirectory()
    with tmp_dir:
        repo = Repository.init(Path(tmp_dir.name) / "knowledge")
        add_predicate(
            repo,
            PredicateAddRequest(
                file=f"{rule_file}_predicates",
                predicate_id=predicate_id,
                arity=1,
            ),
        )

        add_rule(
            repo,
            RuleAddRequest(
                file=rule_file,
                paper=rule_file,
                rule_id="r1",
                kind="defeasible",
                head=f"{predicate_id}(P)",
            ),
        )

        document = repo.families.rules.require(RuleFileRef(rule_file))
        assert document.rules[0].head.predicate == predicate_id


@pytest.mark.property
@given(rule_file=_NAME, predicate_id=_NAME)
@settings(deadline=None, max_examples=15)
def test_generated_rule_add_rejects_declared_predicate_wrong_arity(
    rule_file: str,
    predicate_id: str,
) -> None:
    tmp_dir = tempfile.TemporaryDirectory()
    with tmp_dir:
        repo = Repository.init(Path(tmp_dir.name) / "knowledge")
        add_predicate(
            repo,
            PredicateAddRequest(
                file=f"{rule_file}_predicates",
                predicate_id=predicate_id,
                arity=1,
            ),
        )
        master_before = repo.snapshot.branch_head(repo.snapshot.primary_branch_name())

        with pytest.raises(RuleWorkflowError, match="declared arity"):
            add_rule(
                repo,
                RuleAddRequest(
                    file=rule_file,
                    paper=rule_file,
                    rule_id="r1",
                    kind="defeasible",
                    head=f"{predicate_id}(P, Q)",
                ),
            )

        assert repo.snapshot.branch_head(repo.snapshot.primary_branch_name()) == master_before
        assert repo.families.rules.load(RuleFileRef(rule_file)) is None
