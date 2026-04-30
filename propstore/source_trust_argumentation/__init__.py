"""Argumentation-backed source-trust calibration.

Rule firings are projected into a Dung framework and evaluated by the
`argumentation.dung` kernel. Undefeated supporting firings contribute belief,
undefeated attacking firings contribute disbelief, and the unallocated mass is
uncertainty. This is the direct subjective-logic mapping used by WS-K: support
maps to `b`, attack maps to `d`, blocked or absent rule mass maps to `u`, and
the base rate `a` comes from the fired rule defaults or 0.5.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

import yaml
from argumentation.dung import ArgumentationFramework, grounded_extension

from propstore.opinion import Opinion
from propstore.provenance import ProvenanceStatus
from propstore.repository import Repository
from propstore.families.registry import SourceRef


@dataclass(frozen=True)
class RuleFiring:
    rule_id: str
    effect: str
    weight: float
    base_rate: float
    facts: tuple[tuple[str, object], ...]
    in_grounded_extension: bool


@dataclass(frozen=True)
class SourceTrustResult:
    prior_base_rate: Opinion
    derived_from: tuple[RuleFiring, ...]
    world_snapshot_sha: str
    kernel_version: str
    status: ProvenanceStatus


def _kernel_version() -> str:
    try:
        return metadata.version("formal-argumentation")
    except metadata.PackageNotFoundError:
        return "argumentation:unknown"


def _load_rules_from_repo(repo: Repository) -> tuple[Mapping[str, Any], ...]:
    rules_root = repo.root / "knowledge" / "rules"
    if not rules_root.exists():
        rules_root = repo.root / "rules"
    if not rules_root.exists():
        project_rules = Path(__file__).resolve().parents[2] / "knowledge" / "rules"
        if project_rules.exists():
            rules_root = project_rules
    if not rules_root.exists():
        return ()

    rules: list[Mapping[str, Any]] = []
    for path in sorted(rules_root.rglob("*.yaml")):
        loaded = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if isinstance(loaded, Mapping) and isinstance(loaded.get("rules"), Sequence):
            paper = str(
                loaded.get("source", {}).get("paper", path.parent.name)
                if isinstance(loaded.get("source"), Mapping)
                else path.parent.name
            )
            for rule in loaded["rules"]:
                if isinstance(rule, Mapping):
                    rules.append(_source_trust_rule_from_document(paper, rule))
        elif isinstance(loaded, Mapping):
            rules.append(dict(loaded))
        elif isinstance(loaded, Sequence) and not isinstance(loaded, str):
            rules.extend(dict(item) for item in loaded if isinstance(item, Mapping))
    return tuple(rules)


def _source_trust_rule_from_document(
    paper: str,
    rule: Mapping[str, Any],
) -> Mapping[str, Any]:
    conditions: dict[str, object] = {}
    body = rule.get("body", ())
    if isinstance(body, Sequence) and not isinstance(body, str):
        for literal in body:
            if not isinstance(literal, Mapping) or literal.get("kind") != "positive":
                continue
            atom = literal.get("atom")
            if not isinstance(atom, Mapping):
                continue
            terms = atom.get("terms", ())
            if not isinstance(terms, Sequence) or isinstance(terms, str) or len(terms) < 2:
                continue
            value_term = terms[1]
            if isinstance(value_term, Mapping) and value_term.get("kind") == "const":
                conditions[str(atom["predicate"])] = value_term.get("value")
    head = rule.get("head", {})
    head_predicate = str(head.get("predicate", "")) if isinstance(head, Mapping) else ""
    return {
        "id": f"{paper}:{rule['id']}",
        "effect": "support" if head_predicate == "high_trust" else "attack",
        "weight": 0.25,
        "base_rate": 0.5,
        "conditions": conditions,
    }


def _rule_matches(rule: Mapping[str, Any], metadata_payload: Mapping[str, object]) -> bool:
    conditions = rule.get("conditions", {})
    if not isinstance(conditions, Mapping):
        raise ValueError("source trust rule conditions must be a mapping")
    return all(metadata_payload.get(str(key)) == value for key, value in conditions.items())


def _firing(rule: Mapping[str, Any], *, in_extension: bool) -> RuleFiring:
    conditions = rule.get("conditions", {})
    if not isinstance(conditions, Mapping):
        raise ValueError("source trust rule conditions must be a mapping")
    return RuleFiring(
        rule_id=str(rule["id"]),
        effect=str(rule.get("effect", "support")),
        weight=float(rule.get("weight", 0.0)),
        base_rate=float(rule.get("base_rate", 0.5)),
        facts=tuple(sorted((str(key), value) for key, value in conditions.items())),
        in_grounded_extension=in_extension,
    )


def _framework_for(fired_rules: Sequence[Mapping[str, Any]]) -> ArgumentationFramework:
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
    active = [firing for firing in firings if firing.in_grounded_extension]
    belief = sum(firing.weight for firing in active if firing.effect == "support")
    disbelief = sum(firing.weight for firing in active if firing.effect == "attack")
    committed = min(1.0, belief + disbelief)
    if committed < belief + disbelief:
        belief = belief / (belief + disbelief)
        disbelief = disbelief / (belief + disbelief)
    uncertainty = max(0.0, 1.0 - belief - disbelief)
    base_rates = [firing.base_rate for firing in active] or [0.5]
    return Opinion(
        belief,
        disbelief,
        uncertainty,
        sum(base_rates) / len(base_rates),
        allow_dogmatic=uncertainty <= 1e-9,
    )


def calibrate_source_trust(
    repo: Repository,
    source_name: str,
    *,
    rule_corpus: Sequence[Mapping[str, Any]] | None = None,
    world_snapshot: object | None = None,
) -> SourceTrustResult:
    rules = tuple(rule_corpus) if rule_corpus is not None else _load_rules_from_repo(repo)
    metadata_payload = repo.families.source_metadata.load(SourceRef(source_name)) or {}
    fired_rules = tuple(rule for rule in rules if _rule_matches(rule, metadata_payload))
    repo_head = repo.git.head_sha() if repo.git is not None else None
    world_sha = str(world_snapshot or repo_head or "")

    if not fired_rules:
        return SourceTrustResult(
            prior_base_rate=Opinion.vacuous(0.5),
            derived_from=(),
            world_snapshot_sha=world_sha,
            kernel_version=_kernel_version(),
            status=ProvenanceStatus.DEFAULTED,
        )

    extension = grounded_extension(_framework_for(fired_rules))
    firings = tuple(
        _firing(rule, in_extension=str(rule["id"]) in extension)
        for rule in fired_rules
    )
    active_firings = tuple(firing for firing in firings if firing.in_grounded_extension)
    if not active_firings:
        return SourceTrustResult(
            prior_base_rate=Opinion.vacuous(0.5),
            derived_from=firings,
            world_snapshot_sha=world_sha,
            kernel_version=_kernel_version(),
            status=ProvenanceStatus.VACUOUS,
        )

    return SourceTrustResult(
        prior_base_rate=_opinion_from_firings(firings),
        derived_from=firings,
        world_snapshot_sha=world_sha,
        kernel_version=_kernel_version(),
        status=ProvenanceStatus.CALIBRATED,
    )
