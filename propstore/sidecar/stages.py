"""Typed sidecar build stages and row bundles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from propstore.claims import ClaimFileEntry
from propstore.families.claims.stages import ClaimCheckedBundle
from propstore.families.concepts.stages import LoadedConcept
from propstore.families.contexts.stages import LoadedContext
from propstore.families.forms.stages import FormDefinition

if TYPE_CHECKING:
    from quire.projections import ProjectionRow
    from propstore.compiler.context import CompilationContext
    from propstore.sidecar.micropublications import (
        MicropublicationClaimProjectionRow,
        MicropublicationProjectionRow,
    )
    from propstore.sidecar.sources import SourceProjectionRow


@dataclass(frozen=True)
class ClaimSidecarRows:
    claim_core_rows: tuple["ProjectionRow", ...]
    numeric_payload_rows: tuple["ProjectionRow", ...]
    text_payload_rows: tuple["ProjectionRow", ...]
    algorithm_payload_rows: tuple["ProjectionRow", ...]
    claim_link_rows: tuple["ProjectionRow", ...]
    stance_rows: tuple["ProjectionRow", ...]
    quarantine_diagnostics: tuple["QuarantineDiagnostic", ...]


@dataclass(frozen=True)
class RawIdQuarantineSidecarRows:
    claim_rows: tuple["ProjectionRow", ...]
    diagnostic_rows: tuple["ProjectionRow", ...]


@dataclass(frozen=True)
class QuarantineDiagnostic:
    artifact_id: str
    kind: str
    diagnostic_kind: str
    message: str
    file: str | None = None


@dataclass(frozen=True)
class MicropublicationSidecarRows:
    micropublication_rows: tuple["MicropublicationProjectionRow", ...]
    claim_rows: tuple["MicropublicationClaimProjectionRow", ...]


@dataclass(frozen=True)
class ContextSidecarRows:
    context_rows: tuple["ProjectionRow", ...]
    assumption_rows: tuple["ProjectionRow", ...]
    lifting_rule_rows: tuple["ProjectionRow", ...]
    lifting_materialization_rows: tuple["ProjectionRow", ...] = ()


@dataclass(frozen=True)
class ConceptRelationshipProjectionRow:
    source_id: str
    relationship_type: str
    target_id: str
    conditions_cel: str | None
    note: str | None


@dataclass(frozen=True)
class ConceptSidecarRows:
    form_rows: tuple["ProjectionRow", ...]
    concept_rows: tuple["ProjectionRow", ...]
    alias_rows: tuple["ProjectionRow", ...]
    relationship_rows: tuple[ConceptRelationshipProjectionRow, ...]
    relation_edge_rows: tuple["ProjectionRow", ...]
    parameterization_rows: tuple["ProjectionRow", ...]
    parameterization_group_rows: tuple["ProjectionRow", ...]
    form_algebra_rows: tuple["ProjectionRow", ...]


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
    conflict_rows: tuple["ProjectionRow", ...]
    micropublication_rows: MicropublicationSidecarRows
    stance_rows: tuple["ProjectionRow", ...]
    justification_rows: tuple["ProjectionRow", ...]
    quarantine_diagnostics: tuple[QuarantineDiagnostic, ...]
