"""Typed provenance value objects for the semantic layer.

A :class:`Provenance` records *how* a probability-bearing or asserted value came
to be — its typed :class:`ProvenanceStatus` (``measured`` / ``calibrated`` /
``stated`` / ``defaulted`` / ``vacuous``), the witnesses that asserted it, and the
chain of operations that transformed it. The reference grounding is CLAUDE.md's
"honest ignorance over fabricated confidence": every value entering the
argumentation layer must say *where it came from* rather than fabricate a number.

Scope boundary (PLAN.md §12.0 / §12.4): provenance is carried OUT-OF-BAND and is
NEVER part of concept/lexical identity. The *physical* carrier — a git note on
``refs/notes/provenance`` — is a later phase (Phase 8); this module defines only
the in-memory provenance TYPE that the lemon value objects require. Identity is
computed by functions that exclude provenance (see
:func:`propstore.core.lemon.lexical_entry_identity_key`), so attaching provenance
to a sense or a qualia reference never changes what that entry *is*.

These are frozen ``msgspec.Struct`` value objects so they nest directly inside the
charter document tree (and therefore the sidecar JSON projection) with one
canonical spelling — there is no provenance DTO/payload mirror.
"""

from __future__ import annotations

from enum import StrEnum

import msgspec


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


class ProvenanceWitness(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A single asserter of a value, with the artifact and method behind it."""

    asserter: str
    timestamp: str
    source_artifact_code: str
    method: str


class Provenance(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """Typed provenance: a status, its witnesses, and the operation chain.

    ``operations`` accumulates the deterministic transformations applied to the
    value (e.g. ``qualia_coercion:telic``) so a coerced view can be traced back to
    its source assertion. Provenance never enters identity (see module docstring).
    """

    status: ProvenanceStatus
    witnesses: tuple[ProvenanceWitness, ...] = ()
    operations: tuple[str, ...] = ()


class ProjectionFrameProvenanceRecord(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True
):
    """Out-of-band provenance for one backend-projected argumentation frame.

    When a claim is projected into a backend atom (ASPIC+, ATMS, …) the frame
    records which backend produced it, when, and the situated source assertion
    ids the projected atom is attributable to. Like every other provenance value
    object this rides *beside* the projected datum and never enters identity
    (module docstring): the projection's identity is its structural atom key, not
    this record. The carrier is logical here; the physical git-note carrier is a
    later phase.
    """

    frame_id: str
    backend: str
    projected_at: str
    source_assertion_ids: tuple[str, ...] = ()


def compose_provenance(provenance: Provenance, *, operation: str) -> Provenance:
    """Return a new :class:`Provenance` with ``operation`` appended to the chain.

    Provenance is immutable; composing an operation (e.g. a qualia coercion step)
    yields a fresh value carrying the same status and witnesses plus the recorded
    operation, so the transformation is auditable without mutating the source.
    """

    return Provenance(
        status=provenance.status,
        witnesses=provenance.witnesses,
        operations=(*provenance.operations, operation),
    )
