"""Typed provenance value objects and the named-graph carrier.

A :class:`Provenance` records *how* a probability-bearing or asserted value came
to be — its typed :class:`ProvenanceStatus` (``measured`` / ``calibrated`` /
``stated`` / ``defaulted`` / ``vacuous``), the witnesses that asserted it, the
optional named graph it is published as, the graphs it was derived from, and the
chain of operations that transformed it. The reference grounding is CLAUDE.md's
"honest ignorance over fabricated confidence": every value entering the
argumentation layer must say *where it came from* rather than fabricate a number.

This module has two layers that share one canonical ``Provenance`` spelling:

* The **value object** — a frozen ``msgspec.Struct`` that nests directly inside
  the charter document tree (and therefore the sidecar JSON projection). It is
  the in-band carrier the lemon value objects require.
* The **named-graph carrier** (Carroll, Bizer, Hayes & Stickler 2005) — a
  deterministic JSON-LD ``NamedGraph`` serialization plus the *physical* carrier,
  a git note on ``refs/notes/provenance``. Provenance rides there, beside the
  annotated git object, so it never contaminates claim/concept identity: identity
  is computed by functions that exclude provenance (see
  :func:`propstore.core.lemon.lexical_entry_identity_key`), and the note targets
  an object's sha without touching the object itself.

The semiring provenance algebra (``ProvenancePolynomial`` / ``why_provenance`` /
nogoods) lives in the ``provenance_semiring`` package and is consumed from there
directly — there is no propstore mirror of it (CLAUDE.md substrate boundary).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path

import msgspec
from dulwich.repo import BaseRepo
from quire.notes import NotesRef, read_git_note, write_git_note

from propstore.provenance._jsonld import JSONLD_CONTEXT as _CONTEXT
from propstore.provenance._jsonld import URI_SCHEME_PREFIXES as _GRAPH_NAME_PREFIXES
from propstore.provenance.records import ProjectionFrameProvenanceRecord


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


PROVENANCE_NOTES_REF = b"refs/notes/provenance"
PROVENANCE_NOTES = NotesRef("refs/notes/provenance")

# Composition keeps the *weakest* honest status visible after fusion: a derived
# value is no more trustworthy than its least-grounded input. Higher rank = less
# grounded, so ``max`` surfaces a ``defaulted`` input rather than laundering it
# into a ``measured``/``calibrated`` result — and a ``vacuous`` input (total
# ignorance, the least-grounded input possible) survives composition with
# anything (CLAUDE.md honest ignorance; Jøsang 2001 on vacuous opinions).
_STATUS_RANK = {
    "stated": 1,
    "measured": 2,
    "calibrated": 3,
    "defaulted": 4,
    "vacuous": 5,
}


class ProvenanceStatus(StrEnum):
    """The typed origin of a value (CLAUDE.md honest-ignorance discipline).

    ``VACUOUS`` represents total ignorance honestly (Jøsang 2001); it is never a
    made-up scalar. ``CALIBRATED`` bridges raw model outputs to the opinion
    algebra (Guo et al. 2017). ``MEASURED`` / ``STATED`` / ``DEFAULTED`` cover
    observed, asserted, and fallback origins respectively.
    """

    MEASURED = "measured"
    CALIBRATED = "calibrated"
    STATED = "stated"
    DEFAULTED = "defaulted"
    VACUOUS = "vacuous"


class ProvenanceWitness(
    msgspec.Struct,
    frozen=True,
    forbid_unknown_fields=True,
    omit_defaults=True,
):
    """One witness in a provenance chain.

    ``source_artifact_code`` is the Buneman-style where pointer; ``method`` and
    ``asserter`` are the Carroll/SWP-style warrant metadata.
    ``source_version_id`` and ``source_content_hash`` pin *which* version of that
    source was witnessed: the where pointer names the source, the hash names its
    bytes. Both are optional because a witness may honestly not know them — an
    absent hash is ``None``, never a fabricated digest.

    ``omit_defaults`` keeps an unknown pin *absent* from the named graph rather
    than serializing it as an explicit ``null``: a witness that never knew the
    source version says nothing about it, and notes written before the pins
    existed stay byte-identical.
    """

    asserter: str
    timestamp: str
    source_artifact_code: str
    method: str
    source_version_id: str | None = None
    source_content_hash: str | None = None


class Provenance(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """Typed provenance: a status, its witnesses, lineage, and operation chain.

    ``graph_name`` is the named graph this provenance is published as (Carroll
    2005); ``derived_from`` accumulates the graph names this value was fused from;
    ``operations`` accumulates the deterministic transformations applied (e.g.
    ``qualia_coercion:telic``) so a coerced view can be traced back to its source
    assertion. Provenance never enters identity (see module docstring).
    """

    status: ProvenanceStatus
    witnesses: tuple[ProvenanceWitness, ...] = ()
    graph_name: str | None = None
    derived_from: tuple[str, ...] = ()
    operations: tuple[str, ...] = ()


class _NamedGraphDocument(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    context: dict[str, str] = msgspec.field(name="@context")
    id: str = msgspec.field(name="@id")
    type: str = msgspec.field(name="@type")
    provenance: Provenance


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


def _dedupe_sorted(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


def _witness_key(witness: ProvenanceWitness) -> tuple[str, str, str, str, str, str]:
    # Two witnesses that name the same source at different versions are distinct
    # witnesses, so the pinning fields are part of the dedupe key.
    return (
        witness.asserter,
        witness.method,
        witness.source_artifact_code,
        witness.timestamp,
        witness.source_version_id or "",
        witness.source_content_hash or "",
    )


def _canonical_witnesses(
    witnesses: tuple[ProvenanceWitness, ...],
) -> tuple[ProvenanceWitness, ...]:
    by_key = {_witness_key(witness): witness for witness in witnesses}
    return tuple(by_key[key] for key in sorted(by_key))


def _require_graph_name(value: str | None) -> str:
    graph_name = "" if value is None else value.strip()
    if graph_name == "":
        raise ValueError("provenance graph_name must be explicit")
    if not graph_name.startswith(_GRAPH_NAME_PREFIXES):
        raise ValueError("provenance graph_name must be a URI")
    return graph_name


def _canonical_provenance(
    provenance: Provenance,
    *,
    require_graph_name: bool,
) -> Provenance:
    graph_name = (
        _require_graph_name(provenance.graph_name)
        if require_graph_name
        else provenance.graph_name
    )
    return Provenance(
        status=provenance.status,
        witnesses=_canonical_witnesses(provenance.witnesses),
        graph_name=graph_name,
        # Derived source pointers are a set; causal operation chains are not.
        derived_from=_dedupe_sorted(provenance.derived_from),
        operations=_dedupe_preserve_order(list(provenance.operations)),
    )


def compose_provenance(*records: Provenance, operation: str) -> Provenance:
    """Compose provenance for a derived value.

    Buneman-style witness composition is set union with deterministic ordering.
    The resulting status is the highest-ranked (weakest) status present in the
    input chain, making defaulted inputs visible after fusion instead of silently
    laundering them into a measured/calibrated result (CLAUDE.md honest
    ignorance). Operations preserve their first-observed causal order across the
    input chains, then record ``operation`` last.
    """

    if not records:
        raise ValueError("compose_provenance requires at least one record")

    status = max(records, key=lambda item: _STATUS_RANK[item.status.value]).status
    witnesses: list[ProvenanceWitness] = []
    witness_keys: set[tuple[str, str, str, str, str, str]] = set()
    derived_from: list[str] = []
    operations: list[str] = []

    for record in records:
        if record.graph_name is not None:
            derived_from.append(record.graph_name)
        derived_from.extend(record.derived_from)
        operations.extend(record.operations)
        for witness in record.witnesses:
            key = _witness_key(witness)
            if key in witness_keys:
                continue
            witness_keys.add(key)
            witnesses.append(witness)

    operations.append(operation)
    return _canonical_provenance(
        Provenance(
            status=status,
            witnesses=tuple(witnesses),
            derived_from=_dedupe_preserve_order(derived_from),
            operations=_dedupe_preserve_order(operations),
        ),
        require_graph_name=False,
    )


def encode_named_graph(provenance: Provenance) -> bytes:
    """Serialize provenance as a deterministic JSON-LD named graph."""

    canonical = _canonical_provenance(provenance, require_graph_name=True)
    graph_id = _require_graph_name(canonical.graph_name)
    document = _NamedGraphDocument(
        context=_CONTEXT,
        id=graph_id,
        type="NamedGraph",
        provenance=canonical,
    )
    return msgspec.json.encode(document)


def decode_named_graph(payload: bytes) -> Provenance:
    """Decode a JSON-LD named graph payload into a provenance record."""

    document = msgspec.json.decode(payload, type=_NamedGraphDocument, strict=True)
    if document.type != "NamedGraph":
        raise ValueError(f"Unsupported provenance graph type: {document.type!r}")
    provenance = document.provenance
    graph_id = _require_graph_name(document.id)
    if provenance.graph_name is not None and provenance.graph_name != graph_id:
        raise ValueError("provenance graph_name must match named graph id")
    return _canonical_provenance(
        Provenance(
            status=provenance.status,
            witnesses=provenance.witnesses,
            graph_name=graph_id,
            derived_from=provenance.derived_from,
            operations=provenance.operations,
        ),
        require_graph_name=True,
    )


def write_provenance_note(
    repo: BaseRepo,
    object_sha: bytes | str,
    provenance: Provenance,
) -> bytes:
    """Attach a provenance named graph to a git object using git notes.

    The note rides on ``refs/notes/provenance`` keyed by ``object_sha``; the
    annotated object is never rewritten, so provenance stays out of identity.
    """

    return write_git_note(
        repo,
        PROVENANCE_NOTES,
        _object_sha_bytes(object_sha),
        encode_named_graph(provenance),
        author=b"propstore <propstore@example.com>",
        committer=b"propstore <propstore@example.com>",
        message=b"Record provenance named graph",
    )


def read_provenance_note(
    repo: BaseRepo,
    object_sha: bytes | str,
) -> Provenance | None:
    """Read a provenance named graph from the provenance notes ref."""

    payload = read_git_note(repo, PROVENANCE_NOTES, _object_sha_bytes(object_sha))
    if payload is None:
        return None
    return decode_named_graph(payload)


# ---------------------------------------------------------------------------
# YAML block builder
# ---------------------------------------------------------------------------


def _build_produced_by_yaml(
    agent: str,
    skill: str,
    status: ProvenanceStatus,
    plugin_version: str | None,
    timestamp: str,
) -> str:
    lines = [
        "produced_by:",
        f'  agent: "{agent}"',
        f'  skill: "{skill}"',
        f'  status: "{status.value}"',
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
    status: ProvenanceStatus,
    plugin_version: str | None,
    timestamp: str,
) -> tuple[str, bool]:
    """Add or update produced_by in markdown YAML frontmatter."""
    produced_by_block = _build_produced_by_yaml(
        agent, skill, status, plugin_version, timestamp
    )
    match = _FRONTMATTER_RE.match(text)

    if not match:
        # No frontmatter -- create it with just produced_by.
        result = f"---\n{produced_by_block}\n---\n{text}"
        return result, True

    frontmatter = match.group(1)
    body = text[match.end() :]

    if _PRODUCED_BY_BLOCK_RE.search(frontmatter):
        new_frontmatter = _PRODUCED_BY_BLOCK_RE.sub(
            produced_by_block, frontmatter
        ).rstrip()
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
    status: ProvenanceStatus,
    plugin_version: str | None,
    timestamp: str,
) -> tuple[str, bool]:
    """Add or update produced_by in a YAML file's top level."""
    produced_by_block = (
        _build_produced_by_yaml(agent, skill, status, plugin_version, timestamp) + "\n"
    )

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
    *,
    status: ProvenanceStatus,
    plugin_version: str | None = None,
    timestamp: str | None = None,
) -> bool:
    """Stamp provenance onto *path*. Returns True if the file was changed.

    The ``stated``-method authoring branch: it adds or updates a ``produced_by``
    block recording which agent, skill, and plugin version produced the file,
    plus the provenance status and a UTC timestamp. ``.md`` files are stamped in
    YAML frontmatter (created if absent); ``.yaml`` / ``.yml`` files at the top
    level.
    """
    if timestamp is None:
        timestamp = _utc_timestamp()

    text = path.read_text(encoding="utf-8")

    if path.suffix == ".md":
        result, changed = _stamp_md(
            text, agent, skill, status, plugin_version, timestamp
        )
    elif path.suffix in (".yaml", ".yml"):
        result, changed = _stamp_yaml(
            text, agent, skill, status, plugin_version, timestamp
        )
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    if changed:
        path.write_text(result, encoding="utf-8")
    return changed


__all__ = [
    "PROVENANCE_NOTES",
    "PROVENANCE_NOTES_REF",
    "ProjectionFrameProvenanceRecord",
    "Provenance",
    "ProvenanceStatus",
    "ProvenanceWitness",
    "compose_provenance",
    "decode_named_graph",
    "encode_named_graph",
    "read_provenance_note",
    "stamp_file",
    "write_provenance_note",
]
