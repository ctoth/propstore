"""Extract Codex user requests for a repo/date range from local session JSONL.

This is an audit helper, not a code-refactor tool. It reads Codex session logs,
keeps sessions whose cwd/workspace root is inside the target repo, and writes a
Markdown evidence file containing the user turns grouped by day.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


@dataclass
class UserTurn:
    timestamp: datetime | None
    text: str


@dataclass
class Session:
    path: Path
    session_id: str | None = None
    started_at: datetime | None = None
    cwd: Path | None = None
    workspace_roots: list[Path] = field(default_factory=list)
    user_turns: list[UserTurn] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--sessions-root", required=True, type=Path)
    parser.add_argument("--from-date", required=True)
    parser.add_argument("--through-date", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--compact-out", type=Path)
    parser.add_argument("--ledger-out", type=Path)
    return parser.parse_args()


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def local_day(timestamp: datetime | None) -> date | None:
    if timestamp is None:
        return None
    if timestamp.tzinfo is None:
        return timestamp.date()
    mountain = timezone(timedelta(hours=-6))
    return timestamp.astimezone(mountain).date()


def normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def path_inside(candidate: Path | None, root: Path) -> bool:
    if candidate is None:
        return False
    try:
        candidate.resolve().relative_to(root)
    except ValueError:
        return False
    return True


def collect_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if isinstance(text, str):
            parts.append(text)
    return "\n\n".join(part.strip() for part in parts if part.strip()).strip()


def normalized_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines()).strip()


def is_context_only_message(text: str) -> bool:
    stripped = text.strip()
    if stripped.startswith("# AGENTS.md instructions for "):
        return True
    if stripped.startswith("<environment_context>"):
        return True
    if stripped.startswith("<turn_aborted>"):
        return True
    if stripped.startswith("<subagent_notification>"):
        return True
    return False


def turn_key(turn: UserTurn) -> tuple[str, str]:
    timestamp = turn.timestamp.isoformat() if turn.timestamp else "unknown"
    digest = hashlib.sha256(normalized_text(turn.text).encode("utf-8")).hexdigest()
    return timestamp, digest


def session_files(root: Path, start: date, end: date) -> list[Path]:
    files: list[Path] = []
    for year_dir in root.iterdir():
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir() or not month_dir.name.isdigit():
                continue
            for day_dir in month_dir.iterdir():
                if not day_dir.is_dir() or not day_dir.name.isdigit():
                    continue
                try:
                    day = date(
                        int(year_dir.name), int(month_dir.name), int(day_dir.name)
                    )
                except ValueError:
                    continue
                if start <= day <= end:
                    files.extend(sorted(day_dir.glob("*.jsonl")))
    return sorted(files)


def read_session(path: Path) -> Session:
    session = Session(path=path)
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_time = parse_timestamp(event.get("timestamp"))
            event_type = event.get("type")
            payload = event.get("payload")
            if event_type == "session_meta" and isinstance(payload, dict):
                session.session_id = payload.get("id")
                session.started_at = (
                    parse_timestamp(payload.get("timestamp")) or event_time
                )
                cwd = payload.get("cwd")
                if isinstance(cwd, str):
                    session.cwd = normalize_path(cwd)
                continue
            if event_type == "turn_context" and isinstance(payload, dict):
                cwd = payload.get("cwd")
                if isinstance(cwd, str):
                    session.cwd = normalize_path(cwd)
                roots = payload.get("workspace_roots")
                if isinstance(roots, list):
                    session.workspace_roots = [
                        normalize_path(root) for root in roots if isinstance(root, str)
                    ]
                continue
            if event_type != "response_item" or not isinstance(payload, dict):
                continue
            if payload.get("type") != "message" or payload.get("role") != "user":
                continue
            text = collect_text(payload.get("content"))
            if text and not is_context_only_message(text):
                session.user_turns.append(UserTurn(timestamp=event_time, text=text))
    return session


def session_matches_repo(session: Session, repo: Path) -> bool:
    if path_inside(session.cwd, repo):
        return True
    return any(path_inside(root, repo) for root in session.workspace_roots)


def markdown_escape_block(text: str) -> str:
    return text.replace("```", "'''")


def compact_text(text: str, *, limit: int = 220) -> str:
    stripped = normalized_text(text)
    if stripped.startswith("<user_shell_command>"):
        command = ""
        for line in stripped.splitlines():
            if line and not line.startswith("<") and not line.startswith("Exit code:"):
                command = line
                break
        stripped = f"user shell command: {command or 'unknown command'}"
    stripped = " ".join(stripped.split())
    if len(stripped) <= limit:
        return stripped
    return f"{stripped[: limit - 3]}..."


def grouped_turns(
    sessions: list[Session],
    start: date,
    end: date,
) -> dict[date, list[tuple[Session, UserTurn]]]:
    by_day: dict[date, list[tuple[Session, UserTurn]]] = {}
    seen: set[tuple[str, str]] = set()
    for session in sessions:
        for turn in session.user_turns:
            key = turn_key(turn)
            if key in seen:
                continue
            seen.add(key)
            day = local_day(turn.timestamp) or local_day(session.started_at)
            if day is not None and start <= day <= end:
                by_day.setdefault(day, []).append((session, turn))
    return by_day


def write_markdown(sessions: list[Session], start: date, end: date, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    by_day = grouped_turns(sessions, start, end)

    lines: list[str] = [
        "# Codex User Request Evidence: Propstore, May 1-June 3 2026",
        "",
        "This file is generated by `scripts/extract_codex_requests.py` from local Codex JSONL session logs.",
        "It is evidence for the audit file, not the audit verdict itself.",
        "",
        f"- Sessions with Propstore cwd/workspace root: {len(sessions)}",
        f"- User turns in date range: {sum(len(items) for items in by_day.values())}",
        "",
    ]
    day = start
    while day <= end:
        items = sorted(
            by_day.get(day, []), key=lambda item: item[1].timestamp or datetime.min
        )
        lines.append(f"## {day.isoformat()}")
        lines.append("")
        if not items:
            lines.append(
                "- No Propstore-scoped user turns found in local Codex session logs."
            )
            lines.append("")
            day += timedelta(days=1)
            continue
        for index, (session, turn) in enumerate(items, start=1):
            when = turn.timestamp.isoformat() if turn.timestamp else "unknown-time"
            session_id = session.session_id or session.path.stem
            lines.append(f"### Request {index}: {when}")
            lines.append("")
            lines.append(f"- session: `{session_id}`")
            lines.append(f"- file: `{session.path}`")
            lines.append("")
            lines.append("```text")
            lines.append(markdown_escape_block(turn.text))
            lines.append("```")
            lines.append("")
        day += timedelta(days=1)
    out.write_text("\n".join(lines), encoding="utf-8")


def write_compact(sessions: list[Session], start: date, end: date, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    by_day = grouped_turns(sessions, start, end)
    lines: list[str] = []
    day = start
    while day <= end:
        lines.append(f"## {day.isoformat()}")
        items = sorted(
            by_day.get(day, []), key=lambda item: item[1].timestamp or datetime.min
        )
        if not items:
            lines.append("- no requests")
        for index, (session, turn) in enumerate(items, start=1):
            when = turn.timestamp.isoformat() if turn.timestamp else "unknown-time"
            session_id = session.session_id or session.path.stem
            lines.append(
                f"- request {index}: {when} [{session_id}] {compact_text(turn.text)}"
            )
        lines.append("")
        day += timedelta(days=1)
    out.write_text("\n".join(lines), encoding="utf-8")


def write_ledger(sessions: list[Session], start: date, end: date, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    by_day = grouped_turns(sessions, start, end)
    lines: list[str] = [
        "# Codex User Request Ledger: Propstore, May 1-June 3 2026",
        "",
        "This file is generated by `scripts/extract_codex_requests.py`.",
        "It is a literal request inventory for expanding the audit verdict file.",
        "",
        "| day | request | timestamp | session | request text |",
        "| --- | ---: | --- | --- | --- |",
    ]
    day = start
    while day <= end:
        items = sorted(
            by_day.get(day, []), key=lambda item: item[1].timestamp or datetime.min
        )
        if not items:
            lines.append(
                f"| {day.isoformat()} | 0 | | | no Propstore-scoped user turns found |"
            )
            day += timedelta(days=1)
            continue
        for index, (session, turn) in enumerate(items, start=1):
            when = turn.timestamp.isoformat() if turn.timestamp else "unknown-time"
            session_id = session.session_id or session.path.stem
            text = compact_text(turn.text, limit=500).replace("|", "\\|")
            lines.append(
                f"| {day.isoformat()} | {index} | {when} | `{session_id}` | {text} |"
            )
        day += timedelta(days=1)
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    repo = normalize_path(args.repo)
    start = parse_date(args.from_date)
    end = parse_date(args.through_date)
    sessions = [
        session
        for session in (
            read_session(path) for path in session_files(args.sessions_root, start, end)
        )
        if session_matches_repo(session, repo) and session.user_turns
    ]
    write_markdown(sessions, start, end, args.out)
    if args.compact_out is not None:
        write_compact(sessions, start, end, args.compact_out)
    if args.ledger_out is not None:
        write_ledger(sessions, start, end, args.ledger_out)
    print(f"wrote {args.out} from {len(sessions)} sessions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
