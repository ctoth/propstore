"""pks concept — subcommands for managing concepts."""
from __future__ import annotations

from copy import deepcopy
import sys
from datetime import date
from pathlib import Path
from typing import TypeVar

import click

from quire.artifacts import ArtifactFamily
from quire.tree_path import TreePath as KnowledgePath
from propstore.claims import (
    ClaimFileEntry,
    claim_file_filename,
    claim_file_payload,
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
from propstore.repository import Repository
from propstore.storage.snapshot import RepositorySnapshot
from propstore.validate_concepts import validate_concepts
from propstore.compiler.passes import validate_claims
from propstore.form_utils import parse_form

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


def _artifact_source(repo: Repository, family: ArtifactFamily[Repository, TRef, TDoc], ref: TRef) -> str:
    return repo.artifacts.address(family, ref).require_path()


def _artifact_tree_path(repo: Repository, family: ArtifactFamily[Repository, TRef, TDoc], ref: TRef) -> Path:
    return repo.root / Path(_artifact_source(repo, family, ref))


def _artifact_knowledge_path(repo: Repository, family: ArtifactFamily[Repository, TRef, TDoc], ref: TRef) -> KnowledgePath:
    return repo.tree() / _artifact_source(repo, family, ref)


def _concept_ref(concept_entry: LoadedConcept) -> ConceptFileRef:
    return ConceptFileRef(concept_entry.filename)


def _claims_ref(claim_file: ClaimFileEntry) -> ClaimsFileRef:
    return ClaimsFileRef(claim_file_filename(claim_file))


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
    tree = repo.tree()
    for ref in repo.artifacts.list(CONCEPT_FILE_FAMILY):
        handle = repo.artifacts.require_handle(CONCEPT_FILE_FAMILY, ref)
        concept = LoadedConcept(
            filename=ref.name,
            source_path=tree / handle.address.require_path(),
            knowledge_root=tree,
            record=parse_concept_record_document(handle.document),
            document=handle.document,
        )
        if ref.name == id_or_name:
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
    tree = repo.tree()
    for loaded_ref in repo.artifacts.list(CONCEPT_FILE_FAMILY):
        handle = repo.artifacts.require_handle(CONCEPT_FILE_FAMILY, loaded_ref)
        if loaded_ref == ref:
            concepts.append(
                LoadedConcept(
                    filename=loaded_ref.name,
                    source_path=_artifact_knowledge_path(repo, CONCEPT_FILE_FAMILY, ref),
                    knowledge_root=tree,
                    record=parse_concept_record_document(document),
                    document=document,
                )
            )
            continue
        concepts.append(
            LoadedConcept(
                filename=loaded_ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_concept_record_document(handle.document),
                document=handle.document,
            )
        )

    from propstore.compiler.references import build_claim_reference_lookup

    claim_files = [
        repo.artifacts.require_handle(CLAIMS_FILE_FAMILY, claim_ref)
        for claim_ref in repo.artifacts.list(CLAIMS_FILE_FAMILY)
    ]
    form_registry = {
        document.name: parse_form(document.name, document)
        for form_ref in repo.artifacts.list(FORM_FAMILY)
        for document in (repo.artifacts.require(FORM_FAMILY, form_ref),)
    }
    validation = validate_concepts(
        concepts,
        form_registry=form_registry,
        claim_reference_lookup=build_claim_reference_lookup(claim_files),
    )
    if not validation.ok:
        for e in validation.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Validation failed. No changes written.", err=True)
        sys.exit(EXIT_VALIDATION)
    for w in validation.warnings:
        click.echo(f"WARNING: {w}", err=True)


# Import split command modules after the group and shared helpers are defined.
from propstore.cli.concept import alignment as _alignment
from propstore.cli.concept import display as _display
from propstore.cli.concept import embedding as _embedding
from propstore.cli.concept import mutation as _mutation
