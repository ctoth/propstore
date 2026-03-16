"""pks concept — subcommands for managing concepts."""
from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

import click
import yaml

from compiler.cli.helpers import (
    EXIT_ERROR,
    EXIT_OK,
    EXIT_VALIDATION,
    concepts_dir,
    find_concept,
    load_all_concepts_by_id,
    load_concept_file,
    next_id,
    validate_concept_data,
    write_concept_file,
)
from compiler.validate import load_concepts, validate_concepts

# Valid kind types and relationship types from schema
KIND_TYPES = ("quantity", "category", "boolean", "structural")
RELATIONSHIP_TYPES = (
    "broader", "narrower", "related",
    "component_of", "derived_from", "contested_definition",
)


@click.group()
def concept() -> None:
    """Manage concepts in the registry."""


# ── concept add ──────────────────────────────────────────────────────

@concept.command()
@click.option("--domain", required=True, help="Domain prefix (e.g. speech, narr)")
@click.option("--name", required=True, help="Canonical name (lowercase, underscored)")
@click.option("--definition", default=None, help="Definition (prompted if omitted)")
@click.option("--kind", "kind_type", type=click.Choice(KIND_TYPES), default=None,
              help="Kind type (prompted if omitted)")
@click.option("--unit", default=None, help="Unit for quantity kind")
@click.option("--values", default=None, help="Comma-separated values for category kind")
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing")
def add(
    domain: str,
    name: str,
    definition: str | None,
    kind_type: str | None,
    unit: str | None,
    values: str | None,
    dry_run: bool,
) -> None:
    """Add a new concept to the registry."""
    # Prompt for missing fields
    if definition is None:
        definition = click.prompt("Definition")
    if kind_type is None:
        kind_type = click.prompt("Kind", type=click.Choice(KIND_TYPES))

    # Build kind dict
    kind: dict = {}
    if kind_type == "quantity":
        if unit is None:
            unit = click.prompt("Unit")
        kind["quantity"] = {"unit": unit}
    elif kind_type == "category":
        if values is None:
            values = click.prompt("Values (comma-separated)")
        assert values is not None
        kind["category"] = {"values": [v.strip() for v in values.split(",")], "extensible": True}
    elif kind_type == "boolean":
        kind["boolean"] = {}
    elif kind_type == "structural":
        kind["structural"] = {}

    cid, counter = next_id(domain)
    filepath = concepts_dir() / f"{name}.yaml"

    data = {
        "id": cid,
        "canonical_name": name,
        "status": "proposed",
        "definition": definition,
        "domain": domain,
        "created_date": str(date.today()),
        "kind": kind,
    }

    if dry_run:
        click.echo(f"Would create {filepath}")
        click.echo(yaml.dump(data, default_flow_style=False, sort_keys=False))
        return

    # Validate before writing
    # Temporarily write, validate, roll back on failure
    concepts_dir().mkdir(parents=True, exist_ok=True)
    write_concept_file(filepath, data)

    result = validate_concepts(load_concepts(concepts_dir()))
    if not result.ok:
        filepath.unlink()
        # Roll back the counter
        from compiler.cli.helpers import write_counter
        write_counter(domain, counter)
        for e in result.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Validation failed. No changes written.", err=True)
        sys.exit(EXIT_VALIDATION)

    for w in result.warnings:
        click.echo(f"WARNING: {w}", err=True)

    click.echo(f"Created {filepath} with ID {cid}")


# ── concept alias ────────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id")
@click.option("--name", required=True, help="Alias name")
@click.option("--source", required=True, help="Source paper or 'common'")
@click.option("--note", default=None, help="Optional note")
@click.option("--dry-run", is_flag=True)
def alias(concept_id: str, name: str, source: str, note: str | None, dry_run: bool) -> None:
    """Add an alias to a concept."""
    filepath = find_concept(concept_id)
    if filepath is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)

    data = load_concept_file(filepath)

    # Warn if alias matches another concept's canonical_name
    cdir = concepts_dir()
    for entry in sorted(cdir.iterdir()):
        if entry.is_file() and entry.suffix == ".yaml" and entry != filepath:
            other = load_concept_file(entry)
            if other.get("canonical_name") == name:
                click.echo(
                    f"WARNING: alias '{name}' matches canonical_name of "
                    f"concept '{other.get('id')}'", err=True)

    new_alias: dict[str, str] = {"name": name, "source": source}
    if note:
        new_alias["note"] = note

    if dry_run:
        click.echo(f"Would add alias to {filepath}: {new_alias}")
        return

    aliases = data.get("aliases") or []
    aliases.append(new_alias)
    data["aliases"] = aliases
    data["last_modified"] = str(date.today())
    write_concept_file(filepath, data)

    click.echo(f"Added alias '{name}' to {data.get('id')} ({filepath.stem})")


