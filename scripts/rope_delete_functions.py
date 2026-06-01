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
class FunctionRemoval:
    name: str
    path: str
    start_line: int
    end_line: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Delete Python functions and methods whose names match glob patterns "
            "or whose source contains requested text."
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
        help="Function-name glob. May be repeated.",
    )
    parser.add_argument(
        "--containing",
        action="append",
        dest="containing",
        default=None,
        help="Delete functions whose source contains this exact text. May be repeated.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root for the Rope project.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print matching functions without changing files.",
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


def _function_start(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    decorator_lines = [decorator.lineno for decorator in node.decorator_list]
    return min([node.lineno, *decorator_lines])


def _matching_ranges(
    source: str,
    path: str,
    patterns: tuple[str, ...],
    containing: tuple[str, ...],
) -> list[FunctionRemoval]:
    tree = ast.parse(source, filename=path, type_comments=True)
    lines = source.splitlines(keepends=True)
    removals: list[FunctionRemoval] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if node.end_lineno is None:
            raise ValueError(f"{path}:{node.lineno}: missing function end line")
        function_source = "".join(lines[_function_start(node) - 1 : node.end_lineno])
        if not _matches_name(node.name, patterns) and not _matches_source(
            function_source, containing
        ):
            continue
        removals.append(
            FunctionRemoval(
                name=node.name,
                path=path,
                start_line=_function_start(node),
                end_line=node.end_lineno,
            )
        )
    return sorted(removals, key=lambda item: (item.start_line, item.end_line))


def _without_overlapping_ranges(
    removals: list[FunctionRemoval],
) -> list[FunctionRemoval]:
    kept: list[FunctionRemoval] = []
    for removal in removals:
        if kept and removal.start_line <= kept[-1].end_line:
            previous = kept[-1]
            kept[-1] = FunctionRemoval(
                name=previous.name,
                path=previous.path,
                start_line=min(previous.start_line, removal.start_line),
                end_line=max(previous.end_line, removal.end_line),
            )
            continue
        kept.append(removal)
    return kept


def _delete_ranges(source: str, removals: list[FunctionRemoval]) -> str:
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
) -> tuple[ChangeSet, list[FunctionRemoval]]:
    changes = ChangeSet("delete matching functions")
    all_removals: list[FunctionRemoval] = []
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


def _format_changed_files(root: Path, removals: list[FunctionRemoval]) -> None:
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
    patterns = tuple(args.patterns or DEFAULT_PATTERNS)
    containing = tuple(args.containing or ())
    files = _python_files(root, tuple(args.paths))

    project = Project(str(root), ropefolder=None, ignored_resources=IGNORED_RESOURCES)
    try:
        changes, removals = _planned_changes(project, root, files, patterns, containing)
        for removal in removals:
            print(
                f"{removal.path}:{removal.start_line}-{removal.end_line}: "
                f"{removal.name}"
            )
        print(f"matched {len(removals)} function(s)")
        if removals and not args.dry_run:
            project.do(changes)
            _format_changed_files(root, removals)
    finally:
        project.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
