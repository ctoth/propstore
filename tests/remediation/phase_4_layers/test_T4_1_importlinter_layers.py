from __future__ import annotations

import os
import subprocess


def test_importlinter_layer_contracts_are_clean() -> None:
    command = ["uv", "run"]
    if os.environ.get("PROPSTORE_UV_NO_SOURCES") == "1":
        command.extend(["--locked", "--no-sources"])
    command.append("lint-imports")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
