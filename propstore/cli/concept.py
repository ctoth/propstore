"""pks concept — subcommands for managing concepts."""
from __future__ import annotations

import sqlite3
from copy import deepcopy
import subprocess
import sys
from datetime import date
from pathlib import Path

import click
import yaml

from propstore.cli.helpers import (
    EXIT_ERROR,
    EXIT_VALIDATION,
    find_concept,
    load_concept_file,
    read_counter,
    write_counter,
    write_concept_file,
)
from propstore.cli.repository import Repository
from propstore.validate import LoadedConcept, load_concepts, validate_concepts
from propstore.validate_claims import load_claim_files, validate_claims

RELATIONSHIP_TYPES = (
    "broader", "narrower", "related",
    "component_of", "derived_from", "contested_definition",
)


@click.group()
def concept() -> None:
    """Manage concepts in the registry."""


def _rename_cel_identifier(expression: str, old_name: str, new_name: str) -> str:
    """Rename a CEL identifier without touching quoted string literals."""
    result: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(expression):
        ch = expression[i]
        if quote is not None:
            result.append(ch)
            if ch == quote and (i == 0 or expression[i - 1] != "\\"):
                quote = None
            i += 1
            continue

        if ch in ("'", '"'):
            quote = ch
            result.append(ch)
            i += 1
            continue

        if ch.isalpha() or ch == "_":
            j = i + 1
            while j < len(expression) and (expression[j].isalnum() or expression[j] == "_"):
                j += 1
            token = expression[i:j]
            result.append(new_name if token == old_name else token)
            i = j
            continue

        result.append(ch)
        i += 1

    return "".join(result)


def _rewrite_condition_list(
    conditions: object,
    old_name: str,
    new_name: str,
) -> tuple[object, bool]:
    if not isinstance(conditions, list):
        return conditions, False
    changed = False
    rewritten: list[object] = []
    for condition in conditions:
        if isinstance(condition, str):
            new_condition = _rename_cel_identifier(condition, old_name, new_name)
            changed = changed or new_condition != condition
            rewritten.append(new_condition)
        else:
            rewritten.append(condition)
    return rewritten, changed


def _rewrite_concept_conditions(data: dict, old_name: str, new_name: str) -> bool:
    changed = False
    for rel in data.get("relationships", []) or []:
        rewritten, rel_changed = _rewrite_condition_list(rel.get("conditions"), old_name, new_name)
        if rel_changed:
            rel["conditions"] = rewritten
            changed = True
    for param in data.get("parameterization_relationships", []) or []:
        rewritten, param_changed = _rewrite_condition_list(param.get("conditions"), old_name, new_name)
        if param_changed:
            param["conditions"] = rewritten
            changed = True
    return changed


def _rewrite_claim_conditions(claim_file_data: dict, old_name: str, new_name: str) -> bool:
    changed = False
    for claim in claim_file_data.get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        rewritten, claim_changed = _rewrite_condition_list(claim.get("conditions"), old_name, new_name)
        if claim_changed:
            claim["conditions"] = rewritten
            changed = True
    return changed


# ── concept add ──────────────────────────────────────────────────────

