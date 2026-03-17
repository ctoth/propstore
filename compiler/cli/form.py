"""pks form — subcommands for managing form definitions."""
from __future__ import annotations

import json
import sys

import click
import yaml

from compiler.cli.helpers import EXIT_ERROR
from compiler.cli.repository import Repository


@click.group()
def form() -> None:
    """Manage form definitions."""


# ── form list ────────────────────────────────────────────────────────

@form.command("list")
@click.pass_obj
def list_forms(obj: dict) -> None:
    """List all available forms."""
    repo: Repository = obj["repo"]
    fdir = repo.forms_dir
    if not fdir.exists():
        click.echo("No forms directory found.")
        return

    for entry in sorted(fdir.iterdir()):
        if not entry.is_file() or entry.suffix != ".yaml":
            continue
        with open(entry) as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            continue
        name = data.get("name", entry.stem)
        unit = data.get("unit_symbol") or ""
        unit_col = f"  [{unit}]" if unit else ""
        click.echo(f"  {name:30s}{unit_col}")


# ── form show ────────────────────────────────────────────────────────

@form.command()
@click.argument("name")
@click.pass_obj
def show(obj: dict, name: str) -> None:
    """Show full form definition YAML."""
    repo: Repository = obj["repo"]
    path = repo.forms_dir / f"{name}.yaml"
    if not path.exists():
        click.echo(f"ERROR: Form '{name}' not found", err=True)
        sys.exit(EXIT_ERROR)
    click.echo(path.read_text())


# ── form add ─────────────────────────────────────────────────────────

@form.command()
@click.option("--name", required=True, help="Form name (lowercase, underscored)")
@click.option("--unit", "unit_symbol", default=None, help="Primary unit symbol (e.g. Hz, Pa)")
@click.option("--qudt", default=None, help="QUDT IRI (e.g. qudt:HZ)")
@click.option("--base", default=None, help="Base type (e.g. ratio)")
@click.option("--dimensions", default=None, help="JSON dict of SI dimension exponents, e.g. '{\"T\": -1}'")
@click.option("--dimensionless", default=None, help="Whether the form is dimensionless (true/false)")
@click.option("--common-alternatives", default=None, help="JSON array of alternative unit conversions")
@click.option("--note", default=None, help="Human-readable note about this form")
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing")
@click.pass_obj
def add(
    obj: dict,
    name: str,
    unit_symbol: str | None,
    qudt: str | None,
    base: str | None,
    dimensions: str | None,
    dimensionless: str | None,
    common_alternatives: str | None,
    note: str | None,
    dry_run: bool,
) -> None:
    """Add a new form definition."""
    repo: Repository = obj["repo"]
    fdir = repo.forms_dir
    path = fdir / f"{name}.yaml"
    if path.exists():
        click.echo(f"ERROR: Form '{name}' already exists", err=True)
        sys.exit(EXIT_ERROR)

    # Parse dimensions JSON if provided
    dims_parsed: dict | None = None
    if dimensions is not None:
        try:
            dims_parsed = json.loads(dimensions)
        except json.JSONDecodeError:
            click.echo(f"ERROR: Invalid JSON for --dimensions: {dimensions}", err=True)
            sys.exit(EXIT_ERROR)

    # Determine dimensionless value
    if dimensionless is not None:
        is_dimless = dimensionless.lower() in ("true", "1", "yes")
    elif dims_parsed is not None and len(dims_parsed) > 0:
        is_dimless = False
    else:
        is_dimless = dims_parsed is not None and len(dims_parsed) == 0

    data: dict[str, object] = {"name": name, "dimensionless": is_dimless}
    if base is not None:
        data["base"] = base
    if unit_symbol is not None:
        data["unit_symbol"] = unit_symbol
    if qudt is not None:
        data["qudt"] = qudt
    if dims_parsed is not None:
        data["dimensions"] = dims_parsed

    # Parse common_alternatives JSON if provided
    if common_alternatives is not None:
        try:
            data["common_alternatives"] = json.loads(common_alternatives)
        except json.JSONDecodeError:
            click.echo(f"ERROR: Invalid JSON for --common-alternatives: {common_alternatives}", err=True)
            sys.exit(EXIT_ERROR)

    if note is not None:
        data["note"] = note

    if dry_run:
        click.echo(f"Would create {path}")
        click.echo(yaml.dump(data, default_flow_style=False, sort_keys=False))
        return

    fdir.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    click.echo(f"Created {path}")


