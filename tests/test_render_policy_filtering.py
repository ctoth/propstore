"""Render-layer consumption of the Phase 4 lifecycle-visibility flags.

These tests exercise the contract described in
``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``
(exit criteria) and closed by axis-1 findings 3.1 / 3.2 / 3.3:

- Default render policy hides ``stage='draft'`` rows.
- Default render policy hides ``build_status='blocked'`` rows (raw-id
  quarantine, Phase 3 Gate 1).
- Default render policy hides ``promotion_status='blocked'`` rows
  (partial-promote mirror, Phase 3 Gate 3).
- Default render policy omits ``build_diagnostics`` entries entirely.
- ``include_drafts=True`` lifts the stage filter; ``include_blocked=True``
  lifts the two blocked filters; ``show_quarantined=True`` surfaces
  ``build_diagnostics`` rows.

Fixtures populate a real sqlite sidecar (schema v3) via
``propstore.sidecar.schema``'s real ``create_tables`` +
``create_claim_tables`` helpers, then insert a small hand-crafted mix
of rows covering each lifecycle state. No compile path is exercised —
the tests target the render layer's filtering behavior in isolation.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from propstore.sidecar.schema import (
    SCHEMA_VERSION,
    SIDECAR_META_KEY,
    create_claim_tables,
    create_context_tables,
    create_tables,
    write_schema_metadata,
)
from propstore.world.model import WorldModel
from propstore.world.types import RenderPolicy


def _write_meta(conn: sqlite3.Connection) -> None:
    write_schema_metadata(conn)


def _insert_minimal_source(conn: sqlite3.Connection, slug: str = "test-source") -> None:
    conn.execute(
        """
        INSERT INTO source (slug, source_id, kind, origin_type, origin_value)
        VALUES (?, ?, ?, ?, ?)
        """,
        (slug, slug, "academic_paper", "manual", "fixture"),
    )


def _insert_concept(conn: sqlite3.Connection, concept_id: str = "concept:alpha") -> None:
    conn.execute(
        """
        INSERT INTO concept (
            id, primary_logical_id, logical_ids_json, version_id,
            content_hash, seq, canonical_name, status, definition,
            kind_type, form, form_parameters
        ) VALUES (?, ?, '[]', '', ?, 0, ?, 'active', 'fixture concept',
                  'quantity', 'scalar', '{}')
        """,
        (concept_id, concept_id, f"hash_{concept_id}", concept_id),
    )


def _insert_claim_core(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    concept_id: str = "concept:alpha",
    source_slug: str = "test-source",
    branch: str = "master",
    build_status: str = "ingested",
    stage: str | None = None,
    promotion_status: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO claim_core (
            id, primary_logical_id, logical_ids_json, version_id,
            content_hash, seq, type, concept_id, target_concept,
            source_slug, source_paper, provenance_page, provenance_json,
            context_id, premise_kind, branch,
            build_status, stage, promotion_status
        ) VALUES (
            ?, ?, '[]', '',
            '', 0, 'parameter', ?, NULL,
            ?, ?, 0, NULL,
            NULL, 'ordinary', ?,
            ?, ?, ?
        )
        """,
        (
            claim_id,
            claim_id,
            concept_id,
            source_slug,
            source_slug,
            branch,
            build_status,
            stage,
            promotion_status,
        ),
    )


