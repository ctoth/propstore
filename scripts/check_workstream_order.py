"""Check that a workstream's phase headings satisfy its dependency order."""

from __future__ import annotations

import re
import sys
from pathlib import Path


PHASE_RE = re.compile(r"^## Phase \d+: (?P<title>.+)$", re.MULTILINE)
DEPENDENCY_SECTION_RE = re.compile(
    r"^## Dependency Order\s*$"
    r"(?P<body>.*?)"
    r"^## ",
    re.MULTILINE | re.DOTALL,
)
ORDER_ITEM_RE = re.compile(r"^\s*\d+\.\s+(?P<title>.+?)\s*$", re.MULTILINE)


def normalize(title: str) -> str:
    return title.strip().lower().replace("and", "and").replace("`", "")


def dependency_order(text: str) -> list[str]:
    match = DEPENDENCY_SECTION_RE.search(f"{text}\n## ")
    if match is None:
        raise ValueError("missing Dependency Order section")
    return [match.group("title").strip() for match in ORDER_ITEM_RE.finditer(match.group("body"))]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_workstream_order.py <workstream.md>", file=sys.stderr)
        return 2

    workstream = Path(sys.argv[1])
    text = workstream.read_text(encoding="utf-8")
    try:
        dependencies = dependency_order(text)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not dependencies:
        print("Dependency Order section has no numbered items", file=sys.stderr)
        return 1

    phase_titles = [match.group("title").strip() for match in PHASE_RE.finditer(text)]
    phase_by_normalized = {normalize(title): index for index, title in enumerate(phase_titles)}

    missing = [
        title
        for title in dependencies
        if normalize(title) not in phase_by_normalized
    ]
    if missing:
        for title in missing:
            print(f"missing phase heading: {title}", file=sys.stderr)
        return 1

    failures: list[str] = []
    for index, dependent in enumerate(dependencies):
        dependent_index = phase_by_normalized[normalize(dependent)]
        for prerequisite in dependencies[:index]:
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
