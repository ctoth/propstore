"""Shared test helpers for propstore tests.

Plain functions (not pytest fixtures) since callers invoke them directly.
"""

from __future__ import annotations

import sqlite3


def create_argumentation_schema(conn: sqlite3.Connection) -> None:
    """Create minimal claim + claim_stance tables for testing."""
    conn.executescript("""
        CREATE TABLE claim (
            id TEXT PRIMARY KEY,
            type TEXT,
            concept_id TEXT,
            value REAL,
            sample_size INTEGER,
            uncertainty REAL,
            confidence REAL,
            uncertainty_type TEXT,
            unit TEXT,
            conditions_cel TEXT,
            source_paper TEXT NOT NULL DEFAULT 'test',
            provenance_page INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE claim_stance (
            claim_id TEXT NOT NULL,
            target_claim_id TEXT NOT NULL,
            stance_type TEXT NOT NULL,
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
            FOREIGN KEY (claim_id) REFERENCES claim(id),
            FOREIGN KEY (target_claim_id) REFERENCES claim(id),
            CHECK (
                opinion_belief IS NULL
                OR abs(opinion_belief + opinion_disbelief + opinion_uncertainty - 1.0) < 0.01
            )
        );
        CREATE TABLE IF NOT EXISTS conflicts (
            concept_id TEXT NOT NULL,
            claim_a_id TEXT NOT NULL,
            claim_b_id TEXT NOT NULL,
            warning_class TEXT NOT NULL,
            conditions_a TEXT,
            conditions_b TEXT,
            value_a TEXT,
            value_b TEXT,
            derivation_chain TEXT,
            FOREIGN KEY (claim_a_id) REFERENCES claim(id),
            FOREIGN KEY (claim_b_id) REFERENCES claim(id)
        );
    """)


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
