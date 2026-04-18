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
