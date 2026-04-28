from __future__ import annotations

from pathlib import Path


def test_workstream_q_cas_done() -> None:
    ws_file = Path("reviews/2026-04-26-claude/workstreams/WS-Q-cas-branch-head-discipline.md")
    index_file = Path("reviews/2026-04-26-claude/workstreams/INDEX.md")
    gaps_file = Path("docs/gaps.md")

    ws_text = ws_file.read_text(encoding="utf-8")
    index_text = index_file.read_text(encoding="utf-8")
    gaps_text = gaps_file.read_text(encoding="utf-8")

    assert "**Status**: CLOSED" in ws_text
    assert "| **WS-Q-cas** | Branch-head CAS discipline at propstore call sites | CLOSED" in index_text
    assert "WS-Q-cas branch-head CAS discipline" in gaps_text
