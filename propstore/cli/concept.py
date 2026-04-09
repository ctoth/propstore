"""pks concept — subcommands for managing concepts."""
from __future__ import annotations

import sqlite3
from copy import deepcopy
import sys
from datetime import date
from pathlib import Path

import click
import yaml

from propstore.source import (
    align_sources,
    decide_alignment,
    load_alignment_artifact,
    promote_alignment,
)
from propstore.cli.helpers import (
    EXIT_ERROR,
    EXIT_VALIDATION,
)
from propstore.identity import (
    compute_concept_version_id,
    derive_concept_artifact_id,
    format_logical_id,
    normalize_identity_namespace,
    normalize_claim_file_payload,
    normalize_logical_value,
    primary_logical_id,
)
from propstore.form_utils import load_form_path
from propstore.knowledge_path import KnowledgePath
from propstore.cli.repository import Repository
from propstore.loaded import LoadedEntry
from propstore.validate import load_concepts, validate_concepts
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


def _require_git(repo: Repository):
    if repo.git is None:
        raise click.ClickException("concept mutations require a git-backed repository")
    return repo.git


def _concepts_tree(repo: Repository) -> KnowledgePath:
    return repo.tree() / "concepts"


def _require_repo_relative_source_path(source_path: KnowledgePath | None, *, label: str) -> str:
    if source_path is None:
        raise click.ClickException(f"{label} does not have a source path")
    relative_path = source_path.as_posix()
    if not relative_path:
        raise click.ClickException(f"{label} does not have a file path")
    return relative_path


def _require_repo_tree_path(
    source_path: KnowledgePath | None,
    repo: Repository,
    *,
    label: str,
) -> Path:
    return repo.root / Path(_require_repo_relative_source_path(source_path, label=label))


def _concept_local_handle(data: dict, *, fallback: str | None = None) -> str:
    logical_ids = data.get("logical_ids")
    if isinstance(logical_ids, list):
        for entry in logical_ids:
            if not isinstance(entry, dict):
                continue
            namespace = entry.get("namespace")
            value = entry.get("value")
            if namespace == "propstore" and isinstance(value, str) and value:
                return normalize_logical_value(value)
    raw_id = data.get("id")
    if isinstance(raw_id, str) and raw_id:
        return normalize_logical_value(raw_id)
    return normalize_logical_value(fallback or data.get("canonical_name") or "concept")


def _concept_logical_ids(
    *,
    domain: str,
    canonical_name: str,
    local_handle: str,
    existing: object = None,
) -> list[dict[str, str]]:
    primary = {
        "namespace": normalize_identity_namespace(domain or "propstore"),
        "value": normalize_logical_value(canonical_name),
    }
    logical_ids = [primary]
    seen = {format_logical_id(primary)}
    if isinstance(existing, list):
        for entry in existing:
            if not isinstance(entry, dict):
                continue
            namespace = entry.get("namespace")
            value = entry.get("value")
            if not isinstance(namespace, str) or not isinstance(value, str):
                continue
            normalized = {
                "namespace": normalize_identity_namespace(namespace),
                "value": normalize_logical_value(value),
            }
            formatted = format_logical_id(normalized)
            if formatted is None or formatted in seen:
                continue
            if normalized["namespace"] == primary["namespace"]:
                continue
            logical_ids.append(normalized)
            seen.add(formatted)
    propstore_entry = {"namespace": "propstore", "value": normalize_logical_value(local_handle)}
    formatted_propstore = format_logical_id(propstore_entry)
    if formatted_propstore is not None and formatted_propstore not in seen:
        logical_ids.append(propstore_entry)
    return logical_ids


def _normalize_concept_data(
    data: dict,
    *,
    canonical_name: str | None = None,
    domain: str | None = None,
    local_handle: str | None = None,
) -> dict:
    normalized = deepcopy(data)
    raw_id = normalized.pop("id", None)
    effective_name = canonical_name or normalized.get("canonical_name")
    if not isinstance(effective_name, str) or not effective_name:
        effective_name = str(raw_id or local_handle or "concept")
    normalized["canonical_name"] = effective_name
    effective_domain = domain or normalized.get("domain") or "propstore"
    normalized["domain"] = effective_domain
    propstore_handle = normalize_logical_value(
        local_handle or _concept_local_handle(normalized, fallback=str(raw_id or effective_name))
    )
    artifact_id = normalized.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        artifact_id = derive_concept_artifact_id("propstore", propstore_handle)
    normalized["artifact_id"] = artifact_id
    normalized["logical_ids"] = _concept_logical_ids(
        domain=str(effective_domain),
        canonical_name=str(effective_name),
        local_handle=propstore_handle,
        existing=normalized.get("logical_ids"),
    )
    normalized["version_id"] = compute_concept_version_id(normalized)
    return normalized


