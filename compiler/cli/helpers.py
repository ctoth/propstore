"""Shared helpers for CLI subcommands."""
from __future__ import annotations

import re
from pathlib import Path

import yaml


# ── Paths ────────────────────────────────────────────────────────────

def concepts_dir() -> Path:
    return Path("concepts")


def counters_dir() -> Path:
    d = concepts_dir() / ".counters"
    d.mkdir(parents=True, exist_ok=True)
    return d


def claims_dir() -> Path:
    return Path("claims")



# ── Counter management ───────────────────────────────────────────────

def _scan_max_concept_id() -> int:
    """Scan existing concepts to find the highest numeric ID in use."""
    cdir = concepts_dir()
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


def read_counter(domain: str) -> int:
    # Global counter — domain parameter kept for backward compatibility
    p = counters_dir() / "global.next"
    if p.exists():
        return int(p.read_text().strip())
    # Migrate: if no global counter, scan existing IDs for the true max
    return _scan_max_concept_id() + 1


def write_counter(domain: str, value: int) -> None:
    # Global counter — domain parameter kept for backward compatibility
    p = counters_dir() / "global.next"
    p.write_text(f"{value}\n")


def next_id(domain: str) -> tuple[str, int]:
    """Return (concept_id, next_counter) and increment the counter file."""
    n = read_counter(domain)
    cid = f"concept{n}"
    write_counter(domain, n + 1)
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


def find_concept(id_or_name: str) -> Path | None:
    """Find a concept file by ID or canonical_name. Returns filepath or None."""
    cdir = concepts_dir()
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


def load_all_concepts_by_id() -> dict[str, dict]:
    """Load all concepts keyed by ID."""
    cdir = concepts_dir()
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
