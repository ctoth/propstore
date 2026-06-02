"""Shared ATMS test helper stubs."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping

from propstore.families.contexts.lifting import LiftingSystem
from propstore.core.assertions.refs import ContextReference
from propstore.core.conditions import (
    ConditionSolver,
    CheckedCondition,
    CheckedConditionSet,
    check_condition_ir,
    checked_condition_set,
    checked_condition_set_to_json,
)
from propstore.core.conditions.registry import (
    ConditionRegistry,
    ConceptInfo,
    KindType,
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


def condition_registry_for_sources(sources: Iterable[str]) -> ConditionRegistry:
    names: dict[str, KindType] = {}
    for source in sources:
        for name in _NAME_RE.findall(source):
            quoted = f"{name} == '" in source or f'{name} == "' in source
            quoted = quoted or f"{name} != '" in source or f'{name} != "' in source
            names[name] = (
                KindType.CATEGORY if quoted else names.get(name, KindType.QUANTITY)
            )
    return ConditionRegistry(
        {
            name: ConceptInfo(
                id=name,
                canonical_name=name,
                kind=kind,
                category_extensible=True,
            )
            for name, kind in names.items()
        }
    ).with_standard_synthetic_bindings()


def condition_ir_json(value: object, registry: ConditionRegistry) -> str | None:
    sources = condition_sources_from_json(value)
    if not sources:
        return None
    return json.dumps(
        checked_condition_set_to_json(
            checked_condition_set(
                check_condition_ir(source, registry) for source in sources
            )
        ),
        sort_keys=True,
    )


def condition_registry_for_rows(
    rows: Iterable[Mapping[str, object]],
) -> ConditionRegistry:
    sources: list[str] = []
    for row in rows:
        sources.extend(condition_sources_from_json(row.get("conditions_cel")))
    return condition_registry_for_sources(sources)


def row_with_condition_ir(
    row: Mapping[str, object],
    registry: ConditionRegistry,
) -> dict:
    normalized = dict(row)
    if normalized.get("conditions_cel") and not normalized.get("conditions_ir"):
        normalized["conditions_ir"] = condition_ir_json(
            normalized.get("conditions_cel"),
            registry,
        )
    return normalized


def rows_with_condition_ir(
    rows: Iterable[Mapping[str, object]],
    registry: ConditionRegistry,
) -> list[dict]:
    return [row_with_condition_ir(row, registry) for row in rows]


def condition_solver_for_rows(rows: Iterable[Mapping[str, object]]) -> ConditionSolver:
    return ConditionSolver(condition_registry_for_rows(rows))


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


def leaf_lifting_system(context_id: str) -> LiftingSystem:
    return LiftingSystem(contexts=(ContextReference(context_id),))
