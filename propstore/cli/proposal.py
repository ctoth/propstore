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
(``propose-rules`` / ``promote-rules``) depend on the Phase 10-4 LLM
rule-extraction path and the rule-proposal family, neither of which exists in the
rewrite, so they are deferred rather than fabricated.
"""
from __future__ import annotations

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
