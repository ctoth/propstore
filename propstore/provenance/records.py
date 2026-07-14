"""The typed projection-frame provenance record.

:class:`ProjectionFrameProvenanceRecord` is the *out-of-band* provenance carrier
for the argumentation projection boundary
(:mod:`propstore.structured_projection`, :mod:`propstore.aspic_bridge`), which
holds it as a frozen-dataclass field. It validates its URI invariants on
construction (Carroll et al. 2005 names a provenance graph; the identifiers it
names must be real URIs) and exposes a deterministic ``identity_payload`` so
equal records compare equal. :mod:`propstore.provenance.prov_o` projects it to
PROV-O at export time by attribute access — there is no ``to_payload`` dict hop.

It is the *only* record here. The import-side records (source version, license,
import run, external statement, external inference) were deleted on 2026-07-14:
they were a second spelling of :class:`~propstore.provenance.Provenance`, whose
witnesses now carry the source version and content hash directly, on the git
note where provenance belongs (see ``docs/gaps.md``). Provenance that is stored
rides the note; provenance that a projection holds in memory rides this record.
"""

from __future__ import annotations

from dataclasses import dataclass

from propstore.provenance._jsonld import URI_SCHEME_PREFIXES as _URI_PREFIXES


def _require_non_empty(value: str, label: str) -> str:
    text = str(value).strip()
    if text == "":
        raise ValueError(f"{label} must be non-empty")
    return text


def _require_uri(value: str, label: str) -> str:
    text = _require_non_empty(value, label)
    if not text.startswith(_URI_PREFIXES):
        raise ValueError(f"{label} must be a URI")
    return text


def _canonical_non_empty_set(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    canonical = tuple(sorted({_require_non_empty(value, label) for value in values}))
    if not canonical:
        raise ValueError(f"{label} set must be non-empty")
    return canonical


@dataclass(frozen=True)
class ProjectionFrameProvenanceRecord:
    """Projection activity over one or more situated assertion identities."""

    frame_id: str
    backend: str
    projected_at: str
    source_assertion_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "frame_id", _require_uri(self.frame_id, "frame_id"))
        object.__setattr__(self, "backend", _require_non_empty(self.backend, "backend"))
        object.__setattr__(
            self, "projected_at", _require_non_empty(self.projected_at, "projected_at")
        )
        object.__setattr__(
            self,
            "source_assertion_ids",
            _canonical_non_empty_set(self.source_assertion_ids, "source assertion"),
        )

    def identity_payload(self) -> tuple[str, str, str, tuple[str, ...]]:
        return (
            "projection_frame",
            self.frame_id,
            self.backend,
            self.source_assertion_ids,
        )
