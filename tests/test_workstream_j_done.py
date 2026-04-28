"""Closure sentinel for WS-J worldline determinism."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSTREAMS = ROOT / "reviews" / "2026-04-26-claude" / "workstreams"


def test_workstream_j_done() -> None:
    ws_j = WORKSTREAMS / "WS-J-worldline-causal.md"
    index = WORKSTREAMS / "INDEX.md"
    gaps = ROOT / "docs" / "gaps.md"

    assert (WORKSTREAMS / "WS-J2-intervention-world.md").exists()
    assert (WORKSTREAMS / "WS-J3-spohn-kappa.md").exists()
    assert (WORKSTREAMS / "WS-J4-bonanno-merge.md").exists()
    assert (WORKSTREAMS / "WS-J5-lifting-closure.md").exists()
    assert (WORKSTREAMS / "WS-J6-worldline-stale-fingerprint.md").exists()

    assert "**Status**: CLOSED 9eefe5ce" in ws_j.read_text(encoding="utf-8")
    assert "| WS-J | Worldline determinism, hashing, OverlayWorld rename | CLOSED 9eefe5ce" in index.read_text(
        encoding="utf-8"
    )
    assert "Closed 2026-04-28 (WS-J worldline determinism" in gaps.read_text(
        encoding="utf-8"
    )
