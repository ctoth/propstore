"""Shared test helpers for propstore tests.

Plain functions (not pytest fixtures) since callers invoke them directly.
"""

from __future__ import annotations

import sqlite3


def create_argumentation_schema(conn: sqlite3.Connection) -> None:
    """Create minimal normalized claim/relation/conflict tables for testing."""
    conn.executescript("""
        CREATE TABLE claim_core (
            id TEXT PRIMARY KEY,
            type TEXT,
            concept_id TEXT,
            target_concept TEXT,
            seq INTEGER,
            content_hash TEXT,
            source_paper TEXT NOT NULL DEFAULT 'test',
            provenance_page INTEGER NOT NULL DEFAULT 1,
            provenance_json TEXT,
            context_id TEXT
        );

        CREATE TABLE claim_numeric_payload (
            claim_id TEXT PRIMARY KEY,
            value REAL,
            sample_size INTEGER,
            uncertainty REAL,
            confidence REAL,
            uncertainty_type TEXT,
            unit TEXT
        );

        CREATE TABLE claim_text_payload (
            claim_id TEXT PRIMARY KEY,
            conditions_cel TEXT,
            statement TEXT,
            expression TEXT,
            auto_summary TEXT
        );

        CREATE TABLE claim_algorithm_payload (
            claim_id TEXT PRIMARY KEY,
            body TEXT,
            canonical_ast TEXT,
            variables_json TEXT,
            stage TEXT
        );

        CREATE TABLE relation_edge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_kind TEXT NOT NULL,
            source_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            target_kind TEXT NOT NULL,
            target_id TEXT NOT NULL,
            target_justification_id TEXT,
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
            opinion_base_rate REAL DEFAULT 0.5,
            CHECK(opinion_belief IS NULL OR (opinion_belief >= 0 AND opinion_belief <= 1)),
            CHECK(opinion_disbelief IS NULL OR (opinion_disbelief >= 0 AND opinion_disbelief <= 1)),
            CHECK(opinion_uncertainty IS NULL OR (opinion_uncertainty >= 0 AND opinion_uncertainty <= 1)),
            CHECK(opinion_base_rate IS NULL OR (opinion_base_rate > 0 AND opinion_base_rate < 1)),
            CHECK(opinion_belief IS NULL OR ABS(opinion_belief + opinion_disbelief + opinion_uncertainty - 1.0) <= 1e-6)
        );

        CREATE TABLE IF NOT EXISTS conflict_witness (
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
    """)


def insert_claim(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    claim_type: str | None = None,
    concept_id: str | None = None,
    target_concept: str | None = None,
    value: float | None = None,
    sample_size: int | None = None,
    uncertainty: float | None = None,
    confidence: float | None = None,
    uncertainty_type: str | None = None,
    unit: str | None = None,
    conditions_cel: str | None = None,
    statement: str | None = None,
    expression: str | None = None,
    auto_summary: str | None = None,
    source_paper: str = "test",
    provenance_page: int = 1,
) -> None:
    conn.execute(
        """
        INSERT INTO claim_core (
            id, type, concept_id, target_concept, seq, content_hash,
            source_paper, provenance_page, provenance_json, context_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            claim_type,
            concept_id,
            target_concept,
            None,
            None,
            source_paper,
            provenance_page,
            None,
            None,
        ),
    )
    conn.execute(
        """
        INSERT INTO claim_numeric_payload (
            claim_id, value, sample_size, uncertainty, confidence, uncertainty_type, unit
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (claim_id, value, sample_size, uncertainty, confidence, uncertainty_type, unit),
    )
    conn.execute(
        """
        INSERT INTO claim_text_payload (
            claim_id, conditions_cel, statement, expression, auto_summary
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (claim_id, conditions_cel, statement, expression, auto_summary),
    )


def insert_stance(
    conn: sqlite3.Connection,
    claim_id: str,
    target_claim_id: str,
    stance_type: str,
    *,
    target_justification_id: str | None = None,
    strength: str | None = None,
    conditions_differ: str | None = None,
    note: str | None = None,
    resolution_method: str | None = None,
    resolution_model: str | None = None,
    embedding_model: str | None = None,
    embedding_distance: float | None = None,
    pass_number: int | None = None,
    confidence: float | None = None,
    opinion_belief: float | None = None,
    opinion_disbelief: float | None = None,
    opinion_uncertainty: float | None = None,
    opinion_base_rate: float | None = 0.5,
) -> None:
    conn.execute(
        """
        INSERT INTO relation_edge (
            source_kind, source_id, relation_type, target_kind, target_id,
            target_justification_id,
            strength, conditions_differ, note, resolution_method, resolution_model,
            embedding_model, embedding_distance, pass_number, confidence,
            opinion_belief, opinion_disbelief, opinion_uncertainty, opinion_base_rate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "claim",
            claim_id,
            stance_type,
            "claim",
            target_claim_id,
            target_justification_id,
            strength,
            conditions_differ,
            note,
            resolution_method,
            resolution_model,
            embedding_model,
            embedding_distance,
            pass_number,
            confidence,
            opinion_belief,
            opinion_disbelief,
            opinion_uncertainty,
            opinion_base_rate,
        ),
    )


def insert_conflict(
    conn: sqlite3.Connection,
    *,
    concept_id: str,
    claim_a_id: str,
    claim_b_id: str,
    warning_class: str,
    conditions_a: str | None = None,
    conditions_b: str | None = None,
    value_a: str | None = None,
    value_b: str | None = None,
    derivation_chain: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO conflict_witness (
            concept_id, claim_a_id, claim_b_id, warning_class,
            conditions_a, conditions_b, value_a, value_b, derivation_chain
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            concept_id,
            claim_a_id,
            claim_b_id,
            warning_class,
            conditions_a,
            conditions_b,
            value_a,
            value_b,
            derivation_chain,
        ),
    )


def make_parameter_claim(id, concept_id, value, unit="Hz", *, page=1, paper="test_paper", **kwargs):
    """Build a minimal parameter claim dict for testing.

    Supports keyword-only extras via **kwargs (e.g. notes, conditions).
    """
    c = {
        "id": id,
        "type": "parameter",
        "concept": concept_id,
        "value": value,
        "unit": unit,
        "provenance": {"paper": paper, "page": page},
    }
    c.update(kwargs)
    return c


def make_concept_registry():
    """Build a mock concept registry for testing.

    Returns 3 concepts covering frequency, pressure, and category forms.
    """
    return {
        "concept1": {
            "id": "concept1",
            "canonical_name": "fundamental_frequency",
            "form": "frequency",
            "status": "accepted",
            "definition": "F0",
        },
        "concept2": {
            "id": "concept2",
            "canonical_name": "subglottal_pressure",
            "form": "pressure",
            "status": "accepted",
            "definition": "Ps",
        },
        "concept3": {
            "id": "concept3",
            "canonical_name": "task",
            "form": "category",
            "form_parameters": {"values": ["speech", "singing", "whisper"], "extensible": True},
            "status": "accepted",
            "definition": "Task type",
        },
    }
