"""Verify the May 2026 request audit covers the generated request ledger.

This is an audit helper, not a refactor tool. It checks that every non-sentinel
ledger row is represented either by a literal ``- request N:`` entry under the
matching day or by an explicit duplicate replay marker covering that number.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


LEDGER_ROW_RE = re.compile(r"^\| (?P<day>\d{4}-\d{2}-\d{2}) \| (?P<num>\d+) \|")
DAY_RE = re.compile(r"^## (?P<day>\d{4}-\d{2}-\d{2})$")
REQUEST_RE = re.compile(r"^- request (?P<num>\d+):")
PRE_HEADER_REQUEST_RE = re.compile(r"^- pre-header request (?P<num>\d+):")
CARRIED_OVER_REQUEST_RE = re.compile(r"^- carried-over request (?P<num>\d+):")
DUPLICATE_RE = re.compile(
    r"^- duplicate replay marker for request numbers (?P<start>\d+) through (?P<end>\d+):"
)


@dataclass(frozen=True)
class Coverage:
    literal: set[int]
    duplicate: set[int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    return parser.parse_args()


def parse_ledger(path: Path) -> dict[str, set[int]]:
    by_day: dict[str, set[int]] = defaultdict(set)
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            match = LEDGER_ROW_RE.match(line)
            if match is None:
                continue
            number = int(match.group("num"))
            if number == 0:
                continue
            by_day[match.group("day")].add(number)
    return dict(by_day)


def parse_audit(path: Path) -> dict[str, Coverage]:
    literal: dict[str, set[int]] = defaultdict(set)
    duplicate: dict[str, set[int]] = defaultdict(set)
    current_day: str | None = None
    request_target_day: str | None = None
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            day_match = DAY_RE.match(line.rstrip())
            if day_match is not None:
                current_day = day_match.group("day")
                request_target_day = current_day
                continue
            if current_day is None:
                continue
            if "pre-header cluster from generated" in line:
                request_target_day = (
                    date.fromisoformat(current_day) - timedelta(days=1)
                ).isoformat()
                continue
            if line.startswith("Explicit ") and "generated heading" in line:
                request_target_day = current_day
                continue
            request_match = REQUEST_RE.match(line)
            if request_match is not None:
                literal[request_target_day or current_day].add(int(request_match.group("num")))
                continue
            pre_header_match = PRE_HEADER_REQUEST_RE.match(line)
            if pre_header_match is not None:
                source_day = date.fromisoformat(current_day) - timedelta(days=1)
                literal[source_day.isoformat()].add(int(pre_header_match.group("num")))
                continue
            carried_match = CARRIED_OVER_REQUEST_RE.match(line)
            if carried_match is not None:
                source_day = date.fromisoformat(current_day) - timedelta(days=1)
                literal[source_day.isoformat()].add(int(carried_match.group("num")))
                continue
            duplicate_match = DUPLICATE_RE.match(line)
            if duplicate_match is not None:
                start = int(duplicate_match.group("start"))
                end = int(duplicate_match.group("end"))
                duplicate[current_day].update(range(start, end + 1))
    days = set(literal) | set(duplicate)
    return {
        day: Coverage(
            literal=set(literal.get(day, set())),
            duplicate=set(duplicate.get(day, set())),
        )
        for day in days
    }


def summarize_numbers(numbers: set[int]) -> str:
    if not numbers:
        return "-"
    ordered = sorted(numbers)
    ranges: list[str] = []
    start = previous = ordered[0]
    for number in ordered[1:]:
        if number == previous + 1:
            previous = number
            continue
        ranges.append(f"{start}" if start == previous else f"{start}-{previous}")
        start = previous = number
    ranges.append(f"{start}" if start == previous else f"{start}-{previous}")
    return ", ".join(ranges)


def main() -> int:
    args = parse_args()
    ledger = parse_ledger(args.ledger)
    audit = parse_audit(args.audit)

    failed = False
    all_days = sorted(set(ledger) | set(audit))
    for day in all_days:
        expected = ledger.get(day, set())
        coverage = audit.get(day, Coverage(literal=set(), duplicate=set()))
        covered = coverage.literal | coverage.duplicate
        missing = expected - covered
        extra = covered - expected
        overlap = coverage.literal & coverage.duplicate
        if missing or extra or overlap:
            failed = True
            print(f"{day}: FAIL")
            if missing:
                print(f"  missing: {summarize_numbers(missing)}")
            if extra:
                print(f"  extra: {summarize_numbers(extra)}")
            if overlap:
                print(f"  literal_duplicate_overlap: {summarize_numbers(overlap)}")
        else:
            print(
                f"{day}: ok "
                f"ledger={len(expected)} literal={len(coverage.literal)} "
                f"duplicate={len(coverage.duplicate)}"
            )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
