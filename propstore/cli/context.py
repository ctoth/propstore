"""pks context — subcommands for managing contexts."""
from __future__ import annotations

import click

from propstore.context_lifting import LiftingMode
from propstore.cli.output import emit, emit_success

from quire.documents import encode_document
from propstore.cli.helpers import fail
from propstore.app.contexts import (
    ContextAddRequest,
    ContextLiftingRuleAddRequest,
    ContextNotFoundError,
    ContextReferencedError,
    ContextSearchRequest,
    ContextLiftingRuleUpdateRequest,
    ContextWorkflowError,
    add_context,
    add_context_lifting_rule,
    list_context_items,
    list_context_lifting_rules,
    remove_context,
    remove_context_lifting_rule,
    search_context_items,
    show_context_lifting_rule,
    show_context,
    update_context_lifting_rule,
)
from propstore.cli.helpers import EXIT_ERROR, exit_with_code
from propstore.repository import Repository


@click.group()
def context() -> None:
    """Manage contexts in the registry."""


@context.group("lifting")
def lifting() -> None:
    """Manage authored lifting rules on context artifacts."""


@context.command()
@click.option("--name", required=True, help="Context ID (e.g., ctx_atms_tradition)")
@click.option("--description", required=True, help="Short description")
@click.option("--assumption", multiple=True, help="Context-local CEL assumption")
@click.option("--parameter", multiple=True, help="Context parameter as KEY=VALUE")
@click.option("--perspective", default=None, help="Named perspective for this context")
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing")
@click.pass_obj
def add(
    obj: dict,
    name: str,
    description: str,
    assumption: tuple[str, ...],
    parameter: tuple[str, ...],
    perspective: str | None,
    dry_run: bool,
) -> None:
    """Add a new context to the registry."""
    repo: Repository = obj["repo"]
    request = ContextAddRequest(
        name=name,
        description=description,
        assumptions=assumption,
        parameters=parameter,
        perspective=perspective,
    )
    try:
        report = add_context(repo, request, dry_run=dry_run)
    except ContextWorkflowError as exc:
        fail(exc)

    if not report.created:
        emit(f"Would create {report.filepath}")
        emit(encode_document(report.document).decode("utf-8"))
        return

    emit_success(f"Created {report.filepath}")


@context.command("list")
@click.pass_obj
def list_contexts(obj: dict) -> None:
    """List all registered contexts."""
    repo: Repository = obj["repo"]
    contexts = list_context_items(repo)
    if not contexts:
        emit("No contexts registered.")
        return

    for context in contexts:
        suffix = f" ({context.perspective})" if context.perspective else ""
        emit(f"  {context.context_id}{suffix} — {context.description}")


@context.command("show")
@click.argument("name")
@click.pass_obj
def show(obj: dict, name: str) -> None:
    """Show one context YAML document."""
    repo: Repository = obj["repo"]
    try:
        report = show_context(repo, name)
    except ContextNotFoundError:
        fail(f"Context '{name}' not found")
    emit(report.rendered)


@context.command("remove")
@click.argument("name")
@click.option("--force", is_flag=True, help="Remove even if claims or worldlines still reference this context")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def remove(obj: dict, name: str, force: bool, dry_run: bool) -> None:
    """Remove one context YAML document."""
    repo: Repository = obj["repo"]
    try:
        report = remove_context(repo, name, force=force, dry_run=dry_run)
    except ContextNotFoundError:
        fail(f"Context '{name}' not found")
    except ContextReferencedError as exc:
        emit(f"ERROR: {exc}:")
        for reference in exc.references:
            emit(f"  {reference}")
        emit("Use --force to remove anyway.")
        exit_with_code(EXIT_ERROR)

    if not report.removed:
        emit(f"Would remove {report.filepath}")
        if report.references:
            emit(f"  ({len(report.references)} artifact(s) still reference this context)")
        return

    emit_success(f"Removed {report.filepath}")
    if report.references:
        emit(f"  WARNING: {len(report.references)} artifact(s) still reference this context")


@context.command("search")
@click.argument("query")
@click.option("--limit", default=20, type=click.IntRange(min=1), help="Maximum rows to show.")
@click.pass_obj
def search(obj: dict, query: str, limit: int) -> None:
    """Search contexts by id, description, or perspective."""
    repo: Repository = obj["repo"]
    items = search_context_items(
        repo,
        ContextSearchRequest(query=query, limit=limit),
    )
    if not items:
        emit("No matches.")
        return
    for item in items:
        suffix = f" ({item.perspective})" if item.perspective else ""
        emit(f"  {item.context_id}{suffix} — {item.description}")


@lifting.command("list")
@click.argument("context_name", required=False)
@click.pass_obj
def list_lifting_rules(obj: dict, context_name: str | None) -> None:
    """List authored lifting rules, optionally scoped to one target context."""
    repo: Repository = obj["repo"]
    try:
        items = list_context_lifting_rules(repo, context_name)
    except ContextNotFoundError:
        fail(f"Context '{context_name}' not found")
    if not items:
        emit("No lifting rules registered.")
        return
    for item in items:
        suffix = f", conditions={item.condition_count}" if item.condition_count else ""
        emit(
            f"  {item.owner_context}: {item.rule_id} "
            f"[{item.source_context} -> {item.target_context}, mode={item.mode.value}{suffix}]"
        )


