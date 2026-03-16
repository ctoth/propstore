"""pks claim — subcommands for claim validation and conflict detection."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from compiler.cli.helpers import EXIT_ERROR, EXIT_OK, EXIT_VALIDATION
from compiler.cli.repository import Repository


@click.group()
def claim() -> None:
    """Manage and validate claims."""


@claim.command()
@click.option("--dir", "claims_path", default=None, help="Claims directory")
@click.option("--concepts-dir", "concepts_path", default=None, help="Concepts directory")
@click.pass_obj
def validate(obj: dict, claims_path: str | None, concepts_path: str | None) -> None:
    """Validate all claim files."""
    from compiler.validate_claims import (
        build_concept_registry,
        load_claim_files,
        validate_claims,
    )

    repo: Repository = obj["repo"]
    cd = Path(claims_path) if claims_path else repo.claims_dir
    cpd = Path(concepts_path) if concepts_path else repo.concepts_dir

    if not cd.exists():
        click.echo(f"ERROR: Claims directory '{cd}' does not exist", err=True)
        sys.exit(EXIT_ERROR)
    if not cpd.exists():
        click.echo(f"ERROR: Concepts directory '{cpd}' does not exist", err=True)
        sys.exit(EXIT_ERROR)

    files = load_claim_files(cd)
    if not files:
        click.echo("No claim files found.")
        return

    registry = build_concept_registry(repo)
    result = validate_claims(files, registry)

    for w in result.warnings:
        click.echo(f"WARNING: {w}", err=True)
    for e in result.errors:
        click.echo(f"ERROR: {e}", err=True)

    if result.ok:
        click.echo(f"Validation passed: {len(files)} claim file(s), {len(result.warnings)} warning(s)")
    else:
        click.echo(f"Validation FAILED: {len(result.errors)} error(s)", err=True)
        sys.exit(EXIT_VALIDATION)


@claim.command()
@click.option("--concept", default=None, help="Filter by concept ID")
@click.option("--class", "warning_class", default=None,
              type=click.Choice(["CONFLICT", "OVERLAP", "PARAM_CONFLICT"]),
              help="Filter by warning class")
@click.pass_obj
def conflicts(obj: dict, concept: str | None, warning_class: str | None) -> None:
    """Detect and report claim conflicts."""
    from compiler.conflict_detector import ConflictClass, detect_conflicts
    from compiler.validate_claims import build_concept_registry, load_claim_files

    repo: Repository = obj["repo"]
    cd = repo.claims_dir
    cpd = repo.concepts_dir

    if not cd.exists():
        click.echo(f"ERROR: Claims directory '{cd}' does not exist", err=True)
        sys.exit(EXIT_ERROR)
    if not cpd.exists():
        click.echo(f"ERROR: Concepts directory '{cpd}' does not exist", err=True)
        sys.exit(EXIT_ERROR)

    files = load_claim_files(cd)
    if not files:
        click.echo("No claim files found.")
        return

    registry = build_concept_registry(repo)
    records = detect_conflicts(files, registry)

    # Filter
    if concept:
        records = [r for r in records if r.concept_id == concept]
    if warning_class:
        records = [r for r in records if r.warning_class == ConflictClass(warning_class)]

    if not records:
        click.echo("No conflicts found.")
        return

    for r in records:
        click.echo(
            f"  {r.warning_class.value:16s} concept={r.concept_id} "
            f"{r.claim_a_id} vs {r.claim_b_id}  "
            f"({r.value_a} vs {r.value_b})"
        )
        if r.derivation_chain:
            click.echo(f"    chain: {r.derivation_chain}")

    click.echo(f"\n{len(records)} conflict(s) found.")
