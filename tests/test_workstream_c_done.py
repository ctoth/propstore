from __future__ import annotations

from pathlib import Path


def test_workstream_c_done() -> None:
    ws_file = Path("reviews/2026-04-26-claude/workstreams/WS-C-sidecar-atomicity.md")
    index_file = Path("reviews/2026-04-26-claude/workstreams/INDEX.md")
    gaps_file = Path("docs/gaps.md")

    ws_text = ws_file.read_text(encoding="utf-8")
    index_text = index_file.read_text(encoding="utf-8")
    gaps_text = gaps_file.read_text(encoding="utf-8")

    assert "**Status**: CLOSED" in ws_text
    assert "| WS-C | Sidecar atomicity & SQLite discipline | CLOSED" in index_text
    assert "WS-C sidecar atomicity" in gaps_text
