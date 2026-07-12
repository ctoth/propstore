"""World-consistency owner API.

Reports the conflicts a :class:`~propstore.core.environment.WorldStore` exposes
under a set of bindings — either the direct conflicts a bound belief space sees,
or the multi-hop parameterization-derivation conflicts found across the whole
compiled graph. A presentation adapter (CLI/web, later phase) renders the typed
:class:`WorldConsistencyReport`; this module owns the semantics and never touches
Click, stdout, or exit codes (CLAUDE.md CLI-adapter discipline).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


from propstore.conflict_detector.models import ConflictClaim
from propstore.core.environment import Environment, WorldStore
from propstore.reporting import JsonReportMixin
from propstore.world import model
from propstore.world.bound import conflict_inputs_for_store


@dataclass(frozen=True)
class WorldConsistencyRequest:
    bindings: Mapping[str, str]
    transitive: bool = False


@dataclass(frozen=True)
class WorldConsistencyConflictLine:
    concept_id: str
    warning_class: str | None = None
    claim_a_id: str | None = None
    claim_b_id: str | None = None
    value_a: object = None
    value_b: object = None
    derivation_chain: object = None


@dataclass(frozen=True)
class WorldConsistencyReport(JsonReportMixin):
    transitive: bool
    conflicts: tuple[WorldConsistencyConflictLine, ...]


def check_world_consistency(
    store: WorldStore,
    request: WorldConsistencyRequest,
) -> WorldConsistencyReport:
    """Report the conflicts ``store`` exposes under ``request``'s bindings."""

    if request.transitive:
        return _check_transitive_consistency(store)

    bound = model.bind(store, Environment(bindings=dict(request.bindings)))
    return WorldConsistencyReport(
        transitive=False,
        conflicts=tuple(
            WorldConsistencyConflictLine(
                concept_id=str(record.concept_id),
                warning_class=record.warning_class.value,
                claim_a_id=str(record.claim_a_id),
                claim_b_id=str(record.claim_b_id),
                value_a=record.value_a,
                value_b=record.value_b,
            )
            for record in bound.conflicts()
        ),
    )


def _check_transitive_consistency(store: WorldStore) -> WorldConsistencyReport:
    from propstore.conflict_detector import detect_transitive_conflicts

    compiled = model.compiled_graph(store)
    conflict_claims = [ConflictClaim.from_claim(claim) for claim in compiled.claims]
    concept_registry, _cel_registry = conflict_inputs_for_store(store)
    records = detect_transitive_conflicts(conflict_claims, concept_registry)
    return WorldConsistencyReport(
        transitive=True,
        conflicts=tuple(
            WorldConsistencyConflictLine(
                concept_id=str(record.concept_id),
                value_a=record.value_a,
                value_b=record.value_b,
                derivation_chain=record.derivation_chain,
            )
            for record in records
        ),
    )
