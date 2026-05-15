from __future__ import annotations

import argparse
import ast
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


ROOTS = ("propstore", "tests")
CODEC_NAMES = {
    "to_payload",
    "from_payload",
    "to_dict",
    "from_dict",
    "from_mapping",
    "to_mapping",
}
CLASS_SURFACE_SUFFIXES = ("Request", "Report", "Result", "Row", "Record", "Spec", "Line", "View")
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
    projection_foreign_keys: list[str] = field(default_factory=list)
    fts_projections: list[str] = field(default_factory=list)
    rowid_vec_projections: list[str] = field(default_factory=list)
    embedding_status_projections: list[str] = field(default_factory=list)
    vec_mentions: int = 0
    sqlite_mentions: int = 0
    execute_calls: int = 0
    sql_literals: list[str] = field(default_factory=list)
    sidecar_imports: int = 0
    sidecar_import_symbols: list[str] = field(default_factory=list)
    quire_imports: int = 0
    quire_import_symbols: list[str] = field(default_factory=list)
    materialize_calls: int = 0
    codec_methods: list[str] = field(default_factory=list)
    mapping_annotations: int = 0
    dict_any_annotations: int = 0
    dataclasses: int = 0
    class_surfaces: list[str] = field(default_factory=list)
    row_classes: list[str] = field(default_factory=list)
    json_report_mixins: int = 0
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
            + len(self.class_surfaces)
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


def _string_keyword(node: ast.Call, name: str) -> str | None:
    for keyword in node.keywords:
        if keyword.arg == name and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            return keyword.value.value
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


def _base_names(node: ast.ClassDef) -> list[str]:
    names = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
        elif isinstance(base, ast.Attribute):
            names.append(base.attr)
    return names


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
                item.sidecar_import_symbols.extend(f"{module}.{name}" for name in _imported_names(node))
            if module.startswith("quire"):
                item.quire_imports += 1
                item.quire_import_symbols.extend(f"{module}.{name}" for name in _imported_names(node))
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
                table_name = _string_arg(node) or _string_keyword(node, "table") or _string_keyword(node, "name")
                if table_name:
                    item.projection_tables.append(table_name)
            elif name == "ProjectionForeignKey":
                fk_target = _string_arg(node, 1) or _string_keyword(node, "target_table")
                item.projection_foreign_keys.append(fk_target or "<dynamic>")
            elif name == "FtsProjection":
                fts_name = _string_arg(node) or _string_keyword(node, "table") or _string_keyword(node, "name")
                if fts_name:
                    item.fts_projections.append(fts_name)
            elif name == "rowid_vec_projection":
                vec_name = _string_arg(node) or _string_keyword(node, "table") or _string_keyword(node, "name")
                item.rowid_vec_projections.append(vec_name or "<dynamic>")
            elif name == "embedding_status_projection":
                status_name = _string_arg(node) or _string_keyword(node, "table") or _string_keyword(node, "name")
                item.embedding_status_projections.append(status_name or "<dynamic>")
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
            base_names = _base_names(node)
            if "JsonReportMixin" in base_names:
                item.json_report_mixins += 1
            if node.name.endswith(CLASS_SURFACE_SUFFIXES):
                item.class_surfaces.append(node.name)
            if node.name.endswith("Row"):
                item.row_classes.append(node.name)
        elif isinstance(node, ast.AnnAssign):
            text_value = _annotation_text(node.annotation)
            if "Mapping[" in text_value or "TypedDict" in text_value:
                item.mapping_annotations += 1
            if "dict[str, Any]" in text_value or "dict[str, object]" in text_value:
                item.dict_any_annotations += 1


def _scan_text(text: str, item: FileInventory) -> None:
    item.lines = len(text.splitlines())
    item.vec_mentions = (
        text.count("VecProjection")
        + text.count("sqlite-vec")
        + text.count("rowid_vec_projection")
        + text.count("embedding_status_projection")
    )
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


