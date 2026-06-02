from __future__ import annotations

from pathlib import Path

import click

from propstore.app.claims import (
    ClaimConflictsRequest,
    ClaimPathError,
    ClaimValidationDocumentError,
    ClaimValidationRequest,
    detect_claim_conflicts,
    validate_claims,
)
from propstore.cli.claim import claim
from propstore.cli.helpers import EXIT_VALIDATION, exit_with_code, fail
from propstore.cli.output import emit, emit_error, emit_success, emit_warning
from propstore.repository import Repository


@claim.command()
@click.option("--dir", "claims_path", default=None, help="Claims directory")
@click.option(
    "--concepts-dir", "concepts_path", default=None, help="Concepts directory"
)
@click.pass_obj
def validate(obj: dict, claims_path: str | None, concepts_path: str | None) -> None:
    """Validate all claim files."""
    repo: Repository = obj["repo"]
    try:
        report = validate_claims(
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
        return
    if report.file_count == 0:
        emit("No claims found.")
        return

    for warning in report.warnings:
        emit_warning(f"WARNING: {warning}")
    for error in report.errors:
        emit_error(f"ERROR: {error}")

    if report.ok:
        emit_success(
            f"Validation passed: {report.file_count} claim(s), "
            f"{len(report.warnings)} warning(s)"
        )
        return

    emit_error(f"Validation FAILED: {len(report.errors)} error(s)")
    exit_with_code(EXIT_VALIDATION)


@claim.command()
@click.option("--concept", default=None, help="Filter by concept ID")
@click.option(
    "--class",
    "warning_class",
    default=None,
    type=click.Choice(["CONFLICT", "OVERLAP", "PARAM_CONFLICT"]),
    help="Filter by warning class",
)
@click.pass_obj
def conflicts(obj: dict, concept: str | None, warning_class: str | None) -> None:
    """Detect and report claim conflicts."""
    repo: Repository = obj["repo"]
    report = detect_claim_conflicts(
        repo,
        ClaimConflictsRequest(concept=concept, warning_class=warning_class),
    )
    if report.file_count == 0:
        emit("No claims found.")
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
