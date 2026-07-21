"""CLI adapter tests for the Phase 10-1 advanced command families.

Exercises the thin Click adapters end-to-end through the root ``cli`` lazy
registry (``-C`` points it at the on-disk repo) against the real owner tier:

* ``pks predicate`` — read over ``repo.families.predicate`` plus the predicate
  proposal record/promote path (:mod:`propstore.proposals_predicates`);
* ``pks rule`` — read over the DeLP rule families;
* ``pks proposal`` — stance + predicate proposal promotion
  (:mod:`propstore.proposals`, :mod:`propstore.proposals_predicates`);
* ``pks micropub`` — read over ``repo.families.micropublication``.

The micropub list/show cases are ported from the reference ``test_micropubs`` CLI
suite (the ``lift`` case is deferred: no ``inspect_micropub_lift`` owner exists in
the rewrite). Rule mutation and the LLM rule-extraction proposal path
(``propose-rules`` / ``promote-rules``) have no rewrite owner and are likewise not
exercised here.
"""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner, Result
from doxa import Opinion

from propstore.cli import cli
from propstore.families.claims import Claim, ClaimType
from propstore.families.contexts import Context
from propstore.families.micropublications import Micropublication
from propstore.families.predicates import Predicate
from propstore.families.rules import Atom, DefeasibleRule, RuleSuperiority, Term
from propstore.proposals import commit_stance_proposal
from propstore.repository import Repository
from propstore.stances import StanceType

PAPER = "Ioannidis_2005_WhyMostPublishedResearch"


def _invoke(repo: Repository, args: list[str]) -> Result:
    return CliRunner().invoke(cli, ["-C", str(repo.root), *args])


def _repo(tmp_path: Path) -> Repository:
    return Repository.init(tmp_path / "knowledge")


# --- predicate read ------------------------------------------------------------


def _seed_predicate(repo: Repository) -> None:
    repo.families.predicate.save(
        "sample_size",
        Predicate(
            predicate_id="sample_size",
            arity=2,
            arg_types=("paper_id", "int"),
            description="Paper-level sample size.",
            authoring_group=PAPER,
        ),
        message="seed predicate",
    )


