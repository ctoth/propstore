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
from typing import TYPE_CHECKING, Any, TypeAlias

import yaml
from argumentation.core.dung import ArgumentationFramework, grounded_extension
from doxa import Opinion

from propstore.provenance import ProvenanceStatus

if TYPE_CHECKING:
    from propstore.repository import Repository

_Json: TypeAlias = "None | bool | int | float | str | list[_Json] | dict[str, _Json]"
"""The value shape ``yaml.safe_load`` yields for a rule file (concrete, not Any)."""

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


def _rule_matches(
    rule: Mapping[str, Any], source_metadata: Mapping[str, object]
) -> bool:
    conditions: Mapping[str, Any] = rule.get("conditions", {})
    return all(
        source_metadata.get(str(key)) == value for key, value in conditions.items()
    )


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
            if (
                target_id != attacker_id
                and str(target.get("effect", "support")) == "support"
            ):
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

    version = (
        kernel_version_override
        if kernel_version_override is not None
        else kernel_version()
    )
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


def _load_rules_from_repo(repo: Repository) -> tuple[Mapping[str, Any], ...]:
    """Load source-trust rules from the repository's working-tree rule corpus.

    Rules live as YAML under ``<root>/rules`` (or ``<root>/knowledge/rules``).
    Each file is either a single rule mapping, a list of rule mappings, or a
    ``{"rules": [...]}`` container. A rule is ``{id, effect, conditions, weight,
    base_rate}`` — the shape :func:`project_source_trust` consumes directly.
    """

    rules_root = repo.root / "rules"
    if not rules_root.exists():
        rules_root = repo.root / "knowledge" / "rules"
    if not rules_root.exists():
        return ()

    rules: list[Mapping[str, Any]] = []
    for path in sorted(rules_root.rglob("*.yaml")):
        loaded: _Json = yaml.safe_load(path.read_text(encoding="utf-8"))
        mapping = _str_keyed(loaded)
        if mapping is not None:
            container = mapping.get("rules")
            collected = _collect_rules(container)
            rules.extend(collected if collected else (mapping,))
            continue
        rules.extend(_collect_rules(loaded))
    return tuple(rules)


def _str_keyed(value: _Json) -> dict[str, _Json] | None:
    """Return *value* as a ``{str: value}`` mapping, or ``None`` if not a mapping."""

    if not isinstance(value, dict):
        return None
    return {str(key): item for key, item in value.items()}


def _collect_rules(value: _Json) -> list[Mapping[str, Any]]:
    """Coerce a YAML list of rule mappings into ``[{str: value}, ...]``."""

    if not isinstance(value, list):
        return []
    return [rule for item in value if (rule := _str_keyed(item)) is not None]


def calibrate_source_trust(
    repo: Repository,
    source_name: str,
    *,
    rule_corpus: Sequence[Mapping[str, Any]] | None = None,
    world_snapshot: object | None = None,
) -> SourceTrustResult:
    """Calibrate a source's prior trust from its rule corpus and metadata.

    The repository-bound wiring around the pure :func:`project_source_trust`
    projection: it loads the rule corpus (unless one is supplied) and the source
    branch's stored metadata, then projects an honestly typed
    :class:`SourceTrustResult`. This is a *stamp*, never a gate — a source whose
    metadata fires no rule gets a ``DEFAULTED`` vacuous prior and still promotes;
    calibration never rejects a claim.
    """

    from propstore.source.common import load_source_metadata

    rules = (
        tuple(rule_corpus) if rule_corpus is not None else _load_rules_from_repo(repo)
    )
    metadata_payload = load_source_metadata(repo, source_name) or {}
    repo_head = repo.require_git().head_sha() if repo.git is not None else None
    world_sha = str(world_snapshot if world_snapshot is not None else (repo_head or ""))
    return project_source_trust(
        rules,
        metadata_payload,
        world_snapshot_sha=world_sha,
    )


__all__ = [
    "RuleFiring",
    "SourceTrustResult",
    "calibrate_source_trust",
    "kernel_version",
    "project_source_trust",
]