def _file_record(item: FileInventory, root: Path) -> dict[str, Any]:
    return {
        "path": _relative(item.path, root),
        "lines": item.lines,
        "projection_columns": item.projection_columns,
        "projection_tables": item.projection_tables,
        "projection_foreign_keys": item.projection_foreign_keys,
        "fts_projections": item.fts_projections,
        "rowid_vec_projections": item.rowid_vec_projections,
        "embedding_status_projections": item.embedding_status_projections,
        "vec_mentions": item.vec_mentions,
        "sqlite_mentions": item.sqlite_mentions,
        "execute_calls": item.execute_calls,
        "sql_literals": item.sql_literals,
        "sidecar_imports": item.sidecar_imports,
        "sidecar_import_symbols": item.sidecar_import_symbols,
        "quire_imports": item.quire_imports,
        "quire_import_symbols": item.quire_import_symbols,
        "materialize_calls": item.materialize_calls,
        "codec_methods": item.codec_methods,
        "mapping_annotations": item.mapping_annotations,
        "dict_any_annotations": item.dict_any_annotations,
        "dataclasses": item.dataclasses,
        "class_surfaces": item.class_surfaces,
        "row_classes": item.row_classes,
        "json_report_mixins": item.json_report_mixins,
        "row_types_imports": item.row_types_imports,
        "row_types_names": item.row_types_names,
        "request_report_calls": item.request_report_calls,
        "table_name_mentions": item.table_name_mentions,
        "field_mentions": item.field_mentions,
        "declaration_density": item.declaration_density,
        "raw_sql_score": item.raw_sql_score,
    }


def _summary_metrics(items: list[FileInventory], root: Path) -> dict[str, int]:
    propstore_items = [
        item for item in items if _relative(item.path, root).startswith("propstore/")
    ]
    non_sidecar_items = [
        item
        for item in propstore_items
        if not _relative(item.path, root).startswith("propstore/sidecar/")
    ]
    sidecar_items = [
        item for item in propstore_items if _relative(item.path, root).startswith("propstore/sidecar/")
    ]
    sidecar_declaration_items = [
        item
        for item in sidecar_items
        if any(
            (
                item.projection_columns,
                item.projection_tables,
                item.fts_projections,
                item.projection_foreign_keys,
                item.rowid_vec_projections,
                item.embedding_status_projections,
            )
        )
    ]
    app_world_wrapper_classes = 0
    for item in propstore_items:
        rel = _relative(item.path, root)
        if rel.startswith("propstore/app/") or rel.startswith("propstore/world/"):
            app_world_wrapper_classes += sum(
                1
                for name in item.class_surfaces
                if name.endswith(("Request", "Report", "Result", "Line", "View"))
            )
    return {
        "propstore_python_files": len(propstore_items),
        "propstore_python_lines": sum(item.lines for item in propstore_items),
        "generated_propstore_python_lines": sum(
            item.lines
            for item in propstore_items
            if "/_generated/" in _relative(item.path, root)
            or "/generated/" in _relative(item.path, root)
            or _relative(item.path, root).endswith("_generated.py")
        ),
        "handwritten_propstore_python_lines": sum(
            item.lines
            for item in propstore_items
            if "/_generated/" not in _relative(item.path, root)
            and "/generated/" not in _relative(item.path, root)
            and not _relative(item.path, root).endswith("_generated.py")
        ),
        "sidecar_projection_columns": sum(len(item.projection_columns) for item in sidecar_items),
        "handwritten_projection_tables": sum(len(item.projection_tables) for item in sidecar_declaration_items),
        "handwritten_fts_projections": sum(len(item.fts_projections) for item in sidecar_items),
        "handwritten_vec_declarations": sum(
            len(item.rowid_vec_projections) + len(item.embedding_status_projections)
            for item in sidecar_items
        ),
        "handwritten_fk_edges": sum(len(item.projection_foreign_keys) for item in sidecar_items),
        "raw_sql_score_outside_sidecar": sum(item.raw_sql_score for item in non_sidecar_items),
        "row_types_importers": sum(1 for item in propstore_items if item.row_types_imports),
        "row_types_import_count": sum(item.row_types_imports for item in propstore_items),
        "sidecar_importers_outside_sidecar": sum(1 for item in non_sidecar_items if item.sidecar_imports),
        "sidecar_import_count_outside_sidecar": sum(item.sidecar_imports for item in non_sidecar_items),
        "quire_importers": sum(1 for item in propstore_items if item.quire_imports),
        "table_name_mentions_outside_sidecar": sum(len(item.table_name_mentions) for item in non_sidecar_items),
        "class_surfaces_app_world": app_world_wrapper_classes,
        "codec_methods_families_source": sum(
            len(item.codec_methods)
            for item in propstore_items
            if _relative(item.path, root).startswith(("propstore/families/", "propstore/source/"))
        ),
    }


