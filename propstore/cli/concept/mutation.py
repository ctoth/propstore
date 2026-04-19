from __future__ import annotations

import click

from propstore.app.concepts import (
    ConceptAddRequest,
    ConceptAddValueRequest,
    ConceptAliasRequest,
    ConceptDeprecateRequest,
    ConceptDescriptionKindRequest,
    ConceptLinkRequest,
    ConceptMutationError,
    ConceptMutationReport,
    ConceptProtoRoleRequest,
    ConceptQualiaAddRequest,
    ConceptRenameRequest,
    ConceptValidationError,
    PROTO_ROLE_KINDS,
    QUALIA_ROLES,
    RELATIONSHIP_TYPES,
    add_concept,
    add_concept_alias,
    add_concept_proto_role,
    add_concept_qualia,
    add_concept_value,
    deprecate_concept,
    link_concepts,
    rename_concept,
    set_concept_description_kind,
)
from propstore.cli.concept import (
    concept,
)
from propstore.cli.helpers import EXIT_ERROR, EXIT_VALIDATION
from propstore.repository import Repository


def _render_mutation_report(report: ConceptMutationReport) -> None:
    for warning in report.warnings:
        click.echo(f"WARNING: {warning}", err=True)
    for line in report.lines:
        click.echo(line)


def _run_mutation(action) -> None:
    try:
        report = action()
    except ConceptValidationError as exc:
        for warning in exc.warnings:
            click.echo(f"WARNING: {warning}", err=True)
        for error in exc.errors:
            click.echo(f"ERROR: {error}", err=True)
        click.echo(str(exc), err=True)
        raise SystemExit(EXIT_VALIDATION)
    except ConceptMutationError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        raise SystemExit(EXIT_ERROR)
    _render_mutation_report(report)

# ── concept add ──────────────────────────────────────────────────────


@concept.command()
@click.option(
    "--domain", required=True, help="Domain prefix (e.g. speech, a11y, finance)"
)
@click.option("--name", required=True, help="Canonical name (lowercase, underscored)")
@click.option("--definition", default=None, help="Definition (prompted if omitted)")
@click.option(
    "--form",
    "form_name",
    default=None,
    help="Form name (references forms/<name>.yaml, prompted if omitted)",
)
@click.option(
    "--values",
    default=None,
    help="Comma-separated values (required for category concepts)",
)
@click.option(
    "--closed",
    is_flag=True,
    default=False,
    help="Declare category value set as exhaustive (extensible: false)",
)
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing")
@click.pass_obj
def add(
    obj: dict,
    domain: str,
    name: str,
    definition: str | None,
    form_name: str | None,
    values: str | None,
    closed: bool,
    dry_run: bool,
) -> None:
    """Add a new concept to the registry."""
    repo: Repository = obj["repo"]
    if definition is None:
        definition = click.prompt("Definition")
    if form_name is None:
        available = sorted(form_ref.name for form_ref in repo.families.forms.iter())
        if available:
            click.echo(f"Available forms: {', '.join(available)}")
        form_name = click.prompt("Form")
    if definition is None or form_name is None:
        raise click.ClickException("definition and form are required")

    _run_mutation(
        lambda: add_concept(
            repo,
            ConceptAddRequest(
                domain=domain,
                name=name,
                definition=definition,
                form_name=form_name,
                values=values,
                closed=closed,
                dry_run=dry_run,
            ),
        )
    )


# ── concept alias ────────────────────────────────────────────────────


@concept.command()
@click.argument("concept_id")
@click.option("--name", required=True, help="Alias name")
@click.option("--source", required=True, help="Source paper or 'common'")
@click.option("--note", default=None, help="Optional note")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def alias(
    obj: dict, concept_id: str, name: str, source: str, note: str | None, dry_run: bool
) -> None:
    """Add an alias to a concept."""
    repo: Repository = obj["repo"]
    _run_mutation(
        lambda: add_concept_alias(
            repo,
            ConceptAliasRequest(
                concept_id=concept_id,
                name=name,
                source=source,
                note=note,
                dry_run=dry_run,
            ),
        )
    )


# ── concept rename ───────────────────────────────────────────────────


@concept.command()
@click.argument("concept_id")
@click.option("--name", required=True, help="New canonical name")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def rename(obj: dict, concept_id: str, name: str, dry_run: bool) -> None:
    """Rename a concept, cascading the new name through dependent CEL conditions.

    Updates canonical_name, filename, logical_ids, and artifact_id, then
    rewrites CEL condition expressions in every other concept and every
    claim file that references the old name. Re-validates concepts and
    claims before committing; aborts with a non-zero exit code if validation
    fails. The commit is a batch that adds the new file and deletes the old.
    """
    repo: Repository = obj["repo"]
    _run_mutation(
        lambda: rename_concept(
            repo,
            ConceptRenameRequest(
                concept_id=concept_id,
                name=name,
                dry_run=dry_run,
            ),
        )
    )


# ── concept deprecate ────────────────────────────────────────────────


