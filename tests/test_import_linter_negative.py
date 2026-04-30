from __future__ import annotations

import os
import subprocess
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


LAYER_IMPORT_TARGETS = (
    "propstore.cli",
    "propstore.app",
    "propstore.world",
    "propstore.heuristic",
    "propstore.source",
    "propstore.storage",
)


@contextmanager
def _import_linter_lock() -> Iterator[None]:
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


def _lint_imports_command() -> list[str]:
    command = ["uv", "run"]
    if os.environ.get("PROPSTORE_UV_NO_SOURCES") == "1":
        command.extend(["--locked", "--no-sources"])
    command.append("lint-imports")
    return command


def _module_path(module_name: str) -> Path:
    package_parts = module_name.split(".")
    return Path(*package_parts)


def _violation_pairs() -> list[tuple[str, str]]:
    return [
        (lower, higher)
        for lower_index, lower in enumerate(LAYER_IMPORT_TARGETS)
        for higher in LAYER_IMPORT_TARGETS[:lower_index]
    ]


def test_import_linter_rejects_every_lower_to_higher_layer_import() -> None:
    for lower_module, higher_module in _violation_pairs():
        fixture = _module_path(lower_module) / f"_ws_n2_violation_{uuid.uuid4().hex}.py"
        with _import_linter_lock():
            try:
                fixture.write_text(f"import {higher_module}\n", encoding="utf-8")
                result = subprocess.run(
                    _lint_imports_command(),
                    capture_output=True,
                    text=True,
                    check=False,
                )
            finally:
                fixture.unlink(missing_ok=True)

        output = result.stdout + result.stderr
        assert result.returncode != 0, (
            f"{lower_module} importing {higher_module} was accepted\n{output}"
        )
        assert "propstore six-layer architecture" in output
