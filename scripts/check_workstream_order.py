"""Check that split workstream child prerequisites follow phase order."""

from __future__ import annotations

import re
import sys
from pathlib import Path


PHASE_ORDER_SECTION_RE = re.compile(
    r"^## Phase Order\s*$"
    r"(?P<body>.*?)"
    r"^## ",
    re.MULTILINE | re.DOTALL,
)
LEGACY_PHASE_RE = re.compile(r"^## Phase \d+: (?P<title>.+)$", re.MULTILINE)
DEPENDENCY_SECTION_RE = re.compile(
    r"^## Dependency Order\s*$"
    r"(?P<body>.*?)"
    r"^## ",
    re.MULTILINE | re.DOTALL,
)
ORDER_ITEM_RE = re.compile(r"^\s*\d+\.\s+(?P<title>.+?)\s*$", re.MULTILINE)
TABLE_ROW_RE = re.compile(r"^\|(?P<cells>.+)\|\s*$")
FILE_REF_RE = re.compile(r"`(?P<path>[^`]+\.md)`")
PREREQ_SECTION_RE = re.compile(
    r"^## (?:Prerequisites|Prerequisite Gate Dependencies)\s*$"
    r"(?P<body>.*?)"
    r"^## ",
    re.MULTILINE | re.DOTALL,
)
KNOWN_PREREQUISITE_ALIASES = {
    "mechanical order check and current-state inventory confirmation": "00-index.md",
    "quire sqlachemy dependency and capability proof": "01-quire-capability-and-charter.md",
    "quire sqlalchemy dependency and capability proof": "01-quire-capability-and-charter.md",
    "quire charter/schema ir": "01-quire-capability-and-charter.md",
    "quire sqlachemy table/mapping/session/catalog engine": "02-quire-sqlalchemy-engine.md",
    "quire sqlalchemy table, mapping, session, and catalog": "02-quire-sqlalchemy-engine.md",
    "quire sqlachemy table, mapping, session, and catalog": "02-quire-sqlalchemy-engine.md",
    "quire sqlalchemy table/mapping/session/catalog engine": "02-quire-sqlalchemy-engine.md",
    "quire fts and vector implementation": "03-quire-fts-vector.md",
    "propstore build orchestration cutover": "04-propstore-build-orchestration.md",
    "source vertical slice": "05-source-and-diagnostics.md",
    "source and diagnostics cutover": "05-source-and-diagnostics.md",
    "source and source-diagnostic old paths": "05-source-and-diagnostics.md",
    "forms and sources cleanup closure": "06-forms-concepts-parameterizations.md",
    "forms, concepts, and parameterizations cutover": "06-forms-concepts-parameterizations.md",
    "concept/form/parameterization slice": "06-forms-concepts-parameterizations.md",
    "context/lifting slice": "07-contexts-lifting.md",
    "contexts and lifting cutover": "07-contexts-lifting.md",
    "claims and active claims cutover": "08-claims-active-claims.md",
    "relations, stances, and conflicts cutover": "09-relations-stances-conflicts.md",
    "justifications and micropublications cutover": "10-micropublications-justifications.md",
    "rules, grounding, calibration, and embeddings cutover": "11-rules-grounding-calibration-embeddings.md",
}
ALLOWED_EXTERNAL_REFS = {
    "architecture-wanted-outcome-2026-05-17.md",
    "code-inventory-2026-05-17.md",
    "quire-sqlalchemy-charter-cutover-workstream-2026-05-18.md",
}


def normalize(title: str) -> str:
    return title.strip().lower().replace("and", "and").replace("`", "")


def legacy_dependency_order(text: str) -> list[str]:
    match = DEPENDENCY_SECTION_RE.search(f"{text}\n## ")
    if match is None:
        raise ValueError("missing Dependency Order section")
    return [match.group("title").strip() for match in ORDER_ITEM_RE.finditer(match.group("body"))]


def phase_order_files(text: str) -> list[str]:
    match = PHASE_ORDER_SECTION_RE.search(f"{text}\n## ")
    if match is None:
        raise ValueError("missing Phase Order section")

    ordered: list[str] = []
    for line in match.group("body").splitlines():
        row = TABLE_ROW_RE.match(line.strip())
        if row is None:
            continue
        cells = [cell.strip() for cell in row.group("cells").split("|")]
        if len(cells) < 2 or cells[0] == "---" or cells[0].lower() == "phase":
            continue
        for file_match in FILE_REF_RE.finditer(cells[1]):
            filename = Path(file_match.group("path")).name
            if filename not in ordered:
                ordered.append(filename)

    return ordered


def prerequisite_files(text: str) -> set[str]:
    match = PREREQ_SECTION_RE.search(f"{text}\n## ")
    if match is None:
        return set()
    body = match.group("body")
    files = {Path(file_match.group("path")).name for file_match in FILE_REF_RE.finditer(body)}
    normalized_body = normalize(body)
    for alias, filename in KNOWN_PREREQUISITE_ALIASES.items():
        if alias in normalized_body:
            files.add(filename)
    return files


def check_split_workstream(workstream: Path, text: str) -> int:
    try:
        ordered_files = phase_order_files(text)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not ordered_files:
        print("Phase Order section has no child workstream file refs", file=sys.stderr)
        return 1

    order = {filename: index for index, filename in enumerate(ordered_files)}
    failures: list[str] = []
    for filename, index in order.items():
        child_path = workstream.parent / filename
        if not child_path.exists():
            failures.append(f"missing child workstream file: {filename}")
            continue
        child_text = child_path.read_text(encoding="utf-8")
        for prerequisite in sorted(prerequisite_files(child_text)):
            prerequisite_index = order.get(prerequisite)
            if prerequisite_index is None:
                if prerequisite in ALLOWED_EXTERNAL_REFS:
                    continue
                failures.append(f"{filename} references prerequisite outside phase order: {prerequisite}")
                continue
            if prerequisite_index > index:
                failures.append(f"{filename} depends on later phase {prerequisite}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    print(f"workstream order ok: {workstream}")
    return 0


def check_legacy_workstream(workstream: Path, text: str) -> int:
    try:
        dependencies = legacy_dependency_order(text)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not dependencies:
        print("Dependency Order section has no numbered items", file=sys.stderr)
        return 1

    phase_titles = [match.group("title").strip() for match in LEGACY_PHASE_RE.finditer(text)]
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


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_workstream_order.py <workstream.md>", file=sys.stderr)
        return 2

    workstream = Path(sys.argv[1])
    text = workstream.read_text(encoding="utf-8")
    if PHASE_ORDER_SECTION_RE.search(f"{text}\n## ") is not None:
        return check_split_workstream(workstream, text)
    return check_legacy_workstream(workstream, text)


if __name__ == "__main__":
    raise SystemExit(main())
