"""Typed source-branch promotion-status reports.

Two readers answer "what is this source branch's promotion status?" from two
vantage points:

* :func:`inspect_source_status` (families-only) reports, for a source branch,
  which of its claims would promote cleanly and which would be quarantined —
  computed directly from the source-branch families plus the master
  concept/context state, with no sidecar read. It reuses the promote subsystem's
  quarantine computation so the status a user sees before promoting matches what
  promotion will do.
* :func:`read_sidecar_source_status` reads the *derived store* (the
  ``promotion_blocked`` mirror rows a build materializes, see
  :func:`propstore.source.promote.compile_all_source_promotion_blocked_projection_rows`).
  It surfaces the build-projected blocked state for one source branch from the
  world sidecar through the source subsystem's own sqlite read — it does **not**
  reach up into the world layer.

The sidecar carries the branch-scoped blocked state on
:class:`~propstore.families.diagnostics.BuildDiagnostic` rows whose ``source_ref``
is ``"<source-branch>:<artifact-id>"``; the reader scopes by that prefix.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import msgspec

from propstore.repository import Repository

from .common import load_source_claims_document, source_branch_name
from .promote import (
    compute_blocked_claim_artifact_ids,
    master_context_ids,
    resolve_source_concept_promotions,
)
from .reference_indexes import source_claim_index as build_source_claim_index

if TYPE_CHECKING:
    from quire.derived_store import DerivedStoreHandle


class SourceStatusState(str, Enum):
    """Coarse state of a source branch's promotability.

    The families-only reader uses ``NO_BRANCH`` / ``NO_CLAIMS`` / ``HAS_CLAIMS``.
    The sidecar reader reuses ``NO_CLAIMS`` (no blocked rows mirrored) /
    ``HAS_CLAIMS`` (blocked rows present) and adds ``SIDECAR_MISSING`` when the
    sidecar has no ``build_diagnostic`` table to read (it has not been built).
    """

    NO_BRANCH = "no_branch"
    NO_CLAIMS = "no_claims"
    HAS_CLAIMS = "has_claims"
    SIDECAR_MISSING = "sidecar_missing"


@dataclass(frozen=True)
class SourceStatusDiagnostic:
    kind: str
    message: str


@dataclass(frozen=True)
class SourceStatusRow:
    claim_id: str
    promotion_status: str
    diagnostics: tuple[SourceStatusDiagnostic, ...]


@dataclass(frozen=True)
class SourceStatusReport:
    branch: str
    state: SourceStatusState
    rows: tuple[SourceStatusRow, ...] = ()


def inspect_source_status(repo: Repository, source_name: str) -> SourceStatusReport:
    """Report each source claim's would-be promotion status (ready/blocked)."""

    branch = source_branch_name(source_name)
    git = repo.git
    if git is None or git.branch_sha(branch) is None:
        return SourceStatusReport(branch=branch, state=SourceStatusState.NO_BRANCH)

    claims_doc = load_source_claims_document(repo, source_name)
    if claims_doc is None or not claims_doc.claims:
        return SourceStatusReport(branch=branch, state=SourceStatusState.NO_CLAIMS)

    concept_resolution = resolve_source_concept_promotions(repo, source_name)
    source_index = build_source_claim_index(repo, source_name)
    blocked_ids, reasons = compute_blocked_claim_artifact_ids(
        claims_doc=claims_doc,
        justifications_doc=None,
        source_claim_index_exists=source_index.exists,
        concept_map=concept_resolution.concept_map,
        blocked_concept_refs=concept_resolution.blocked_concept_refs,
        master_context_ids=master_context_ids(repo),
    )

    rows: list[SourceStatusRow] = []
    for claim in claims_doc.claims:
        artifact_id = claim.artifact_id
        if not isinstance(artifact_id, str) or not artifact_id:
            continue
        blocked = artifact_id in blocked_ids
        diagnostics = tuple(
            SourceStatusDiagnostic(kind=kind, message=detail)
            for kind, detail in reasons.get(artifact_id, [])
        )
        rows.append(
            SourceStatusRow(
                claim_id=artifact_id,
                promotion_status="blocked" if blocked else "ready",
                diagnostics=diagnostics,
            )
        )

    return SourceStatusReport(
        branch=branch,
        state=SourceStatusState.HAS_CLAIMS,
        rows=tuple(rows),
    )


def _escape_sql_like(value: str) -> str:
    """Escape LIKE wildcards in *value* for an ``ESCAPE '!'`` pattern."""

    return value.replace("!", "!!").replace("%", "!%").replace("_", "!_")


def _has_build_diagnostic_table(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        ("build_diagnostic",),
    ).fetchone()
    return row is not None


def _reason_kind(detail_json: object, fallback: str) -> str:
    """Pull the structured ``reason_kind`` out of a diagnostic's ``detail_json``."""

    if not isinstance(detail_json, str) or not detail_json:
        return fallback
    decoded = msgspec.json.decode(detail_json, type=dict[str, object])
    kind = decoded.get("reason_kind")
    if isinstance(kind, str) and kind:
        return kind
    return fallback


def read_sidecar_source_status(
    handle: DerivedStoreHandle, name: str
) -> SourceStatusReport:
    """Surface a source branch's build-projected blocked-promotion status.

    Reads the world sidecar's ``promotion_blocked`` diagnostic rows scoped to this
    source branch (``source_ref`` prefix) and groups them per blocked claim. The
    rows are *present* in the sidecar — surfaced here regardless of render policy —
    because this is the audit reader for the quarantine state, not the default
    render view. Read-only; opens its own sqlite connection and closes it.
    """

    branch = source_branch_name(name)
    conn = handle.open_readonly()
    conn.row_factory = sqlite3.Row
    try:
        if not _has_build_diagnostic_table(conn):
            return SourceStatusReport(
                branch=branch, state=SourceStatusState.SIDECAR_MISSING
            )
        like_pattern = f"{_escape_sql_like(branch)}:%"
        diagnostic_rows = conn.execute(
            "SELECT claim_id, diagnostic_kind, message, source_ref, detail_json "
            "FROM build_diagnostic "
            "WHERE diagnostic_kind = 'promotion_blocked' "
            "AND source_ref LIKE ? ESCAPE '!' "
            "ORDER BY source_ref, diagnostic_id",
            (like_pattern,),
        ).fetchall()
    finally:
        conn.close()

    diagnostics_by_claim: dict[str, list[SourceStatusDiagnostic]] = {}
    order: list[str] = []
    for row in diagnostic_rows:
        source_ref = str(row["source_ref"] or "")
        claim_id = row["claim_id"]
        key = str(claim_id) if claim_id else source_ref.split(":", 1)[-1]
        if key not in diagnostics_by_claim:
            diagnostics_by_claim[key] = []
            order.append(key)
        diagnostics_by_claim[key].append(
            SourceStatusDiagnostic(
                kind=_reason_kind(row["detail_json"], str(row["diagnostic_kind"])),
                message=str(row["message"]),
            )
        )

    if not order:
        return SourceStatusReport(branch=branch, state=SourceStatusState.NO_CLAIMS)

    rows = tuple(
        SourceStatusRow(
            claim_id=key,
            promotion_status="blocked",
            diagnostics=tuple(diagnostics_by_claim[key]),
        )
        for key in order
    )
    return SourceStatusReport(
        branch=branch, state=SourceStatusState.HAS_CLAIMS, rows=rows
    )
