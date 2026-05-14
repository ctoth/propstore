from __future__ import annotations

import argparse
import ast
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


ROOTS = ("propstore", "tests")
CODEC_NAMES = {
    "to_payload",
    "from_payload",
    "to_dict",
    "from_dict",
    "from_mapping",
    "to_mapping",
}
ROW_CLASS_SUFFIXES = ("Row", "Record", "Report", "Request")
SQL_WORDS = ("SELECT", "INSERT", "UPDATE", "DELETE", "PRAGMA")
DIRECT_SQL_PATTERNS = (
    "sqlite3",
    "connect_sidecar",
    "connect_sidecar_readonly",
    "row_factory",
)
TABLE_NAMES = (
    "meta",
    "source",
    "concept",
    "alias",
    "relationship",
    "relation_edge",
    "parameterization",
    "parameterization_group",
    "form",
    "form_algebra",
    "concept_fts",
    "context",
    "context_assumption",
    "context_lifting_rule",
    "context_lifting_materialization",
    "claim_core",
    "claim_concept_link",
    "claim_numeric_payload",
    "claim_text_payload",
    "claim_algorithm_payload",
    "claim_fts",
    "conflict_witness",
    "justification",
    "calibration_counts",
    "build_diagnostics",
    "micropublication",
    "micropublication_claim",
    "grounded_fact",
    "grounded_fact_empty_predicate",
    "grounded_bundle_input",
    "embedding_model",
    "embedding_status",
    "concept_embedding_status",
)
REPEATED_FIELD_NAMES = (
    "id",
    "claim_id",
    "concept_id",
    "context_id",
    "source_id",
    "source_kind",
    "source_slug",
    "source_paper",
    "target_id",
    "target_kind",
    "provenance_json",
    "conditions_cel",
    "conditions_ir",
    "content_hash",
    "version_id",
    "primary_logical_id",
    "logical_ids_json",
    "seq",
    "status",
    "stage",
    "build_status",
    "promotion_status",
    "embedding_model",
    "opinion_belief",
    "opinion_disbelief",
    "opinion_uncertainty",
    "opinion_base_rate",
    "diagnostic_kind",
)


@dataclass
class FileInventory:
    path: Path
    lines: int = 0
    projection_columns: list[str] = field(default_factory=list)
    projection_tables: list[str] = field(default_factory=list)
    fts_projections: list[str] = field(default_factory=list)
    vec_mentions: int = 0
    sqlite_mentions: int = 0
    execute_calls: int = 0
    sql_literals: list[str] = field(default_factory=list)
    sidecar_imports: int = 0
    materialize_calls: int = 0
    codec_methods: list[str] = field(default_factory=list)
    mapping_annotations: int = 0
    dict_any_annotations: int = 0
    dataclasses: int = 0
    row_classes: list[str] = field(default_factory=list)
    row_types_imports: int = 0
    row_types_names: list[str] = field(default_factory=list)
    request_report_calls: list[str] = field(default_factory=list)
    table_name_mentions: list[str] = field(default_factory=list)
    field_mentions: list[str] = field(default_factory=list)

    @property
    def declaration_density(self) -> int:
        return (
            len(self.projection_columns)
            + len(self.codec_methods)
            + self.mapping_annotations
            + self.dict_any_annotations
            + len(self.row_classes)
        )

    @property
    def raw_sql_score(self) -> int:
        return self.sqlite_mentions + self.execute_calls + len(self.sql_literals)


def _py_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for name in ROOTS:
        base = root / name
        if base.exists():
            paths.extend(path for path in base.rglob("*.py") if path.is_file())
    return sorted(paths)


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _string_arg(node: ast.Call, index: int = 0) -> str | None:
    if len(node.args) <= index:
        return None
    arg = node.args[index]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value
    return None


def _has_sql_word(value: str) -> bool:
    upper = value.upper()
    return any(word in upper for word in SQL_WORDS)


