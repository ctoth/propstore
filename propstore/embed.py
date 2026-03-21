"""Claim embedding generation and storage via litellm + sqlite-vec."""
from __future__ import annotations

import dataclasses
import struct
import sqlite3
from collections.abc import Callable
from datetime import datetime, timezone


def _require_litellm():
    try:
        import litellm
        return litellm
    except ImportError:
        raise ImportError(
            "litellm is required for embedding commands. "
            "Install with: uv pip install 'propstore[embeddings]'"
        )


def _require_sqlite_vec():
    try:
        import sqlite_vec
        return sqlite_vec
    except ImportError:
        raise ImportError(
            "sqlite-vec is required for embedding commands. "
            "Install with: uv pip install 'propstore[embeddings]'"
        )


def _load_vec_extension(conn: sqlite3.Connection) -> None:
    sqlite_vec = _require_sqlite_vec()
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)


def _sanitize_model_key(model_name: str) -> str:
    """Convert litellm model string to valid SQL identifier fragment."""
    return "".join(c if c.isalnum() else "_" for c in model_name)


def _serialize_float32(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _deserialize_float32(blob: bytes) -> list[float]:
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


def _embedding_text_for_claim(claim: dict) -> str:
    """Build text to embed for a claim. Uses best available field."""
    for field in ("auto_summary", "statement", "expression", "name"):
        val = claim.get(field)
        if val:
            return str(val)
    return claim.get("id", "unknown")


def _ensure_embedding_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS embedding_model (
            model_key TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            dimensions INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS embedding_status (
            model_key TEXT NOT NULL,
            claim_id TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            embedded_at TEXT NOT NULL,
            PRIMARY KEY (model_key, claim_id)
        );
    """)


def _ensure_vec_table(conn: sqlite3.Connection, model_key: str, dimensions: int) -> None:
    table_name = f"claim_vec_{model_key}"
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    ).fetchone()
    if row is None:
        conn.execute(
            f"CREATE VIRTUAL TABLE [{table_name}] USING vec0(embedding float[{dimensions}])"
        )


def embed_claims(
    conn: sqlite3.Connection,
    model_name: str,
    claim_ids: list[str] | None = None,
    batch_size: int = 64,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict:
    """Generate and store embeddings for claims.

    Args:
        conn: Open read-write sidecar connection (with vec extension loaded).
        model_name: litellm model string (e.g. "gemini/gemini-embedding-001").
        claim_ids: Specific claim IDs, or None for all claims.
        batch_size: Texts per API call.
        on_progress: Optional callback(embedded_so_far, total) for progress reporting.

    Returns:
        {"embedded": int, "skipped": int, "errors": int}
    """
    litellm = _require_litellm()
    _ensure_embedding_tables(conn)
    model_key = _sanitize_model_key(model_name)

    # Fetch claims
    if claim_ids:
        placeholders = ",".join("?" for _ in claim_ids)
        rows = conn.execute(
            f"SELECT id, seq, content_hash, auto_summary, statement, expression, name "
            f"FROM claim WHERE id IN ({placeholders})", claim_ids
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, seq, content_hash, auto_summary, statement, expression, name FROM claim"
        ).fetchall()

    claims = [dict(r) for r in rows]

    # Check existing embeddings -- skip unchanged
    existing = {}
    try:
        for r in conn.execute(
            "SELECT claim_id, content_hash FROM embedding_status WHERE model_key=?",
            (model_key,)
        ).fetchall():
            existing[r["claim_id"]] = r["content_hash"]
    except sqlite3.OperationalError:
        pass  # table doesn't exist yet

    to_embed = []
    skipped = 0
    for claim in claims:
        if claim["id"] in existing and existing[claim["id"]] == claim["content_hash"]:
            skipped += 1
            continue
        to_embed.append(claim)

    if not to_embed:
        return {"embedded": 0, "skipped": skipped, "errors": 0}

    # Process in batches
    embedded = 0
    errors = 0
    dimensions = None
    now = datetime.now(timezone.utc).isoformat()

    for i in range(0, len(to_embed), batch_size):
        batch = to_embed[i:i + batch_size]
        texts = [_embedding_text_for_claim(c) for c in batch]

        try:
            response = litellm.embedding(model=model_name, input=texts)
        except Exception as e:
            errors += len(batch)
            continue

        # First successful batch: discover dimensions, register model, create table
        if dimensions is None:
            dimensions = len(response.data[0]["embedding"])
            conn.execute(
                "INSERT OR REPLACE INTO embedding_model VALUES (?, ?, ?, ?)",
                (model_key, model_name, dimensions, now)
            )
            _ensure_vec_table(conn, model_key, dimensions)

        table_name = f"claim_vec_{model_key}"
        for j, claim in enumerate(batch):
            vec = response.data[j]["embedding"]
            seq = claim["seq"]

            # Delete existing vector for this seq if re-embedding
            conn.execute(f"DELETE FROM [{table_name}] WHERE rowid = ?", (seq,))

            # Insert new vector
            conn.execute(
                f"INSERT INTO [{table_name}](rowid, embedding) VALUES (?, ?)",
                (seq, _serialize_float32(vec))
            )

            # Update status
            conn.execute(
                "INSERT OR REPLACE INTO embedding_status VALUES (?, ?, ?, ?)",
                (model_key, claim["id"], claim["content_hash"], now)
            )
            embedded += 1

        if on_progress:
            on_progress(embedded, len(to_embed))

    return {"embedded": embedded, "skipped": skipped, "errors": errors}


def find_similar(
    conn: sqlite3.Connection,
    claim_id: str,
    model_name: str,
    top_k: int = 10,
) -> list[dict]:
    """Find top-k most similar claims by embedding distance."""
    model_key = _sanitize_model_key(model_name)
    table_name = f"claim_vec_{model_key}"

    # Get claim's seq
    row = conn.execute("SELECT seq FROM claim WHERE id = ?", (claim_id,)).fetchone()
    if not row:
        raise ValueError(f"Claim {claim_id} not found")
    seq = row["seq"]

    # Get claim's embedding
    vec_row = conn.execute(
        f"SELECT embedding FROM [{table_name}] WHERE rowid = ?", (seq,)
    ).fetchone()
    if not vec_row:
        raise ValueError(f"No embedding for {claim_id} under model {model_name}")

    # KNN search
    results = conn.execute(
        f"""SELECT v.rowid, v.distance, c.id, c.type, c.auto_summary, c.statement,
                   c.source_paper, c.concept_id
            FROM [{table_name}] v
            JOIN claim c ON c.seq = v.rowid
            WHERE v.embedding MATCH ? AND k = ?
            ORDER BY v.distance""",
        (vec_row["embedding"], top_k + 1)
    ).fetchall()

    return [dict(r) for r in results if r["id"] != claim_id][:top_k]


def get_registered_models(conn: sqlite3.Connection) -> list[dict]:
    """Return all registered embedding models."""
    try:
        return [dict(r) for r in conn.execute(
            "SELECT model_key, model_name, dimensions, created_at FROM embedding_model"
        ).fetchall()]
    except sqlite3.OperationalError:
        return []


def find_similar_agree(
    conn: sqlite3.Connection,
    claim_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Claims similar under ALL stored models (intersection)."""
    models = get_registered_models(conn)
    if not models:
        return []

    result_sets = []
    for m in models:
        try:
            results = find_similar(conn, claim_id, m["model_name"], top_k=top_k * 2)
            result_sets.append({r["id"] for r in results})
        except ValueError:
            continue

    if not result_sets:
        return []

    common_ids = result_sets[0]
    for s in result_sets[1:]:
        common_ids &= s

    # Re-fetch with first model for distances
    all_results = find_similar(conn, claim_id, models[0]["model_name"], top_k=top_k * 2)
    return [r for r in all_results if r["id"] in common_ids][:top_k]


def find_similar_disagree(
    conn: sqlite3.Connection,
    claim_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Claims similar under some models but not others."""
    models = get_registered_models(conn)
    if len(models) < 2:
        return []

    per_model = {}
    for m in models:
        try:
            results = find_similar(conn, claim_id, m["model_name"], top_k=top_k * 2)
            per_model[m["model_name"]] = {r["id"] for r in results}
        except ValueError:
            continue

    if len(per_model) < 2:
        return []

    all_ids = set()
    for ids in per_model.values():
        all_ids |= ids

    # Keep only IDs that appear in some but not all
    disagree_ids = set()
    for cid in all_ids:
        present_in = sum(1 for ids in per_model.values() if cid in ids)
        if 0 < present_in < len(per_model):
            disagree_ids.add(cid)

    # Fetch full data from first model that has each result
    results = []
    first_model = models[0]["model_name"]
    try:
        all_results = find_similar(conn, claim_id, first_model, top_k=top_k * 3)
        for r in all_results:
            if r["id"] in disagree_ids:
                # Annotate with which models found it similar
                r["similar_in"] = [mn for mn, ids in per_model.items() if r["id"] in ids]
                r["not_similar_in"] = [mn for mn, ids in per_model.items() if r["id"] not in ids]
                results.append(r)
    except ValueError:
        pass

    return results[:top_k]


@dataclasses.dataclass
class EmbeddingSnapshot:
    models: list[dict]
    statuses: list[dict]
    vectors: dict[str, list[tuple[int, str, bytes]]]  # model_key -> [(seq, claim_id, blob)]


@dataclasses.dataclass
class RestoreReport:
    restored: int = 0
    stale: int = 0
    orphaned: int = 0


def extract_embeddings(conn: sqlite3.Connection) -> EmbeddingSnapshot | None:
    """Extract all embedding data before sidecar rebuild."""
    try:
        models = [dict(r) for r in conn.execute("SELECT * FROM embedding_model").fetchall()]
    except sqlite3.OperationalError:
        return None

    if not models:
        return None

    statuses = [dict(r) for r in conn.execute("SELECT * FROM embedding_status").fetchall()]

    vectors = {}
    for m in models:
        table_name = f"claim_vec_{m['model_key']}"
        try:
            rows = conn.execute(
                f"""SELECT v.rowid, es.claim_id, v.embedding
                    FROM [{table_name}] v
                    JOIN embedding_status es ON es.model_key = ?
                    JOIN claim c ON c.seq = v.rowid AND c.id = es.claim_id
                    WHERE es.model_key = ?""",
                (m["model_key"], m["model_key"])
            ).fetchall()
            vectors[m["model_key"]] = [(r[0], r[1], r[2]) for r in rows]
        except sqlite3.OperationalError:
            vectors[m["model_key"]] = []

    return EmbeddingSnapshot(models=models, statuses=statuses, vectors=vectors)


def restore_embeddings(
    conn: sqlite3.Connection, snapshot: EmbeddingSnapshot
) -> RestoreReport:
    """Restore embeddings after sidecar rebuild. Skips stale/orphaned claims."""
    _ensure_embedding_tables(conn)
    report = RestoreReport()

    # Build claim_id -> (seq, content_hash) map from new sidecar
    current_claims = {}
    for r in conn.execute("SELECT id, seq, content_hash FROM claim").fetchall():
        current_claims[r["id"]] = (r["seq"], r["content_hash"])

    # Build status lookup: (model_key, claim_id) -> content_hash_at_embed_time
    status_lookup = {}
    for s in snapshot.statuses:
        status_lookup[(s["model_key"], s["claim_id"])] = s["content_hash"]

    for m in snapshot.models:
        model_key = m["model_key"]
        dimensions = m["dimensions"]

        conn.execute(
            "INSERT OR REPLACE INTO embedding_model VALUES (?, ?, ?, ?)",
            (model_key, m["model_name"], dimensions, m["created_at"])
        )
        _ensure_vec_table(conn, model_key, dimensions)

        table_name = f"claim_vec_{model_key}"

        for _old_seq, claim_id, blob in snapshot.vectors.get(model_key, []):
            if claim_id not in current_claims:
                report.orphaned += 1
                continue

            new_seq, current_hash = current_claims[claim_id]
            embed_hash = status_lookup.get((model_key, claim_id), "")

            if current_hash != embed_hash:
                report.stale += 1
                continue

            # Claim still exists and content unchanged -- restore
            conn.execute(
                f"INSERT INTO [{table_name}](rowid, embedding) VALUES (?, ?)",
                (new_seq, blob)
            )
            conn.execute(
                "INSERT OR REPLACE INTO embedding_status VALUES (?, ?, ?, ?)",
                (model_key, claim_id, current_hash,
                 next((s["embedded_at"] for s in snapshot.statuses
                       if s["model_key"] == model_key and s["claim_id"] == claim_id), ""))
            )
            report.restored += 1

    return report
