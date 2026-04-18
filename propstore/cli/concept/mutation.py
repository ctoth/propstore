from __future__ import annotations

from copy import deepcopy
import sys
from datetime import date
from pathlib import Path

import click

from propstore.claims import (
    ClaimFileEntry,
    claim_file_payload,
    claim_file_filename,
    loaded_claim_file_from_payload,
)
from propstore.artifacts.documents.claims import ClaimsFileDocument
from propstore.artifacts.documents.concepts import ConceptDocument
from propstore.artifacts.families import CLAIMS_FILE_FAMILY, CONCEPT_FILE_FAMILY, FORM_FAMILY
from propstore.artifacts.identity import (
    normalize_canonical_concept_payload,
    normalize_claim_file_payload,
)
from propstore.artifacts.refs import ClaimsFileRef, ConceptFileRef
from propstore.source import (
    align_sources,
    decide_alignment,
    load_alignment_artifact,
    promote_alignment,
)
from propstore.cli.helpers import EXIT_ERROR, EXIT_VALIDATION
from propstore.identity import format_logical_id, primary_logical_id
from propstore.core.concepts import (
    LoadedConcept,
    concept_document_to_payload,
    concept_document_to_record_payload,
    parse_concept_record,
    parse_concept_record_document,
)
from propstore.compiler.context import build_compilation_context_from_loaded
from propstore.compiler.references import build_claim_reference_lookup
from propstore.concept_ids import next_concept_id_for_repo, record_concept_id_for_repo
from propstore.repository import Repository
from propstore.validate_concepts import validate_concepts
from propstore.compiler.passes import validate_claims
from propstore.form_utils import parse_form
from propstore.cli.concept import (
    PROTO_ROLE_KINDS,
    QUALIA_ROLES,
    RELATIONSHIP_TYPES,
    _artifact_knowledge_path,
    _artifact_source,
    _artifact_tree_path,
    _canonical_concept_document,
    _claims_document,
    _claims_ref,
    _concept_artifact_payload,
    _concept_display_handle,
    _concept_document,
    _concept_ref,
    _find_concept_entry,
    _first_lexical_sense,
    _normalize_concept_data,
    _provenance_payload,
    _require_concept_artifact_id,
    _require_concept_reference,
    _require_snapshot,
    _rewrite_claim_conditions,
    _rewrite_concept_conditions,
    _validate_updated_concept,
    concept,
)


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
        available = sorted(form_ref.name for form_ref in repo.families.forms.list())
        if available:
            click.echo(f"Available forms: {', '.join(available)}")
        form_name = click.prompt("Form")

    ref = ConceptFileRef(name)
    filepath = _artifact_tree_path(repo, CONCEPT_FILE_FAMILY, ref)
    semantic_path = _artifact_knowledge_path(repo, CONCEPT_FILE_FAMILY, ref)
    if semantic_path.exists():
        click.echo(f"ERROR: Concept file '{filepath}' already exists", err=True)
        sys.exit(EXIT_ERROR)

    numeric_concept_id = next_concept_id_for_repo(repo)
    cid = f"concept{numeric_concept_id}"

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
        click.echo(repo.families.concepts.render(document))
        return

    tree = repo.tree()
    concepts: list[LoadedConcept] = []
    for existing_ref in repo.families.concepts.list():
        handle = repo.families.concepts.require_handle(existing_ref)
        concepts.append(
            LoadedConcept(
                filename=existing_ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_concept_record_document(handle.document),
                document=handle.document,
            )
        )
    concepts.append(
        LoadedConcept(
            filename=name,
            source_path=semantic_path,
            knowledge_root=tree,
            record=parse_concept_record_document(document),
            document=document,
        )
    )

    form_registry = {
        document.name: parse_form(document.name, document)
        for form_ref in repo.families.forms.list()
        for document in (repo.families.forms.require(form_ref),)
    }
    result = validate_concepts(concepts, form_registry=form_registry)
    if not result.ok:
        for e in result.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Validation failed. No changes written.", err=True)
        sys.exit(EXIT_VALIDATION)

    for w in result.warnings:
        click.echo(f"WARNING: {w}", err=True)

    repo.families.concepts.save(
        ref,
        document,
        message=f"Add concept: {name} ({_concept_display_handle(concept_document_to_record_payload(document))})",
    )
    record_concept_id_for_repo(repo, numeric_concept_id)
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
    tree = repo.tree()
    for other_ref in repo.families.concepts.list():
        if other_ref == ref:
            continue
        other_document = repo.families.concepts.require(other_ref)
        other_entry = LoadedConcept(
            filename=other_ref.name,
            source_path=tree / repo.families.concepts.address(other_ref).require_path(),
            knowledge_root=tree,
            record=parse_concept_record_document(other_document),
            document=other_document,
        )
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
    repo.families.concepts.save(
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

    tree = repo.tree()
    loaded_concepts: list[LoadedConcept] = []
    for loaded_ref in repo.families.concepts.list():
        handle = repo.families.concepts.require_handle(loaded_ref)
        loaded_concepts.append(
            LoadedConcept(
                filename=loaded_ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_concept_record_document(handle.document),
                document=handle.document,
            )
        )
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

    claim_files = [
        repo.families.claims.require_handle(claim_ref)
        for claim_ref in repo.families.claims.list()
    ]
    concept_validation = validate_concepts(
        [entry for _, _, entry in updated_concepts],
        form_registry={
            document.name: parse_form(document.name, document)
            for form_ref in repo.families.forms.list()
            for document in (repo.families.forms.require(form_ref),)
        },
        claim_reference_lookup=build_claim_reference_lookup(claim_files),
    )
    if not concept_validation.ok:
        for e in concept_validation.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Rename validation failed. No changes written.", err=True)
        sys.exit(EXIT_VALIDATION)
    updated_claim_files: list[tuple[ClaimsFileRef, ClaimFileEntry]] = []
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
                    filename=claim_file_filename(claim_file),
                    source_path=_artifact_knowledge_path(repo, CLAIMS_FILE_FAMILY, claim_ref),
                    knowledge_root=repo.tree(),
                    data=claim_data,
                ),
            ))
        compilation_context = build_compilation_context_from_loaded(
            [entry for _, _, entry in updated_concepts],
            form_registry={
                document.name: parse_form(document.name, document)
                for form_ref in repo.families.forms.list()
                for document in (repo.families.forms.require(form_ref),)
            },
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

    with repo.families.transact(message=f"Rename concept: {old_name} -> {name}") as transaction:
        for original_ref, updated_ref, updated_concept in updated_concepts:
            if original_ref == old_ref:
                transaction.concepts.move(
                    old_ref,
                    new_ref,
                    _concept_document(repo, updated_ref, updated_concept.record.to_payload()),
                )
                continue
            if original_ref in changed_concept_refs:
                transaction.concepts.save(
                    updated_ref,
                    _concept_document(repo, updated_ref, updated_concept.record.to_payload()),
                )

        for claim_ref, updated_claim_file in updated_claim_files:
            if claim_ref not in changed_claim_refs:
                continue
            transaction.claims.save(
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
    repo.families.concepts.save(
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

    tree = repo.tree()
    concepts: list[LoadedConcept] = []
    for loaded_ref in repo.families.concepts.list():
        handle = repo.families.concepts.require_handle(loaded_ref)
        concepts.append(
            LoadedConcept(
                filename=loaded_ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_concept_record_document(handle.document),
                document=handle.document,
            )
        )
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
        form_registry={
            document.name: parse_form(document.name, document)
            for form_ref in repo.families.forms.list()
            for document in (repo.families.forms.require(form_ref),)
        },
        claim_reference_lookup=build_claim_reference_lookup([
            repo.families.claims.require_handle(claim_ref)
            for claim_ref in repo.families.claims.list()
        ]),
    )
    if not validation.ok:
        for e in validation.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Validation failed. No changes written.", err=True)
        sys.exit(EXIT_VALIDATION)

    for w in validation.warnings:
        click.echo(f"WARNING: {w}", err=True)

    repo.families.concepts.save(
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
        click.echo(repo.families.concepts.render(document))
        return

    _validate_updated_concept(repo, concept_entry, document)
    repo.families.concepts.save(
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
        click.echo(repo.families.concepts.render(document))
        return

    _validate_updated_concept(repo, concept_entry, document)
    repo.families.concepts.save(
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
        click.echo(repo.families.concepts.render(document))
        return

    _validate_updated_concept(repo, concept_entry, document)
    repo.families.concepts.save(
        ref,
        document,
        message=f"Add {role_kind} proto-role {property_name} to {_concept_display_handle(data)}",
    )
    snapshot.sync_worktree()
    click.echo(f"Added {role_kind} proto-role {property_name} to {_concept_display_handle(data)}")


# ── concept search ───────────────────────────────────────────────────


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
    repo.families.concepts.save(
        ref,
        _concept_document(repo, ref, data),
        message=f"Add value '{value}' to {concept_name}",
    )
    snapshot.sync_worktree()
    click.echo(f"Added '{value}' to {concept_name} — values: {', '.join(values)}")


# ── concept categories ───────────────────────────────────────────────
