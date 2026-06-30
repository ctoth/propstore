"""Canonical claim-tree integrity verification.

:func:`verify_claim_tree` is a *read-only* auditor over a repository's canonical
corpus. It walks the charter-derived foreign-key graph (the same
:func:`~propstore.families.registry.semantic_foreign_keys` specs the commit-time
gate enforces) and resolves every cross-family reference through quire's
:class:`~quire.references.FamilyReferenceIndex`. Where the commit-time validator
(`quire.families._validate_registry_post_state`) *raises* on the first dangling
reference, this is its post-hoc, non-raising counterpart: it can be run against
*any* committed repository state — after an import, after a merge, against
historical commits — to produce a typed integrity report.

Non-commitment (CLAUDE.md): verify never drops, collapses, or rewrites anything.
It *reports*. A reference that does not resolve is surfaced as ``dangling``; it is
not deleted. Crucially, a record that is itself *quarantined* (a ``BLOCKED``
authoring status — present in storage but hidden by default render policy) is not
a hard failure: its unresolved references are reported under ``quarantined``,
because quarantine is a valid present-but-filtered state, not corruption. The
report is the deliverable; whether any state is "bad" is a downstream policy call.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from quire.references import (
    ForeignKeySpec,
    ForeignKeyValidationError,
    ReferenceIndex,
    validate_foreign_key,
)

from propstore.families.registry import (
    PROPSTORE_FAMILY_REGISTRY,
    semantic_foreign_keys,
)

if TYPE_CHECKING:
    from propstore.repository import Repository

_QUARANTINE_STATUS = "blocked"


@dataclass(frozen=True)
class ForeignKeyResolution:
    """The outcome of resolving one foreign-key reference held by one record.

    ``resolved_ids`` carries the canonical ids the reference resolved to (one for
    a singular foreign key, possibly several for a ``many`` key). ``detail`` is
    ``None`` for a resolved reference and carries the validator's diagnostic when
    the reference failed to resolve.
    """

    foreign_key: str
    source_family: str
    source_id: str
    target_family: str
    resolved_ids: tuple[str, ...]
    detail: str | None = None


@dataclass(frozen=True)
class QuarantinedRecord:
    """A quarantined (``BLOCKED``) record carrying unresolved references.

    The references in ``unresolved`` would be reported as ``dangling`` for an
    authored record; because this record is quarantined they are excused — surfaced
    so an auditor sees them, but never counted as a hard failure.
    """

    family: str
    artifact_id: str
    status: str
    unresolved: tuple[ForeignKeyResolution, ...]


@dataclass(frozen=True)
class ClaimTreeIntegrityReport:
    """A typed integrity report over the canonical claim tree.

    Surfaces problems; it does not decide them. ``resolved`` holds every
    foreign-key reference that resolved against the charter-derived graph;
    ``dangling`` holds references on authored records that did not resolve;
    ``quarantined`` holds blocked records whose unresolved references are excused;
    ``malformed_identity`` holds ``(family, detail)`` pairs for records lacking a
    well-formed artifact id.
    """

    resolved: tuple[ForeignKeyResolution, ...]
    dangling: tuple[ForeignKeyResolution, ...]
    quarantined: tuple[QuarantinedRecord, ...]
    malformed_identity: tuple[tuple[str, str], ...]

    @property
    def ok(self) -> bool:
        """Whether the tree is free of integrity problems.

        ``True`` when there is no dangling reference and no malformed identity.
        Quarantined records do not make a tree not-``ok`` — quarantine is a valid
        state, not corruption.
        """

        return not self.dangling and not self.malformed_identity


def _is_quarantined(record: object) -> bool:
    """Whether *record* is in a quarantined (``BLOCKED``) authoring status."""

    status = getattr(record, "status", None)
    value = getattr(status, "value", status)
    return value == _QUARANTINE_STATUS


def _quarantine_status(record: object) -> str:
    status = getattr(record, "status", None)
    value = getattr(status, "value", status)
    return str(value)


def _specs_by_source(
    specs: tuple[ForeignKeySpec, ...],
) -> dict[str, list[ForeignKeySpec]]:
    grouped: dict[str, list[ForeignKeySpec]] = defaultdict(list)
    for spec in specs:
        grouped[spec.source_family].append(spec)
    return grouped


def verify_claim_tree(
    repo: Repository, *, commit: str | None = None
) -> ClaimTreeIntegrityReport:
    """Audit the integrity of the canonical claim tree at *commit*.

    Every record of every semantic family is checked: its identity must be
    well-formed, and each of its charter-declared foreign keys must resolve
    against the referenced family's :class:`~quire.references.FamilyReferenceIndex`.
    Read-only — nothing is mutated, dropped, or collapsed.
    """

    specs_by_source = _specs_by_source(semantic_foreign_keys())

    target_indexes: dict[str, ReferenceIndex[object]] = {}

    def target_index(target_family: str) -> ReferenceIndex[object]:
        cached = target_indexes.get(target_family)
        if cached is not None:
            return cached
        family_index = repo.families.by_name(target_family).reference_index(
            commit=commit
        )
        records: dict[str, object] = dict(family_index.records_by_id)
        index: ReferenceIndex[object] = ReferenceIndex(
            family=family_index.family,
            records_by_id=records,
            lookup=family_index.lookup,
        )
        target_indexes[target_family] = index
        return index

    resolved: list[ForeignKeyResolution] = []
    dangling: list[ForeignKeyResolution] = []
    quarantined: list[QuarantinedRecord] = []
    malformed_identity: list[tuple[str, str]] = []

    for source_family, specs in specs_by_source.items():
        definition = PROPSTORE_FAMILY_REGISTRY.by_name(source_family)
        identity_field = definition.identity_field
        bound = repo.families.by_name(source_family)
        for handle in bound.iter_handles(commit=commit):
            record = handle.document
            raw_id = (
                getattr(record, identity_field, None)
                if identity_field is not None
                else None
            )
            if not isinstance(raw_id, str) or not raw_id:
                malformed_identity.append((source_family, repr(record)))
                continue
            artifact_id = raw_id
            record_is_quarantined = _is_quarantined(record)
            record_unresolved: list[ForeignKeyResolution] = []
            for spec in specs:
                try:
                    resolved_ids = validate_foreign_key(
                        spec, record, target_index(spec.target_family)
                    )
                except ForeignKeyValidationError as error:
                    failure = ForeignKeyResolution(
                        foreign_key=spec.name,
                        source_family=source_family,
                        source_id=artifact_id,
                        target_family=spec.target_family,
                        resolved_ids=(),
                        detail=str(error),
                    )
                    if record_is_quarantined:
                        record_unresolved.append(failure)
                    else:
                        dangling.append(failure)
                    continue
                if resolved_ids:
                    resolved.append(
                        ForeignKeyResolution(
                            foreign_key=spec.name,
                            source_family=source_family,
                            source_id=artifact_id,
                            target_family=spec.target_family,
                            resolved_ids=tuple(resolved_ids),
                        )
                    )
            if record_is_quarantined and record_unresolved:
                quarantined.append(
                    QuarantinedRecord(
                        family=source_family,
                        artifact_id=artifact_id,
                        status=_quarantine_status(record),
                        unresolved=tuple(record_unresolved),
                    )
                )

    return ClaimTreeIntegrityReport(
        resolved=tuple(resolved),
        dangling=tuple(dangling),
        quarantined=tuple(quarantined),
        malformed_identity=tuple(malformed_identity),
    )