# ── form remove ──────────────────────────────────────────────────────

@form.command()
@click.argument("name")
@click.option("--force", is_flag=True, help="Remove even if concepts reference this form")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def remove(obj: dict, name: str, force: bool, dry_run: bool) -> None:
    """Remove a form definition."""
    repo: Repository = obj["repo"]
    path = repo.forms_dir / f"{name}.yaml"
    if not path.exists():
        click.echo(f"ERROR: Form '{name}' not found", err=True)
        sys.exit(EXIT_ERROR)

    # Check for concepts that reference this form
    concepts_path = repo.concepts_dir
    referencing: list[str] = []
    if concepts_path.exists():
        for entry in sorted(concepts_path.iterdir()):
            if not entry.is_file() or entry.suffix != ".yaml":
                continue
            with open(entry) as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict) and data.get("form") == name:
                referencing.append(f"{data.get('id', '?')} ({entry.stem})")

    if referencing and not force:
        click.echo(f"ERROR: Form '{name}' is referenced by {len(referencing)} concept(s):", err=True)
        for ref in referencing:
            click.echo(f"  {ref}", err=True)
        click.echo("Use --force to remove anyway.", err=True)
        sys.exit(EXIT_ERROR)

    if dry_run:
        click.echo(f"Would remove {path}")
        if referencing:
            click.echo(f"  ({len(referencing)} concept(s) still reference this form)")
        return

    path.unlink()
    click.echo(f"Removed {path}")
    if referencing:
        click.echo(f"  WARNING: {len(referencing)} concept(s) still reference this form")


# ── form validate ────────────────────────────────────────────────────

@form.command()
@click.argument("name", required=False)
@click.pass_obj
def validate(obj: dict, name: str | None) -> None:
    """Validate form definitions (one or all).

    Checks that every form YAML has a valid name field and that forms
    referenced by concepts actually exist.
    """
    repo: Repository = obj["repo"]
    fdir = repo.forms_dir
    if not fdir.exists():
        click.echo("No forms directory found.")
        return

    errors: list[str] = []

    if name is not None:
        paths = [fdir / f"{name}.yaml"]
        if not paths[0].exists():
            click.echo(f"ERROR: Form '{name}' not found", err=True)
            sys.exit(EXIT_ERROR)
    else:
        paths = sorted(p for p in fdir.iterdir() if p.is_file() and p.suffix == ".yaml")

    form_names: set[str] = set()
    for path in paths:
        with open(path) as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            errors.append(f"{path.name}: not a valid YAML mapping")
            continue
        form_name = data.get("name")
        if not isinstance(form_name, str) or not form_name:
            errors.append(f"{path.name}: missing or invalid 'name' field")
            continue
        if form_name != path.stem:
            errors.append(f"{path.name}: name '{form_name}' does not match filename")
        form_names.add(form_name)

    # Check that concepts reference existing forms
    concepts_path = repo.concepts_dir
    if concepts_path.exists():
        all_forms = {p.stem for p in fdir.iterdir() if p.is_file() and p.suffix == ".yaml"}
        for entry in sorted(concepts_path.iterdir()):
            if not entry.is_file() or entry.suffix != ".yaml":
                continue
            with open(entry) as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                continue
            ref = data.get("form")
            if isinstance(ref, str) and ref and ref not in all_forms:
                errors.append(f"concept {entry.stem}: references missing form '{ref}'")

    if errors:
        for e in errors:
            click.echo(f"ERROR: {e}", err=True)
        sys.exit(EXIT_ERROR)

    count = len(paths)
    click.echo(f"OK: {count} form(s) valid")
