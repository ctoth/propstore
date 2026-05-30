"""Build the propstore contract manifest from the source tree at git HEAD.

Phase 1 dev guard helper: the contract schema is materialized from Python, so
there is no checked-in manifest file to diff against. To gate charter changes on
a version bump in CI, this script exports the source tree at ``HEAD`` into a
temporary directory, builds the contract manifest from *that* (older) source in
an isolated subprocess, and prints the manifest YAML to stdout.

The test compares the YAML this prints (the previous manifest) against a
freshly-built manifest from the working tree via ``check_contract_manifest``.
Run standalone:

    uv run python scripts/build_head_contract_manifest.py

Exit code is non-zero (with a diagnostic on stderr) when HEAD cannot be
exported or built, so callers can skip rather than fail when not in a git
checkout.
"""

from __future__ import annotations

import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


_BUILD_SNIPPET = (
    "import sys; "
    "from propstore.contracts import build_propstore_contract_manifest; "
    "sys.stdout.buffer.write(build_propstore_contract_manifest().to_yaml())"
)


def export_head_tree(destination: Path) -> None:
    """Export the source tree at HEAD into *destination* via ``git archive``."""
    archive = subprocess.run(
        ["git", "archive", "HEAD"],
        check=True,
        capture_output=True,
    )
    tar_path = destination / "_head.tar"
    tar_path.write_bytes(archive.stdout)
    with tarfile.open(tar_path) as tar:
        tar.extractall(destination, filter="data")
    tar_path.unlink()


def build_head_manifest_yaml() -> bytes:
    """Return the contract manifest YAML built from HEAD's source tree."""
    with tempfile.TemporaryDirectory() as raw_dir:
        checkout = Path(raw_dir)
        export_head_tree(checkout)
        result = subprocess.run(
            [sys.executable, "-c", _BUILD_SNIPPET],
            check=True,
            capture_output=True,
            cwd=checkout,
        )
        return result.stdout


def main() -> int:
    try:
        sys.stdout.buffer.write(build_head_manifest_yaml())
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr.decode("utf-8", "replace"))
        return exc.returncode or 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
