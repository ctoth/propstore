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

from propstore.sidecar.stages import ContextSidecarRows

SCHEMA_VERSION = 5
SIDECAR_META_KEY = "sidecar"


def create_meta_table(conn: sqlite3.Connection) -> None:
    """Create the sidecar metadata table."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            schema_version INTEGER NOT NULL
        )
        """
    )


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


def create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE source (
            slug TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            origin_type TEXT,
            origin_value TEXT,
            origin_retrieved TEXT,
            origin_content_ref TEXT,
            prior_base_rate TEXT,
            quality_json TEXT,
            derived_from_json TEXT,
            artifact_code TEXT
        );

        CREATE TABLE concept (
            id TEXT PRIMARY KEY,
            primary_logical_id TEXT NOT NULL DEFAULT '',
            logical_ids_json TEXT NOT NULL DEFAULT '[]',
            version_id TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL,
            seq INTEGER NOT NULL,
            canonical_name TEXT NOT NULL,
            status TEXT NOT NULL,
            domain TEXT,
            definition TEXT NOT NULL,
            kind_type TEXT NOT NULL,
            form TEXT NOT NULL,
            form_parameters TEXT,
            range_min REAL,
            range_max REAL,
            is_dimensionless INTEGER NOT NULL DEFAULT 0,
            unit_symbol TEXT,
            created_date TEXT,
            last_modified TEXT
        );

        CREATE TABLE alias (
            concept_id TEXT NOT NULL,
            alias_name TEXT NOT NULL,
            source TEXT NOT NULL,
            FOREIGN KEY (concept_id) REFERENCES concept(id)
        );

        CREATE TABLE relationship (
            source_id TEXT NOT NULL,
            type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            conditions_cel TEXT,
            note TEXT,
            FOREIGN KEY (source_id) REFERENCES concept(id),
            FOREIGN KEY (target_id) REFERENCES concept(id)
        );

        CREATE TABLE parameterization (
            output_concept_id TEXT NOT NULL,
            concept_ids TEXT NOT NULL,
            formula TEXT NOT NULL,
            sympy TEXT,
            exactness TEXT NOT NULL,
            conditions_cel TEXT,
            FOREIGN KEY (output_concept_id) REFERENCES concept(id)
        );

        CREATE TABLE parameterization_group (
            concept_id TEXT NOT NULL,
            group_id INTEGER NOT NULL,
            FOREIGN KEY (concept_id) REFERENCES concept(id)
        );

        CREATE TABLE relation_edge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_kind TEXT NOT NULL,
            source_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            target_kind TEXT NOT NULL,
            target_id TEXT NOT NULL,
            perspective_source_claim_id TEXT,
            target_justification_id TEXT,
            conditions_cel TEXT,
            strength TEXT,
            conditions_differ TEXT,
            note TEXT,
            resolution_method TEXT,
            resolution_model TEXT,
            embedding_model TEXT,
            embedding_distance REAL,
            pass_number INTEGER,
            confidence REAL,
            opinion_belief REAL,
            opinion_disbelief REAL,
            opinion_uncertainty REAL,
            opinion_base_rate REAL,
            CHECK(opinion_belief IS NULL OR (opinion_belief >= 0 AND opinion_belief <= 1)),
            CHECK(opinion_disbelief IS NULL OR (opinion_disbelief >= 0 AND opinion_disbelief <= 1)),
            CHECK(opinion_uncertainty IS NULL OR (opinion_uncertainty >= 0 AND opinion_uncertainty <= 1)),
            CHECK(opinion_base_rate IS NULL OR (opinion_base_rate > 0 AND opinion_base_rate < 1)),
            CHECK(opinion_belief IS NULL OR ABS(opinion_belief + opinion_disbelief + opinion_uncertainty - 1.0) <= 1e-6)
        );

        CREATE TABLE form (
            name TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            unit_symbol TEXT,
            is_dimensionless INTEGER NOT NULL DEFAULT 0,
            dimensions TEXT
        );

        CREATE TABLE form_algebra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            output_form TEXT NOT NULL,
            input_forms TEXT NOT NULL,
            operation TEXT NOT NULL,
            source_concept_id TEXT,
            source_formula TEXT,
            dim_verified INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (output_form) REFERENCES form(name)
        );

        CREATE INDEX idx_alias_name ON alias(alias_name);
        CREATE INDEX idx_alias_concept ON alias(concept_id);
        CREATE INDEX idx_source_source_id ON source(source_id);
        CREATE INDEX idx_concept_primary_logical_id ON concept(primary_logical_id);
        CREATE INDEX idx_rel_source ON relationship(source_id);
        CREATE INDEX idx_rel_target ON relationship(target_id);
        CREATE INDEX idx_relation_edge_source ON relation_edge(source_kind, source_id);
        CREATE INDEX idx_relation_edge_target ON relation_edge(target_kind, target_id);
        CREATE INDEX idx_relation_edge_type ON relation_edge(relation_type);
        CREATE INDEX idx_param_group ON parameterization_group(group_id);
        CREATE INDEX idx_form_algebra_output ON form_algebra(output_form);
    """)


def build_minimal_world_model_schema(conn: sqlite3.Connection) -> None:
    """Build the production schema surface required by WorldModel tests."""
    from propstore.sidecar.rules import create_grounded_fact_table

    write_schema_metadata(conn)
    create_tables(conn)
    create_concept_fts_table(conn)
    create_context_tables(conn)
    create_claim_tables(conn)
    create_micropublication_tables(conn)
    create_grounded_fact_table(conn)


def create_context_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS context (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            parameters_json TEXT,
            perspective TEXT
        );

        CREATE TABLE IF NOT EXISTS context_assumption (
            context_id TEXT NOT NULL,
            assumption_cel TEXT NOT NULL,
            seq INTEGER NOT NULL,
            FOREIGN KEY (context_id) REFERENCES context(id)
        );

        CREATE TABLE IF NOT EXISTS context_lifting_rule (
            id TEXT PRIMARY KEY,
            source_context_id TEXT NOT NULL,
            target_context_id TEXT NOT NULL,
            conditions_cel TEXT,
            mode TEXT NOT NULL,
            justification TEXT,
            FOREIGN KEY (source_context_id) REFERENCES context(id),
            FOREIGN KEY (target_context_id) REFERENCES context(id)
        );

        CREATE TABLE IF NOT EXISTS context_lifting_materialization (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT NOT NULL,
            source_context_id TEXT NOT NULL,
            target_context_id TEXT NOT NULL,
            proposition_id TEXT NOT NULL,
            status TEXT NOT NULL,
            exception_id TEXT,
            provenance_json TEXT NOT NULL,
            FOREIGN KEY (rule_id) REFERENCES context_lifting_rule(id),
            FOREIGN KEY (source_context_id) REFERENCES context(id),
            FOREIGN KEY (target_context_id) REFERENCES context(id)
        );

        CREATE INDEX IF NOT EXISTS idx_ctx_assumption ON context_assumption(context_id);
        CREATE INDEX IF NOT EXISTS idx_ctx_lift_source ON context_lifting_rule(source_context_id);
        CREATE INDEX IF NOT EXISTS idx_ctx_lift_target ON context_lifting_rule(target_context_id);
        CREATE INDEX IF NOT EXISTS idx_ctx_lift_mat_target
            ON context_lifting_materialization(target_context_id, proposition_id);
    """)


