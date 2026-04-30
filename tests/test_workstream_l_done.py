from __future__ import annotations

from pathlib import Path

def test_workstream_l_status_is_closed() -> None:
    workstream = Path("reviews/2026-04-26-claude/workstreams/WS-L-merge.md")
    text = workstream.read_text(encoding="utf-8")
    assert "**Status**: CLOSED" in text
