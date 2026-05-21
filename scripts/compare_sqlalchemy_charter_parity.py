from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


BLOCK_TABLE_MARKERS = {
    "diagnostics": ("diagnostic",),
    "fts": ("_fts",),
    "vectors": ("vec", "embedding"),
    "behaviors": ("behavior",),
}
SCHEMA_CATALOG_TABLE = "quire_schema_catalog"
SCHEMA_CATALOG_KEY = "default"


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        report = run(args)
    except Exception as exc:
        report = _error_report(args, str(exc))
        _write_json(Path(args.out), report)
        return 1
    _write_json(Path(args.out), report)
    return 1 if report["failures"] else 0


def run(args: argparse.Namespace) -> dict[str, Any]:
    knowledge_dir = Path(args.knowledge_dir)
    workstream = Path(args.workstream)
    allowed_differences = _parse_workstream(workstream, args.owner)
    if args.capture_before == "projection":
        before = Path(args.before)
        baseline_head_sha, semantic_input_hash = _build_projection_sidecar(
            knowledge_dir,
            before,
        )
        before_snapshot = _snapshot_sqlite(before)
        return _report_shell(
            args,
            allowed_differences=allowed_differences,
            baseline_head_sha=baseline_head_sha,
            after_head_sha=None,
            semantic_input_hash=semantic_input_hash,
            before_path=before,
            after_path=None,
            before_snapshot=before_snapshot,
            after_snapshot=None,
            failures=[],
        )

    before = Path(args.before)
    after = Path(args.after)
    if not before.is_file():
        raise FileNotFoundError(f"missing baseline SQLite file: {before}")
    baseline = _load_baseline(before)
    baseline_hash = str(baseline.get("semantic_input_hash") or "")

    after_head_sha = None
    semantic_input_hash = ""
    if args.build_after == "sqlalchemy-charter":
        after_head_sha, semantic_input_hash = _build_sqlalchemy_charter_sidecar(
            knowledge_dir,
            after,
        )
    elif not after.is_file():
        raise FileNotFoundError(f"missing after SQLite file: {after}")

    failures: list[str] = []
    if baseline_hash and semantic_input_hash != baseline_hash:
        failures.append(
            "semantic_input_hash mismatch: "
            f"baseline {baseline_hash}, after {semantic_input_hash}"
        )

    before_snapshot = _snapshot_sqlite(before)
    after_snapshot = _snapshot_sqlite(after)
    comparison = _compare_snapshots(before_snapshot, after_snapshot)
    _add_required_vector_blocks(
        comparison,
        required_vectors=tuple(args.require_vector or ()),
    )
    failures.extend(comparison.pop("failures"))
    failures.extend(
        _required_block_failures(
            comparison,
            required_vectors=tuple(args.require_vector or ()),
            required_behaviors=tuple(args.require_behavior or ()),
        )
    )

    return _report_shell(
        args,
        allowed_differences=allowed_differences,
        baseline_head_sha=str(baseline.get("baseline_head_sha") or ""),
        after_head_sha=after_head_sha,
        semantic_input_hash=semantic_input_hash,
        before_path=before,
        after_path=after,
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
        failures=failures,
        comparison=comparison,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--knowledge-dir", required=True)
    parser.add_argument("--capture-before", choices=("projection",))
    parser.add_argument("--before", required=True)
    parser.add_argument("--build-after", choices=("sqlalchemy-charter",))
    parser.add_argument("--after")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--workstream", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--require-vector", action="append", default=[])
    parser.add_argument("--require-behavior", action="append", default=[])
    return parser


def _parse_workstream(path: Path, owner: str) -> list[str]:
    if not path.is_file():
        raise FileNotFoundError(f"missing workstream file: {path}")
    text = path.read_text(encoding="utf-8")
    if owner not in text:
        raise ValueError(f"workstream {path} does not mention owner {owner!r}")
    if "Data-Parity Gate" not in text:
        raise ValueError(f"workstream {path} is missing Data-Parity Gate section")
    marker = "Accepted parity difference allowlist:"
    if marker not in text:
        raise ValueError(
            f"workstream {path} is missing Accepted parity difference allowlist section"
        )
    allowed: list[str] = []
    tail = text.split(marker, 1)[1]
    for line in tail.splitlines()[1:]:
        stripped = line.strip()
        if stripped.startswith("## ") and allowed:
            break
        if not stripped:
            continue
        if stripped.startswith("- "):
            allowed.append(stripped[2:])
            continue
        if allowed:
            allowed[-1] = f"{allowed[-1]} {stripped}"
            continue
    if not allowed:
        raise ValueError(f"workstream {path} has an empty parity allowlist")
    return allowed


