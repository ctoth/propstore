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

from quire.projections import ProjectionColumn, ProjectionSchemaError, ProjectionTable
from propstore.families.calibration.declaration import CALIBRATION_COUNTS_PROJECTION
from propstore.families.claims.declaration import (
    CLAIM_ALGORITHM_PAYLOAD_PROJECTION,
    CLAIM_CONCEPT_LINK_PROJECTION,
    CLAIM_CORE_PROJECTION,
    CLAIM_FTS_PROJECTION,
    CLAIM_NUMERIC_PAYLOAD_PROJECTION,
    CLAIM_TEXT_PAYLOAD_PROJECTION,
    CONFLICT_WITNESS_PROJECTION,
    JUSTIFICATION_PROJECTION,
)
from propstore.families.concepts.declaration import (
    ALIAS_PROJECTION,
    CONCEPT_FTS_PROJECTION,
    CONCEPT_PROJECTION,
    FORM_ALGEBRA_PROJECTION,
    FORM_PROJECTION,
    PARAMETERIZATION_PROJECTION,
    PARAMETERIZATION_GROUP_PROJECTION,
    RELATIONSHIP_PROJECTION,
)
from propstore.families.contexts.declaration import (
    ContextSidecarRows,
    create_context_tables,
    populate_contexts as populate_context_projection_rows,
)
from propstore.families.diagnostics.declaration import BUILD_DIAGNOSTICS_PROJECTION
from propstore.families.embeddings.declaration import ensure_embedding_tables
from propstore.families.micropublications.declaration import create_micropublication_tables
from propstore.families.projection_catalog import PROPSTORE_WORLD_PROJECTION_SCHEMA
from propstore.families.relations.declaration import RELATION_EDGE_PROJECTION
from propstore.families.sources.declaration import SOURCE_PROJECTION

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


def sidecar_table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def read_sidecar_schema_version(conn: sqlite3.Connection) -> int:
    if not sidecar_table_exists(conn, "meta"):
        raise ValueError(
            "Unsupported sidecar schema: missing table(s) meta. "
            "Rebuild with 'pks build'."
        )
    meta_row = conn.execute(
        "SELECT schema_version FROM meta WHERE key = ?",
        (SIDECAR_META_KEY,),
    ).fetchone()
    if meta_row is None:
        raise ValueError(
            "Unsupported sidecar schema: missing metadata row for sidecar. "
            "Rebuild with 'pks build'."
        )
    return int(meta_row["schema_version"])


def validate_world_sidecar_schema(conn: sqlite3.Connection) -> None:
    actual_version = read_sidecar_schema_version(conn)
    if actual_version != SCHEMA_VERSION:
        raise ValueError(
            "Unsupported sidecar schema version: "
            f"expected {SCHEMA_VERSION}, found {actual_version}. "
            "Rebuild with 'pks build'."
        )

    try:
        PROPSTORE_WORLD_PROJECTION_SCHEMA.validate_connection(conn)
    except ProjectionSchemaError as error:
        raise ValueError(
            f"Unsupported sidecar schema: {error}. Rebuild with 'pks build'."
        ) from error


def create_tables(conn: sqlite3.Connection) -> None:
    for projection in (
        SOURCE_PROJECTION,
        FORM_PROJECTION,
        FORM_ALGEBRA_PROJECTION,
        CONCEPT_PROJECTION,
        ALIAS_PROJECTION,
        CONCEPT_FTS_PROJECTION,
        PARAMETERIZATION_PROJECTION,
        PARAMETERIZATION_GROUP_PROJECTION,
        RELATIONSHIP_PROJECTION,
        RELATION_EDGE_PROJECTION,
    ):
        for statement in projection.ddl_statements():
            conn.execute(statement)


def build_minimal_world_model_schema(conn: sqlite3.Connection) -> None:
    """Build the production schema surface required by WorldQuery tests."""
    from propstore.families.rules.declaration import create_grounded_fact_table

    write_schema_metadata(conn)
    create_tables(conn)
    create_context_tables(conn)
    create_claim_tables(conn)
    create_micropublication_tables(conn)
    create_grounded_fact_table(conn)
    ensure_embedding_tables(conn)


def populate_contexts(
    conn: sqlite3.Connection,
    rows: ContextSidecarRows,
) -> None:
    populate_context_projection_rows(
        conn,
        context_rows=rows.context_rows,
        assumption_rows=rows.assumption_rows,
        lifting_rule_rows=rows.lifting_rule_rows,
        lifting_materialization_rows=rows.lifting_materialization_rows,
    )


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
