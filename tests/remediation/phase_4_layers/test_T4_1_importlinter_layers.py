from __future__ import annotations

import configparser
import os
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

LEGACY_FORBIDDEN_CONTRACTS = {
    "importlinter:contract:storage-merge",
    "importlinter:contract:source-heuristic",
    "importlinter:contract:heuristic-source-finalize",
    "importlinter:contract:concept-argumentation",
    "importlinter:contract:worldline-support-revision",
}


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


def _contract_sections(parser: configparser.ConfigParser) -> list[str]:
    return [
        section
        for section in parser.sections()
        if section.startswith("importlinter:contract:")
    ]


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

    parser = configparser.ConfigParser()
    parser.read(Path(".importlinter"), encoding="utf-8")
    contract_sections = _contract_sections(parser)

    assert len(contract_sections) == 1
    assert parser.get(contract_sections[0], "type") == "layers"
    assert not (set(contract_sections) & LEGACY_FORBIDDEN_CONTRACTS)
    assert {
        parser.get(section, "type")
        for section in contract_sections
    } == {"layers"}
    assert not Path("tests/_allowlists/layered_contract_residual.txt").exists()
