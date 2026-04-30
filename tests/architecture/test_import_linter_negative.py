from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_import_linter_rejects_heuristic_importing_source_finalize() -> None:
    fixture = Path("propstore/heuristic/_import_linter_negative_fixture.py")
    command = ["uv", "run"]
    if os.environ.get("PROPSTORE_UV_NO_SOURCES") == "1":
        command.extend(["--locked", "--no-sources"])
    command.append("lint-imports")

    try:
        fixture.write_text("from propstore.source import finalize\n")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        fixture.unlink(missing_ok=True)

    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert "heuristic -> source.finalize" in output
