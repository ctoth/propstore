"""Typed sidecar build stages and row bundles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any

from propstore.claims import ClaimFileEntry
from propstore.families.claims.stages import ClaimCheckedBundle
from propstore.families.concepts.stages import LoadedConcept
from propstore.families.contexts.stages import LoadedContext
from propstore.families.forms.stages import FormDefinition

if TYPE_CHECKING:
    from propstore.compiler.context import CompilationContext
    from propstore.sidecar.claims import (
        ClaimAlgorithmPayloadProjectionRow,
        ClaimConceptLinkProjectionRow,
        ClaimCoreProjectionRow,
        ClaimFtsProjectionRow,
        ClaimNumericPayloadProjectionRow,
        ClaimStanceProjectionRow,
        ClaimTextPayloadProjectionRow,
        ConflictWitnessProjectionRow,
        JustificationProjectionRow,
    )
    from propstore.sidecar.contexts import (
        ContextAssumptionProjectionRow,
        ContextLiftingMaterializationProjectionRow,
        ContextLiftingRuleProjectionRow,
        ContextProjectionRow,
    )
    from propstore.sidecar.diagnostics import BuildDiagnosticProjectionRow
    from propstore.sidecar.concepts import (
        AliasProjectionRow,
        ConceptFtsProjectionRow,
        ConceptProjectionRow,
        FormAlgebraProjectionRow,
        FormProjectionRow,
        ParameterizationProjectionRow,
        ParameterizationGroupProjectionRow,
    )
    from propstore.sidecar.relations import RelationEdgeProjectionRow
    from propstore.sidecar.sources import SourceProjectionRow


@dataclass(frozen=True)
class ClaimSidecarRows:
    claim_core_rows: tuple["ClaimCoreProjectionRow", ...]
    numeric_payload_rows: tuple["ClaimNumericPayloadProjectionRow", ...]
    text_payload_rows: tuple["ClaimTextPayloadProjectionRow", ...]
    algorithm_payload_rows: tuple["ClaimAlgorithmPayloadProjectionRow", ...]
    claim_link_rows: tuple["ClaimConceptLinkProjectionRow", ...]
    stance_rows: tuple["ClaimStanceProjectionRow", ...]
    quarantine_diagnostics: tuple["QuarantineDiagnostic", ...]


@dataclass(frozen=True)
class RawIdQuarantineSidecarRows:
    claim_rows: tuple["ClaimCoreProjectionRow", ...]
    diagnostic_rows: tuple["BuildDiagnosticProjectionRow", ...]


@dataclass(frozen=True)
class QuarantineDiagnostic:
    artifact_id: str
    kind: str
    diagnostic_kind: str
    message: str
    file: str | None = None


@dataclass(frozen=True)
class MicropublicationInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class MicropublicationClaimInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class MicropublicationSidecarRows:
    micropublication_rows: tuple[MicropublicationInsertRow, ...]
    claim_rows: tuple[MicropublicationClaimInsertRow, ...]


@dataclass(frozen=True)
class ContextSidecarRows:
    context_rows: tuple["ContextProjectionRow", ...]
    assumption_rows: tuple["ContextAssumptionProjectionRow", ...]
    lifting_rule_rows: tuple["ContextLiftingRuleProjectionRow", ...]
    lifting_materialization_rows: tuple["ContextLiftingMaterializationProjectionRow", ...] = ()


@dataclass(frozen=True)
class ConceptRelationshipInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class ConceptSidecarRows:
    form_rows: tuple["FormProjectionRow", ...]
    concept_rows: tuple["ConceptProjectionRow", ...]
    alias_rows: tuple["AliasProjectionRow", ...]
    relationship_rows: tuple[ConceptRelationshipInsertRow, ...]
    relation_edge_rows: tuple["RelationEdgeProjectionRow", ...]
    parameterization_rows: tuple["ParameterizationProjectionRow", ...]
    parameterization_group_rows: tuple["ParameterizationGroupProjectionRow", ...]
    form_algebra_rows: tuple["FormAlgebraProjectionRow", ...]
    concept_fts_rows: tuple["ConceptFtsProjectionRow", ...]


@dataclass(frozen=True)
class RepositoryCheckedBundle:
    concepts: list[LoadedConcept]
    form_registry: dict[str, FormDefinition]
    context_files: tuple[LoadedContext, ...]
    context_ids: frozenset[str]
    compilation_context: "CompilationContext"
    concept_registry: dict
    claim_checked_bundle: ClaimCheckedBundle | None
    normalized_claim_files: tuple[ClaimFileEntry, ...] | None


@dataclass(frozen=True)
class SidecarBuildPlan:
    source_rows: tuple["SourceProjectionRow", ...]
    concept_rows: ConceptSidecarRows
    context_rows: ContextSidecarRows
    claim_rows: ClaimSidecarRows | None
    raw_id_quarantine_rows: RawIdQuarantineSidecarRows
    conflict_rows: tuple["ConflictWitnessProjectionRow", ...]
    claim_fts_rows: tuple["ClaimFtsProjectionRow", ...]
    micropublication_rows: MicropublicationSidecarRows
    stance_rows: tuple["ClaimStanceProjectionRow", ...]
    justification_rows: tuple["JustificationProjectionRow", ...]
    quarantine_diagnostics: tuple[QuarantineDiagnostic, ...]
