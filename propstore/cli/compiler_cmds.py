"""pks validate / build / query / export-aliases — top-level compiler commands."""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

import click
import yaml

from propstore.cli.helpers import EXIT_VALIDATION, open_world_model, write_yaml_file
from propstore.cli.repository import Repository


def _format_value_with_si(claim: dict) -> str:
    """Format a claim's value with optional SI normalization.

    Returns e.g. ``value=0.2 kHz (SI: 200.0 Hz)`` when the stored unit
    differs from the canonical SI unit, or ``value=200.0 Hz`` when they match.
    """
    value = claim.get("value")
    unit = claim.get("unit")
    value_si = claim.get("value_si")
    if unit and value_si is not None and float(value_si) != float(value):
        return f"value={value} {unit} (SI: {value_si} Hz)"
    elif unit:
        return f"value={value} {unit}"
    else:
        return f"value={value}"


@click.command()
@click.pass_obj
def validate(obj: dict) -> None:
    """Validate all concepts and claims. Runs CEL type-checking."""
    from propstore.validate import load_concepts, validate_concepts
    from propstore.validate_claims import (
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
    from propstore.form_utils import validate_form_files

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
    from propstore.build_sidecar import build_sidecar
    from propstore.validate import load_concepts, validate_concepts
    from propstore.validate_claims import (
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
    from propstore.form_utils import validate_form_files

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

    # Step 1b: Load and validate contexts (if any)
    from propstore.validate_contexts import load_contexts, validate_contexts
    context_files = None
    context_ids: set[str] = set()
    if repo.contexts_dir.exists():
        ctx_list = load_contexts(repo.contexts_dir)
        if ctx_list:
            ctx_result = validate_contexts(ctx_list)
            for w in ctx_result.warnings:
                click.echo(f"WARNING (context): {w}", err=True)
            if not ctx_result.ok:
                for e in ctx_result.errors:
                    click.echo(f"ERROR (context): {e}", err=True)
                click.echo("Build aborted: context validation failed.", err=True)
                sys.exit(EXIT_VALIDATION)
            context_files = ctx_list
            context_ids = {c.data["id"] for c in ctx_list if c.data.get("id")}

    # Step 2: Validate claims (if any)
    claim_files = None
    concept_registry = None
    cd = repo.claims_dir
    if cd.exists():
        files = load_claim_files(cd)
        if files:
            concept_registry = build_concept_registry(repo)
            claim_result = validate_claims(
                files, concept_registry,
                context_ids=context_ids if context_ids else None,
            )
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
        context_files=context_files,
    )

    # Step 4: Summary via WorldModel (proves the roundtrip)
    from propstore.world import WorldModel

    warning_count = len(concept_result.warnings)
    try:
        wm = WorldModel(repo)
        s = wm.stats()
        conflict_count = s["conflicts"]
        claim_count = s["claims"]

        conflicts = wm.conflicts()
        # Group PHI_NODEs by concept for compact display
        from collections import defaultdict
        phi_groups: dict[str, set[str]] = defaultdict(set)
        for c in conflicts:
            wc = c["warning_class"]
            if wc in ("PHI_NODE", "CONTEXT_PHI_NODE"):
                key = f"{wc}: {c['concept_id']}"
                phi_groups[key].add(c["claim_a_id"])
                phi_groups[key].add(c["claim_b_id"])
            else:
                click.echo(
                    f"  {wc}: {c['concept_id']} "
                    f"({c['claim_a_id']} vs {c['claim_b_id']})", err=True)
        for key, claim_ids in phi_groups.items():
            sorted_ids = sorted(claim_ids)
            click.echo(
                f"  {key} — {len(sorted_ids)} branches: "
                f"{', '.join(sorted_ids)}", err=True)
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
    conn.execute("PRAGMA query_only=ON")
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

    from propstore.validate import load_concepts

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


def _resolve_concept_refs(
    claim: dict, name_to_id: dict[str, str],
) -> tuple[dict, int, int]:
    """Resolve concept names to IDs within a single claim.

    Returns (modified_claim, resolved_count, unresolved_count).
    """
    _CONCEPT_ID_RE = re.compile(r"^concept\d+$")
    resolved = 0
    unresolved = 0

    def _resolve_one(ref: str) -> str:
        nonlocal resolved, unresolved
        if _CONCEPT_ID_RE.match(ref):
            return ref  # already an ID
        if ref in name_to_id:
            resolved += 1
            return name_to_id[ref]
        unresolved += 1
        click.echo(f"  WARNING: concept name '{ref}' not found in registry", err=True)
        return ref

    # claim.concepts[] — list of concept references (observations)
    if "concepts" in claim and isinstance(claim["concepts"], list):
        claim["concepts"] = [
            _resolve_one(c) if isinstance(c, str) else c
            for c in claim["concepts"]
        ]

    # claim.concept — single concept reference (parameter claims)
    if "concept" in claim and isinstance(claim["concept"], str):
        claim["concept"] = _resolve_one(claim["concept"])

    # claim.variables[].concept — equation variable concepts
    for var in claim.get("variables", []) or []:
        if isinstance(var, dict) and "concept" in var and isinstance(var["concept"], str):
            var["concept"] = _resolve_one(var["concept"])

    # Resolve concept names in sympy expression strings (whole identifiers only)
    if "sympy" in claim and isinstance(claim["sympy"], str):
        sympy_str = claim["sympy"]
        for name, cid in name_to_id.items():
            # Replace whole identifiers only: bounded by non-word chars or string edges
            sympy_str = re.sub(r"(?<!\w)" + re.escape(name) + r"(?!\w)", cid, sympy_str)
        if sympy_str != claim["sympy"]:
            # Count how many substitutions happened
            # (already counted via the field-level resolvers above, so just update)
            claim["sympy"] = sympy_str

    return claim, resolved, unresolved


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
@click.option("--strict", is_flag=True, help="Abort import if any dimensional check fails")
@click.pass_obj
def import_papers(obj: dict, papers_root: Path, output_dir: Path | None, dry_run: bool, strict: bool) -> None:
    """Import paper-local claims.yaml files from a papers/ corpus."""
    from propstore.validate import load_concepts

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

    # Build concept name → ID lookup table
    name_to_id: dict[str, str] = {}
    concepts = load_concepts(repo.concepts_dir)
    id_to_concept: dict[str, dict] = {}
    for c in concepts:
        cid = c.data.get("id", "")
        name = c.data.get("canonical_name", "")
        if cid and name:
            name_to_id[name] = cid
        if cid:
            id_to_concept[cid] = c.data
        # Also add aliases
        for alias in c.data.get("aliases", []) or []:
            alias_name = alias.get("name", "") if isinstance(alias, dict) else ""
            if alias_name:
                name_to_id[alias_name] = cid

    # Load and resolve all paper data (needed for both dry-run and real import)
    resolved_papers: list[tuple[Path, Path, dict]] = []
    total_claims = 0
    total_resolved = 0
    total_unresolved = 0
    for source_path, destination_path in imports:
        with open(source_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise click.ClickException(f"{source_path} is not a YAML mapping")
        source = data.get("source")
        if not isinstance(source, dict):
            source = {}
            data["source"] = source
        source_name = source_path.parent.name
        source["paper"] = source_name
        # Prefix claim IDs with knowledge source for global uniqueness
        for claim in data.get("claims", []) or []:
            if isinstance(claim, dict):
                if "id" in claim and ":" not in claim["id"]:
                    claim["id"] = f"{source_name}:{claim['id']}"
                total_claims += 1
                # Prefix inline stance targets only if they reference
                # claims within this same file (local IDs)
                local_ids = {
                    c.get("id", "").split(":")[-1]
                    for c in data.get("claims", []) or []
                    if isinstance(c, dict) and c.get("id")
                }
                for stance in claim.get("stances", []) or []:
                    if isinstance(stance, dict):
                        target = stance.get("target")
                        if target and ":" not in target and target in local_ids:
                            stance["target"] = f"{source_name}:{target}"
                # Resolve concept names to IDs
                _, r, u = _resolve_concept_refs(claim, name_to_id)
                total_resolved += r
                total_unresolved += u
        resolved_papers.append((source_path, destination_path, data))

    # ── Dimensional pre-check (bridgman) ─────────────────────────────
    dim_verified = 0
    dim_warnings = 0
    try:
        import sympy as sp
        from bridgman import verify_expr, DimensionalError, format_dims
        from propstore.form_utils import load_form

        for _source_path, _dest_path, data in resolved_papers:
            for claim in data.get("claims", []) or []:
                if not isinstance(claim, dict):
                    continue
                if claim.get("type") != "equation":
                    continue
                sympy_str = claim.get("sympy")
                variables = claim.get("variables")
                if not sympy_str or not isinstance(variables, list):
                    continue

                # Build symbol → concept ID mapping from the variables list
                sym_to_cid: dict[str, str] = {}
                dependent_symbol: str | None = None
                for var in variables:
                    if not isinstance(var, dict):
                        continue
                    sym = var.get("symbol")
                    cid = var.get("concept")
                    if sym and cid:
                        sym_to_cid[sym] = cid
                        if var.get("role") == "dependent":
                            dependent_symbol = sym

                if not sym_to_cid:
                    continue

                # Build dim_map: symbol name → dimensions dict
                dim_map: dict[str, dict[str, int]] = {}
                skip = False
                for sym, cid in sym_to_cid.items():
                    concept_data = id_to_concept.get(cid)
                    if concept_data is None:
                        skip = True
                        break
                    form_name = concept_data.get("form")
                    fd = load_form(repo.forms_dir, form_name)
                    if fd is None:
                        skip = True
                        break
                    if fd.dimensions is not None:
                        dim_map[sym] = dict(fd.dimensions)
                    elif fd.is_dimensionless:
                        dim_map[sym] = {}
                    else:
                        skip = True
                        break
                if skip:
                    continue

                # Parse and verify
                claim_id = claim.get("id", "<unknown>")
                try:
                    parsed = sp.sympify(sympy_str)
                    # If sympy field is not an Eq, wrap it as Eq(dependent, rhs)
                    if not isinstance(parsed, sp.Eq) and dependent_symbol:
                        parsed = sp.Eq(sp.Symbol(dependent_symbol), parsed)
                    if not isinstance(parsed, sp.Eq):
                        continue

                    if verify_expr(parsed, dim_map):
                        dim_verified += 1
                    else:
                        dim_warnings += 1
                        # Build detail strings
                        details = []
                        for sym, cid in sym_to_cid.items():
                            dims = dim_map.get(sym, {})
                            details.append(f"  {sym} ({cid}): {format_dims(dims)}")
                        click.echo(
                            f"WARNING: dimensional mismatch in claim '{claim_id}':\n"
                            + "\n".join(details),
                            err=True,
                        )
                except (DimensionalError, KeyError, TypeError) as exc:
                    dim_warnings += 1
                    click.echo(
                        f"WARNING: dimensional check error in claim '{claim_id}': {exc}",
                        err=True,
                    )
                except Exception:
                    pass  # non-fatal: skip claims that can't be parsed
    except ImportError:
        pass  # sympy or bridgman not available — skip dim check

    eq_total = dim_verified + dim_warnings
    if eq_total > 0:
        click.echo(
            f"Dimensional check: {dim_verified} equation(s) verified, "
            f"{dim_warnings} warning(s)"
        )

    if strict and dim_warnings > 0:
        raise click.ClickException(
            f"Aborting import: {dim_warnings} dimensional warning(s) in --strict mode"
        )

    # ── Write files (skip in dry-run mode) ───────────────────────────
    if dry_run:
        for source_path, destination_path, _data in resolved_papers:
            click.echo(f"Would import {source_path} -> {destination_path}")
        click.echo(f"Would import {len(resolved_papers)} paper claim file(s)")
        click.echo(f"Resolved {total_resolved} concept name(s) to IDs, {total_unresolved} unresolved")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    for _source_path, destination_path, data in resolved_papers:
        write_yaml_file(destination_path, data)

    click.echo(f"Imported {len(resolved_papers)} paper claim file(s) into {output_dir} ({total_claims} claims)")
    click.echo(f"Resolved {total_resolved} concept name(s) to IDs, {total_unresolved} unresolved")


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
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        s = wm.stats()
        click.echo(f"Concepts: {s['concepts']}")
        click.echo(f"Claims:   {s['claims']}")
        click.echo(f"Conflicts: {s['conflicts']}")


@world.command("query")
@click.argument("concept_id")
@click.pass_obj
def world_query(obj: dict, concept_id: str) -> None:
    """Show all claims for a concept."""
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        # Try alias resolution
        resolved = wm.resolve_alias(concept_id) or concept_id
        concept = wm.get_concept(resolved)
        if concept is None:
            click.echo(f"Unknown concept: {concept_id}", err=True)
            sys.exit(1)

        click.echo(f"{concept['canonical_name']} ({resolved})")
        claims = wm.claims_for(resolved)
        if not claims:
            click.echo("  (no claims)")
        for c in claims:
            conds = c.get("conditions_cel") or "[]"
            val_part = _format_value_with_si(c)
            click.echo(f"  {c['id']}: {c['type']} {val_part} conditions={conds}")


@world.command("bind")
@click.argument("args", nargs=-1)
@click.pass_obj
def world_bind(obj: dict, args: tuple[str, ...]) -> None:
    """Show active claims under condition bindings.

    Usage: pks world bind domain=example [concept_id]

    Arguments with '=' are bindings, the last argument without '=' is a concept filter.
    """
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        # Parse: args with '=' are bindings, last arg without '=' is concept_id
        binding_args = [a for a in args if "=" in a]
        non_binding = [a for a in args if "=" not in a]
        query_concept = non_binding[-1] if non_binding else None

        parsed: dict[str, str] = {}
        for b in binding_args:
            if "=" not in b:
                click.echo(f"Invalid binding: {b} (expected key=value)", err=True)
                sys.exit(1)
            key, _, value = b.partition("=")
            parsed[key] = value

        bound = wm.bind(**parsed)

        if query_concept:
            resolved = wm.resolve_alias(query_concept) or query_concept
            result = bound.value_of(resolved)
            click.echo(f"{resolved}: {result.status}")
            for c in result.claims:
                val_part = _format_value_with_si(c)
                click.echo(f"  {c['id']}: {val_part} source={c.get('source_paper')}")
        else:
            active = bound.active_claims()
            click.echo(f"Active claims: {len(active)}")
            for c in active:
                conds = c.get("conditions_cel") or "[]"
                val_part = _format_value_with_si(c)
                click.echo(
                    f"  {c['id']}: {c.get('concept_id', '?')} "
                    f"{val_part} conditions={conds}")


@world.command("explain")
@click.argument("claim_id")
@click.pass_obj
def world_explain(obj: dict, claim_id: str) -> None:
    """Show the stance chain for a claim."""
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        claim = wm.get_claim(claim_id)
        if claim is None:
            click.echo(f"Unknown claim: {claim_id}", err=True)
            sys.exit(1)

    click.echo(f"{claim_id}: {claim['type']} concept={claim.get('concept_id')} value={claim.get('value')}")
    chain = wm.explain(claim_id)
    if not chain:
        click.echo("  (no stances)")
    for s in chain:
        src = s['claim_id']
        indent = "  " if src == claim_id else "    "
        click.echo(
            f"{indent}{src} {s['stance_type']} -> {s['target_claim_id']}"
            f" (strength={s.get('strength')}, note={s.get('note')})")
    wm.close()


@world.command("algorithms")
@click.option("--stage", default=None, help="Filter by processing stage")
@click.option("--concept", default=None, help="Filter by concept")
@click.pass_obj
def world_algorithms(obj: dict, stage: str | None, concept: str | None) -> None:
    """List algorithm claims in the world model."""
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        # Fetch all algorithm claims
        all_claims = wm.claims_for(None)
        algos = [c for c in all_claims if c.get("type") == "algorithm"]

    if stage:
        algos = [c for c in algos if c.get("stage") == stage]
    if concept:
        algos = [c for c in algos if c.get("concept_id") == concept]

    if not algos:
        click.echo("No algorithm claims found.")
        wm.close()
        return

    # Table header
    click.echo(f"{'ID':<20} {'Name':<30} {'Stage':<15} {'Concept(s)'}")
    click.echo("-" * 80)
    for a in algos:
        aid = a.get("id", "?")
        name = a.get("name") or a.get("body", "")[:25] or "?"
        a_stage = a.get("stage") or "-"
        a_concept = a.get("concept_id") or "-"
        click.echo(f"{aid:<20} {name:<30} {a_stage:<15} {a_concept}")

    click.echo(f"\n{len(algos)} algorithm claim(s).")
    wm.close()


def _parse_bindings(args: tuple[str, ...]) -> tuple[dict[str, str], str | None]:
    """Parse CLI args into (bindings, concept_id).

    Arguments with '=' are bindings, the last argument without '=' is concept_id.
    """
    from propstore.cli.helpers import parse_kv_pairs

    parsed, remaining = parse_kv_pairs(args)
    concept_id = remaining[-1] if remaining else None
    return parsed, concept_id


def _bind_atms_world(
    repo: Repository,
    args: tuple[str, ...],
    *,
    context: str | None = None,
):
    from propstore.world import Environment, ReasoningBackend, RenderPolicy, WorldModel

    wm = WorldModel(repo)
    bindings, concept_id = _parse_bindings(args)
    policy = RenderPolicy(reasoning_backend=ReasoningBackend.ATMS)
    if context:
        bound = wm.bind(Environment(bindings=bindings, context_id=context), policy=policy)
    else:
        bound = wm.bind(policy=policy, **bindings)
    return wm, bound, bindings, concept_id


def _format_assumption_ids(assumption_ids: list[str] | tuple[str, ...]) -> str:
    if not assumption_ids:
        return "[]"
    return "[" + ", ".join(assumption_ids) + "]"


def _parse_queryables(queryables: tuple[str, ...]) -> list[str]:
    parsed: list[str] = []
    for queryable in queryables:
        if any(operator in queryable for operator in ("==", "!=", ">=", "<=", ">", "<")):
            parsed.append(queryable)
            continue
        if "=" in queryable:
            key, _, value = queryable.partition("=")
            parsed.append(f"{key} == '{value}'")
            continue
        parsed.append(queryable)
    return parsed


def _format_future_summary(future: dict) -> str:
    queryables = ", ".join(future.get("queryable_cels", ()))
    return (
        f"[{queryables}] -> {future['status']}"
        f" environment={_format_assumption_ids(future.get('environment', ())) }"
    )


@world.command("atms-status")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_status(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Show ATMS-native claim status, support quality, and essential support."""
    repo: Repository = obj["repo"]
    wm, bound, _bindings, concept_id = _bind_atms_world(repo, args, context=context)

    resolved = None
    if concept_id:
        resolved = wm.resolve_alias(concept_id) or concept_id
    active_claims = sorted(bound.active_claims(resolved), key=lambda claim: claim["id"])
    if not active_claims:
        click.echo("No active claims for the current ATMS view.")
        wm.close()
        return

    for claim in active_claims:
        inspection = bound.claim_status(claim["id"])
        click.echo(
            f"{claim['id']}: status={inspection.status.value} "
            f"support_quality={inspection.support_quality.value} "
            f"essential_support={_format_assumption_ids(inspection.essential_support.assumption_ids if inspection.essential_support else ())}"
        )
        click.echo(f"  reason: {inspection.reason}")

    wm.close()


@world.command("atms-context")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_context(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Show which ATMS-supported claims hold in the current bound environment."""
    repo: Repository = obj["repo"]
    wm, bound, _bindings, concept_id = _bind_atms_world(repo, args, context=context)

    environment_key = tuple(
        assumption.assumption_id
        for assumption in bound._environment.assumptions
    )
    click.echo(f"Environment: {_format_assumption_ids(environment_key)}")

    claim_ids = bound.claims_in_environment(environment_key)
    if concept_id:
        resolved = wm.resolve_alias(concept_id) or concept_id
        allowed = {
            claim["id"]
            for claim in bound.active_claims(resolved)
        }
        claim_ids = [claim_id for claim_id in claim_ids if claim_id in allowed]

    if not claim_ids:
        click.echo("No claims have exact ATMS support in the current environment.")
        wm.close()
        return

    for claim_id in sorted(claim_ids):
        inspection = bound.claim_status(claim_id)
        click.echo(
            f"{claim_id}: status={inspection.status.value} "
            f"essential_support={_format_assumption_ids(inspection.essential_support.assumption_ids if inspection.essential_support else ())}"
        )

    wm.close()


@world.command("atms-verify")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_verify(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Run ATMS label self-checks for the current bound environment."""
    repo: Repository = obj["repo"]
    wm, bound, _bindings, _concept_id = _bind_atms_world(repo, args, context=context)

    report = bound.atms_engine().verify_labels()
    if report["ok"]:
        click.echo("ATMS labels verified.")
        wm.close()
        return

    for section in (
        "consistency_errors",
        "minimality_errors",
        "soundness_errors",
        "completeness_errors",
    ):
        errors = report.get(section) or []
        if not errors:
            continue
        click.echo(f"{section}:")
        for error in errors:
            click.echo(f"  {error}")

    wm.close()
    sys.exit(2)


@world.command("atms-futures")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_futures(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show bounded ATMS future environments for a claim or concept."""
    repo: Repository = obj["repo"]
    wm, bound, _bindings, _concept_id = _bind_atms_world(repo, args, context=context)

    parsed_queryables = _parse_queryables(queryables)
    claim = wm.get_claim(target)
    if claim is not None:
        report = bound.claim_future_statuses(target, parsed_queryables, limit=limit)
        click.echo(
            f"{target}: current_status={report['current'].status.value} "
            f"could_become_in={report['could_become_in']} "
            f"could_become_out={report['could_become_out']}"
        )
        for future in report["futures"]:
            click.echo(
                f"  future [{', '.join(future['queryable_cels'])}] -> {future['status'].value}"
            )
        wm.close()
        return

    resolved = wm.resolve_alias(target) or target
    concept_report = bound.concept_future_statuses(resolved, parsed_queryables, limit=limit)
    if not concept_report:
        click.echo("No active claims for the requested ATMS future view.")
        wm.close()
        return
    for claim_id in sorted(concept_report):
        report = concept_report[claim_id]
        click.echo(
            f"{claim_id}: current_status={report['current'].status.value} "
            f"could_become_in={report['could_become_in']} "
            f"could_become_out={report['could_become_out']}"
        )
        for future in report["futures"]:
            click.echo(
                f"  future [{', '.join(future['queryable_cels'])}] -> {future['status'].value}"
            )
    wm.close()


@world.command("atms-why-out")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--queryable", "queryables", multiple=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_why_out(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Explain whether an ATMS OUT status is missing-support or nogood-pruned."""
    repo: Repository = obj["repo"]
    wm, bound, _bindings, _concept_id = _bind_atms_world(repo, args, context=context)

    parsed_queryables = _parse_queryables(queryables)
    claim = wm.get_claim(target)
    if claim is not None:
        report = bound.atms_engine().why_out(
            f"claim:{target}",
            queryables=parsed_queryables,
            limit=limit,
        )
        click.echo(
            f"{target}: out_kind={report['out_kind'].value if report['out_kind'] is not None else 'none'} "
            f"future_activatable={report['future_activatable']}"
        )
        click.echo(
            f"  candidate_queryables={_format_assumption_ids([', '.join(item) for item in report['candidate_queryable_cels']])}"
        )
        click.echo(f"  reason: {report['reason']}")
        wm.close()
        return

    resolved = wm.resolve_alias(target) or target
    concept_report = bound.why_concept_out(resolved, parsed_queryables, limit=limit)
    click.echo(
            f"{resolved}: value_status={concept_report['value_status']} "
            f"supported_claim_ids={_format_assumption_ids(concept_report['supported_claim_ids'])}"
        )
    for claim_id, report in sorted(concept_report["claim_reasons"].items()):
        click.echo(
            f"  {claim_id}: out_kind={report['out_kind'].value if report['out_kind'] is not None else 'none'} "
            f"future_activatable={report['future_activatable']}"
        )
    wm.close()


@world.command("atms-stability")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_stability(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show bounded ATMS-native stability over the implemented future replay substrate."""
    repo: Repository = obj["repo"]
    wm, bound, _bindings, _concept_id = _bind_atms_world(repo, args, context=context)

    parsed_queryables = _parse_queryables(queryables)
    claim = wm.get_claim(target)
    if claim is not None:
        report = bound.claim_stability(target, parsed_queryables, limit=limit)
        click.echo(
            f"{target}: status={report['current'].status.value} "
            f"stable={report['stable']} "
            f"consistent_futures={report['consistent_future_count']}"
        )
        if not report["witnesses"]:
            click.echo("  no bounded consistent future flips the status")
        for witness in report["witnesses"]:
            click.echo(
                f"  witness [{', '.join(witness['queryable_cels'])}] -> {witness['status'].value}"
            )
        wm.close()
        return

    resolved = wm.resolve_alias(target) or target
    report = bound.concept_stability(resolved, parsed_queryables, limit=limit)
    click.echo(
        f"{resolved}: value_status={report['current_status']} "
        f"stable={report['stable']} "
        f"consistent_futures={report['consistent_future_count']}"
    )
    if not report["witnesses"]:
        click.echo("  no bounded consistent future flips the value status")
    for witness in report["witnesses"]:
        click.echo(
            f"  witness [{', '.join(witness['queryable_cels'])}] -> {witness['status']}"
        )
    wm.close()


@world.command("atms-relevance")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_relevance(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show which bounded queryables can flip an ATMS or concept status."""
    repo: Repository = obj["repo"]
    wm, bound, _bindings, _concept_id = _bind_atms_world(repo, args, context=context)

    parsed_queryables = _parse_queryables(queryables)
    claim = wm.get_claim(target)
    if claim is not None:
        report = bound.claim_relevance(target, parsed_queryables, limit=limit)
        click.echo(
            f"{target}: current_status={report['current'].status.value} "
            f"relevant_queryables={_format_assumption_ids(report['relevant_queryables'])}"
        )
        for queryable_cel, pairs in sorted(report["witness_pairs"].items()):
            for pair in pairs:
                click.echo(
                    f"  {queryable_cel}: "
                    f"[{', '.join(pair['without']['queryable_cels'])}] -> {pair['without']['status'].value}; "
                    f"[{', '.join(pair['with']['queryable_cels'])}] -> {pair['with']['status'].value}"
                )
        wm.close()
        return

    resolved = wm.resolve_alias(target) or target
    report = bound.concept_relevance(resolved, parsed_queryables, limit=limit)
    click.echo(
        f"{resolved}: current_status={report['current_status']} "
        f"relevant_queryables={_format_assumption_ids(report['relevant_queryables'])}"
    )
    for queryable_cel, pairs in sorted(report["witness_pairs"].items()):
        for pair in pairs:
            click.echo(
                f"  {queryable_cel}: "
                f"[{', '.join(pair['without']['queryable_cels'])}] -> {pair['without']['status']}; "
                f"[{', '.join(pair['with']['queryable_cels'])}] -> {pair['with']['status']}"
            )
    wm.close()


@world.command("atms-interventions")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--target-status", required=True, help="Desired ATMS node status (IN/OUT)")
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_interventions(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    target_status: str,
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show bounded additive intervention plans for an ATMS claim or concept."""
    repo: Repository = obj["repo"]
    wm, bound, _bindings, _concept_id = _bind_atms_world(repo, args, context=context)

    parsed_queryables = _parse_queryables(queryables)
    click.echo("bounded additive plans over declared queryables")
    click.echo("not revision/contraction")

    claim = wm.get_claim(target)
    if claim is not None:
        plans = bound.claim_interventions(target, parsed_queryables, target_status, limit=limit)
        for plan in plans:
            status_val = plan["result_status"]
            if hasattr(status_val, "value"):
                status_val = status_val.value
            click.echo(
                f"  plan [{', '.join(plan['queryable_cels'])}] -> {status_val}"
            )
        wm.close()
        return

    resolved = wm.resolve_alias(target) or target
    plans = bound.concept_interventions(resolved, parsed_queryables, target_status, limit=limit)
    for plan in plans:
        status_val = plan["result_status"]
        if hasattr(status_val, "value"):
            status_val = status_val.value
        click.echo(
            f"  plan [{', '.join(plan['queryable_cels'])}] -> {status_val}"
        )
    wm.close()


@world.command("atms-next-query")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--target-status", required=True, help="Desired ATMS node status (IN/OUT)")
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_next_query(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    target_status: str,
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show next-query suggestions derived from bounded additive intervention plans."""
    repo: Repository = obj["repo"]
    wm, bound, _bindings, _concept_id = _bind_atms_world(repo, args, context=context)

    parsed_queryables = _parse_queryables(queryables)
    click.echo("derived from bounded additive intervention plans")

    claim = wm.get_claim(target)
    if claim is not None:
        suggestions = bound.claim_next_queryables(target, parsed_queryables, target_status, limit=limit)
        for suggestion in suggestions:
            click.echo(
                f"  {suggestion['queryable_cel']}: "
                f"coverage={suggestion['plan_count']} "
                f"smallest_plan_size={suggestion['smallest_plan_size']}"
            )
        wm.close()
        return

    resolved = wm.resolve_alias(target) or target
    suggestions = bound.concept_next_queryables(resolved, parsed_queryables, target_status, limit=limit)
    for suggestion in suggestions:
        click.echo(
            f"  {suggestion['queryable_cel']}: "
            f"coverage={suggestion['plan_count']} "
            f"smallest_plan_size={suggestion['smallest_plan_size']}"
        )
    wm.close()


@world.command("derive")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.pass_obj
def world_derive(obj: dict, concept_id: str, args: tuple[str, ...]) -> None:
    """Derive a value for a concept via parameterization relationships.

    Usage: pks world derive concept5 domain=example
    """
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
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
              type=click.Choice(["recency", "sample_size", "argumentation", "override"]))
@click.option("--override", "override_id", default=None, help="Claim ID for override strategy")
@click.option("--semantics", default="grounded",
              type=click.Choice(["grounded", "preferred", "stable"]),
              help="Argumentation semantics (default: grounded)")
@click.option("--set-comparison", "set_comparison", default="elitist",
              type=click.Choice(["elitist", "democratic"]),
              help="Set comparison for preference ordering (default: elitist)")
@click.option("--decision-criterion", "decision_criterion", default="pignistic",
              type=click.Choice(["pignistic", "lower_bound", "upper_bound", "hurwicz"]),
              help="Decision criterion for opinion interpretation (default: pignistic)")
@click.option("--pessimism-index", "pessimism_index", default=0.5,
              type=float, help="Hurwicz pessimism index α ∈ [0,1] (default: 0.5)")
@click.option("--reasoning-backend", "reasoning_backend", default="claim_graph",
              type=click.Choice(["claim_graph", "structured_projection", "atms", "praf"]),
              help="Argumentation backend (default: claim_graph)")
@click.option("--praf-strategy", "praf_strategy", default="auto",
              type=click.Choice(["auto", "mc", "exact", "dfquad"]),
              help="PrAF computation strategy (default: auto)")
@click.option("--praf-epsilon", "praf_epsilon", default=0.01,
              type=float, help="PrAF MC error tolerance (default: 0.01)")
@click.option("--praf-confidence", "praf_confidence", default=0.95,
              type=float, help="PrAF MC confidence level (default: 0.95)")
@click.option("--praf-seed", "praf_seed", default=None,
              type=int, help="PrAF MC RNG seed (default: random)")
@click.pass_obj
def world_resolve(obj: dict, concept_id: str, args: tuple[str, ...],
                  strategy: str, override_id: str | None,
                  semantics: str, set_comparison: str,
                  decision_criterion: str,
                  pessimism_index: float,
                  reasoning_backend: str,
                  praf_strategy: str,
                  praf_epsilon: float,
                  praf_confidence: float,
                  praf_seed: int | None) -> None:
    """Resolve a conflicted concept using a strategy.

    Usage: pks world resolve concept1 domain=example --strategy argumentation
    """
    from propstore.world import (
        ReasoningBackend,
        RenderPolicy,
        ResolutionStrategy,
        WorldModel,
        resolve,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        resolved = wm.resolve_alias(concept_id) or concept_id
        bound = wm.bind(**bindings)
        strat = ResolutionStrategy(strategy)
        overrides_dict = {resolved: override_id} if override_id else None
        backend = ReasoningBackend(reasoning_backend)

        policy = RenderPolicy(
            reasoning_backend=backend,
            strategy=strat,
            semantics=semantics,
            comparison=set_comparison,
            decision_criterion=decision_criterion,
            pessimism_index=pessimism_index,
            praf_strategy=praf_strategy,
            praf_mc_epsilon=praf_epsilon,
            praf_mc_confidence=praf_confidence,
            praf_mc_seed=praf_seed,
            overrides=overrides_dict or {},
        )

        try:
            result = resolve(
                bound, resolved, policy=policy, world=wm,
            )
        except (ValueError, NotImplementedError) as e:
            click.echo(f"ERROR: {e}", err=True)
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
        if result.acceptance_probs:
            click.echo("  acceptance_probs:")
            for cid, prob in sorted(result.acceptance_probs.items()):
                click.echo(f"    {cid}: {prob:.4f}")


@world.command("extensions")
@click.argument("args", nargs=-1)
@click.option("--backend", "backend_name", default="claim_graph",
              type=click.Choice(["claim_graph", "structured_projection", "atms", "praf"]),
              help="Argumentation backend (default: claim_graph)")
@click.option("--semantics", default="grounded",
              type=click.Choice(["grounded", "preferred", "stable"]),
              help="Argumentation semantics (default: grounded)")
@click.option("--set-comparison", "set_comparison", default="elitist",
              type=click.Choice(["elitist", "democratic"]),
              help="Set comparison for preference ordering (default: elitist)")
@click.option("--context", default=None, help="Context to scope the argumentation")
@click.option("--praf-strategy", "praf_strategy", default="auto",
              type=click.Choice(["auto", "mc", "exact", "dfquad"]),
              help="PrAF computation strategy (default: auto)")
@click.option("--praf-epsilon", "praf_epsilon", default=0.01,
              type=float, help="PrAF MC error tolerance (default: 0.01)")
@click.option("--praf-confidence", "praf_confidence", default=0.95,
              type=float, help="PrAF MC confidence level (default: 0.95)")
@click.option("--praf-seed", "praf_seed", default=None,
              type=int, help="PrAF MC RNG seed (default: random)")
@click.pass_obj
def world_extensions(obj: dict, args: tuple[str, ...],
                     backend_name: str, semantics: str, set_comparison: str,
                     context: str | None,
                     praf_strategy: str,
                     praf_epsilon: float,
                     praf_confidence: float,
                     praf_seed: int | None) -> None:
    """Show argumentation extensions — all claims that survive scrutiny.

    Usage: pks world extensions domain=example --semantics grounded
    """
    from propstore.argumentation import stance_summary
    from propstore.world import Environment, ReasoningBackend, WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        if context:
            env = Environment(bindings=bindings, context_id=context)
            bound = wm.bind(env)
        else:
            bound = wm.bind(**bindings)
        active = bound.active_claims()
        if not active:
            click.echo("No active claims for given bindings.")
            return

        claim_ids = {c["id"] for c in active}
        backend = ReasoningBackend(backend_name)

        if backend == ReasoningBackend.ATMS:
            click.echo(
                "ERROR: backend 'atms' does not expose Dung extensions; "
                "use worldline or resolve with reasoning_backend=atms instead.",
                err=True,
            )
            sys.exit(2)

        if backend == ReasoningBackend.PRAF:
            from propstore.argumentation import build_praf
            from propstore.praf import compute_praf_acceptance

            praf = build_praf(wm, claim_ids, comparison=set_comparison)
            praf_result = compute_praf_acceptance(
                praf, semantics=semantics,
                strategy=praf_strategy,
                mc_epsilon=praf_epsilon,
                mc_confidence=praf_confidence,
                rng_seed=praf_seed,
            )
            summary = stance_summary(wm, claim_ids)
            click.echo(f"Backend: {backend.value}")
            click.echo(f"Semantics: {semantics}")
            click.echo(f"Strategy used: {praf_result.strategy_used}")
            if praf_result.samples is not None:
                click.echo(f"MC samples: {praf_result.samples}")
            click.echo(f"Active claims: {len(claim_ids)}")
            click.echo(f"Stances: {summary['total_stances']} total, "
                       f"{summary['included_as_attacks']} included as attacks")
            click.echo("\nAcceptance probabilities:")
            claim_map = {c["id"]: c for c in active}
            for cid, prob in sorted(
                praf_result.acceptance_probs.items(),
                key=lambda x: -x[1],
            ):
                c = claim_map.get(cid)
                label = cid
                if c:
                    value = c.get("value")
                    concept_id_val = c.get("concept_id")
                    if concept_id_val:
                        concept = wm.get_concept(concept_id_val)
                        cname = concept.get("canonical_name", concept_id_val) if concept else concept_id_val
                        if value is not None:
                            label = f"{cid}: {cname} = {value}"
                        else:
                            label = f"{cid}: {cname}"
                click.echo(f"  {label}  P(accepted) = {prob:.4f}")
            return

        if backend == ReasoningBackend.CLAIM_GRAPH:
            from propstore.argumentation import (
                build_argumentation_framework,
                compute_claim_graph_justified_claims,
            )

            result = compute_claim_graph_justified_claims(
                wm, claim_ids,
                semantics=semantics,
                comparison=set_comparison,
            )
            af = build_argumentation_framework(
                wm, claim_ids,
                comparison=set_comparison,
            )
            arg_to_claim = {cid: cid for cid in claim_ids}
        elif backend == ReasoningBackend.STRUCTURED_PROJECTION:
            from propstore.structured_argument import (
                build_structured_projection,
                compute_structured_justified_arguments,
            )

            support_metadata: dict[str, tuple[object | None, object]] = {}
            claim_support = getattr(bound, "claim_support", None)
            if callable(claim_support):
                for claim in active:
                    claim_id = claim.get("id")
                    if claim_id:
                        support_metadata[claim_id] = claim_support(claim)

            projection = build_structured_projection(
                wm,
                active,
                support_metadata=support_metadata,
                comparison=set_comparison,
            )
            result = compute_structured_justified_arguments(
                projection,
                semantics=semantics,
            )
            af = projection.framework
            arg_to_claim = dict(projection.argument_to_claim_id)
        else:
            raise NotImplementedError(f"Unknown backend: {backend.value}")

        summary = stance_summary(wm, claim_ids)
        click.echo(f"Backend: {backend.value}")
        click.echo(f"Semantics: {semantics}")
        click.echo(f"Set comparison: {set_comparison}")
        click.echo(f"Active claims: {len(claim_ids)}")
        click.echo(f"Stances: {summary['total_stances']} total, "
                   f"{summary['included_as_attacks']} included as attacks, "
                   f"{summary['vacuous_count']} vacuous, "
                   f"{summary['excluded_non_attack']} non-attack")
        if summary["models"]:
            click.echo(f"Models: {', '.join(summary['models'])}")

        claim_map = {c["id"]: c for c in active}

        def _claim_label(cid: str) -> str:
            """Format a claim for display: id (type) concept = value."""
            c = claim_map.get(cid)
            if c is None:
                return cid
            ctype = c.get("type", "?")
            concept_id = c.get("concept_id")
            value = c.get("value")
            cname = None
            if concept_id:
                concept = wm.get_concept(concept_id)
                if concept:
                    cname = concept.get("canonical_name", concept_id)
            if ctype == "parameter" and value is not None:
                return f"{cid}: {cname} = {value}"
            if ctype == "equation":
                expr = c.get("expression", "")
                return f"{cid}: {expr}" if expr else f"{cid} ({ctype})"
            if ctype in ("observation", "limitation", "mechanism", "comparison"):
                stmt = c.get("statement") or c.get("description") or ""
                if len(stmt) > 60:
                    stmt = stmt[:57] + "..."
                return f"{cid}: {stmt}" if stmt else f"{cid} ({ctype})"
            if value is not None:
                return f"{cid}: {cname} = {value}" if cname else f"{cid} = {value}"
            return f"{cid} ({ctype})"

        def _group_by_type(cids: set[str]) -> dict[str, list[str]]:
            groups: dict[str, list[str]] = {}
            for cid in sorted(cids):
                c = claim_map.get(cid)
                ctype = c.get("type", "unknown") if c else "unknown"
                groups.setdefault(ctype, []).append(cid)
            return groups

        if semantics == "grounded":
            if backend == ReasoningBackend.STRUCTURED_PROJECTION:
                assert isinstance(result, frozenset)
                justified_claims = {arg_to_claim[arg_id] for arg_id in result}
            else:
                assert isinstance(result, frozenset)
                justified_claims = set(result)

            defeated = claim_ids - justified_claims
            defeaters_map: dict[str, list[str]] = {}
            for src, tgt in af.defeats:
                src_claim = arg_to_claim.get(src, src)
                tgt_claim = arg_to_claim.get(tgt, tgt)
                if tgt_claim in defeated:
                    defeaters_map.setdefault(tgt_claim, []).append(src_claim)

            accepted_groups = _group_by_type(justified_claims)
            click.echo(f"Accepted ({len(justified_claims)} claims):")
            for ctype, cids in sorted(accepted_groups.items()):
                click.echo(f"  {ctype} ({len(cids)}):")
                for cid in cids:
                    click.echo(f"    {_claim_label(cid)}")

            if defeated:
                click.echo(f"Defeated ({len(defeated)} claims):")
                for cid in sorted(defeated):
                    defeaters = defeaters_map.get(cid, [])
                    if defeaters:
                        by = ", ".join(sorted(defeaters))
                        click.echo(f"  {_claim_label(cid)}")
                        click.echo(f"    defeated by: {by}")
                    else:
                        click.echo(f"  {_claim_label(cid)}")
        else:
            assert isinstance(result, list)
            click.echo(f"Extensions ({len(result)}):")
            for i, ext in enumerate(result):
                ext_claims = (
                    {arg_to_claim[arg_id] for arg_id in ext}
                    if backend == ReasoningBackend.STRUCTURED_PROJECTION
                    else set(ext)
                )
                click.echo(f"  Extension {i + 1} ({len(ext_claims)} claims):")
                groups = _group_by_type(ext_claims)
                for ctype, cids in sorted(groups.items()):
                    click.echo(f"    {ctype}:")
                    for cid in cids:
                        click.echo(f"      {_claim_label(cid)}")


@world.command("hypothetical")
@click.argument("args", nargs=-1)
@click.option("--remove", multiple=True, help="Claim ID to remove")
@click.option("--add", "add_json", default=None, help="JSON synthetic claim")
@click.pass_obj
def world_hypothetical(obj: dict, args: tuple[str, ...],
                       remove: tuple[str, ...], add_json: str | None) -> None:
    """Show what changes if claims are removed/added.

    Usage: pks world hypothetical domain=example --remove claim2
    """
    from propstore.world import HypotheticalWorld, SyntheticClaim, WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
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


@world.command("chain")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option("--strategy", default=None,
              type=click.Choice(["recency", "sample_size", "argumentation", "override"]))
@click.pass_obj
def world_chain(obj: dict, concept_id: str, args: tuple[str, ...],
                strategy: str | None) -> None:
    """Traverse the parameter space to derive a target concept.

    Usage: pks world chain concept5 domain=example --strategy sample_size
    """
    from propstore.world import ResolutionStrategy, WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        resolved = wm.resolve_alias(concept_id) or concept_id
        strat = ResolutionStrategy(strategy) if strategy else None
        result = wm.chain_query(resolved, strategy=strat, **bindings)

        def _label(cid: str) -> str:
            """Return 'conceptN (canonical_name)' or just the id if no name."""
            c = wm.get_concept(cid)
            name = c.get("canonical_name", "") if c else ""
            return f"{cid} ({name})" if name else cid

        click.echo(f"Target: {_label(resolved)}")
        click.echo(f"Result: {result.result.status}")
        from propstore.world import DerivedResult
        if isinstance(result.result, DerivedResult) and result.result.value is not None:
            click.echo(f"  value: {result.result.value}")
        click.echo(f"Steps ({len(result.steps)}):")
        for step in result.steps:
            click.echo(f"  {_label(step.concept_id)}: {step.value} ({step.source})")


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

    Usage: pks world export-graph domain=example --format dot --output graph.dot
    """
    from propstore.graph_export import build_knowledge_graph
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
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


@world.command("sensitivity")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_obj
def world_sensitivity(obj: dict, concept_id: str, args: tuple[str, ...],
                      fmt: str) -> None:
    """Analyze which input most influences a derived quantity.

    Usage: pks world sensitivity concept5 domain=example
    """
    from propstore.sensitivity import analyze_sensitivity
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        resolved = wm.resolve_alias(concept_id) or concept_id
        bound = wm.bind(**bindings)
        result = analyze_sensitivity(wm, resolved, bound)

        if result is None:
            click.echo(f"No sensitivity analysis available for {resolved}.")
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


@world.command("check-consistency")
@click.argument("args", nargs=-1)
@click.option("--transitive", is_flag=True, help="Check multi-hop transitive conflicts")
@click.pass_obj
def world_check_consistency(obj: dict, args: tuple[str, ...],
                            transitive: bool) -> None:
    """Check for conflicts, optionally including transitive (multi-hop) ones.

    Usage: pks world check-consistency domain=example
           pks world check-consistency --transitive
    """
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        if transitive:
            from propstore.conflict_detector import detect_transitive_conflicts
            from propstore.validate_claims import load_claim_files

            claim_files = load_claim_files(repo.claims_dir)
            concept_registry: dict[str, dict] = {}
            for cdata in wm.all_concepts():
                cdata = dict(cdata)
                cid = cdata["id"]
                param_rows = wm.parameterizations_for(cid)
                if param_rows:
                    cdata["parameterization_relationships"] = []
                    for pr in param_rows:
                        prd = dict(pr)
                        cdata["parameterization_relationships"].append({
                            "inputs": json.loads(prd["concept_ids"]),
                            "sympy": prd.get("sympy"),
                            "exactness": prd.get("exactness"),
                            "conditions": json.loads(prd["conditions_cel"]) if prd.get("conditions_cel") else [],
                        })
                concept_registry[cid] = cdata

            records = detect_transitive_conflicts(claim_files, concept_registry)
            if not records:
                click.echo("No transitive conflicts found.")
            else:
                click.echo(f"Found {len(records)} transitive conflict(s):")
                for r in records:
                    click.echo(f"  {r.concept_id}: {r.value_a} vs {r.value_b}")
                    if r.derivation_chain:
                        click.echo(f"    chain: {r.derivation_chain}")
        else:
            bound = wm.bind(**bindings)
            conflicts = bound.conflicts()
            if not conflicts:
                click.echo("No conflicts under current bindings.")
            else:
                click.echo(f"Found {len(conflicts)} conflict(s):")
                for c in conflicts:
                    click.echo(
                        f"  {c['concept_id']}: {c.get('warning_class', '?')} "
                        f"({c['claim_a_id']} vs {c['claim_b_id']})"
                    )
