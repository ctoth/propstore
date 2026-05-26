"""Context family model construction and lifting read APIs."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

import msgspec
from sqlalchemy import select
from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, CharterIndex, FamilyCharter, FamilyModel
from quire.derived_store import DerivedStoreHandle
from quire.families import FamilyDefinition
from quire.references import ReferenceKey
from quire.versions import VersionId

from .lifting import (
    IstProposition,
    LiftedAssertion,
    LiftingDecision,
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


class LiftingRuleDocumentProtocol(Protocol):
    id: str
    source: str
    target: str
    conditions: tuple[CelExpr, ...] | None
    mode: str
    justification: str | None


class ContextDocumentProtocol(Protocol):
    id: str
    name: str
    description: str | None
    assumptions: tuple[CelExpr, ...] | None
    parameters: dict[str, str] | None
    perspective: str | None
    lifting_rules: tuple[LiftingRuleDocumentProtocol, ...] | None


class ContextReferenceDocument(msgspec.Struct, forbid_unknown_fields=True):
    id: str

    def to_payload(self) -> dict[str, object]:
        return {"id": self.id}


CONTEXT_LIFTING_RULE_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="context_lifting_rule",
        name="context_lifting_rule",
        contract_version=_CONTEXT_WORLD_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-context_lifting_rule",
            contract_version=_CONTEXT_WORLD_CONTRACT_VERSION,
            doc_type=ContextLiftingRule,
            placement=FlatYamlPlacement(".derived/context_lifting_rule", str),
        ),
        identity_field="id",
        reference_keys=(ReferenceKey.field("name"),),
    ),
    model=ContextLiftingRule,
    fields=(
        CharterField("id", str, primary_key=True, nullable=False),
        CharterField(
            "source_context_id",
            str,
            nullable=False,
            document_name="source",
        ),
        CharterField(
            "target_context_id",
            str,
            nullable=False,
            document_name="target",
        ),
        CharterField(
            "conditions_cel",
            tuple[CelExpr, ...],
            parse_boundary="json",
            nullable=True,
            document_name="conditions",
        ),
        CharterField(
            "mode",
            str,
            nullable=False,
            default=LiftingMode.BRIDGE.value,
        ),
        CharterField("justification", str, nullable=True),
    ),
    indexes=(
        CharterIndex("idx_context_lifting_rule_source_context_id", ("source_context_id",)),
        CharterIndex("idx_context_lifting_rule_target_context_id", ("target_context_id",)),
    ),
    semantic_metadata={"semantic": "propstore.world"},
)

LiftingRuleDocument: Any = CONTEXT_LIFTING_RULE_CHARTER.generated_document()


CONTEXT_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="context",
        name="context",
        contract_version=_CONTEXT_WORLD_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-context",
            contract_version=_CONTEXT_WORLD_CONTRACT_VERSION,
            doc_type=Context,
            placement=FlatYamlPlacement(".derived/context", str),
        ),
        identity_field="id",
    ),
    model=Context,
    fields=(
        CharterField("id", str, primary_key=True, nullable=False),
        CharterField("name", str, nullable=False),
        CharterField("description", str, nullable=True),
        CharterField(
            "assumptions",
            tuple[CelExpr, ...],
            parse_boundary="json",
            nullable=True,
        ),
        CharterField(
            "parameters_json",
            dict[str, str],
            parse_boundary="json",
            document_name="parameters",
            nullable=True,
        ),
        CharterField("perspective", str, nullable=True),
        CharterField(
            "lifting_rules",
            tuple[LiftingRuleDocument, ...],
            parse_boundary="json",
            nullable=True,
        ),
    ),
    semantic_metadata={"semantic": "propstore.world"},
)

ContextDocument: Any = CONTEXT_CHARTER.generated_document()

CONTEXT_ASSUMPTION_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="context_assumption",
        name="context_assumption",
        contract_version=_CONTEXT_WORLD_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-context_assumption",
            contract_version=_CONTEXT_WORLD_CONTRACT_VERSION,
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
)

ContextAssumptionDocument = CONTEXT_ASSUMPTION_CHARTER.generated_document()

CONTEXT_LIFTING_MATERIALIZATION_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="context_lifting_materialization",
        name="context_lifting_materialization",
        contract_version=_CONTEXT_WORLD_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-context_lifting_materialization",
            contract_version=_CONTEXT_WORLD_CONTRACT_VERSION,
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
