"""Rename the `compiler` package to `propstore` using rope."""

from pathlib import Path

from rope.base.project import Project
from rope.refactor.rename import Rename


def main():
    root = Path(__file__).resolve().parent.parent
    project = Project(str(root))

    try:
        resource = project.get_resource("compiler/__init__.py")
        print(f"Found resource: {resource.path}")

        # Offset 0 targets the module/package name itself
        renamer = Rename(project, resource, offset=None)
        changes = renamer.get_changes("propstore")

        print("Planned changes:")
        print(changes.get_description())
        print()

        project.do(changes)
        print("Rename applied successfully.")
    finally:
        project.close()


if __name__ == "__main__":
    main()
