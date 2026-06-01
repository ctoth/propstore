"""Context family model construction and lifting read APIs."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Annotated

from sqlalchemy import select
from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import CharterIndex, FamilyCharter, FamilyModel
from quire.derived_store import DerivedStoreHandle
from quire.references import ReferenceKey
from quire.versions import VersionId

from .lifting import (
    IstProposition,
    LiftingMode,
    LiftingRule,
    LiftingSystem,
)
from ...core.assertions.refs import ContextReference
from ...core.id_types import ContextId
from ...cel_types import CelExpr, to_cel_exprs
from .stages import (
    LoadedContext,
    loaded_contexts_to_lifting_system,
)


_CONTEXT_WORLD_CONTRACT_VERSION = VersionId("2026.05.25", allow_placeholder=False)


class ContextLiftingMaterializationMixin:
    """Row behaviour for the context-lifting-materialization model.

    ``@charter(model_mixin=...)`` makes the generated SQLAlchemy model inherit
    this, so the materialization row keeps its ``provenance`` accessor that
    decodes the stored ``provenance_json`` column.
    """

    provenance_json: str

    @property
    def provenance(self) -> dict[str, object]:
        loaded = json.loads(self.provenance_json)
        if not isinstance(loaded, Mapping):
            raise TypeError("context lifting provenance must be a JSON object")
        return dict(loaded)


if TYPE_CHECKING:
    # ``@charter`` generates these SQLAlchemy-mappable models at runtime (via
    # ``model_name=``) and binds them into this module's namespace; the static
    # stubs let this module and external importers type-check model construction
    # and attribute access while the runtime classes replace them.
    class Context(FamilyModel): ...

    class ContextAssumption(FamilyModel): ...

    class ContextLiftingRule(FamilyModel): ...

    class ContextLiftingMaterialization(FamilyModel):
        @property
        def provenance(self) -> dict[str, object]: ...


class ContextReferenceDocument(CharterDoc):
    id: str


@charter(
    key="context_lifting_rule",
    name="context_lifting_rule",
    contract_version=_CONTEXT_WORLD_CONTRACT_VERSION,
    placement=".derived/context_lifting_rule",
    identity_field="id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-context_lifting_rule",
    model_name="ContextLiftingRule",
    reference_keys=(ReferenceKey.field("name"),),
    indexes=(
        CharterIndex(
            "idx_context_lifting_rule_source_context_id", ("source_context_id",)
        ),
        CharterIndex(
            "idx_context_lifting_rule_target_context_id", ("target_context_id",)
        ),
    ),
)
class Context_lifting_ruleDocument(CharterDoc):
    id: Annotated[str, charter_field(primary_key=True)]
    source: Annotated[str, charter_field(column_name="source_context_id")]
    target: Annotated[str, charter_field(column_name="target_context_id")]
    conditions: Annotated[
        tuple[CelExpr, ...] | None,
        charter_field(column_name="conditions_cel", json=True, nullable=True),
    ] = None
    mode: str = LiftingMode.BRIDGE.value
    justification: str | None = None


LiftingRuleDocument = Context_lifting_ruleDocument


@charter(
    key="context",
    name="context",
    contract_version=_CONTEXT_WORLD_CONTRACT_VERSION,
    placement=".derived/context",
    identity_field="id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-context",
    model_name="Context",
)
class ContextDocument(CharterDoc):
    id: Annotated[str, charter_field(primary_key=True)]
    name: str
    description: str | None = None
    assumptions: Annotated[tuple[CelExpr, ...] | None, charter_field(json=True)] = None
    parameters: Annotated[
        dict[str, str] | None, charter_field(column_name="parameters_json", json=True)
    ] = None
    perspective: str | None = None
    lifting_rules: Annotated[
        tuple[LiftingRuleDocument, ...] | None, charter_field(json=True)
    ] = None


@charter(
    key="context_assumption",
    name="context_assumption",
    contract_version=_CONTEXT_WORLD_CONTRACT_VERSION,
    placement=".derived/context_assumption",
    identity_field="context_id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-context_assumption",
    model_name="ContextAssumption",
    indexes=(CharterIndex("idx_context_assumption_context_id", ("context_id",)),),
)
class Context_assumptionDocument(CharterDoc):
    context_id: str
    assumption_cel: str
    seq: int


ContextAssumptionDocument = Context_assumptionDocument


@charter(
    key="context_lifting_materialization",
    name="context_lifting_materialization",
    contract_version=_CONTEXT_WORLD_CONTRACT_VERSION,
    placement=".derived/context_lifting_materialization",
    identity_field="id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-context_lifting_materialization",
    model_name="ContextLiftingMaterialization",
    model_mixin=ContextLiftingMaterializationMixin,
    indexes=(
        CharterIndex(
            "idx_context_lifting_materialization_source_context_id",
            ("source_context_id",),
        ),
        CharterIndex(
            "idx_context_lifting_materialization_target_context_id",
            ("target_context_id",),
        ),
    ),
)
class Context_lifting_materializationDocument(CharterDoc):
    id: Annotated[int, charter_field(primary_key=True)]
    rule_id: str
    source_context_id: str
    target_context_id: str
    proposition_id: str
    status: str
    exception_id: Annotated[str, charter_field(nullable=True)]
    provenance_json: str


CONTEXT_LIFTING_RULE_CHARTER: FamilyCharter = Context_lifting_ruleDocument.__charter__
CONTEXT_CHARTER: FamilyCharter = ContextDocument.__charter__
CONTEXT_ASSUMPTION_CHARTER: FamilyCharter = Context_assumptionDocument.__charter__
CONTEXT_LIFTING_MATERIALIZATION_CHARTER: FamilyCharter = (
    Context_lifting_materializationDocument.__charter__
)


CONTEXT_CHARTERS: tuple[FamilyCharter, ...] = (
    CONTEXT_CHARTER,
    CONTEXT_ASSUMPTION_CHARTER,
    CONTEXT_LIFTING_RULE_CHARTER,
    CONTEXT_LIFTING_MATERIALIZATION_CHARTER,
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
    context_ids = {context.id for context in contexts}
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
                assumptions=tuple(record.assumptions),
                parameters_json=dict(record.parameters) if record.parameters else None,
                perspective=record.perspective,
                lifting_rules=tuple(
                    LiftingRuleDocument(
                        id=rule.id,
                        source=str(rule.source.id),
                        target=str(rule.target.id),
                        conditions=tuple(rule.conditions),
                        mode=rule.mode.value,
                        justification=rule.justification,
                    )
                    for rule in record.lifting_rules
                ),
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
                    conditions_cel=tuple(rule.conditions),
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
        materialization_models = compile_context_lifting_materializations(decisions)

    return (
        tuple(context_models),
        tuple(assumption_models),
        tuple(lifting_rule_models),
        tuple(materialization_models),
    )


def load_lifting_system(derived_store: DerivedStoreHandle) -> LiftingSystem | None:
    from propstore.families.registry import world_schema

    schema = world_schema()
    context_model = schema.model(CONTEXT_CHARTER.family.name)
    assumption_model = schema.model(CONTEXT_ASSUMPTION_CHARTER.family.name)
    lifting_rule_model = schema.model(CONTEXT_LIFTING_RULE_CHARTER.family.name)
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
        ContextReference(id=ContextId(context_id)) for context_id in context_ids
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
        conditions = _context_lifting_conditions(row.conditions_cel)
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


def _context_lifting_conditions(raw: object) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        decoded = json.loads(raw)
    else:
        decoded = raw
    if not isinstance(decoded, Sequence) or isinstance(decoded, str):
        raise TypeError("expected context lifting condition JSON array")
    return tuple(str(item) for item in decoded)
