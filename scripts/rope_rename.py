from __future__ import annotations

import argparse
from pathlib import Path

from rope.base.project import Project
from rope.refactor.rename import Rename


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="File containing the symbol to rename")
    parser.add_argument("name", help="Current symbol name")
    parser.add_argument("new_name", help="Replacement symbol name")
    parser.add_argument(
        "--root",
        default=".",
        help="Project root for the Rope project",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    target_path = Path(args.path).resolve()

    project = Project(str(root))
    try:
        resource = project.get_file(str(target_path.relative_to(root)).replace("\\", "/"))
        source = resource.read()
        offset = source.find(args.name)
        if offset < 0:
            raise SystemExit(f"symbol not found: {args.name}")
        changes = Rename(project, resource, offset).get_changes(args.new_name)
        project.do(changes)
    finally:
        project.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
