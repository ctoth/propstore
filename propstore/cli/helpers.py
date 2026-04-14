"""Shared helpers for CLI subcommands."""
from __future__ import annotations

import logging
import os
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import click

from propstore.artifact_documents.concepts import ConceptIdScanDocument
from propstore.document_schema import decode_document_path


# ── File locking (cross-platform, stdlib only) ──────────────────────

def _lock_file(fd: int) -> None:
    """Acquire an exclusive lock on an open file descriptor."""
    if sys.platform == "win32":
        import msvcrt
        # msvcrt.locking with LK_NBLCK can fail transiently; retry briefly.
        for _ in range(50):
            try:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                time.sleep(0.05)
        # Final blocking attempt — LK_LOCK waits up to 10 s internally.
        msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
    else:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX)


def _unlock_file(fd: int) -> None:
    """Release an exclusive lock on an open file descriptor."""
    if sys.platform == "win32":
        import msvcrt
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass  # already unlocked or handle closing
    else:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_UN)


# ── Counter management ───────────────────────────────────────────────

def _scan_max_concept_id(cdir: Path) -> int:
    """Scan existing concepts to find the highest numeric ID in use."""
    if not cdir.exists():
        return 0
    max_id = 0
    for entry in cdir.iterdir():
        if entry.is_file() and entry.suffix == ".yaml":
            try:
                data = decode_document_path(entry, ConceptIdScanDocument)
            except ValueError:
                logging.warning("Failed to parse concept document in scan: %s", entry)
                continue
            for logical_id in data.logical_ids:
                if logical_id.namespace == "propstore":
                    match = re.match(r"^concept(\d+)$", logical_id.value)
                    if match:
                        max_id = max(max_id, int(match.group(1)))
            for candidate in (data.id, data.artifact_id):
                if not isinstance(candidate, str):
                    continue
                match = re.match(r"^concept(\d+)$", candidate)
                if match:
                    max_id = max(max_id, int(match.group(1)))
    return max_id


def read_counter(counters: Path) -> int:
    """Read the global concept counter from the given counters directory."""
    p = counters / "global.next"
    if p.exists():
        return int(p.read_text().strip())
    # Migrate: if no global counter, scan existing IDs for the true max
    return _scan_max_concept_id(counters.parent) + 1


def write_counter(counters: Path, value: int) -> None:
    """Write the global concept counter to the given counters directory."""
    counters.mkdir(parents=True, exist_ok=True)
    p = counters / "global.next"
    p.write_text(f"{value}\n")


class CounterLock:
    """Context manager that holds an exclusive lock on the concept counter.

    Usage::

        with CounterLock(counters_dir) as cl:
            value = cl.value          # current counter (not yet incremented)
            # ... do validation / work ...
            cl.commit()               # atomically write value+1 on success

    If ``commit()`` is never called (e.g. validation fails), the counter
    file is left unchanged and the lock is released.
    """

    def __init__(self, counters: Path) -> None:
        self._counters = counters
        self._fd: int | None = None
        self._committed = False
        self.value: int = 0

    def __enter__(self) -> "CounterLock":
        self._counters.mkdir(parents=True, exist_ok=True)
        lock_path = self._counters / "global.next.lock"
        lock_path.touch(exist_ok=True)
        self._fd = os.open(str(lock_path), os.O_RDWR)
        _lock_file(self._fd)
        self.value = read_counter(self._counters)
        return self

    def commit(self) -> None:
        """Write the incremented counter value while still holding the lock."""
        if not self._committed:
            write_counter(self._counters, self.value + 1)
            self._committed = True

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object) -> None:
        if self._fd is not None:
            _unlock_file(self._fd)
            os.close(self._fd)
            self._fd = None
        return None


def atomic_next_counter(counters: Path) -> int:
    """Atomically read and increment the global concept counter.

    Convenience wrapper around :class:`CounterLock` for callers that
    always want to increment unconditionally.
    """
    with CounterLock(counters) as cl:
        cl.commit()
        return cl.value


def next_id(counters: Path) -> tuple[str, int]:
    """Return (concept_id, next_counter) and increment the counter file.

    Uses file locking so concurrent processes never get the same ID.
    """
    n = atomic_next_counter(counters)
    cid = f"concept{n}"
    return cid, n


# ── WorldModel helpers ────────────────────────────────────────────────

@contextmanager
def open_world_model(repo):
    """Open WorldModel, exit with error if sidecar not found.

    Usage::

        with open_world_model(repo) as wm:
            ...  # wm is auto-closed on exit
    """
    from propstore.world import WorldModel

    try:
        wm = WorldModel(repo)
    except FileNotFoundError:
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)
    try:
        yield wm
    finally:
        wm.close()


# ── Key=value parsing ────────────────────────────────────────────────

def parse_kv_pairs(
    args: tuple[str, ...] | list[str],
    *,
    coerce: bool = False,
) -> tuple[dict[str, object], list[str]]:
    """Parse ``key=value`` arguments into a dict.

    Returns ``(parsed_dict, remaining)`` where *remaining* holds every
    element of *args* that did not contain ``=``.

    Parameters
    ----------
    coerce:
        When ``True``, apply basic scalar coercion (booleans, ints,
        floats) to values.  When ``False`` (the default), values stay
        as plain strings.
    """
    parsed: dict[str, object] = {}
    remaining: list[str] = []
    for arg in args:
        if "=" not in arg:
            remaining.append(arg)
            continue
        key, _, value = arg.partition("=")
        parsed[key] = _coerce_cli_scalar(value) if coerce else value
    return parsed, remaining


def _coerce_cli_scalar(value: str) -> object:
    """Coerce basic CLI scalars while leaving ordinary strings untouched."""
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    signless = value.lstrip("+-")
    if signless.isdigit():
        try:
            return int(value)
        except ValueError:
            pass

    try:
        if any(ch in value for ch in (".", "e", "E")):
            return float(value)
    except ValueError:
        pass

    return value


# ── Exit codes ───────────────────────────────────────────────────────

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_VALIDATION = 2