def _concept_display_handle(data: dict) -> str:
    return primary_logical_id(data) or data.get("canonical_name") or data.get("artifact_id") or "?"


def _build_concept_registry(
    concepts: list[LoadedEntry],
    *,
    forms_root: KnowledgePath,
) -> dict[str, dict]:
    registry: dict[str, dict] = {}
    for concept_record in concepts:
        data = deepcopy(concept_record.data)
        form_name = data.get("form")
        if isinstance(form_name, str) and form_name:
            form_def = load_form_path(forms_root, form_name)
            if form_def is None:
                raise click.ClickException(
                    f"concept '{data.get('artifact_id') or data.get('canonical_name') or concept_record.filename}' "
                    f"references missing form definition '{form_name}'"
                )
            data["_form_definition"] = form_def
        artifact_id = data.get("artifact_id")
        if isinstance(artifact_id, str) and artifact_id:
            registry[artifact_id] = data
        canonical_name = data.get("canonical_name")
        if isinstance(canonical_name, str) and canonical_name and canonical_name not in registry:
            registry[canonical_name] = data
        logical_ids = data.get("logical_ids")
        if isinstance(logical_ids, list):
            for entry in logical_ids:
                if not isinstance(entry, dict):
                    continue
                formatted = format_logical_id(entry)
                if formatted and formatted not in registry:
                    registry[formatted] = data
        aliases = data.get("aliases")
        if isinstance(aliases, list):
            for alias in aliases:
                alias_name = alias.get("name") if isinstance(alias, dict) else None
                if isinstance(alias_name, str) and alias_name and alias_name not in registry:
                    registry[alias_name] = data
    return registry


def _find_concept_entry(repo: Repository, id_or_name: str) -> LoadedEntry | None:
    concepts = load_concepts(_concepts_tree(repo))
    direct = _concepts_tree(repo) / f"{id_or_name}.yaml"
    if direct.exists():
        direct_rel = direct.as_posix()
        for concept in concepts:
            if concept.source_path is not None and concept.source_path.as_posix() == direct_rel:
                return concept
    for concept in concepts:
        if concept.data.get("canonical_name") == id_or_name:
            return concept
        if concept.data.get("artifact_id") == id_or_name:
            return concept
        logical_ids = concept.data.get("logical_ids")
        if isinstance(logical_ids, list):
            for entry in logical_ids:
                if isinstance(entry, dict) and format_logical_id(entry) == id_or_name:
                    return concept
        aliases = concept.data.get("aliases")
        if isinstance(aliases, list):
            for alias in aliases:
                if isinstance(alias, dict) and alias.get("name") == id_or_name:
                    return concept
    return None


def _require_concept_artifact_id(repo: Repository, handle: str, *, label: str) -> str:
    concept_entry = _find_concept_entry(repo, handle)
    if concept_entry is None:
        raise click.ClickException(f"{label} '{handle}' not found")
    artifact_id = concept_entry.data.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        raise click.ClickException(f"{label} '{handle}' does not have an artifact_id")
    return artifact_id


def _resolve_sidecar_concept_id(conn: sqlite3.Connection, handle: str) -> str:
    conn.row_factory = sqlite3.Row
    direct = conn.execute("SELECT id FROM concept WHERE id = ?", (handle,)).fetchone()
    if direct is not None:
        return str(direct["id"])
    primary = conn.execute(
        "SELECT id FROM concept WHERE primary_logical_id = ?",
        (handle,),
    ).fetchone()
    if primary is not None:
        return str(primary["id"])
    canonical = conn.execute(
        "SELECT id FROM concept WHERE canonical_name = ?",
        (handle,),
    ).fetchone()
    if canonical is not None:
        return str(canonical["id"])
    alias = conn.execute(
        "SELECT concept_id FROM alias WHERE alias_name = ?",
        (handle,),
    ).fetchone()
    if alias is not None:
        return str(alias["concept_id"])
    raise click.ClickException(f"Concept '{handle}' not found")


