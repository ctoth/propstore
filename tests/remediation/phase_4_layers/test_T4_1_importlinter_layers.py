from __future__ import annotations

import subprocess


def test_importlinter_layer_contracts_are_clean() -> None:
    result = subprocess.run(
        ["uv", "run", "lint-imports"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
