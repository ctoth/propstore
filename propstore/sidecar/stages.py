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


@dataclass(frozen=True)
class ClaimInsertRow:
    values: dict[str, object]


@dataclass(frozen=True)
class ClaimStanceInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class ClaimSidecarRows:
    claim_rows: tuple[ClaimInsertRow, ...]
    stance_rows: tuple[ClaimStanceInsertRow, ...]


@dataclass(frozen=True)
class JustificationInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class ConflictWitnessInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class ClaimFtsInsertRow:
    values: tuple[Any, ...]


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
class FormInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class ConceptInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class ConceptAliasInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class ConceptRelationshipInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class RelationEdgeInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class ConceptParameterizationInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class ConceptParameterizationGroupInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class FormAlgebraInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class ConceptFtsInsertRow:
    values: tuple[Any, ...]


@dataclass(frozen=True)
class ConceptSidecarRows:
    form_rows: tuple[FormInsertRow, ...]
    concept_rows: tuple[ConceptInsertRow, ...]
    alias_rows: tuple[ConceptAliasInsertRow, ...]
    relationship_rows: tuple[ConceptRelationshipInsertRow, ...]
    relation_edge_rows: tuple[RelationEdgeInsertRow, ...]
    parameterization_rows: tuple[ConceptParameterizationInsertRow, ...]
    parameterization_group_rows: tuple[ConceptParameterizationGroupInsertRow, ...]
    form_algebra_rows: tuple[FormAlgebraInsertRow, ...]
    concept_fts_rows: tuple[ConceptFtsInsertRow, ...]


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