def _insert_build_diagnostic(
    conn: sqlite3.Connection,
    *,
    claim_id: str | None,
    source_kind: str,
    diagnostic_kind: str,
    message: str,
    blocking: int = 1,
    severity: str = "error",
    source_ref: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO build_diagnostics (
            claim_id, source_kind, source_ref,
            diagnostic_kind, severity, blocking, message
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (claim_id, source_kind, source_ref, diagnostic_kind, severity, blocking, message),
    )


@pytest.fixture
def lifecycle_sidecar(tmp_path: Path) -> Path:
    """Populate a schema-v3 sidecar with one row per lifecycle state.

    Rows produced:
      - ``claim_final`` — normal ingested row (default visible).
      - ``claim_draft`` — ``stage='draft'``.
      - ``claim_raw_id`` — ``build_status='blocked'`` (raw-id quarantine
        shape from Phase 3 Gate 1).
      - ``claim_promote_blocked`` — ``promotion_status='blocked'`` on a
        source branch (partial-promote mirror shape from Phase 3 Gate 3).

    One ``build_diagnostics`` row is attached per blocked state so
    ``show_quarantined=True`` has something to surface.
    """
    sidecar_dir = tmp_path / "sidecar"
    sidecar_dir.mkdir()
    sidecar_path = sidecar_dir / "propstore.sqlite"

    conn = sqlite3.connect(sidecar_path)
    try:
        create_tables(conn)
        create_context_tables(conn)
        create_claim_tables(conn)
        # ``concept_fts`` is normally built by
        # ``propstore.sidecar.concepts.build_concept_fts_index`` during the
        # full build; WorldModel validates its presence. Create a stub
        # virtual table so the render-policy fixture can open a WorldModel
        # without running the entire compile path.
        conn.execute(
            """
            CREATE VIRTUAL TABLE concept_fts USING fts5(
                concept_id UNINDEXED,
                canonical_name,
                aliases,
                definition,
                conditions
            )
            """
        )
        _write_meta(conn)

        _insert_minimal_source(conn)
        _insert_concept(conn)

        _insert_claim_core(conn, "claim_final")
        _insert_claim_core(conn, "claim_draft", stage="draft")
        _insert_claim_core(
            conn,
            "claim_raw_id",
            build_status="blocked",
        )
        _insert_claim_core(
            conn,
            "claim_promote_blocked",
            branch="source/fixture",
            promotion_status="blocked",
        )

        _insert_build_diagnostic(
            conn,
            claim_id="claim_raw_id",
            source_kind="claim",
            diagnostic_kind="raw_id_input",
            message="claim uses raw 'id' input without canonical identity fields",
        )
        _insert_build_diagnostic(
            conn,
            claim_id="claim_promote_blocked",
            source_kind="claim",
            source_ref="source/fixture:claim_promote_blocked",
            diagnostic_kind="promotion_blocked",
            message="finalize error: unresolved stance target",
        )

        conn.commit()
    finally:
        conn.close()

    return sidecar_path


@pytest.fixture
def wm(lifecycle_sidecar: Path) -> WorldModel:
    model = WorldModel(sidecar_path=lifecycle_sidecar)
    yield model
    model.close()


# ── Schema sanity check ──────────────────────────────────────────────


def test_fixture_sidecar_is_schema_v3(lifecycle_sidecar: Path) -> None:
    """Sanity: the fixture must actually use schema v3 (lifecycle columns
    are only meaningful on schema >= 3)."""
    conn = sqlite3.connect(lifecycle_sidecar)
    try:
        row = conn.execute(
            "SELECT schema_version FROM meta WHERE key = ?",
            (SIDECAR_META_KEY,),
        ).fetchone()
        assert row is not None
        assert row[0] == SCHEMA_VERSION == 3
    finally:
        conn.close()


# ── Default policy filters ──────────────────────────────────────────


def test_default_policy_hides_draft(wm: WorldModel) -> None:
    """Default ``RenderPolicy()`` hides ``stage='draft'`` rows.

    Per ws-z-render-gates.md exit criterion: ``pks query`` default output
    matches pre-fix behaviour for clean trees — drafts stay queryable
    through opt-in (include_drafts=True) but are not in the default
    view.
    """
    policy = RenderPolicy()
    rows = wm.claims_with_policy(None, policy)
    ids = {str(row.claim_id) for row in rows}
    assert "claim_draft" not in ids
    assert "claim_final" in ids


def test_default_policy_hides_build_status_blocked(wm: WorldModel) -> None:
    """Default policy hides ``build_status='blocked'`` rows (Phase 3
    Gate 1 raw-id quarantine)."""
    rows = wm.claims_with_policy(None, RenderPolicy())
    ids = {str(row.claim_id) for row in rows}
    assert "claim_raw_id" not in ids


def test_default_policy_hides_promotion_status_blocked(wm: WorldModel) -> None:
    """Default policy hides ``promotion_status='blocked'`` mirror rows
    (Phase 3 Gate 3 partial-promote mirror)."""
    rows = wm.claims_with_policy(None, RenderPolicy())
    ids = {str(row.claim_id) for row in rows}
    assert "claim_promote_blocked" not in ids


def test_default_policy_only_surfaces_clean_claims(wm: WorldModel) -> None:
    """Default policy ONLY returns the single ingested final claim."""
    rows = wm.claims_with_policy(None, RenderPolicy())
    ids = {str(row.claim_id) for row in rows}
    assert ids == {"claim_final"}


def test_default_policy_omits_build_diagnostics(wm: WorldModel) -> None:
    """Default policy returns no ``build_diagnostics`` rows.

    Per ws-z-render-gates.md: diagnostics ride alongside in storage but
    do not surface in the default render — user opts in via
    ``show_quarantined=True``.
    """
    diagnostics = wm.build_diagnostics(RenderPolicy())
    assert diagnostics == []


# ── Opt-in flags ────────────────────────────────────────────────────


def test_include_drafts_surfaces_draft_rows(wm: WorldModel) -> None:
    """``include_drafts=True`` lifts the draft filter while leaving the
    other lifecycle filters in effect."""
    policy = RenderPolicy(include_drafts=True)
    rows = wm.claims_with_policy(None, policy)
    ids = {str(row.claim_id) for row in rows}
    assert "claim_draft" in ids
    assert "claim_final" in ids
    # Still hides the blocked rows — include_drafts is orthogonal.
    assert "claim_raw_id" not in ids
    assert "claim_promote_blocked" not in ids


def test_include_blocked_surfaces_build_status_blocked(wm: WorldModel) -> None:
    """``include_blocked=True`` lifts the build_status filter."""
    policy = RenderPolicy(include_blocked=True)
    rows = wm.claims_with_policy(None, policy)
    ids = {str(row.claim_id) for row in rows}
    assert "claim_raw_id" in ids
    assert "claim_final" in ids


def test_include_blocked_surfaces_promotion_status_blocked(wm: WorldModel) -> None:
    """``include_blocked=True`` ALSO lifts the promotion_status filter —
    per the scout proposal, the single flag controls both blocked
    variants because they are conceptually the same render concern
    ("show me problematic rows")."""
    policy = RenderPolicy(include_blocked=True)
    rows = wm.claims_with_policy(None, policy)
    ids = {str(row.claim_id) for row in rows}
    assert "claim_promote_blocked" in ids


def test_show_quarantined_surfaces_diagnostics(wm: WorldModel) -> None:
    """``show_quarantined=True`` returns all ``build_diagnostics`` rows;
    the default policy returns none."""
    policy = RenderPolicy(show_quarantined=True)
    diagnostics = wm.build_diagnostics(policy)
    assert len(diagnostics) == 2
    kinds = {row["diagnostic_kind"] for row in diagnostics}
    assert kinds == {"raw_id_input", "promotion_blocked"}


def test_all_flags_on_surfaces_everything(wm: WorldModel) -> None:
    """All three flags on → every lifecycle row is visible + diagnostics
    surfaced. The full cross-cut."""
    policy = RenderPolicy(
        include_drafts=True,
        include_blocked=True,
        show_quarantined=True,
    )
    rows = wm.claims_with_policy(None, policy)
    ids = {str(row.claim_id) for row in rows}
    assert ids == {
        "claim_final",
        "claim_draft",
        "claim_raw_id",
        "claim_promote_blocked",
    }
    diagnostics = wm.build_diagnostics(policy)
    assert len(diagnostics) == 2