# ── concept add ──────────────────────────────────────────────────────

@concept.command()
@click.option("--domain", required=True, help="Domain prefix (e.g. speech, a11y, finance)")
@click.option("--name", required=True, help="Canonical name (lowercase, underscored)")
@click.option("--definition", default=None, help="Definition (prompted if omitted)")
@click.option("--form", "form_name", default=None,
              help="Form name (references forms/<name>.yaml, prompted if omitted)")
@click.option("--values", default=None, help="Comma-separated values (required for category concepts)")
@click.option("--closed", is_flag=True, default=False, help="Declare category value set as exhaustive (extensible: false)")
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing")
@click.pass_obj
def add(
    obj: dict,
    domain: str,
    name: str,
    definition: str | None,
    form_name: str | None,
    values: str | None,
    closed: bool,
    dry_run: bool,
) -> None:
    """Add a new concept to the registry."""
    repo: Repository = obj["repo"]
    git = _require_git(repo)
    # Prompt for missing fields
    if definition is None:
        definition = click.prompt("Definition")
    if form_name is None:
        # List available forms
        forms = repo.tree() / "forms"
        if forms.exists():
            available = sorted(f.stem for f in forms.iterdir() if f.suffix == ".yaml")
            click.echo(f"Available forms: {', '.join(available)}")
        form_name = click.prompt("Form")

    filepath = repo.root / "concepts" / f"{name}.yaml"
    semantic_path = _concepts_tree(repo) / f"{name}.yaml"
    if semantic_path.exists():
        click.echo(f"ERROR: Concept file '{filepath}' already exists", err=True)
        sys.exit(EXIT_ERROR)

    cid = f"concept{git.next_concept_id()}"

    data = {
        "canonical_name": name,
        "status": "proposed",
        "definition": definition,
        "domain": domain,
        "created_date": str(date.today()),
        "form": form_name,
    }

    # Category concepts require --values
    if form_name == "category":
        if values is None:
            click.echo("ERROR: --values is required when --form=category", err=True)
            sys.exit(EXIT_ERROR)
        value_list = [v.strip() for v in values.split(",") if v.strip()]
        if not value_list:
            click.echo("ERROR: --values must contain at least one value", err=True)
            sys.exit(EXIT_ERROR)
        fp: dict = {"values": value_list}
        if closed:
            fp["extensible"] = False
        data["form_parameters"] = fp
    elif values is not None:
        click.echo("ERROR: --values is only valid with --form=category", err=True)
        sys.exit(EXIT_ERROR)
    elif closed:
        click.echo("ERROR: --closed is only valid with --form=category", err=True)
        sys.exit(EXIT_ERROR)

    data = _normalize_concept_data(data, local_handle=cid)

    if dry_run:
        click.echo(f"Would create {filepath}")
        click.echo(yaml.dump(data, default_flow_style=False, sort_keys=False))
        return

    concepts = load_concepts(_concepts_tree(repo))
    concepts.append(
        LoadedEntry(
            filename=name,
            source_path=semantic_path,
            knowledge_root=repo.tree(),
            data=data,
        )
    )

    result = validate_concepts(concepts, forms_dir=repo.tree() / "forms")
    if not result.ok:
        for e in result.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Validation failed. No changes written.", err=True)
        sys.exit(EXIT_VALIDATION)

    for w in result.warnings:
        click.echo(f"WARNING: {w}", err=True)

    yaml_bytes = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True).encode("utf-8")
    rel_path = f"concepts/{name}.yaml"
    git.commit_files({rel_path: yaml_bytes}, f"Add concept: {name} ({_concept_display_handle(data)})")
    git.sync_worktree()
    click.echo(f"Created {filepath} with logical ID {_concept_display_handle(data)}")


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
    git = _require_git(repo)
    concept_entry = _find_concept_entry(repo, concept_id)
    if concept_entry is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)

    filepath = _require_repo_tree_path(concept_entry.source_path, repo, label=f"concept '{concept_entry.filename}'")
    data = deepcopy(concept_entry.data)

    # Warn if alias matches another concept's canonical_name
    for other_entry in load_concepts(_concepts_tree(repo)):
        if other_entry.source_path is not None and concept_entry.source_path is not None:
            if other_entry.source_path.as_posix() == concept_entry.source_path.as_posix():
                continue
        if other_entry.data.get("canonical_name") == name:
            click.echo(
                f"WARNING: alias '{name}' matches canonical_name of "
                f"concept '{other_entry.data.get('id')}'", err=True)

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
    data = _normalize_concept_data(data)

    yaml_bytes = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True).encode("utf-8")
    rel_path = _require_repo_relative_source_path(
        concept_entry.source_path,
        label=f"concept '{concept_entry.filename}'",
    )
    git.commit_files({rel_path: yaml_bytes}, f"Add alias '{name}' to {_concept_display_handle(data)}")
    git.sync_worktree()

    click.echo(f"Added alias '{name}' to {_concept_display_handle(data)} ({filepath.stem})")


