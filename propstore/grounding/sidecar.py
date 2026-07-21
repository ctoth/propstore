"""A raw-sqlite ``grounded_fact`` sidecar for a :class:`GroundedRulesBundle`.

The grounded marking sections are projected into a single ``grounded_fact`` table
(one row per ``(predicate, arguments, section)``) so the four sections survive a
round-trip into sqlite and back. Non-commitment: every section's rows are written
(``no`` / ``undecided`` / ``unknown`` alongside ``yes``); :func:`read_grounded_facts`
always returns all four keys, even when empty.
"""

from __future__ import annotations

import json
import sqlite3
from types import MappingProxyType

import gunray

from propstore.grounding.bundle import SECTION_NAMES, GroundedRulesBundle, SectionMap


def create_grounded_fact_table(conn: sqlite3.Connection) -> None:
    """Create the ``grounded_fact`` table (predicate, arguments, section)."""

    conn.execute(
        "CREATE TABLE IF NOT EXISTS grounded_fact ("
        " predicate TEXT NOT NULL,"
        " arguments TEXT NOT NULL,"
        " section TEXT NOT NULL,"
        " PRIMARY KEY (predicate, arguments, section)"
        ")"
    )
    conn.commit()


def populate_grounded_facts(
    conn: sqlite3.Connection, bundle: GroundedRulesBundle
) -> int:
    """Insert one row per (atom, section) across all four sections; return count."""

    count = 0
    for section, inner in bundle.sections.items():
        for predicate, rows in inner.items():
            for row in rows:
                conn.execute(
                    "INSERT INTO grounded_fact (predicate, arguments, section) VALUES (?, ?, ?)",
                    (predicate, json.dumps(list(row)), section),
                )
                count += 1
    conn.commit()
    return count


def read_grounded_facts(conn: sqlite3.Connection) -> SectionMap:
    """Read the grounded facts back, always returning all four section keys."""

    collected: dict[str, dict[str, set[tuple[gunray.Scalar, ...]]]] = {
        name: {} for name in SECTION_NAMES
    }
    cursor = conn.execute("SELECT predicate, arguments, section FROM grounded_fact")
    for record in cursor.fetchall():
        predicate = str(record[0])
        section = str(record[2])
        decoded: list[gunray.Scalar] = json.loads(record[1])
        collected.setdefault(section, {}).setdefault(predicate, set()).add(
            tuple(decoded)
        )
    return MappingProxyType(
        {
            name: MappingProxyType(
                {predicate: frozenset(rows) for predicate, rows in inner.items()}
            )
            for name, inner in collected.items()
        }
    )
