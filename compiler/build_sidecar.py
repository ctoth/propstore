"""SQLite sidecar builder for the propstore concept registry.

Reads validated concept files and builds a SQLite database with:
- concept table
- alias table
- relationship table
- parameterization table
- FTS5 index over names, aliases, definitions, conditions
- claim table (when claim files provided)
- conflicts table (when claim files provided)
- claim FTS5 index (when claim files provided)
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

from compiler.validate import LoadedConcept, load_concepts


def _content_hash(
    concepts: list[LoadedConcept],
    claim_files: list | None = None,
) -> str:
    """Hash all concept and claim file contents to detect changes."""
    h = hashlib.sha256()
    for c in sorted(concepts, key=lambda x: x.filename):
        h.update(c.filename.encode())
        h.update(json.dumps(c.data, sort_keys=True, default=str).encode())
    if claim_files:
        for cf in sorted(claim_files, key=lambda x: x.filename):
            h.update(cf.filename.encode())
            h.update(json.dumps(cf.data, sort_keys=True, default=str).encode())
    return h.hexdigest()


def _get_kind_type(data: dict) -> str:
    kind = data.get("kind", {})
    if not isinstance(kind, dict):
        return "unknown"
    for k in ("quantity", "category", "boolean", "structural"):
        if kind.get(k) is not None:
            return k
    return "unknown"


def build_sidecar(
    concepts: list[LoadedConcept],
    sidecar_path: Path,
    force: bool = False,
    claim_files: list | None = None,
    concept_registry: dict | None = None,
) -> bool:
    """Build the SQLite sidecar from concept data.

    When claim_files is provided, also creates claim, conflicts, and claim_fts
    tables. concept_registry is required for conflict detection when claim_files
    is provided.

    Returns True if the sidecar was rebuilt, False if skipped.
    """
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if rebuild is needed
    content_hash = _content_hash(concepts, claim_files)
    hash_path = sidecar_path.with_suffix(".hash")

    if not force and sidecar_path.exists() and hash_path.exists():
        existing_hash = hash_path.read_text().strip()
        if existing_hash == content_hash:
            return False

    # Build fresh
    if sidecar_path.exists():
        sidecar_path.unlink()

    conn = sqlite3.connect(sidecar_path)
    conn.execute("PRAGMA journal_mode=WAL")

    _create_tables(conn)
    _populate_concepts(conn, concepts)
    _populate_aliases(conn, concepts)
    _populate_relationships(conn, concepts)
    _populate_parameterizations(conn, concepts)
    _build_fts_index(conn, concepts)

    if claim_files is not None:
        _create_claim_tables(conn)
        _populate_claims(conn, claim_files)
        if concept_registry is None:
            concept_registry = {c.data["id"]: c.data for c in concepts if c.data.get("id")}
        _populate_conflicts(conn, claim_files, concept_registry)
        _build_claim_fts_index(conn, claim_files)

    conn.commit()
    conn.close()

    # Write content hash
    hash_path.write_text(content_hash)

    return True


def _create_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE concept (
            id TEXT PRIMARY KEY,
            canonical_name TEXT NOT NULL,
            status TEXT NOT NULL,
            domain TEXT,
            definition TEXT NOT NULL,
            kind_type TEXT NOT NULL,
            created_date TEXT,
            last_modified TEXT
        );

        CREATE TABLE alias (
            concept_id TEXT NOT NULL,
            alias_name TEXT NOT NULL,
            source TEXT NOT NULL,
            FOREIGN KEY (concept_id) REFERENCES concept(id)
        );

        CREATE TABLE relationship (
            source_id TEXT NOT NULL,
            type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            conditions_cel TEXT,
            FOREIGN KEY (source_id) REFERENCES concept(id),
            FOREIGN KEY (target_id) REFERENCES concept(id)
        );

        CREATE TABLE parameterization (
            concept_ids TEXT NOT NULL,
            formula TEXT NOT NULL,
            sympy TEXT,
            exactness TEXT NOT NULL,
            conditions_cel TEXT
        );

        CREATE INDEX idx_alias_name ON alias(alias_name);
        CREATE INDEX idx_alias_concept ON alias(concept_id);
        CREATE INDEX idx_rel_source ON relationship(source_id);
        CREATE INDEX idx_rel_target ON relationship(target_id);
    """)