# ── concept rename ───────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id")
@click.option("--name", required=True, help="New canonical name")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def rename(obj: dict, concept_id: str, name: str, dry_run: bool) -> None:
    """Rename a concept (updates canonical_name and filename)."""
    repo: Repository = obj["repo"]
    git = _require_git(repo)
    concept_entry = _find_concept_entry(repo, concept_id)
    if concept_entry is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)

    filepath = _require_repo_tree_path(
        concept_entry.source_path,
        repo,
        label=f"concept '{concept_entry.filename}'",
    )
    data = deepcopy(concept_entry.data)
    old_name = data.get("canonical_name", filepath.stem)
    new_path = filepath.parent / f"{name}.yaml"
    new_semantic_path = _concepts_tree(repo) / f"{name}.yaml"
    if old_name == name:
        click.echo(f"No change: concept already named '{name}'")
        return
    if new_semantic_path.exists():
        click.echo(f"ERROR: Concept file '{new_path}' already exists", err=True)
        sys.exit(EXIT_ERROR)

    if dry_run:
        click.echo(f"Would rename: {old_name} -> {name}")
        click.echo(f"  {filepath} -> {new_path}")
        return

    loaded_concepts = load_concepts(repo.tree() / "concepts")
    updated_concepts = []
    changed_concept_paths: set[Path] = set()
    for concept_record in loaded_concepts:
        concept_path = _require_repo_tree_path(
            concept_record.source_path,
            repo,
            label=f"concept '{concept_record.filename}'",
        )
        concept_data = deepcopy(concept_record.data)
        local_handle = _concept_local_handle(concept_record.data, fallback=concept_record.filename)
        if concept_path == filepath:
            concept_data["canonical_name"] = name
            concept_data["last_modified"] = str(date.today())
            changed_concept_paths.add(concept_path)
        if _rewrite_concept_conditions(concept_data, old_name, name):
            changed_concept_paths.add(concept_path)
        concept_data = _normalize_concept_data(concept_data, local_handle=local_handle)
        source_path = concept_record.source_path
        if source_path is None:
            raise click.ClickException(f"concept '{concept_record.filename}' does not have a source path")
        updated_concepts.append(
            type(concept_record)(
                filename=name if concept_path == filepath else concept_record.filename,
                source_path=(source_path.parent / f"{name}.yaml") if concept_path == filepath else source_path,
                knowledge_root=concept_record.knowledge_root,
                data=concept_data,
            )
        )

    claims_root = repo.tree() / "claims"
    concept_validation = validate_concepts(
        updated_concepts,
        claims_dir=claims_root if claims_root.exists() else None,
        forms_dir=repo.tree() / "forms",
    )
    if not concept_validation.ok:
        for e in concept_validation.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Rename validation failed. No changes written.", err=True)
        sys.exit(EXIT_VALIDATION)
    claim_files = load_claim_files(claims_root) if claims_root.exists() else []
    updated_claim_files = []
    changed_claim_paths: set[Path] = set()
    if claim_files:
        for claim_file in claim_files:
            claim_path = _require_repo_tree_path(
                claim_file.source_path,
                repo,
                label=f"claim file '{claim_file.filename}'",
            )
            claim_data = deepcopy(claim_file.data)
            if _rewrite_claim_conditions(claim_data, old_name, name):
                changed_claim_paths.add(claim_path)
                claim_data, _ = normalize_claim_file_payload(claim_data)
            source_path = claim_file.source_path
            if source_path is None:
                raise click.ClickException(f"claim file '{claim_file.filename}' does not have a source path")
            updated_claim_files.append(type(claim_file)(
                filename=claim_file.filename,
                source_path=source_path,
                data=claim_data,
            ))
        concept_registry = _build_concept_registry(
            updated_concepts,
            forms_root=repo.tree() / "forms",
        )
        claim_validation = validate_claims(updated_claim_files, concept_registry)
        if not claim_validation.ok:
            for e in claim_validation.errors:
                click.echo(f"ERROR: {e}", err=True)
            click.echo("Rename validation failed. No changes written.", err=True)
            sys.exit(EXIT_VALIDATION)

    adds: dict[str | Path, bytes] = {}
    for concept_record in updated_concepts:
        target_rel = _require_repo_relative_source_path(
            concept_record.source_path,
            label=f"concept '{concept_record.filename}'",
        )
        target_path = repo.root / Path(target_rel)
        if target_path == new_path or target_path in changed_concept_paths:
            yaml_bytes = yaml.dump(
                concept_record.data, default_flow_style=False,
                sort_keys=False, allow_unicode=True,
            ).encode("utf-8")
            adds[target_rel] = yaml_bytes

    for claim_file in updated_claim_files:
        claim_rel = _require_repo_relative_source_path(
            claim_file.source_path,
            label=f"claim file '{claim_file.filename}'",
        )
        claim_path = repo.root / Path(claim_rel)
        if claim_path in changed_claim_paths:
            yaml_bytes = yaml.dump(
                claim_file.data, default_flow_style=False,
                sort_keys=False, allow_unicode=True,
            ).encode("utf-8")
            adds[claim_rel] = yaml_bytes

    old_rel = _require_repo_relative_source_path(
        concept_entry.source_path,
        label=f"concept '{concept_entry.filename}'",
    )
    git.commit_batch(
        adds=adds,
        deletes=[old_rel],
        message=f"Rename concept: {old_name} -> {name}",
    )
    git.sync_worktree()

    click.echo(f"{old_name} -> {name}")
    click.echo(f"  {filepath} -> {new_path}")
    click.echo(f"  Logical ID: {_concept_display_handle(updated_concepts[0].data) if updated_concepts else name}")


