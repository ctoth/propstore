"""Shared ATMS test helper stubs."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping

from propstore.context_lifting import LiftingSystem
from propstore.core.assertions import ContextReference
from propstore.core.conditions import (
    ConditionSolver,
    CheckedCondition,
    CheckedConditionSet,
    check_condition_ir,
    checked_condition_set,
    checked_condition_set_to_json,
)
from propstore.core.conditions.registry import (
    ConceptInfo,
    KindType,
    with_standard_synthetic_bindings,
)


_NAME_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b\s*(?:==|!=|<=|>=|<|>|in\b)")


def condition_sources_from_json(value: object) -> tuple[str, ...]:
    if not value:
        return ()
    if isinstance(value, str):
        loaded = json.loads(value)
        return tuple(str(item) for item in loaded)
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value)
    return (str(value),)


def condition_registry_for_sources(sources: Iterable[str]) -> dict[str, ConceptInfo]:
    names: dict[str, KindType] = {}
    for source in sources:
        for name in _NAME_RE.findall(source):
            quoted = f"{name} == '" in source or f'{name} == "' in source
            quoted = quoted or f"{name} != '" in source or f'{name} != "' in source
            names[name] = KindType.CATEGORY if quoted else names.get(name, KindType.QUANTITY)
    return with_standard_synthetic_bindings(
        {
            name: ConceptInfo(
                id=name,
                canonical_name=name,
                kind=kind,
                category_extensible=True,
            )
            for name, kind in names.items()
        }
    )


def condition_ir_json(value: object, registry: Mapping[str, ConceptInfo]) -> str | None:
    sources = condition_sources_from_json(value)
    if not sources:
        return None
    return json.dumps(
        checked_condition_set_to_json(
            checked_condition_set(
                check_condition_ir(source, registry)
                for source in sources
            )
        ),
        sort_keys=True,
    )


def condition_sources(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, CheckedConditionSet):
        return tuple(str(source) for source in value.sources)
    if isinstance(value, CheckedCondition):
        return (value.source,)
    if isinstance(value, str):
        return condition_sources_from_json(value)
    if isinstance(value, Iterable):
        sources: list[str] = []
        for item in value:
            if isinstance(item, CheckedCondition):
                sources.append(item.source)
            else:
                sources.append(str(item))
        return tuple(sources)
    return (str(value),)


class _ExactMatchSolver:
    @property
    def registry(self):
        return condition_registry_for_sources(())

    def are_disjoint(self, left: object, right: object) -> bool:
        return set(condition_sources(left)).isdisjoint(condition_sources(right))


class _OverlapSolver:
    @property
    def registry(self):
        return condition_registry_for_sources(("x == 1", "x > 0"))

    def are_disjoint(self, left: object, right: object) -> bool:
        left_sources = condition_sources(left)
        right_sources = condition_sources(right)
        if "x == 1" in left_sources and "x > 0" in right_sources:
            return False
        if "x > 0" in left_sources and "x == 1" in right_sources:
            return False
        return set(left_sources).isdisjoint(right_sources)


def leaf_lifting_system(context_id: str) -> LiftingSystem:
    return LiftingSystem(contexts=(ContextReference(context_id),))
