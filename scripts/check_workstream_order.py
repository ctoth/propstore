"""Check that a workstream's phase headings satisfy its dependency order."""

from __future__ import annotations

import re
import sys
from pathlib import Path


DEPENDENCIES = {
    "Relations module consolidation": (),
    "Predicate canonical artifact cutover": ("Relations module consolidation",),
    "Rule canonical artifact cutover": ("Predicate canonical artifact cutover",),
    "Rule-superiority artifact cutover": ("Rule canonical artifact cutover",),
    "Research-papers plugin and `pks` workflow updates": (
        "Rule-superiority artifact cutover",
    ),
    "Boilerplate standardization": (
        "Research-papers plugin and `pks` workflow updates",
    ),
    "Contract, manifest, documentation, and full-suite closure": (
        "Boilerplate standardization",
    ),
}

PHASE_RE = re.compile(r"^## Phase \d+: (?P<title>.+)$", re.MULTILINE)


def normalize(title: str) -> str:
    return title.strip().lower().replace("and", "and").replace("`", "")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_workstream_order.py <workstream.md>", file=sys.stderr)
        return 2

    workstream = Path(sys.argv[1])
    text = workstream.read_text(encoding="utf-8")
    phase_titles = [match.group("title").strip() for match in PHASE_RE.finditer(text)]
    phase_by_normalized = {normalize(title): index for index, title in enumerate(phase_titles)}

    missing = [
        title
        for title in DEPENDENCIES
        if normalize(title) not in phase_by_normalized
    ]
    if missing:
        for title in missing:
            print(f"missing phase heading: {title}", file=sys.stderr)
        return 1

    failures: list[str] = []
    for dependent, prerequisites in DEPENDENCIES.items():
        dependent_index = phase_by_normalized[normalize(dependent)]
        for prerequisite in prerequisites:
            prerequisite_index = phase_by_normalized[normalize(prerequisite)]
            if prerequisite_index >= dependent_index:
                failures.append(f"{dependent!r} must appear after {prerequisite!r}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    print(f"workstream order ok: {workstream}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
