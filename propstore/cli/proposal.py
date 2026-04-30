"""pks proposal - proposal promotion commands."""

from __future__ import annotations

import click
from pathlib import Path

from propstore.app.proposals import (
    ProposalPromotionRequest,
    plan_proposal_promotion,
    promote_proposals,
)
from propstore.cli.output import emit, emit_success, emit_table
from propstore.proposals import UnknownProposalPath


@click.group()
def proposal() -> None:
    """Manage proposal branches and proposal artifacts."""


@proposal.command("promote")
@click.argument("path", required=False, default=None, type=click.Path())
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def promote(ctx: click.Context, path: str | None, yes: bool) -> None:
    """Promote committed stance proposals into source-of-truth storage."""
    repo = ctx.obj["repo"]
    plan = plan_proposal_promotion(repo, ProposalPromotionRequest(path=path))
    if not plan.has_branch:
        emit(f"No {plan.branch} branch found. Nothing to promote.")
        return

    if not plan.items:
        emit(f"No stance proposal files found on {plan.branch}.")
        return

    emit_table(
        ("SOURCE", "TARGET"),
        [(item.source_relpath, item.target_path) for item in plan.items],
    )

    if not yes:
        click.confirm("Promote these files?", abort=True)

    result = promote_proposals(repo, plan)
    for item in result.promoted_items:
        emit_success(f"  Promoted: {item.filename}")

    emit_success(f"\nPromoted {result.moved} of {len(plan.items)} file(s).")


def _fixture_payload(path: str | None) -> str | None:
    if path is None:
        return None
    return Path(path).read_text(encoding="utf-8")


@proposal.group("predicates")
def predicates() -> None:
    """Manage predicate proposal artifacts."""


@predicates.command("declare")
@click.option("--paper", required=True)
@click.option("--model", "model_name", default="default-model", show_default=True)
@click.option("--prompt-version", default="v1", show_default=True)
@click.option("--dry-run", is_flag=True)
@click.option("--mock-llm-fixture", type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def declare_predicates(
    ctx: click.Context,
    paper: str,
    model_name: str,
    prompt_version: str,
    dry_run: bool,
    mock_llm_fixture: str | None,
) -> None:
    """Propose predicate declarations for a meta-paper."""
    from propstore.heuristic.predicate_extraction import propose_predicates_for_paper

    repo = ctx.obj["repo"]
    result = propose_predicates_for_paper(
        repo,
        source_paper=paper,
        model_name=model_name,
        prompt_version=prompt_version,
        dry_run=dry_run,
        llm_response=_fixture_payload(mock_llm_fixture),
    )
    for declaration in result.declarations:
        emit(f"{declaration.name}/{declaration.arity} {tuple(declaration.arg_types)}")
    if result.commit_sha is not None:
        emit_success(f"Proposal commit: {result.commit_sha[:8]} on proposal/predicates")


@predicates.command("promote")
@click.option("--paper", required=True)
@click.pass_context
def promote_predicates(ctx: click.Context, paper: str) -> None:
    """Promote a predicate proposal document."""
    from propstore.proposals_predicates import (
        plan_predicate_proposal_promotion,
        promote_predicate_proposals,
    )

    repo = ctx.obj["repo"]
    try:
        plan = plan_predicate_proposal_promotion(repo, source_paper=paper)
    except UnknownProposalPath as exc:
        raise click.ClickException(f"UnknownProposalPath: {exc}") from exc
    result = promote_predicate_proposals(repo, plan)
    emit_success(f"Promoted {result.moved} predicate proposal file(s).")


@proposal.command("propose-rules")
@click.option("--paper", required=True)
@click.option("--model", "model_name", default="default-model", show_default=True)
@click.option("--prompt-version", default="v1", show_default=True)
@click.option("--dry-run", is_flag=True)
@click.option("--mock-llm-fixture", type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def propose_rules(
    ctx: click.Context,
    paper: str,
    model_name: str,
    prompt_version: str,
    dry_run: bool,
    mock_llm_fixture: str | None,
) -> None:
    """Propose rule files for a meta-paper."""
    from propstore.heuristic.rule_extraction import propose_rules_for_paper

    repo = ctx.obj["repo"]
    result = propose_rules_for_paper(
        repo,
        source_paper=paper,
        model_name=model_name,
        prompt_version=prompt_version,
        dry_run=dry_run,
        llm_response=_fixture_payload(mock_llm_fixture),
    )
    for proposal_doc in result.proposals:
        emit(
            f"{proposal_doc.rule_id} {proposal_doc.proposed_rule.kind} "
            f"{proposal_doc.proposed_rule.head.predicate} "
            f"{', '.join(proposal_doc.predicates_referenced)} "
            f"{proposal_doc.page_reference or ''}"
        )
    for rejection in result.rejections:
        emit(f"Rejected {rejection.rule_id}: {rejection.reason}")
    if result.commit_sha is not None:
        emit_success(f"Proposal commit: {result.commit_sha[:8]} on proposal/rules")


@proposal.command("promote-rules")
@click.option("--paper", required=True)
@click.option("--rule-id", "rule_ids", multiple=True)
@click.option("--all", "promote_all", is_flag=True)
@click.pass_context
def promote_rules(
    ctx: click.Context,
    paper: str,
    rule_ids: tuple[str, ...],
    promote_all: bool,
) -> None:
    """Promote selected rule proposals, or print the plan in review mode."""
    from propstore.families.registry import RuleProposalRef
    from propstore.proposals_rules import (
        plan_rule_proposal_promotion,
        promote_rule_proposals,
    )

    repo = ctx.obj["repo"]
    selected_rule_ids = None if promote_all else (rule_ids or None)
    try:
        plan = plan_rule_proposal_promotion(
            repo,
            source_paper=paper,
            rule_ids=selected_rule_ids,
        )
    except UnknownProposalPath as exc:
        raise click.ClickException(f"UnknownProposalPath: {exc}") from exc

    if not rule_ids and not promote_all:
        for item in plan.items:
            proposal_doc = repo.families.proposal_rules.require(
                RuleProposalRef(item.source_paper, item.rule_id),
                commit=plan.proposal_tip,
            )
            body = ", ".join(
                literal.atom.predicate for literal in proposal_doc.proposed_rule.body
            )
            emit(
                f"{proposal_doc.rule_id} {proposal_doc.proposed_rule.kind} "
                f"{proposal_doc.proposed_rule.head.predicate} body=[{body}] "
                f"predicates=[{', '.join(proposal_doc.predicates_referenced)}] "
                f"{proposal_doc.page_reference or ''}"
            )
        return

    result = promote_rule_proposals(repo, plan)
    emit_success(f"Promoted {result.moved} rule proposal file(s).")
