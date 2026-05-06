"""Compiler-facing CLI commands.

Exposes top-level commands for validation, sidecar builds, raw sidecar SQL,
and alias export.
"""
from __future__ import annotations

import json

import click

from propstore.cli.output import emit, emit_error, emit_success

from propstore.app.compiler import (
    CompilerWorkflowError,
    build_repository,
    export_aliases as run_export_aliases,
    validate_repository,
)
from propstore.cli.helpers import EXIT_VALIDATION, exit_with_code, fail
from propstore.repository import Repository


_PHI_GROUP_GLOSSES = {
    "PHI_NODE": "concept slot with multiple competing claim branches in the same context",
    "CONTEXT_PHI_NODE": "concept slot with competing branches across different contexts",
}


def _emit_workflow_messages(messages) -> None:
    for message in messages:
        label = message.level.upper()
        emit_error(f"{label} ({message.family.value}): {message.render()}")


@click.command()
@click.pass_obj
def validate(obj: dict) -> None:
    """Validate all concepts and claims. Runs CEL type-checking."""
    repo: Repository = obj["repo"]
    try:
        report = validate_repository(repo)
    except CompilerWorkflowError as exc:
        _emit_workflow_messages(exc.messages)
        emit_error(exc.summary)
        exit_with_code(EXIT_VALIDATION)
        return

    if report.no_concepts:
        emit("No concept files found.")
        return

    _emit_workflow_messages(report.messages)
    if report.ok:
        emit_success(
            f"Validation passed: {report.concept_count} concept(s), "
            f"{report.claim_file_count} claim file(s)")
    else:
        emit_error(f"Validation FAILED: {len(report.errors)} error(s)")
        exit_with_code(EXIT_VALIDATION)
        return


@click.command()
@click.option("-o", "--output", default=None, help="Output path")
@click.option("--force", is_flag=True, help="Force rebuild")
@click.pass_obj
def build(obj: dict, output: str | None, force: bool) -> None:
    """Validate everything, build sidecar, run conflict detection."""
    repo: Repository = obj["repo"]
    try:
        report = build_repository(repo, output=output, force=force)
    except CompilerWorkflowError as exc:
        _emit_workflow_messages(exc.messages)
        emit_error(exc.summary)
        exit_with_code(EXIT_VALIDATION)
        return

    if report.no_concepts:
        emit("No concept files found.")
        return

    _emit_workflow_messages(report.messages)
    if report.sidecar_missing:
        emit_error("Build FAILED: sidecar database was not created.")
        exit_with_code(EXIT_VALIDATION)
        return

    for conflict in report.conflicts:
        emit(
            f"  {conflict.warning_class}: {conflict.concept_id} "
            f"({conflict.claim_a_id} vs {conflict.claim_b_id})",
            err=True,
        )
    emitted_phi_glosses: set[str] = set()
    for group in report.phi_groups:
        group_kind = group.key.split(":", 1)[0]
        gloss = _PHI_GROUP_GLOSSES.get(group_kind)
        if gloss is not None and group_kind not in emitted_phi_glosses:
            emit(f"  {group_kind} — {gloss}", err=True)
            emitted_phi_glosses.add(group_kind)
        emit(
            f"  {group.key} — {len(group.claim_ids)} branches: "
            f"{', '.join(group.claim_ids)}",
            err=True,
        )
    if report.embedding_snapshot is not None:
        snapshot = report.embedding_snapshot
        emit(
            "  Embedding snapshot: "
            f"{snapshot.model_count} model(s), "
            f"{snapshot.claim_vector_count} claim vecs, "
            f"{snapshot.concept_vector_count} concept vecs",
            err=True,
        )

    status = "rebuilt" if report.rebuilt else "unchanged"
    emit(
        f"Build {status}: {report.concept_count} concepts, "
        f"{report.claim_count} claims, {report.conflict_count} hard conflicts, "
        f"{report.phi_node_count} phi-nodes, {report.warning_count} warnings")


@click.command("export-aliases")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text",
              help="Output format")
@click.pass_obj
def export_aliases(obj: dict, fmt: str) -> None:
    """Export the alias lookup table."""
    repo: Repository = obj["repo"]
    try:
        aliases = run_export_aliases(repo)
    except FileNotFoundError:
        fail("No concepts directory.")

    if fmt == "json":
        emit(json.dumps(
            {alias: entry.to_dict() for alias, entry in aliases.items()},
            indent=2,
        ))
    else:
        for alias_name, info in sorted(aliases.items()):
            emit(f"{alias_name} -> {info.logical_id} ({info.name})")
