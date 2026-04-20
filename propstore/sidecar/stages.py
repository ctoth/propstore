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
class RepositoryCheckedBundle:
    concepts: list[LoadedConcept]
    form_registry: dict[str, FormDefinition]
    context_files: tuple[LoadedContext, ...]
    context_ids: frozenset[str]
    compilation_context: "CompilationContext"
    concept_registry: dict
    claim_checked_bundle: ClaimCheckedBundle | None
    normalized_claim_files: tuple[ClaimFileEntry, ...] | None
