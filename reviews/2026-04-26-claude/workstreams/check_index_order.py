from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


INDEX_PATH = Path(__file__).with_name("INDEX.md")


@dataclass(frozen=True)
class WorkstreamRow:
    row_number: int
    workstream_id: str
    title: str
    status: str
    deps: tuple[str, ...]
    blocks: tuple[str, ...]


def _strip_markup(value: str) -> str:
    value = value.strip()
    value = value.replace("**", "")
    value = value.replace("~~", "")
    value = value.replace("`", "")
    return value.strip()


def _normalise_id(value: str) -> str:
    token = _strip_markup(value)
    token = re.sub(r"\s+", " ", token)
    token = token.strip()
    if not token:
        return token
    if token.startswith("WS-"):
        return token
    return f"WS-{token}"


def _parse_deps(value: str) -> tuple[str, ...]:
    value = _strip_markup(value)
    if not value or value == "-":
        return ()
    if value in {"—", "n/a", "none"}:
        return ()
    deps: list[str] = []
    for raw_part in value.split(","):
        part = _strip_markup(raw_part)
        part = part.strip()
        if not part or part == "—":
            continue
        if " " in part:
            raise ValueError(f"dependency token contains whitespace: {part!r}")
        deps.append(_normalise_id(part))
    return tuple(deps)


def _parse_rows(index_text: str) -> list[WorkstreamRow]:
    rows: list[WorkstreamRow] = []
    for line_number, line in enumerate(index_text.splitlines(), start=1):
        if not line.startswith("|"):
            continue
        if line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        if cells[0] == "ID":
            continue
        rows.append(
            WorkstreamRow(
                row_number=line_number,
                workstream_id=_normalise_id(cells[0]),
                title=_strip_markup(cells[1]),
                status=_strip_markup(cells[2]),
                deps=_parse_deps(cells[3]),
                blocks=_parse_deps(cells[4]),
            )
        )
    return rows


def main() -> int:
    rows = _parse_rows(INDEX_PATH.read_text(encoding="utf-8"))
    positions = {row.workstream_id: index for index, row in enumerate(rows)}
    errors: list[str] = []

    for row in rows:
        if row.status.startswith("SUPERSEDED"):
            continue
        for dep in row.deps:
            if dep not in positions:
                errors.append(
                    f"{row.workstream_id} line {row.row_number}: unknown dependency {dep}"
                )
                continue
            if positions[dep] > positions[row.workstream_id]:
                dep_row = rows[positions[dep]]
                errors.append(
                    f"{row.workstream_id} line {row.row_number}: dependency {dep} "
                    f"appears later on line {dep_row.row_number}"
                )
        for blocked in row.blocks:
            if blocked not in positions:
                continue
            blocked_row = rows[positions[blocked]]
            if positions[blocked] < positions[row.workstream_id]:
                errors.append(
                    f"{row.workstream_id} line {row.row_number}: blocks {blocked}, "
                    f"but {blocked} appears earlier on line {blocked_row.row_number}"
                )

    if errors:
        print("INDEX.md is not in dependency order:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"INDEX.md dependency order OK ({len(rows)} rows checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
