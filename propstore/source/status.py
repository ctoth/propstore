"""Typed source-branch promotion-status reports (families-only).

``inspect_source_status`` reports, for a source branch, which of its claims would
promote cleanly and which would be quarantined — computed directly from the
source-branch families plus the master concept/context state, with no sidecar
read. It reuses the promote subsystem's quarantine computation so the status a
user sees before promoting matches what promotion will do.

The reference status surface also reads the *derived store* (the sidecar mirror
rows a build materializes for blocked promotions). That reader depends on the
Phase-9 derived-store/projection pipeline and is deferred; see
``docs/rewrite/deferred-tests.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from propstore.repository import Repository

from .common import load_source_claims_document, source_branch_name
from .promote import (
    compute_blocked_claim_artifact_ids,
    master_context_ids,
    resolve_source_concept_promotions,
)
from .reference_indexes import source_claim_index as build_source_claim_index


class SourceStatusState(str, Enum):
    """Coarse state of a source branch's promotability."""

    NO_BRANCH = "no_branch"
    NO_CLAIMS = "no_claims"
    HAS_CLAIMS = "has_claims"


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