def create_micropublication_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS micropublication (
            id TEXT PRIMARY KEY,
            context_id TEXT NOT NULL,
            assumptions_json TEXT NOT NULL DEFAULT '[]',
            evidence_json TEXT NOT NULL DEFAULT '[]',
            stance TEXT,
            provenance_json TEXT,
            source_slug TEXT,
            FOREIGN KEY (context_id) REFERENCES context(id)
        );

        CREATE TABLE IF NOT EXISTS micropublication_claim (
            micropublication_id TEXT NOT NULL,
            claim_id TEXT NOT NULL,
            seq INTEGER NOT NULL,
            PRIMARY KEY (micropublication_id, claim_id),
            FOREIGN KEY (micropublication_id) REFERENCES micropublication(id),
            FOREIGN KEY (claim_id) REFERENCES claim_core(id)
        );

        CREATE INDEX IF NOT EXISTS idx_micropub_context ON micropublication(context_id);
        CREATE INDEX IF NOT EXISTS idx_micropub_claim ON micropublication_claim(claim_id);
    """)


def populate_contexts(
    conn: sqlite3.Connection,
    rows: ContextSidecarRows,
) -> None:
    for row in rows.context_rows:
        conn.execute(
            """
            INSERT INTO context (id, name, description, parameters_json, perspective)
            VALUES (?, ?, ?, ?, ?)
            """,
            row.values,
        )

    for row in rows.assumption_rows:
        conn.execute(
            "INSERT INTO context_assumption (context_id, assumption_cel, seq) "
            "VALUES (?, ?, ?)",
            row.values,
        )

    for row in rows.lifting_rule_rows:
        conn.execute(
            """
            INSERT INTO context_lifting_rule (
                id, source_context_id, target_context_id,
                conditions_cel, mode, justification
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            row.values,
        )

    for row in rows.lifting_materialization_rows:
        conn.execute(
            """
            INSERT INTO context_lifting_materialization (
                rule_id, source_context_id, target_context_id,
                proposition_id, status, exception_id, provenance_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            row.values,
        )


def create_build_diagnostics_table(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS build_diagnostics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id TEXT,
            source_kind TEXT NOT NULL,
            source_ref TEXT,
            diagnostic_kind TEXT NOT NULL,
            severity TEXT NOT NULL,
            blocking INTEGER NOT NULL,
            message TEXT NOT NULL,
            file TEXT,
            detail_json TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_build_diagnostics_claim ON build_diagnostics(claim_id);
        CREATE INDEX IF NOT EXISTS idx_build_diagnostics_kind ON build_diagnostics(diagnostic_kind);
        CREATE INDEX IF NOT EXISTS idx_build_diagnostics_source ON build_diagnostics(source_kind, source_ref);
    """)


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

    conn.executescript("""
        CREATE TABLE claim_core (
            id TEXT PRIMARY KEY,
            primary_logical_id TEXT NOT NULL DEFAULT '',
            logical_ids_json TEXT NOT NULL DEFAULT '[]',
            version_id TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            seq INTEGER NOT NULL,
            type TEXT NOT NULL,
            target_concept TEXT,
            source_slug TEXT,
            source_paper TEXT NOT NULL,
            provenance_page INTEGER NOT NULL,
            provenance_json TEXT,
            context_id TEXT,
            premise_kind TEXT NOT NULL DEFAULT 'ordinary',
            branch TEXT,
            build_status TEXT NOT NULL DEFAULT 'ingested',
            stage TEXT,
            promotion_status TEXT,
            FOREIGN KEY (context_id) REFERENCES context(id)
        );

        CREATE TABLE claim_concept_link (
            claim_id TEXT NOT NULL,
            concept_id TEXT NOT NULL,
            role TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            binding_name TEXT,
            PRIMARY KEY (claim_id, role, ordinal, concept_id),
            FOREIGN KEY (claim_id) REFERENCES claim_core(id),
            FOREIGN KEY (concept_id) REFERENCES concept(id)
        );

        CREATE TABLE claim_numeric_payload (
            claim_id TEXT PRIMARY KEY,
            value REAL,
            lower_bound REAL,
            upper_bound REAL,
            uncertainty REAL,
            uncertainty_type TEXT,
            sample_size INTEGER,
            unit TEXT,
            value_si REAL,
            lower_bound_si REAL,
            upper_bound_si REAL,
            FOREIGN KEY (claim_id) REFERENCES claim_core(id)
        );

        CREATE TABLE claim_text_payload (
            claim_id TEXT PRIMARY KEY,
            conditions_cel TEXT,
            statement TEXT,
            expression TEXT,
            sympy_generated TEXT,
            sympy_error TEXT,
            name TEXT,
            measure TEXT,
            listener_population TEXT,
            methodology TEXT,
            notes TEXT,
            description TEXT,
            auto_summary TEXT,
            FOREIGN KEY (claim_id) REFERENCES claim_core(id)
        );

        CREATE TABLE claim_algorithm_payload (
            claim_id TEXT PRIMARY KEY,
            body TEXT,
            canonical_ast TEXT,
            variables_json TEXT,
            algorithm_stage TEXT,
            FOREIGN KEY (claim_id) REFERENCES claim_core(id)
        );

        CREATE TABLE conflict_witness (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id TEXT NOT NULL,
            claim_a_id TEXT NOT NULL,
            claim_b_id TEXT NOT NULL,
            warning_class TEXT NOT NULL,
            conditions_a TEXT,
            conditions_b TEXT,
            value_a TEXT,
            value_b TEXT,
            derivation_chain TEXT
        );

        CREATE TABLE justification (
            id TEXT PRIMARY KEY,
            justification_kind TEXT NOT NULL,
            conclusion_claim_id TEXT NOT NULL,
            premise_claim_ids TEXT NOT NULL,
            source_relation_type TEXT,
            source_claim_id TEXT,
            provenance_json TEXT,
            rule_strength TEXT NOT NULL DEFAULT 'defeasible'
        );

        CREATE TABLE IF NOT EXISTS calibration_counts (
            pass_number INTEGER NOT NULL,
            category TEXT NOT NULL,
            correct_count INTEGER NOT NULL,
            total_count INTEGER NOT NULL,
            PRIMARY KEY (pass_number, category)
        );

        CREATE TABLE build_diagnostics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id TEXT,
            source_kind TEXT NOT NULL,
            source_ref TEXT,
            diagnostic_kind TEXT NOT NULL,
            severity TEXT NOT NULL,
            blocking INTEGER NOT NULL,
            message TEXT NOT NULL,
            file TEXT,
            detail_json TEXT
        );

        CREATE VIRTUAL TABLE claim_fts USING fts5(
            claim_id UNINDEXED,
            statement,
            conditions,
            expression
        );

        CREATE INDEX idx_claim_core_target ON claim_core(target_concept);
        CREATE INDEX idx_claim_concept_link_claim ON claim_concept_link(claim_id);
        CREATE INDEX idx_claim_concept_link_concept ON claim_concept_link(concept_id);
        CREATE INDEX idx_claim_concept_link_role ON claim_concept_link(role);
        CREATE INDEX idx_claim_core_type ON claim_core(type);
        CREATE INDEX idx_claim_core_primary_logical_id ON claim_core(primary_logical_id);
        CREATE INDEX idx_claim_core_build_status ON claim_core(build_status);
        CREATE INDEX idx_claim_core_stage ON claim_core(stage);
        CREATE INDEX idx_claim_core_promotion_status ON claim_core(promotion_status);
        CREATE INDEX idx_claim_algorithm_stage ON claim_algorithm_payload(algorithm_stage);
        CREATE INDEX idx_conflict_witness_concept ON conflict_witness(concept_id);
        CREATE INDEX idx_build_diagnostics_claim ON build_diagnostics(claim_id);
        CREATE INDEX idx_build_diagnostics_kind ON build_diagnostics(diagnostic_kind);
        CREATE INDEX idx_build_diagnostics_source ON build_diagnostics(source_kind, source_ref);
    """)
