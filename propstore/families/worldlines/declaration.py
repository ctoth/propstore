"""Worldline family charters and generated document types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import msgspec
from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, FamilyCharter, FamilyModel
from quire.families import FamilyDefinition
from quire.versions import VersionId

from propstore.cel_types import CelExpr


WORLDLINES_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")


class WorldlineAssumptionDocument(msgspec.Struct, forbid_unknown_fields=True):
    assumption_id: str
    kind: str
    source: str
    cel: CelExpr


class WorldlineInputsDocument(msgspec.Struct, forbid_unknown_fields=True):
    bindings: dict[str, Any] = msgspec.field(default_factory=dict)
    context_id: str | None = None
    effective_assumptions: tuple[CelExpr, ...] = ()
    assumptions: tuple[WorldlineAssumptionDocument, ...] = ()
    overrides: dict[str, float | str] = msgspec.field(default_factory=dict)


class WorldlinePolicyDocument(msgspec.Struct, forbid_unknown_fields=True):
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


class WorldlineVariableRefDocument(msgspec.Struct, forbid_unknown_fields=True):
    name: str | None = None
    symbol: str | None = None
    concept_id: str | None = None
    value: str | None = None


class WorldlineInputSourceDocument(msgspec.Struct, forbid_unknown_fields=True):
    source: str
    value: float | str | None = None
    claim_id: str | None = None
    formula: str | None = None
    reason: str | None = None
    strategy: str | None = None
    inputs_used: dict[str, WorldlineInputSourceDocument] = msgspec.field(
        default_factory=dict
    )


class WorldlineTargetValueDocument(msgspec.Struct, forbid_unknown_fields=True):
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


class WorldlineStepDocument(msgspec.Struct, forbid_unknown_fields=True):
    concept: str
    source: str
    value: float | str | None = None
    claim_id: str | None = None
    strategy: str | None = None
    reason: str | None = None
    formula: str | None = None


class WorldlineDependenciesDocument(msgspec.Struct, forbid_unknown_fields=True):
    claims: tuple[str, ...] = ()
    stances: tuple[str, ...] = ()
    contexts: tuple[str, ...] = ()


class WorldlineRevisionAtomDocument(msgspec.Struct, forbid_unknown_fields=True):
    kind: str = "claim"
    id: str | None = None
    atom_id: str | None = None
    value: float | str | None = None


class WorldlineRevisionQueryDocument(msgspec.Struct, forbid_unknown_fields=True):
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


class WorldlineRevisionResultDocument(msgspec.Struct, forbid_unknown_fields=True):
    accepted_atom_ids: tuple[str, ...] = ()
    rejected_atom_ids: tuple[str, ...] = ()
    incision_set: tuple[str, ...] = ()
    explanation: dict[str, Any] | None = None


class WorldlineDefinition(FamilyModel):
    pass


class WorldlineResult(FamilyModel):
    pass


class WorldlineRevisionState(FamilyModel):
    pass


class WorldlineJournal(FamilyModel):
    pass


WORLDLINE_REVISION_STATE_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="worldline_revision_state",
        name="worldline_revision_state",
        contract_version=WORLDLINES_FAMILY_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-worldline_revision_state",
            contract_version=WORLDLINES_FAMILY_CONTRACT_VERSION,
            doc_type=WorldlineRevisionState,
            placement=FlatYamlPlacement(".derived/worldline_revision_state", str),
        ),
        identity_field="operation",
    ),
    model=WorldlineRevisionState,
    fields=(
        CharterField("operation", str, primary_key=True, nullable=False),
        CharterField("input_atom_id", str, nullable=True),
        CharterField(
            "target_atom_ids",
            tuple[str, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
        ),
        CharterField(
            "result",
            WorldlineRevisionResultDocument,
            parse_boundary="json",
            nullable=True,
        ),
        CharterField("state", dict[str, Any], parse_boundary="json", nullable=True),
        CharterField("status", str, nullable=True),
        CharterField("error", str, nullable=True),
    ),
    semantic_metadata={"semantic": "propstore.world"},
)

if TYPE_CHECKING:

    class WorldlineRevisionStateDocument(msgspec.Struct, forbid_unknown_fields=True):
        operation: str
        input_atom_id: str | None = None
        target_atom_ids: tuple[str, ...] = ()
        result: WorldlineRevisionResultDocument | None = None
        state: dict[str, Any] | None = None
        status: str | None = None
        error: str | None = None

else:
    WorldlineRevisionStateDocument: Any = (
        WORLDLINE_REVISION_STATE_CHARTER.generated_document()
    )
    WorldlineRevisionStateDocument.__name__ = "WorldlineRevisionStateDocument"
    WorldlineRevisionStateDocument.__qualname__ = "WorldlineRevisionStateDocument"
    WorldlineRevisionStateDocument.__module__ = __name__


WORLDLINE_JOURNAL_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="worldline_journal",
        name="worldline_journal",
        contract_version=WORLDLINES_FAMILY_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-worldline_journal",
            contract_version=WORLDLINES_FAMILY_CONTRACT_VERSION,
            doc_type=WorldlineJournal,
            placement=FlatYamlPlacement(".derived/worldline_journal", str),
        ),
        identity_field="schema_version",
    ),
    model=WorldlineJournal,
    fields=(
        CharterField("schema_version", str, primary_key=True, nullable=False),
        CharterField(
            "entries",
            tuple[dict[str, Any], ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
        ),
    ),
    semantic_metadata={"semantic": "propstore.world"},
)

if TYPE_CHECKING:

    class WorldlineJournalDocument(msgspec.Struct, forbid_unknown_fields=True):
        schema_version: str
        entries: tuple[dict[str, Any], ...] = ()

else:
    WorldlineJournalDocument: Any = WORLDLINE_JOURNAL_CHARTER.generated_document()
    WorldlineJournalDocument.__name__ = "WorldlineJournalDocument"
    WorldlineJournalDocument.__qualname__ = "WorldlineJournalDocument"
    WorldlineJournalDocument.__module__ = __name__


WORLDLINE_RESULT_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="worldline_result",
        name="worldline_result",
        contract_version=WORLDLINES_FAMILY_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-worldline_result",
            contract_version=WORLDLINES_FAMILY_CONTRACT_VERSION,
            doc_type=WorldlineResult,
            placement=FlatYamlPlacement(".derived/worldline_result", str),
        ),
        identity_field="content_hash",
    ),
    model=WorldlineResult,
    fields=(
        CharterField("computed", str, nullable=False),
        CharterField("content_hash", str, primary_key=True, nullable=False),
        CharterField(
            "target_values",
            dict[str, WorldlineTargetValueDocument],
            document_name="values",
            parse_boundary="json",
            nullable=False,
        ),
        CharterField(
            "dependencies",
            WorldlineDependenciesDocument,
            parse_boundary="json",
            nullable=False,
        ),
        CharterField(
            "steps",
            tuple[WorldlineStepDocument, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
        ),
        CharterField("sensitivity", dict[str, Any], parse_boundary="json", nullable=True),
        CharterField("argumentation", dict[str, Any], parse_boundary="json", nullable=True),
        CharterField(
            "revision",
            WorldlineRevisionStateDocument,
            parse_boundary="json",
            nullable=True,
        ),
    ),
    semantic_metadata={"semantic": "propstore.world"},
)

if TYPE_CHECKING:

    class WorldlineResultDocument(msgspec.Struct, forbid_unknown_fields=True):
        computed: str
        content_hash: str
        values: dict[str, WorldlineTargetValueDocument]
        dependencies: WorldlineDependenciesDocument
        steps: tuple[WorldlineStepDocument, ...] = ()
        sensitivity: dict[str, Any] | None = None
        argumentation: dict[str, Any] | None = None
        revision: WorldlineRevisionStateDocument | None = None

else:
    WorldlineResultDocument: Any = WORLDLINE_RESULT_CHARTER.generated_document()
    WorldlineResultDocument.__name__ = "WorldlineResultDocument"
    WorldlineResultDocument.__qualname__ = "WorldlineResultDocument"
    WorldlineResultDocument.__module__ = __name__


WORLDLINE_DEFINITION_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="worldline_definition",
        name="worldline_definition",
        contract_version=WORLDLINES_FAMILY_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-worldline_definition",
            contract_version=WORLDLINES_FAMILY_CONTRACT_VERSION,
            doc_type=WorldlineDefinition,
            placement=FlatYamlPlacement(".derived/worldline_definition", str),
        ),
        identity_field="id",
    ),
    model=WorldlineDefinition,
    fields=(
        CharterField("id", str, primary_key=True, nullable=False),
        CharterField(
            "targets",
            tuple[str, ...],
            parse_boundary="json",
            nullable=False,
        ),
        CharterField("name", str, nullable=False, default="", default_sql="''"),
        CharterField("created", str, nullable=False, default="", default_sql="''"),
        CharterField(
            "inputs",
            WorldlineInputsDocument,
            parse_boundary="json",
            nullable=True,
        ),
        CharterField(
            "policy",
            WorldlinePolicyDocument,
            parse_boundary="json",
            nullable=True,
        ),
        CharterField(
            "revision",
            WorldlineRevisionQueryDocument,
            parse_boundary="json",
            nullable=True,
        ),
        CharterField(
            "journal",
            WorldlineJournalDocument,
            parse_boundary="json",
            nullable=True,
        ),
        CharterField(
            "results",
            WorldlineResultDocument,
            parse_boundary="json",
            nullable=True,
        ),
    ),
    semantic_metadata={"semantic": "propstore.world"},
)

WORLDLINE_CHARTERS: tuple[FamilyCharter, ...] = (
    WORLDLINE_DEFINITION_CHARTER,
    WORLDLINE_RESULT_CHARTER,
    WORLDLINE_REVISION_STATE_CHARTER,
    WORLDLINE_JOURNAL_CHARTER,
)

if TYPE_CHECKING:

    class WorldlineDefinitionDocument(msgspec.Struct, forbid_unknown_fields=True):
        id: str
        targets: tuple[str, ...]
        name: str = ""
        created: str = ""
        inputs: WorldlineInputsDocument | None = None
        policy: WorldlinePolicyDocument | None = None
        revision: WorldlineRevisionQueryDocument | None = None
        journal: WorldlineJournalDocument | None = None
        results: WorldlineResultDocument | None = None

else:
    WorldlineDefinitionDocument: Any = (
        WORLDLINE_DEFINITION_CHARTER.generated_document()
    )
    WorldlineDefinitionDocument.__name__ = "WorldlineDefinitionDocument"
    WorldlineDefinitionDocument.__qualname__ = "WorldlineDefinitionDocument"
    WorldlineDefinitionDocument.__module__ = __name__
