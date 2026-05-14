"""Sidecar schema and table helpers.

Schema version 5 extends the build-time schema with per-row
lifecycle annotations and a quarantine surface so the render layer can
filter on policy without losing data. This implements the build-to-render
gate-removal workstream described in
``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md`` —
specifically the changes called out in axis-1 findings 3.1 (raw-id input
quarantine), 3.2 (draft visibility), and 3.3 (partial source promotion).

The discipline (``reviews/2026-04-16-code-review/workstreams/disciplines.md``
rule 5: "Filter at render, not at build") is concrete here:

- ``build_diagnostics`` carries per-row build-time diagnostic information
  (kind, severity, blocking-vs-warning flag, optional structured payload).
  Render-policy filtering at query time decides what to show.
- ``claim_core.build_status`` annotates whether a claim row was
  ingested cleanly (``'ingested'``) or admitted under a relaxed gate
  with a quarantine diagnostic attached (``'blocked'``). The default
  preserves "ingested" for all rows that the build wrote without issue.
- ``claim_core.stage`` is the *file-level* lifecycle marker for the row
  (e.g., ``'draft'`` or ``'final'``). It is distinct from
  ``claim_algorithm_payload.algorithm_stage``, which records an
  algorithm-internal sub-phase (e.g., ``'excitation'``). Drafts populate
  normally; the render layer's default policy hides them.
- ``claim_core.promotion_status`` records whether a source-branch claim
  was promoted to the primary branch (``'promoted'``), held back due to
  finalize errors (``'blocked'``), or is not part of a source-branch
  promotion flow (``NULL``).

These three columns are intentionally orthogonal — they index three
independent lifecycle dimensions: ingestion success
(``build_status``), file-level lifecycle (``stage``), and
source-promotion status (``promotion_status``). A single row may carry
any combination, and each is filtered independently by the render
policy. Collapsing them into a single ``status`` field would force
heuristic resolution at storage time, which violates the project's
non-commitment-at-source design principle (``CLAUDE.md`` core design
principle).
"""

from __future__ import annotations

import sqlite3

from propstore.sidecar.calibration import CALIBRATION_COUNTS_PROJECTION
from propstore.sidecar.claims import (
    CLAIM_ALGORITHM_PAYLOAD_PROJECTION,
    CLAIM_CONCEPT_LINK_PROJECTION,
    CLAIM_CORE_PROJECTION,
    CLAIM_FTS_PROJECTION,
    CLAIM_NUMERIC_PAYLOAD_PROJECTION,
    CLAIM_TEXT_PAYLOAD_PROJECTION,
    CONFLICT_WITNESS_PROJECTION,
    JUSTIFICATION_PROJECTION,
)
from propstore.sidecar.concepts import (
    ALIAS_PROJECTION,
    CONCEPT_FTS_PROJECTION,
    CONCEPT_PROJECTION,
    FORM_ALGEBRA_PROJECTION,
    FORM_PROJECTION,
    PARAMETERIZATION_PROJECTION,
    PARAMETERIZATION_GROUP_PROJECTION,
    RELATIONSHIP_PROJECTION,
)
from propstore.sidecar.contexts import (
    CONTEXT_ASSUMPTION_PROJECTION,
    CONTEXT_LIFTING_MATERIALIZATION_PROJECTION,
    CONTEXT_LIFTING_RULE_PROJECTION,
    CONTEXT_PROJECTION,
)
from propstore.sidecar.diagnostics import (
    BUILD_DIAGNOSTICS_PROJECTION,
    create_build_diagnostics_table as create_build_diagnostics_projection_table,
)
from propstore.sidecar.embedding_store import ensure_embedding_tables
from propstore.sidecar.micropublications import (
    create_micropublication_tables as create_micropublication_projection_tables,
)
from quire.projections import ProjectionColumn, ProjectionTable
from propstore.sidecar.relations import RELATION_EDGE_PROJECTION
from propstore.sidecar.sources import SOURCE_PROJECTION
from propstore.sidecar.stages import ContextSidecarRows

SCHEMA_VERSION = 6
SIDECAR_META_KEY = "sidecar"


META_PROJECTION = ProjectionTable(
    name="meta",
    columns=(
        ProjectionColumn("key", "TEXT", primary_key=True),
        ProjectionColumn("schema_version", "INTEGER", nullable=False),
    ),
    if_not_exists=True,
)


def create_meta_table(conn: sqlite3.Connection) -> None:
    """Create the sidecar metadata table."""
    for statement in META_PROJECTION.ddl_statements():
        conn.execute(statement)


def write_schema_metadata(conn: sqlite3.Connection) -> None:
    """Persist the current schema version for this compiled sidecar."""
    create_meta_table(conn)
    conn.execute(
        """
        INSERT INTO meta (key, schema_version)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET schema_version=excluded.schema_version
        """,
        (SIDECAR_META_KEY, SCHEMA_VERSION),
    )