def _build_projection_sidecar(
    knowledge_dir: Path,
    before: Path,
) -> tuple[str, str]:
    from propstore.derived_build import export_sidecar
    from propstore.repository import Repository

    repo = Repository(knowledge_dir)
    head = repo.require_git().head_sha()
    if head is None:
        raise ValueError("capture requires a committed git repository")
    before.unlink(missing_ok=True)
    export_sidecar(repo, before, force=True, commit_hash=head)
    return str(head), _semantic_input_hash(repo, str(head))


def _build_sqlalchemy_charter_sidecar(
    knowledge_dir: Path,
    after: Path,
) -> tuple[str, str]:
    from propstore.derived_build import export_sidecar
    from propstore.repository import Repository

    repo = Repository(knowledge_dir)
    head = repo.require_git().head_sha()
    if head is None:
        raise ValueError("comparison requires a committed git repository")
    after.unlink(missing_ok=True)
    export_sidecar(repo, after, force=True, commit_hash=head)
    return str(head), _semantic_input_hash(repo, str(head))


def _semantic_input_hash(repo: Any, head: str) -> str:
    from propstore.derived_build import _source_branch_tips
    from propstore.families.registry import semantic_import_roots, semantic_init_roots

    git = repo.require_git()
    roots = tuple(sorted(set(semantic_init_roots()) | set(semantic_import_roots())))
    source_branch_tips = tuple(_source_branch_tips(repo))
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            {
                "semantic_roots": roots,
                "source_branch_tips": source_branch_tips,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    digest.update(b"\0")
    _hash_tree_files(digest, git.iter_tree_files(commit=head, roots=roots))
    for branch_name, branch_tip in source_branch_tips:
        digest.update(branch_name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(branch_tip.encode("utf-8"))
        digest.update(b"\0")
        _hash_tree_files(digest, git.iter_tree_files(commit=branch_tip))
    return digest.hexdigest()


def _hash_tree_files(digest: Any, tree_files: Any) -> None:
    for tree_file in tree_files:
        digest.update(tree_file.relpath.encode("utf-8"))
        digest.update(b"\0")
        digest.update(tree_file.content)
        digest.update(b"\0")


def _load_baseline(before: Path) -> dict[str, Any]:
    baseline_path = before.with_name("baseline.json")
    if not baseline_path.is_file():
        raise FileNotFoundError(f"missing baseline report: {baseline_path}")
    loaded = json.loads(baseline_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"baseline report must be a JSON object: {baseline_path}")
    return loaded


def _snapshot_sqlite(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"missing SQLite file: {path}")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        tables = _table_names(conn)
        return {
            "path": str(path),
            "schema_hash": _schema_hash(conn),
            "tables": {
                table: _table_snapshot(conn, table)
                for table in tables
            },
        }
    finally:
        conn.close()


def _table_names(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type IN ('table', 'view')
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    )
    return [str(row[0]) for row in rows if str(row[0]) != SCHEMA_CATALOG_TABLE]


def _schema_hash(conn: sqlite3.Connection) -> str:
    try:
        row = conn.execute(
            f"""
            SELECT schema_hash
            FROM {_quote(SCHEMA_CATALOG_TABLE)}
            WHERE key = ?
            """,
            (SCHEMA_CATALOG_KEY,),
        ).fetchone()
    except sqlite3.OperationalError:
        return ""
    return "" if row is None else str(row[0])


def _table_snapshot(conn: sqlite3.Connection, table: str) -> dict[str, Any]:
    columns_info = conn.execute(f"PRAGMA table_info({_quote(table)})").fetchall()
    columns = [str(row["name"]) for row in columns_info]
    primary_key = [
        str(row["name"])
        for row in sorted(columns_info, key=lambda item: int(item["pk"]))
        if int(row["pk"]) > 0
    ]
    rows = [
        {column: _jsonable(row[column]) for column in columns}
        for row in conn.execute(f"SELECT * FROM {_quote(table)}").fetchall()
    ]
    return {
        "columns": columns,
        "primary_key": primary_key,
        "rows": rows,
        "row_count": len(rows),
        "keys": _row_keys(rows, primary_key),
    }


def _row_keys(rows: list[dict[str, Any]], primary_key: list[str]) -> list[str]:
    if not primary_key:
        return [str(index) for index, _row in enumerate(rows)]
    return [
        json.dumps([row.get(column) for column in primary_key], sort_keys=True)
        for row in rows
    ]


def _compare_snapshots(
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    before_tables = before["tables"]
    after_tables = after["tables"]
    all_table_names = sorted(set(before_tables) | set(after_tables))
    tables: dict[str, Any] = {}
    row_counts: dict[str, Any] = {}
    key_sets: dict[str, Any] = {}
    blocks = {name: [] for name in BLOCK_TABLE_MARKERS}
    for table in all_table_names:
        before_table = before_tables.get(table)
        after_table = after_tables.get(table)
        table_comparison = _compare_table(table, before_table, after_table)
        report_table = before_table if before_table is not None else after_table
        tables[table] = {
            "columns": None if report_table is None else report_table["columns"],
            "primary_key": None if report_table is None else report_table["primary_key"],
            "status": table_comparison["status"],
        }
        row_counts[table] = {
            "before": 0 if before_table is None else before_table["row_count"],
            "after": 0 if after_table is None else after_table["row_count"],
            "status": table_comparison["status"],
        }
        key_sets[table] = {
            "missing_keys": table_comparison["missing_keys"],
            "extra_keys": table_comparison["extra_keys"],
            "status": table_comparison["status"],
        }
        failures.extend(table_comparison["failures"])
        block_name = _block_kind(table)
        if block_name is not None:
            blocks[block_name].append(table_comparison)
    return {
        "tables": tables,
        "row_counts": row_counts,
        "key_sets": key_sets,
        "fts": blocks["fts"],
        "vectors": blocks["vectors"],
        "diagnostics": blocks["diagnostics"],
        "semantic_queries": [],
        "behaviors": blocks["behaviors"],
        "failures": failures,
    }


def _compare_table(
    name: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> dict[str, Any]:
    failures: list[str] = []
    if before is None:
        assert after is not None
        if after["row_count"] == 0:
            return _comparison_block(name, "pass", 0, 0, (), (), (), failures)
        failures.append(f"extra table {name}")
        return _comparison_block(name, "fail", 0, after["row_count"], (), after["keys"], (), failures)
    if after is None:
        failures.append(f"missing table {name}")
        return _comparison_block(name, "fail", before["row_count"], 0, before["keys"], (), (), failures)
    before_rows = _rows_by_key(before)
    after_rows = _rows_by_key(after)
    missing = tuple(sorted(set(before_rows) - set(after_rows)))
    extra = tuple(sorted(set(after_rows) - set(before_rows)))
    changed = tuple(
        key
        for key in sorted(set(before_rows) & set(after_rows))
        if before_rows[key] != after_rows[key]
    )
    if missing:
        failures.append(f"{name} missing keys: {', '.join(missing)}")
    if extra:
        failures.append(f"{name} extra keys: {', '.join(extra)}")
    if changed:
        failures.append(f"{name} changed rows: {', '.join(changed)}")
    status = "pass" if not missing and not extra and not changed else "fail"
    return _comparison_block(
        name,
        status,
        before["row_count"],
        after["row_count"],
        missing,
        extra,
        changed,
        failures,
    )


def _comparison_block(
    name: str,
    status: str,
    before_count: int,
    after_count: int,
    missing_keys: Any,
    extra_keys: Any,
    changed_values: Any,
    failures: list[str],
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "before_count": before_count,
        "after_count": after_count,
        "missing_keys": list(missing_keys),
        "extra_keys": list(extra_keys),
        "changed_values": list(changed_values),
        "failures": failures,
    }


def _rows_by_key(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    keys = snapshot["keys"]
    return dict(zip(keys, snapshot["rows"], strict=True))


def _block_kind(table: str) -> str | None:
    lower = table.lower()
    for block_name, markers in BLOCK_TABLE_MARKERS.items():
        if any(marker in lower for marker in markers):
            return block_name
    return None


def _required_block_failures(
    comparison: dict[str, Any],
    *,
    required_vectors: tuple[str, ...],
    required_behaviors: tuple[str, ...],
) -> list[str]:
    failures: list[str] = []
    for name in required_vectors:
        failures.extend(_require_block(comparison["vectors"], "vector", name))
    for name in required_behaviors:
        failures.extend(_require_block(comparison["behaviors"], "behavior", name))
    return failures


def _add_required_vector_blocks(
    comparison: dict[str, Any],
    *,
    required_vectors: tuple[str, ...],
) -> None:
    blocks = comparison["vectors"]
    existing = {str(block["name"]): block for block in blocks}
    for name in required_vectors:
        if name in existing:
            continue
        dependencies = _semantic_vector_dependencies(name, existing)
        if not dependencies:
            continue
        failures = [
            failure
            for dependency in dependencies
            for failure in dependency["failures"]
        ]
        status = "pass" if not failures else "fail"
        blocks.append(
            _comparison_block(
                name,
                status,
                sum(int(dependency["before_count"]) for dependency in dependencies),
                sum(int(dependency["after_count"]) for dependency in dependencies),
                tuple(
                    key
                    for dependency in dependencies
                    for key in dependency["missing_keys"]
                ),
                tuple(
                    key
                    for dependency in dependencies
                    for key in dependency["extra_keys"]
                ),
                tuple(
                    key
                    for dependency in dependencies
                    for key in dependency["changed_values"]
                ),
                failures,
            )
        )


def _semantic_vector_dependencies(
    name: str,
    existing: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    if name == "embedding-snapshot-restore":
        dependency_names = (
            "embedding_model",
            "embedding_status",
            "concept_embedding_status",
        )
    elif name.startswith("claim-"):
        dependency_names = ("embedding_model", "embedding_status")
    elif name.startswith("concept-"):
        dependency_names = ("embedding_model", "concept_embedding_status")
    else:
        return ()
    dependencies = tuple(
        existing[dependency_name]
        for dependency_name in dependency_names
        if dependency_name in existing
    )
    return dependencies if len(dependencies) == len(dependency_names) else ()


def _require_block(blocks: list[dict[str, Any]], block_kind: str, name: str) -> list[str]:
    for block in blocks:
        if block["name"] == name and block["status"] == "pass":
            return []
    return [f"missing passing {block_kind} comparison block {name!r}"]


def _report_shell(
    args: argparse.Namespace,
    *,
    allowed_differences: list[str],
    baseline_head_sha: str | None,
    after_head_sha: str | None,
    semantic_input_hash: str,
    before_path: Path,
    after_path: Path | None,
    before_snapshot: dict[str, Any] | None,
    after_snapshot: dict[str, Any] | None,
    failures: list[str],
    comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    comparison = _empty_comparison() if comparison is None else comparison
    return {
        "owner": args.owner,
        "workstream": str(Path(args.workstream)),
        "knowledge_dir": str(Path(args.knowledge_dir)),
        "baseline_head_sha": baseline_head_sha or "",
        "after_head_sha": after_head_sha or "",
        "semantic_input_hash": semantic_input_hash,
        "before": _side_report(before_path, before_snapshot),
        "after": _side_report(after_path, after_snapshot),
        "tables": comparison["tables"],
        "row_counts": comparison["row_counts"],
        "key_sets": comparison["key_sets"],
        "fts": comparison["fts"],
        "vectors": comparison["vectors"],
        "diagnostics": comparison["diagnostics"],
        "semantic_queries": comparison["semantic_queries"],
        "behaviors": comparison["behaviors"],
        "allowed_differences": allowed_differences,
        "failures": failures,
    }


def _empty_comparison() -> dict[str, Any]:
    return {
        "tables": {},
        "row_counts": {},
        "key_sets": {},
        "fts": [],
        "vectors": [],
        "diagnostics": [],
        "semantic_queries": [],
        "behaviors": [],
    }


def _side_report(path: Path | None, snapshot: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "path": "" if path is None else str(path),
        "build": "not_run" if path is None else "available",
        "schema_hash": "" if snapshot is None else str(snapshot.get("schema_hash") or ""),
        "diagnostics": [],
        "tables": [] if snapshot is None else sorted(snapshot["tables"]),
    }


def _error_report(args: argparse.Namespace, message: str) -> dict[str, Any]:
    return {
        "owner": getattr(args, "owner", ""),
        "workstream": getattr(args, "workstream", ""),
        "knowledge_dir": getattr(args, "knowledge_dir", ""),
        "baseline_head_sha": "",
        "after_head_sha": "",
        "semantic_input_hash": "",
        "before": {},
        "after": {},
        "tables": {},
        "row_counts": {},
        "key_sets": {},
        "fts": [],
        "vectors": [],
        "diagnostics": [],
        "semantic_queries": [],
        "behaviors": [],
        "allowed_differences": [],
        "failures": [message],
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"__bytes__": value.hex()}
    return value


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
