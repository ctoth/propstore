"""``pks predicate declare`` / ``promote`` — the predicate proposal record/promote
path.

Thin adapters over :mod:`propstore.proposals_predicates`: ``declare`` records an
explicitly-supplied (``stated``) predicate declaration on the proposal branch via
:func:`~propstore.proposals_predicates.propose_predicates`; ``promote`` runs the
explicit accept-then-promote path
(:func:`~propstore.proposals_predicates.plan_predicate_proposal_promotion` then
:func:`~propstore.proposals_predicates.promote_predicate_proposals`). The proposal
recorder and promoter own all storage semantics; this module only builds the typed
inputs and maps typed owner failures to clean CLI errors (CLAUDE.md "CLI adapter
discipline"). The LLM extraction that *produces* declarations is Phase 10-4 and is
not built here.
"""

from __future__ import annotations

import click

from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit, emit_success
from propstore.cli.predicate import predicate
from propstore.families.predicates import (
    PredicateDeclaration,
    PredicateExtractionProvenance,
)
from propstore.proposal_promotion import UnknownProposalPath
from propstore.proposals_predicates import (
    PredicateProposalConflict,
    plan_predicate_proposal_promotion,
    promote_predicate_proposals,
    propose_predicates,
)


@predicate.command("declare")
@click.option("--paper", required=True, help="Source paper the declaration belongs to.")
@click.option("--name", required=True, help="Predicate name (e.g. sample_size).")
@click.option(
    "--arity",
    required=True,
    type=int,
    help="Non-negative number of argument positions.",
)
@click.option(
    "--arg-type",
    "arg_type",
    multiple=True,
    help="Per-position sort. Repeat once per position; total must equal --arity.",
)
@click.option("--description", required=True, help="Human-readable explanation.")
@click.option(
    "--date",
    "extraction_date",
    required=True,
    help="Authoring date recorded with the proposal (e.g. 2026-06-30).",
)
@click.pass_obj
def predicate_declare(
    obj: CliContext,
    paper: str,
    name: str,
    arity: int,
    arg_type: tuple[str, ...],
    description: str,
    extraction_date: str,
) -> None:
    """Record one stated predicate declaration on the proposal branch."""

    repo = require_repo(obj)
    try:
        declaration = PredicateDeclaration(
            name=name,
            arity=arity,
            arg_types=tuple(arg_type),
            description=description,
        )
    except ValueError as exc:
        fail(exc)
    provenance = PredicateExtractionProvenance(
        operations=("predicate-declare",),
        agent="pks-cli",
        model="manual",
        prompt_sha="",
        notes_sha="",
        status="stated",
    )
    commit_sha = propose_predicates(
        repo,
        source_paper=paper,
        declarations=(declaration,),
        extraction_provenance=provenance,
        extraction_date=extraction_date,
    )
    emit(f"{declaration.name}/{declaration.arity} {tuple(declaration.arg_types)}")
    if commit_sha is not None:
        emit_success(f"Proposal commit: {commit_sha[:8]} on proposal/predicates")


@predicate.command("promote")
@click.option("--paper", required=True, help="Source paper whose proposal to promote.")
@click.pass_obj
def predicate_promote(obj: CliContext, paper: str) -> None:
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
