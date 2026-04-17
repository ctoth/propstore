"""Sidecar-backed embedding entity and vector APIs."""

from __future__ import annotations

import dataclasses
import sqlite3
from collections.abc import Sequence

from propstore.core.embeddings import (
    EmbeddingEntity,
    claim_embedding_text,
    concept_embedding_text,
)
from propstore.core.row_types import ClaimRow, ConceptRow


@dataclasses.dataclass
class EmbeddingSnapshot:
    models: list[dict]
    claim_statuses: list[dict]
    claim_vectors: dict[str, list[tuple[int, str, bytes]]]
    concept_statuses: list[dict]
    concept_vectors: dict[str, list[tuple[int, str, bytes]]]


@dataclasses.dataclass
class RestoreReport:
    restored: int = 0
    stale: int = 0
    orphaned: int = 0


def _is_missing_table_error(error: sqlite3.OperationalError) -> bool:
    return "no such table" in str(error)


def ensure_embedding_tables(conn: sqlite3.Connection) -> None:
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


def _ensure_vec_table(
    conn: sqlite3.Connection,
    model_key: str,
    dimensions: int,
    prefix: str,
) -> None:
    table_name = f"{prefix}_{model_key}"
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    if row is None:
        conn.execute(
            f"CREATE VIRTUAL TABLE [{table_name}] USING vec0(embedding float[{dimensions}])"
        )


class SidecarEmbeddingRegistry:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_registered_models(self) -> list[dict]:
        try:
            return [
                dict(row)
                for row in self._conn.execute(
                    "SELECT model_key, model_name, dimensions, created_at FROM embedding_model"
                ).fetchall()
            ]
        except sqlite3.OperationalError as error:
            if not _is_missing_table_error(error):
                raise
            return []


class _SidecarEntityEmbeddingStore:
    status_table: str
    status_id_column: str
    vec_prefix: str
    join_source: str
    join_columns: str

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def ensure_storage(self) -> None:
        ensure_embedding_tables(self._conn)

    def existing_content_hashes(self, model_key: str) -> dict[str, str]:
        existing: dict[str, str] = {}
        try:
            rows = self._conn.execute(
                f"SELECT {self.status_id_column}, content_hash "
                f"FROM {self.status_table} WHERE model_key=?",
                (model_key,),
            ).fetchall()
        except sqlite3.OperationalError as error:
            if not _is_missing_table_error(error):
                raise
            return existing
        for row in rows:
            existing[str(row[self.status_id_column])] = str(row["content_hash"])
        return existing

    def prepare_model(
        self,
        model_key: str,
        model_name: str,
        dimensions: int,
        created_at: str,
    ) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO embedding_model VALUES (?, ?, ?, ?)",
            (model_key, model_name, dimensions, created_at),
        )
        _ensure_vec_table(
            self._conn,
            model_key,
            dimensions,
            prefix=self.vec_prefix,
        )

    def save_embedding(
        self,
        model_key: str,
        entity: EmbeddingEntity,
        vector_blob: bytes,
        embedded_at: str,
    ) -> None:
        table_name = f"{self.vec_prefix}_{model_key}"
        self._conn.execute(f"DELETE FROM [{table_name}] WHERE rowid = ?", (entity.seq,))
        self._conn.execute(
            f"INSERT INTO [{table_name}](rowid, embedding) VALUES (?, ?)",
            (entity.seq, vector_blob),
        )
        self._conn.execute(
            f"INSERT OR REPLACE INTO {self.status_table} VALUES (?, ?, ?, ?)",
            (model_key, entity.entity_id, entity.content_hash, embedded_at),
        )

    def vector_for(self, model_key: str, seq: int) -> bytes | None:
        table_name = f"{self.vec_prefix}_{model_key}"
        row = self._conn.execute(
            f"SELECT embedding FROM [{table_name}] WHERE rowid = ?",
            (seq,),
        ).fetchone()
        return None if row is None else row["embedding"]

    def similar_entities(
        self,
        model_key: str,
        query_vector: bytes,
        k: int,
    ) -> list[dict]:
        table_name = f"{self.vec_prefix}_{model_key}"
        rows = self._conn.execute(
            f"""SELECT v.rowid, v.distance, {self.join_columns}
                FROM [{table_name}] v
                JOIN {self.join_source} c ON c.seq = v.rowid
                WHERE v.embedding MATCH ? AND k = ?
                ORDER BY v.distance""",
            (query_vector, k),
        ).fetchall()
        return [dict(row) for row in rows]


class SidecarClaimEmbeddingStore(_SidecarEntityEmbeddingStore):
    status_table = "embedding_status"
    status_id_column = "claim_id"
    vec_prefix = "claim_vec"
    join_source = """
        (
            SELECT
                core.id,
                core.seq,
                core.type,
                core.source_paper,
                core.concept_id,
                txt.auto_summary,
                txt.statement
            FROM claim_core AS core
            LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
        )
    """
    join_columns = (
        "c.id, c.type, c.auto_summary, c.statement, c.source_paper, c.concept_id"
    )

    def load_entities(
        self,
        entity_ids: Sequence[str] | None = None,
    ) -> list[EmbeddingEntity]:
        query = """
            SELECT
                core.id,
                core.id AS artifact_id,
                core.seq,
                core.content_hash,
                txt.auto_summary,
                txt.statement,
                txt.expression,
                txt.name
            FROM claim_core AS core
            LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
        """
        params: tuple[str, ...] = ()
        if entity_ids:
            placeholders = ",".join("?" for _ in entity_ids)
            query += f" WHERE core.id IN ({placeholders})"
            params = tuple(entity_ids)
        rows = self._conn.execute(query, params).fetchall()
        entities: list[EmbeddingEntity] = []
        for row in rows:
            claim = ClaimRow.from_mapping(dict(row))
            if claim.seq is None:
                raise ValueError(f"Claim {claim.claim_id} has no sidecar sequence")
            entities.append(
                EmbeddingEntity(
                    entity_id=str(claim.claim_id),
                    seq=claim.seq,
                    content_hash=str(row["content_hash"]),
                    text=claim_embedding_text(claim),
                )
            )
        return entities

    def resolve_entity(self, entity_id: str) -> tuple[str, int]:
        row = self._conn.execute(
            "SELECT id, seq FROM claim_core WHERE id = ?",
            (entity_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Claim {entity_id} not found")
        return str(row["id"]), int(row["seq"])


class SidecarConceptEmbeddingStore(_SidecarEntityEmbeddingStore):
    status_table = "concept_embedding_status"
    status_id_column = "concept_id"
    vec_prefix = "concept_vec"
    join_source = "concept"
    join_columns = "c.id, c.primary_logical_id, c.canonical_name, c.definition"

    def load_entities(
        self,
        entity_ids: Sequence[str] | None = None,
    ) -> list[EmbeddingEntity]:
        query = """
            SELECT
                id,
                seq,
                content_hash,
                canonical_name,
                definition
            FROM concept
        """
        params: tuple[str, ...] = ()
        if entity_ids:
            placeholders = ",".join("?" for _ in entity_ids)
            query += f" WHERE id IN ({placeholders})"
            params = tuple(entity_ids)
        rows = self._conn.execute(query, params).fetchall()
        aliases = self._aliases_by_concept_id(tuple(str(row["id"]) for row in rows))
        entities: list[EmbeddingEntity] = []
        for row in rows:
            concept = ConceptRow.from_mapping(dict(row))
            entities.append(
                EmbeddingEntity(
                    entity_id=str(concept.concept_id),
                    seq=int(row["seq"]),
                    content_hash=str(row["content_hash"]),
                    text=concept_embedding_text(
                        concept,
                        aliases.get(str(concept.concept_id), ()),
                    ),
                )
            )
        return entities

    def resolve_entity(self, entity_id: str) -> tuple[str, int]:
        row = self._conn.execute(
            "SELECT id, seq FROM concept WHERE id = ? OR canonical_name = ?",
            (entity_id, entity_id),
        ).fetchone()
        if row is None:
            raise ValueError(f"Concept {entity_id} not found")
        return str(row["id"]), int(row["seq"])

    def _aliases_by_concept_id(
        self,
        concept_ids: Sequence[str],
    ) -> dict[str, tuple[str, ...]]:
        if not concept_ids:
            return {}
        placeholders = ",".join("?" for _ in concept_ids)
        rows = self._conn.execute(
            f"SELECT concept_id, alias_name FROM alias WHERE concept_id IN ({placeholders})",
            tuple(concept_ids),
        ).fetchall()
        aliases: dict[str, list[str]] = {}
        for row in rows:
            aliases.setdefault(str(row["concept_id"]), []).append(str(row["alias_name"]))
        return {
            concept_id: tuple(names)
            for concept_id, names in aliases.items()
        }


class SidecarEmbeddingSnapshotStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def extract(self) -> EmbeddingSnapshot | None:
        try:
            models = [
                dict(row)
                for row in self._conn.execute("SELECT * FROM embedding_model").fetchall()
            ]
        except sqlite3.OperationalError as error:
            if not _is_missing_table_error(error):
                raise
            return None

        if not models:
            return None

        claim_statuses = [
            dict(row)
            for row in self._conn.execute("SELECT * FROM embedding_status").fetchall()
        ]
        claim_vectors: dict[str, list[tuple[int, str, bytes]]] = {}
        for model in models:
            model_key = model["model_key"]
            table_name = f"claim_vec_{model_key}"
            try:
                rows = self._conn.execute(
                    f"""SELECT v.rowid, es.claim_id, v.embedding
                        FROM [{table_name}] v
                        JOIN embedding_status es ON es.model_key = ?
                        JOIN claim_core c ON c.seq = v.rowid AND c.id = es.claim_id
                        WHERE es.model_key = ?""",
                    (model_key, model_key),
                ).fetchall()
            except sqlite3.OperationalError as error:
                if not _is_missing_table_error(error):
                    raise
                rows = []
            claim_vectors[model_key] = [
                (int(row[0]), str(row[1]), row[2])
                for row in rows
            ]

        try:
            concept_statuses = [
                dict(row)
                for row in self._conn.execute(
                    "SELECT * FROM concept_embedding_status"
                ).fetchall()
            ]
        except sqlite3.OperationalError as error:
            if not _is_missing_table_error(error):
                raise
            concept_statuses = []

        concept_vectors: dict[str, list[tuple[int, str, bytes]]] = {}
        for model in models:
            model_key = model["model_key"]
            table_name = f"concept_vec_{model_key}"
            try:
                rows = self._conn.execute(
                    f"""SELECT v.rowid, cs.concept_id, v.embedding
                        FROM [{table_name}] v
                        JOIN concept_embedding_status cs ON cs.model_key = ?
                        JOIN concept c ON c.seq = v.rowid AND c.id = cs.concept_id
                        WHERE cs.model_key = ?""",
                    (model_key, model_key),
                ).fetchall()
            except sqlite3.OperationalError as error:
                if not _is_missing_table_error(error):
                    raise
                rows = []
            concept_vectors[model_key] = [
                (int(row[0]), str(row[1]), row[2])
                for row in rows
            ]

        return EmbeddingSnapshot(
            models=models,
            claim_statuses=claim_statuses,
            claim_vectors=claim_vectors,
            concept_statuses=concept_statuses,
            concept_vectors=concept_vectors,
        )

    def restore(self, snapshot: EmbeddingSnapshot) -> RestoreReport:
        ensure_embedding_tables(self._conn)
        report = RestoreReport()
        self._restore_claims(snapshot, report)
        self._restore_concepts(snapshot, report)
        return report

    def _restore_claims(
        self,
        snapshot: EmbeddingSnapshot,
        report: RestoreReport,
    ) -> None:
        current_claims: dict[str, tuple[int, str]] = {}
        try:
            rows = self._conn.execute(
                "SELECT id, seq, content_hash FROM claim_core"
            ).fetchall()
        except sqlite3.OperationalError as error:
            if not _is_missing_table_error(error):
                raise
            rows = []
        for row in rows:
            current_claims[str(row["id"])] = (int(row["seq"]), str(row["content_hash"]))

        status_lookup = {
            (status["model_key"], status["claim_id"]): status["content_hash"]
            for status in snapshot.claim_statuses
        }
        embedded_at_lookup = {
            (status["model_key"], status["claim_id"]): status.get("embedded_at", "")
            for status in snapshot.claim_statuses
        }

        for model in snapshot.models:
            model_key = model["model_key"]
            self._conn.execute(
                "INSERT OR REPLACE INTO embedding_model VALUES (?, ?, ?, ?)",
                (
                    model_key,
                    model["model_name"],
                    model["dimensions"],
                    model["created_at"],
                ),
            )
            _ensure_vec_table(
                self._conn,
                model_key,
                int(model["dimensions"]),
                prefix="claim_vec",
            )
            table_name = f"claim_vec_{model_key}"
            for _old_seq, claim_id, blob in snapshot.claim_vectors.get(model_key, []):
                current = current_claims.get(claim_id)
                if current is None:
                    report.orphaned += 1
                    continue
                new_seq, current_hash = current
                if current_hash != status_lookup.get((model_key, claim_id), ""):
                    report.stale += 1
                    continue
                self._conn.execute(
                    f"INSERT INTO [{table_name}](rowid, embedding) VALUES (?, ?)",
                    (new_seq, blob),
                )
                self._conn.execute(
                    "INSERT OR REPLACE INTO embedding_status VALUES (?, ?, ?, ?)",
                    (
                        model_key,
                        claim_id,
                        current_hash,
                        embedded_at_lookup.get((model_key, claim_id), ""),
                    ),
                )
                report.restored += 1

    def _restore_concepts(
        self,
        snapshot: EmbeddingSnapshot,
        report: RestoreReport,
    ) -> None:
        current_concepts: dict[str, tuple[int, str]] = {}
        try:
            rows = self._conn.execute(
                "SELECT id, seq, content_hash FROM concept"
            ).fetchall()
        except sqlite3.OperationalError as error:
            if not _is_missing_table_error(error):
                raise
            rows = []
        for row in rows:
            current_concepts[str(row["id"])] = (
                int(row["seq"]),
                str(row["content_hash"]),
            )

        status_lookup = {
            (status["model_key"], status["concept_id"]): status["content_hash"]
            for status in snapshot.concept_statuses
        }
        embedded_at_lookup = {
            (status["model_key"], status["concept_id"]): status.get("embedded_at", "")
            for status in snapshot.concept_statuses
        }

        for model in snapshot.models:
            model_key = model["model_key"]
            _ensure_vec_table(
                self._conn,
                model_key,
                int(model["dimensions"]),
                prefix="concept_vec",
            )
            table_name = f"concept_vec_{model_key}"
            for _old_seq, concept_id, blob in snapshot.concept_vectors.get(model_key, []):
                current = current_concepts.get(concept_id)
                if current is None:
                    report.orphaned += 1
                    continue
                new_seq, current_hash = current
                if current_hash != status_lookup.get((model_key, concept_id), ""):
                    report.stale += 1
                    continue
                self._conn.execute(
                    f"INSERT INTO [{table_name}](rowid, embedding) VALUES (?, ?)",
                    (new_seq, blob),
                )
                self._conn.execute(
                    "INSERT OR REPLACE INTO concept_embedding_status VALUES (?, ?, ?, ?)",
                    (
                        model_key,
                        concept_id,
                        current_hash,
                        embedded_at_lookup.get((model_key, concept_id), ""),
                    ),
                )
                report.restored += 1
