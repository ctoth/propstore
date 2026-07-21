"""``pks event`` — render-time description-claim coreference.

A thin Click adapter (CLAUDE.md "CLI adapter discipline") over the owner
:mod:`propstore.app.events`. ``show``/``list`` resolve stored merge-argument
proposals into coreference clusters under a chosen semantics; ``propose``/``attack``
author proposals on the ``proposal/coreference`` branch. No query, authoring, or
policy semantics live here — this module only parses flags into typed requests,
calls the owner, renders the typed reports, and maps typed failures to exit codes.

Coreference clusters are defined only for the sceptical ``grounded`` and the
credulous ``preferred`` semantics, so ``--semantics`` offers exactly those; the
owner still returns a typed failure for anything else, which this adapter maps to
the validation exit code.
"""

from __future__ import annotations

import click

from propstore.app.events import (
    CoreferenceClustersReport,
    UnknownCoreferenceArgument,
    UnsupportedCoreferenceSemantics,
    coreference_clusters,
    coreference_clusters_for_claim,
    propose_coreference_merge_argument,
    record_coreference_attack,
)
from propstore.cli.helpers import (
    EXIT_VALIDATION,
    CliContext,
    exit_with_code,
    fail,
    require_repo,
)
from propstore.cli.output import emit
from propstore.core.reasoning import ArgumentationSemantics
from propstore.core.render_policy import RenderPolicy
from propstore.provenance import Provenance, ProvenanceStatus

_SEMANTICS_CHOICE = click.Choice(["grounded", "preferred"])
_PROVENANCE_CHOICE = click.Choice([status.value for status in ProvenanceStatus])


def _policy(semantics: str) -> RenderPolicy:
    return RenderPolicy(semantics=ArgumentationSemantics(semantics))


def _split_ids(raw: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _emit_report(report: CoreferenceClustersReport) -> None:
    emit(f"Semantics: {report.semantics.value}")
    if not report.clusters:
        emit("No coreference clusters.")
        return
    for view in report.clusters:
        emit(f"Cluster: {', '.join(view.claim_ids)}")
        for argument in view.supporting_arguments:
            emit(
                f"  supported by {argument.argument_id} "
                f"({argument.provenance.status.value})"
            )


def _render_or_exit(
    report: CoreferenceClustersReport | UnsupportedCoreferenceSemantics,
) -> None:
    if isinstance(report, UnsupportedCoreferenceSemantics):
        emit(report.message())
        exit_with_code(EXIT_VALIDATION)
    _emit_report(report)


@click.group()
def event() -> None:
    """Query and author render-time description-claim coreference."""


@event.command("list")
@click.option("--semantics", type=_SEMANTICS_CHOICE, default="grounded")
@click.pass_obj
def event_list(obj: CliContext, semantics: str) -> None:
    """List every coreference cluster admitted under the chosen semantics."""

    repo = require_repo(obj)
    _render_or_exit(coreference_clusters(repo, _policy(semantics)))


@event.command("show")
@click.argument("claim_id")
@click.option("--semantics", type=_SEMANTICS_CHOICE, default="grounded")
@click.pass_obj
def event_show(obj: CliContext, claim_id: str, semantics: str) -> None:
    """Show the coreference cluster(s) containing CLAIM_ID under the semantics."""

    repo = require_repo(obj)
    _render_or_exit(coreference_clusters_for_claim(repo, claim_id, _policy(semantics)))


@event.command("propose")
@click.option(
    "--supports",
    required=True,
    help="Comma-separated claim ids this merge argument would merge.",
)
@click.option(
    "--description-claims",
    default=None,
    help="Comma-separated description-claim ids (defaults to --supports).",
)
@click.option(
    "--provenance-status",
    type=_PROVENANCE_CHOICE,
    default=ProvenanceStatus.STATED.value,
)
@click.option("--note", default=None, help="Optional free-text note.")
@click.pass_obj
def event_propose(
    obj: CliContext,
    supports: str,
    description_claims: str | None,
    provenance_status: str,
    note: str | None,
) -> None:
    """Author a coreference merge-argument proposal."""

    repo = require_repo(obj)
    support_ids = _split_ids(supports)
    if not support_ids:
        fail(
            "propose requires at least one --supports claim id",
            exit_code=EXIT_VALIDATION,
        )
    description_ids = _split_ids(description_claims) if description_claims else ()
    result = propose_coreference_merge_argument(
        repo,
        supports=support_ids,
        description_claim_ids=description_ids,
        provenance=Provenance(status=ProvenanceStatus(provenance_status)),
        note=note,
    )
    emit(result.argument_id)


@event.command("attack")
@click.argument("attacker_id")
@click.argument("target_id")
@click.pass_obj
def event_attack(obj: CliContext, attacker_id: str, target_id: str) -> None:
    """Record that ATTACKER_ID attacks TARGET_ID between stored merge arguments."""

    repo = require_repo(obj)
    try:
        record_coreference_attack(repo, attacker_id=attacker_id, target_id=target_id)
    except UnknownCoreferenceArgument as exc:
        fail(str(exc), exit_code=EXIT_VALIDATION)
    emit(f"Recorded attack {attacker_id} -> {target_id}")