# ── concept deprecate ────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id")
@click.option("--replaced-by", required=True, help="Replacement concept ID")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def deprecate(obj: dict, concept_id: str, replaced_by: str, dry_run: bool) -> None:
    """Deprecate a concept with a replacement."""
    repo: Repository = obj["repo"]
    git = _require_git(repo)
    concept_entry = _find_concept_entry(repo, concept_id)
    if concept_entry is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)
    filepath = _require_repo_tree_path(
        concept_entry.source_path,
        repo,
        label=f"concept '{concept_entry.filename}'",
    )

    # Validate replacement target
    replacement_entry = _find_concept_entry(repo, replaced_by)
    if replacement_entry is None:
        click.echo(f"ERROR: Replacement concept '{replaced_by}' not found", err=True)
        sys.exit(EXIT_ERROR)

    replacement_data = replacement_entry.data
    if replacement_data.get("status") == "deprecated":
        click.echo(f"ERROR: Replacement concept '{replaced_by}' is itself deprecated", err=True)
        sys.exit(EXIT_ERROR)

    data = deepcopy(concept_entry.data)

    if dry_run:
        click.echo(f"Would deprecate {_concept_display_handle(data)} ({filepath.stem})")
        click.echo(f"  replaced_by: {_concept_display_handle(replacement_data)}")
        return

    data["status"] = "deprecated"
    replacement_artifact_id = replacement_data.get("artifact_id")
    if not isinstance(replacement_artifact_id, str) or not replacement_artifact_id:
        raise click.ClickException(f"Replacement concept '{replaced_by}' does not have an artifact_id")
    data["replaced_by"] = replacement_artifact_id
    data["last_modified"] = str(date.today())
    data = _normalize_concept_data(data)

    yaml_bytes = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True).encode("utf-8")
    rel_path = _require_repo_relative_source_path(
        concept_entry.source_path,
        label=f"concept '{concept_entry.filename}'",
    )
    git.commit_files(
        {rel_path: yaml_bytes},
        f"Deprecate {_concept_display_handle(data)}, replaced by {_concept_display_handle(replacement_data)}",
    )
    git.sync_worktree()

    click.echo(f"Deprecated {_concept_display_handle(data)} ({filepath.stem}), replaced by {_concept_display_handle(replacement_data)}")


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
    git = _require_git(repo)
    concept_entry = _find_concept_entry(repo, source_id)
    if concept_entry is None:
        click.echo(f"ERROR: Source concept '{source_id}' not found", err=True)
        sys.exit(EXIT_ERROR)
    filepath = _require_repo_tree_path(
        concept_entry.source_path,
        repo,
        label=f"concept '{concept_entry.filename}'",
    )

    target_entry = _find_concept_entry(repo, target_id)
    if target_entry is None:
        click.echo(f"ERROR: Target concept '{target_id}' not found", err=True)
        sys.exit(EXIT_ERROR)
    target_artifact_id = target_entry.data.get("artifact_id")
    if not isinstance(target_artifact_id, str) or not target_artifact_id:
        raise click.ClickException(f"Target concept '{target_id}' does not have an artifact_id")

    data = deepcopy(concept_entry.data)

    rel: dict[str, object] = {"type": rel_type, "target": target_artifact_id}
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
    data = _normalize_concept_data(data)

    concepts = load_concepts(repo.tree() / "concepts")
    updated_concepts = []
    for concept_record in concepts:
        concept_path = _require_repo_tree_path(
            concept_record.source_path,
            repo,
            label=f"concept '{concept_record.filename}'",
        )
        updated_concepts.append(
            LoadedEntry(
                filename=concept_record.filename,
                source_path=concept_record.source_path,
                knowledge_root=concept_record.knowledge_root,
                data=data if concept_path == filepath else concept_record.data,
            )
        )
    validation = validate_concepts(
        updated_concepts,
        claims_dir=(repo.tree() / "claims") if (repo.tree() / "claims").exists() else None,
        forms_dir=repo.tree() / "forms",
    )
    if not validation.ok:
        for e in validation.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Validation failed. No changes written.", err=True)
        sys.exit(EXIT_VALIDATION)

    for w in validation.warnings:
        click.echo(f"WARNING: {w}", err=True)

    yaml_bytes = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True).encode("utf-8")
    rel_path = _require_repo_relative_source_path(
        concept_entry.source_path,
        label=f"concept '{concept_entry.filename}'",
    )
    git.commit_files({rel_path: yaml_bytes}, f"Link {_concept_display_handle(data)} {rel_type} {_concept_display_handle(target_entry.data)}")
    git.sync_worktree()

    click.echo(f"Added {rel_type} -> {_concept_display_handle(target_entry.data)} on {_concept_display_handle(data)} ({filepath.stem})")