def _repeated_projection_fields(items: list[FileInventory], root: Path) -> dict[str, list[str]]:
    field_files: dict[str, set[str]] = defaultdict(set)
    for item in items:
        if not _relative(item.path, root).startswith("propstore/"):
            continue
        for name in item.projection_columns:
            field_files[name].add(_relative(item.path, root))
    return {
        name: sorted(paths)
        for name, paths in sorted(field_files.items(), key=lambda pair: (-len(pair[1]), pair[0]))
        if len(paths) > 1
    }


def _sidecar_dispositions(items: list[FileInventory], root: Path) -> list[dict[str, Any]]:
    records = []
    for item in items:
        rel = _relative(item.path, root)
        if not rel.startswith("propstore/sidecar/"):
            continue
        disposition = "needs-ledger"
        if item.projection_columns or item.fts_projections or item.projection_foreign_keys:
            disposition = "derived-declaration-owner"
        elif item.rowid_vec_projections or item.embedding_status_projections:
            disposition = "vector-declaration-owner"
        elif rel.endswith("sqlite.py"):
            disposition = "quire-owned-candidate"
        elif rel.endswith("query.py"):
            disposition = "retained-product-escape-hatch-candidate"
        records.append(
            {
                "path": rel,
                "suggested_disposition": disposition,
                "projection_columns": len(item.projection_columns),
                "projection_tables": len(item.projection_tables),
                "fts_projections": len(item.fts_projections),
                "fk_edges": len(item.projection_foreign_keys),
                "vec_declarations": len(item.rowid_vec_projections) + len(item.embedding_status_projections),
                "raw_sql_score": item.raw_sql_score,
                "class_surfaces": item.class_surfaces,
            }
        )
    return records


def _source_local_canonical_overlap(items: list[FileInventory], root: Path) -> list[dict[str, Any]]:
    source_fields: set[str] = set()
    family_fields: dict[str, set[str]] = defaultdict(set)
    for item in items:
        rel = _relative(item.path, root)
        if rel == "propstore/families/documents/sources.py":
            source_fields.update(item.field_mentions)
        elif rel.startswith("propstore/families/"):
            parts = Path(rel).parts
            if len(parts) >= 3:
                family_fields[parts[2]].update(item.field_mentions)
    records = []
    for family, fields in sorted(family_fields.items()):
        overlap = sorted(source_fields & fields)
        if overlap:
            records.append({"family": family, "fields": overlap, "count": len(overlap)})
    return records


