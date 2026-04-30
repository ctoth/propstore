from __future__ import annotations

import os
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def _import_linter_lock():
    lock_path = Path(".tmp/import-linter-tests.lock")
    lock_path.parent.mkdir(exist_ok=True)
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            time.sleep(0.05)
    try:
        yield
    finally:
        os.close(fd)
        lock_path.unlink(missing_ok=True)


def test_importlinter_layer_contracts_are_clean() -> None:
    command = ["uv", "run"]
    if os.environ.get("PROPSTORE_UV_NO_SOURCES") == "1":
        command.extend(["--locked", "--no-sources"])
    command.append("lint-imports")

    with _import_linter_lock():
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

    assert result.returncode == 0, result.stdout + result.stderr
