"""``pks temporal`` — author temporal evidence and query happens-before order.

A thin Click adapter (CLAUDE.md "CLI adapter discipline") over the owner
:mod:`propstore.app.temporal`. ``frame``/``anchor``/``edge`` author canonical
temporal artifacts; ``order`` recomputes the happens-before order between two
claims per query and renders the verdict together with its witnessing evidence
path. No authoring or ordering semantics live here — this module only parses flags
into typed requests, calls the owner, renders the typed reports, and maps typed
failures to exit codes.
"""

from __future__ import annotations

import click

from propstore.app.temporal import (
    UnknownHappensBeforeAccount,
    anchor_description_claim,
    assert_happens_before,
    declare_temporal_frame,
    temporal_order_between,
)
from propstore.cli.helpers import (
    EXIT_VALIDATION,
    CliContext,
    exit_with_code,
    require_repo,
)
from propstore.cli.output import emit
from propstore.core.lemon.temporal import (
    HappensBeforeAccount,
    OrderingEvidenceKind,
    OrderingLink,
    TemporalOrderJudgment,
)
from propstore.provenance import Provenance, ProvenanceStatus

_PROVENANCE_CHOICE = click.Choice([status.value for status in ProvenanceStatus])
_ACCOUNT_CHOICE = click.Choice([account.value for account in HappensBeforeAccount])


def _provenance(status: str) -> Provenance:
    return Provenance(status=ProvenanceStatus(status))


@click.group()
def temporal() -> None:
    """Author temporal frames/anchors/edges and query happens-before order."""


@temporal.command("frame")
@click.option("--frame-id", required=True, help="Identity of the declared frame.")
@click.option(
    "--description", required=True, help="What clock/sensor/narrative it declares."
)
@click.option(
    "--provenance-status",
    type=_PROVENANCE_CHOICE,
    default=ProvenanceStatus.STATED.value,
)
@click.pass_obj
def temporal_frame(
    obj: CliContext, frame_id: str, description: str, provenance_status: str
) -> None:
    """Declare a totally-ordered temporal frame."""

    repo = require_repo(obj)
    result = declare_temporal_frame(
        repo,
        frame_id=frame_id,
        description=description,
        provenance=_provenance(provenance_status),
    )
    emit(result.frame_id)


@temporal.command("anchor")
@click.option("--anchor-id", required=True, help="Identity of the anchor.")
@click.option("--claim-id", required=True, help="The description claim being anchored.")
@click.option("--frame-id", required=True, help="The frame the claim is anchored in.")
@click.option("--valid-from", type=float, default=None, help="Optional lower bound.")
@click.option("--valid-until", type=float, default=None, help="Optional upper bound.")
@click.option(
    "--provenance-status",
    type=_PROVENANCE_CHOICE,
    default=ProvenanceStatus.STATED.value,
)
@click.pass_obj
def temporal_anchor(
    obj: CliContext,
    anchor_id: str,
    claim_id: str,
    frame_id: str,
    valid_from: float | None,
    valid_until: float | None,
    provenance_status: str,
) -> None:
    """Anchor a description claim on a frame's timeline, with optional bounds."""

    repo = require_repo(obj)
    result = anchor_description_claim(
        repo,
        anchor_id=anchor_id,
        claim_id=claim_id,
        frame_id=frame_id,
        valid_from=valid_from,
        valid_until=valid_until,
        provenance=_provenance(provenance_status),
    )
    emit(result.anchor_id)


@temporal.command("edge")
@click.argument("earlier_claim_id")
@click.argument("later_claim_id")
@click.option("--edge-id", required=True, help="Identity of the happens-before edge.")
@click.option(
    "--account",
    type=_ACCOUNT_CHOICE,
    required=True,
    help="The evidence account (mandatory; no default).",
)
@click.option(
    "--provenance-status",
    type=_PROVENANCE_CHOICE,
    default=ProvenanceStatus.STATED.value,
)
@click.pass_obj
def temporal_edge(
    obj: CliContext,
    earlier_claim_id: str,
    later_claim_id: str,
    edge_id: str,
    account: str,
    provenance_status: str,
) -> None:
    """Assert that EARLIER_CLAIM_ID happens-before LATER_CLAIM_ID."""

    repo = require_repo(obj)
    result = assert_happens_before(
        repo,
        edge_id=edge_id,
        earlier_claim_id=earlier_claim_id,
        later_claim_id=later_claim_id,
        account=account,
        provenance=_provenance(provenance_status),
    )
    if isinstance(result, UnknownHappensBeforeAccount):
        emit(result.message())
        exit_with_code(EXIT_VALIDATION)
    emit(result.edge_id)


@temporal.command("order")
@click.argument("left_claim_id")
@click.argument("right_claim_id")
@click.option(
    "--assume-complete",
    is_flag=True,
    default=False,
    help="Read absence of order as concurrency under a declared-complete evidence set.",
)
@click.pass_obj
def temporal_order_cmd(
    obj: CliContext,
    left_claim_id: str,
    right_claim_id: str,
    assume_complete: bool,
) -> None:
    """Recompute and render the happens-before order between two claims."""

    repo = require_repo(obj)
    report = temporal_order_between(
        repo, left_claim_id, right_claim_id, assume_complete=assume_complete
    )
    _emit_judgment(report.judgment)


def _emit_judgment(judgment: TemporalOrderJudgment) -> None:
    emit(f"Verdict: {judgment.verdict.value}")
    _emit_path("Forward path", judgment.forward_path)
    _emit_path("Backward path", judgment.backward_path)
    if judgment.refuting_frame_id is not None:
        emit(f"Refuted by frame: {judgment.refuting_frame_id}")
    if judgment.proven_frame_id is not None:
        emit(f"Concurrency proven by frame: {judgment.proven_frame_id}")


def _emit_path(label: str, path: tuple[OrderingLink, ...]) -> None:
    if not path:
        return
    emit(f"{label}:")
    for link in path:
        emit(
            f"  {link.earlier_claim_id} -> {link.later_claim_id} [{_link_evidence(link)}]"
        )


def _link_evidence(link: OrderingLink) -> str:
    if link.kind is OrderingEvidenceKind.AUTHORED_POSIT:
        account = link.account.value if link.account is not None else "?"
        return f"authored_posit account={account} edge={link.edge_id}"
    return f"coordinate_derived frame={link.frame_id}"