# ── concept search ───────────────────────────────────────────────────

@concept.command()
@click.argument("query")
@click.pass_obj
def search(obj: dict, query: str) -> None:
    """Search concepts by name, definition, or alias."""
    repo: Repository = obj["repo"]
    sidecar = repo.sidecar_path

    if not sidecar.exists():
        raise click.ClickException(
            "concept search requires a built sidecar; run 'pks build' first"
        )

    import contextlib
    conn = sqlite3.connect(sidecar)
    with contextlib.closing(conn):
        rows = conn.execute(
            "SELECT concept.primary_logical_id, concept_fts.canonical_name, concept_fts.definition "
            "FROM concept_fts JOIN concept ON concept.id = concept_fts.concept_id "
            "WHERE concept_fts MATCH ? LIMIT 20",
            (query,),
        ).fetchall()
    if rows:
        for logical_id, name, defn in rows:
            snippet = (defn or "")[:80]
            click.echo(f"  {logical_id}  {name}  — {snippet}")
    else:
        click.echo("No matches.")


# ── concept list ─────────────────────────────────────────────────────

@concept.command("list")
@click.option("--domain", default=None, help="Filter by domain")
@click.option("--status", default=None, help="Filter by status")
@click.pass_obj
def list_concepts(obj: dict, domain: str | None, status: str | None) -> None:
    """List concepts, optionally filtered."""
    repo: Repository = obj["repo"]
    concepts_tree = _concepts_tree(repo)
    if not concepts_tree.exists():
        click.echo("No concepts directory found.")
        return

    concepts = load_concepts(concepts_tree)
    for c in concepts:
        d = c.data
        c_domain = d.get("domain", "")
        c_status = d.get("status", "")

        if domain and c_domain != domain:
            continue
        if status and c_status != status:
            continue

        click.echo(f"  {_concept_display_handle(d):30s} {d.get('canonical_name', '?'):30s} [{c_status}]")


