"""Shared helpers for CLI subcommands."""
from __future__ import annotations

import re
from pathlib import Path

import yaml


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
            except Exception:
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


def next_id(counters: Path) -> tuple[str, int]:
    """Return (concept_id, next_counter) and increment the counter file."""
    n = read_counter(counters)
    cid = f"concept{n}"
    write_counter(counters, n + 1)
    return cid, n


# ── YAML I/O ─────────────────────────────────────────────────────────

def load_concept_file(path: Path) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)
    return data if data else {}


def write_concept_file(path: Path, data: dict) -> None:
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


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


# ── Exit codes ───────────────────────────────────────────────────────

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_VALIDATION = 2
