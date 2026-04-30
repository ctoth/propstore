from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WS_FILE = ROOT / "reviews/2026-04-26-claude/workstreams/WS-M-provenance.md"
REPORT = ROOT / "reviews/2026-04-26-claude/workstreams/reports/WS-M-closure.md"


def test_workstream_m_is_closed_with_report() -> None:
    text = WS_FILE.read_text(encoding="utf-8")

    assert "**Status**: CLOSED " in text
    assert REPORT.exists()
