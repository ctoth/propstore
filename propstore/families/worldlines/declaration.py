"""Worldline family charters and declarative document types."""

from __future__ import annotations

from typing import Annotated, Any

import msgspec
from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import FamilyCharter
from quire.versions import VersionId

from propstore.cel_types import CelExpr


WORLDLINES_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")


# ---------------------------------------------------------------------------
# Nested Pop-B document structs (json-embedded; not independently chartered).
#
# Intra-file order is define-before-use: leaf structs first, then structs that
# embed them, then the four charter documents in the dependency chain
# RevisionResult -> RevisionState -> Result -> Definition.
# ---------------------------------------------------------------------------


class WorldlineAssumptionDocument(CharterDoc):
    assumption_id: str
    kind: str
    source: str
    cel: CelExpr


class WorldlinePolicyDocument(CharterDoc):
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


class WorldlineVariableRefDocument(CharterDoc):
    name: str | None = None
    symbol: str | None = None
    concept_id: str | None = None
    value: str | None = None


class WorldlineStepDocument(CharterDoc):
    concept: str
    source: str
    value: float | str | None = None
    claim_id: str | None = None
    strategy: str | None = None
    reason: str | None = None
    formula: str | None = None


class WorldlineDependenciesDocument(CharterDoc):
    claims: tuple[str, ...] = ()
    stances: tuple[str, ...] = ()
    contexts: tuple[str, ...] = ()


class WorldlineRevisionAtomDocument(CharterDoc):
    kind: str = "claim"
    id: str | None = None
    atom_id: str | None = None
    value: float | str | None = None


class WorldlineRevisionResultDocument(CharterDoc):
    accepted_atom_ids: tuple[str, ...] = ()
    rejected_atom_ids: tuple[str, ...] = ()
    incision_set: tuple[str, ...] = ()
    explanation: dict[str, Any] | None = None


class WorldlineInputSourceDocument(CharterDoc):
    source: str
    value: float | str | None = None
    claim_id: str | None = None
    formula: str | None = None
    reason: str | None = None
    strategy: str | None = None
    inputs_used: dict[str, WorldlineInputSourceDocument] = msgspec.field(
        default_factory=dict
    )


class WorldlineInputsDocument(CharterDoc):
    bindings: dict[str, Any] = msgspec.field(default_factory=dict)
    context_id: str | None = None
    effective_assumptions: tuple[CelExpr, ...] = ()
    assumptions: tuple[WorldlineAssumptionDocument, ...] = ()
    overrides: dict[str, float | str] = msgspec.field(default_factory=dict)


class WorldlineTargetValueDocument(CharterDoc):
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
    inputs_used: dict[str, WorldlineInputSourceDocument] = msgspec.field(
        default_factory=dict
    )


class WorldlineRevisionQueryDocument(CharterDoc):
    operation: str
    atom: WorldlineRevisionAtomDocument | None = None
    target: str | None = None
    conflicts: dict[str, tuple[str, ...]] = msgspec.field(default_factory=dict)
    operator: str | None = None
    merge_operator: str | None = None
    profile_atom_ids: tuple[tuple[str, ...], ...] = ()
    integrity_constraint: dict[str, Any] | None = None
    merge_parent_commits: tuple[str, ...] = ()
    max_alphabet_size: int | None = None


# ---------------------------------------------------------------------------
# Charter documents (the @charter-decorated classes ARE the documents).
# ---------------------------------------------------------------------------


@charter(
    key="worldline_revision_state",
    name="worldline_revision_state",
    contract_version=WORLDLINES_FAMILY_CONTRACT_VERSION,
    placement=".derived/worldline_revision_state",
    identity_field="operation",
    semantic="propstore.world",
    artifact_family_name="propstore-world-worldline_revision_state",
    model_name="WorldlineRevisionState",
)
class WorldlineRevisionStateDocument(CharterDoc):
    operation: Annotated[str, charter_field(primary_key=True)]
    input_atom_id: str | None = None
    target_atom_ids: Annotated[
        tuple[str, ...], charter_field(json=True, default_sql="'[]'")
    ] = ()
    result: Annotated[
        WorldlineRevisionResultDocument | None, charter_field(json=True)
    ] = None
    state: Annotated[dict[str, Any] | None, charter_field(json=True)] = None
    status: str | None = None
    error: str | None = None


