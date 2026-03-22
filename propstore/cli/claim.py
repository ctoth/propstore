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


@claim.command("validate-file")
@click.argument("filepath", type=click.Path(exists=True, path_type=Path))
@click.option("--concepts-dir", "concepts_path", default=None, help="Concepts directory")
@click.pass_obj
def validate_file(obj: dict, filepath: Path, concepts_path: str | None) -> None:
    """Validate a single claims YAML file."""
    from propstore.validate_claims import (
        build_concept_registry_from_paths,
        validate_single_claim_file,
    )

    repo: Repository = obj["repo"]
    cpd = Path(concepts_path) if concepts_path else repo.concepts_dir

    if not cpd.exists():
        click.echo(f"ERROR: Concepts directory '{cpd}' does not exist", err=True)
        sys.exit(EXIT_ERROR)

    forms_dir = cpd.parent / "forms"
    if not forms_dir.exists():
        forms_dir = repo.forms_dir

    registry = build_concept_registry_from_paths(cpd, forms_dir)
    result = validate_single_claim_file(filepath, registry)

    for w in result.warnings:
        click.echo(f"WARNING: {w}", err=True)
    for e in result.errors:
        click.echo(f"ERROR: {e}", err=True)

    if result.ok:
        click.echo(f"Valid: {filepath.name} ({len(result.warnings)} warning(s))")
    else:
        click.echo(f"FAILED: {filepath.name} ({len(result.errors)} error(s))", err=True)
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


@claim.command()
@click.argument("claim_id", required=False, default=None)
@click.option("--all", "embed_all", is_flag=True, help="Embed all claims")
@click.option("--model", required=True, help="litellm model string, or 'all' for every registered model")
@click.option("--batch-size", default=64, type=int, help="Claims per API call")
@click.pass_obj
def embed(obj: dict, claim_id: str | None, embed_all: bool, model: str, batch_size: int) -> None:
    """Generate embeddings for claims via litellm."""
    if not claim_id and not embed_all:
        click.echo("Error: provide a claim ID or use --all", err=True)
        raise SystemExit(1)

    from propstore.embed import embed_claims, _load_vec_extension, get_registered_models

    repo = obj["repo"]
    sidecar = repo.sidecar_path
    if not sidecar.exists():
        click.echo("Error: sidecar not found. Run 'pks build' first.", err=True)
        raise SystemExit(1)

    import sqlite3
    conn = sqlite3.connect(sidecar)
    conn.row_factory = sqlite3.Row
    _load_vec_extension(conn)

    ids = [claim_id] if claim_id else None

    if model == "all":
        models = get_registered_models(conn)
        if not models:
            click.echo("Error: no models registered. Run embed with a specific model first.", err=True)
            conn.close()
            raise SystemExit(1)
        for m in models:
            click.echo(f"Embedding with {m['model_name']}...")
            result = embed_claims(
                conn, m["model_name"], claim_ids=ids, batch_size=batch_size,
                on_progress=lambda done, total: click.echo(f"  {done}/{total}", nl=False) if done % batch_size == 0 else None
            )
            click.echo(f"  embedded={result['embedded']} skipped={result['skipped']} errors={result['errors']}")
    else:
        def progress(done: int, total: int) -> None:
            click.echo(f"  {done}/{total} claims embedded", err=True)

        result = embed_claims(conn, model, claim_ids=ids, batch_size=batch_size, on_progress=progress)
        click.echo(f"Embedded: {result['embedded']}, Skipped: {result['skipped']}, Errors: {result['errors']}")

    conn.commit()
    conn.close()


