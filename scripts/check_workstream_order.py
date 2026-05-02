from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PHASE_RE = re.compile(r"^## Phase (-?\d+) - ")
EXPECTED_ORDER = [-1, 0, 1, 2, 3, 4, 5, 6, 7, 8]


def phase_order(plan_path: Path) -> list[int]:
    phases: list[int] = []
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        match = PHASE_RE.match(line)
        if match:
            phases.append(int(match.group(1)))
    return phases


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify that a workstream plan's phase headings are topologically ordered.",
    )
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()

    actual_order = phase_order(args.plan)
    if actual_order != EXPECTED_ORDER:
        print(
            f"phase order mismatch: expected {EXPECTED_ORDER}, got {actual_order}",
            file=sys.stderr,
        )
        return 1

    print(f"phase order ok: {' -> '.join(str(phase) for phase in actual_order)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
