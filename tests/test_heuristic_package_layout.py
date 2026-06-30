"""Class-B discipline gate: heuristic modules live only inside the heuristic package.

The heuristic layer (CLAUDE.md layer 3) is a self-contained package; none of its
modules leak to the top-level ``propstore`` namespace.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEURISTIC_MODULES = (
    "embed",
    "classify",
    "relate",
    "calibrate",
    "predicate_extraction",
    "rule_extraction",
)


def test_heuristic_modules_live_only_inside_heuristic_package() -> None:
    for name in HEURISTIC_MODULES:
        assert not ROOT.joinpath("propstore", f"{name}.py").exists()
        assert ROOT.joinpath("propstore", "heuristic", f"{name}.py").exists()
