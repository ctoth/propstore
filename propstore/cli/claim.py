"""pks claim — subcommands for claim validation and conflict detection."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from propstore.cli.helpers import EXIT_ERROR, EXIT_VALIDATION
from propstore.cli.repository import Repository


@click.group()
def claim() -> None:
    """Manage and validate claims."""


@claim.command()
@click.option("--dir", "claims_path", default=None, help="Claims directory")
@click.option("--concepts-dir", "concepts_path", default=None, help="Concepts directory")
@click.pass_obj
def validate(obj: dict, claims_path: str | None, concepts_path: str | None) -> None:
    """Validate all claim files."""
    from propstore.validate_claims import (
        build_concept_registry_from_paths,
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

    forms_dir = cpd.parent / "forms"
    if not forms_dir.exists():
        forms_dir = repo.forms_dir

    registry = build_concept_registry_from_paths(cpd, forms_dir)
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
    from propstore.conflict_detector import ConflictClass, detect_conflicts
    from propstore.validate_claims import build_concept_registry, load_claim_files

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


@claim.command()
@click.argument("id_a")
@click.argument("id_b")
@click.option("--bindings", "-b", multiple=True, help="Known values as key=value pairs")
@click.pass_obj
def compare(obj: dict, id_a: str, id_b: str, bindings: tuple[str, ...]) -> None:
    """Compare two algorithm claims for equivalence."""
    from ast_equiv import compare as ast_compare

    from propstore.world_model import WorldModel

    repo: Repository = obj["repo"]
    try:
        wm = WorldModel(repo)
    except FileNotFoundError:
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(EXIT_ERROR)

    claim_a = wm.get_claim(id_a)
    if claim_a is None:
        click.echo(f"ERROR: Claim '{id_a}' not found.", err=True)
        wm.close()
        sys.exit(EXIT_ERROR)

    claim_b = wm.get_claim(id_b)
    if claim_b is None:
        click.echo(f"ERROR: Claim '{id_b}' not found.", err=True)
        wm.close()
        sys.exit(EXIT_ERROR)

    body_a = claim_a.get("body")
    body_b = claim_b.get("body")
    if not body_a or not body_b:
        click.echo("ERROR: Both claims must be algorithm claims with a body.", err=True)
        wm.close()
        sys.exit(EXIT_ERROR)

    import json as _json

    def _parse_variables(claim: dict) -> dict[str, str]:
        vj = claim.get("variables_json")
        if not vj:
            return {}
        variables = _json.loads(vj)
        result: dict[str, str] = {}
        if isinstance(variables, list):
            for var in variables:
                if isinstance(var, dict):
                    name = var.get("name") or var.get("symbol")
                    concept = var.get("concept", "")
                    if name:
                        result[name] = concept
        elif isinstance(variables, dict):
            result.update(variables)
        return result

    bindings_a = _parse_variables(claim_a)
    bindings_b = _parse_variables(claim_b)

    # Parse known values from --bindings options
    known_values: dict[str, float] | None = None
    if bindings:
        known_values = {}
        for b in bindings:
            key, _, value = b.partition("=")
            try:
                known_values[key] = float(value)
            except ValueError:
                click.echo(f"WARNING: Ignoring non-numeric binding: {b}", err=True)

    result = ast_compare(body_a, bindings_a, body_b, bindings_b,
                         known_values=known_values or None)

    click.echo(f"Tier:       {result.tier}")
    click.echo(f"Equivalent: {result.equivalent}")
    click.echo(f"Similarity: {result.similarity:.4f}")
    if result.details:
        click.echo(f"Details:    {result.details}")
    wm.close()