@claim.command()
@click.argument("claim_id")
@click.option("--model", default=None, help="litellm model string (default: first available)")
@click.option("--top-k", default=10, type=int, help="Number of results")
@click.option("--agree", is_flag=True, help="Similar under ALL stored models")
@click.option("--disagree", is_flag=True, help="Similar under some models but not others")
@click.pass_obj
def similar(obj: dict, claim_id: str, model: str | None, top_k: int, agree: bool, disagree: bool) -> None:
    """Find similar claims by embedding distance."""
    from propstore.embed import find_similar, find_similar_agree, find_similar_disagree, _load_vec_extension, get_registered_models

    repo = obj["repo"]
    sidecar = repo.sidecar_path
    if not sidecar.exists():
        click.echo("Error: sidecar not found. Run 'pks build' first.", err=True)
        raise SystemExit(1)

    import sqlite3
    conn = sqlite3.connect(sidecar)
    conn.row_factory = sqlite3.Row
    _load_vec_extension(conn)

    try:
        if agree:
            results = find_similar_agree(conn, claim_id, top_k=top_k)
        elif disagree:
            results = find_similar_disagree(conn, claim_id, top_k=top_k)
        else:
            if model is None:
                models = get_registered_models(conn)
                if not models:
                    click.echo("Error: no embeddings found. Run 'pks claim embed' first.", err=True)
                    raise SystemExit(1)
                model = models[0]["model_name"]
            results = find_similar(conn, claim_id, model, top_k=top_k)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    finally:
        conn.close()

    if not results:
        click.echo("No similar claims found.")
        return

    for r in results:
        dist = r.get("distance", 0)
        cid = r.get("id", "?")
        summary = r.get("auto_summary") or r.get("statement") or ""
        paper = r.get("source_paper", "")
        click.echo(f"  {dist:.4f}  {cid}  [{paper}]  {summary[:120]}")


@claim.command()
@click.argument("claim_id", required=False, default=None)
@click.option("--all", "relate_all_flag", is_flag=True, help="Relate all claims")
@click.option("--model", required=True, help="LLM model for classification")
@click.option("--embedding-model", default=None, help="Embedding model for similarity")
@click.option("--top-k", default=5, type=int, help="Number of similar claims to classify")
@click.option("--concurrency", default=20, type=int, help="Max concurrent LLM calls")
@click.option("--second-pass-threshold", default=0.75, type=float, help="Distance threshold for second-pass NLI")
@click.pass_obj
def relate(obj, claim_id, relate_all_flag, model, embedding_model, top_k, concurrency, second_pass_threshold):
    """Classify epistemic relationships between similar claims via LLM."""
    from propstore.relate import relate_claim, relate_all as relate_all_fn, write_stance_file
    from propstore.embed import _load_vec_extension

    repo = obj["repo"]
    sidecar = repo.sidecar_path
    if not sidecar.exists():
        click.echo("Error: sidecar not found. Run 'pks build' first.", err=True)
        raise SystemExit(1)

    import sqlite3
    conn = sqlite3.connect(sidecar)
    conn.row_factory = sqlite3.Row
    _load_vec_extension(conn)

    stances_dir = repo.stances_dir

    if claim_id and not relate_all_flag:
        # Single claim
        stances = relate_claim(conn, claim_id, model, embedding_model, top_k,
                               second_pass_threshold=second_pass_threshold)
        conn.close()

        if stances:
            write_stance_file(stances_dir, claim_id, stances, model)
            for s in stances:
                click.echo(f"  {s['type']:12s} {s.get('strength', ''):8s} -> {s['target']}  {s.get('note', '')}")
            click.echo(f"\n{len(stances)} stances written to {stances_dir / f'{claim_id}.yaml'}")
        else:
            click.echo("No epistemic relationships found.")

    elif relate_all_flag:
        def progress(done, total):
            if done % 10 == 0 or done == total:
                click.echo(f"  {done}/{total} claims processed", err=True)

        result = relate_all_fn(conn, model, embedding_model, top_k, concurrency=concurrency,
                               on_progress=progress, second_pass_threshold=second_pass_threshold)
        conn.close()

        # Write stance files
        for cid, stances in result.get("stances_by_claim", {}).items():
            write_stance_file(stances_dir, cid, stances, model)

        click.echo(f"\nProcessed: {result['claims_processed']}, Stances found: {result['stances_found']}, No relation: {result['no_relation']}")
    else:
        click.echo("Error: provide a claim ID or use --all", err=True)
        conn.close()
        raise SystemExit(1)
