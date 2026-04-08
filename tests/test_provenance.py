"""Tests for propstore.provenance – stamp_provenance functionality."""

from __future__ import annotations

from pathlib import Path

from propstore.provenance import stamp_file


def test_stamp_yaml_file(tmp_path: Path) -> None:
    """Stamp a .yaml file and verify produced_by block appears."""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(
        "source:\n  name: test-paper\n  kind: paper\n",
        encoding="utf-8",
    )

    changed = stamp_file(
        yaml_file,
        agent="claude-opus-4-6",
        skill="paper-reader",
        plugin_version="1.0.0",
        timestamp="2026-04-07T12:00:00Z",
    )

    assert changed is True
    content = yaml_file.read_text(encoding="utf-8")
    assert "produced_by:" in content
    assert 'agent: "claude-opus-4-6"' in content
    assert 'skill: "paper-reader"' in content
    assert 'plugin_version: "1.0.0"' in content
    assert 'timestamp: "2026-04-07T12:00:00Z"' in content


def test_stamp_md_file(tmp_path: Path) -> None:
    """Stamp a .md file with existing frontmatter."""
    md_file = tmp_path / "notes.md"
    md_file.write_text(
        "---\ntitle: Test Paper\nauthor: Someone\n---\n\n# Content here\n",
        encoding="utf-8",
    )

    changed = stamp_file(
        md_file,
        agent="claude-opus-4-6",
        skill="paper-reader",
        timestamp="2026-04-07T12:00:00Z",
    )

    assert changed is True
    content = md_file.read_text(encoding="utf-8")
    assert "produced_by:" in content
    assert 'agent: "claude-opus-4-6"' in content
    assert 'skill: "paper-reader"' in content
    assert 'timestamp: "2026-04-07T12:00:00Z"' in content
    # Frontmatter should still be intact
    assert "title: Test Paper" in content
    assert "# Content here" in content


def test_stamp_idempotent(tmp_path: Path) -> None:
    """Stamping twice should update, not duplicate, the produced_by block."""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(
        "source:\n  name: test-paper\n  kind: paper\n",
        encoding="utf-8",
    )

    stamp_file(
        yaml_file,
        agent="claude-opus-4-6",
        skill="paper-reader",
        timestamp="2026-04-07T12:00:00Z",
    )

    # Stamp again with different timestamp
    changed = stamp_file(
        yaml_file,
        agent="claude-opus-4-6",
        skill="extract-claims",
        timestamp="2026-04-07T13:00:00Z",
    )

    content = yaml_file.read_text(encoding="utf-8")
    # Should only have ONE produced_by block
    assert content.count("produced_by:") == 1
    # Should have the UPDATED values
    assert 'skill: "extract-claims"' in content
    assert 'timestamp: "2026-04-07T13:00:00Z"' in content


def test_stamp_md_no_frontmatter(tmp_path: Path) -> None:
    """Stamping a .md file without frontmatter should create frontmatter."""
    md_file = tmp_path / "bare.md"
    md_file.write_text("# Just a heading\n\nSome content.\n", encoding="utf-8")

    changed = stamp_file(
        md_file,
        agent="claude-opus-4-6",
        skill="paper-reader",
        timestamp="2026-04-07T12:00:00Z",
    )

    assert changed is True
    content = md_file.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    assert "produced_by:" in content
    assert 'agent: "claude-opus-4-6"' in content
    # Original content should still be there
    assert "# Just a heading" in content
