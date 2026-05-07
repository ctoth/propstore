from __future__ import annotations

import re
import sys
from pathlib import Path


WORKSTREAM = Path("reviews/2026-05-05-agm-proposal/workstreams/WS-AGM-propstore-belief-set-cutover.md")
PHASE_RE = re.compile(r"^### Phase (?P<number>\d+) ")


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else WORKSTREAM
    text = path.read_text(encoding="utf-8")
    phases = [int(match.group("number")) for line in text.splitlines() if (match := PHASE_RE.match(line))]
    expected = list(range(0, 14))
    if phases != expected:
        print(f"AGM workstream phases are not linear 0..13: {phases}", file=sys.stderr)
        return 1

    phase_positions = {phase: phases.index(phase) for phase in phases}
    dependencies = {
        1: (0,),
        2: (0, 1),
        3: (2,),
        4: (3,),
        5: (3, 4),
        6: (3,),
        7: (3, 4, 5),
        8: (3, 7),
        9: (3, 4, 5, 7, 8),
        10: (9,),
        11: (1,),
        12: (0,),
        13: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12),
    }
    violations: list[str] = []
    for phase, prereqs in dependencies.items():
        for prereq in prereqs:
            if phase_positions[prereq] > phase_positions[phase]:
                violations.append(f"Phase {phase} appears before prerequisite Phase {prereq}")
    if violations:
        print("\n".join(violations), file=sys.stderr)
        return 1

    print(f"{path}: AGM workstream phase order is dependency-safe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
