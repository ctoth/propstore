"""pks form — subcommands for managing form definitions."""
from __future__ import annotations

import json
import sys

import click
import yaml

from propstore.cli.helpers import EXIT_ERROR, write_yaml_file
from propstore.cli.repository import Repository


@click.group()
def form() -> None:
    """Manage form definitions."""


# ── form list ────────────────────────────────────────────────────────

@form.command("list")
@click.option("--dims", "dims_filter", default=None,
              help="Filter by dimensions (e.g. M:1,L:1,T:-2). Implies showing dims column.")
@click.option("--show-dims", "show_dims_flag", is_flag=True, default=False,
              help="Show dimensions column.")
@click.pass_obj
def list_forms(obj: dict, dims_filter: str | None, show_dims_flag: bool) -> None:
    """List all available forms.

    With --show-dims: show dimensions column.
    With --dims M:1,L:1,T:-2: filter to forms matching those dimensions.
    """
    repo: Repository = obj["repo"]
    fdir = repo.forms_dir
    if not fdir.exists():
        click.echo("No forms directory found.")
        return

    from propstore.form_utils import load_all_forms
    registry = load_all_forms(fdir)

    # Parse filter dimensions if provided
    filter_dims: dict[str, int] | None = None
    if dims_filter is not None:
        filter_dims = _parse_dims_spec(dims_filter)

    show_dims = show_dims_flag or dims_filter is not None

    for fd in sorted(registry.values(), key=lambda f: f.name):
        if filter_dims is not None:
            from bridgman import dims_equal
            form_dims = fd.dimensions or ({} if fd.is_dimensionless else None)
            if form_dims is None or not dims_equal(form_dims, filter_dims):
                continue

        unit = fd.unit_symbol or ""
        unit_col = f"  [{unit}]" if unit else ""
        if show_dims:
            dims_str = _format_dims_col(fd.dimensions, fd.is_dimensionless)
            click.echo(f"  {fd.name:30s}{unit_col:10s}  {dims_str}")
        else:
            click.echo(f"  {fd.name:30s}{unit_col}")


def _parse_dims_spec(spec: str) -> dict[str, int]:
    """Parse 'M:1,L:1,T:-2' into {'M': 1, 'L': 1, 'T': -2}."""
    result: dict[str, int] = {}
    for part in spec.split(","):
        part = part.strip()
        if ":" not in part:
            continue
        key, val = part.split(":", 1)
        result[key.strip()] = int(val.strip())
    return result


def _format_dims_col(dimensions: dict[str, int] | None, is_dimensionless: bool) -> str:
    """Format dimensions for display column."""
    if dimensions is None:
        return "(dimensionless)" if is_dimensionless else ""
    if not dimensions or all(v == 0 for v in dimensions.values()):
        return "(dimensionless)"
    try:
        from bridgman import format_dims
        return format_dims(dimensions)
    except ImportError:
        return str(dimensions)


# ── form show ────────────────────────────────────────────────────────

@form.command()
@click.argument("name")
@click.pass_obj
def show(obj: dict, name: str) -> None:
    """Show full form definition YAML, plus algebra if sidecar exists."""
    repo: Repository = obj["repo"]
    path = repo.forms_dir / f"{name}.yaml"
    if not path.exists():
        click.echo(f"ERROR: Form '{name}' not found", err=True)
        sys.exit(EXIT_ERROR)
    click.echo(path.read_text())

    # Display unit conversions if the form has any
    from propstore.form_utils import load_form
    form_def = load_form(repo.forms_dir, name)
    if form_def and form_def.conversions:
        click.echo("Unit Conversions:")
        si = form_def.unit_symbol or "SI"
        for conv in form_def.conversions.values():
            if conv.type == "multiplicative":
                click.echo(f"  {conv.unit} \u2192 {si}  (\u00d7{conv.multiplier:g})")
            elif conv.type == "affine":
                click.echo(f"  {conv.unit} \u2192 {si}  (\u00d7{conv.multiplier:g} + {conv.offset:g}, affine)")
            elif conv.type == "logarithmic":
                click.echo(f"  {conv.unit} \u2192 {si}  (logarithmic, ref={conv.reference:g})")
            else:
                click.echo(f"  {conv.unit} \u2192 {si}  ({conv.type})")

    # Append algebra from sidecar if available
    if repo.sidecar_path.exists():
        try:
            from propstore.world import WorldModel
            wm = WorldModel(repo)
            decompositions = wm.form_algebra_for(name)
            uses = wm.form_algebra_using(name)
            wm.close()

            if decompositions or uses:
                click.echo("---")
                click.echo("# Form Algebra (derived from concept parameterizations)")
            if decompositions:
                click.echo("decompositions:")
                for entry in decompositions:
                    input_forms = json.loads(entry["input_forms"])
                    click.echo(f"  - {name} = {' * '.join(input_forms)}")
                    if entry.get("source_formula"):
                        click.echo(f"    from: {entry['source_formula']} ({entry.get('source_concept_id', '?')})")
            if uses:
                click.echo("used_in:")
                for entry in uses:
                    input_forms = json.loads(entry["input_forms"])
                    click.echo(f"  - {entry['output_form']} = {' * '.join(input_forms)}")
        except (FileNotFoundError, Exception):
            pass  # No sidecar or error — just show the YAML


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
    write_yaml_file(path, data)
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
