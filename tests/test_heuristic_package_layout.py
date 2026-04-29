from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEURISTIC_MODULES = ("embed", "classify", "relate", "calibrate")


def test_heuristic_modules_live_only_inside_heuristic_package() -> None:
    for name in HEURISTIC_MODULES:
        assert not ROOT.joinpath("propstore", f"{name}.py").exists()
        assert ROOT.joinpath("propstore", "heuristic", f"{name}.py").exists()
