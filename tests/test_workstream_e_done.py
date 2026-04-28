from __future__ import annotations

from pathlib import Path


def test_workstream_e_done() -> None:
    ws_file = Path("reviews/2026-04-26-claude/workstreams/WS-E-source-promote.md")
    index_file = Path("reviews/2026-04-26-claude/workstreams/INDEX.md")
    gaps_file = Path("docs/gaps.md")

    ws_text = ws_file.read_text(encoding="utf-8")
    index_text = index_file.read_text(encoding="utf-8")
    gaps_text = gaps_file.read_text(encoding="utf-8")

    assert "**Status**: CLOSED" in ws_text
    assert "| WS-E | Source-promote correctness | CLOSED" in index_text
    assert "WS-E source-promote correctness" in gaps_text