@concept.command()
@click.argument("concept_id")
@click.option("--replaced-by", required=True, help="Replacement concept ID")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def deprecate(obj: dict, concept_id: str, replaced_by: str, dry_run: bool) -> None:
    """Deprecate a concept with a replacement."""
    repo: Repository = obj["repo"]
    _run_mutation(
        lambda: deprecate_concept(
            repo,
            ConceptDeprecateRequest(
                concept_id=concept_id,
                replaced_by=replaced_by,
                dry_run=dry_run,
            ),
        )
    )


# ── concept link ─────────────────────────────────────────────────────


@concept.command()
@click.argument("source_id")
@click.argument("rel_type", type=click.Choice(RELATIONSHIP_TYPES))
@click.argument("target_id")
@click.option("--source", "paper_source", default=None, help="Source paper")
@click.option("--note", default=None)
@click.option("--conditions", default=None, help="Comma-separated CEL expressions")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def link(
    obj: dict,
    source_id: str,
    rel_type: str,
    target_id: str,
    paper_source: str | None,
    note: str | None,
    conditions: str | None,
    dry_run: bool,
) -> None:
    """Add a relationship between concepts."""
    repo: Repository = obj["repo"]
    _run_mutation(
        lambda: link_concepts(
            repo,
            ConceptLinkRequest(
                source_id=source_id,
                rel_type=rel_type,
                target_id=target_id,
                paper_source=paper_source,
                note=note,
                conditions=conditions,
                dry_run=dry_run,
            ),
        )
    )


# ── concept qualia-add ───────────────────────────────────────────────


@concept.command("qualia-add")
@click.argument("concept_id")
@click.argument("role", type=click.Choice(QUALIA_ROLES))
@click.argument("target_concept")
@click.option(
    "--type-constraint",
    default=None,
    help="Concept that the qualia target must satisfy",
)
@click.option("--asserter", required=True)
@click.option("--timestamp", required=True)
@click.option("--source-artifact-code", required=True)
@click.option("--method", required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def qualia_add(
    obj: dict,
    concept_id: str,
    role: str,
    target_concept: str,
    type_constraint: str | None,
    asserter: str,
    timestamp: str,
    source_artifact_code: str,
    method: str,
    dry_run: bool,
) -> None:
    """Add a provenance-bearing qualia reference to a concept sense."""
    repo: Repository = obj["repo"]
    _run_mutation(
        lambda: add_concept_qualia(
            repo,
            ConceptQualiaAddRequest(
                concept_id=concept_id,
                role=role,
                target_concept=target_concept,
                type_constraint=type_constraint,
                asserter=asserter,
                timestamp=timestamp,
                source_artifact_code=source_artifact_code,
                method=method,
                dry_run=dry_run,
            ),
        )
    )


# ── concept description-kind ─────────────────────────────────────────


@concept.command("description-kind")
@click.argument("concept_id")
@click.option("--name", required=True)
@click.option("--reference", "reference_handle", required=True)
@click.option("--slot", "slots", multiple=True, help="Slot as name=type-concept")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def description_kind_cmd(
    obj: dict,
    concept_id: str,
    name: str,
    reference_handle: str,
    slots: tuple[str, ...],
    dry_run: bool,
) -> None:
    """Set the description-kind structure carried by a concept sense."""
    repo: Repository = obj["repo"]
    _run_mutation(
        lambda: set_concept_description_kind(
            repo,
            ConceptDescriptionKindRequest(
                concept_id=concept_id,
                name=name,
                reference_handle=reference_handle,
                slots=slots,
                dry_run=dry_run,
            ),
        )
    )


# ── concept proto-role ───────────────────────────────────────────────


@concept.command("proto-role")
@click.argument("concept_id")
@click.argument("role_name")
@click.argument("role_kind", type=click.Choice(PROTO_ROLE_KINDS))
@click.argument("property_name")
@click.argument("value", type=float)
@click.option("--asserter", required=True)
@click.option("--timestamp", required=True)
@click.option("--source-artifact-code", required=True)
@click.option("--method", required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def proto_role_cmd(
    obj: dict,
    concept_id: str,
    role_name: str,
    role_kind: str,
    property_name: str,
    value: float,
    asserter: str,
    timestamp: str,
    source_artifact_code: str,
    method: str,
    dry_run: bool,
) -> None:
    """Add a Dowty proto-role entailment to a named role."""
    repo: Repository = obj["repo"]
    _run_mutation(
        lambda: add_concept_proto_role(
            repo,
            ConceptProtoRoleRequest(
                concept_id=concept_id,
                role_name=role_name,
                role_kind=role_kind,
                property_name=property_name,
                value=value,
                asserter=asserter,
                timestamp=timestamp,
                source_artifact_code=source_artifact_code,
                method=method,
                dry_run=dry_run,
            ),
        )
    )


# ── concept search ───────────────────────────────────────────────────


@concept.command("add-value")
@click.argument("concept_name")
@click.option(
    "--value", required=True, help="Value to add to the category concept's value set"
)
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing")
@click.pass_obj
def add_value(obj: dict, concept_name: str, value: str, dry_run: bool) -> None:
    """Add a value to a category concept's value set."""
    repo: Repository = obj["repo"]
    _run_mutation(
        lambda: add_concept_value(
            repo,
            ConceptAddValueRequest(
                concept_name=concept_name,
                value=value,
                dry_run=dry_run,
            ),
        )
    )


# ── concept categories ───────────────────────────────────────────────
