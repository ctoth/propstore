from __future__ import annotations

import sqlite3
from pathlib import Path

from propstore.sidecar.embedding_store import ensure_embedding_tables


def test_embedding_identity_distinguishes_punctuation_collisions() -> None:
    from propstore.heuristic.embedding_identity import EmbeddingModelIdentity

    identities = [
        EmbeddingModelIdentity(
            provider="litellm",
            model_name=model_name,
            model_version="2026-04",
            content_digest="same-provider-spec",
        )
        for model_name in ("a/b", "a-b", "a_b", "a b")
    ]

    assert len(set(identities)) == 4
    assert len({identity.identity_hash for identity in identities}) == 4


def test_sidecar_embedding_registry_stores_typed_identity_rows() -> None:
    from propstore.heuristic.embedding_identity import EmbeddingModelIdentity

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_embedding_tables(conn)

    identities = [
        EmbeddingModelIdentity(
            provider="litellm",
            model_name=model_name,
            model_version="2026-04",
            content_digest="same-provider-spec",
        )
        for model_name in ("a/b", "a-b", "a_b", "a b")
    ]

    for identity in identities:
        conn.execute(
            """
            INSERT OR IGNORE INTO embedding_model (
                model_identity_hash,
                provider,
                model_name,
                model_version,
                content_digest,
                dimensions,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                identity.identity_hash,
                identity.provider,
                identity.model_name,
                identity.model_version,
                identity.content_digest,
                2,
                "2026-04-29T00:00:00+00:00",
            ),
        )

    duplicate = identities[0]
    conn.execute(
        """
        INSERT OR IGNORE INTO embedding_model (
            model_identity_hash,
            provider,
            model_name,
            model_version,
            content_digest,
            dimensions,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            duplicate.identity_hash,
            duplicate.provider,
            duplicate.model_name,
            duplicate.model_version,
            duplicate.content_digest,
            2,
            "2026-04-29T00:00:00+00:00",
        ),
    )

    rows = conn.execute(
        """
        SELECT model_identity_hash, provider, model_name, model_version, content_digest
        FROM embedding_model
        ORDER BY model_name
        """
    ).fetchall()

    assert len(rows) == 4
    assert {row["model_name"] for row in rows} == {"a/b", "a-b", "a_b", "a b"}
    assert len({row["model_identity_hash"] for row in rows}) == 4
    assert "model_key" not in {
        row["name"] for row in conn.execute("PRAGMA table_info(embedding_model)")
    }


def test_embedding_sanitizer_deleted() -> None:
    embed_source = Path("propstore/heuristic/embed.py").read_text()

    assert "_sanitize_model_key" not in embed_source