def _populate_concepts(conn: sqlite3.Connection, concepts: list[LoadedConcept]):
    for c in concepts:
        d = c.data
        created = d.get("created_date")
        if created and not isinstance(created, str):
            created = str(created)
        modified = d.get("last_modified")
        if modified and not isinstance(modified, str):
            modified = str(modified)

        conn.execute(
            "INSERT INTO concept (id, canonical_name, status, domain, definition, kind_type, created_date, last_modified) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (d.get("id"), d.get("canonical_name"), d.get("status"),
             d.get("domain"), d.get("definition"), _get_kind_type(d),
             created, modified),
        )


def _populate_aliases(conn: sqlite3.Connection, concepts: list[LoadedConcept]):
    for c in concepts:
        d = c.data
        cid = d.get("id")
        for alias in d.get("aliases", []) or []:
            conn.execute(
                "INSERT INTO alias (concept_id, alias_name, source) VALUES (?, ?, ?)",
                (cid, alias.get("name"), alias.get("source")),
            )


def _populate_relationships(conn: sqlite3.Connection, concepts: list[LoadedConcept]):
    for c in concepts:
        d = c.data
        source_id = d.get("id")
        for rel in d.get("relationships", []) or []:
            conditions = rel.get("conditions", []) or []
            conn.execute(
                "INSERT INTO relationship (source_id, type, target_id, conditions_cel) VALUES (?, ?, ?, ?)",
                (source_id, rel.get("type"), rel.get("target"),
                 json.dumps(conditions) if conditions else None),
            )


def _populate_parameterizations(conn: sqlite3.Connection, concepts: list[LoadedConcept]):
    for c in concepts:
        d = c.data
        for param in d.get("parameterization_relationships", []) or []:
            inputs = param.get("inputs", [])
            conditions = param.get("conditions", []) or []
            conn.execute(
                "INSERT INTO parameterization (concept_ids, formula, sympy, exactness, conditions_cel) "
                "VALUES (?, ?, ?, ?, ?)",
                (json.dumps(inputs), param.get("formula"), param.get("sympy"),
                 param.get("exactness"),
                 json.dumps(conditions) if conditions else None),
            )


def _build_fts_index(conn: sqlite3.Connection, concepts: list[LoadedConcept]):
    """Build FTS5 index over concept names, aliases, definitions, and condition strings."""
    conn.execute("""
        CREATE VIRTUAL TABLE concept_fts USING fts5(
            concept_id UNINDEXED,
            canonical_name,
            aliases,
            definition,
            conditions
        )
    """)

    for c in concepts:
        d = c.data
        cid = d.get("id", "")
        name = d.get("canonical_name", "")
        definition = d.get("definition", "")

        # Collect all alias names
        alias_names = [a.get("name", "") for a in d.get("aliases", []) or []]
        aliases_text = " ".join(alias_names)

        # Collect all condition strings
        conditions_parts = []
        for rel in d.get("relationships", []) or []:
            for cond in rel.get("conditions", []) or []:
                conditions_parts.append(cond)
        for param in d.get("parameterization_relationships", []) or []:
            for cond in param.get("conditions", []) or []:
                conditions_parts.append(cond)
        conditions_text = " ".join(conditions_parts)

        conn.execute(
            "INSERT INTO concept_fts (concept_id, canonical_name, aliases, definition, conditions) "
            "VALUES (?, ?, ?, ?, ?)",
            (cid, name, aliases_text, definition, conditions_text),
        )


