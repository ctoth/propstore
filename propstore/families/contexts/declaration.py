"""Context family model construction and lifting read APIs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from collections.abc import Mapping, Sequence

from sqlalchemy import select
from quire.derived_store import DerivedStoreHandle

from propstore.context_lifting import (
    IstProposition,
    LiftedAssertion,
    LiftingDecision,
    LiftingMode,
    LiftingRule,
    LiftingSystem,
)
from propstore.core.assertions import ContextReference
from propstore.core.id_types import to_context_id
from propstore.cel_types import to_cel_exprs
from propstore.families.contexts.stages import (
    LoadedContext,
    coerce_loaded_contexts,
    loaded_contexts_to_lifting_system,
)


class Context:
    def __init__(
        self,
        id: str,
        name: str,
        description: str | None = None,
        parameters_json: str | None = None,
        perspective: str | None = None,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.parameters_json = parameters_json
        self.perspective = perspective


class ContextAssumption:
    def __init__(self, context_id: str, assumption_cel: str, seq: int) -> None:
        self.context_id = context_id
        self.assumption_cel = assumption_cel
        self.seq = seq


class ContextLiftingRule:
    def __init__(
        self,
        id: str,
        source_context_id: str,
        target_context_id: str,
        conditions_cel: str | None = None,
        mode: str = LiftingMode.BRIDGE.value,
        justification: str | None = None,
    ) -> None:
        self.id = id
        self.source_context_id = source_context_id
        self.target_context_id = target_context_id
        self.conditions_cel = conditions_cel
        self.mode = mode
        self.justification = justification


class ContextLiftingMaterialization:
    def __init__(
        self,
        rule_id: str,
        source_context_id: str,
        target_context_id: str,
        proposition_id: str,
        status: str,
        provenance_json: str,
        id: int | None = None,
        exception_id: str | None = None,
    ) -> None:
        self.id = id
        self.rule_id = rule_id
        self.source_context_id = source_context_id
        self.target_context_id = target_context_id
        self.proposition_id = proposition_id
        self.status = status
        self.exception_id = exception_id
        self.provenance_json = provenance_json

    @property
    def provenance(self) -> dict[str, object]:
        loaded = json.loads(self.provenance_json)
        if not isinstance(loaded, Mapping):
            raise TypeError("context lifting provenance must be a JSON object")
        return dict(loaded)


@dataclass(frozen=True)
class ContextWriteModels:
    contexts: tuple[Context, ...]
    assumptions: tuple[ContextAssumption, ...]
    lifting_rules: tuple[ContextLiftingRule, ...]
    lifting_materializations: tuple[ContextLiftingMaterialization, ...]


def filter_invalid_context_lifting_models(
    models: ContextWriteModels,
) -> ContextWriteModels:
    context_ids = {
        context.id
        for context in models.contexts
    }
    return ContextWriteModels(
        contexts=models.contexts,
        assumptions=models.assumptions,
        lifting_rules=tuple(
            rule
            for rule in models.lifting_rules
            if rule.source_context_id in context_ids
            and rule.target_context_id in context_ids
        ),
        lifting_materializations=models.lifting_materializations,
    )


def compile_context_models(
    contexts: Sequence[LoadedContext],
    *,
    authored_ist_assertions: Sequence[IstProposition] = (),
) -> ContextWriteModels:
    context_models: list[Context] = []
    assumption_models: list[ContextAssumption] = []
    lifting_rule_models: list[ContextLiftingRule] = []

    for context in coerce_loaded_contexts(contexts):
        record = context.record
        if record.context_id is None:
            continue
        context_id = str(record.context_id)

        context_models.append(
            Context(
                id=context_id,
                name=record.name or "",
                description=record.description,
                parameters_json=_json_or_none(dict(record.parameters)),
                perspective=record.perspective,
            )
        )

        for seq, assumption in enumerate(record.assumptions, 1):
            assumption_models.append(
                ContextAssumption(
                    context_id=context_id,
                    assumption_cel=str(assumption),
                    seq=seq,
                )
            )

        for rule in record.lifting_rules:
            lifting_rule_models.append(
                ContextLiftingRule(
                    id=rule.id,
                    source_context_id=str(rule.source.id),
                    target_context_id=str(rule.target.id),
                    conditions_cel=_json_or_none(tuple(rule.conditions)),
                    mode=rule.mode.value,
                    justification=rule.justification,
                )
            )

    materialization_models = ()
    if authored_ist_assertions:
        lifting_system = loaded_contexts_to_lifting_system(contexts)
        decisions = tuple(
            decision
            for assertion in authored_ist_assertions
            for decision in lifting_system.lift_decisions_for(assertion)
        )
        materialization_models = compile_context_lifting_materializations(
            decisions
        )

    return ContextWriteModels(
        contexts=tuple(context_models),
        assumptions=tuple(assumption_models),
        lifting_rules=tuple(lifting_rule_models),
        lifting_materializations=tuple(materialization_models),
    )


def compile_context_lifting_materializations(
    materializations: Sequence[LiftedAssertion | LiftingDecision],
) -> tuple[ContextLiftingMaterialization, ...]:
    models: list[ContextLiftingMaterialization] = []
    for materialization in materializations:
        if isinstance(materialization, LiftingDecision):
            provenance = materialization.provenance.to_payload()
            exception_id = materialization.provenance.exception_id
            models.append(
                ContextLiftingMaterialization(
                    rule_id=materialization.rule_id,
                    source_context_id=str(materialization.source_context.id),
                    target_context_id=str(materialization.target_context.id),
                    proposition_id=materialization.proposition_id,
                    status=materialization.status.value,
                    exception_id=exception_id,
                    provenance_json=json.dumps(provenance, sort_keys=True),
                )
            )
            continue
        models.append(
            ContextLiftingMaterialization(
                rule_id=materialization.rule_id,
                source_context_id=str(materialization.source_context.id),
                target_context_id=str(materialization.target_context.id),
                proposition_id=materialization.proposition_id,
                status=materialization.status.value,
                exception_id=materialization.exception_id,
                provenance_json=json.dumps(materialization.provenance, sort_keys=True),
            )
        )
    return tuple(models)


def load_lifting_system(derived_store: DerivedStoreHandle) -> LiftingSystem | None:
    from propstore.families.world_charters import world_sqlalchemy_schema

    schema = world_sqlalchemy_schema()
    context_model = schema.model("context")
    assumption_model = schema.model("context_assumption")
    lifting_rule_model = schema.model("context_lifting_rule")
    with derived_store.readonly_session(schema) as derived:
        contexts = tuple(
            derived.execute(select(context_model).order_by(context_model.id)).scalars()
        )
        assumptions = tuple(
            derived.execute(
                select(assumption_model).order_by(
                    assumption_model.context_id,
                    assumption_model.seq,
                )
            ).scalars()
        )
        lifting_rows = tuple(
            derived.execute(
                select(lifting_rule_model).order_by(lifting_rule_model.id)
            ).scalars()
        )
    return load_lifting_system_from_models(
        contexts=contexts,
        assumptions=assumptions,
        lifting_rules=lifting_rows,
    )


def load_lifting_system_from_models(
    *,
    contexts: Sequence[Context],
    assumptions: Sequence[ContextAssumption],
    lifting_rules: Sequence[ContextLiftingRule],
) -> LiftingSystem | None:
    if not contexts:
        return None

    context_ids = [str(context.id) for context in contexts]
    context_refs = tuple(
        ContextReference(id=to_context_id(context_id))
        for context_id in context_ids
    )

    assumptions_by_id: dict[str, list[str]] = {
        context_id: [] for context_id in context_ids
    }
    for row in assumptions:
        context_id = str(row.context_id)
        if context_id not in assumptions_by_id:
            continue
        assumptions_by_id[context_id].append(str(row.assumption_cel))

    rules: list[LiftingRule] = []
    for row in lifting_rules:
        conditions = _json_string_tuple(row.conditions_cel)
        rules.append(
            LiftingRule(
                id=row.id,
                source=ContextReference(id=to_context_id(row.source_context_id)),
                target=ContextReference(id=to_context_id(row.target_context_id)),
                conditions=to_cel_exprs(conditions),
                mode=LiftingMode(row.mode),
                justification=row.justification,
            )
        )

    return LiftingSystem(
        contexts=context_refs,
        lifting_rules=tuple(rules),
        context_assumptions={
            to_context_id(context_id): to_cel_exprs(assumptions)
            for context_id, assumptions in assumptions_by_id.items()
        },
    )


def _json_or_none(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, Mapping) and not value:
        return None
    if isinstance(value, Sequence) and not isinstance(value, str) and not value:
        return None
    return json.dumps(value, sort_keys=True)


def _json_string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(str(item) for item in value)
    if not isinstance(value, str):
        raise TypeError(f"expected JSON text, got {type(value).__name__}")
    decoded = json.loads(value)
    if not isinstance(decoded, Sequence) or isinstance(decoded, str):
        raise TypeError("expected JSON array")
    return tuple(str(item) for item in decoded)