@concept.command()
@click.option("--domain", required=True, help="Domain prefix (e.g. speech, a11y, finance)")
@click.option("--name", required=True, help="Canonical name (lowercase, underscored)")
@click.option("--definition", default=None, help="Definition (prompted if omitted)")
@click.option("--form", "form_name", default=None,
              help="Form name (references forms/<name>.yaml, prompted if omitted)")
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing")
@click.pass_obj
def add(
    obj: dict,
    domain: str,
    name: str,
    definition: str | None,
    form_name: str | None,
    dry_run: bool,
) -> None:
    """Add a new concept to the registry."""
    repo: Repository = obj["repo"]
    # Prompt for missing fields
    if definition is None:
        definition = click.prompt("Definition")
    if form_name is None:
        # List available forms
        if repo.forms_dir.exists():
            available = sorted(f.stem for f in repo.forms_dir.iterdir() if f.suffix == ".yaml")
            click.echo(f"Available forms: {', '.join(available)}")
        form_name = click.prompt("Form")

    filepath = repo.concepts_dir / f"{name}.yaml"
    if filepath.exists():
        click.echo(f"ERROR: Concept file '{filepath}' already exists", err=True)
        sys.exit(EXIT_ERROR)

    next_counter = read_counter(repo.counters_dir)
    cid = f"concept{next_counter}"

    data = {
        "id": cid,
        "canonical_name": name,
        "status": "proposed",
        "definition": definition,
        "domain": domain,
        "created_date": str(date.today()),
        "form": form_name,
    }

    if dry_run:
        click.echo(f"Would create {filepath}")
        click.echo(yaml.dump(data, default_flow_style=False, sort_keys=False))
        return

    repo.concepts_dir.mkdir(parents=True, exist_ok=True)
    concepts = load_concepts(repo.concepts_dir)
    concepts.append(LoadedConcept(filename=name, filepath=filepath, data=data))

    result = validate_concepts(concepts, repo=repo)
    if not result.ok:
        for e in result.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Validation failed. No changes written.", err=True)
        sys.exit(EXIT_VALIDATION)

    for w in result.warnings:
        click.echo(f"WARNING: {w}", err=True)

    write_concept_file(filepath, data)
    write_counter(repo.counters_dir, next_counter + 1)
    click.echo(f"Created {filepath} with ID {cid}")


