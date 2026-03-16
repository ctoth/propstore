"""pks validate / build / query / export-aliases — top-level compiler commands."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import click

from compiler.cli.helpers import EXIT_OK, EXIT_VALIDATION, claims_dir, concepts_dir


@click.command()
def validate() -> None:
    """Validate all concepts and claims. Runs CEL type-checking."""
    from compiler.validate import load_concepts, validate_concepts
    from compiler.validate_claims import (
        build_concept_registry,
        load_claim_files,
        validate_claims,
    )

    cpd = concepts_dir()
    if not cpd.exists():
        click.echo(f"ERROR: Concepts directory '{cpd}' does not exist", err=True)
        sys.exit(1)

    concepts = load_concepts(cpd)
    if not concepts:
        click.echo("No concept files found.")
        return

    concept_result = validate_concepts(concepts)

    for w in concept_result.warnings:
        click.echo(f"WARNING: {w}", err=True)
    for e in concept_result.errors:
        click.echo(f"ERROR: {e}", err=True)

    # Claims (if directory exists)
    claim_error_count = 0
    claim_file_count = 0
    cd = claims_dir()
    if cd.exists():
        files = load_claim_files(cd)
        claim_file_count = len(files)
        if files:
            registry = build_concept_registry(cpd)
            claim_result = validate_claims(files, registry)
            for w in claim_result.warnings:
                click.echo(f"WARNING: {w}", err=True)
            for e in claim_result.errors:
                click.echo(f"ERROR: {e}", err=True)
            claim_error_count = len(claim_result.errors)

    total_errors = len(concept_result.errors) + claim_error_count

    if total_errors == 0:
        click.echo(
            f"Validation passed: {len(concepts)} concept(s), "
            f"{claim_file_count} claim file(s)")
    else:
        click.echo(f"Validation FAILED: {total_errors} error(s)", err=True)
        sys.exit(EXIT_VALIDATION)


@click.command()
@click.option("-o", "--output", default="sidecar/propstore.sqlite", help="Output path")
@click.option("--force", is_flag=True, help="Force rebuild")
def build(output: str, force: bool) -> None:
    """Validate everything, build sidecar, run conflict detection."""
    from compiler.build_sidecar import build_sidecar
    from compiler.conflict_detector import detect_conflicts
    from compiler.validate import load_concepts, validate_concepts
    from compiler.validate_claims import (
        build_concept_registry,
        load_claim_files,
        validate_claims,
    )

    cpd = concepts_dir()
    if not cpd.exists():
        click.echo(f"ERROR: Concepts directory '{cpd}' does not exist", err=True)
        sys.exit(1)

    concepts = load_concepts(cpd)
    if not concepts:
        click.echo("No concept files found.")
        return

    # Step 1: Validate concepts
    concept_result = validate_concepts(concepts)
    if not concept_result.ok:
        for e in concept_result.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Build aborted: concept validation failed.", err=True)
        sys.exit(EXIT_VALIDATION)

    # Step 2: Validate claims (if any)
    claim_files = None
    concept_registry = None
    cd = claims_dir()
    if cd.exists():
        files = load_claim_files(cd)
        if files:
            concept_registry = build_concept_registry(cpd)
            claim_result = validate_claims(files, concept_registry)
            if not claim_result.ok:
                for e in claim_result.errors:
                    click.echo(f"ERROR: {e}", err=True)
                click.echo("Build aborted: claim validation failed.", err=True)
                sys.exit(EXIT_VALIDATION)
            claim_files = files

    # Step 3: Build sidecar
    sidecar_path = Path(output)
    rebuilt = build_sidecar(
        concepts, sidecar_path, force=force,
        claim_files=claim_files,
        concept_registry=concept_registry,
    )

    # Step 4: Conflict detection summary
    conflict_count = 0
    warning_count = len(concept_result.warnings)
    if claim_files and concept_registry:
        records = detect_conflicts(claim_files, concept_registry)
        conflict_count = len(records)
        for r in records:
            click.echo(
                f"  {r.warning_class.value}: {r.concept_id} "
                f"({r.claim_a_id} vs {r.claim_b_id})", err=True)

    claim_count = 0
    if claim_files:
        for cf in claim_files:
            claim_count += len(cf.data.get("claims", []))

    status = "rebuilt" if rebuilt else "unchanged"
    click.echo(
        f"Build {status}: {len(concepts)} concepts, {claim_count} claims, "
        f"{conflict_count} conflicts, {warning_count} warnings")


@click.command()
@click.argument("sql")
def query(sql: str) -> None:
    """Run raw SQL against the sidecar SQLite."""
    sidecar = Path("sidecar/propstore.sqlite")
    if not sidecar.exists():
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)

    conn = sqlite3.connect(sidecar)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        if rows:
            # Print header
            keys = rows[0].keys()
            click.echo("\t".join(keys))
            for row in rows:
                click.echo("\t".join(str(row[k]) for k in keys))
        else:
            click.echo("(no results)")
    except sqlite3.Error as e:
        click.echo(f"SQL error: {e}", err=True)
        sys.exit(1)
    finally:
        conn.close()


@click.command("export-aliases")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text",
              help="Output format")
def export_aliases(fmt: str) -> None:
    """Export the alias lookup table."""
    all_concepts = concepts_dir()
    if not all_concepts.exists():
        click.echo("ERROR: No concepts directory.", err=True)
        sys.exit(1)

    from compiler.validate import load_concepts

    concepts = load_concepts(all_concepts)
    aliases: dict[str, dict[str, str]] = {}

    for c in concepts:
        d = c.data
        cid = d.get("id", "")
        name = d.get("canonical_name", "")
        for a in d.get("aliases", []) or []:
            alias_name = a.get("name", "")
            if alias_name:
                aliases[alias_name] = {"id": cid, "name": name}

    if fmt == "json":
        click.echo(json.dumps(aliases, indent=2))
    else:
        for alias_name, info in sorted(aliases.items()):
            click.echo(f"{alias_name} -> {info['id']} ({info['name']})")
