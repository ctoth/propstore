"""pks claim — subcommands for inspecting, validating, and relating claims.

Exposes show (display a single claim), validate / validate-file
(CEL type-checking over one or many claim files), conflicts (detect
parameter conflicts), compare (algorithm claim equivalence), embed
(litellm embeddings), similar (embedding nearest-neighbour search),
and relate (LLM-assisted epistemic relationship classification)."""
from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.output import emit, emit_error, emit_success, emit_warning

from propstore.app.claims import (
    ClaimCompareRequest,
    ClaimComparisonError,
    ClaimConflictsRequest,
    ClaimEmbedRequest,
    ClaimEmbeddingModelError,
    ClaimPathError,
    ClaimRelateRequest,
    ClaimSidecarMissingError,
    ClaimSimilarRequest,
    ClaimValidateFileRequest,
    ClaimValidationDocumentError,
    ClaimValidationRequest,
    ClaimWorkflowError,
    UnknownClaimError,
    compare_algorithm_claims_from_repo,
    detect_claim_conflicts,
    embed_claim_embeddings,
    find_similar_claims,
    relate_claims,
    show_claim_from_repo,
    validate_claim_file,
    validate_claim_files,
)
from propstore.cli.helpers import EXIT_VALIDATION, exit_with_code, fail
from propstore.repository import Repository


@click.group()
def claim() -> None:
    """Manage and validate claims."""


@claim.command("show")
@click.argument("claim_id")
@click.pass_obj
def show(obj: dict, claim_id: str) -> None:
    """Display details of a single claim."""
    repo: Repository = obj["repo"]
    try:
        report = show_claim_from_repo(repo, claim_id)
    except ClaimSidecarMissingError as exc:
        fail(exc)
    except UnknownClaimError:
        fail(f"Claim '{claim_id}' not found.")

    if report.logical_id:
        emit(f"Logical ID: {report.logical_id}")
    emit(f"Artifact ID: {report.artifact_id}")
    if report.version_id:
        emit(f"Version ID: {report.version_id}")
    if report.concept_id:
        emit(f"  concept: {report.concept_id}")
    if report.claim_type:
        emit(f"  type: {report.claim_type}")
    if report.value is not None:
        emit(f"  value: {report.value} {report.unit}".rstrip())
        if report.value_si is not None and report.value_si != report.value:
            si_label = f"{report.value_si} {report.canonical_unit}".rstrip()
            emit(f"  value (SI): {si_label}")
    if report.lower_bound is not None:
        si_part = (
            f" -> {report.lower_bound_si}"
            if report.lower_bound_si is not None
            and report.lower_bound_si != report.lower_bound
            else ""
        )
        emit(f"  lower_bound: {report.lower_bound}{si_part}")
    if report.upper_bound is not None:
        si_part = (
            f" -> {report.upper_bound_si}"
            if report.upper_bound_si is not None
            and report.upper_bound_si != report.upper_bound
            else ""
        )
        emit(f"  upper_bound: {report.upper_bound}{si_part}")
    if report.uncertainty is not None:
        emit(f"  uncertainty: {report.uncertainty}")
    if report.sample_size is not None:
        emit(f"  sample_size: {report.sample_size}")
    if report.source_paper:
        emit(f"  source: {report.source_paper}")
    if report.conditions_cel:
        emit(f"  conditions: {report.conditions_cel}")


@claim.command()
@click.option("--dir", "claims_path", default=None, help="Claims directory")
@click.option("--concepts-dir", "concepts_path", default=None, help="Concepts directory")
@click.pass_obj
def validate(obj: dict, claims_path: str | None, concepts_path: str | None) -> None:
    """Validate all claim files."""
    repo: Repository = obj["repo"]
    try:
        report = validate_claim_files(
            repo,
            ClaimValidationRequest(
                claims_path=None if claims_path is None else Path(claims_path),
                concepts_path=None if concepts_path is None else Path(concepts_path),
            ),
        )
    except ClaimPathError as exc:
        fail(exc)
    except ClaimValidationDocumentError as exc:
        emit_error(f"ERROR: {exc}")
        emit_error("Validation FAILED: 1 error(s)")
        exit_with_code(EXIT_VALIDATION)
    if report.file_count == 0:
        emit("No claim files found.")
        return

    for warning in report.warnings:
        emit_warning(f"WARNING: {warning}")
    for error in report.errors:
        emit_error(f"ERROR: {error}")

    if report.ok:
        emit_success(
            f"Validation passed: {report.file_count} claim file(s), "
            f"{len(report.warnings)} warning(s)"
        )
    else:
        emit_error(f"Validation FAILED: {len(report.errors)} error(s)")
        exit_with_code(EXIT_VALIDATION)


