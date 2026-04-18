"""Tests for artifact-boundary YAML helpers."""
from __future__ import annotations

from pathlib import Path

import yaml
import pytest


def test_load_yaml_dir_returns_sorted_tuples(tmp_path: Path) -> None:
    """load_yaml_dir returns (stem, path, data) tuples sorted by filename."""
    from propstore.document_codecs import load_yaml_dir

    # Create two YAML files (b before a alphabetically reversed in creation)
    (tmp_path / "beta.yaml").write_text("id: concept2\nname: Beta\n")
    (tmp_path / "alpha.yaml").write_text("id: concept1\nname: Alpha\n")

    result = load_yaml_dir(tmp_path)
    assert len(result) == 2
    # Should be sorted: alpha first
    assert result[0][0] == "alpha"
    assert result[0][1] == tmp_path / "alpha.yaml"
    assert result[0][2] == {"id": "concept1", "name": "Alpha"}

    assert result[1][0] == "beta"
    assert result[1][1] == tmp_path / "beta.yaml"
    assert result[1][2] == {"id": "concept2", "name": "Beta"}


def test_load_yaml_dir_skips_non_yaml(tmp_path: Path) -> None:
    """load_yaml_dir ignores non-.yaml files and directories."""
    from propstore.document_codecs import load_yaml_dir

    (tmp_path / "good.yaml").write_text("x: 1\n")
    (tmp_path / "readme.txt").write_text("not yaml")
    (tmp_path / "subdir").mkdir()

    result = load_yaml_dir(tmp_path)
    assert len(result) == 1
    assert result[0][0] == "good"


def test_load_yaml_dir_empty_file_gives_empty_dict(tmp_path: Path) -> None:
    """An empty YAML file should produce an empty dict, not None."""
    from propstore.document_codecs import load_yaml_dir

    (tmp_path / "empty.yaml").write_text("")

    result = load_yaml_dir(tmp_path)
    assert len(result) == 1
    assert result[0][2] == {}


def test_load_yaml_dir_empty_directory(tmp_path: Path) -> None:
    """An empty directory returns an empty list."""
    from propstore.document_codecs import load_yaml_dir

    result = load_yaml_dir(tmp_path)
    assert result == []


def test_write_yaml_file_roundtrip(tmp_path: Path) -> None:
    """write_yaml_file writes YAML that can be read back identically."""
    from propstore.document_codecs import write_yaml_file

    path = tmp_path / "out.yaml"
    data = {"id": "concept1", "name": "Test", "unicode": "Rényi entropy"}
    write_yaml_file(path, data)

    with open(path, encoding="utf-8") as f:
        loaded = yaml.safe_load(f)

    assert loaded == data


def test_write_yaml_file_preserves_key_order(tmp_path: Path) -> None:
    """write_yaml_file preserves dict key insertion order (sort_keys=False)."""
    from propstore.document_codecs import write_yaml_file

    path = tmp_path / "ordered.yaml"
    data = {"z_last": 1, "a_first": 2, "m_middle": 3}
    write_yaml_file(path, data)

    text = path.read_text(encoding="utf-8")
    lines = [l.split(":")[0] for l in text.strip().splitlines()]
    assert lines == ["z_last", "a_first", "m_middle"]


def test_write_yaml_file_uses_block_style(tmp_path: Path) -> None:
    """write_yaml_file uses block style, not flow style for nested structures."""
    from propstore.document_codecs import write_yaml_file

    path = tmp_path / "block.yaml"
    data = {"items": [1, 2, 3]}
    write_yaml_file(path, data)

    text = path.read_text(encoding="utf-8")
    # Block style uses "- 1\n- 2\n" not "[1, 2, 3]"
    assert "{" not in text
    assert "[" not in text


def test_write_yaml_file_handles_unicode(tmp_path: Path) -> None:
    """write_yaml_file writes unicode directly, not escaped."""
    from propstore.document_codecs import write_yaml_file

    path = tmp_path / "unicode.yaml"
    data = {"name": "Rényi"}
    write_yaml_file(path, data)

    text = path.read_text(encoding="utf-8")
    assert "Rényi" in text  # not \xe9 escape
