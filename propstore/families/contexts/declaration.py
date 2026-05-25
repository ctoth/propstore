"""Context family model construction and lifting read APIs."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from sqlalchemy import select
from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, CharterIndex, FamilyCharter, FamilyModel
from quire.derived_store import DerivedStoreHandle
from quire.families import FamilyDefinition

from propstore.context_lifting import (
    IstProposition,
    LiftedAssertion,
    LiftingDecision,
    LiftingMode,
    LiftingRule,
    LiftingSystem,
)
from propstore.core.assertions.refs import ContextReference
from propstore.core.id_types import ContextId
from propstore.cel_types import to_cel_exprs
from propstore.families.contexts.stages import (
    LoadedContext,
    loaded_contexts_to_lifting_system,
)
from propstore.families.meta.declaration import _WORLD_CONTRACT_VERSION


class Context(FamilyModel):
    pass


class ContextAssumption(FamilyModel):
    pass


class ContextLiftingRule(FamilyModel):
    pass


class ContextLiftingMaterialization(FamilyModel):
    @property
    def provenance(self) -> dict[str, object]:
        loaded = json.loads(self.provenance_json)
        if not isinstance(loaded, Mapping):
            raise TypeError("context lifting provenance must be a JSON object")
        return dict(loaded)


CONTEXT_CHARTERS: tuple[FamilyCharter, ...] = (
        FamilyCharter(
            family=FamilyDefinition(
                key="context",
                name="context",
                contract_version=_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-context",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    doc_type=Context,
                    placement=FlatYamlPlacement(".derived/context", str),
                ),
                identity_field="id",
            ),
            model=Context,
            fields=(
                CharterField("id", str, primary_key=True, nullable=False),
                CharterField("name", str, nullable=False),
                CharterField("description", str),
                CharterField("parameters_json", str),
                CharterField("perspective", str),
            ),
            semantic_metadata={"semantic": "propstore.world"},
        ),
        FamilyCharter(
            family=FamilyDefinition(
                key="context_assumption",
                name="context_assumption",
                contract_version=_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-context_assumption",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    doc_type=ContextAssumption,
                    placement=FlatYamlPlacement(".derived/context_assumption", str),
                ),
                identity_field="context_id",
            ),
            model=ContextAssumption,
            fields=(
                CharterField("context_id", str, nullable=False),
                CharterField("assumption_cel", str, nullable=False),
                CharterField("seq", int, nullable=False),
            ),
            indexes=(CharterIndex("idx_context_assumption_context_id", ("context_id",)),),
            semantic_metadata={"semantic": "propstore.world"},
        ),
        FamilyCharter(
            family=FamilyDefinition(
                key="context_lifting_rule",
                name="context_lifting_rule",
                contract_version=_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-context_lifting_rule",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    doc_type=ContextLiftingRule,
                    placement=FlatYamlPlacement(".derived/context_lifting_rule", str),
                ),
                identity_field="id",
            ),
            model=ContextLiftingRule,
            fields=(
                CharterField("id", str, primary_key=True, nullable=False),
                CharterField("source_context_id", str, nullable=False),
                CharterField("target_context_id", str, nullable=False),
                CharterField("conditions_cel", str),
                CharterField("mode", str, nullable=False),
                CharterField("justification", str),
            ),
            indexes=(
                CharterIndex("idx_context_lifting_rule_source_context_id", ("source_context_id",)),
                CharterIndex("idx_context_lifting_rule_target_context_id", ("target_context_id",)),
            ),
            semantic_metadata={"semantic": "propstore.world"},
        ),
        FamilyCharter(
            family=FamilyDefinition(
                key="context_lifting_materialization",
                name="context_lifting_materialization",
                contract_version=_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-context_lifting_materialization",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    doc_type=ContextLiftingMaterialization,
                    placement=FlatYamlPlacement(".derived/context_lifting_materialization", str),
                ),
                identity_field="id",
            ),
            model=ContextLiftingMaterialization,
            fields=(
                CharterField("id", int, primary_key=True, nullable=False),
                CharterField("rule_id", str, nullable=False),
                CharterField("source_context_id", str, nullable=False),
                CharterField("target_context_id", str, nullable=False),
                CharterField("proposition_id", str, nullable=False),
                CharterField("status", str, nullable=False),
                CharterField("exception_id", str),
                CharterField("provenance_json", str, nullable=False),
            ),
            indexes=(
                CharterIndex("idx_context_lifting_materialization_source_context_id", ("source_context_id",)),
                CharterIndex("idx_context_lifting_materialization_target_context_id", ("target_context_id",)),
            ),
            semantic_metadata={"semantic": "propstore.world"},
        ),
    )


ContextModelBatches = tuple[
    tuple[Context, ...],
    tuple[ContextAssumption, ...],
    tuple[ContextLiftingRule, ...],
    tuple[ContextLiftingMaterialization, ...],
]


def filter_invalid_context_lifting_models(
    models: ContextModelBatches,
) -> ContextModelBatches:
    contexts, assumptions, lifting_rules, lifting_materializations = models
    context_ids = {
        context.id
        for context in contexts
    }
    return (
        contexts,
        assumptions,
        tuple(
            rule
            for rule in lifting_rules
            if rule.source_context_id in context_ids
            and rule.target_context_id in context_ids
        ),
        lifting_materializations,
    )


def compile_context_models(
    contexts: Sequence[LoadedContext],
    *,
    authored_ist_assertions: Sequence[IstProposition] = (),
) -> ContextModelBatches:
    context_models: list[Context] = []
    assumption_models: list[ContextAssumption] = []
    lifting_rule_models: list[ContextLiftingRule] = []

    for context in contexts:
        record = context.record
        if record.context_id is None:
            continue
        context_id = str(record.context_id)

        context_models.append(
            Context(
                id=context_id,
                name=record.name or "",
                description=record.description,
                parameters_json=(
                    json.dumps(dict(record.parameters), sort_keys=True)
                    if record.parameters
                    else None
                ),
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
                    conditions_cel=(
                        json.dumps(tuple(rule.conditions), sort_keys=True)
                        if rule.conditions
                        else None
                    ),
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

    return (
        tuple(context_models),
        tuple(assumption_models),
        tuple(lifting_rule_models),
        tuple(materialization_models),
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
    from propstore.families.registry import world_schema

    schema = world_schema()
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
        ContextReference(id=ContextId(context_id))
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
        if row.conditions_cel is None:
            conditions = ()
        else:
            decoded = json.loads(row.conditions_cel)
            if not isinstance(decoded, Sequence) or isinstance(decoded, str):
                raise TypeError("expected context lifting condition JSON array")
            conditions = tuple(str(item) for item in decoded)
        rules.append(
            LiftingRule(
                id=row.id,
                source=ContextReference(id=ContextId(row.source_context_id)),
                target=ContextReference(id=ContextId(row.target_context_id)),
                conditions=to_cel_exprs(conditions),
                mode=LiftingMode(row.mode),
                justification=row.justification,
            )
        )

    return LiftingSystem(
        contexts=context_refs,
        lifting_rules=tuple(rules),
        context_assumptions={
            ContextId(context_id): to_cel_exprs(assumptions)
            for context_id, assumptions in assumptions_by_id.items()
        },
    )