@claim.command("validate-file")
@click.argument("filepath", type=click.Path(exists=True, path_type=Path))
@click.option("--concepts-dir", "concepts_path", default=None, help="Concepts directory")
@click.pass_obj
def validate_file(obj: dict, filepath: Path, concepts_path: str | None) -> None:
    """Validate a single claims YAML file."""
    repo: Repository = obj["repo"]
    try:
        report = validate_claim_file(
            repo,
            ClaimValidateFileRequest(
                filepath=filepath,
                concepts_path=None if concepts_path is None else Path(concepts_path),
            ),
        )
    except ClaimPathError as exc:
        fail(exc)
    except ClaimValidationDocumentError as exc:
        emit_error(f"ERROR: {exc}")
        emit_error(f"FAILED: {filepath.name} (1 error(s))")
        exit_with_code(EXIT_VALIDATION)

    for warning in report.warnings:
        emit_warning(f"WARNING: {warning}")
    for error in report.errors:
        emit_error(f"ERROR: {error}")

    if report.ok:
        emit_success(f"Valid: {filepath.name} ({len(report.warnings)} warning(s))")
    else:
        emit_error(f"FAILED: {filepath.name} ({len(report.errors)} error(s))")
        exit_with_code(EXIT_VALIDATION)


@claim.command()
@click.option("--concept", default=None, help="Filter by concept ID")
@click.option("--class", "warning_class", default=None,
              type=click.Choice(["CONFLICT", "OVERLAP", "PARAM_CONFLICT"]),
              help="Filter by warning class")
@click.pass_obj
def conflicts(obj: dict, concept: str | None, warning_class: str | None) -> None:
    """Detect and report claim conflicts."""
    repo: Repository = obj["repo"]
    report = detect_claim_conflicts(
        repo,
        ClaimConflictsRequest(concept=concept, warning_class=warning_class),
    )
    if report.file_count == 0:
        emit("No claim files found.")
        return

    if not report.conflicts:
        emit("No conflicts found.")
        return

    for conflict in report.conflicts:
        emit(
            f"  {conflict.warning_class:16s} concept={conflict.concept_id} "
            f"{conflict.claim_a_id} vs {conflict.claim_b_id}  "
            f"({conflict.value_a} vs {conflict.value_b})"
        )
        if conflict.derivation_chain:
            emit(f"    chain: {conflict.derivation_chain}")

    emit(f"\n{len(report.conflicts)} conflict(s) found.")


@claim.command()
@click.argument("id_a")
@click.argument("id_b")
@click.option("--bindings", "-b", multiple=True, help="Known values as key=value pairs")
@click.pass_obj
def compare(obj: dict, id_a: str, id_b: str, bindings: tuple[str, ...]) -> None:
    """Compare two algorithm claims for equivalence."""
    repo: Repository = obj["repo"]

    known_values: dict[str, float] | None = None
    if bindings:
        known_values = {}
        for b in bindings:
            key, _, value = b.partition("=")
            try:
                known_values[key] = float(value)
            except ValueError:
                emit_warning(f"WARNING: Ignoring non-numeric binding: {b}")

    try:
        result = compare_algorithm_claims_from_repo(
            repo,
            ClaimCompareRequest(id_a, id_b, known_values or None),
        )
    except ClaimSidecarMissingError as exc:
        fail(exc)
    except UnknownClaimError as exc:
        fail(f"Claim '{exc.claim_id}' not found.")
    except ClaimComparisonError as exc:
        fail(exc)

    emit(f"Tier:       {result.tier}")
    emit(f"Equivalent: {result.equivalent}")
    emit(f"Similarity: {result.similarity:.4f}")
    if result.details:
        emit(f"Details:    {result.details}")


