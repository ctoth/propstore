from __future__ import annotations

from pathlib import Path


def test_source_extraction_provenance_uses_timezone_aware_utc() -> None:
    offenders = [
        str(path)
        for path in (
            Path("propstore/source/claims.py"),
            Path("propstore/source/relations.py"),
        )
        if "datetime.utcnow" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []
