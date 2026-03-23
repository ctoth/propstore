from __future__ import annotations

import sqlite3


class SQLiteArgumentationStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, dict]:
        if not claim_ids:
            return {}
        placeholders = ",".join("?" for _ in claim_ids)
        rows = self._conn.execute(
            f"SELECT * FROM claim WHERE id IN ({placeholders})",  # noqa: S608
            list(claim_ids),
        ).fetchall()
        return {row["id"]: dict(row) for row in rows}

    def stances_between(self, claim_ids: set[str]) -> list[dict]:
        if not claim_ids:
            return []
        placeholders = ",".join("?" for _ in claim_ids)
        rows = self._conn.execute(
            f"SELECT * FROM claim_stance WHERE claim_id IN ({placeholders}) "  # noqa: S608
            f"AND target_claim_id IN ({placeholders})",
            list(claim_ids) + list(claim_ids),
        ).fetchall()
        return [dict(row) for row in rows]