@lifting.command("show")
@click.argument("context_name")
@click.argument("rule_id")
@click.pass_obj
def show_lifting_rule(obj: dict, context_name: str, rule_id: str) -> None:
    """Show one authored lifting rule as YAML."""
    repo: Repository = obj["repo"]
    try:
        report = show_context_lifting_rule(repo, context_name, rule_id)
    except ContextNotFoundError:
        fail(f"Context '{context_name}' not found")
    except ContextWorkflowError as exc:
        fail(exc)
    emit(report.rendered)


@lifting.command("add")
@click.argument("context_name")
@click.option("--rule-id", required=True, help="Stable authored lifting-rule id")
@click.option("--source", "source_context", required=True, help="Source context id")
@click.option("--condition", multiple=True, help="CEL condition required for the lift")
@click.option(
    "--mode",
    type=click.Choice([mode.value for mode in LiftingMode], case_sensitive=False),
    default=LiftingMode.BRIDGE.value,
    show_default=True,
    help="Lifting mode",
)
@click.option("--justification", default=None, help="Optional authored justification text")
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing")
@click.pass_obj
def add_lifting_rule(
    obj: dict,
    context_name: str,
    rule_id: str,
    source_context: str,
    condition: tuple[str, ...],
    mode: str,
    justification: str | None,
    dry_run: bool,
) -> None:
    """Add one authored lifting rule to a target context."""
    repo: Repository = obj["repo"]
    request = ContextLiftingRuleAddRequest(
        rule_id=rule_id,
        source_context=source_context,
        conditions=condition,
        mode=LiftingMode(mode),
        justification=justification,
    )
    try:
        report = add_context_lifting_rule(repo, context_name, request, dry_run=dry_run)
    except ContextNotFoundError:
        fail(f"Context '{context_name}' not found")
    except ContextWorkflowError as exc:
        fail(exc)
    if not report.created:
        emit(f"Would add lifting rule '{report.rule_id}' in {report.filepath}")
        return
    emit_success(f"Added lifting rule '{report.rule_id}' in {report.filepath}")


@lifting.command("update")
@click.argument("context_name")
@click.argument("rule_id")
@click.option("--source", "source_context", default=None, help="Replacement source context id")
@click.option("--condition", multiple=True, help="Replace rule conditions with these CEL expressions")
@click.option("--clear-conditions", is_flag=True, help="Remove all rule conditions")
@click.option(
    "--mode",
    type=click.Choice([mode.value for mode in LiftingMode], case_sensitive=False),
    default=None,
    help="Replacement lifting mode",
)
@click.option("--justification", default=None, help="Replacement justification text")
@click.option("--clear-justification", is_flag=True, help="Remove the existing justification")
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing")
@click.pass_obj
def update_lifting_rule(
    obj: dict,
    context_name: str,
    rule_id: str,
    source_context: str | None,
    condition: tuple[str, ...],
    clear_conditions: bool,
    mode: str | None,
    justification: str | None,
    clear_justification: bool,
    dry_run: bool,
) -> None:
    """Update one authored lifting rule on a target context."""
    if condition and clear_conditions:
        fail("Cannot use --condition and --clear-conditions together")
    if justification is not None and clear_justification:
        fail("Cannot use --justification and --clear-justification together")
    repo: Repository = obj["repo"]
    conditions: tuple[str, ...] | None = None
    if clear_conditions:
        conditions = ()
    elif condition:
        conditions = condition
    request = ContextLiftingRuleUpdateRequest(
        source_context=source_context,
        conditions=conditions,
        mode=None if mode is None else LiftingMode(mode),
        justification=justification,
        clear_justification=clear_justification,
    )
    try:
        report = update_context_lifting_rule(
            repo,
            context_name,
            rule_id,
            request,
            dry_run=dry_run,
        )
    except ContextNotFoundError:
        fail(f"Context '{context_name}' not found")
    except ContextWorkflowError as exc:
        fail(exc)
    if not report.updated:
        emit(f"Would update lifting rule '{report.rule_id}' in {report.filepath}")
        return
    emit_success(f"Updated lifting rule '{report.rule_id}' in {report.filepath}")


@lifting.command("remove")
@click.argument("context_name")
@click.argument("rule_id")
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing")
@click.pass_obj
def remove_lifting_rule(
    obj: dict,
    context_name: str,
    rule_id: str,
    dry_run: bool,
) -> None:
    """Remove one authored lifting rule from a target context."""
    repo: Repository = obj["repo"]
    try:
        report = remove_context_lifting_rule(
            repo,
            context_name,
            rule_id,
            dry_run=dry_run,
        )
    except ContextNotFoundError:
        fail(f"Context '{context_name}' not found")
    except ContextWorkflowError as exc:
        fail(exc)
    if not report.removed:
        emit(f"Would remove lifting rule '{report.rule_id}' from {report.filepath}")
        return
    emit_success(f"Removed lifting rule '{report.rule_id}' from {report.filepath}")
