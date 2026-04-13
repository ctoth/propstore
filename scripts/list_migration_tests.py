from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MigrationNode:
    path: Path
    node_id: str


def _is_migration_marker(node: ast.AST) -> bool:
    if isinstance(node, ast.Attribute):
        return (
            node.attr == "migration"
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "mark"
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id == "pytest"
        )
    if isinstance(node, ast.Call):
        return _is_migration_marker(node.func)
    return False


def _module_has_migration_mark(tree: ast.Module) -> bool:
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "pytestmark" for target in statement.targets):
            continue
        value = statement.value
        if _is_migration_marker(value):
            return True
        if isinstance(value, (ast.List, ast.Tuple)):
            return any(_is_migration_marker(element) for element in value.elts)
    return False


def _decorators_include_migration(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> bool:
    return any(_is_migration_marker(decorator) for decorator in node.decorator_list)


def _collect_nodes(path: Path) -> list[MigrationNode]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    module_marked = _module_has_migration_mark(tree)
    results: list[MigrationNode] = []

    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)) and statement.name.startswith("test_"):
            if module_marked or _decorators_include_migration(statement):
                results.append(MigrationNode(path, f"{path.as_posix()}::{statement.name}"))
            continue
        if isinstance(statement, ast.ClassDef) and statement.name.startswith("Test"):
            class_marked = module_marked or _decorators_include_migration(statement)
            for member in statement.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and member.name.startswith("test_"):
                    if class_marked or _decorators_include_migration(member):
                        results.append(
                            MigrationNode(path, f"{path.as_posix()}::{statement.name}::{member.name}")
                        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="List migration-marked tests in the suite.")
    parser.add_argument(
        "--root",
        default="tests",
        help="Root directory to scan. Defaults to tests.",
    )
    parser.add_argument(
        "--fail-on-any",
        action="store_true",
        help="Exit non-zero if any migration-marked tests are present.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    nodes: list[MigrationNode] = []
    for path in sorted(root.rglob("test_*.py")):
        nodes.extend(_collect_nodes(path))

    if not nodes:
        print("No migration-marked tests found.")
        return 0

    print(f"Found {len(nodes)} migration-marked test(s):")
    for node in nodes:
        print(node.node_id)
    return 1 if args.fail_on_any else 0


if __name__ == "__main__":
    raise SystemExit(main())