@claim.command()
@click.argument("claim_id", required=False, default=None)
@click.option("--all", "embed_all", is_flag=True, help="Embed all claims")
@click.option("--model", required=True, help="litellm model string, or 'all' for every registered model")
@click.option("--batch-size", default=64, type=int, help="Claims per API call")
@click.pass_obj
def embed(obj: dict, claim_id: str | None, embed_all: bool, model: str, batch_size: int) -> None:
    """Generate embeddings for claims via litellm."""
    repo = obj["repo"]
    try:
        report = embed_claim_embeddings(
            repo,
            ClaimEmbedRequest(
                claim_id=claim_id,
                embed_all=embed_all,
                model=model,
                batch_size=batch_size,
            ),
            on_progress=(
                (lambda model_name, done, total: emit(f"  {done}/{total}") if done % batch_size == 0 or done == total else None)
                if model == "all"
                else (lambda model_name, done, total: emit(f"  {done}/{total} claims embedded", err=True))
            ),
        )
    except ClaimSidecarMissingError as exc:
        fail(exc)
    except ClaimEmbeddingModelError as exc:
        fail(exc)
    except ClaimWorkflowError as exc:
        fail(exc)

    if model == "all":
        for result in report.results:
            emit(f"Embedding with {result.model_name}...")
            emit(f"  embedded={result.embedded} skipped={result.skipped} errors={result.errors}")
    else:
        result = report.results[0]
        emit(f"Embedded: {result.embedded}, Skipped: {result.skipped}, Errors: {result.errors}")


@claim.command()
@click.argument("claim_id")
@click.option("--model", default=None, help="litellm model string (default: first available)")
@click.option("--top-k", default=10, type=int, help="Number of results")
@click.option("--agree", is_flag=True, help="Similar under ALL stored models")
@click.option("--disagree", is_flag=True, help="Similar under some models but not others")
@click.pass_obj
def similar(obj: dict, claim_id: str, model: str | None, top_k: int, agree: bool, disagree: bool) -> None:
    """Find similar claims by embedding distance."""
    repo = obj["repo"]
    try:
        report = find_similar_claims(
            repo,
            ClaimSimilarRequest(
                claim_id=claim_id,
                model=model,
                top_k=top_k,
                agree=agree,
                disagree=disagree,
            ),
        )
    except ClaimSidecarMissingError as exc:
        fail(exc)
    except (ClaimEmbeddingModelError, ClaimWorkflowError) as exc:
        fail(exc)

    if not report.hits:
        emit("No similar claims found.")
        return

    for hit in report.hits:
        emit(f"  {hit.distance:.4f}  {hit.claim_id}  [{hit.source_paper}]  {hit.summary[:120]}")


@claim.command()
@click.argument("claim_id", required=False, default=None)
@click.option("--all", "relate_all_flag", is_flag=True, help="Relate all claims")
@click.option("--model", required=True, help="LLM model for classification")
@click.option("--embedding-model", default=None, help="Embedding model for similarity")
@click.option("--top-k", default=5, type=int, help="Number of similar claims to classify")
@click.option("--concurrency", default=20, type=int, help="Max concurrent LLM calls")
@click.pass_obj
def relate(obj, claim_id, relate_all_flag, model, embedding_model, top_k, concurrency):
    """Classify epistemic relationships between similar claims via LLM.

    Uses embedding similarity to pick top-k candidates per claim, then calls
    the LLM to label each (support / rebut / refine / etc.) and commits the
    classifications as stance proposal files to the stance proposal placement branch.
    The main branch is not mutated; promote proposals into source-of-truth
    storage with ``pks promote``."""
    repo = obj["repo"]
    try:
        report = relate_claims(
            repo,
            ClaimRelateRequest(
                claim_id=claim_id,
                relate_all=relate_all_flag,
                model=model,
                embedding_model=embedding_model,
                top_k=top_k,
                concurrency=concurrency,
            ),
            on_progress=lambda done, total: (
                emit(f"  {done}/{total} claims processed", err=True)
                if done % 10 == 0 or done == total
                else None
            ),
        )
    except ClaimSidecarMissingError as exc:
        fail(exc)
    except ClaimWorkflowError as exc:
        fail(exc)

    if claim_id and not relate_all_flag:
        if report.stances:
            for stance in report.stances:
                emit(
                    f"  {str(stance['type']):12s} "
                    f"{str(stance.get('strength', '')):8s} "
                    f"-> {stance['target']}  {stance.get('note', '')}"
                )
            assert report.commit_sha is not None
            emit(
                f"\nCommitted {len(report.relpaths)} proposal file(s) to "
                f"{report.branch} at {report.commit_sha[:8]}"
            )
        else:
            emit("No epistemic relationships found.")
        return

    if relate_all_flag:
        if report.commit_sha is not None:
            emit(
                f"Proposal commit: {report.commit_sha[:8]} on {report.branch} "
                f"({len(report.relpaths)} file(s))"
            )
        emit(
            f"\nProcessed: {report.claims_processed}, "
            f"Stances found: {report.stances_found}, "
            f"No relation: {report.no_relation}"
        )
        return

    fail("provide a claim ID or use --all")
