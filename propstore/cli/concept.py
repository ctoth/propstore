"""pks concept — subcommands for managing concepts."""
from __future__ import annotations

import sqlite3
from copy import deepcopy
import sys
from datetime import date
from pathlib import Path
from typing import TypeVar

import click

from propstore.claims import (
    LoadedClaimsFile,
    claim_file_payload,
    loaded_claim_file_from_payload,
    load_claim_files,
)
from propstore.artifacts.documents.claims import ClaimsFileDocument
from propstore.artifacts.documents.concepts import ConceptDocument
from propstore.artifacts.families import CLAIMS_FILE_FAMILY, CONCEPT_FILE_FAMILY
from propstore.artifacts.identity import (
    normalize_canonical_concept_payload,
    normalize_claim_file_payload,
)
from propstore.artifacts.refs import ClaimsFileRef, ConceptFileRef
from propstore.artifacts.types import ArtifactFamily
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
    format_logical_id,
    primary_logical_id,
)
from propstore.core.concepts import (
    LoadedConcept,
    concept_document_to_payload,
    concept_document_to_record_payload,
    parse_concept_record,
    parse_concept_record_document,
)
from propstore.core.concept_relationship_types import VALID_CONCEPT_RELATIONSHIP_TYPES
from propstore.compiler.context import build_compilation_context_from_loaded
from propstore.concept_ids import next_concept_id
from propstore.knowledge_path import KnowledgePath
from propstore.repository import Repository
from propstore.storage.snapshot import RepositorySnapshot
from propstore.core.concepts import load_concepts
from propstore.validate_concepts import validate_concepts
from propstore.compiler.passes import validate_claims

RELATIONSHIP_TYPES = tuple(sorted(VALID_CONCEPT_RELATIONSHIP_TYPES))
QUALIA_ROLES = ("formal", "constitutive", "telic", "agentive")
PROTO_ROLE_KINDS = ("agent", "patient")
TRef = TypeVar("TRef")
TDoc = TypeVar("TDoc")


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


def _require_snapshot(repo: Repository) -> RepositorySnapshot:
    try:
        repo.snapshot.head_sha()
    except ValueError as exc:
        raise click.ClickException("concept mutations require a git-backed repository") from exc
    return repo.snapshot


def _concepts_tree(repo: Repository) -> KnowledgePath:
    return repo.tree() / "concepts"


def _artifact_source(repo: Repository, family: ArtifactFamily[TRef, TDoc], ref: TRef) -> str:
    return repo.artifacts.resolve(family, ref).relpath


def _artifact_tree_path(repo: Repository, family: ArtifactFamily[TRef, TDoc], ref: TRef) -> Path:
    return repo.root / Path(_artifact_source(repo, family, ref))

def _artifact_knowledge_path(repo: Repository, family: ArtifactFamily[TRef, TDoc], ref: TRef) -> KnowledgePath:
    return repo.tree() / _artifact_source(repo, family, ref)


def _concept_ref(concept_entry: LoadedConcept) -> ConceptFileRef:
    return ConceptFileRef(concept_entry.filename)


def _claims_ref(claim_file: LoadedClaimsFile) -> ClaimsFileRef:
    return ClaimsFileRef(claim_file.filename)


def _concept_document(repo: Repository, ref: ConceptFileRef, data: dict) -> ConceptDocument:
    payload = _normalize_concept_data(data)
    return repo.artifacts.coerce(
        CONCEPT_FILE_FAMILY,
        payload,
        source=_artifact_source(repo, CONCEPT_FILE_FAMILY, ref),
    )


def _canonical_concept_document(repo: Repository, ref: ConceptFileRef, data: dict) -> ConceptDocument:
    document = _concept_document(repo, ref, data)
    return _concept_document(repo, ref, concept_document_to_payload(document))


def _claims_document(repo: Repository, ref: ClaimsFileRef, data: dict) -> ClaimsFileDocument:
    return repo.artifacts.coerce(CLAIMS_FILE_FAMILY, data, source=_artifact_source(repo, CLAIMS_FILE_FAMILY, ref))


