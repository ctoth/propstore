"""pks validate / build / query / export-aliases — top-level compiler commands."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import click
import yaml

from compiler.cli.helpers import EXIT_VALIDATION
from compiler.cli.repository import Repository


@click.command()
@click.pass_obj
def validate(obj: dict) -> None:
    """Validate all concepts and claims. Runs CEL type-checking."""
    from compiler.validate import load_concepts, validate_concepts
    from compiler.validate_claims import (
        build_concept_registry,
        load_claim_files,
        validate_claims,
    )

    repo: Repository = obj["repo"]
    cpd = repo.concepts_dir
    if not cpd.exists():
        click.echo(f"ERROR: Concepts directory '{cpd}' does not exist", err=True)
        sys.exit(1)

    concepts = load_concepts(cpd)
    if not concepts:
        click.echo("No concept files found.")
        return

    # Validate form schema files
    from compiler.form_utils import validate_form_files

    form_errors = validate_form_files(repo.forms_dir)
    for e in form_errors:
        click.echo(f"ERROR (form): {e}", err=True)

    concept_result = validate_concepts(
        concepts,
        claims_dir=repo.claims_dir if repo.claims_dir.exists() else None,
        repo=repo,
    )

    for w in concept_result.warnings:
        click.echo(f"WARNING: {w}", err=True)
    for e in concept_result.errors:
        click.echo(f"ERROR: {e}", err=True)

    # Claims (if directory exists)
    claim_error_count = 0
    claim_file_count = 0
    cd = repo.claims_dir
    if cd.exists():
        files = load_claim_files(cd)
        claim_file_count = len(files)
        if files:
            registry = build_concept_registry(repo)
            claim_result = validate_claims(files, registry)
            for w in claim_result.warnings:
                click.echo(f"WARNING: {w}", err=True)
            for e in claim_result.errors:
                click.echo(f"ERROR: {e}", err=True)
            claim_error_count = len(claim_result.errors)

    total_errors = len(concept_result.errors) + claim_error_count + len(form_errors)

    if total_errors == 0:
        click.echo(
            f"Validation passed: {len(concepts)} concept(s), "
            f"{claim_file_count} claim file(s)")
    else:
        click.echo(f"Validation FAILED: {total_errors} error(s)", err=True)
        sys.exit(EXIT_VALIDATION)


@click.command()
@click.option("-o", "--output", default=None, help="Output path")
@click.option("--force", is_flag=True, help="Force rebuild")
@click.pass_obj
def build(obj: dict, output: str | None, force: bool) -> None:
    """Validate everything, build sidecar, run conflict detection."""
    from compiler.build_sidecar import build_sidecar
    from compiler.validate import load_concepts, validate_concepts
    from compiler.validate_claims import (
        build_concept_registry,
        load_claim_files,
        validate_claims,
    )

    repo: Repository = obj["repo"]
    cpd = repo.concepts_dir
    if not cpd.exists():
        click.echo(f"ERROR: Concepts directory '{cpd}' does not exist", err=True)
        sys.exit(1)

    concepts = load_concepts(cpd)
    if not concepts:
        click.echo("No concept files found.")
        return

    # Step 0: Validate form schema files
    from compiler.form_utils import validate_form_files

    form_errors = validate_form_files(repo.forms_dir)
    if form_errors:
        for e in form_errors:
            click.echo(f"ERROR (form): {e}", err=True)
        click.echo("Build aborted: form validation failed.", err=True)
        sys.exit(EXIT_VALIDATION)

    # Step 1: Validate concepts
    concept_result = validate_concepts(
        concepts,
        claims_dir=repo.claims_dir if repo.claims_dir.exists() else None,
        repo=repo,
    )
    if not concept_result.ok:
        for e in concept_result.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Build aborted: concept validation failed.", err=True)
        sys.exit(EXIT_VALIDATION)

    # Step 2: Validate claims (if any)
    claim_files = None
    concept_registry = None
    cd = repo.claims_dir
    if cd.exists():
        files = load_claim_files(cd)
        if files:
            concept_registry = build_concept_registry(repo)
            claim_result = validate_claims(files, concept_registry)
            if not claim_result.ok:
                for e in claim_result.errors:
                    click.echo(f"ERROR: {e}", err=True)
                click.echo("Build aborted: claim validation failed.", err=True)
                sys.exit(EXIT_VALIDATION)
            claim_files = files

    # Step 3: Build sidecar
    sidecar_path = Path(output) if output else repo.sidecar_path
    rebuilt = build_sidecar(
        concepts, sidecar_path, force=force,
        claim_files=claim_files,
        concept_registry=concept_registry,
        repo=repo,
    )

    # Step 4: Summary via WorldModel (proves the roundtrip)
    from compiler.world_model import WorldModel

    warning_count = len(concept_result.warnings)
    try:
        wm = WorldModel(repo)
        s = wm.stats()
        conflict_count = s["conflicts"]
        claim_count = s["claims"]

        conflicts = wm.conflicts()
        for c in conflicts:
            click.echo(
                f"  {c['warning_class']}: {c['concept_id']} "
                f"({c['claim_a_id']} vs {c['claim_b_id']})", err=True)
        wm.close()
    except FileNotFoundError:
        # Sidecar didn't get written (no claims?) — fall back to counting
        conflict_count = 0
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
@click.pass_obj
def query(obj: dict, sql: str) -> None:
    """Run raw SQL against the sidecar SQLite."""
    repo: Repository = obj["repo"]
    sidecar = repo.sidecar_path
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
@click.pass_obj
def export_aliases(obj: dict, fmt: str) -> None:
    """Export the alias lookup table."""
    repo: Repository = obj["repo"]
    all_concepts = repo.concepts_dir
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


@click.command("import-papers")
@click.option(
    "--papers-root",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to research-papers-plugin papers/ directory",
)
@click.option(
    "--output-dir",
    default=None,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory to write imported claim files into",
)
@click.option("--dry-run", is_flag=True, help="Report what would be imported without writing")
@click.pass_obj
def import_papers(obj: dict, papers_root: Path, output_dir: Path | None, dry_run: bool) -> None:
    """Import paper-local claims.yaml files from a papers/ corpus."""
    repo: Repository = obj["repo"]
    if output_dir is None:
        output_dir = repo.claims_dir
    paper_dirs = sorted(entry for entry in papers_root.iterdir() if entry.is_dir())
    imports: list[tuple[Path, Path]] = []
    for paper_dir in paper_dirs:
        source_path = paper_dir / "claims.yaml"
        if not source_path.exists():
            continue
        imports.append((source_path, output_dir / f"{paper_dir.name}.yaml"))

    if not imports:
        click.echo(f"No claims.yaml files found under {papers_root}")
        return

    if dry_run:
        for source_path, destination_path in imports:
            click.echo(f"Would import {source_path} -> {destination_path}")
        click.echo(f"Would import {len(imports)} paper claim file(s)")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    for source_path, destination_path in imports:
        with open(source_path) as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise click.ClickException(f"{source_path} is not a YAML mapping")
        source = data.get("source")
        if not isinstance(source, dict):
            source = {}
            data["source"] = source
        source["paper"] = source_path.parent.name
        with open(destination_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    click.echo(f"Imported {len(imports)} paper claim file(s) into {output_dir}")


# ── World command group ──────────────────────────────────────────────


@click.group()
@click.pass_obj
def world(obj: dict) -> None:
    """Query the compiled knowledge base."""
    pass


@world.command("status")
@click.pass_obj
def world_status(obj: dict) -> None:
    """Show knowledge base stats (concepts, claims, conflicts)."""
    from compiler.world_model import WorldModel

    repo: Repository = obj["repo"]
    try:
        wm = WorldModel(repo)
    except FileNotFoundError:
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)

    s = wm.stats()
    click.echo(f"Concepts: {s['concepts']}")
    click.echo(f"Claims:   {s['claims']}")
    click.echo(f"Conflicts: {s['conflicts']}")
    wm.close()


@world.command("query")
@click.argument("concept_id")
@click.pass_obj
def world_query(obj: dict, concept_id: str) -> None:
    """Show all claims for a concept."""
    from compiler.world_model import WorldModel

    repo: Repository = obj["repo"]
    try:
        wm = WorldModel(repo)
    except FileNotFoundError:
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)

    # Try alias resolution
    resolved = wm.resolve_alias(concept_id) or concept_id
    concept = wm.get_concept(resolved)
    if concept is None:
        click.echo(f"Unknown concept: {concept_id}", err=True)
        wm.close()
        sys.exit(1)

    click.echo(f"{concept['canonical_name']} ({resolved})")
    claims = wm.claims_for(resolved)
    if not claims:
        click.echo("  (no claims)")
    for c in claims:
        conds = c.get("conditions_cel") or "[]"
        click.echo(f"  {c['id']}: {c['type']} value={c.get('value')} conditions={conds}")
    wm.close()


@world.command("bind")
@click.argument("args", nargs=-1)
@click.pass_obj
def world_bind(obj: dict, args: tuple[str, ...]) -> None:
    """Show active claims under condition bindings.

    Usage: pks world bind task=speech [concept_id]

    Arguments with '=' are bindings, the last argument without '=' is a concept filter.
    """
    from compiler.world_model import WorldModel

    repo: Repository = obj["repo"]
    try:
        wm = WorldModel(repo)
    except FileNotFoundError:
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)

    # Parse: args with '=' are bindings, last arg without '=' is concept_id
    binding_args = [a for a in args if "=" in a]
    non_binding = [a for a in args if "=" not in a]
    query_concept = non_binding[-1] if non_binding else None

    parsed: dict[str, str] = {}
    for b in binding_args:
        if "=" not in b:
            click.echo(f"Invalid binding: {b} (expected key=value)", err=True)
            wm.close()
            sys.exit(1)
        key, _, value = b.partition("=")
        parsed[key] = value

    bound = wm.bind(**parsed)

    if query_concept:
        resolved = wm.resolve_alias(query_concept) or query_concept
        result = bound.value_of(resolved)
        click.echo(f"{resolved}: {result.status}")
        for c in result.claims:
            click.echo(f"  {c['id']}: value={c.get('value')} source={c.get('source_paper')}")
    else:
        active = bound.active_claims()
        click.echo(f"Active claims: {len(active)}")
        for c in active:
            conds = c.get("conditions_cel") or "[]"
            click.echo(
                f"  {c['id']}: {c.get('concept_id', '?')} "
                f"value={c.get('value')} conditions={conds}")

    wm.close()


@world.command("explain")
@click.argument("claim_id")
@click.pass_obj
def world_explain(obj: dict, claim_id: str) -> None:
    """Show the stance chain for a claim."""
    from compiler.world_model import WorldModel

    repo: Repository = obj["repo"]
    try:
        wm = WorldModel(repo)
    except FileNotFoundError:
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)

    claim = wm.get_claim(claim_id)
    if claim is None:
        click.echo(f"Unknown claim: {claim_id}", err=True)
        wm.close()
        sys.exit(1)

    click.echo(f"{claim_id}: {claim['type']} concept={claim.get('concept_id')} value={claim.get('value')}")
    chain = wm.explain(claim_id)
    if not chain:
        click.echo("  (no stances)")
    for s in chain:
        click.echo(
            f"  {s['stance_type']} -> {s['target_claim_id']}"
            f" (strength={s.get('strength')}, note={s.get('note')})")
    wm.close()


def _parse_bindings(args: tuple[str, ...]) -> tuple[dict[str, str], str | None]:
    """Parse CLI args into (bindings, concept_id).

    Arguments with '=' are bindings, the last argument without '=' is concept_id.
    """
    binding_args = [a for a in args if "=" in a]
    non_binding = [a for a in args if "=" not in a]
    concept_id = non_binding[-1] if non_binding else None

    parsed: dict[str, str] = {}
    for b in binding_args:
        key, _, value = b.partition("=")
        parsed[key] = value

    return parsed, concept_id


@world.command("derive")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.pass_obj
def world_derive(obj: dict, concept_id: str, args: tuple[str, ...]) -> None:
    """Derive a value for a concept via parameterization relationships.

    Usage: pks world derive concept5 task=speech
    """
    from compiler.world_model import WorldModel

    repo: Repository = obj["repo"]
    try:
        wm = WorldModel(repo)
    except FileNotFoundError:
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)

    bindings, _ = _parse_bindings(args)
    resolved = wm.resolve_alias(concept_id) or concept_id
    bound = wm.bind(**bindings)
    result = bound.derived_value(resolved)

    click.echo(f"{resolved}: {result.status}")
    if result.value is not None:
        click.echo(f"  value: {result.value}")
    if result.formula:
        click.echo(f"  formula: {result.formula}")
    if result.input_values:
        click.echo(f"  inputs: {result.input_values}")
    if result.exactness:
        click.echo(f"  exactness: {result.exactness}")
    wm.close()


@world.command("resolve")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option("--strategy", required=True,
              type=click.Choice(["recency", "sample_size", "stance", "override"]))
@click.option("--override", "override_id", default=None, help="Claim ID for override strategy")
@click.pass_obj
def world_resolve(obj: dict, concept_id: str, args: tuple[str, ...],
                  strategy: str, override_id: str | None) -> None:
    """Resolve a conflicted concept using a strategy.

    Usage: pks world resolve concept1 task=speech --strategy sample_size
    """
    from compiler.world_model import ResolutionStrategy, WorldModel, resolve

    repo: Repository = obj["repo"]
    try:
        wm = WorldModel(repo)
    except FileNotFoundError:
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)

    bindings, _ = _parse_bindings(args)
    resolved = wm.resolve_alias(concept_id) or concept_id
    bound = wm.bind(**bindings)

    strat = ResolutionStrategy(strategy)
    overrides = {resolved: override_id} if override_id else None

    try:
        result = resolve(bound, resolved, strat, world=wm, overrides=overrides)
    except ValueError as e:
        click.echo(f"ERROR: {e}", err=True)
        wm.close()
        sys.exit(1)

    click.echo(f"{resolved}: {result.status}")
    if result.value is not None:
        click.echo(f"  value: {result.value}")
    if result.winning_claim_id:
        click.echo(f"  winner: {result.winning_claim_id}")
    if result.strategy:
        click.echo(f"  strategy: {result.strategy}")
    if result.reason:
        click.echo(f"  reason: {result.reason}")
    wm.close()


@world.command("hypothetical")
@click.argument("args", nargs=-1)
@click.option("--remove", multiple=True, help="Claim ID to remove")
@click.option("--add", "add_json", default=None, help="JSON synthetic claim")
@click.pass_obj
def world_hypothetical(obj: dict, args: tuple[str, ...],
                       remove: tuple[str, ...], add_json: str | None) -> None:
    """Show what changes if claims are removed/added.

    Usage: pks world hypothetical task=speech --remove claim2
    """
    from compiler.world_model import HypotheticalWorld, SyntheticClaim, WorldModel

    repo: Repository = obj["repo"]
    try:
        wm = WorldModel(repo)
    except FileNotFoundError:
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)

    bindings, _ = _parse_bindings(args)
    bound = wm.bind(**bindings)

    synthetics: list[SyntheticClaim] = []
    if add_json:
        data = json.loads(add_json)
        if isinstance(data, dict):
            data = [data]
        for d in data:
            synthetics.append(SyntheticClaim(
                id=d["id"],
                concept_id=d["concept_id"],
                type=d.get("type", "parameter"),
                value=d.get("value"),
                conditions=d.get("conditions", []),
            ))

    hypo = HypotheticalWorld(bound, remove=list(remove), add=synthetics)
    diff = hypo.diff()

    if not diff:
        click.echo("No changes detected.")
    else:
        for cid, (base_vr, hypo_vr) in diff.items():
            click.echo(f"{cid}: {base_vr.status} → {hypo_vr.status}")
    wm.close()


@world.command("chain")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option("--strategy", default=None,
              type=click.Choice(["recency", "sample_size", "stance", "override"]))
@click.pass_obj
def world_chain(obj: dict, concept_id: str, args: tuple[str, ...],
                strategy: str | None) -> None:
    """Traverse the parameter space to derive a target concept.

    Usage: pks world chain concept5 task=speech --strategy sample_size
    """
    from compiler.world_model import ResolutionStrategy, WorldModel

    repo: Repository = obj["repo"]
    try:
        wm = WorldModel(repo)
    except FileNotFoundError:
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)

    bindings, _ = _parse_bindings(args)
    resolved = wm.resolve_alias(concept_id) or concept_id

    strat = ResolutionStrategy(strategy) if strategy else None
    result = wm.chain_query(resolved, strategy=strat, **bindings)

    click.echo(f"Target: {resolved}")
    click.echo(f"Result: {result.result.status}")
    if hasattr(result.result, "value") and result.result.value is not None:
        click.echo(f"  value: {result.result.value}")
    click.echo(f"Steps ({len(result.steps)}):")
    for step in result.steps:
        click.echo(f"  {step.concept_id}: {step.value} ({step.source})")
    wm.close()


@world.command("export-graph")
@click.argument("args", nargs=-1)
@click.option("--format", "fmt", type=click.Choice(["dot", "json"]), default="dot")
@click.option("--group", "group_id", type=int, default=None,
              help="Parameterization group ID to filter by")
@click.option("--output", "output_file", default=None, help="Output file path")
@click.pass_obj
def world_export_graph(obj: dict, args: tuple[str, ...], fmt: str,
                       group_id: int | None, output_file: str | None) -> None:
    """Export the knowledge graph as DOT or JSON.

    Usage: pks world export-graph task=speech --format dot --output graph.dot
    """
    from compiler.graph_export import build_knowledge_graph
    from compiler.world_model import WorldModel

    repo: Repository = obj["repo"]
    try:
        wm = WorldModel(repo)
    except FileNotFoundError:
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)

    bindings, _ = _parse_bindings(args)
    bound = wm.bind(**bindings) if bindings else None

    graph = build_knowledge_graph(wm, bound=bound, group_id=group_id)

    if fmt == "json":
        output = json.dumps(graph.to_json(), indent=2)
    else:
        output = graph.to_dot()

    if output_file:
        Path(output_file).write_text(output)
        click.echo(f"Graph written to {output_file}")
    else:
        click.echo(output)

    wm.close()


@world.command("sensitivity")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_obj
def world_sensitivity(obj: dict, concept_id: str, args: tuple[str, ...],
                      fmt: str) -> None:
    """Analyze which input most influences a derived quantity.

    Usage: pks world sensitivity concept5 task=speech
    """
    from compiler.sensitivity import analyze_sensitivity
    from compiler.world_model import WorldModel

    repo: Repository = obj["repo"]
    try:
        wm = WorldModel(repo)
    except FileNotFoundError:
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)

    bindings, _ = _parse_bindings(args)
    resolved = wm.resolve_alias(concept_id) or concept_id
    bound = wm.bind(**bindings)

    result = analyze_sensitivity(wm, resolved, bound)

    if result is None:
        click.echo(f"No sensitivity analysis available for {resolved}.")
        wm.close()
        return

    if fmt == "json":
        data = {
            "concept_id": result.concept_id,
            "formula": result.formula,
            "output_value": result.output_value,
            "input_values": result.input_values,
            "entries": [
                {
                    "input_concept_id": e.input_concept_id,
                    "partial_derivative_expr": e.partial_derivative_expr,
                    "partial_derivative_value": e.partial_derivative_value,
                    "elasticity": e.elasticity,
                }
                for e in result.entries
            ],
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Sensitivity: {resolved}")
        click.echo(f"Formula: {result.formula}")
        click.echo(f"Output value: {result.output_value}")
        click.echo(f"Inputs: {result.input_values}")
        click.echo("")
        click.echo(f"{'Input':<25} {'Partial':>12} {'Elasticity':>12}")
        click.echo("-" * 51)
        for e in result.entries:
            pval = f"{e.partial_derivative_value:.6g}" if e.partial_derivative_value is not None else "N/A"
            elast = f"{e.elasticity:.4f}" if e.elasticity is not None else "N/A"
            click.echo(f"{e.input_concept_id:<25} {pval:>12} {elast:>12}")

    wm.close()