# ── concept add-value ────────────────────────────────────────────────

@concept.command("add-value")
@click.argument("concept_name")
@click.option("--value", required=True, help="Value to add to the category concept's value set")
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing")
@click.pass_obj
def add_value(obj: dict, concept_name: str, value: str, dry_run: bool) -> None:
    """Add a value to a category concept's value set."""
    repo: Repository = obj["repo"]
    git = _require_git(repo)
    concept_entry = _find_concept_entry(repo, concept_name)
    if concept_entry is None:
        click.echo(f"ERROR: Concept '{concept_name}' not found", err=True)
        sys.exit(EXIT_ERROR)
    filepath = _require_repo_tree_path(
        concept_entry.source_path,
        repo,
        label=f"concept '{concept_entry.filename}'",
    )

    data = deepcopy(concept_entry.data)

    if data.get("form") != "category":
        click.echo(f"ERROR: '{concept_name}' is not a category concept (form={data.get('form')})", err=True)
        sys.exit(EXIT_ERROR)

    fp = data.get("form_parameters", {}) or {}
    extensible = fp.get("extensible", True)
    if not extensible:
        click.echo(f"ERROR: '{concept_name}' is not extensible — cannot add values", err=True)
        sys.exit(EXIT_ERROR)

    values = fp.get("values", [])
    if value in values:
        click.echo(f"ERROR: Value '{value}' already exists in '{concept_name}'", err=True)
        sys.exit(EXIT_ERROR)

    if dry_run:
        click.echo(f"Would add '{value}' to {concept_name} values: {values + [value]}")
        return

    values.append(value)
    fp["values"] = values
    data["form_parameters"] = fp
    data["last_modified"] = str(date.today())
    data = _normalize_concept_data(data)

    yaml_bytes = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True).encode("utf-8")
    rel_path = _require_repo_relative_source_path(
        concept_entry.source_path,
        label=f"concept '{concept_entry.filename}'",
    )
    git.commit_files({rel_path: yaml_bytes}, f"Add value '{value}' to {concept_name}")
    git.sync_worktree()
    click.echo(f"Added '{value}' to {concept_name} — values: {', '.join(values)}")


# ── concept categories ───────────────────────────────────────────────

@concept.command("categories")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_obj
def categories(obj: dict, as_json: bool) -> None:
    """List all category concepts and their allowed values."""
    repo: Repository = obj["repo"]
    concepts = load_concepts(repo.tree() / "concepts")

    cat_data = {}
    for c in concepts:
        if c.data.get("form") != "category":
            continue
        fp = c.data.get("form_parameters", {}) or {}
        values = fp.get("values", [])
        extensible = fp.get("extensible", True)
        cat_data[c.data["canonical_name"]] = {
            "values": values,
            "extensible": extensible,
        }

    if as_json:
        import json
        click.echo(json.dumps(cat_data, indent=2))
        return

    if not cat_data:
        click.echo("No category concepts found.")
        return

    for name, info in sorted(cat_data.items()):
        ext = " (extensible)" if info["extensible"] else ""
        vals = ", ".join(info["values"])
        click.echo(f"{name}{ext}: {vals}")


# ── concept show ─────────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id_or_name")
@click.pass_obj
def show(obj: dict, concept_id_or_name: str) -> None:
    """Show full concept YAML."""
    repo: Repository = obj["repo"]
    if concept_id_or_name.startswith("align:"):
        try:
            _, artifact = load_alignment_artifact(repo, concept_id_or_name)
        except FileNotFoundError:
            click.echo(f"ERROR: Concept alignment '{concept_id_or_name}' not found", err=True)
            sys.exit(EXIT_ERROR)
        click.echo(
            yaml.dump(
                artifact,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            ).rstrip()
        )
        return
    concept_entry = _find_concept_entry(repo, concept_id_or_name)
    if concept_entry is None:
        click.echo(f"ERROR: Concept '{concept_id_or_name}' not found", err=True)
        sys.exit(EXIT_ERROR)

    click.echo(
        yaml.dump(
            concept_entry.data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        ).rstrip()
    )


