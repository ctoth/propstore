from __future__ import annotations

import json
import sqlite3
from sqlite3 import Connection
from dataclasses import dataclass
from pathlib import Path

import msgspec

from propstore.opinion import Opinion
from propstore.repository import Repository
from propstore.compiler.workflows import build_repository_world_store


@dataclass(frozen=True)
class WebDemoRepositoryFixture:
    repo: Repository
    sidecar_path: Path
    focus_claim_id: str
    supporter_claim_id: str
    attacker_claim_id: str
    concept_id: str


def seed_web_demo_repository(tmp_path: Path) -> WebDemoRepositoryFixture:
    repo = Repository.init(tmp_path / "web-demo-repo")
    handle, _ = build_repository_world_store(repo, force=True)
    conn = sqlite3.connect(handle.path)
    try:
        _seed_rows(conn)
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("PRAGMA journal_mode=DELETE")
    finally:
        conn.close()
    return WebDemoRepositoryFixture(
        repo=repo,
        sidecar_path=handle.path,
        focus_claim_id="demo_focus",
        supporter_claim_id="demo_supporter",
        attacker_claim_id="demo_attacker",
        concept_id="demo_concept",
    )


def _seed_rows(conn: Connection) -> None:
    conn.execute(
        """
        INSERT INTO source (
            slug, source_id, kind, origin, trust, quality, derived_from, artifact_code
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "demo_source",
            "demo_source",
            "academic_paper",
            json.dumps({"type": "manual", "value": "web demo fixture"}),
            json.dumps(
                {
                    "status": "stated",
                    "prior_base_rate": {"b": 0.0, "d": 0.0, "u": 1.0, "a": 0.5},
                }
            ),
            None,
            None,
            None,
        ),
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
            confidence, opinion
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "claim",
            "demo_supporter",
            "supports",
            "claim",
            "demo_focus",
            0.85,
            msgspec.json.encode(Opinion(0.7, 0.1, 0.2, 0.5)).decode(),
        ),
    )
    conn.execute(
        """
        INSERT INTO relation_edge (
            source_kind, source_id, relation_type, target_kind, target_id,
            confidence, opinion
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "claim",
            "demo_attacker",
            "rebuts",
            "claim",
            "demo_focus",
            0.8,
            msgspec.json.encode(Opinion(0.65, 0.15, 0.2, 0.5)).decode(),
        ),
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