def _create_claim_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE claim (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            concept_id TEXT,
            value TEXT,
            unit TEXT,
            conditions_cel TEXT,
            statement TEXT,
            expression TEXT,
            name TEXT,
            source_paper TEXT NOT NULL,
            provenance_page INTEGER NOT NULL,
            provenance_json TEXT
        );

        CREATE TABLE conflicts (
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

        CREATE VIRTUAL TABLE claim_fts USING fts5(
            claim_id UNINDEXED,
            statement,
            conditions,
            expression
        );

        CREATE INDEX idx_claim_concept ON claim(concept_id);
        CREATE INDEX idx_claim_type ON claim(type);
        CREATE INDEX idx_conflicts_concept ON conflicts(concept_id);
        CREATE INDEX idx_conflicts_class ON conflicts(warning_class);
    """)


def _populate_claims(conn: sqlite3.Connection, claim_files: list):
    from compiler.validate_claims import LoadedClaimFile

    for cf in claim_files:
        source_paper = cf.data.get("source", {}).get("paper", cf.filename)
        for claim in cf.data.get("claims", []):
            cid = claim.get("id")
            ctype = claim.get("type")
            prov = claim.get("provenance", {})
            conditions = claim.get("conditions")

            # Type-specific fields
            concept_id = None
            value = None
            unit = None
            statement = None
            expression = None
            name = None

            if ctype == "parameter":
                concept_id = claim.get("concept")
                value = json.dumps(claim.get("value"))
                unit = claim.get("unit")
            elif ctype == "observation":
                statement = claim.get("statement")
            elif ctype == "equation":
                expression = claim.get("expression")
            elif ctype == "model":
                name = claim.get("name")

            conn.execute(
                "INSERT INTO claim (id, type, concept_id, value, unit, "
                "conditions_cel, statement, expression, name, "
                "source_paper, provenance_page, provenance_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (cid, ctype, concept_id, value, unit,
                 json.dumps(conditions) if conditions else None,
                 statement, expression, name,
                 prov.get("paper", source_paper),
                 prov.get("page", 0),
                 json.dumps(prov)),
            )


def _populate_conflicts(conn: sqlite3.Connection, claim_files: list, concept_registry: dict):
    from compiler.conflict_detector import detect_conflicts

    records = detect_conflicts(claim_files, concept_registry)
    for r in records:
        conn.execute(
            "INSERT INTO conflicts (concept_id, claim_a_id, claim_b_id, "
            "warning_class, conditions_a, conditions_b, value_a, value_b, "
            "derivation_chain) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (r.concept_id, r.claim_a_id, r.claim_b_id,
             r.warning_class.value,
             json.dumps(r.conditions_a),
             json.dumps(r.conditions_b),
             r.value_a, r.value_b,
             r.derivation_chain),
        )


def _build_claim_fts_index(conn: sqlite3.Connection, claim_files: list):
    """Build FTS5 index over claim statements, conditions, and expressions."""
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            cid = claim.get("id", "")
            statement = claim.get("statement", "") or ""
            expression = claim.get("expression", "") or ""
            conditions = claim.get("conditions", []) or []
            conditions_text = " ".join(conditions)

            conn.execute(
                "INSERT INTO claim_fts (claim_id, statement, conditions, expression) "
                "VALUES (?, ?, ?, ?)",
                (cid, statement, conditions_text, expression),
            )


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Build propstore SQLite sidecar")
    parser.add_argument("concept_dir", nargs="?", default="concepts",
                        help="Path to concepts directory")
    parser.add_argument("-o", "--output", default="sidecar/propstore.sqlite",
                        help="Output SQLite file path")
    parser.add_argument("--force", action="store_true",
                        help="Force rebuild even if unchanged")
    args = parser.parse_args()

    concept_dir = Path(args.concept_dir)
    if not concept_dir.exists():
        print(f"ERROR: Concept directory '{concept_dir}' does not exist")
        sys.exit(1)

    concepts = load_concepts(concept_dir)
    if not concepts:
        print("No concept files found.")
        sys.exit(0)

    sidecar_path = Path(args.output)
    rebuilt = build_sidecar(concepts, sidecar_path, force=args.force)

    if rebuilt:
        print(f"Sidecar built: {sidecar_path} ({len(concepts)} concepts)")
    else:
        print(f"Sidecar unchanged: {sidecar_path}")


if __name__ == "__main__":
    main()
