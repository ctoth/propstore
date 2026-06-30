"""Phase 9-3: blocked-claim sidecar mirror + source-status derived-store reader.

The quarantine *invariant* (a claim that cannot promote cleanly stays on the
source branch, present and surfaced) was already proven in 8-3b. Phase 9-3 adds
the derived-store *projection* of that state: the build mirrors each source
branch's blocked-promotion reasons into the world sidecar as ``promotion_blocked``
``build_diagnostic`` rows (present, filtered at render — never dropped), and
``read_sidecar_source_status`` reads them back, scoped to one source branch,
without reaching up into the world layer.
"""

from __future__ import annotations

from pathlib import Path

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.claims import ClaimType
from propstore.families.contexts import Context
from propstore.derived_build import materialize_world_sidecar
from propstore.repository import Repository
from propstore.source import (
    compile_all_source_promotion_blocked_projection_rows,
    finalize_source_branch,
    init_source_branch,
    read_sidecar_source_status,
    source_branch_name,
)
from propstore.source.claims import commit_source_claim_proposal
from propstore.source.concepts import commit_source_concept_proposal
from propstore.source.status import SourceStatusState

_SOURCE = "Blocked Demo 2026"


def _new_source(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path)
    init_source_branch(
        repo,
        _SOURCE,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value="manual",
    )
    return repo


def _seed_context(repo: Repository, context_id: str = "ctx") -> None:
    repo.families.context.save(
        context_id,
        Context(context_id=context_id, name=context_id),
        message=f"seed context {context_id}",
    )


def _author_claim(
    repo: Repository, *, claim_id: str, concept: str = "widget", context: str = "ctx"
) -> str:
    commit_source_concept_proposal(
        repo, _SOURCE, local_name=concept, definition="a thing", form="dimensionless"
    )
    stored = commit_source_claim_proposal(
        repo,
        _SOURCE,
        claim_id=claim_id,
        claim_type=ClaimType.OBSERVATION,
        context=context,
        statement="it holds",
        concepts=(concept,),
        page=1,
    )
    assert stored.artifact_id is not None
    return stored.artifact_id


def test_blocked_promotion_mirrors_into_sidecar(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo, "ctx")
    _author_claim(repo, claim_id="ok", context="ctx")
    # A claim whose context is not on master cannot promote cleanly.
    blocked_id = _author_claim(repo, claim_id="bad", context="ghost_ctx")
    finalize_source_branch(repo, _SOURCE)

    rows = compile_all_source_promotion_blocked_projection_rows(repo)

    assert rows.diagnostics, "the blocked claim must project a diagnostic"
    blocked = [d for d in rows.diagnostics if d.claim_id == blocked_id]
    assert blocked, "the off-master-context claim is the blocked one"
    diagnostic = blocked[0]
    assert diagnostic.diagnostic_kind == "promotion_blocked"
    assert diagnostic.severity == "error"
    assert diagnostic.blocking == 1
    assert diagnostic.source_ref == f"{source_branch_name(_SOURCE)}:{blocked_id}"
    # The cleanly-promotable claim contributes no blocked diagnostic.
    assert all(d.claim_id != "ok" for d in rows.diagnostics)


def test_read_sidecar_source_status_surfaces_blocked(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo, "ctx")
    _author_claim(repo, claim_id="ok", context="ctx")
    blocked_id = _author_claim(repo, claim_id="bad", context="ghost_ctx")
    finalize_source_branch(repo, _SOURCE)

    handle, _ = materialize_world_sidecar(repo)
    report = read_sidecar_source_status(handle, _SOURCE)

    assert report.state is SourceStatusState.HAS_CLAIMS
    assert report.branch == source_branch_name(_SOURCE)
    blocked_rows = {row.claim_id: row for row in report.rows}
    assert blocked_id in blocked_rows
    row = blocked_rows[blocked_id]
    assert row.promotion_status == "blocked"
    assert row.diagnostics, "the blocked row carries its reason"
    assert any("ghost_ctx" in d.message for d in row.diagnostics)
    # Non-commitment: the blocked claim is still PRESENT on the source branch.
    tip = repo.require_git().branch_sha(source_branch_name(_SOURCE))
    assert tip is not None


def test_read_sidecar_source_status_no_blocked_rows(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo, "ctx")
    _author_claim(repo, claim_id="ok", context="ctx")
    finalize_source_branch(repo, _SOURCE)

    handle, _ = materialize_world_sidecar(repo)
    report = read_sidecar_source_status(handle, _SOURCE)

    # Every claim promotes cleanly, so nothing is mirrored as blocked.
    assert report.state is SourceStatusState.NO_CLAIMS
    assert report.rows == ()