# ── concept alias ────────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id")
@click.option("--name", required=True, help="Alias name")
@click.option("--source", required=True, help="Source paper or 'common'")
@click.option("--note", default=None, help="Optional note")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def alias(obj: dict, concept_id: str, name: str, source: str, note: str | None, dry_run: bool) -> None:
    """Add an alias to a concept."""
    repo: Repository = obj["repo"]
    filepath = find_concept(concept_id, repo.concepts_dir)
    if filepath is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)

    data = load_concept_file(filepath)

    # Warn if alias matches another concept's canonical_name
    cdir = repo.concepts_dir
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
@click.pass_obj
def rename(obj: dict, concept_id: str, name: str, dry_run: bool) -> None:
    """Rename a concept (updates canonical_name and filename)."""
    repo: Repository = obj["repo"]
    filepath = find_concept(concept_id, repo.concepts_dir)
    if filepath is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)

    data = load_concept_file(filepath)
    old_name = data.get("canonical_name", filepath.stem)
    new_path = filepath.parent / f"{name}.yaml"
    if old_name == name:
        click.echo(f"No change: concept already named '{name}'")
        return
    if new_path.exists():
        click.echo(f"ERROR: Concept file '{new_path}' already exists", err=True)
        sys.exit(EXIT_ERROR)

    if dry_run:
        click.echo(f"Would rename: {old_name} -> {name}")
        click.echo(f"  {filepath} -> {new_path}")
        return

    loaded_concepts = load_concepts(repo.concepts_dir)
    updated_concepts = []
    changed_concept_paths: set[Path] = set()
    for concept_record in loaded_concepts:
        concept_data = deepcopy(concept_record.data)
        if concept_record.filepath == filepath:
            concept_data["canonical_name"] = name
            concept_data["last_modified"] = str(date.today())
            changed_concept_paths.add(concept_record.filepath)
        if _rewrite_concept_conditions(concept_data, old_name, name):
            changed_concept_paths.add(concept_record.filepath)
        updated_concepts.append(
            type(concept_record)(
                filename=name if concept_record.filepath == filepath else concept_record.filename,
                filepath=new_path if concept_record.filepath == filepath else concept_record.filepath,
                data=concept_data,
            )
        )

    concept_validation = validate_concepts(
        updated_concepts,
        claims_dir=repo.claims_dir if repo.claims_dir.exists() else None,
        repo=repo,
    )
    if not concept_validation.ok:
        for e in concept_validation.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Rename validation failed. No changes written.", err=True)
        sys.exit(EXIT_VALIDATION)

    claim_files = load_claim_files(repo.claims_dir) if repo.claims_dir.exists() else []
    updated_claim_files = []
    changed_claim_paths: set[Path] = set()
    if claim_files:
        for claim_file in claim_files:
            claim_data = deepcopy(claim_file.data)
            if _rewrite_claim_conditions(claim_data, old_name, name):
                changed_claim_paths.add(claim_file.filepath)
            updated_claim_files.append(type(claim_file)(
                filename=claim_file.filename,
                filepath=claim_file.filepath,
                data=claim_data,
            ))
        concept_registry = {
            concept_record.data["id"]: deepcopy(concept_record.data)
            for concept_record in updated_concepts
            if concept_record.data.get("id")
        }
        claim_validation = validate_claims(updated_claim_files, concept_registry)
        if not claim_validation.ok:
            for e in claim_validation.errors:
                click.echo(f"ERROR: {e}", err=True)
            click.echo("Rename validation failed. No changes written.", err=True)
            sys.exit(EXIT_VALIDATION)

    # Write the renamed concept to the new path first, then remove old
    for concept_record in updated_concepts:
        target_path = concept_record.filepath
        if target_path == new_path:
            write_concept_file(new_path, concept_record.data)
        elif concept_record.filepath in changed_concept_paths:
            write_concept_file(target_path, concept_record.data)

    for claim_file in updated_claim_files:
        if claim_file.filepath in changed_claim_paths:
            with open(claim_file.filepath, "w") as f:
                yaml.dump(claim_file.data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # Remove old file and track with git if available
    try:
        subprocess.run(
            ["git", "rm", str(filepath)],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "add", str(new_path)],
            check=True, capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        filepath.unlink(missing_ok=True)

    click.echo(f"{old_name} -> {name}")
    click.echo(f"  {filepath} -> {new_path}")
    click.echo(f"  ID unchanged: {data.get('id')}")


# ── concept deprecate ────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id")
@click.option("--replaced-by", required=True, help="Replacement concept ID")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def deprecate(obj: dict, concept_id: str, replaced_by: str, dry_run: bool) -> None:
    """Deprecate a concept with a replacement."""
    repo: Repository = obj["repo"]
    filepath = find_concept(concept_id, repo.concepts_dir)
    if filepath is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)

    # Validate replacement target
    replacement_path = find_concept(replaced_by, repo.concepts_dir)
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
    filepath = find_concept(source_id, repo.concepts_dir)
    if filepath is None:
        click.echo(f"ERROR: Source concept '{source_id}' not found", err=True)
        sys.exit(EXIT_ERROR)

    if find_concept(target_id, repo.concepts_dir) is None:
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

    concepts = load_concepts(repo.concepts_dir)
    updated_concepts = []
    for concept_record in concepts:
        updated_concepts.append(
            LoadedConcept(
                filename=concept_record.filename,
                filepath=concept_record.filepath,
                data=data if concept_record.filepath == filepath else concept_record.data,
            )
        )
    validation = validate_concepts(
        updated_concepts,
        claims_dir=repo.claims_dir if repo.claims_dir.exists() else None,
        repo=repo,
    )
    if not validation.ok:
        for e in validation.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Validation failed. No changes written.", err=True)
        sys.exit(EXIT_VALIDATION)

    for w in validation.warnings:
        click.echo(f"WARNING: {w}", err=True)

    write_concept_file(filepath, data)

    click.echo(f"Added {rel_type} -> {target_id} on {data.get('id')} ({filepath.stem})")


# ── concept search ───────────────────────────────────────────────────

@concept.command()
@click.argument("query")
@click.pass_obj
def search(obj: dict, query: str) -> None:
    """Search concepts by name, definition, or alias."""
    repo: Repository = obj["repo"]
    sidecar = repo.sidecar_path

    if sidecar.exists():
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
    cdir = repo.concepts_dir
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
@click.pass_obj
def list_concepts(obj: dict, domain: str | None, status: str | None) -> None:
    """List concepts, optionally filtered."""
    repo: Repository = obj["repo"]
    cdir = repo.concepts_dir
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
@click.pass_obj
def show(obj: dict, concept_id_or_name: str) -> None:
    """Show full concept YAML."""
    repo: Repository = obj["repo"]
    filepath = find_concept(concept_id_or_name, repo.concepts_dir)
    if filepath is None:
        click.echo(f"ERROR: Concept '{concept_id_or_name}' not found", err=True)
        sys.exit(EXIT_ERROR)

    click.echo(filepath.read_text())


