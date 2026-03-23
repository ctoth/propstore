"""Claim embedding generation and storage via litellm + sqlite-vec."""
from __future__ import annotations

import dataclasses
import logging
import struct
import sqlite3
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any


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
        CREATE TABLE IF NOT EXISTS concept_embedding_status (
            model_key TEXT NOT NULL,
            concept_id TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            embedded_at TEXT NOT NULL,
            PRIMARY KEY (model_key, concept_id)
        );
    """)


def _embedding_text_for_concept(concept: dict, aliases: list[dict]) -> str:
    """Build text to embed for a concept."""
    name = concept.get("canonical_name", "")
    definition = concept.get("definition", "")
    alias_names = [a["alias_name"] for a in aliases]
    parts = [name]
    if alias_names:
        parts.append(f"(also known as: {', '.join(alias_names)})")
    if definition:
        parts.append(f"— {definition}")
    return " ".join(parts)


def _ensure_vec_table(
    conn: sqlite3.Connection, model_key: str, dimensions: int, prefix: str = "claim_vec"
) -> None:
    table_name = f"{prefix}_{model_key}"
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    ).fetchone()
    if row is None:
        conn.execute(
            f"CREATE VIRTUAL TABLE [{table_name}] USING vec0(embedding float[{dimensions}])"
        )


@dataclasses.dataclass(frozen=True)
class _EmbedConfig:
    """Configuration that differs between claim and concept embedding."""
    entity_table: str              # "claim" or "concept"
    select_columns: str            # columns to SELECT from entity table
    status_table: str              # "embedding_status" or "concept_embedding_status"
    status_id_column: str          # "claim_id" or "concept_id"
    vec_prefix: str                # "claim_vec" or "concept_vec"
    text_builder: Callable[..., str]  # function to build embedding text
    pre_batch_hook: Callable[[sqlite3.Connection, list[dict]], Any] | None = None


_CLAIM_CONFIG = _EmbedConfig(
    entity_table="claim",
    select_columns="id, seq, content_hash, auto_summary, statement, expression, name",
    status_table="embedding_status",
    status_id_column="claim_id",
    vec_prefix="claim_vec",
    text_builder=lambda entity, _extra: _embedding_text_for_claim(entity),
)


def _concept_pre_batch_hook(conn: sqlite3.Connection, to_embed: list[dict]) -> dict[str, list[dict]]:
    """Fetch aliases for all concepts to embed."""
    alias_map: dict[str, list[dict]] = {}
    for concept in to_embed:
        alias_rows = conn.execute(
            "SELECT alias_name FROM alias WHERE concept_id = ?", (concept["id"],)
        ).fetchall()
        alias_map[concept["id"]] = [dict(r) for r in alias_rows]
    return alias_map


_CONCEPT_CONFIG = _EmbedConfig(
    entity_table="concept",
    select_columns="id, seq, canonical_name, definition, content_hash",
    status_table="concept_embedding_status",
    status_id_column="concept_id",
    vec_prefix="concept_vec",
    text_builder=lambda entity, extra: _embedding_text_for_concept(entity, extra.get(entity["id"], [])),
    pre_batch_hook=_concept_pre_batch_hook,
)


def _embed_entities(
    conn: sqlite3.Connection,
    model_name: str,
    config: _EmbedConfig,
    entity_ids: list[str] | None = None,
    batch_size: int = 64,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict:
    """Generic embedding function for claims or concepts.

    Returns:
        {"embedded": int, "skipped": int, "errors": int}
    """
    litellm = _require_litellm()
    _ensure_embedding_tables(conn)
    model_key = _sanitize_model_key(model_name)

    # Fetch entities
    if entity_ids:
        placeholders = ",".join("?" for _ in entity_ids)
        rows = conn.execute(
            f"SELECT {config.select_columns} "
            f"FROM {config.entity_table} WHERE id IN ({placeholders})", entity_ids
        ).fetchall()
    else:
        rows = conn.execute(
            f"SELECT {config.select_columns} FROM {config.entity_table}"
        ).fetchall()

    entities = [dict(r) for r in rows]

    # Check existing embeddings -- skip unchanged
    existing = {}
    try:
        for r in conn.execute(
            f"SELECT {config.status_id_column}, content_hash FROM {config.status_table} WHERE model_key=?",
            (model_key,)
        ).fetchall():
            existing[r[config.status_id_column]] = r["content_hash"]
    except sqlite3.OperationalError:
        pass  # table doesn't exist yet

    to_embed = []
    skipped = 0
    for entity in entities:
        if entity["id"] in existing and existing[entity["id"]] == entity["content_hash"]:
            skipped += 1
            continue
        to_embed.append(entity)

    if not to_embed:
        return {"embedded": 0, "skipped": skipped, "errors": 0}

    # Run pre-batch hook (e.g. fetch aliases for concepts)
    extra = config.pre_batch_hook(conn, to_embed) if config.pre_batch_hook else None

    # Process in batches
    embedded = 0
    errors = 0
    dimensions = None
    now = datetime.now(timezone.utc).isoformat()

    for i in range(0, len(to_embed), batch_size):
        batch = to_embed[i:i + batch_size]
        texts = [config.text_builder(e, extra) for e in batch]

        try:
            response = litellm.embedding(model=model_name, input=texts)
        except (ConnectionError, TimeoutError, OSError, ValueError) as exc:
            logging.warning("Embedding API call failed for batch %d: %s", i, exc)
            errors += len(batch)
            continue

        # First successful batch: discover dimensions, register model, create table
        if dimensions is None:
            dimensions = len(response.data[0]["embedding"])
            conn.execute(
                "INSERT OR REPLACE INTO embedding_model VALUES (?, ?, ?, ?)",
                (model_key, model_name, dimensions, now)
            )
            _ensure_vec_table(conn, model_key, dimensions, prefix=config.vec_prefix)

        table_name = f"{config.vec_prefix}_{model_key}"
        for j, entity in enumerate(batch):
            vec = response.data[j]["embedding"]
            seq = entity["seq"]

            conn.execute(f"DELETE FROM [{table_name}] WHERE rowid = ?", (seq,))
            conn.execute(
                f"INSERT INTO [{table_name}](rowid, embedding) VALUES (?, ?)",
                (seq, _serialize_float32(vec))
            )
            conn.execute(
                f"INSERT OR REPLACE INTO {config.status_table} VALUES (?, ?, ?, ?)",
                (model_key, entity["id"], entity["content_hash"], now)
            )
            embedded += 1

        if on_progress:
            on_progress(embedded, len(to_embed))

    return {"embedded": embedded, "skipped": skipped, "errors": errors}


def embed_claims(
    conn: sqlite3.Connection,
    model_name: str,
    claim_ids: list[str] | None = None,
    batch_size: int = 64,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict:
    """Generate and store embeddings for claims."""
    return _embed_entities(conn, model_name, _CLAIM_CONFIG, claim_ids, batch_size, on_progress)


@dataclasses.dataclass(frozen=True)
class _FindConfig:
    """Configuration for find-similar queries."""
    vec_prefix: str                # "claim_vec" or "concept_vec"
    entity_table: str              # "claim" or "concept"
    join_columns: str              # columns to SELECT from entity table in KNN join
    resolve_id: Callable[[sqlite3.Connection, str], tuple[str, int]]


def _resolve_claim_id(conn: sqlite3.Connection, claim_id: str) -> tuple[str, int]:
    """Resolve a claim ID to (id, seq)."""
    row = conn.execute("SELECT id, seq FROM claim WHERE id = ?", (claim_id,)).fetchone()
    if not row:
        raise ValueError(f"Claim {claim_id} not found")
    return row["id"], row["seq"]


_FIND_CLAIM_CONFIG = _FindConfig(
    vec_prefix="claim_vec",
    entity_table="claim",
    join_columns="c.id, c.type, c.auto_summary, c.statement, c.source_paper, c.concept_id",
    resolve_id=_resolve_claim_id,
)

def _resolve_concept_id(conn: sqlite3.Connection, concept_id_or_name: str) -> tuple[str, int]:
    """Resolve a concept ID or canonical_name to (id, seq).

    Tries exact ID match first, then canonical_name lookup.
    Raises ValueError if not found.
    """
    row = conn.execute(
        "SELECT id, seq FROM concept WHERE id = ? OR canonical_name = ?",
        (concept_id_or_name, concept_id_or_name),
    ).fetchone()
    if not row:
        raise ValueError(f"Concept {concept_id_or_name} not found")
    return row["id"], row["seq"]


_FIND_CONCEPT_CONFIG = _FindConfig(
    vec_prefix="concept_vec",
    entity_table="concept",
    join_columns="c.id, c.canonical_name, c.definition",
    resolve_id=_resolve_concept_id,
)


def _find_similar_entities(
    conn: sqlite3.Connection,
    entity_id: str,
    model_name: str,
    config: _FindConfig,
    top_k: int = 10,
) -> list[dict]:
    """Generic find-similar for claims or concepts."""
    model_key = _sanitize_model_key(model_name)
    table_name = f"{config.vec_prefix}_{model_key}"

    resolved_id, seq = config.resolve_id(conn, entity_id)

    vec_row = conn.execute(
        f"SELECT embedding FROM [{table_name}] WHERE rowid = ?", (seq,)
    ).fetchone()
    if not vec_row:
        raise ValueError(f"No embedding for {resolved_id} under model {model_name}")

    results = conn.execute(
        f"""SELECT v.rowid, v.distance, {config.join_columns}
            FROM [{table_name}] v
            JOIN {config.entity_table} c ON c.seq = v.rowid
            WHERE v.embedding MATCH ? AND k = ?
            ORDER BY v.distance""",
        (vec_row["embedding"], top_k + 1)
    ).fetchall()

    return [dict(r) for r in results if r["id"] != resolved_id][:top_k]


def find_similar(
    conn: sqlite3.Connection,
    claim_id: str,
    model_name: str,
    top_k: int = 10,
) -> list[dict]:
    """Find top-k most similar claims by embedding distance."""
    return _find_similar_entities(conn, claim_id, model_name, _FIND_CLAIM_CONFIG, top_k)


def get_registered_models(conn: sqlite3.Connection) -> list[dict]:
    """Return all registered embedding models."""
    try:
        return [dict(r) for r in conn.execute(
            "SELECT model_key, model_name, dimensions, created_at FROM embedding_model"
        ).fetchall()]
    except sqlite3.OperationalError:
        return []


def _find_similar_agree_generic(
    conn: sqlite3.Connection,
    entity_id: str,
    config: _FindConfig,
    top_k: int = 10,
) -> list[dict]:
    """Entities similar under ALL stored models (intersection)."""
    models = get_registered_models(conn)
    if not models:
        return []

    result_sets = []
    for m in models:
        try:
            results = _find_similar_entities(conn, entity_id, m["model_name"], config, top_k=top_k * 2)
            result_sets.append({r["id"] for r in results})
        except ValueError:
            continue

    if not result_sets:
        return []

    common_ids = result_sets[0]
    for s in result_sets[1:]:
        common_ids &= s

    all_results = _find_similar_entities(conn, entity_id, models[0]["model_name"], config, top_k=top_k * 2)
    return [r for r in all_results if r["id"] in common_ids][:top_k]


def _find_similar_disagree_generic(
    conn: sqlite3.Connection,
    entity_id: str,
    config: _FindConfig,
    top_k: int = 10,
) -> list[dict]:
    """Entities similar under some models but not others."""
    models = get_registered_models(conn)
    if len(models) < 2:
        return []

    per_model = {}
    for m in models:
        try:
            results = _find_similar_entities(conn, entity_id, m["model_name"], config, top_k=top_k * 2)
            per_model[m["model_name"]] = {r["id"] for r in results}
        except ValueError:
            continue

    if len(per_model) < 2:
        return []

    all_ids = set()
    for ids in per_model.values():
        all_ids |= ids

    disagree_ids = set()
    for cid in all_ids:
        present_in = sum(1 for ids in per_model.values() if cid in ids)
        if 0 < present_in < len(per_model):
            disagree_ids.add(cid)

    results = []
    first_model = models[0]["model_name"]
    try:
        all_results = _find_similar_entities(conn, entity_id, first_model, config, top_k=top_k * 3)
        for r in all_results:
            if r["id"] in disagree_ids:
                r["similar_in"] = [mn for mn, ids in per_model.items() if r["id"] in ids]
                r["not_similar_in"] = [mn for mn, ids in per_model.items() if r["id"] not in ids]
                results.append(r)
    except ValueError:
        pass

    return results[:top_k]


def find_similar_agree(
    conn: sqlite3.Connection,
    claim_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Claims similar under ALL stored models (intersection)."""
    return _find_similar_agree_generic(conn, claim_id, _FIND_CLAIM_CONFIG, top_k)