def _concept_artifact_payload(concept_entry: LoadedConcept) -> dict:
    if concept_entry.document is not None:
        return concept_document_to_payload(concept_entry.document)
    return _normalize_concept_data(concept_entry.record.to_payload())


def _normalize_concept_data(
    data: dict,
    *,
    canonical_name: str | None = None,
    domain: str | None = None,
    local_handle: str | None = None,
) -> dict:
    return normalize_canonical_concept_payload(
        deepcopy(data),
        canonical_name=canonical_name,
        domain=domain,
        local_handle=local_handle,
    )


def _concept_display_handle(data: dict) -> str:
    lexical_entry = data.get("lexical_entry")
    lexical_name = None
    if isinstance(lexical_entry, dict):
        canonical_form = lexical_entry.get("canonical_form")
        if isinstance(canonical_form, dict):
            lexical_name = canonical_form.get("written_rep")
    return primary_logical_id(data) or data.get("canonical_name") or lexical_name or data.get("artifact_id") or "?"


def _find_concept_entry(repo: Repository, id_or_name: str) -> LoadedConcept | None:
    concepts = load_concepts(_concepts_tree(repo))
    for concept in concepts:
        if concept.filename == id_or_name:
            return concept
        data = concept.record.to_payload()
        if data.get("canonical_name") == id_or_name:
            return concept
        if data.get("artifact_id") == id_or_name:
            return concept
        logical_ids = data.get("logical_ids")
        if isinstance(logical_ids, list):
            for entry in logical_ids:
                if isinstance(entry, dict) and format_logical_id(entry) == id_or_name:
                    return concept
        aliases = data.get("aliases")
        if isinstance(aliases, list):
            for alias in aliases:
                if isinstance(alias, dict) and alias.get("name") == id_or_name:
                    return concept
    return None


def _require_concept_artifact_id(repo: Repository, handle: str, *, label: str) -> str:
    concept_entry = _find_concept_entry(repo, handle)
    if concept_entry is None:
        raise click.ClickException(f"{label} '{handle}' not found")
    artifact_id = concept_entry.record.to_payload().get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        raise click.ClickException(f"{label} '{handle}' does not have an artifact_id")
    return artifact_id


def _require_concept_reference(repo: Repository, handle: str, *, label: str) -> dict[str, str]:
    concept_entry = _find_concept_entry(repo, handle)
    if concept_entry is None:
        raise click.ClickException(f"{label} '{handle}' not found")
    data = concept_entry.record.to_payload()
    artifact_id = data.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        raise click.ClickException(f"{label} '{handle}' does not have an artifact_id")
    reference: dict[str, str] = {"uri": artifact_id}
    canonical_name = data.get("canonical_name")
    if isinstance(canonical_name, str) and canonical_name:
        reference["label"] = canonical_name
    return reference


def _provenance_payload(
    *,
    asserter: str,
    timestamp: str,
    source_artifact_code: str,
    method: str,
) -> dict[str, object]:
    return {
        "status": "stated",
        "witnesses": [
            {
                "asserter": asserter,
                "timestamp": timestamp,
                "source_artifact_code": source_artifact_code,
                "method": method,
            }
        ],
    }


def _first_lexical_sense(data: dict) -> dict:
    lexical_entry = data.get("lexical_entry")
    if not isinstance(lexical_entry, dict):
        raise click.ClickException("concept is missing lexical_entry")
    senses = lexical_entry.get("senses")
    if not isinstance(senses, list) or not senses or not isinstance(senses[0], dict):
        raise click.ClickException("concept lexical_entry requires at least one sense")
    return senses[0]


