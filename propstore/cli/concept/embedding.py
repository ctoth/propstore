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
)
from propstore.artifacts.documents.claims import ClaimsFileDocument
from propstore.artifacts.documents.concepts import ConceptDocument
from propstore.identity import (
    normalize_canonical_concept_payload,
    normalize_claim_file_payload,
)
from propstore.families.registry import ClaimsFileRef, ConceptFileRef
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
from propstore.repository import Repository
from propstore.validate_concepts import validate_concepts
from propstore.compiler.passes import validate_claims
from propstore.cli.concept import (
    PROTO_ROLE_KINDS,
    QUALIA_ROLES,
    RELATIONSHIP_TYPES,
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


# ── concept embed ────────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id", required=False, default=None)
@click.option("--all", "embed_all", is_flag=True, help="Embed all concepts")
@click.option("--model", required=True, help="litellm model string, or 'all'")
@click.option("--batch-size", default=64, type=int, help="Concepts per API call")
@click.pass_obj
def embed(obj: dict, concept_id: str | None, embed_all: bool, model: str, batch_size: int) -> None:
    """Generate embeddings for concepts via litellm."""
    from propstore.concepts import (
        ConceptEmbedRequest,
        ConceptEmbeddingModelError,
        ConceptSidecarMissingError,
        ConceptWorkflowError,
        UnknownConceptError,
        embed_concept_embeddings,
    )

    def progress(model_name: str, done: int, total: int) -> None:
        if model == "all":
            if done % batch_size == 0:
                click.echo(f"  {done}/{total}", nl=False)
            return
        click.echo(f"  {done}/{total} concepts embedded", err=True)

    try:
        report = embed_concept_embeddings(
            obj["repo"],
            ConceptEmbedRequest(
                concept_id=concept_id,
                embed_all=embed_all,
                model=model,
                batch_size=batch_size,
            ),
            on_progress=progress,
        )
    except ConceptSidecarMissingError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    except (ConceptEmbeddingModelError, ConceptWorkflowError, UnknownConceptError) as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if model == "all":
        for result in report.results:
            click.echo(f"Embedding with {result.model_name}...")
            click.echo(
                f"  embedded={result.embedded} "
                f"skipped={result.skipped} "
                f"errors={result.errors}"
            )
        return

    result = report.results[0]
    click.echo(
        f"Embedded: {result.embedded}, "
        f"Skipped: {result.skipped}, "
        f"Errors: {result.errors}"
    )


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
    from propstore.concepts import (
        ConceptEmbeddingModelError,
        ConceptSidecarMissingError,
        ConceptSimilarRequest,
        ConceptWorkflowError,
        UnknownConceptError,
        find_similar_concepts,
    )

    try:
        report = find_similar_concepts(
            obj["repo"],
            ConceptSimilarRequest(
                concept_id=concept_id,
                model=model,
                top_k=top_k,
                agree=agree,
                disagree=disagree,
            ),
        )
    except ConceptSidecarMissingError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    except (ConceptEmbeddingModelError, ConceptWorkflowError, UnknownConceptError) as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if not report.hits:
        click.echo("No similar concepts found.")
        return

    for hit in report.hits:
        definition = hit.definition[:80]
        click.echo(
            f"  {hit.distance:.4f}  "
            f"{hit.concept_id}  "
            f"{hit.canonical_name}  — {definition}"
        )