# ── concept rename ───────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id")
@click.option("--name", required=True, help="New canonical name")
@click.option("--dry-run", is_flag=True)
def rename(concept_id: str, name: str, dry_run: bool) -> None:
    """Rename a concept (updates canonical_name and filename)."""
    filepath = find_concept(concept_id)
    if filepath is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)

    data = load_concept_file(filepath)
    old_name = data.get("canonical_name", filepath.stem)
    new_path = filepath.parent / f"{name}.yaml"

    if dry_run:
        click.echo(f"Would rename: {old_name} -> {name}")
        click.echo(f"  {filepath} -> {new_path}")
        return

    data["canonical_name"] = name
    data["last_modified"] = str(date.today())
    write_concept_file(filepath, data)

    # Try git mv, fall back to plain rename
    try:
        subprocess.run(
            ["git", "mv", str(filepath), str(new_path)],
            check=True, capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        filepath.rename(new_path)

    click.echo(f"{old_name} -> {name}")
    click.echo(f"  {filepath} -> {new_path}")
    click.echo(f"  ID unchanged: {data.get('id')}")


# ── concept deprecate ────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id")
@click.option("--replaced-by", required=True, help="Replacement concept ID")
@click.option("--dry-run", is_flag=True)
def deprecate(concept_id: str, replaced_by: str, dry_run: bool) -> None:
    """Deprecate a concept with a replacement."""
    filepath = find_concept(concept_id)
    if filepath is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)

    # Validate replacement target
    replacement_path = find_concept(replaced_by)
    if replacement_path is None:
        click.echo(f"ERROR: Replacement concept '{replaced_by}' not found", err=True)
        sys.exit(EXIT_ERROR)

    replacement_data = load_concept_file(replacement_path)
    if replacement_data.get("status") == "deprecated":
        click.echo(f"ERROR: Replacement concept '{replaced_by}' is itself deprecated", err=True)
        sys.exit(EXIT_ERROR)

    data = load_concept_file(filepath)

    if dry_run:
        click.echo(f"Would deprecate {data.get('id')} ({filepath.stem})")
        click.echo(f"  replaced_by: {replaced_by}")
        return

    data["status"] = "deprecated"
    data["replaced_by"] = replaced_by
    data["last_modified"] = str(date.today())
    write_concept_file(filepath, data)

    click.echo(f"Deprecated {data.get('id')} ({filepath.stem}), replaced by {replaced_by}")


# ── concept link ─────────────────────────────────────────────────────

@concept.command()
@click.argument("source_id")
@click.argument("rel_type", type=click.Choice(RELATIONSHIP_TYPES))
@click.argument("target_id")
@click.option("--source", "paper_source", default=None, help="Source paper")
@click.option("--note", default=None)
@click.option("--conditions", default=None, help="Comma-separated CEL expressions")
@click.option("--dry-run", is_flag=True)
def link(
    source_id: str,
    rel_type: str,
    target_id: str,
    paper_source: str | None,
    note: str | None,
    conditions: str | None,
    dry_run: bool,
) -> None:
    """Add a relationship between concepts."""
    filepath = find_concept(source_id)
    if filepath is None:
        click.echo(f"ERROR: Source concept '{source_id}' not found", err=True)
        sys.exit(EXIT_ERROR)

    if find_concept(target_id) is None:
        click.echo(f"ERROR: Target concept '{target_id}' not found", err=True)
        sys.exit(EXIT_ERROR)

    data = load_concept_file(filepath)

    rel: dict[str, object] = {"type": rel_type, "target": target_id}
    if paper_source:
        rel["source"] = paper_source
    if note:
        rel["note"] = note
    if conditions:
        rel["conditions"] = [c.strip() for c in conditions.split(",")]

    if dry_run:
        click.echo(f"Would add relationship to {filepath.stem}: {rel}")
        return

    rels = data.get("relationships") or []
    rels.append(rel)
    data["relationships"] = rels
    data["last_modified"] = str(date.today())
    write_concept_file(filepath, data)

    click.echo(f"Added {rel_type} -> {target_id} on {data.get('id')} ({filepath.stem})")


# ── concept search ───────────────────────────────────────────────────

@concept.command()
@click.argument("query")
def search(query: str) -> None:
    """Search concepts by name, definition, or alias."""
    sidecar = Path("sidecar/propstore.sqlite")

    if sidecar.exists():
        import sqlite3
        conn = sqlite3.connect(sidecar)
        rows = conn.execute(
            "SELECT concept_id, canonical_name, definition "
            "FROM concept_fts WHERE concept_fts MATCH ? LIMIT 20",
            (query,),
        ).fetchall()
        conn.close()
        if rows:
            for cid, name, defn in rows:
                snippet = (defn or "")[:80]
                click.echo(f"  {cid}  {name}  — {snippet}")
        else:
            click.echo("No matches.")
        return

    # Fallback: grep over YAML files
    query_lower = query.lower()
    cdir = concepts_dir()
    if not cdir.exists():
        click.echo("No concepts directory found.")
        return

    found = False
    for entry in sorted(cdir.iterdir()):
        if not entry.is_file() or entry.suffix != ".yaml":
            continue
        data = load_concept_file(entry)
        searchable = " ".join([
            data.get("canonical_name", ""),
            data.get("definition", ""),
            " ".join(a.get("name", "") for a in (data.get("aliases") or [])),
        ]).lower()
        if query_lower in searchable:
            snippet = (data.get("definition", "") or "")[:80]
            click.echo(f"  {data.get('id')}  {data.get('canonical_name')}  — {snippet}")
            found = True

    if not found:
        click.echo("No matches.")


# ── concept list ─────────────────────────────────────────────────────

@concept.command("list")
@click.option("--domain", default=None, help="Filter by domain")
@click.option("--status", default=None, help="Filter by status")
def list_concepts(domain: str | None, status: str | None) -> None:
    """List concepts, optionally filtered."""
    cdir = concepts_dir()
    if not cdir.exists():
        click.echo("No concepts directory found.")
        return

    concepts = load_concepts(cdir)
    for c in concepts:
        d = c.data
        c_domain = d.get("domain", "")
        c_status = d.get("status", "")

        if domain and c_domain != domain:
            continue
        if status and c_status != status:
            continue

        click.echo(f"  {d.get('id', '?'):15s} {d.get('canonical_name', '?'):30s} [{c_status}]")


# ── concept show ─────────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id_or_name")
def show(concept_id_or_name: str) -> None:
    """Show full concept YAML."""
    filepath = find_concept(concept_id_or_name)
    if filepath is None:
        click.echo(f"ERROR: Concept '{concept_id_or_name}' not found", err=True)
        sys.exit(EXIT_ERROR)

    click.echo(filepath.read_text())
