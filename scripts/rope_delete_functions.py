from __future__ import annotations

import argparse
import ast
import fnmatch
import subprocess
from dataclasses import dataclass
from pathlib import Path

from rope.base.change import ChangeContents, ChangeSet
from rope.base.project import Project


IGNORED_RESOURCES = [
    ".git",
    ".git/*",
    ".hypothesis",
    ".hypothesis/*",
    ".mypy_cache",
    ".mypy_cache/*",
    ".pytest_cache",
    ".pytest_cache/*",
    ".ruff_cache",
    ".ruff_cache/*",
    ".tmp",
    ".tmp/*",
    ".venv",
    ".venv/*",
    "logs",
    "logs/*",
    "reports",
    "reports/*",
    "out",
    "out/*",
    "pyghidra_mcp_projects",
    "pyghidra_mcp_projects/*",
]


DEFAULT_PATTERNS = (
    "*to_payload*",
    "*from_payload*",
    "*to_document*",
    "*from_document*",
    "encode*document*",
    "decode*document*",
)


@dataclass(frozen=True)
class NodeRemoval:
    name: str
    kind: str
    path: str
    start_line: int
    end_line: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Delete Python functions, methods, and classes whose names match "
            "glob patterns or whose source contains requested text."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=("propstore", "tests", "scripts"),
        help="Files or directories to scan.",
    )
    parser.add_argument(
        "--pattern",
        action="append",
        dest="patterns",
        default=None,
        help="Function/class-name glob. May be repeated.",
    )
    parser.add_argument(
        "--containing",
        action="append",
        dest="containing",
        default=None,
        help="Delete functions/classes whose source contains this exact text. May be repeated.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root for the Rope project.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print matching nodes without changing files.",
    )
    return parser.parse_args()


def _python_files(root: Path, paths: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = (root / raw_path).resolve()
        if path.is_dir():
            files.extend(sorted(path.rglob("*.py")))
        elif path.suffix == ".py" and path.exists():
            files.append(path)
    return [
        path
        for path in files
        if ".venv" not in path.parts
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
    ]


def _matches_name(name: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns)


def _matches_source(source: str, containing: tuple[str, ...]) -> bool:
    return any(text in source for text in containing)


FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
ClassNode = ast.ClassDef


def _decorated_start(node: FunctionNode | ClassNode) -> int:
    decorator_lines = [decorator.lineno for decorator in node.decorator_list]
    return min([node.lineno, *decorator_lines])


def _node_range(node: ast.AST) -> tuple[int, int]:
    if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
        raise ValueError(f"{type(node).__name__} has no source range")
    end_line = node.end_lineno
    if end_line is None:
        raise ValueError(f"{type(node).__name__} has no end line")
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return _decorated_start(node), end_line
    return node.lineno, end_line


def _covers(removal: NodeRemoval, node: ast.AST) -> bool:
    start_line, end_line = _node_range(node)
    return removal.start_line <= start_line and end_line <= removal.end_line


def _ignorable_class_body_node(node: ast.AST) -> bool:
    return isinstance(node, ast.Pass) or (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _deleted_by(removals: list[NodeRemoval], node: ast.AST) -> bool:
    return any(_covers(removal, node) for removal in removals)


def _classes_empty_after_function_removal(
    tree: ast.AST, removals: list[NodeRemoval], path: str
) -> list[NodeRemoval]:
    class_removals: list[NodeRemoval] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if _deleted_by(removals, node):
            continue
        if node.end_lineno is None:
            raise ValueError(f"{path}:{node.lineno}: missing class end line")
        substantive_nodes = [
            child for child in node.body if not _ignorable_class_body_node(child)
        ]
        if not substantive_nodes:
            continue
        if all(_deleted_by(removals, child) for child in substantive_nodes):
            class_removals.append(
                NodeRemoval(
                    name=node.name,
                    kind="class",
                    path=path,
                    start_line=_decorated_start(node),
                    end_line=node.end_lineno,
                )
            )
    return class_removals


def _matching_ranges(
    source: str,
    path: str,
    patterns: tuple[str, ...],
    containing: tuple[str, ...],
) -> list[NodeRemoval]:
    tree = ast.parse(source, filename=path, type_comments=True)
    lines = source.splitlines(keepends=True)
    removals: list[NodeRemoval] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue
        if node.end_lineno is None:
            raise ValueError(f"{path}:{node.lineno}: missing node end line")
        node_source = "".join(lines[_decorated_start(node) - 1 : node.end_lineno])
        if not _matches_name(node.name, patterns) and not _matches_source(
            node_source, containing
        ):
            continue
        removals.append(
            NodeRemoval(
                name=node.name,
                kind=("class" if isinstance(node, ast.ClassDef) else "function"),
                path=path,
                start_line=_decorated_start(node),
                end_line=node.end_lineno,
            )
        )
    removals.extend(_classes_empty_after_function_removal(tree, removals, path))
    return sorted(removals, key=lambda item: (item.start_line, item.end_line))


def _without_overlapping_ranges(
    removals: list[NodeRemoval],
) -> list[NodeRemoval]:
    kept: list[NodeRemoval] = []
    for removal in removals:
        if kept and removal.start_line <= kept[-1].end_line:
            previous = kept[-1]
            kept[-1] = NodeRemoval(
                name=previous.name,
                kind=previous.kind,
                path=previous.path,
                start_line=min(previous.start_line, removal.start_line),
                end_line=max(previous.end_line, removal.end_line),
            )
            continue
        kept.append(removal)
    return kept


def _delete_ranges(source: str, removals: list[NodeRemoval]) -> str:
    lines = source.splitlines(keepends=True)
    for removal in reversed(_without_overlapping_ranges(removals)):
        del lines[removal.start_line - 1 : removal.end_line]
    return "".join(lines)


def _planned_changes(
    project: Project,
    root: Path,
    files: list[Path],
    patterns: tuple[str, ...],
    containing: tuple[str, ...],
) -> tuple[ChangeSet, list[NodeRemoval]]:
    changes = ChangeSet("delete matching functions/classes")
    all_removals: list[NodeRemoval] = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        resource = project.get_file(relative)
        source = resource.read()
        removals = _matching_ranges(source, relative, patterns, containing)
        if not removals:
            continue
        updated = _delete_ranges(source, removals)
        ast.parse(updated, filename=relative, type_comments=True)
        changes.add_change(ChangeContents(resource, updated, old_contents=source))
        all_removals.extend(removals)
    return changes, all_removals


def _format_changed_files(root: Path, removals: list[NodeRemoval]) -> None:
    paths = [removal.path for removal in removals]
    unique_paths = sorted(dict.fromkeys(paths))
    if not unique_paths:
        return
    subprocess.run(
        ["uv", "run", "ruff", "format", *unique_paths],
        cwd=root,
        check=True,
    )


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    containing = tuple(args.containing or ())
    patterns = tuple(args.patterns or (() if containing else DEFAULT_PATTERNS))
    files = _python_files(root, tuple(args.paths))

    project = Project(str(root), ropefolder=None, ignored_resources=IGNORED_RESOURCES)
    try:
        changes, removals = _planned_changes(project, root, files, patterns, containing)
        for removal in removals:
            print(
                f"{removal.path}:{removal.start_line}-{removal.end_line}: "
                f"{removal.kind} {removal.name}"
            )
        print(f"matched {len(removals)} node(s)")
        if removals and not args.dry_run:
            project.do(changes)
            _format_changed_files(root, removals)
    finally:
        project.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
