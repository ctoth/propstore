"""Argumentation-backed source-trust calibration (the projection core).

A source's prior trust is *argued for*, not assumed: trust rules fire against a
source's metadata, the firings are projected into a Dung framework, and the
``argumentation.core.dung`` kernel decides which survive. The surviving firings
map directly into a subjective-logic opinion (Jøsang 2001): undefeated *support*
firings contribute belief ``b``, undefeated *attack* firings contribute
disbelief ``d``, the unallocated mass is uncertainty ``u``, and the base rate
``a`` is the mean of the active firings' base rates.

Honest ignorance (CLAUDE.md): when no rule fires the prior is *defaulted* to a
vacuous opinion; when rules fire but none survive the grounded extension the
prior is *vacuous*; only when a firing survives is the result *calibrated*. The
typed :class:`~propstore.provenance.ProvenanceStatus` records which case held, so
a vacuous prior is never mistaken for evidence.

This module owns the pure, repository-free projection. Wiring it to a source
branch's stored metadata (loading rule corpora, resolving the world snapshot) is
the source subsystem's job in a later phase; that wiring calls
:func:`project_source_trust` and adds nothing to the b/d/u/a mapping.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib import metadata
from typing import Any

from argumentation.core.dung import ArgumentationFramework, grounded_extension
from doxa import Opinion

from propstore.provenance import ProvenanceStatus

_DOGMATIC_TOL = 1e-9
_DEFAULT_BASE_RATE = 0.5


@dataclass(frozen=True)
class RuleFiring:
    """One trust rule that matched a source's metadata, with its kernel verdict."""

    rule_id: str
    effect: str
    weight: float
    base_rate: float
    facts: tuple[tuple[str, object], ...]
    in_grounded_extension: bool


@dataclass(frozen=True)
class SourceTrustResult:
    """The calibrated (or honestly vacuous) prior trust opinion for a source.

    :attr:`prior_base_rate` is the ``doxa.Opinion`` and :attr:`status` is the
    typed origin of its value (``calibrated`` / ``vacuous`` / ``defaulted``) — the
    status rides *beside* the opinion, the honesty-layer pairing discipline.
    """

    prior_base_rate: Opinion
    derived_from: tuple[RuleFiring, ...]
    world_snapshot_sha: str
    kernel_version: str
    status: ProvenanceStatus


def kernel_version() -> str:
    """The installed argumentation package version (or an honest unknown)."""

    try:
        return metadata.version("formal-argumentation")
    except metadata.PackageNotFoundError:
        return "argumentation:unknown"


def _rule_matches(rule: Mapping[str, Any], source_metadata: Mapping[str, object]) -> bool:
    conditions: Mapping[str, Any] = rule.get("conditions", {})
    return all(source_metadata.get(str(key)) == value for key, value in conditions.items())


def _firing(rule: Mapping[str, Any], *, in_extension: bool) -> RuleFiring:
    conditions: Mapping[str, Any] = rule.get("conditions", {})
    return RuleFiring(
        rule_id=str(rule["id"]),
        effect=str(rule.get("effect", "support")),
        weight=float(rule.get("weight", 0.0)),
        base_rate=float(rule.get("base_rate", _DEFAULT_BASE_RATE)),
        facts=tuple(sorted((str(key), value) for key, value in conditions.items())),
        in_grounded_extension=in_extension,
    )


def _framework_for(fired_rules: Sequence[Mapping[str, Any]]) -> ArgumentationFramework:
    """Project fired rules to a Dung AF where attacks defeat supports.

    Every ``attack``-effect firing defeats every distinct ``support``-effect
    firing. The grounded extension then decides which firings stand.
    """

    arguments = frozenset(str(rule["id"]) for rule in fired_rules)
    defeats: set[tuple[str, str]] = set()
    for attacker in fired_rules:
        if str(attacker.get("effect", "support")) != "attack":
            continue
        attacker_id = str(attacker["id"])
        for target in fired_rules:
            target_id = str(target["id"])
            if target_id != attacker_id and str(target.get("effect", "support")) == "support":
                defeats.add((attacker_id, target_id))
    return ArgumentationFramework(arguments=arguments, defeats=frozenset(defeats))


def _opinion_from_firings(firings: Sequence[RuleFiring]) -> Opinion:
    """Map surviving firings to ``b`` (support) / ``d`` (attack) / ``u`` / ``a``."""

    active = [firing for firing in firings if firing.in_grounded_extension]
    belief = sum(firing.weight for firing in active if firing.effect == "support")
    disbelief = sum(firing.weight for firing in active if firing.effect == "attack")
    total = belief + disbelief
    if total > 1.0:
        belief, disbelief = belief / total, disbelief / total
    uncertainty = max(0.0, 1.0 - belief - disbelief)
    base_rates = [firing.base_rate for firing in active] or [_DEFAULT_BASE_RATE]
    return Opinion(
        belief,
        disbelief,
        uncertainty,
        sum(base_rates) / len(base_rates),
        allow_dogmatic=uncertainty <= _DOGMATIC_TOL,
    )


def project_source_trust(
    rules: Sequence[Mapping[str, Any]],
    source_metadata: Mapping[str, object],
    *,
    world_snapshot_sha: str = "",
    kernel_version_override: str | None = None,
) -> SourceTrustResult:
    """Calibrate a source's prior trust from trust rules and its metadata.

    Returns an honestly typed result: ``DEFAULTED`` + vacuous when no rule fires,
    ``VACUOUS`` when rules fire but none survive the grounded extension, and
    ``CALIBRATED`` with the projected opinion otherwise.
    """

    version = kernel_version_override if kernel_version_override is not None else kernel_version()
    fired_rules = tuple(rule for rule in rules if _rule_matches(rule, source_metadata))

    if not fired_rules:
        return SourceTrustResult(
            prior_base_rate=Opinion.vacuous(_DEFAULT_BASE_RATE),
            derived_from=(),
            world_snapshot_sha=world_snapshot_sha,
            kernel_version=version,
            status=ProvenanceStatus.DEFAULTED,
        )

    extension = grounded_extension(_framework_for(fired_rules))
    firings = tuple(
        _firing(rule, in_extension=str(rule["id"]) in extension) for rule in fired_rules
    )
    if not any(firing.in_grounded_extension for firing in firings):
        return SourceTrustResult(
            prior_base_rate=Opinion.vacuous(_DEFAULT_BASE_RATE),
            derived_from=firings,
            world_snapshot_sha=world_snapshot_sha,
            kernel_version=version,
            status=ProvenanceStatus.VACUOUS,
        )

    return SourceTrustResult(
        prior_base_rate=_opinion_from_firings(firings),
        derived_from=firings,
        world_snapshot_sha=world_snapshot_sha,
        kernel_version=version,
        status=ProvenanceStatus.CALIBRATED,
    )


__all__ = [
    "RuleFiring",
    "SourceTrustResult",
    "kernel_version",
    "project_source_trust",
]
