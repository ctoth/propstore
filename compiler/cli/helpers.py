"""Shared helpers for CLI subcommands."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import jsonschema
import yaml

from compiler.validate import LoadedConcept, ValidationResult, load_concepts, validate_concepts


# ── Paths ────────────────────────────────────────────────────────────

def concepts_dir() -> Path:
    return Path("concepts")


def counters_dir() -> Path:
    d = concepts_dir() / ".counters"
    d.mkdir(parents=True, exist_ok=True)
    return d


def claims_dir() -> Path:
    return Path("claims")


def schema_path() -> Path:
    return Path("schema") / "generated" / "concept_registry.schema.json"


# ── Counter management ───────────────────────────────────────────────

def read_counter(domain: str) -> int:
    p = counters_dir() / f"{domain}.next"
    if p.exists():
        return int(p.read_text().strip())
    return 1


def write_counter(domain: str, value: int) -> None:
    p = counters_dir() / f"{domain}.next"
    p.write_text(f"{value}\n")


def next_id(domain: str) -> tuple[str, int]:
    """Return (concept_id, next_counter) and increment the counter file."""
    n = read_counter(domain)
    cid = f"concept{n}"
    write_counter(domain, n + 1)
    return cid, n


# ── YAML I/O ─────────────────────────────────────────────────────────

def _json_safe(obj: object) -> object:
    """Convert date objects for JSON Schema validation."""
    import datetime
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return obj


def load_concept_file(path: Path) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)
    return data if data else {}


def write_concept_file(path: Path, data: dict) -> None:
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def validate_concept_data(data: dict, filename: str) -> ValidationResult:
    """Validate a single concept dict using both JSON Schema and compiler checks."""
    result = ValidationResult()

    # JSON Schema
    sp = schema_path()
    if sp.exists():
        with open(sp) as f:
            json_schema = json.load(f)
        try:
            jsonschema.validate(_json_safe(data), json_schema)
        except jsonschema.ValidationError as e:
            result.errors.append(f"{filename}: JSON Schema: {e.message}")

    # Compiler contract checks need all concepts loaded
    concepts = load_concepts(concepts_dir())
    full_result = validate_concepts(concepts)
    return full_result


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