def _annotation_text(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def _imported_names(node: ast.ImportFrom) -> list[str]:
    return [alias.asname or alias.name for alias in node.names]


def _scan_ast(text: str, item: FileInventory) -> None:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "sqlite3" for alias in node.names):
                item.sqlite_mentions += 1
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "sqlite3":
                item.sqlite_mentions += 1
            if module.startswith("propstore.sidecar"):
                item.sidecar_imports += 1
            if module == "propstore.core.row_types":
                item.row_types_imports += 1
                item.row_types_names.extend(_imported_names(node))
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name == "ProjectionColumn":
                column_name = _string_arg(node)
                if column_name:
                    item.projection_columns.append(column_name)
            elif name == "ProjectionTable":
                table_name = _string_arg(node)
                if table_name:
                    item.projection_tables.append(table_name)
            elif name == "FtsProjection":
                fts_name = _string_arg(node)
                if fts_name:
                    item.fts_projections.append(fts_name)
            elif name == "execute":
                item.execute_calls += 1
                sql = _string_arg(node)
                if sql and _has_sql_word(sql):
                    item.sql_literals.append(" ".join(sql.split()))
            elif name == "materialize_world_sidecar":
                item.materialize_calls += 1
            if name.endswith(("Request", "Report")):
                item.request_report_calls.append(name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in CODEC_NAMES:
                item.codec_methods.append(node.name)
        elif isinstance(node, ast.ClassDef):
            if node.name.endswith(ROW_CLASS_SUFFIXES):
                item.row_classes.append(node.name)
        elif isinstance(node, ast.AnnAssign):
            text_value = _annotation_text(node.annotation)
            if "Mapping[" in text_value or "TypedDict" in text_value:
                item.mapping_annotations += 1
            if "dict[str, Any]" in text_value or "dict[str, object]" in text_value:
                item.dict_any_annotations += 1


def _scan_text(text: str, item: FileInventory) -> None:
    item.lines = len(text.splitlines())
    item.vec_mentions = text.count("VecProjection") + text.count("sqlite-vec")
    item.sqlite_mentions += sum(text.count(pattern) for pattern in DIRECT_SQL_PATTERNS)
    item.dataclasses = text.count("@dataclass")
    for table in TABLE_NAMES:
        if re.search(rf"\b{re.escape(table)}\b", text):
            item.table_name_mentions.append(table)
    for field_name in REPEATED_FIELD_NAMES:
        if re.search(rf"\b{re.escape(field_name)}\b", text):
            item.field_mentions.append(field_name)


def collect_inventory(root: Path) -> list[FileInventory]:
    items: list[FileInventory] = []
    for path in _py_files(root):
        text = path.read_text(encoding="utf-8")
        item = FileInventory(path=path)
        _scan_text(text, item)
        _scan_ast(text, item)
        items.append(item)
    return items


def _top(items: Iterable[FileInventory], key_name: str, limit: int) -> list[FileInventory]:
    return sorted(
        [item for item in items if getattr(item, key_name)],
        key=lambda item: (getattr(item, key_name), item.lines, str(item.path)),
        reverse=True,
    )[:limit]


def _print_table(headers: tuple[str, ...], rows: Iterable[tuple[object, ...]]) -> None:
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        print("| " + " | ".join(str(value) for value in row) + " |")


def _bucket(relative_path: Path) -> str:
    parts = relative_path.parts
    if len(parts) >= 2 and parts[0] == "propstore":
        return parts[1]
    return parts[0]


def render_markdown(items: list[FileInventory], root: Path, limit: int) -> None:
    propstore_items = [
        item for item in items if _relative(item.path, root).startswith("propstore/")
    ]
    tests_items = [item for item in items if _relative(item.path, root).startswith("tests/")]
    print("# Typed Metadata Cleanup Mechanical Inventory")
    print()
    print("Generated by `uv run scripts/typed_metadata_inventory.py --format markdown`.")
    print()
    print("## Package Metrics")
    bucket_rows = []
    by_bucket: dict[str, list[FileInventory]] = defaultdict(list)
    for item in propstore_items:
        by_bucket[_bucket(item.path.relative_to(root))].append(item)
    for bucket, bucket_items in sorted(by_bucket.items()):
        bucket_rows.append(
            (
                bucket,
                sum(item.lines for item in bucket_items),
                sum(len(item.projection_columns) for item in bucket_items),
                sum(item.raw_sql_score for item in bucket_items),
                sum(len(item.codec_methods) for item in bucket_items),
                sum(item.mapping_annotations + item.dict_any_annotations for item in bucket_items),
                sum(len(item.row_classes) for item in bucket_items),
            )
        )
    _print_table(
        ("package", "lines", "projection_columns", "raw_sql_score", "codec_methods", "mapping_hints", "row_classes"),
        bucket_rows,
    )

    print()
    print("## Repeated Projection Fields")
    field_files: dict[str, set[str]] = defaultdict(set)
    for item in propstore_items:
        for name in item.projection_columns:
            field_files[name].add(_relative(item.path, root))
    rows = [
        (name, len(paths), ", ".join(sorted(paths)[:8]))
        for name, paths in sorted(field_files.items(), key=lambda pair: (-len(pair[1]), pair[0]))
        if len(paths) > 1
    ]
    _print_table(("field", "files", "sample_files"), rows)

    print()
    print("## Highest Declaration Density")
    rows = [
        (
            _relative(item.path, root),
            item.declaration_density,
            len(item.projection_columns),
            len(item.codec_methods),
            item.mapping_annotations + item.dict_any_annotations,
            len(item.row_classes),
        )
        for item in _top(propstore_items, "declaration_density", limit)
    ]
    _print_table(("path", "score", "projection_columns", "codecs", "mapping_hints", "row_classes"), rows)

    print()
    print("## Raw SQL Outside Sidecar")
    rows = [
        (
            _relative(item.path, root),
            item.raw_sql_score,
            item.sqlite_mentions,
            item.execute_calls,
            len(item.sql_literals),
            ", ".join(item.table_name_mentions[:10]),
        )
        for item in sorted(
            [
                item
                for item in propstore_items
                if not _relative(item.path, root).startswith("propstore/sidecar/")
                and item.raw_sql_score
            ],
            key=lambda item: (item.raw_sql_score, item.execute_calls, str(item.path)),
            reverse=True,
        )[:limit]
    ]
    _print_table(("path", "score", "sqlite_mentions", "execute_calls", "sql_literals", "table_mentions"), rows)

    print()
    print("## Sidecar API Coupling Outside Sidecar")
    rows = [
        (
            _relative(item.path, root),
            item.sidecar_imports,
            item.materialize_calls,
            ", ".join(item.table_name_mentions[:10]),
        )
        for item in sorted(
            [
                item
                for item in propstore_items
                if not _relative(item.path, root).startswith("propstore/sidecar/")
                and (item.sidecar_imports or item.materialize_calls)
            ],
            key=lambda item: (item.sidecar_imports + item.materialize_calls, str(item.path)),
            reverse=True,
        )[:limit]
    ]
    _print_table(("path", "sidecar_imports", "materialize_calls", "table_mentions"), rows)

    print()
    print("## Core Row Type Importers")
    rows = [
        (_relative(item.path, root), item.row_types_imports, ", ".join(sorted(set(item.row_types_names))))
        for item in sorted(
            [item for item in propstore_items if item.row_types_imports],
            key=lambda item: (item.row_types_imports, str(item.path)),
            reverse=True,
        )
    ]
    _print_table(("path", "imports", "names"), rows)

    print()
    print("## CLI Request/Report Adapter Surface")
    rows = [
        (
            _relative(item.path, root),
            len(item.request_report_calls),
            ", ".join(sorted(set(item.request_report_calls))[:12]),
        )
        for item in sorted(
            [
                item
                for item in propstore_items
                if _relative(item.path, root).startswith("propstore/cli/")
                and item.request_report_calls
            ],
            key=lambda item: (len(item.request_report_calls), str(item.path)),
            reverse=True,
        )[:limit]
    ]
    _print_table(("path", "request_report_calls", "sample_names"), rows)

    print()
    print("## Test Pins")
    rows = [
        (
            _relative(item.path, root),
            len(item.table_name_mentions),
            len(item.field_mentions),
            item.sidecar_imports,
            ", ".join(item.table_name_mentions[:8]),
        )
        for item in sorted(
            [
                item
                for item in tests_items
                if item.table_name_mentions or item.field_mentions or item.sidecar_imports
            ],
            key=lambda item: (
                len(item.table_name_mentions) + len(item.field_mentions) + item.sidecar_imports,
                str(item.path),
            ),
            reverse=True,
        )[:limit]
    ]
    _print_table(("path", "table_mentions", "field_mentions", "sidecar_imports", "sample_tables"), rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory typed metadata cleanup surfaces.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--format", choices=("markdown",), default="markdown")
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args()

    root = args.root.resolve()
    items = collect_inventory(root)
    render_markdown(items, root, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
