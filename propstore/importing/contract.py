"""The repository import contract: what an external import must provide.

An import is not a privileged write. Every row an external knowledge base (BFO,
QUDT, a material database, an OWL ruleset, a mined association, an LLM proposal)
contributes becomes a *defeasible claim with provenance* — argueable,
conflictable, and supersedable exactly like any hand-authored claim, with no
source privileged ([[feedback_imports_are_opinions]]). This module defines the
typed request an importer hands the repository: the source identity and origin,
the typed concept/claim/stance candidate rows, and the *honest* provenance
status the import carries.

Provenance honesty is enforced here (CLAUDE.md honest-ignorance discipline): an
import may only declare :data:`ProvenanceStatus.STATED` (the external source
asserts the row) or :data:`ProvenanceStatus.DEFAULTED` (a fallback). It may never
launder an external assertion into ``MEASURED`` / ``CALIBRATED`` — those statuses
mean the *system* observed or calibrated the value, which an import did not do —
nor into ``VACUOUS`` (which would erase the assertion the source did make).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.claims import ClaimType
from propstore.provenance import ProvenanceStatus
from propstore.stances import StanceType, coerce_stance_type

_IMPORT_PROVENANCE_STATUSES = (ProvenanceStatus.STATED, ProvenanceStatus.DEFAULTED)


def _require_non_empty(value: str, label: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


@dataclass(frozen=True)
class ImportConceptRow:
    """One external row mapped to a source-branch concept candidate.

    ``local_name`` is the source-local handle the external KB used; it is never
    lowered to a canonical concept id here — that happens (defeasibly) at
    promote time. ``form`` names the dimensional/structural form the concept
    takes.
    """

    local_name: str
    definition: str
    form: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "local_name",
            _require_non_empty(self.local_name, "concept local_name"),
        )
        object.__setattr__(
            self,
            "definition",
            _require_non_empty(self.definition, "concept definition"),
        )
        object.__setattr__(self, "form", _require_non_empty(self.form, "concept form"))


@dataclass(frozen=True)
class ImportClaimRow:
    """One external row mapped to a source-branch claim candidate.

    ``local_id`` is the source-local handle; concept references (``concept`` /
    ``concepts``) hold source-local concept handles until promotion lowers them.
    """

    local_id: str
    claim_type: ClaimType
    context: str
    statement: str | None = None
    concept: str | None = None
    concepts: tuple[str, ...] = ()
    value: float | None = None
    unit: str | None = None
    conditions: tuple[str, ...] = ()
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "local_id", _require_non_empty(self.local_id, "claim local_id")
        )
        object.__setattr__(
            self, "context", _require_non_empty(self.context, "claim context")
        )


@dataclass(frozen=True)
class ImportStanceRow:
    """One external row mapped to a source-branch stance candidate.

    ``source_claim`` / ``target`` hold source-local claim handles; they are
    lowered to canonical claim ids by the import normalization pipeline.
    """

    source_claim: str
    target: str
    stance_type: StanceType
    strength: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_claim",
            _require_non_empty(self.source_claim, "stance source_claim"),
        )
        object.__setattr__(
            self, "target", _require_non_empty(self.target, "stance target")
        )
        coerced = coerce_stance_type(self.stance_type)
        if coerced is None:
            raise ValueError(f"unknown stance type: {self.stance_type!r}")
        object.__setattr__(self, "stance_type", coerced)


@dataclass(frozen=True)
class ImportManifest:
    """The typed request an external import hands the repository.

    Validated on construction: the declared :class:`ProvenanceStatus` must be an
    honest import status (``stated`` or ``defaulted``) — never a laundered
    ``measured`` / ``calibrated`` / ``vacuous``.
    """

    source_name: str
    kind: SourceKind
    origin_type: SourceOriginType
    origin_value: str
    provenance_status: ProvenanceStatus
    concepts: tuple[ImportConceptRow, ...] = ()
    claims: tuple[ImportClaimRow, ...] = ()
    stances: tuple[ImportStanceRow, ...] = ()
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "source_name", _require_non_empty(self.source_name, "source_name")
        )
        object.__setattr__(
            self, "origin_value", _require_non_empty(self.origin_value, "origin_value")
        )
        if self.provenance_status not in _IMPORT_PROVENANCE_STATUSES:
            allowed = ", ".join(status.value for status in _IMPORT_PROVENANCE_STATUSES)
            raise ValueError(
                f"import provenance status {self.provenance_status.value!r} is not honest: "
                f"an imported row is a stated/defaulted defeasible claim, never "
                f"measured/calibrated/vacuous (allowed: {allowed})"
            )


@dataclass(frozen=True)
class ImportResult:
    """The outcome of importing a manifest onto a source branch.

    The import does not touch canonical ``master``: it lands the rows on the
    source branch ``source_branch`` as defeasible claims, then leaves them to the
    ordinary finalize -> promote lifecycle. ``provenance_status`` is the honest
    status stamped on the source manifest and the import provenance note.
    """

    source_name: str
    source_branch: str
    commit_sha: str
    provenance_status: ProvenanceStatus
    concept_count: int
    claim_count: int
    stance_count: int
    warnings: tuple[str, ...] = ()
