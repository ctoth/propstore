from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from propstore.repository import Repository
from propstore.sidecar.schema import (
    create_claim_tables,
    create_context_tables,
    create_tables,
    write_schema_metadata,
)


@dataclass(frozen=True)
class WebDemoRepositoryFixture:
    repo: Repository
    focus_claim_id: str
    supporter_claim_id: str
    attacker_claim_id: str
    concept_id: str


def seed_web_demo_repository(tmp_path: Path) -> WebDemoRepositoryFixture:
    repo = Repository.init(tmp_path / "web-demo-repo")
    repo.sidecar_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(repo.sidecar_path)
    try:
        create_tables(conn)
        create_claim_tables(conn)
        create_context_tables(conn)
        write_schema_metadata(conn)
        _create_concept_fts(conn)
        _seed_rows(conn)
        conn.commit()
    finally:
        conn.close()
    return WebDemoRepositoryFixture(
        repo=repo,
        focus_claim_id="demo_focus",
        supporter_claim_id="demo_supporter",
        attacker_claim_id="demo_attacker",
        concept_id="demo_concept",
    )


def _create_concept_fts(conn: sqlite3.Connection) -> None:
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


def _seed_rows(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT INTO source (
            slug, source_id, kind, origin_type, origin_value, prior_base_rate
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("demo_source", "demo_source", "academic_paper", "manual", "web demo fixture", 0.5),
    )
    conn.execute(
        """
        INSERT INTO concept (
            id, primary_logical_id, logical_ids_json, version_id, content_hash,
            seq, canonical_name, status, domain, definition, kind_type, form,
            is_dimensionless, unit_symbol
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "demo_concept",
            "demo:uncertain_temperature",
            '[{"namespace":"demo","value":"uncertain_temperature"}]',
            "demo-concept-version",
            "demo-concept-hash",
            1,
            "uncertain temperature",
            "accepted",
            "demo",
            "A demo quantity used by the first web fixture.",
            "quantity",
            "temperature",
            0,
            "K",
        ),
    )
    conn.execute(
        """
        INSERT INTO form (
            name, kind, unit_symbol, is_dimensionless, dimensions
        ) VALUES (?, ?, ?, ?, ?)
        """,
        ("temperature", "quantity", "K", 0, '{"temperature":1}'),
    )
    conn.execute(
        """
        INSERT INTO concept_fts (
            concept_id, canonical_name, aliases, definition, conditions
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            "demo_concept",
            "uncertain temperature",
            "",
            "A demo quantity used by the first web fixture.",
            "",
        ),
    )
    _insert_claim(
        conn,
        claim_id="demo_focus",
        logical_id="demo:focus",
        claim_type="parameter",
        value=295.0,
        uncertainty=0.25,
        uncertainty_type="stddev",
        sample_size=8,
        build_status="blocked",
    )
    _insert_claim(
        conn,
        claim_id="demo_supporter",
        logical_id="demo:supporter",
        claim_type="measurement",
        value=294.8,
        uncertainty=0.2,
        uncertainty_type="stddev",
        sample_size=12,
        build_status="ingested",
    )
    _insert_claim(
        conn,
        claim_id="demo_attacker",
        logical_id="demo:attacker",
        claim_type="parameter",
        value=301.0,
        uncertainty=0.1,
        uncertainty_type="stddev",
        sample_size=20,
        build_status="ingested",
    )
    conn.execute(
        """
        INSERT INTO relation_edge (
            source_kind, source_id, relation_type, target_kind, target_id,
            confidence, opinion_belief, opinion_disbelief, opinion_uncertainty,
            opinion_base_rate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("claim", "demo_supporter", "supports", "claim", "demo_focus", 0.85, 0.7, 0.1, 0.2, 0.5),
    )
    conn.execute(
        """
        INSERT INTO relation_edge (
            source_kind, source_id, relation_type, target_kind, target_id,
            confidence, opinion_belief, opinion_disbelief, opinion_uncertainty,
            opinion_base_rate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("claim", "demo_attacker", "rebuts", "claim", "demo_focus", 0.8, 0.65, 0.15, 0.2, 0.5),
    )
    conn.execute(
        """
        INSERT INTO build_diagnostics (
            claim_id, source_kind, source_ref, diagnostic_kind, severity,
            blocking, message
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "demo_focus",
            "claim",
            "demo_focus",
            "fixture_policy_blocked",
            "warning",
            1,
            "Demo fixture marks the focus claim blocked to exercise render policy state.",
        ),
    )


def _insert_claim(
    conn: sqlite3.Connection,
    *,
    claim_id: str,
    logical_id: str,
    claim_type: str = "parameter",
    value: float,
    uncertainty: float,
    uncertainty_type: str,
    sample_size: int,
    build_status: str,
) -> None:
    conn.execute(
        """
        INSERT INTO claim_core (
            id, primary_logical_id, logical_ids_json, version_id, content_hash,
            seq, type, source_slug, source_paper, provenance_page,
            premise_kind, branch, build_status, stage
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            logical_id,
            f'[{{"namespace":"demo","value":"{logical_id.split(":", 1)[1]}"}}]',
            f"{claim_id}-version",
            f"{claim_id}-hash",
            1,
            claim_type,
            "demo_source",
            "demo_source",
            7,
            "ordinary",
            "master",
            build_status,
            "final",
        ),
    )
    conn.execute(
        """
        INSERT INTO claim_concept_link (
            claim_id, concept_id, role, ordinal, binding_name
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (claim_id, "demo_concept", "output", 0, None),
    )
    conn.execute(
        """
        INSERT INTO claim_numeric_payload (
            claim_id, value, uncertainty, uncertainty_type, sample_size, unit,
            value_si
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (claim_id, value, uncertainty, uncertainty_type, sample_size, "K", value),
    )
