"""Stamp extraction provenance onto pipeline artifacts.

Adds or updates a ``produced_by`` block recording which agent, skill, and
plugin version produced the file, plus a UTC timestamp.

Supports two file types:
  - .md  -- writes into YAML frontmatter (creates frontmatter if absent)
  - .yaml / .yml -- writes as a top-level block

Ported from research-papers-plugin stamp_provenance.py.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# YAML block builder
# ---------------------------------------------------------------------------

def _build_produced_by_yaml(
    agent: str,
    skill: str,
    plugin_version: str | None,
    timestamp: str,
) -> str:
    lines = [
        "produced_by:",
        f'  agent: "{agent}"',
        f'  skill: "{skill}"',
    ]
    if plugin_version is not None:
        lines.append(f'  plugin_version: "{plugin_version}"')
    lines.append(f'  timestamp: "{timestamp}"')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Markdown frontmatter
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

_PRODUCED_BY_BLOCK_RE = re.compile(
    r"^produced_by:\s*\n(?:[ \t]+\S[^\n]*\n?)*", re.MULTILINE
)


def _stamp_md(
    text: str,
    agent: str,
    skill: str,
    plugin_version: str | None,
    timestamp: str,
) -> tuple[str, bool]:
    """Add or update produced_by in markdown YAML frontmatter."""
    produced_by_block = _build_produced_by_yaml(agent, skill, plugin_version, timestamp)
    match = _FRONTMATTER_RE.match(text)

    if not match:
        # No frontmatter -- create it with just produced_by.
        result = f"---\n{produced_by_block}\n---\n{text}"
        return result, True

    frontmatter = match.group(1)
    body = text[match.end():]

    if _PRODUCED_BY_BLOCK_RE.search(frontmatter):
        new_frontmatter = _PRODUCED_BY_BLOCK_RE.sub(produced_by_block, frontmatter).rstrip()
    else:
        new_frontmatter = frontmatter.rstrip() + "\n" + produced_by_block

    result = f"---\n{new_frontmatter}\n---\n{body}"
    return result, result != text


# ---------------------------------------------------------------------------
# YAML files
# ---------------------------------------------------------------------------

_YAML_PRODUCED_BY_RE = re.compile(
    r"^produced_by:\s*\n(?:[ \t]+\S[^\n]*\n?)*", re.MULTILINE
)

_SOURCE_BLOCK_RE = re.compile(r"^source:\s*\n(?:[ \t]+\S[^\n]*\n)*", re.MULTILINE)


def _stamp_yaml(
    text: str,
    agent: str,
    skill: str,
    plugin_version: str | None,
    timestamp: str,
) -> tuple[str, bool]:
    """Add or update produced_by in a YAML file's top level."""
    produced_by_block = _build_produced_by_yaml(agent, skill, plugin_version, timestamp) + "\n"

    if _YAML_PRODUCED_BY_RE.search(text):
        result = _YAML_PRODUCED_BY_RE.sub(produced_by_block, text, count=1)
        return result, result != text

    # Insert after the source: block if present, otherwise prepend.
    source_match = _SOURCE_BLOCK_RE.search(text)
    if source_match:
        insert_pos = source_match.end()
        if not text[insert_pos - 1 : insert_pos] == "\n":
            produced_by_block = "\n" + produced_by_block
        result = text[:insert_pos] + produced_by_block + text[insert_pos:]
    else:
        result = produced_by_block + text

    return result, result != text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def stamp_file(
    path: Path,
    agent: str,
    skill: str,
    plugin_version: str | None = None,
    timestamp: str | None = None,
) -> bool:
    """Stamp provenance onto *path*. Returns True if the file was changed."""
    if timestamp is None:
        timestamp = _utc_timestamp()

    text = path.read_text(encoding="utf-8")

    if path.suffix == ".md":
        result, changed = _stamp_md(text, agent, skill, plugin_version, timestamp)
    elif path.suffix in (".yaml", ".yml"):
        result, changed = _stamp_yaml(text, agent, skill, plugin_version, timestamp)
    else:
        print(f"Unsupported file type: {path.suffix}", file=sys.stderr)
        return False

    if changed:
        path.write_text(result, encoding="utf-8")
    return changed
