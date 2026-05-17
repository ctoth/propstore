"""Sidecar row compilation passes."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from quire.projections import ProjectionRow

from propstore.claims import (
    ClaimFileEntry,
)
from propstore.families.concepts.stages import LoadedConcept
from propstore.families.concepts.declaration import (
    ConceptSidecarRows,
    compile_concept_sidecar_rows,
)
from propstore.families.contexts.stages import LoadedContext, loaded_contexts_to_lifting_system
from propstore.families.contexts.declaration import (
    compile_context_sidecar_rows,
)
from propstore.families.claims.stages import (
    ClaimCheckedBundle,
    ClaimSidecarRows,
    RawIdQuarantineSidecarRows,
)
from propstore.families.claims.references import (
    build_claim_file_reference_index,
)
from propstore.families.forms.stages import (
    FormDefinition,
)
from propstore.families.claims.declaration import (
    compile_authored_justification_sidecar_rows_with_diagnostics,
    compile_claim_sidecar_rows,
    compile_conflict_sidecar_rows,
    compile_raw_id_quarantine_sidecar_rows,
)
from propstore.families.diagnostics.declaration import (
    QuarantineDiagnostic,
)
from propstore.families.micropublications.declaration import (
    MicropublicationSidecarRows,
    compile_micropublication_sidecar_rows_with_diagnostics,
)
from propstore.families.relations.declaration import (
    compile_authored_stance_sidecar_rows_with_diagnostics,
)
from propstore.families.sources.declaration import (
    SourceProjectionRow,
    compile_source_sidecar_rows,
)

if TYPE_CHECKING:
    from propstore.compiler.context import CompilationContext
    from propstore.families.documents.justifications import JustificationDocument
    from propstore.families.documents.micropubs import MicropublicationDocument
    from propstore.families.documents.sources import SourceDocument
    from propstore.families.documents.stances import StanceDocument


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
    source_rows: tuple[SourceProjectionRow, ...]
    concept_rows: ConceptSidecarRows
    context_rows: tuple[ProjectionRow, ...]
    claim_rows: ClaimSidecarRows | None
    raw_id_quarantine_rows: RawIdQuarantineSidecarRows
    conflict_rows: tuple[ProjectionRow, ...]
    micropublication_rows: MicropublicationSidecarRows
    stance_rows: tuple[ProjectionRow, ...]
    justification_rows: tuple[ProjectionRow, ...]
    quarantine_diagnostics: tuple[QuarantineDiagnostic, ...]


def compile_sidecar_build_plan(
    repository_checked_bundle: RepositoryCheckedBundle,
    *,
    source_entries: Iterable[tuple[str, SourceDocument]],
    stance_entries: Iterable[tuple[str, StanceDocument]],
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    micropub_entries: Iterable[tuple[str, MicropublicationDocument]],
) -> SidecarBuildPlan:
    claim_rows: ClaimSidecarRows | None = None
    raw_id_quarantine_rows = compile_raw_id_quarantine_sidecar_rows(())
    conflict_rows: tuple[ProjectionRow, ...] = ()
    stance_rows: tuple[ProjectionRow, ...] = ()
    justification_rows: tuple[ProjectionRow, ...] = ()
    quarantine_diagnostics: tuple[QuarantineDiagnostic, ...] = ()
    claim_index = build_claim_file_reference_index(())

    if repository_checked_bundle.normalized_claim_files is not None:
        checked_claims = repository_checked_bundle.claim_checked_bundle
        if checked_claims is None:
            raise ValueError("checked claim bundle is required to populate claims")
        normalized_claim_files = repository_checked_bundle.normalized_claim_files
        claim_index = build_claim_file_reference_index(normalized_claim_files)
        claim_rows = compile_claim_sidecar_rows(
            checked_claims.bundle,
            repository_checked_bundle.concept_registry,
            form_registry=repository_checked_bundle.form_registry,
        )
        quarantine_diagnostics = claim_rows.quarantine_diagnostics
        raw_id_quarantine_rows = compile_raw_id_quarantine_sidecar_rows(
            checked_claims.raw_id_quarantine_records
        )
        lifting_system = (
            loaded_contexts_to_lifting_system(
                list(repository_checked_bundle.context_files)
            )
            if repository_checked_bundle.context_files
            else None
        )
        conflict_rows = compile_conflict_sidecar_rows(
            list(normalized_claim_files),
            repository_checked_bundle.concept_registry,
            dict(repository_checked_bundle.compilation_context.cel_registry),
            lifting_system=lifting_system,
        )
        stance_rows, stance_quarantine_diagnostics = (
            compile_authored_stance_sidecar_rows_with_diagnostics(
                stance_entries,
                claim_index,
            )
        )
        justification_rows, justification_quarantine_diagnostics = (
            compile_authored_justification_sidecar_rows_with_diagnostics(
                justification_entries,
                claim_index,
            )
        )
        quarantine_diagnostics = (
            quarantine_diagnostics
            + stance_quarantine_diagnostics
            + justification_quarantine_diagnostics
        )

    micropublication_rows, micropublication_quarantine_diagnostics = (
        compile_micropublication_sidecar_rows_with_diagnostics(
            micropub_entries,
            claim_index,
        )
    )
    quarantine_diagnostics = (
        quarantine_diagnostics + micropublication_quarantine_diagnostics
    )

    return SidecarBuildPlan(
        source_rows=compile_source_sidecar_rows(source_entries),
        concept_rows=compile_concept_sidecar_rows(
            repository_checked_bundle.concepts,
            repository_checked_bundle.form_registry,
            dict(repository_checked_bundle.compilation_context.cel_registry),
        ),
        context_rows=compile_context_sidecar_rows(
            repository_checked_bundle.context_files,
        ),
        claim_rows=claim_rows,
        raw_id_quarantine_rows=raw_id_quarantine_rows,
        conflict_rows=conflict_rows,
        micropublication_rows=micropublication_rows,
        stance_rows=stance_rows,
        justification_rows=justification_rows,
        quarantine_diagnostics=quarantine_diagnostics,
    )
