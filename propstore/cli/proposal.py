"""``pks proposal`` — promote recorded proposals into the canonical corpus.

Thin Click adapters (CLAUDE.md "CLI adapter discipline") over the explicit
accept-then-promote owners:

* stance proposals — :mod:`propstore.proposals`
  (:func:`~propstore.proposals.plan_stance_proposal_promotion`,
  :func:`~propstore.proposals.promote_stance_proposals`);
* predicate proposals — :mod:`propstore.proposals_predicates`
  (:func:`~propstore.proposals_predicates.plan_predicate_proposal_promotion`,
  :func:`~propstore.proposals_predicates.promote_predicate_proposals`).

This module builds the plan, shows it, and (on confirmation) promotes it; the
owners own every storage/promotion semantic. The rule-proposal subcommands
(``propose-rules`` / ``promote-rules``) are thin adapters over
:mod:`propstore.heuristic.rule_extraction` and :mod:`propstore.proposals_rules`;
``propose-rules`` accepts a ``--mock-llm-fixture`` so it is exercisable without an
LLM endpoint.
"""
from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit, emit_success, emit_table
from propstore.proposal_promotion import UnknownProposalPath
from propstore.proposals import (
    plan_stance_proposal_promotion,
    promote_stance_proposals,
)
from propstore.proposals_predicates import (
    PredicateProposalConflict,
    plan_predicate_proposal_promotion,
    promote_predicate_proposals,
)
from propstore.proposals_rules import (
    RuleWorkflowError,
    plan_rule_proposal_promotion,
    promote_rule_proposals,
)


@click.group()
def proposal() -> None:
    """Promote recorded stance and predicate proposals into storage."""


@proposal.command("promote")
@click.option(
    "--stance-id",
    "stance_id",
    default=None,
    help="Promote only this stance proposal (default: every recorded proposal).",
)
@click.option("-y", "--yes", is_flag=True, help="Skip the confirmation prompt.")
@click.pass_obj
def promote(obj: CliContext, stance_id: str | None, yes: bool) -> None:
    """Promote recorded stance proposals into canonical stances."""

    repo = require_repo(obj)
    try:
        plan = plan_stance_proposal_promotion(repo, stance_id=stance_id)
    except UnknownProposalPath as exc:
        fail(exc)
    if not plan.has_branch:
        emit(f"No {plan.branch} branch found. Nothing to promote.")
        return
    if not plan.items:
        emit(f"No stance proposals found on {plan.branch}.")
        return

    emit_table(
        ("STANCE", "SOURCE CLAIM"),
        [(item.stance_id, item.source_claim) for item in plan.items],
    )
    if not yes:
        click.confirm("Promote these proposals?", abort=True)

    result = promote_stance_proposals(repo, plan)
    for item in result.promoted_items:
        emit_success(f"  Promoted: {item.stance_id}")
    emit_success(f"Promoted {result.moved} of {len(plan.items)} stance proposal(s).")


@proposal.group("predicates")
def predicates() -> None:
    """Promote recorded predicate proposals."""


@predicates.command("promote")
@click.option("--paper", required=True, help="Source paper whose proposal to promote.")
@click.pass_obj
def promote_predicates_cmd(obj: CliContext, paper: str) -> None:
    """Promote a recorded predicate proposal into canonical predicates."""

    repo = require_repo(obj)
    try:
        plan = plan_predicate_proposal_promotion(repo, source_paper=paper)
    except UnknownProposalPath as exc:
        fail(exc)
    if not plan.has_branch:
        emit(f"No {plan.branch} branch found. Nothing to promote.")
        return
    if not plan.items:
        emit(f"No predicate proposals to promote for {paper}.")
        return
    try:
        result = promote_predicate_proposals(repo, plan)
    except PredicateProposalConflict as exc:
        fail(exc)
    for item in result.promoted_items:
        emit_success(f"  Promoted: {item.predicate_id}")
    emit_success(f"Promoted {result.moved} predicate proposal(s).")


@proposal.command("propose-rules")
@click.option("--paper", required=True, help="Source paper to extract rules from.")
@click.option(
    "--model",
    "model_name",
    default="heuristic-llm",
    show_default=True,
    help="LLM model name recorded as extraction provenance.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Parse and plan the extraction without recording any proposal.",
)
@click.option(
    "--mock-llm-fixture",
    "mock_llm_fixture",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Read the LLM response from this JSON file instead of calling a model.",
)
@click.pass_obj
def propose_rules_cmd(
    obj: CliContext,
    paper: str,
    model_name: str,
    dry_run: bool,
    mock_llm_fixture: Path | None,
) -> None:
    """Extract candidate DeLP rules for a paper and record them as proposals."""

    from propstore.heuristic.rule_extraction import propose_rules_for_paper

    repo = require_repo(obj)
    llm_response = (
        mock_llm_fixture.read_text(encoding="utf-8")
        if mock_llm_fixture is not None
        else None
    )
    try:
        result = propose_rules_for_paper(
            repo,
            source_paper=paper,
            model_name=model_name,
            dry_run=dry_run,
            llm_response=llm_response,
        )
    except (ValueError, RuntimeError) as exc:
        fail(exc)

    if result.rule_ids:
        emit_table(
            ("RULE", "PATH"),
            list(zip(result.rule_ids, result.relpaths, strict=True)),
        )
    else:
        emit("No rules admitted.")
    for rejection in result.rejections:
        emit(
            f"  Rejected {rejection.rule_id}: {rejection.reason} "
            f"({', '.join(rejection.predicates_referenced)})"
        )
    if dry_run:
        emit_success(f"Dry run: {len(result.rule_ids)} rule proposal(s) planned.")
        return
    emit_success(f"Recorded {len(result.rule_ids)} rule proposal(s) for {paper}.")


@proposal.command("promote-rules")
@click.option("--paper", required=True, help="Source paper whose rules to promote.")
@click.option(
    "--rule-id",
    "rule_ids",
    multiple=True,
    required=True,
    help="A rule id to promote (repeatable).",
)
@click.pass_obj
def promote_rules_cmd(
    obj: CliContext, paper: str, rule_ids: tuple[str, ...]
) -> None:
    """Promote recorded rule proposals into canonical defeasible rules."""

    repo = require_repo(obj)
    try:
        plan = plan_rule_proposal_promotion(
            repo, source_paper=paper, rule_ids=rule_ids
        )
    except UnknownProposalPath as exc:
        fail(exc)
    if not plan.has_branch:
        emit(f"No {plan.branch} branch found. Nothing to promote.")
        return
    if not plan.items:
        emit(f"No rule proposals to promote for {paper}.")
        return
    try:
        result = promote_rule_proposals(repo, plan)
    except RuleWorkflowError as exc:
        fail(exc)
    for item in result.promoted_items:
        emit_success(f"  Promoted: {item.rule_id}")
    emit_success(f"Promoted {result.moved} rule proposal(s).")