def find_similar_disagree(
    conn: sqlite3.Connection,
    claim_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Claims similar under some models but not others."""
    return _find_similar_disagree_generic(conn, claim_id, _FIND_CLAIM_CONFIG, top_k)


def embed_concepts(
    conn: sqlite3.Connection,
    model_name: str,
    concept_ids: list[str] | None = None,
    batch_size: int = 64,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict:
    """Generate and store embeddings for concepts."""
    return _embed_entities(conn, model_name, _CONCEPT_CONFIG, concept_ids, batch_size, on_progress)


def find_similar_concepts(
    conn: sqlite3.Connection,
    concept_id: str,
    model_name: str,
    top_k: int = 10,
) -> list[dict]:
    """Find top-k most similar concepts by embedding distance."""
    return _find_similar_entities(conn, concept_id, model_name, _FIND_CONCEPT_CONFIG, top_k)


def find_similar_concepts_agree(
    conn: sqlite3.Connection,
    concept_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Concepts similar under ALL stored models (intersection)."""
    return _find_similar_agree_generic(conn, concept_id, _FIND_CONCEPT_CONFIG, top_k)


def find_similar_concepts_disagree(
    conn: sqlite3.Connection,
    concept_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Concepts similar under some models but not others."""
    return _find_similar_disagree_generic(conn, concept_id, _FIND_CONCEPT_CONFIG, top_k)


@dataclasses.dataclass
class EmbeddingSnapshot:
    models: list[dict]
    claim_statuses: list[dict]
    claim_vectors: dict[str, list[tuple[int, str, bytes]]]  # model_key -> [(seq, claim_id, blob)]
    concept_statuses: list[dict]
    concept_vectors: dict[str, list[tuple[int, str, bytes]]]  # model_key -> [(seq, concept_id, blob)]


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

    claim_statuses = [dict(r) for r in conn.execute("SELECT * FROM embedding_status").fetchall()]

    claim_vectors = {}
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
            claim_vectors[m["model_key"]] = [(r[0], r[1], r[2]) for r in rows]
        except sqlite3.OperationalError:
            claim_vectors[m["model_key"]] = []

    # Concept embeddings
    concept_statuses = []
    try:
        concept_statuses = [dict(r) for r in conn.execute(
            "SELECT * FROM concept_embedding_status"
        ).fetchall()]
    except sqlite3.OperationalError:
        pass

    concept_vectors = {}
    for m in models:
        table_name = f"concept_vec_{m['model_key']}"
        try:
            rows = conn.execute(
                f"""SELECT v.rowid, cs.concept_id, v.embedding
                    FROM [{table_name}] v
                    JOIN concept_embedding_status cs ON cs.model_key = ?
                    JOIN concept c ON c.seq = v.rowid AND c.id = cs.concept_id
                    WHERE cs.model_key = ?""",
                (m["model_key"], m["model_key"])
            ).fetchall()
            concept_vectors[m["model_key"]] = [(r[0], r[1], r[2]) for r in rows]
        except sqlite3.OperationalError:
            concept_vectors[m["model_key"]] = []

    return EmbeddingSnapshot(
        models=models,
        claim_statuses=claim_statuses,
        claim_vectors=claim_vectors,
        concept_statuses=concept_statuses,
        concept_vectors=concept_vectors,
    )


def restore_embeddings(
    conn: sqlite3.Connection, snapshot: EmbeddingSnapshot
) -> RestoreReport:
    """Restore embeddings after sidecar rebuild. Skips stale/orphaned claims."""
    _ensure_embedding_tables(conn)
    report = RestoreReport()

    # Build claim_id -> (seq, content_hash) map from new sidecar
    current_claims = {}
    try:
        for r in conn.execute("SELECT id, seq, content_hash FROM claim").fetchall():
            current_claims[r["id"]] = (r["seq"], r["content_hash"])
    except sqlite3.OperationalError:
        pass

    # Build status lookup: (model_key, claim_id) -> content_hash_at_embed_time
    status_lookup = {}
    for s in snapshot.claim_statuses:
        status_lookup[(s["model_key"], s["claim_id"])] = s["content_hash"]

    # Pre-build lookup dicts to avoid O(n^2) scans
    claim_at_lookup = {
        (s["model_key"], s["claim_id"]): s.get("embedded_at", "")
        for s in snapshot.claim_statuses
    }

    for m in snapshot.models:
        model_key = m["model_key"]
        dimensions = m["dimensions"]

        conn.execute(
            "INSERT OR REPLACE INTO embedding_model VALUES (?, ?, ?, ?)",
            (model_key, m["model_name"], dimensions, m["created_at"])
        )
        _ensure_vec_table(conn, model_key, dimensions, prefix="claim_vec")

        table_name = f"claim_vec_{model_key}"

        for _old_seq, claim_id, blob in snapshot.claim_vectors.get(model_key, []):
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
                 claim_at_lookup.get((model_key, claim_id), ""))
            )
            report.restored += 1

    # Restore concept embeddings
    current_concepts = {}
    try:
        for r in conn.execute("SELECT id, seq, content_hash FROM concept").fetchall():
            current_concepts[r["id"]] = (r["seq"], r["content_hash"])
    except sqlite3.OperationalError:
        pass

    concept_status_lookup = {}
    for s in snapshot.concept_statuses:
        concept_status_lookup[(s["model_key"], s["concept_id"])] = s["content_hash"]

    concept_at_lookup = {
        (s["model_key"], s["concept_id"]): s.get("embedded_at", "")
        for s in snapshot.concept_statuses
    }

    for m in snapshot.models:
        model_key = m["model_key"]
        dimensions = m["dimensions"]
        _ensure_vec_table(conn, model_key, dimensions, prefix="concept_vec")

        table_name = f"concept_vec_{model_key}"

        for _old_seq, concept_id, blob in snapshot.concept_vectors.get(model_key, []):
            if concept_id not in current_concepts:
                report.orphaned += 1
                continue

            new_seq, current_hash = current_concepts[concept_id]
            embed_hash = concept_status_lookup.get((model_key, concept_id), "")

            if current_hash != embed_hash:
                report.stale += 1
                continue

            conn.execute(
                f"INSERT INTO [{table_name}](rowid, embedding) VALUES (?, ?)",
                (new_seq, blob)
            )
            conn.execute(
                "INSERT OR REPLACE INTO concept_embedding_status VALUES (?, ?, ?, ?)",
                (model_key, concept_id, current_hash,
                 concept_at_lookup.get((model_key, concept_id), ""))
            )
            report.restored += 1

    return report
