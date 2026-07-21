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

:func:`verify_source_artifact_codes` is the second auditor: it recomputes each
source artifact's content code from its current content (reusing
:func:`propstore.artifact_codes.stamp_source_artifact_codes`) and compares it to
the stored code, and verifies the source's ``origin`` ni-URI against the retained
content file. This is the artifact-code *recompute* half of ``pks verify``; it is
deliberately world-free (storage layer reaches only down). The ATMS-label half of
the verify surface needs the bound belief space and therefore lives in the world
layer (:func:`propstore.world.serialize_claim_atms_label`); the CLI/audit surface
composes the two (PLAN.md §12.6 — no storage→world upward import).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from quire.references import (
    ForeignKeySpec,
    ForeignKeyValidationError,
    ReferenceIndex,
    validate_foreign_key,
)

from propstore.artifact_codes import stamp_source_artifact_codes
from propstore.families.registry import (
    PROPSTORE_FAMILY_REGISTRY,
    semantic_foreign_keys,
)
from propstore.source.common import (
    load_source_claims_document,
    load_source_document,
    load_source_justifications_document,
    load_source_stances_document,
    source_paper_slug,
)
from propstore.uri import verify_ni_uri

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


# --------------------------------------------------------------------------- #
# Source artifact-code recompute + origin verification
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ArtifactCodeMatch:
    """The recompute outcome for one source artifact's content code.

    ``expected`` is the stored ``artifact_code`` (``None`` when the artifact was
    never stamped); ``actual`` is the code recomputed from current content.
    """

    artifact_kind: str
    artifact_id: str
    expected: str | None
    actual: str

    @property
    def status(self) -> str:
        if not self.expected:
            return "unstamped"
        return "ok" if self.expected == self.actual else "mismatch"


@dataclass(frozen=True)
class OriginVerification:
    """Whether a source's retained content file matches its ``origin`` ni-URI."""

    status: str
    content_ref: str | None
    path: str | None


@dataclass(frozen=True)
class SourceArtifactVerificationReport:
    """Recompute report for one source branch's artifact codes plus its origin."""

    source_name: str
    matches: tuple[ArtifactCodeMatch, ...]
    origin: OriginVerification

    @property
    def ok(self) -> bool:
        """True when no recomputed code mismatches and the origin does not mismatch.

        An ``unstamped`` artifact (never finalized) or an ``unavailable`` origin
        (the content file is not retained locally) is not a failure — only an
        actual ``mismatch`` is.
        """

        return (
            all(match.status != "mismatch" for match in self.matches)
            and self.origin.status != "mismatch"
        )


def _verify_source_origin(
    repo: Repository, source_name: str, content_ref: str | None, origin_value: str
) -> OriginVerification:
    """Verify a source's ``origin`` ni-URI against its retained content file."""

    if not content_ref:
        return OriginVerification("unavailable", content_ref, None)
    papers_dir = repo.root.parent / "papers" / source_paper_slug(source_name)
    candidates: list[Path] = []
    if origin_value:
        value_path = Path(origin_value)
        if value_path.is_absolute():
            candidates.append(value_path)
        candidates.append(papers_dir / value_path.name)
    candidates.append(papers_dir / "paper.pdf")
    for candidate in candidates:
        if candidate.is_file():
            matched = verify_ni_uri(content_ref, candidate.read_bytes())
            return OriginVerification(
                "matched" if matched else "mismatch", content_ref, str(candidate)
            )
    return OriginVerification("unavailable", content_ref, None)


def verify_source_artifact_codes(
    repo: Repository, source_name: str
) -> SourceArtifactVerificationReport:
    """Recompute a source branch's artifact codes and verify its origin ni-URI.

    Recomputes the source manifest / claim / justification / stance codes from
    their current content (reusing the one canonical
    :func:`~propstore.artifact_codes.stamp_source_artifact_codes`, so finalize and
    verify compute the *same* code) and compares each to the stored code; a
    content edit since finalize surfaces as a ``mismatch`` (and cascades into the
    claim codes that fold in the source code). Read-only — it reports, never
    rewrites (CLAUDE.md non-commitment).
    """

    source_doc = load_source_document(repo, source_name)
    claims_doc = load_source_claims_document(repo, source_name)
    justifications_doc = load_source_justifications_document(repo, source_name)
    stances_doc = load_source_stances_document(repo, source_name)

    rec_source, rec_claims, rec_justifications, rec_stances = (
        stamp_source_artifact_codes(
            source_doc, claims_doc, justifications_doc, stances_doc
        )
    )

    matches: list[ArtifactCodeMatch] = [
        ArtifactCodeMatch(
            artifact_kind="source",
            artifact_id=source_doc.id,
            expected=source_doc.artifact_code,
            actual=rec_source.artifact_code or "",
        )
    ]
    if claims_doc is not None and rec_claims is not None:
        for original, recomputed in zip(claims_doc.claims, rec_claims.claims):
            matches.append(
                ArtifactCodeMatch(
                    artifact_kind="claim",
                    artifact_id=original.artifact_id or original.id or "?",
                    expected=original.artifact_code,
                    actual=recomputed.artifact_code or "",
                )
            )
    if justifications_doc is not None and rec_justifications is not None:
        for original, recomputed in zip(
            justifications_doc.justifications, rec_justifications.justifications
        ):
            matches.append(
                ArtifactCodeMatch(
                    artifact_kind="justification",
                    artifact_id=original.id or "?",
                    expected=original.artifact_code,
                    actual=recomputed.artifact_code or "",
                )
            )
    if stances_doc is not None and rec_stances is not None:
        for original, recomputed in zip(stances_doc.stances, rec_stances.stances):
            matches.append(
                ArtifactCodeMatch(
                    artifact_kind="stance",
                    artifact_id=f"{original.source_claim}->{original.target}",
                    expected=original.artifact_code,
                    actual=recomputed.artifact_code or "",
                )
            )

    origin = _verify_source_origin(
        repo, source_name, source_doc.origin.content_ref, source_doc.origin.value
    )
    return SourceArtifactVerificationReport(
        source_name=source_name, matches=tuple(matches), origin=origin
    )
