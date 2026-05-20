from __future__ import annotations

import argparse
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
        if not stripped:
            if allowed:
                break
            continue
        if not stripped.startswith("- "):
            if allowed:
                break
            continue
        allowed.append(stripped[2:])
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
    from propstore.derived_build import _source_branch_tips, world_sidecar_hash

    return world_sidecar_hash(
        head,
        source_branch_tips=_source_branch_tips(repo),
    )


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
    return [str(row[0]) for row in rows]


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
        tables[table] = {
            "columns": None if before_table is None else before_table["columns"],
            "primary_key": None if before_table is None else before_table["primary_key"],
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
        "schema_hash": "",
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
