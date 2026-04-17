"""Provenance records and extraction-provenance stamping.

The core provenance model follows the WS-A Phase 1 design:

* Buneman, Khanna, and Tan's why/where split is represented by a witness
  chain that keeps the justifying source artifact separate from the value
  being justified.
* Carroll et al.'s named graph discipline is represented by deterministic
  JSON-LD payloads stored as Git notes on ``refs/notes/provenance``.

The older ``stamp_file`` helper remains as the stated-method authoring branch:
it adds or updates a ``produced_by`` block recording which agent, skill, and
plugin version produced the file, plus a UTC timestamp.

Supports two file types:
  - .md  -- writes into YAML frontmatter (creates frontmatter if absent)
  - .yaml / .yml -- writes as a top-level block
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

import msgspec
from dulwich.notes import Notes
from dulwich.repo import BaseRepo

from propstore.artifacts.schema import DocumentStruct


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


PROVENANCE_NOTES_REF = b"refs/notes/provenance"

_CONTEXT = {
    "ps": "https://prop.store/ns#",
    "prov": "http://www.w3.org/ns/prov#",
    "swp": "http://www.w3.org/2004/03/trix/swp-2/",
}
_ANONYMOUS_GRAPH_NAME = "urn:propstore:provenance:anonymous"

_STATUS_RANK = {
    "vacuous": 0,
    "stated": 1,
    "measured": 2,
    "calibrated": 3,
    "defaulted": 4,
}


class ProvenanceStatus(StrEnum):
    """Status discriminator for probability-bearing values."""

    MEASURED = "measured"
    CALIBRATED = "calibrated"
    STATED = "stated"
    DEFAULTED = "defaulted"
    VACUOUS = "vacuous"


class ProvenanceWitness(DocumentStruct):
    """One witness in a provenance chain.

    ``source_artifact_code`` is the Buneman-style where pointer; ``method`` and
    ``asserter`` are the Carroll/SWP-style warrant metadata.
    """

    asserter: str
    timestamp: str
    source_artifact_code: str
    method: str

    def to_payload(self) -> dict[str, str]:
        return {
            "asserter": self.asserter,
            "timestamp": self.timestamp,
            "source_artifact_code": self.source_artifact_code,
            "method": self.method,
        }


class Provenance(DocumentStruct):
    """A named-graph provenance record."""

    status: ProvenanceStatus
    witnesses: tuple[ProvenanceWitness, ...]
    graph_name: str | None = None
    derived_from: tuple[str, ...] = ()
    operations: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status.value,
            "witnesses": [witness.to_payload() for witness in self.witnesses],
        }
        if self.graph_name is not None:
            payload["graph_name"] = self.graph_name
        if self.derived_from:
            payload["derived_from"] = list(self.derived_from)
        if self.operations:
            payload["operations"] = list(self.operations)
        return payload


class _NamedGraphDocument(DocumentStruct):
    context: dict[str, str] = msgspec.field(name="@context")
    id: str = msgspec.field(name="@id")
    type: str = msgspec.field(name="@type")
    provenance: Provenance


def _sha_text(value: str) -> str:
    return value if value.startswith("ni:///sha-1;") else f"ni:///sha-1;{value}"


def _object_sha_bytes(object_sha: bytes | str) -> bytes:
    if isinstance(object_sha, bytes):
        return object_sha
    return object_sha.encode("ascii")


def _dedupe_preserve_order(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return tuple(result)


def compose_provenance(*records: Provenance, operation: str) -> Provenance:
    """Compose provenance for a derived value.

    Buneman-style witness composition is set union with deterministic ordering.
    The resulting status is the highest-ranked status present in the input
    chain, making defaulted inputs visible after fusion instead of silently
    laundering them into a measured/calibrated result.
    """

    if not records:
        raise ValueError("compose_provenance requires at least one record")

    status = max(records, key=lambda item: _STATUS_RANK[item.status.value]).status
    witnesses: list[ProvenanceWitness] = []
    witness_keys: set[tuple[str, str, str, str]] = set()
    derived_from: list[str] = []
    operations: list[str] = []

    for record in records:
        if record.graph_name is not None:
            derived_from.append(record.graph_name)
        derived_from.extend(record.derived_from)
        operations.extend(record.operations)
        for witness in record.witnesses:
            key = (
                witness.asserter,
                witness.timestamp,
                witness.source_artifact_code,
                witness.method,
            )
            if key in witness_keys:
                continue
            witness_keys.add(key)
            witnesses.append(witness)

    operations.append(operation)
    return Provenance(
        status=status,
        witnesses=tuple(witnesses),
        derived_from=_dedupe_preserve_order(derived_from),
        operations=_dedupe_preserve_order(operations),
    )


def encode_named_graph(provenance: Provenance) -> bytes:
    """Serialize provenance as a deterministic JSON-LD named graph."""

    graph_id = provenance.graph_name or _ANONYMOUS_GRAPH_NAME
    document = _NamedGraphDocument(
        context=_CONTEXT,
        id=graph_id,
        type="NamedGraph",
        provenance=provenance,
    )
    return msgspec.json.encode(document)


def decode_named_graph(payload: bytes) -> Provenance:
    """Decode a JSON-LD named graph payload into a provenance record."""

    document = msgspec.json.decode(payload, type=_NamedGraphDocument, strict=True)
    if document.type != "NamedGraph":
        raise ValueError(f"Unsupported provenance graph type: {document.type!r}")
    provenance = document.provenance
    if provenance.graph_name is None and document.id != _ANONYMOUS_GRAPH_NAME:
        return Provenance(
            status=provenance.status,
            witnesses=provenance.witnesses,
            graph_name=document.id,
            derived_from=provenance.derived_from,
            operations=provenance.operations,
        )
    return provenance


def write_provenance_note(
    repo: BaseRepo,
    object_sha: bytes | str,
    provenance: Provenance,
) -> bytes:
    """Attach a provenance named graph to a git object using git notes."""

    notes = Notes(repo.object_store, repo.refs)
    return notes.set_note(
        _object_sha_bytes(object_sha),
        encode_named_graph(provenance),
        notes_ref=PROVENANCE_NOTES_REF,
        message=b"Record provenance named graph",
    )


def read_provenance_note(
    repo: BaseRepo,
    object_sha: bytes | str,
) -> Provenance | None:
    """Read a provenance named graph from the provenance notes ref."""

    notes = Notes(repo.object_store, repo.refs)
    payload = notes.get_note(
        _object_sha_bytes(object_sha),
        notes_ref=PROVENANCE_NOTES_REF,
    )
    if payload is None:
        return None
    return decode_named_graph(payload)


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


from propstore.provenance.derivative import partial_derivative
from propstore.provenance.homomorphism import Homomorphism, evaluate
from propstore.provenance.nogoods import NogoodWitness, ProvenanceNogood, live
from propstore.provenance.polynomial import (
    PolynomialTerm,
    ProvenancePolynomial,
    VariablePower,
)
from propstore.provenance.projections import (
    WhySupport,
    boolean_presence,
    derivation_count,
    tropical_cost,
    why_provenance,
)
from propstore.provenance.support import SupportEvidence, SupportQuality
from propstore.provenance.variables import (
    SourceRole,
    SourceVariable,
    SourceVariableId,
    derive_source_variable_id,
)


__all__ = [
    "Homomorphism",
    "NogoodWitness",
    "PolynomialTerm",
    "PROVENANCE_NOTES_REF",
    "Provenance",
    "ProvenanceNogood",
    "ProvenancePolynomial",
    "ProvenanceStatus",
    "ProvenanceWitness",
    "SourceRole",
    "SourceVariable",
    "SourceVariableId",
    "SupportEvidence",
    "SupportQuality",
    "VariablePower",
    "WhySupport",
    "boolean_presence",
    "compose_provenance",
    "decode_named_graph",
    "derive_source_variable_id",
    "derivation_count",
    "encode_named_graph",
    "evaluate",
    "live",
    "partial_derivative",
    "read_provenance_note",
    "stamp_file",
    "tropical_cost",
    "why_provenance",
    "write_provenance_note",
]
