from __future__ import annotations

from pathlib import Path

from scripts.check_workstream_order import check_split_workstream


def test_split_workstream_checker_resolves_prose_prerequisite_aliases(tmp_path, capsys) -> None:
    index = tmp_path / "00-index.md"
    index.write_text(
        """# Index

## Phase Order

| Phase | Child workstream file | Gate to proceed |
| --- | --- | --- |
| 0 | `00-index.md` | Start |
| 1 | `01-quire-capability-and-charter.md` | Capability |
| 2 | `02-quire-sqlalchemy-engine.md` | Engine |
""",
        encoding="utf-8",
    )
    (tmp_path / "01-quire-capability-and-charter.md").write_text(
        """# Capability

## Prerequisites

- Quire SQLAlchemy table/mapping/session/catalog engine.
""",
        encoding="utf-8",
    )
    (tmp_path / "02-quire-sqlalchemy-engine.md").write_text(
        """# Engine

## Prerequisites

- Quire SQLAlchemy dependency and capability proof.
""",
        encoding="utf-8",
    )

    assert check_split_workstream(index, index.read_text(encoding="utf-8")) == 1
    assert "01-quire-capability-and-charter.md depends on later phase 02-quire-sqlalchemy-engine.md" in capsys.readouterr().err


def test_split_workstream_checker_reads_prerequisite_gate_dependencies(tmp_path, capsys) -> None:
    index = tmp_path / "00-index.md"
    index.write_text(
        """# Index

## Phase Order

| Phase | Child workstream file | Gate to proceed |
| --- | --- | --- |
| 0 | `00-index.md` | Start |
| 1 | `01-quire-capability-and-charter.md` | Capability |
| 2 | `13-final-deletion-gates.md` | Final |
""",
        encoding="utf-8",
    )
    (tmp_path / "01-quire-capability-and-charter.md").write_text(
        """# Capability

## Prerequisites
""",
        encoding="utf-8",
    )
    (tmp_path / "13-final-deletion-gates.md").write_text(
        """# Final

## Prerequisite Gate Dependencies

| Dependency | Required evidence |
| --- | --- |
| `99-missing.md` | Not in phase order. |
""",
        encoding="utf-8",
    )

    assert check_split_workstream(index, index.read_text(encoding="utf-8")) == 1
    assert "13-final-deletion-gates.md references prerequisite outside phase order: 99-missing.md" in capsys.readouterr().err


def test_split_workstream_checker_requires_all_earlier_phase_prerequisites(tmp_path, capsys) -> None:
    index = tmp_path / "00-index.md"
    index.write_text(
        """# Index

## Phase Order

| Phase | Child workstream file | Gate to proceed |
| --- | --- | --- |
| 0 | `00-index.md` | Start |
| 1 | `01-quire-capability-and-charter.md` | Capability |
| 2 | `02-quire-sqlalchemy-engine.md` | Engine |
| 3 | `03-quire-fts-vector.md` | FTS |
""",
        encoding="utf-8",
    )
    (tmp_path / "01-quire-capability-and-charter.md").write_text(
        """# Capability

## Prerequisites
""",
        encoding="utf-8",
    )
    (tmp_path / "02-quire-sqlalchemy-engine.md").write_text(
        """# Engine

## Prerequisites

- `01-quire-capability-and-charter.md`.
""",
        encoding="utf-8",
    )
    (tmp_path / "03-quire-fts-vector.md").write_text(
        """# FTS

## Prerequisites

- `02-quire-sqlalchemy-engine.md`.
""",
        encoding="utf-8",
    )

    assert check_split_workstream(index, index.read_text(encoding="utf-8")) == 1
    assert "03-quire-fts-vector.md omits required earlier phase prerequisite: 01-quire-capability-and-charter.md" in capsys.readouterr().err
