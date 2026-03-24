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
import yaml


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
                data = yaml.safe_load(entry.read_text())
            except yaml.YAMLError:
                logging.warning("Failed to parse YAML in concept scan: %s", entry)
                continue
            cid = (data or {}).get("id", "")
            if isinstance(cid, str) and cid.startswith("concept"):
                try:
                    max_id = max(max_id, int(cid[len("concept"):]))
                except ValueError:
                    pass
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


# ── YAML I/O ─────────────────────────────────────────────────────────

def load_concept_file(path: Path) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)
    return data if data else {}


def write_yaml_file(path: Path, data: dict) -> None:
    """Write a dict to a YAML file with consistent formatting.

    Uses block style, preserves key order, and writes unicode directly.
    """
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def write_concept_file(path: Path, data: dict) -> None:
    write_yaml_file(path, data)


# ── Lookup helpers ───────────────────────────────────────────────────

_ID_RE = re.compile(r'^concept\d+$')


def find_concept(id_or_name: str, cdir: Path) -> Path | None:
    """Find a concept file by ID or canonical_name. Returns filepath or None."""
    if not cdir.exists():
        return None

    # Try as canonical_name (direct file lookup)
    direct = cdir / f"{id_or_name}.yaml"
    if direct.exists():
        return direct

    # Try as ID — scan files
    if _ID_RE.match(id_or_name):
        for entry in sorted(cdir.iterdir()):
            if entry.is_file() and entry.suffix == ".yaml":
                data = load_concept_file(entry)
                if data.get("id") == id_or_name:
                    return entry
    return None


def load_all_concepts_by_id(cdir: Path) -> dict[str, dict]:
    """Load all concepts keyed by ID."""
    if not cdir.exists():
        return {}
    result: dict[str, dict] = {}
    for entry in sorted(cdir.iterdir()):
        if entry.is_file() and entry.suffix == ".yaml":
            data = load_concept_file(entry)
            cid = data.get("id")
            if cid:
                result[cid] = data
    return result


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


# ── Exit codes ───────────────────────────────────────────────────────

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_VALIDATION = 2
