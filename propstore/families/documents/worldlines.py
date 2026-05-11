from __future__ import annotations

from typing import Any

import msgspec

from quire.documents import DocumentStruct
from propstore.cel_types import CelExpr


class WorldlineAssumptionDocument(DocumentStruct):
    assumption_id: str
    kind: str
    source: str
    cel: CelExpr


class WorldlineInputsDocument(DocumentStruct):
    bindings: dict[str, Any] = msgspec.field(default_factory=dict)
    context_id: str | None = None
    effective_assumptions: tuple[CelExpr, ...] = ()
    assumptions: tuple[WorldlineAssumptionDocument, ...] = ()
    overrides: dict[str, float | str] = msgspec.field(default_factory=dict)


class WorldlinePolicyDocument(DocumentStruct):
    reasoning_backend: str | None = None
    strategy: str | None = None
    semantics: str | None = None
    comparison: str | None = None
    link: str | None = None
    decision_criterion: str | None = None
    pessimism_index: float | None = None
    show_uncertainty_interval: bool | None = None
    praf_strategy: str | None = None
    praf_mc_epsilon: float | None = None
    praf_mc_confidence: float | None = None
    praf_treewidth_cutoff: int | None = None
    praf_mc_seed: int | None = None
    merge_operator: str | None = None
    branch_filter: tuple[str, ...] | None = None
    branch_weights: dict[str, float] | None = None
    integrity_constraints: tuple[dict[str, Any], ...] = ()
    future_queryables: tuple[str, ...] = ()
    future_limit: int | None = None
    overrides: dict[str, str] = msgspec.field(default_factory=dict)
    concept_strategies: dict[str, str] = msgspec.field(default_factory=dict)


class WorldlineVariableRefDocument(DocumentStruct):
    name: str | None = None
    symbol: str | None = None
    concept_id: str | None = None
    value: str | None = None


class WorldlineInputSourceDocument(DocumentStruct):
    source: str
    value: float | str | None = None
    claim_id: str | None = None
    formula: str | None = None
    reason: str | None = None
    strategy: str | None = None
    inputs_used: dict[str, WorldlineInputSourceDocument] = msgspec.field(default_factory=dict)


class WorldlineTargetValueDocument(DocumentStruct):
    status: str
    value: float | str | None = None
    source: str | None = None
    reason: str | None = None
    claim_id: str | None = None
    winning_claim_id: str | None = None
    claim_type: str | None = None
    statement: str | None = None
    expression: str | None = None
    body: str | None = None
    name: str | None = None
    canonical_ast: str | None = None
    variables: tuple[WorldlineVariableRefDocument, ...] | dict[str, str] = ()
    formula: str | None = None
    strategy: str | None = None
    inputs_used: dict[str, WorldlineInputSourceDocument] = msgspec.field(default_factory=dict)


class WorldlineStepDocument(DocumentStruct):
    concept: str
    source: str
    value: float | str | None = None
    claim_id: str | None = None
    strategy: str | None = None
    reason: str | None = None
    formula: str | None = None


class WorldlineDependenciesDocument(DocumentStruct):
    claims: tuple[str, ...] = ()
    stances: tuple[str, ...] = ()
    contexts: tuple[str, ...] = ()


class WorldlineRevisionAtomDocument(DocumentStruct):
    kind: str = "claim"
    id: str | None = None
    atom_id: str | None = None
    value: float | str | None = None


class WorldlineRevisionQueryDocument(DocumentStruct):
    operation: str
    atom: WorldlineRevisionAtomDocument | None = None
    target: str | None = None
    conflicts: dict[str, tuple[str, ...]] = msgspec.field(default_factory=dict)
    operator: str | None = None
    profile_atom_ids: tuple[tuple[str, ...], ...] = ()
    integrity_constraint: dict[str, Any] | None = None
    merge_parent_commits: tuple[str, ...] = ()
    merge_operator: str | None = None
    max_alphabet_size: int | None = None


class WorldlineRevisionResultDocument(DocumentStruct):
    accepted_atom_ids: tuple[str, ...] = ()
    rejected_atom_ids: tuple[str, ...] = ()
    incision_set: tuple[str, ...] = ()
    explanation: dict[str, Any] | None = None


class WorldlineRevisionStateDocument(DocumentStruct):
    operation: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = ()
    result: WorldlineRevisionResultDocument | None = None
    state: dict[str, Any] | None = None
    status: str | None = None
    error: str | None = None


class WorldlineJournalDocument(DocumentStruct):
    schema_version: str
    entries: tuple[dict[str, Any], ...] = ()


class WorldlineResultDocument(DocumentStruct):
    computed: str
    content_hash: str
    values: dict[str, WorldlineTargetValueDocument]
    dependencies: WorldlineDependenciesDocument
    steps: tuple[WorldlineStepDocument, ...] = ()
    sensitivity: dict[str, Any] | None = None
    argumentation: dict[str, Any] | None = None
    revision: WorldlineRevisionStateDocument | None = None


class WorldlineDefinitionDocument(DocumentStruct):
    id: str
    targets: tuple[str, ...]
    name: str = ""
    created: str = ""
    inputs: WorldlineInputsDocument | None = None
    policy: WorldlinePolicyDocument | None = None
    revision: WorldlineRevisionQueryDocument | None = None
    journal: WorldlineJournalDocument | None = None
    results: WorldlineResultDocument | None = None
