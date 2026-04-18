from __future__ import annotations

from copy import deepcopy
import sys
from datetime import date
from pathlib import Path

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
from propstore.concept_ids import next_concept_id
from propstore.repository import Repository
from propstore.core.concepts import load_concepts
from propstore.validate_concepts import validate_concepts
from propstore.compiler.passes import validate_claims
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
    _concepts_tree,
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


@concept.command()
@click.argument("query")
@click.pass_obj
def search(obj: dict, query: str) -> None:
    """Search concepts via the FTS5 index over canonical_name, aliases, definition, and CEL conditions."""
    from propstore.concepts import (
        ConceptSearchRequest,
        ConceptSidecarMissingError,
        search_concepts,
    )

    try:
        report = search_concepts(
            obj["repo"],
            ConceptSearchRequest(query=query),
        )
    except ConceptSidecarMissingError as exc:
        raise click.ClickException(
            "concept search requires a built sidecar; run 'pks build' first"
        ) from exc

    if report.hits:
        for hit in report.hits:
            snippet = hit.definition[:80]
            click.echo(f"  {hit.logical_id}  {hit.canonical_name}  — {snippet}")
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
