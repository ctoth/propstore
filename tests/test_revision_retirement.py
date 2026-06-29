from __future__ import annotations

import importlib.util
from pathlib import Path


def test_drifted_revision_package_is_retired() -> None:
    assert importlib.util.find_spec("propstore.revision") is None


def test_active_surfaces_do_not_reference_retired_revision_package() -> None:
    candidate_paths = [
        Path("propstore/world/bound.py"),
        Path("propstore/worldline/revision_capture.py"),
        Path("propstore/worldline/revision_types.py"),
        Path("docs/atms.md"),
        Path("docs/argumentation.md"),
    ]
    paths = [path for path in candidate_paths if path.exists()]

    offenders = [
        str(path)
        for path in paths
        if "propstore.revision" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []
