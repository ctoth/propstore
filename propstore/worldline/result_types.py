"""The typed content of a materialized worldline.

These are field-subset **views** built by attribute access from the values the
render already produced — never re-typed from a payload mapping. The worldline
charter stores them directly (``WorldlineDefinition.results``) and Quire's codec
owns the encode/decode, so there is no ``from_mapping``/``to_dict`` pair here and
no second spelling of the render's own types: the ATMS reports are the canonical
:mod:`propstore.core.atms_reports` ones, not local mirrors.

This module is **storage-pure** — it imports only from ``propstore.core`` — which
is what lets the charter (read by the storage layer, which may never import
``world``) declare a typed result document instead of a ``dict[str, Any]`` blob.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from propstore.core.atms_reports import (
    ATMSFutureStatusReport,
    ATMSNodeFutureStatusEntry,
    ATMSNodeRelevanceReport,
    ATMSNodeStabilityReport,
    ATMSNogoodDetail,
    ATMSWhyOutReport,
    SerializedEnvironment,
)


class WorldlineRevisionTargetValidationError(ValueError):
    """Raised when a revision target cannot be resolved as an atom id."""


def validated_revision_target(operation: str, target: object) -> str | None:
    """The single canonical revision-target validator.

    Lives here rather than on the charter so the charter and the revision query
    can both reach it without an import cycle.
    """

    if target is None:
        return None
    target_id = str(target)
    if operation == "contract" and not (
        target_id.startswith("ps:assertion:")
        or target_id.startswith("assumption:")
    ):
        raise WorldlineRevisionTargetValidationError(
            "Worldline revision target must be an assertion or assumption atom id: "
            f"{target_id}"
        )
    return target_id


class WorldlineCaptureError(Enum):
    """Which capture subsystem failed, recorded instead of an exception string.

    Equivalent failures must hash identically, so the fingerprint carries this
    typed marker rather than free-form exception text.
    """

    ARGUMENTATION = "argumentation"
    REVISION = "revision"
    SENSITIVITY = "sensitivity"


@dataclass(frozen=True)
class WorldlineVariableRef:
    """A variable a claim binds — name, symbol, and the concept it refers to."""

    name: str | None = None
    symbol: str | None = None
    concept_id: str | None = None


@dataclass(frozen=True)
class WorldlineInputSource:
    """Where one input to a derived value came from."""

    source: str
    value: float | str | None = None
    claim_id: str | None = None
    formula: str | None = None
    reason: str | None = None
    strategy: str | None = None
    inputs_used: Mapping[str, "WorldlineInputSource"] = field(
        default_factory=dict[str, "WorldlineInputSource"]
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "inputs_used", dict(self.inputs_used))


@dataclass(frozen=True)
class WorldlineTargetValue:
    """The resolved value of one worldline target."""

    status: str
    value: float | str | None = None
    source: str | None = None
    reason: str | None = None
    claim_id: str | None = None
    winning_claim_id: str | None = None
    claim_type: str | None = None
    statement: str | None = None
    expression: str | None = None
    body: str | None = None
    name: str | None = None
    variables: tuple[WorldlineVariableRef, ...] = ()
    formula: str | None = None
    strategy: str | None = None
    inputs_used: Mapping[str, WorldlineInputSource] = field(
        default_factory=dict[str, WorldlineInputSource]
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "inputs_used", dict(self.inputs_used))


@dataclass(frozen=True)
class WorldlineStep:
    """One recorded step of the resolution trace."""

    concept: str
    source: str
    value: float | str | None = None
    claim_id: str | None = None
    strategy: str | None = None
    reason: str | None = None
    formula: str | None = None


@dataclass(frozen=True)
class WorldlineDependencies:
    """The artifacts a render depended on — its cache key in provenance form."""

    claims: tuple[str, ...] = ()
    stances: tuple[str, ...] = ()
    contexts: tuple[str, ...] = ()
    lifting_rules: tuple[str, ...] = ()
    blocked_exceptions: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorldlineSensitivityEntry:
    input_name: str
    elasticity: float | None = None
    partial_derivative: float | None = None


@dataclass(frozen=True)
class WorldlineSensitivityOutcome:
    """Sensitivity for one target: entries, or an honest capture-failure marker."""

    entries: tuple[WorldlineSensitivityEntry, ...] = ()
    error: WorldlineCaptureError | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))


@dataclass(frozen=True)
class WorldlineSensitivityReport:
    targets: Mapping[str, WorldlineSensitivityOutcome] = field(
        default_factory=dict[str, WorldlineSensitivityOutcome]
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "targets", dict(self.targets))


@dataclass(frozen=True)
class WorldlineArgumentationState:
    """The argumentation state a render captured, whatever backend produced it.

    The ATMS-scoped fields hold the engine's own report types by direct
    attribute access. They used to arrive through a dict hop that never parsed
    them back, so a freshly captured state held typed reports while a state
    loaded from disk held raw dicts — one static type, two runtime shapes. The
    charter now stores these typed and Quire decodes them, so both paths agree.
    """

    backend: str | None = None
    status: str | None = None
    error: WorldlineCaptureError | None = None
    justified: tuple[str, ...] = ()
    defeated: tuple[str, ...] = ()
    extensions: tuple[tuple[str, ...], ...] = ()
    inference_mode: str | None = None
    acceptance_probs: Mapping[str, float] = field(default_factory=dict[str, float])
    strategy_used: str | None = None
    samples: int | None = None
    confidence_interval_half: float | None = None
    semantics: str | None = None
    supported: tuple[str, ...] = ()
    nogoods: tuple[tuple[str, ...], ...] = ()
    node_statuses: Mapping[str, str] = field(default_factory=dict[str, str])
    support_quality: Mapping[str, str] = field(default_factory=dict[str, str])
    # The minimal environment each claim's support rests on. This is an
    # environment (assumption ids + context ids), not a flat id list: the old
    # dict hop declared it ``tuple[str, ...]`` and then iterated the serialized
    # environment *mapping*, so every stored value was the literal key list
    # ``("assumption_ids", "context_ids")`` rather than the support itself.
    essential_support: Mapping[str, SerializedEnvironment | None] = field(
        default_factory=dict[str, SerializedEnvironment | None]
    )
    status_reasons: Mapping[str, str | None] = field(default_factory=dict[str, str | None])
    nogood_details: tuple[ATMSNogoodDetail, ...] = ()
    declared_queryables: tuple[str, ...] = ()
    future_statuses: Mapping[str, ATMSFutureStatusReport] = field(
        default_factory=dict[str, ATMSFutureStatusReport]
    )
    stability: Mapping[str, ATMSNodeStabilityReport] = field(
        default_factory=dict[str, ATMSNodeStabilityReport]
    )
    relevance: Mapping[str, ATMSNodeRelevanceReport] = field(
        default_factory=dict[str, ATMSNodeRelevanceReport]
    )
    witness_futures: Mapping[str, tuple[ATMSNodeFutureStatusEntry, ...]] = field(
        default_factory=dict[str, tuple[ATMSNodeFutureStatusEntry, ...]]
    )
    why_out: Mapping[str, ATMSWhyOutReport] = field(default_factory=dict[str, ATMSWhyOutReport])

    def __post_init__(self) -> None:
        object.__setattr__(self, "justified", tuple(self.justified))
        object.__setattr__(self, "defeated", tuple(self.defeated))
        object.__setattr__(
            self,
            "extensions",
            tuple(tuple(str(item) for item in extension) for extension in self.extensions),
        )
        object.__setattr__(self, "acceptance_probs", dict(self.acceptance_probs))
        object.__setattr__(self, "supported", tuple(self.supported))
        object.__setattr__(
            self,
            "nogoods",
            tuple(tuple(str(item) for item in entry) for entry in self.nogoods),
        )
        object.__setattr__(self, "node_statuses", dict(self.node_statuses))
        object.__setattr__(self, "support_quality", dict(self.support_quality))
        object.__setattr__(self, "essential_support", dict(self.essential_support))
        object.__setattr__(self, "status_reasons", dict(self.status_reasons))
        object.__setattr__(self, "nogood_details", tuple(self.nogood_details))
        object.__setattr__(self, "declared_queryables", tuple(self.declared_queryables))
        object.__setattr__(self, "future_statuses", dict(self.future_statuses))
        object.__setattr__(self, "stability", dict(self.stability))
        object.__setattr__(self, "relevance", dict(self.relevance))
        object.__setattr__(
            self,
            "witness_futures",
            {
                str(claim_id): tuple(entries)
                for claim_id, entries in self.witness_futures.items()
            },
        )
        object.__setattr__(self, "why_out", dict(self.why_out))


__all__ = [
    "WorldlineArgumentationState",
    "WorldlineCaptureError",
    "WorldlineDependencies",
    "WorldlineInputSource",
    "WorldlineRevisionTargetValidationError",
    "WorldlineSensitivityEntry",
    "WorldlineSensitivityOutcome",
    "WorldlineSensitivityReport",
    "WorldlineStep",
    "WorldlineTargetValue",
    "WorldlineVariableRef",
    "validated_revision_target",
]
