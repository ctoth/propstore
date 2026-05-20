"""Sidecar row compilation passes."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

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
    filter_invalid_context_lifting_rows,
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
from propstore.families.world_charters import WorldModel, world_records

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
class WorldWriteBatch:
    table_name: str
    objects: tuple[WorldModel, ...]


@dataclass(frozen=True)
class SidecarBuildPlan:
    write_batches: tuple[WorldWriteBatch, ...]
    has_claim_rows: bool
    has_raw_id_quarantine_claims: bool
    quarantine_diagnostics: tuple[QuarantineDiagnostic, ...]


def compile_sidecar_build_plan(
    repository_checked_bundle: RepositoryCheckedBundle,
    *,
    source_entries: Iterable[tuple[str, SourceDocument]],
    stance_entries: Iterable[tuple[str, StanceDocument]],
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    micropub_entries: Iterable[tuple[str, MicropublicationDocument]],
    drop_invalid_context_lifting_rows: bool = False,
) -> SidecarBuildPlan:
    claim_rows: ClaimSidecarRows | None = None
    raw_id_quarantine_rows = compile_raw_id_quarantine_sidecar_rows(())
    conflict_rows: tuple[object, ...] = ()
    stance_rows: tuple[object, ...] = ()
    justification_rows: tuple[object, ...] = ()
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

    context_rows = compile_context_sidecar_rows(
        repository_checked_bundle.context_files,
    )
    if drop_invalid_context_lifting_rows:
        context_rows = filter_invalid_context_lifting_rows(context_rows)
    batches = (
        _batch("source", compile_source_sidecar_rows(source_entries)),
        *_concept_batches(
            compile_concept_sidecar_rows(
                repository_checked_bundle.concepts,
                repository_checked_bundle.form_registry,
                dict(repository_checked_bundle.compilation_context.cel_registry),
            )
        ),
        *_projection_row_batches(
            context_rows,
            (
                "context",
                "context_assumption",
                "context_lifting_rule",
                "context_lifting_materialization",
            ),
        ),
        *_claim_batches(claim_rows),
        *_raw_id_quarantine_batches(raw_id_quarantine_rows),
        _batch("conflict_witness", conflict_rows),
        *_micropublication_batches(micropublication_rows),
        _batch("relation_edge", stance_rows),
        _batch("justification", justification_rows),
    )
    return SidecarBuildPlan(
        write_batches=tuple(batch for batch in batches if batch.objects),
        has_claim_rows=claim_rows is not None,
        has_raw_id_quarantine_claims=bool(raw_id_quarantine_rows.claim_rows),
        quarantine_diagnostics=quarantine_diagnostics,
    )


def _batch(table_name: str, rows: Iterable[object] | None) -> WorldWriteBatch:
    return WorldWriteBatch(table_name=table_name, objects=world_records(table_name, rows))


def _projection_row_batches(
    rows: Iterable[object],
    table_order: tuple[str, ...],
) -> tuple[WorldWriteBatch, ...]:
    grouped: dict[str, list[object]] = {table_name: [] for table_name in table_order}
    for row in rows:
        table_name = str(getattr(row, "table"))
        if table_name not in grouped:
            grouped[table_name] = []
        grouped[table_name].append(row)
    return tuple(
        _batch(table_name, grouped.get(table_name, ()))
        for table_name in table_order
    )


def _concept_batches(rows: ConceptSidecarRows) -> tuple[WorldWriteBatch, ...]:
    return (
        _batch("form", rows.form_rows),
        _batch("concept", rows.concept_rows),
        _batch("alias", rows.alias_rows),
        _batch("relationship", rows.relationship_rows),
        _batch("relation_edge", rows.relation_edge_rows),
        _batch("parameterization", rows.parameterization_rows),
        _batch("parameterization_group", rows.parameterization_group_rows),
        _batch("form_algebra", rows.form_algebra_rows),
    )


def _claim_batches(rows: ClaimSidecarRows | None) -> tuple[WorldWriteBatch, ...]:
    if rows is None:
        return ()
    return (
        _batch("claim_core", rows.claim_core_rows),
        _batch("claim_numeric_payload", rows.numeric_payload_rows),
        _batch("claim_text_payload", rows.text_payload_rows),
        _batch("claim_algorithm_payload", rows.algorithm_payload_rows),
        _batch("claim_concept_link", rows.claim_link_rows),
        _batch("relation_edge", rows.stance_rows),
    )


def _raw_id_quarantine_batches(
    rows: RawIdQuarantineSidecarRows,
) -> tuple[WorldWriteBatch, ...]:
    return (
        _batch("claim_core", rows.claim_rows),
        _batch("build_diagnostics", rows.diagnostic_rows),
    )


def _micropublication_batches(
    rows: MicropublicationSidecarRows,
) -> tuple[WorldWriteBatch, ...]:
    return (
        _batch("micropublication", rows.micropublication_rows),
        _batch("micropublication_claim", rows.claim_rows),
    )