@charter(
    key="worldline_journal",
    name="worldline_journal",
    contract_version=WORLDLINES_FAMILY_CONTRACT_VERSION,
    placement=".derived/worldline_journal",
    identity_field="schema_version",
    semantic="propstore.world",
    artifact_family_name="propstore-world-worldline_journal",
    model_name="WorldlineJournal",
)
class WorldlineJournalDocument(CharterDoc):
    schema_version: Annotated[str, charter_field(primary_key=True)]
    entries: Annotated[
        tuple[dict[str, Any], ...], charter_field(json=True, default_sql="'[]'")
    ] = ()


@charter(
    key="worldline_result",
    name="worldline_result",
    contract_version=WORLDLINES_FAMILY_CONTRACT_VERSION,
    placement=".derived/worldline_result",
    identity_field="content_hash",
    semantic="propstore.world",
    artifact_family_name="propstore-world-worldline_result",
    model_name="WorldlineResult",
)
class WorldlineResultDocument(CharterDoc):
    computed: str
    content_hash: Annotated[str, charter_field(primary_key=True)]
    values: Annotated[
        dict[str, WorldlineTargetValueDocument],
        charter_field(column_name="target_values", json=True),
    ]
    dependencies: Annotated[
        WorldlineDependenciesDocument, charter_field(json=True)
    ]
    steps: Annotated[
        tuple[WorldlineStepDocument, ...],
        charter_field(json=True, default_sql="'[]'"),
    ] = ()
    sensitivity: Annotated[dict[str, Any] | None, charter_field(json=True)] = None
    argumentation: Annotated[dict[str, Any] | None, charter_field(json=True)] = None
    revision: Annotated[
        WorldlineRevisionStateDocument | None, charter_field(json=True)
    ] = None


@charter(
    key="worldline_definition",
    name="worldline_definition",
    contract_version=WORLDLINES_FAMILY_CONTRACT_VERSION,
    placement=".derived/worldline_definition",
    identity_field="id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-worldline_definition",
    model_name="WorldlineDefinition",
)
class WorldlineDefinitionDocument(CharterDoc):
    id: Annotated[str, charter_field(primary_key=True)]
    targets: Annotated[tuple[str, ...], charter_field(json=True)]
    name: Annotated[str, charter_field(default_sql="''")] = ""
    created: Annotated[str, charter_field(default_sql="''")] = ""
    inputs: Annotated[WorldlineInputsDocument | None, charter_field(json=True)] = None
    policy: Annotated[WorldlinePolicyDocument | None, charter_field(json=True)] = None
    revision: Annotated[
        WorldlineRevisionQueryDocument | None, charter_field(json=True)
    ] = None
    journal: Annotated[WorldlineJournalDocument | None, charter_field(json=True)] = None
    results: Annotated[WorldlineResultDocument | None, charter_field(json=True)] = None


WORLDLINE_REVISION_STATE_CHARTER: FamilyCharter = (
    WorldlineRevisionStateDocument.__charter__
)
WORLDLINE_JOURNAL_CHARTER: FamilyCharter = WorldlineJournalDocument.__charter__
WORLDLINE_RESULT_CHARTER: FamilyCharter = WorldlineResultDocument.__charter__
WORLDLINE_DEFINITION_CHARTER: FamilyCharter = WorldlineDefinitionDocument.__charter__


WORLDLINE_CHARTERS: tuple[FamilyCharter, ...] = (
    WORLDLINE_DEFINITION_CHARTER,
    WORLDLINE_RESULT_CHARTER,
    WORLDLINE_REVISION_STATE_CHARTER,
    WORLDLINE_JOURNAL_CHARTER,
)
