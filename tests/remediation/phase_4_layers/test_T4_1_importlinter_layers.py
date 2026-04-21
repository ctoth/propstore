from __future__ import annotations

import subprocess


def test_importlinter_catches_known_layer_violations() -> None:
    result = subprocess.run(
        ["uv", "run", "lint-imports"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    output = result.stdout + result.stderr
    for expected in (
        "storage -> merge",
        "source -> heuristic",
        "concept -> argumentation",
        "support_revision -> belief_set",
        "worldline -> support_revision",
        "aspic_bridge -> gunray",
    ):
        assert expected in output