# ── concept embed ────────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id", required=False, default=None)
@click.option("--all", "embed_all", is_flag=True, help="Embed all concepts")
@click.option("--model", required=True, help="litellm model string, or 'all'")
@click.option("--batch-size", default=64, type=int, help="Concepts per API call")
@click.pass_obj
def embed(obj: dict, concept_id: str | None, embed_all: bool, model: str, batch_size: int) -> None:
    """Generate embeddings for concepts via litellm."""
    if not concept_id and not embed_all:
        click.echo("Error: provide a concept ID or use --all", err=True)
        raise SystemExit(1)

    from propstore.embed import embed_concepts, _load_vec_extension, get_registered_models

    repo: Repository = obj["repo"]
    sidecar = repo.sidecar_path
    if not sidecar.exists():
        click.echo("Error: sidecar not found. Run 'pks build' first.", err=True)
        raise SystemExit(1)

    conn = sqlite3.connect(sidecar)
    conn.row_factory = sqlite3.Row
    _load_vec_extension(conn)

    ids = [concept_id] if concept_id else None

    if model == "all":
        models = get_registered_models(conn)
        if not models:
            click.echo("Error: no models registered. Run embed with a specific model first.", err=True)
            conn.close()
            raise SystemExit(1)
        for m in models:
            click.echo(f"Embedding with {m['model_name']}...")
            result = embed_concepts(
                conn, m["model_name"], concept_ids=ids, batch_size=batch_size,
                on_progress=lambda done, total: click.echo(f"  {done}/{total}", nl=False) if done % batch_size == 0 else None
            )
            click.echo(f"  embedded={result['embedded']} skipped={result['skipped']} errors={result['errors']}")
    else:
        def progress(done: int, total: int) -> None:
            click.echo(f"  {done}/{total} concepts embedded", err=True)

        result = embed_concepts(conn, model, concept_ids=ids, batch_size=batch_size, on_progress=progress)
        click.echo(f"Embedded: {result['embedded']}, Skipped: {result['skipped']}, Errors: {result['errors']}")

    conn.commit()
    conn.close()


# ── concept similar ──────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id")
@click.option("--model", default=None, help="litellm model string (default: first available)")
@click.option("--top-k", default=10, type=int, help="Number of results")
@click.option("--agree", is_flag=True, help="Similar under ALL stored models")
@click.option("--disagree", is_flag=True, help="Similar under some models but not others")
@click.pass_obj
def similar(obj: dict, concept_id: str, model: str | None, top_k: int, agree: bool, disagree: bool) -> None:
    """Find similar concepts by embedding distance."""
    from propstore.embed import (
        find_similar_concepts, find_similar_concepts_agree,
        find_similar_concepts_disagree, _load_vec_extension, get_registered_models,
    )

    repo: Repository = obj["repo"]
    sidecar = repo.sidecar_path
    if not sidecar.exists():
        click.echo("Error: sidecar not found. Run 'pks build' first.", err=True)
        raise SystemExit(1)

    conn = sqlite3.connect(sidecar)
    conn.row_factory = sqlite3.Row
    _load_vec_extension(conn)

    try:
        if agree:
            results = find_similar_concepts_agree(conn, concept_id, top_k=top_k)
        elif disagree:
            results = find_similar_concepts_disagree(conn, concept_id, top_k=top_k)
        else:
            if model is None:
                models = get_registered_models(conn)
                if not models:
                    click.echo("Error: no embeddings found. Run 'pks concept embed' first.", err=True)
                    raise SystemExit(1)
                model = models[0]["model_name"]
            results = find_similar_concepts(conn, concept_id, model, top_k=top_k)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    finally:
        conn.close()

    if not results:
        click.echo("No similar concepts found.")
        return

    for r in results:
        dist = r.get("distance", 0)
        cid = r.get("id", "?")
        name = r.get("canonical_name", "")
        defn = (r.get("definition") or "")[:80]
        click.echo(f"  {dist:.4f}  {cid}  {name}  — {defn}")