def build_json_report(items: list[FileInventory], root: Path) -> dict[str, Any]:
    files = [_file_record(item, root) for item in items]
    return {
        "schema_version": 1,
        "root": str(root),
        "summary": _summary_metrics(items, root),
        "repeated_projection_fields": _repeated_projection_fields(items, root),
        "sidecar_dispositions": _sidecar_dispositions(items, root),
        "source_local_canonical_overlap": _source_local_canonical_overlap(items, root),
        "files": files,
    }


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
                sum(len(item.class_surfaces) for item in bucket_items),
            )
        )
    _print_table(
        ("package", "lines", "projection_columns", "raw_sql_score", "codec_methods", "mapping_hints", "class_surfaces"),
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
            len(item.class_surfaces),
        )
        for item in _top(propstore_items, "declaration_density", limit)
    ]
    _print_table(("path", "score", "projection_columns", "codecs", "mapping_hints", "class_surfaces"), rows)

    print()
    print("## FTS Vector and FK Declarations")
    rows = [
        (
            _relative(item.path, root),
            len(item.fts_projections),
            len(item.rowid_vec_projections),
            len(item.embedding_status_projections),
            len(item.projection_foreign_keys),
            ", ".join((item.fts_projections + item.rowid_vec_projections + item.embedding_status_projections)[:8]),
        )
        for item in sorted(
            [
                item
                for item in propstore_items
                if item.fts_projections
                or item.rowid_vec_projections
                or item.embedding_status_projections
                or item.projection_foreign_keys
            ],
            key=lambda item: (
                len(item.fts_projections)
                + len(item.rowid_vec_projections)
                + len(item.embedding_status_projections)
                + len(item.projection_foreign_keys),
                str(item.path),
            ),
            reverse=True,
        )[:limit]
    ]
    _print_table(("path", "fts", "rowid_vec", "embedding_status", "fk_edges", "sample_names"), rows)

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
    print("## Quire Import Surface")
    rows = [
        (
            _relative(item.path, root),
            item.quire_imports,
            ", ".join(sorted(set(item.quire_import_symbols))[:12]),
        )
        for item in sorted(
            [item for item in propstore_items if item.quire_imports],
            key=lambda item: (item.quire_imports, str(item.path)),
            reverse=True,
        )[:limit]
    ]
    _print_table(("path", "quire_imports", "sample_symbols"), rows)

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
    print("## Class Definition Surfaces")
    rows = [
        (
            _relative(item.path, root),
            len(item.class_surfaces),
            item.json_report_mixins,
            ", ".join(sorted(set(item.class_surfaces))[:12]),
        )
        for item in sorted(
            [item for item in propstore_items if item.class_surfaces],
            key=lambda item: (len(item.class_surfaces), str(item.path)),
            reverse=True,
        )[:limit]
    ]
    _print_table(("path", "class_surfaces", "json_report_mixins", "sample_names"), rows)

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
    print("## Sidecar File Disposition Candidates")
    rows = [
        (
            record["path"],
            record["suggested_disposition"],
            record["projection_columns"],
            record["fts_projections"],
            record["fk_edges"],
            record["vec_declarations"],
            record["raw_sql_score"],
        )
        for record in _sidecar_dispositions(items, root)[:limit]
    ]
    _print_table(("path", "suggested_disposition", "projection_columns", "fts", "fk_edges", "vec", "raw_sql_score"), rows)

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


def _load_summary(path: Path) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    summary = data.get("summary")
    if not isinstance(summary, dict):
        raise ValueError(f"{path} does not contain a summary object")
    result: dict[str, int] = {}
    for key, value in summary.items():
        if isinstance(value, int):
            result[key] = value
    return result


def compare_baseline(current: dict[str, int], baseline_path: Path, metrics: list[str]) -> int:
    baseline = _load_summary(baseline_path)
    failed = False
    for metric in metrics:
        if metric not in baseline:
            print(f"missing baseline metric: {metric}")
            failed = True
            continue
        if metric not in current:
            print(f"missing current metric: {metric}")
            failed = True
            continue
        old = baseline[metric]
        new = current[metric]
        if new >= old:
            print(f"{metric}: no improvement ({old} -> {new})")
            failed = True
        else:
            print(f"{metric}: improved ({old} -> {new})")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory typed metadata cleanup surfaces.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--compare-baseline", type=Path)
    parser.add_argument("--require-improvement", action="append", default=[])
    args = parser.parse_args()

    root = args.root.resolve()
    items = collect_inventory(root)
    report = build_json_report(items, root)
    if args.compare_baseline:
        return compare_baseline(
            report["summary"],
            args.compare_baseline,
            list(args.require_improvement),
        )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        render_markdown(items, root, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
