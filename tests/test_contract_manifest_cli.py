"""CLI tests for ``pks contract-manifest`` (adapter over the manifest builder)."""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.contracts import build_propstore_contract_manifest


def test_contract_manifest_renders_to_stdout(tmp_path: Path) -> None:
    result = CliRunner().invoke(cli, ["-C", str(tmp_path), "contract-manifest"])
    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["package"]["name"] == "propstore"
    assert payload["registry"]["name"] == build_propstore_contract_manifest().registry_name
    assert payload["contracts"]


def test_contract_manifest_writes_output_file(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "manifest.yaml"
    result = CliRunner().invoke(
        cli, ["-C", str(tmp_path), "contract-manifest", "--output", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert f"Wrote {out}" in result.output
    assert out.is_file()
    parsed = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert parsed["package"]["name"] == "propstore"