def _validate_updated_concept(
    repo: Repository,
    concept_entry: LoadedConcept,
    document: ConceptDocument,
) -> None:
    ref = _concept_ref(concept_entry)
    concepts = []
    for loaded in load_concepts(_concepts_tree(repo)):
        if _concept_ref(loaded) == ref:
            concepts.append(
                LoadedConcept(
                    filename=loaded.filename,
                    source_path=_artifact_knowledge_path(repo, CONCEPT_FILE_FAMILY, ref),
                    knowledge_root=loaded.knowledge_root,
                    record=parse_concept_record_document(document),
                    document=document,
                )
            )
            continue
        concepts.append(loaded)

    validation = validate_concepts(
        concepts,
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
    snapshot = _require_snapshot(repo)
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

    ref = ConceptFileRef(name)
    filepath = _artifact_tree_path(repo, CONCEPT_FILE_FAMILY, ref)
    semantic_path = _artifact_knowledge_path(repo, CONCEPT_FILE_FAMILY, ref)
    if semantic_path.exists():
        click.echo(f"ERROR: Concept file '{filepath}' already exists", err=True)
        sys.exit(EXIT_ERROR)

    cid = f"concept{next_concept_id(repo.tree() / 'concepts')}"

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
    document = _concept_document(repo, ref, data)

    if dry_run:
        click.echo(f"Would create {filepath}")
        click.echo(repo.artifacts.render(document))
        return

    concepts = load_concepts(_concepts_tree(repo))
    concepts.append(
        LoadedConcept(
            filename=name,
            source_path=semantic_path,
            knowledge_root=repo.tree(),
            record=parse_concept_record_document(document),
            document=document,
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

    repo.artifacts.save(
        CONCEPT_FILE_FAMILY,
        ref,
        document,
        message=f"Add concept: {name} ({_concept_display_handle(concept_document_to_record_payload(document))})",
    )
    snapshot.sync_worktree()
    click.echo(f"Created {filepath} with logical ID {_concept_display_handle(concept_document_to_record_payload(document))}")


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
    snapshot = _require_snapshot(repo)
    concept_entry = _find_concept_entry(repo, concept_id)
    if concept_entry is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)

    ref = _concept_ref(concept_entry)
    filepath = _artifact_tree_path(repo, CONCEPT_FILE_FAMILY, ref)
    data = deepcopy(concept_entry.record.to_payload())

    # Warn if alias matches another concept's canonical_name
    for other_entry in load_concepts(_concepts_tree(repo)):
        if _concept_ref(other_entry) == ref:
            continue
        if other_entry.record.to_payload().get("canonical_name") == name:
            click.echo(
                f"WARNING: alias '{name}' matches canonical_name of "
                f"concept '{other_entry.record.artifact_id}'", err=True)

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
    document = _concept_document(repo, ref, data)
    repo.artifacts.save(
        CONCEPT_FILE_FAMILY,
        ref,
        document,
        message=f"Add alias '{name}' to {_concept_display_handle(data)}",
    )
    snapshot.sync_worktree()

    click.echo(f"Added alias '{name}' to {_concept_display_handle(data)} ({filepath.stem})")


# ── concept rename ───────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id")
@click.option("--name", required=True, help="New canonical name")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def rename(obj: dict, concept_id: str, name: str, dry_run: bool) -> None:
    """Rename a concept, cascading the new name through dependent CEL conditions.

    Updates canonical_name, filename, logical_ids, and artifact_id, then
    rewrites CEL condition expressions in every other concept and every
    claim file that references the old name. Re-validates concepts and
    claims before committing; aborts with a non-zero exit code if validation
    fails. The commit is a batch that adds the new file and deletes the old.
    """
    repo: Repository = obj["repo"]
    snapshot = _require_snapshot(repo)
    concept_entry = _find_concept_entry(repo, concept_id)
    if concept_entry is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)
    old_ref = _concept_ref(concept_entry)
    new_ref = ConceptFileRef(name)

    filepath = _artifact_tree_path(repo, CONCEPT_FILE_FAMILY, old_ref)
    data = deepcopy(concept_entry.record.to_payload())
    old_name = data.get("canonical_name", filepath.stem)
    new_path = _artifact_tree_path(repo, CONCEPT_FILE_FAMILY, new_ref)
    new_semantic_path = _artifact_knowledge_path(repo, CONCEPT_FILE_FAMILY, new_ref)
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
    updated_concepts: list[tuple[ConceptFileRef, ConceptFileRef, LoadedConcept]] = []
    changed_concept_refs: set[ConceptFileRef] = set()
    for concept_record in loaded_concepts:
        concept_ref = _concept_ref(concept_record)
        concept_data = deepcopy(concept_record.record.to_payload())
        local_handle = concept_record.filename
        updated_ref = concept_ref
        if concept_ref == old_ref:
            concept_data["canonical_name"] = name
            concept_data["last_modified"] = str(date.today())
            updated_ref = new_ref
            changed_concept_refs.add(concept_ref)
        if _rewrite_concept_conditions(concept_data, old_name, name):
            changed_concept_refs.add(concept_ref)
        concept_data = _normalize_concept_data(concept_data)
        concept_document = _concept_document(repo, updated_ref, concept_data)
        updated_concepts.append((
            concept_ref,
            updated_ref,
            LoadedConcept(
                filename=name if updated_ref == new_ref else concept_record.filename,
                source_path=_artifact_knowledge_path(repo, CONCEPT_FILE_FAMILY, updated_ref),
                knowledge_root=concept_record.knowledge_root,
                record=parse_concept_record_document(concept_document),
                document=concept_document,
            ),
        ))

    claims_root = repo.tree() / "claims"
    concept_validation = validate_concepts(
        [entry for _, _, entry in updated_concepts],
        claims_dir=claims_root if claims_root.exists() else None,
        forms_dir=repo.tree() / "forms",
    )
    if not concept_validation.ok:
        for e in concept_validation.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Rename validation failed. No changes written.", err=True)
        sys.exit(EXIT_VALIDATION)
    claim_files = load_claim_files(claims_root) if claims_root.exists() else []
    updated_claim_files: list[tuple[ClaimsFileRef, LoadedClaimsFile]] = []
    changed_claim_refs: set[ClaimsFileRef] = set()
    if claim_files:
        for claim_file in claim_files:
            claim_ref = _claims_ref(claim_file)
            claim_data = deepcopy(claim_file_payload(claim_file))
            if _rewrite_claim_conditions(claim_data, old_name, name):
                changed_claim_refs.add(claim_ref)
                claim_data, _ = normalize_claim_file_payload(claim_data)
            updated_claim_files.append((
                claim_ref,
                loaded_claim_file_from_payload(
                    filename=claim_file.filename,
                    source_path=_artifact_knowledge_path(repo, CLAIMS_FILE_FAMILY, claim_ref),
                    knowledge_root=claim_file.knowledge_root,
                    data=claim_data,
                ),
            ))
        compilation_context = build_compilation_context_from_loaded(
            [entry for _, _, entry in updated_concepts],
            forms_dir=repo.tree() / "forms",
            claim_files=[entry for _, entry in updated_claim_files],
        )
        claim_validation = validate_claims(
            [entry for _, entry in updated_claim_files],
            compilation_context,
        )
        if not claim_validation.ok:
            for e in claim_validation.errors:
                click.echo(f"ERROR: {e}", err=True)
            click.echo("Rename validation failed. No changes written.", err=True)
            sys.exit(EXIT_VALIDATION)

    with repo.artifacts.transact(message=f"Rename concept: {old_name} -> {name}") as transaction:
        for original_ref, updated_ref, updated_concept in updated_concepts:
            if original_ref == old_ref:
                transaction.move(
                    CONCEPT_FILE_FAMILY,
                    old_ref,
                    new_ref,
                    _concept_document(repo, updated_ref, updated_concept.record.to_payload()),
                )
                continue
            if original_ref in changed_concept_refs:
                transaction.save(
                    CONCEPT_FILE_FAMILY,
                    updated_ref,
                    _concept_document(repo, updated_ref, updated_concept.record.to_payload()),
                )

        for claim_ref, updated_claim_file in updated_claim_files:
            if claim_ref not in changed_claim_refs:
                continue
            transaction.save(
                CLAIMS_FILE_FAMILY,
                claim_ref,
                _claims_document(repo, claim_ref, claim_file_payload(updated_claim_file)),
            )
    snapshot.sync_worktree()

    click.echo(f"{old_name} -> {name}")
    click.echo(f"  {filepath} -> {new_path}")
    renamed_entry = next((entry for _, updated_ref, entry in updated_concepts if updated_ref == new_ref), None)
    click.echo(f"  Logical ID: {_concept_display_handle(renamed_entry.record.to_payload()) if renamed_entry is not None else name}")


# ── concept deprecate ────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id")
@click.option("--replaced-by", required=True, help="Replacement concept ID")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def deprecate(obj: dict, concept_id: str, replaced_by: str, dry_run: bool) -> None:
    """Deprecate a concept with a replacement."""
    repo: Repository = obj["repo"]
    snapshot = _require_snapshot(repo)
    concept_entry = _find_concept_entry(repo, concept_id)
    if concept_entry is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)
    ref = _concept_ref(concept_entry)
    filepath = _artifact_tree_path(repo, CONCEPT_FILE_FAMILY, ref)

    # Validate replacement target
    replacement_entry = _find_concept_entry(repo, replaced_by)
    if replacement_entry is None:
        click.echo(f"ERROR: Replacement concept '{replaced_by}' not found", err=True)
        sys.exit(EXIT_ERROR)

    replacement_data = replacement_entry.record.to_payload()
    if replacement_data.get("status") == "deprecated":
        click.echo(f"ERROR: Replacement concept '{replaced_by}' is itself deprecated", err=True)
        sys.exit(EXIT_ERROR)

    data = deepcopy(concept_entry.record.to_payload())

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
    repo.artifacts.save(
        CONCEPT_FILE_FAMILY,
        ref,
        _concept_document(repo, ref, data),
        message=f"Deprecate {_concept_display_handle(data)}, replaced by {_concept_display_handle(replacement_data)}",
    )
    snapshot.sync_worktree()

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
    snapshot = _require_snapshot(repo)
    concept_entry = _find_concept_entry(repo, source_id)
    if concept_entry is None:
        click.echo(f"ERROR: Source concept '{source_id}' not found", err=True)
        sys.exit(EXIT_ERROR)
    ref = _concept_ref(concept_entry)
    filepath = _artifact_tree_path(repo, CONCEPT_FILE_FAMILY, ref)

    target_entry = _find_concept_entry(repo, target_id)
    if target_entry is None:
        click.echo(f"ERROR: Target concept '{target_id}' not found", err=True)
        sys.exit(EXIT_ERROR)
    target_data = target_entry.record.to_payload()
    target_artifact_id = target_data.get("artifact_id")
    if not isinstance(target_artifact_id, str) or not target_artifact_id:
        raise click.ClickException(f"Target concept '{target_id}' does not have an artifact_id")

    data = deepcopy(concept_entry.record.to_payload())

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
    updated_document = _concept_document(repo, ref, data)

    concepts = load_concepts(repo.tree() / "concepts")
    updated_concepts = []
    for concept_record in concepts:
        concept_path = _artifact_tree_path(
            repo,
            CONCEPT_FILE_FAMILY,
            _concept_ref(concept_record),
        )
        updated_concepts.append(
            LoadedConcept(
                filename=concept_record.filename,
                source_path=_artifact_knowledge_path(
                    repo,
                    CONCEPT_FILE_FAMILY,
                    _concept_ref(concept_record),
                ),
                knowledge_root=concept_record.knowledge_root,
                record=parse_concept_record(
                    concept_document_to_record_payload(updated_document)
                    if concept_path == filepath
                    else concept_record.record.to_payload(),
                ),
                document=updated_document if concept_path == filepath else concept_record.document,
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

    repo.artifacts.save(
        CONCEPT_FILE_FAMILY,
        ref,
        updated_document,
        message=f"Link {_concept_display_handle(data)} {rel_type} {_concept_display_handle(target_data)}",
    )
    snapshot.sync_worktree()

    click.echo(f"Added {rel_type} -> {_concept_display_handle(target_data)} on {_concept_display_handle(data)} ({filepath.stem})")


def _apply_proto_role_entailment(
    bundle: dict[str, object],
    *,
    role_kind: str,
    entailment: dict[str, object],
) -> None:
    key = (
        "proto_agent_entailments"
        if role_kind == "agent"
        else "proto_patient_entailments"
    )
    entailments = bundle.get(key)
    if not isinstance(entailments, list):
        entailments = []
    entailments.append(entailment)
    bundle[key] = entailments


# ── concept qualia-add ───────────────────────────────────────────────

@concept.command("qualia-add")
@click.argument("concept_id")
@click.argument("role", type=click.Choice(QUALIA_ROLES))
@click.argument("target_concept")
@click.option("--type-constraint", default=None, help="Concept that the qualia target must satisfy")
@click.option("--asserter", required=True)
@click.option("--timestamp", required=True)
@click.option("--source-artifact-code", required=True)
@click.option("--method", required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def qualia_add(
    obj: dict,
    concept_id: str,
    role: str,
    target_concept: str,
    type_constraint: str | None,
    asserter: str,
    timestamp: str,
    source_artifact_code: str,
    method: str,
    dry_run: bool,
) -> None:
    """Add a provenance-bearing qualia reference to a concept sense."""
    repo: Repository = obj["repo"]
    snapshot = _require_snapshot(repo)
    concept_entry = _find_concept_entry(repo, concept_id)
    if concept_entry is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)
    ref = _concept_ref(concept_entry)
    data = _concept_artifact_payload(concept_entry)
    sense = _first_lexical_sense(data)

    qualia = sense.get("qualia")
    if not isinstance(qualia, dict):
        qualia = {}
    role_entries = qualia.get(role)
    if not isinstance(role_entries, list):
        role_entries = []
    entry: dict[str, object] = {
        "reference": _require_concept_reference(repo, target_concept, label="Target concept"),
        "provenance": _provenance_payload(
            asserter=asserter,
            timestamp=timestamp,
            source_artifact_code=source_artifact_code,
            method=method,
        ),
    }
    if type_constraint is not None:
        entry["type_constraint"] = {
            "reference": _require_concept_reference(
                repo,
                type_constraint,
                label="Type constraint",
            )
        }
    role_entries.append(entry)
    qualia[role] = role_entries
    sense["qualia"] = qualia
    data["last_modified"] = str(date.today())
    document = _canonical_concept_document(repo, ref, data)
    data = concept_document_to_record_payload(document)

    if dry_run:
        click.echo(repo.artifacts.render(document))
        return

    _validate_updated_concept(repo, concept_entry, document)
    repo.artifacts.save(
        CONCEPT_FILE_FAMILY,
        ref,
        document,
        message=f"Add {role} qualia to {_concept_display_handle(data)}",
    )
    snapshot.sync_worktree()
    click.echo(f"Added {role} qualia to {_concept_display_handle(data)}")


# ── concept description-kind ─────────────────────────────────────────

@concept.command("description-kind")
@click.argument("concept_id")
@click.option("--name", required=True)
@click.option("--reference", "reference_handle", required=True)
@click.option("--slot", "slots", multiple=True, help="Slot as name=type-concept")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def description_kind_cmd(
    obj: dict,
    concept_id: str,
    name: str,
    reference_handle: str,
    slots: tuple[str, ...],
    dry_run: bool,
) -> None:
    """Set the description-kind structure carried by a concept sense."""
    repo: Repository = obj["repo"]
    snapshot = _require_snapshot(repo)
    concept_entry = _find_concept_entry(repo, concept_id)
    if concept_entry is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)
    ref = _concept_ref(concept_entry)
    data = _concept_artifact_payload(concept_entry)
    sense = _first_lexical_sense(data)

    slot_payloads: list[dict[str, object]] = []
    for raw_slot in slots:
        slot_name, separator, type_handle = raw_slot.partition("=")
        if not separator or not slot_name or not type_handle:
            raise click.ClickException("--slot must use name=type-concept")
        slot_payloads.append(
            {
                "name": slot_name,
                "type_constraint": _require_concept_reference(
                    repo,
                    type_handle,
                    label=f"Slot '{slot_name}' type constraint",
                ),
            }
        )

    sense["description_kind"] = {
        "name": name,
        "reference": _require_concept_reference(repo, reference_handle, label="Description-kind reference"),
        "slots": slot_payloads,
    }
    data["last_modified"] = str(date.today())
    document = _canonical_concept_document(repo, ref, data)
    data = concept_document_to_record_payload(document)

    if dry_run:
        click.echo(repo.artifacts.render(document))
        return

    _validate_updated_concept(repo, concept_entry, document)
    repo.artifacts.save(
        CONCEPT_FILE_FAMILY,
        ref,
        document,
        message=f"Set description kind on {_concept_display_handle(data)}",
    )
    snapshot.sync_worktree()
    click.echo(f"Set description kind on {_concept_display_handle(data)}")


# ── concept proto-role ───────────────────────────────────────────────

@concept.command("proto-role")
@click.argument("concept_id")
@click.argument("role_name")
@click.argument("role_kind", type=click.Choice(PROTO_ROLE_KINDS))
@click.argument("property_name")
@click.argument("value", type=float)
@click.option("--asserter", required=True)
@click.option("--timestamp", required=True)
@click.option("--source-artifact-code", required=True)
@click.option("--method", required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def proto_role_cmd(
    obj: dict,
    concept_id: str,
    role_name: str,
    role_kind: str,
    property_name: str,
    value: float,
    asserter: str,
    timestamp: str,
    source_artifact_code: str,
    method: str,
    dry_run: bool,
) -> None:
    """Add a Dowty proto-role entailment to a named role."""
    repo: Repository = obj["repo"]
    snapshot = _require_snapshot(repo)
    concept_entry = _find_concept_entry(repo, concept_id)
    if concept_entry is None:
        click.echo(f"ERROR: Concept '{concept_id}' not found", err=True)
        sys.exit(EXIT_ERROR)
    ref = _concept_ref(concept_entry)
    data = _concept_artifact_payload(concept_entry)
    sense = _first_lexical_sense(data)

    entailment = {
        "property": property_name,
        "value": value,
        "provenance": _provenance_payload(
            asserter=asserter,
            timestamp=timestamp,
            source_artifact_code=source_artifact_code,
            method=method,
        ),
    }
    role_bundles = sense.get("role_bundles")
    if not isinstance(role_bundles, dict):
        role_bundles = {}
    bundle = role_bundles.get(role_name)
    if not isinstance(bundle, dict):
        bundle = {}
    _apply_proto_role_entailment(bundle, role_kind=role_kind, entailment=entailment)
    role_bundles[role_name] = bundle
    sense["role_bundles"] = role_bundles

    description_kind = sense.get("description_kind")
    if isinstance(description_kind, dict):
        slots = description_kind.get("slots")
        if isinstance(slots, list):
            for slot in slots:
                if not isinstance(slot, dict) or slot.get("name") != role_name:
                    continue
                slot_bundle = slot.get("proto_role_bundle")
                if not isinstance(slot_bundle, dict):
                    slot_bundle = {}
                _apply_proto_role_entailment(
                    slot_bundle,
                    role_kind=role_kind,
                    entailment=deepcopy(entailment),
                )
                slot["proto_role_bundle"] = slot_bundle
                break

    data["last_modified"] = str(date.today())
    document = _canonical_concept_document(repo, ref, data)
    data = concept_document_to_record_payload(document)

    if dry_run:
        click.echo(repo.artifacts.render(document))
        return

    _validate_updated_concept(repo, concept_entry, document)
    repo.artifacts.save(
        CONCEPT_FILE_FAMILY,
        ref,
        document,
        message=f"Add {role_kind} proto-role {property_name} to {_concept_display_handle(data)}",
    )
    snapshot.sync_worktree()
    click.echo(f"Added {role_kind} proto-role {property_name} to {_concept_display_handle(data)}")


# ── concept search ───────────────────────────────────────────────────

@concept.command()
@click.argument("query")
@click.pass_obj
def search(obj: dict, query: str) -> None:
    """Search concepts via the FTS5 index over canonical_name, aliases, definition, and CEL conditions."""
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
        d = c.record.to_payload()
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
    snapshot = _require_snapshot(repo)
    concept_entry = _find_concept_entry(repo, concept_name)
    if concept_entry is None:
        click.echo(f"ERROR: Concept '{concept_name}' not found", err=True)
        sys.exit(EXIT_ERROR)
    ref = _concept_ref(concept_entry)
    filepath = _artifact_tree_path(repo, CONCEPT_FILE_FAMILY, ref)

    data = deepcopy(concept_entry.record.to_payload())

    if data.get("form") != "category":
        click.echo(f"ERROR: '{concept_name}' is not a category concept (form={data.get('form')})", err=True)
        sys.exit(EXIT_ERROR)

    raw_form_parameters = data.get("form_parameters")
    if raw_form_parameters is None:
        fp = {}
    elif isinstance(raw_form_parameters, dict):
        fp = raw_form_parameters
    else:
        click.echo(f"ERROR: '{concept_name}' form_parameters must be a mapping", err=True)
        sys.exit(EXIT_ERROR)
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
    repo.artifacts.save(
        CONCEPT_FILE_FAMILY,
        ref,
        _concept_document(repo, ref, data),
        message=f"Add value '{value}' to {concept_name}",
    )
    snapshot.sync_worktree()
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
        data = c.record.to_payload()
        if data.get("form") != "category":
            continue
        raw_form_parameters = data.get("form_parameters")
        if raw_form_parameters is None:
            fp = {}
        elif isinstance(raw_form_parameters, dict):
            fp = raw_form_parameters
        else:
            click.echo(
                f"ERROR: '{data.get('canonical_name')}' form_parameters must be a mapping",
                err=True,
            )
            sys.exit(EXIT_ERROR)
        values = fp.get("values", [])
        extensible = fp.get("extensible", True)
        cat_data[data["canonical_name"]] = {
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
        click.echo(repo.artifacts.render(artifact))
        return
    concept_entry = _find_concept_entry(repo, concept_id_or_name)
    if concept_entry is None:
        click.echo(f"ERROR: Concept '{concept_id_or_name}' not found", err=True)
        sys.exit(EXIT_ERROR)
    ref = _concept_ref(concept_entry)
    click.echo(repo.artifacts.render(_concept_document(repo, ref, concept_entry.record.to_payload())))


@concept.command("align")
@click.option("--sources", "first_source", required=True)
@click.argument("extra_sources", nargs=-1)
@click.pass_obj
def align_cmd(obj: dict, first_source: str, extra_sources: tuple[str, ...]) -> None:
    """Build and persist a concept-alignment artifact from source branches."""
    repo: Repository = obj["repo"]
    artifact = align_sources(repo, [first_source, *extra_sources])
    click.echo(f"Created {artifact.id}")


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

    if operator is not None:
        scores = artifact.queries.operator_scores.get(operator, {})
        for argument_id, score in sorted(scores.items()):
            click.echo(f"{argument_id}\t{score}")
        return

    accepted = (
        artifact.queries.skeptical_acceptance
        if mode == "skeptical"
        else artifact.queries.credulous_acceptance
    )
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
    click.echo(f"Updated {updated.id}")


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
    click.echo(f"Promoted {updated.id}")


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
