"""Compiler-facing CLI commands.

Thin Click adapters over :mod:`propstore.compiler.workflows`: ``pks validate``
runs the shared semantic check set, ``pks build`` additionally materialises the
world sidecar and reports the conflict / phi summary. No compiler workflow logic
lives here (CLAUDE.md "CLI adapter discipline").
"""

from __future__ import annotations

import json
from collections.abc import Iterable

from propstore.app.aliases import export_concept_aliases
from propstore.app.world import WorldSidecarMissingError, open_app_world_model
from propstore.cli.helpers import (
    EXIT_VALIDATION,
    CliContext,
    exit_with_code,
    fail,
    require_repo,
)
from propstore.cli.output import emit, emit_error, emit_success
from propstore.compiler.errors import CompilerWorkflowError
from propstore.compiler.workflows import build_repository, validate_repository
from propstore.semantic_passes.types import PassDiagnostic

import click

_PHI_GROUP_GLOSSES = {
    "PHI_NODE": "concept slot with multiple competing claim branches in the same context",
    "CONTEXT_PHI_NODE": "concept slot with competing branches across different contexts",
}


def _emit_workflow_messages(messages: Iterable[PassDiagnostic]) -> None:
    for message in messages:
        label = message.level.upper()
        family = (
            "authoring"
            if message.code.startswith("authoring.")
            else message.family.value
        )
        emit_error(f"{label} ({family}): {message.render()}")


@click.command()
@click.pass_obj
def validate(obj: CliContext) -> None:
    """Validate all concepts and claims. Runs CEL type-checking."""
    repo = require_repo(obj)
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
            f"{report.claim_count} claim file(s)"
        )
    else:
        emit_error(f"Validation FAILED: {len(report.errors)} error(s)")
        exit_with_code(EXIT_VALIDATION)
        return


@click.command()
@click.option("--force", is_flag=True, help="Force rebuild")
@click.option(
    "--strict-authoring",
    is_flag=True,
    help="Promote authoring lints to build errors.",
)
@click.pass_obj
def build(
    obj: CliContext,
    force: bool,
    strict_authoring: bool,
) -> None:
    """Validate everything, build sidecar, run conflict detection."""
    repo = require_repo(obj)
    try:
        report = build_repository(
            repo,
            force=force,
            strict_authoring=strict_authoring,
        )
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
        f"{report.phi_node_count} phi-nodes, {report.warning_count} warnings"
    )
    if report.derived_store is not None:
        handle = report.derived_store
        emit(
            "Derived store: "
            f"{handle.projection_id} {handle.source_commit} "
            f"{handle.cache_key} {handle.path}"
        )


@click.command("export-aliases")
@click.pass_obj
def export_aliases(obj: CliContext) -> None:
    """Export every concept's lemon other-form aliases as a JSON map.

    Thin adapter over :func:`propstore.app.aliases.export_concept_aliases`: opens
    the world sidecar, projects each alias to its canonical concept identity, and
    prints an ``alias -> {logical_id, name}`` JSON object.
    """
    repo = require_repo(obj)
    try:
        with open_app_world_model(repo) as world_query:
            aliases = export_concept_aliases(world_query)
    except WorldSidecarMissingError as exc:
        fail(str(exc))
    payload = {name: entry.to_dict() for name, entry in sorted(aliases.items())}
    emit(json.dumps(payload, indent=2))
