from __future__ import annotations

from pathlib import Path


ARGUMENTATION_WS_O_ARG_SHA = "f8ebd8575681f150e658c733cf0b25a265966503"


def test_workstream_o_arg_pin_done() -> None:
    root = Path(__file__).resolve().parents[2]

    assert ARGUMENTATION_WS_O_ARG_SHA in (root / "pyproject.toml").read_text(encoding="utf-8")
    assert ARGUMENTATION_WS_O_ARG_SHA in (root / "uv.lock").read_text(encoding="utf-8")