@concept.command("align")
@click.option("--sources", "first_source", required=True)
@click.argument("extra_sources", nargs=-1)
@click.pass_obj
def align_cmd(obj: dict, first_source: str, extra_sources: tuple[str, ...]) -> None:
    """Build and persist a concept-alignment artifact from source branches."""
    repo: Repository = obj["repo"]
    artifact = align_sources(repo, [first_source, *extra_sources])
    click.echo(f"Created {artifact['id']}")


@concept.command("query")
@click.argument("cluster_id")
@click.option("--mode", type=click.Choice(["skeptical", "credulous"]), default="credulous")
@click.option("--operator", type=click.Choice(["sum", "max", "leximax"]), default=None)
@click.pass_obj
def query_alignment(obj: dict, cluster_id: str, mode: str, operator: str | None) -> None:
    """Query an alignment artifact."""
    repo: Repository = obj["repo"]
    try:
        _, artifact = load_alignment_artifact(repo, cluster_id)
    except FileNotFoundError:
        click.echo(f"ERROR: Concept alignment '{cluster_id}' not found", err=True)
        sys.exit(EXIT_ERROR)

    queries = artifact.get("queries", {})
    if operator is not None:
        scores = queries.get("operator_scores", {}).get(operator, {})
        for argument_id, score in sorted(scores.items()):
            click.echo(f"{argument_id}\t{score}")
        return

    accepted = queries.get(f"{mode}_acceptance", [])
    for argument_id in accepted:
        click.echo(argument_id)


@concept.command("decide")
@click.argument("cluster_id")
@click.option("--accept", "accepted", multiple=True)
@click.option("--reject", "rejected", multiple=True)
@click.pass_obj
def decide_cmd(obj: dict, cluster_id: str, accepted: tuple[str, ...], rejected: tuple[str, ...]) -> None:
    """Persist accepted and rejected alternatives for an alignment artifact."""
    repo: Repository = obj["repo"]
    updated = decide_alignment(repo, cluster_id, accept=list(accepted), reject=list(rejected))
    click.echo(f"Updated {updated['id']}")


@concept.command("promote")
@click.argument("cluster_id")
@click.pass_obj
def promote_cmd(obj: dict, cluster_id: str) -> None:
    """Promote an accepted alignment alternative into the canonical concept registry."""
    repo: Repository = obj["repo"]
    try:
        updated = promote_alignment(repo, cluster_id)
    except ValueError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(EXIT_ERROR)
    click.echo(f"Promoted {updated['id']}")


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

    import contextlib
    conn = sqlite3.connect(sidecar)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        _load_vec_extension(conn)

        ids = [_resolve_sidecar_concept_id(conn, concept_id)] if concept_id else None

        if model == "all":
            models = get_registered_models(conn)
            if not models:
                click.echo("Error: no models registered. Run embed with a specific model first.", err=True)
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
            resolved_id = _resolve_sidecar_concept_id(conn, concept_id)
            results = find_similar_concepts_agree(conn, resolved_id, top_k=top_k)
        elif disagree:
            resolved_id = _resolve_sidecar_concept_id(conn, concept_id)
            results = find_similar_concepts_disagree(conn, resolved_id, top_k=top_k)
        else:
            if model is None:
                models = get_registered_models(conn)
                if not models:
                    click.echo("Error: no embeddings found. Run 'pks concept embed' first.", err=True)
                    raise SystemExit(1)
                model = str(models[0]["model_name"])
            resolved_id = _resolve_sidecar_concept_id(conn, concept_id)
            results = find_similar_concepts(conn, resolved_id, model, top_k=top_k)
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
        cid = r.get("primary_logical_id") or r.get("id", "?")
        name = r.get("canonical_name", "")
        defn = (r.get("definition") or "")[:80]
        click.echo(f"  {dist:.4f}  {cid}  {name}  — {defn}")
