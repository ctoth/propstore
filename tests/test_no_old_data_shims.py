from __future__ import annotations

from pathlib import Path

from propstore.world.types import DecisionValueSource


def test_d3_old_data_shim_symbols_are_deleted() -> None:
    forbidden = {
        "_CONCEPT_STATUS_ALIASES": Path("propstore/core/concept_status.py"),
        "CONFIDENCE_FALLBACK": Path("propstore/world/types.py"),
        "(may be None for old data)": Path("propstore/world/types.py"),
        "Fall back to raw confidence when opinion is missing (old data)": Path(
            "propstore/world/types.py"
        ),
        "fallback: treat whole response as forward": Path("propstore/heuristic/classify.py"),
        "for backwards compatibility": Path("propstore/grounding/grounder.py"),
        '"propstore/aspic_bridge.py"': Path("pyproject.toml"),
    }

    offenders = [
        f"{path}:{needle}"
        for needle, path in forbidden.items()
        if needle in path.read_text(encoding="utf-8")
    ]

    assert "CONFIDENCE_FALLBACK" not in DecisionValueSource.__members__
    assert offenders == []