def test_predicate_list_and_show(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _seed_predicate(repo)

    listed = _invoke(repo, ["predicate", "list"])
    assert listed.exit_code == 0, listed.output
    assert "sample_size" in listed.output
    assert "paper_id, int" in listed.output

    shown = _invoke(repo, ["predicate", "show", "sample_size"])
    assert shown.exit_code == 0, shown.output
    assert "predicate_id: sample_size" in shown.output


def test_predicate_list_empty(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    result = _invoke(repo, ["predicate", "list"])
    assert result.exit_code == 0, result.output
    assert "No predicates declared." in result.output


def test_predicate_show_unknown_fails(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    result = _invoke(repo, ["predicate", "show", "nope"])
    assert result.exit_code != 0
    assert "not found" in result.output


# --- predicate declare / promote ----------------------------------------------


def test_predicate_declare_then_promote(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    declared = _invoke(
        repo,
        [
            "predicate",
            "declare",
            "--paper",
            PAPER,
            "--name",
            "statistical_power",
            "--arity",
            "2",
            "--arg-type",
            "paper_id",
            "--arg-type",
            "float",
            "--description",
            "Paper-level statistical power.",
            "--date",
            "2026-06-30",
        ],
    )
    assert declared.exit_code == 0, declared.output
    assert "statistical_power/2" in declared.output
    assert "proposal/predicates" in declared.output
    # Nothing canonical yet.
    assert list(repo.families.predicate.iter_refs()) == []

    promoted = _invoke(repo, ["predicate", "promote", "--paper", PAPER])
    assert promoted.exit_code == 0, promoted.output
    assert "Promoted: statistical_power" in promoted.output
    assert repo.families.predicate.require("statistical_power").authoring_group == PAPER


def test_predicate_declare_bad_arity_fails(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    result = _invoke(
        repo,
        [
            "predicate",
            "declare",
            "--paper",
            PAPER,
            "--name",
            "bad",
            "--arity",
            "2",
            "--arg-type",
            "paper_id",
            "--description",
            "mismatched arity",
            "--date",
            "2026-06-30",
        ],
    )
    assert result.exit_code != 0
    assert "does not match arity" in result.output


def test_predicate_promote_unknown_paper_fails(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    # Seed a proposal so the branch exists, then promote a different paper.
    _invoke(
        repo,
        [
            "predicate",
            "declare",
            "--paper",
            PAPER,
            "--name",
            "sample_size",
            "--arity",
            "2",
            "--arg-type",
            "paper_id",
            "--arg-type",
            "int",
            "--description",
            "Sample size.",
            "--date",
            "2026-06-30",
        ],
    )
    result = _invoke(repo, ["predicate", "promote", "--paper", "missing_paper"])
    assert result.exit_code != 0
    assert "missing_paper" in result.output


# --- rule read -----------------------------------------------------------------


def _seed_rule(repo: Repository) -> None:
    repo.families.defeasible_rule.save(
        "r_demo",
        DefeasibleRule(
            rule_id="r_demo",
            kind="defeasible",
            head=Atom(predicate="reliable", terms=(Term(kind="var", name="P"),)),
            source=PAPER,
            authoring_group=PAPER,
        ),
        message="seed rule",
    )
    repo.families.defeasible_rule.save(
        "r_other",
        DefeasibleRule(
            rule_id="r_other",
            kind="strict",
            head=Atom(predicate="unreliable", terms=(Term(kind="var", name="P"),)),
            authoring_group=PAPER,
        ),
        message="seed rule 2",
    )
    repo.families.rule_superiority.save(
        "sup_demo",
        RuleSuperiority(
            superiority_id="sup_demo",
            superior_rule_id="r_demo",
            inferior_rule_id="r_other",
            authoring_group=PAPER,
        ),
        message="seed superiority",
    )


def test_rule_list_and_show(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _seed_rule(repo)

    listed = _invoke(repo, ["rule", "list"])
    assert listed.exit_code == 0, listed.output
    assert "r_demo" in listed.output
    assert "defeasible" in listed.output
    assert "sup_demo" in listed.output

    shown = _invoke(repo, ["rule", "show", "r_demo"])
    assert shown.exit_code == 0, shown.output
    assert "rule_id: r_demo" in shown.output

    shown_sup = _invoke(repo, ["rule", "show", "sup_demo"])
    assert shown_sup.exit_code == 0, shown_sup.output
    assert "superiority_id: sup_demo" in shown_sup.output


def test_rule_list_empty(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    result = _invoke(repo, ["rule", "list"])
    assert result.exit_code == 0, result.output
    assert "No rules authored." in result.output


def test_rule_show_unknown_fails(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    result = _invoke(repo, ["rule", "show", "nope"])
    assert result.exit_code != 0
    assert "not found" in result.output


# --- proposal promote (stance) -------------------------------------------------


def _seed_stance_proposal(repo: Repository) -> str:
    for claim_id in ("claim_a", "claim_b"):
        repo.families.claim.save(
            claim_id, Claim(claim_id=claim_id), message=f"seed {claim_id}"
        )
    return commit_stance_proposal(
        repo,
        source_claim_id="claim_a",
        target_claim_id="claim_b",
        stance_type=StanceType.SUPPORTS,
        resolution_model="test-model",
        confidence=0.7,
        opinion=Opinion(0.7, 0.1, 0.2, 0.5),
    )


def test_proposal_promote_stance(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    stance_id = _seed_stance_proposal(repo)

    result = _invoke(repo, ["proposal", "promote", "--yes"])
    assert result.exit_code == 0, result.output
    assert "Promoted 1 of 1 stance proposal(s)." in result.output
    assert repo.families.stance.require(stance_id).stance_type is StanceType.SUPPORTS


def test_proposal_promote_no_branch(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    result = _invoke(repo, ["proposal", "promote", "--yes"])
    assert result.exit_code == 0, result.output
    assert "Nothing to promote." in result.output


def test_proposal_promote_unknown_stance_fails(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _seed_stance_proposal(repo)
    result = _invoke(
        repo, ["proposal", "promote", "--stance-id", "ps:stance:typo", "--yes"]
    )
    assert result.exit_code != 0
    assert "ps:stance:typo" in result.output


# --- proposal predicates promote ----------------------------------------------


def test_proposal_predicates_promote(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _invoke(
        repo,
        [
            "predicate",
            "declare",
            "--paper",
            PAPER,
            "--name",
            "sample_size",
            "--arity",
            "2",
            "--arg-type",
            "paper_id",
            "--arg-type",
            "int",
            "--description",
            "Sample size.",
            "--date",
            "2026-06-30",
        ],
    )
    result = _invoke(repo, ["proposal", "predicates", "promote", "--paper", PAPER])
    assert result.exit_code == 0, result.output
    assert "Promoted: sample_size" in result.output
    assert repo.families.predicate.require("sample_size").authoring_group == PAPER


# --- micropub read (ported from reference test_micropubs CLI list/show) --------


def _seed_micropub(repo: Repository) -> None:
    repo.families.context.save(
        "ctx_source", Context(context_id="ctx_source", name="Source"), message="ctx"
    )
    repo.families.claim.save(
        "claim_one",
        Claim(
            claim_id="claim_one",
            context_id="ctx_source",
            claim_type=ClaimType.OBSERVATION,
            statement="x",
        ),
        message="claim",
    )
    repo.families.micropublication.save(
        "ps:micropub:test",
        Micropublication(
            artifact_id="ps:micropub:test",
            context_id="ctx_source",
            claims=("claim_one",),
            source="demo",
        ),
        message="seed micropub",
    )


def test_micropub_list_and_show(tmp_path: Path) -> None:
    repo = _seed_micropub_repo(tmp_path)

    listed = _invoke(repo, ["micropub", "list"])
    assert listed.exit_code == 0, listed.output
    assert "ps:micropub:test" in listed.output
    assert "demo" in listed.output

    shown = _invoke(repo, ["micropub", "show", "ps:micropub:test"])
    assert shown.exit_code == 0, shown.output
    assert "claims:" in shown.output
    assert "ps:micropub:test" in shown.output


def test_micropub_list_empty(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    result = _invoke(repo, ["micropub", "list"])
    assert result.exit_code == 0, result.output
    assert "No micropublications." in result.output


def test_micropub_show_unknown_fails(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    result = _invoke(repo, ["micropub", "show", "ps:micropub:missing"])
    assert result.exit_code != 0
    assert "not found" in result.output


def _seed_micropub_repo(tmp_path: Path) -> Repository:
    repo = _repo(tmp_path)
    _seed_micropub(repo)
    return repo