def create_concept_fts_table(conn: sqlite3.Connection) -> None:
    for statement in CONCEPT_FTS_PROJECTION.ddl_statements():
        conn.execute(statement)


def create_tables(conn: sqlite3.Connection) -> None:
    for projection in (
        SOURCE_PROJECTION,
        FORM_PROJECTION,
        FORM_ALGEBRA_PROJECTION,
        CONCEPT_PROJECTION,
        ALIAS_PROJECTION,
        PARAMETERIZATION_PROJECTION,
        PARAMETERIZATION_GROUP_PROJECTION,
        RELATIONSHIP_PROJECTION,
        RELATION_EDGE_PROJECTION,
    ):
        for statement in projection.ddl_statements():
            conn.execute(statement)


def build_minimal_world_model_schema(conn: sqlite3.Connection) -> None:
    """Build the production schema surface required by WorldQuery tests."""
    from propstore.sidecar.rules import create_grounded_fact_table

    write_schema_metadata(conn)
    create_tables(conn)
    create_concept_fts_table(conn)
    create_context_tables(conn)
    create_claim_tables(conn)
    create_micropublication_tables(conn)
    create_grounded_fact_table(conn)
    ensure_embedding_tables(conn)


def create_context_tables(conn: sqlite3.Connection) -> None:
    for projection in (
        CONTEXT_PROJECTION,
        CONTEXT_ASSUMPTION_PROJECTION,
        CONTEXT_LIFTING_RULE_PROJECTION,
        CONTEXT_LIFTING_MATERIALIZATION_PROJECTION,
    ):
        for statement in projection.ddl_statements():
            conn.execute(statement)


def create_micropublication_tables(conn: sqlite3.Connection) -> None:
    create_micropublication_projection_tables(conn)


def populate_contexts(
    conn: sqlite3.Connection,
    rows: ContextSidecarRows,
) -> None:
    context_insert_sql = CONTEXT_PROJECTION.insert_sql()
    for row in rows.context_rows:
        conn.execute(context_insert_sql, row.as_insert_mapping())

    assumption_insert_sql = CONTEXT_ASSUMPTION_PROJECTION.insert_sql()
    for row in rows.assumption_rows:
        conn.execute(assumption_insert_sql, row.as_insert_mapping())

    lifting_rule_insert_sql = CONTEXT_LIFTING_RULE_PROJECTION.insert_sql()
    for row in rows.lifting_rule_rows:
        conn.execute(lifting_rule_insert_sql, row.as_insert_mapping())

    materialization_insert_sql = CONTEXT_LIFTING_MATERIALIZATION_PROJECTION.insert_sql()
    for row in rows.lifting_materialization_rows:
        conn.execute(materialization_insert_sql, row.as_insert_mapping())


def create_build_diagnostics_table(conn: sqlite3.Connection) -> None:
    create_build_diagnostics_projection_table(conn)


def create_claim_tables(conn: sqlite3.Connection) -> None:
    """Create the claim, payload, witness, and build-diagnostics tables.

    Schema-v3 additions (per
    ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``
    findings 3.1/3.2/3.3):

    - ``claim_core.build_status`` — ``'ingested' | 'blocked'``; default
      ``'ingested'``. Per finding 3.1: claims that ingested only because
      a build-time gate was relaxed carry ``'blocked'`` plus a row in
      ``build_diagnostics``.
    - ``claim_core.stage`` — file-level lifecycle marker
      (``'draft' | 'final' | NULL``). Per finding 3.2: drafts populate
      normally; the render-policy default hides them.
    - ``claim_core.promotion_status`` —
      ``'promoted' | 'blocked' | NULL``. Per finding 3.3: tracks the
      outcome of source-branch promotion, with ``'blocked'`` meaning the
      claim stayed on its source branch because finalize had errors.
    - ``build_diagnostics`` — quarantine surface. Each row attaches a
      diagnostic to a claim (``claim_id``) or to a non-claim source
      artifact (``source_kind``/``source_ref``); ``blocking=1`` indicates
      the attached row was quarantined, ``blocking=0`` is informational.
      The render layer joins ``build_diagnostics`` against
      ``claim_core`` to surface "what's wrong with this row" under
      opt-in policy flags.
    """

    for statement in CALIBRATION_COUNTS_PROJECTION.ddl_statements():
        conn.execute(statement)

    for projection in (
        CLAIM_CORE_PROJECTION,
        CLAIM_CONCEPT_LINK_PROJECTION,
        CLAIM_NUMERIC_PAYLOAD_PROJECTION,
        CLAIM_TEXT_PAYLOAD_PROJECTION,
        CLAIM_ALGORITHM_PAYLOAD_PROJECTION,
        CONFLICT_WITNESS_PROJECTION,
        JUSTIFICATION_PROJECTION,
        CLAIM_FTS_PROJECTION,
        BUILD_DIAGNOSTICS_PROJECTION,
    ):
        for statement in projection.ddl_statements():
            conn.execute(statement)
