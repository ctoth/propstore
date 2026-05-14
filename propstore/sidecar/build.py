"""Sidecar build orchestration.

Schema-v3 gate refactor (``reviews/2026-04-16-code-review/workstreams/
ws-z-render-gates.md`` axis-1 finding 3.1): the former
``_raise_on_raw_id_claim_inputs`` build-time abort has been replaced with
the claim family pipeline, which produces typed quarantine records.
The build proceeds; the offending claim lands as a stub row in
``claim_core`` with ``build_status='blocked'`` and a ``build_diagnostics``
row carries the reason. Render-policy filtering (phase 4) decides
whether to show these rows. This implements the discipline declared in
``reviews/2026-04-16-code-review/workstreams/disciplines.md`` rule 5:
"Filter at render, not at build".
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from quire.derived_store import (
    DerivedStoreHandle,
    checkpoint_and_close_sqlite,
    derived_store_content_hash,
    digest_directory,
    materialize_sqlite_file,
    read_dependency_pins,
)
from propstore.claims import ClaimFileEntry
from propstore.compiler.context import (
    build_compilation_context_from_loaded,
)
from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY
from propstore.families.claims.passes import register_claim_pipeline, run_claim_pipeline
from propstore.families.claims.stages import ClaimAuthoredFiles, ClaimCheckedBundle
from propstore.families.contexts.passes import register_context_pipeline
from propstore.families.contexts.stages import (
    LoadedContext,
    parse_context_record_document,
)
from propstore.families.concepts.passes import register_concept_pipeline
from propstore.families.concepts.stages import LoadedConcept, parse_concept_record_document
from propstore.families.forms.passes import register_form_pipeline, run_form_pipeline
from propstore.families.forms.stages import FormCheckedRegistry, LoadedForm
from propstore.grounding.loading import build_grounded_bundle
from propstore.sidecar.claims import (
    CLAIM_FTS_PROJECTION,
    CLAIM_CORE_PROJECTION,
    populate_authored_justifications,
    populate_claims,
    populate_conflicts,
    populate_raw_id_quarantine_records,
    populate_stances,
)
from propstore.sidecar.passes import compile_sidecar_build_plan
from propstore.sidecar.stages import ContextSidecarRows, RepositoryCheckedBundle
from propstore.sidecar.concepts import CONCEPT_FTS_PROJECTION, populate_concept_sidecar_rows
from propstore.sidecar.diagnostics import BUILD_DIAGNOSTICS_PROJECTION
from propstore.sidecar.embedding_store import ensure_embedding_tables
from propstore.sidecar.schema import (
    create_claim_tables,
    create_micropublication_tables,
    create_context_tables,
    create_tables,
    populate_contexts,
    write_schema_metadata,
)
from propstore.sidecar.micropublications import populate_micropublications
from propstore.sidecar.quarantine import QuarantinableWriter
from propstore.sidecar.rules import create_grounded_fact_table, populate_grounded_facts
from propstore.sidecar.sources import populate_sources
from propstore.compiler.context import build_authored_concept_registry
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.types import PassDiagnostic
import propstore.sidecar.schema as sidecar_schema
from propstore.sidecar.stages import QuarantineDiagnostic
from propstore.sidecar.sqlite import connect_sidecar

if TYPE_CHECKING:
    from propstore.compiler.context import CompilationContext
    from propstore.repository import Repository

_SIDECAR_CACHE_DEPENDENCIES = (
    "argumentation",
    "ast-equiv",
    "bridgman",
    "gunray",
    "quire",
)


@dataclass(frozen=True)
class EmbeddingSnapshotReport:
    model_count: int
    claim_vector_count: int
    concept_vector_count: int


def world_sidecar_hash_inputs(
    source_revision: str,
    *,
    source_branch_tips: tuple[tuple[str, str], ...] = (),
) -> dict[str, object]:
    repo_root = Path(__file__).resolve().parents[2]
    dependency_pins = read_dependency_pins(
        repo_root / "uv.lock",
        _SIDECAR_CACHE_DEPENDENCIES,
    )
    return {
        "source_revision": source_revision,
        "source_branch_tips": source_branch_tips,
        "sidecar_schema_version": sidecar_schema.SCHEMA_VERSION,
        "passes": _semantic_pass_versions(),
        "family_contract_versions": _family_contract_versions(),
        "build_time_config": {
            "PROPSTORE_SIDECAR_CACHE_BUST": os.environ.get(
                "PROPSTORE_SIDECAR_CACHE_BUST",
                "",
            ),
        },
        "generated_schema_version": digest_directory(repo_root / "schema" / "generated"),
        "dependency_pins": dependency_pins,
    }


def _source_branch_tips(repo: "Repository") -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (branch.name, branch.tip_sha)
            for branch in repo.snapshot.iter_branches()
            if branch.kind == "source"
        )
    )


def world_sidecar_hash(
    source_revision: str,
    *,
    source_branch_tips: tuple[tuple[str, str], ...] = (),
) -> str:
    inputs = world_sidecar_hash_inputs(
        source_revision,
        source_branch_tips=source_branch_tips,
    )
    dependencies = read_dependency_pins(
        Path(__file__).resolve().parents[2] / "uv.lock",
        _SIDECAR_CACHE_DEPENDENCIES,
    )
    content_hash = derived_store_content_hash(
        projection_version=str(sidecar_schema.SCHEMA_VERSION),
        schema_hash=str(inputs["generated_schema_version"]),
        dependencies=dependencies,
        extra_inputs={
            "source_revision": inputs["source_revision"],
            "source_branch_tips": inputs["source_branch_tips"],
            "passes": inputs["passes"],
            "family_contract_versions": inputs["family_contract_versions"],
            "build_time_config": inputs["build_time_config"],
        },
    )
    return content_hash.removeprefix("sha256:")


def _family_contract_versions() -> dict[str, str]:
    versions = {
        "propstore_registry": str(PROPSTORE_FAMILY_REGISTRY.contract_version),
    }
    for family in PROPSTORE_FAMILY_REGISTRY.families:
        versions[family.name] = str(family.contract_version)
        artifact_family = getattr(family, "artifact_family", None)
        artifact_name = getattr(artifact_family, "name", None)
        artifact_version = getattr(artifact_family, "contract_version", None)
        if isinstance(artifact_name, str) and artifact_version is not None:
            versions[artifact_name] = str(artifact_version)
    return dict(sorted(versions.items()))


def _semantic_pass_versions() -> tuple[dict[str, str], ...]:
    registry = PipelineRegistry()
    register_claim_pipeline(registry)
    register_concept_pipeline(registry)
    register_context_pipeline(registry)
    register_form_pipeline(registry)
    pass_inputs: list[dict[str, str]] = []
    for pass_class in registry.registered_passes():
        version = getattr(pass_class, "version", None)
        if not isinstance(version, str) or not version:
            raise RuntimeError(
                f"semantic pass {pass_class.name!r} must declare a non-empty version"
            )
        pass_inputs.append(
            {
                "family": pass_class.family.value,
                "name": pass_class.name,
                "input_stage": pass_class.input_stage.value,
                "output_stage": pass_class.output_stage.value,
                "version": version,
            }
        )
    return tuple(
        sorted(
            pass_inputs,
            key=lambda item: (
                item["family"],
                item["name"],
                item["input_stage"],
                item["output_stage"],
            ),
        )
    )


def _record_build_exception(conn: sqlite3.Connection, exc: Exception) -> None:
    """Persist a build-exception diagnostic instead of deleting the sidecar.

    Rule 5 from the render-gates workstream keeps build failures inspectable at
    render time; the partial sidecar is evidence, not trash to unlink.
    """
    for statement in BUILD_DIAGNOSTICS_PROJECTION.ddl_statements():
        conn.execute(statement)
    BUILD_DIAGNOSTICS_PROJECTION.insert_row(
        conn,
        BUILD_DIAGNOSTICS_PROJECTION.row(
            claim_id=None,
            source_kind="sidecar_build",
            source_ref=None,
            diagnostic_kind="build_exception",
            severity="error",
            blocking=1,
            message=str(exc),
            file=None,
            detail_json=None,
        ),
    )
    conn.commit()


def _record_embedding_restore_diagnostic(
    conn: sqlite3.Connection,
    exc: Exception,
) -> None:
    for statement in BUILD_DIAGNOSTICS_PROJECTION.ddl_statements():
        conn.execute(statement)
    BUILD_DIAGNOSTICS_PROJECTION.insert_row(
        conn,
        BUILD_DIAGNOSTICS_PROJECTION.row(
            claim_id=None,
            source_kind="embedding",
            source_ref="restore",
            diagnostic_kind="embedding_restore",
            severity="warning",
            blocking=0,
            message=f"embedding restore failed: {exc}",
            file=None,
            detail_json=None,
        ),
    )


def _record_form_diagnostics(
    conn: sqlite3.Connection,
    diagnostics: tuple[PassDiagnostic, ...],
) -> None:
    if not diagnostics:
        return
    writer = QuarantinableWriter(conn)
    for diagnostic in diagnostics:
        if not diagnostic.is_error:
            continue
        writer.quarantine(
            artifact_id=diagnostic.filename or diagnostic.artifact_id or "unknown",
            kind="form",
            diagnostic_kind="form_validation",
            message=diagnostic.render(),
            file=diagnostic.filename,
        )


def _record_claim_diagnostics(
    conn: sqlite3.Connection,
    diagnostics: tuple[PassDiagnostic, ...],
) -> None:
    if not diagnostics:
        return
    writer = QuarantinableWriter(conn)
    for diagnostic in diagnostics:
        if not diagnostic.is_error:
            continue
        writer.quarantine(
            artifact_id=diagnostic.artifact_id or diagnostic.filename or "unknown",
            kind="claim",
            diagnostic_kind="claim_validation",
            message=diagnostic.render(),
            file=diagnostic.filename,
        )


def _record_concept_diagnostics(
    conn: sqlite3.Connection,
    diagnostics: tuple[PassDiagnostic, ...],
) -> None:
    if not diagnostics:
        return
    writer = QuarantinableWriter(conn)
    for diagnostic in diagnostics:
        if not diagnostic.is_error:
            continue
        writer.quarantine(
            artifact_id=diagnostic.artifact_id or diagnostic.filename or "unknown",
            kind="concept",
            diagnostic_kind="concept_validation",
            message=diagnostic.render(),
            file=diagnostic.filename,
        )


def _record_context_diagnostics(
    conn: sqlite3.Connection,
    diagnostics: tuple[PassDiagnostic, ...],
) -> None:
    if not diagnostics:
        return
    writer = QuarantinableWriter(conn)
    for diagnostic in diagnostics:
        if not diagnostic.is_error:
            continue
        writer.quarantine(
            artifact_id=diagnostic.artifact_id or diagnostic.filename or "unknown",
            kind="context",
            diagnostic_kind="context_validation",
            message=diagnostic.render(),
            file=diagnostic.filename,
        )


def _record_authoring_diagnostics(
    conn: sqlite3.Connection,
    diagnostics: tuple[PassDiagnostic, ...],
) -> None:
    for diagnostic in diagnostics:
        BUILD_DIAGNOSTICS_PROJECTION.insert_row(
            conn,
            BUILD_DIAGNOSTICS_PROJECTION.row(
                claim_id=diagnostic.artifact_id,
                source_kind="authoring",
                source_ref=diagnostic.artifact_id or diagnostic.filename,
                diagnostic_kind=diagnostic.code,
                severity=diagnostic.level,
                blocking=1 if diagnostic.is_error else 0,
                message=diagnostic.render(),
                file=diagnostic.filename,
                detail_json=None,
            ),
        )


def _filter_invalid_context_lifting_rows(
    rows: ContextSidecarRows,
) -> ContextSidecarRows:
    context_ids = {row.values["id"] for row in rows.context_rows}
    valid_lifting_rows = tuple(
        row
        for row in rows.lifting_rule_rows
        if row.values["source_context_id"] in context_ids
        and row.values["target_context_id"] in context_ids
    )
    return ContextSidecarRows(
        context_rows=rows.context_rows,
        assumption_rows=rows.assumption_rows,
        lifting_rule_rows=valid_lifting_rows,
        lifting_materialization_rows=rows.lifting_materialization_rows,
    )


def _record_quarantine_diagnostics(
    conn: sqlite3.Connection,
    diagnostics: tuple[QuarantineDiagnostic, ...],
) -> None:
    if not diagnostics:
        return
    writer = QuarantinableWriter(conn)
    for diagnostic in diagnostics:
        writer.quarantine(
            artifact_id=diagnostic.artifact_id,
            kind=diagnostic.kind,
            diagnostic_kind=diagnostic.diagnostic_kind,
            message=diagnostic.message,
            file=diagnostic.file,
        )


def _compile_source_promotion_blocked_rows(repo: "Repository"):
    from propstore.source.promote import compile_source_promotion_blocked_projection_rows

    claim_rows = []
    diagnostic_rows = []
    for branch in repo.snapshot.iter_branches():
        if branch.kind != "source":
            continue
        source_name = branch.name.removeprefix("source/")
        rows = compile_source_promotion_blocked_projection_rows(repo, source_name)
        claim_rows.extend(rows.claim_rows)
        diagnostic_rows.extend(rows.diagnostic_rows)
    return tuple(claim_rows), tuple(diagnostic_rows)


def _populate_promotion_blocked_rows(
    conn: sqlite3.Connection,
    claim_rows,
    diagnostic_rows,
) -> None:
    if not claim_rows and not diagnostic_rows:
        return
    child_claim_tables = {
        row[0]
        for row in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name IN (
                  'claim_concept_link',
                  'claim_numeric_payload',
                  'claim_text_payload',
                  'claim_algorithm_payload',
                  'micropublication_claim'
              )
            """
        ).fetchall()
    }
    schema_tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    if "concept" not in schema_tables:
        child_claim_tables.discard("claim_concept_link")
    claim_rows_by_id = {str(row.values["id"]): row for row in claim_rows}
    claim_ids = tuple(claim_rows_by_id)
    for claim_id in claim_ids:
        for table_name in (
            "claim_concept_link",
            "claim_numeric_payload",
            "claim_text_payload",
            "claim_algorithm_payload",
            "micropublication_claim",
        ):
            if table_name not in child_claim_tables:
                continue
            conn.execute(
                f"DELETE FROM {table_name} WHERE claim_id = ?",
                (claim_id,),
            )
        conn.execute("DELETE FROM claim_core WHERE id = ?", (claim_id,))
        conn.execute(
            "DELETE FROM build_diagnostics "
            "WHERE claim_id = ? AND diagnostic_kind = 'promotion_blocked'",
            (claim_id,),
        )
    CLAIM_CORE_PROJECTION.insert_rows(conn, (row.values for row in claim_rows_by_id.values()))
    for row in diagnostic_rows:
        BUILD_DIAGNOSTICS_PROJECTION.insert_row(conn, row)


def materialize_world_sidecar(
    repo: "Repository",
    force: bool = False,
    **kwargs,
) -> tuple[DerivedStoreHandle, bool]:
    with repo.mutation_guard():
        return _materialize_world_sidecar_locked(repo, force, **kwargs)


def _materialize_world_sidecar_locked(
    repo: "Repository",
    force: bool = False,
    **kwargs,
) -> tuple[DerivedStoreHandle, bool]:
    commit_hash = kwargs.get("commit_hash")
    if commit_hash is None:
        commit_hash = repo.require_git().head_sha()
        if commit_hash is None:
            raise ValueError("world sidecar materialization requires a committed git repository")
        kwargs["commit_hash"] = commit_hash
    source_branch_tips = _source_branch_tips(repo)
    content_hash = world_sidecar_hash(
        str(commit_hash),
        source_branch_tips=source_branch_tips,
    )

    def _build(target: Path) -> None:
        _build_sidecar_file(repo, target, force=True, **kwargs)

    materialization = repo.derived_stores.materialize_with_report(
        projection_id="propstore.world",
        source_commit=str(commit_hash),
        content_hash=content_hash,
        build=_build,
        force=force,
    )
    return materialization.handle, materialization.built


def export_sidecar(
    repo: "Repository",
    output_path: Path,
    force: bool = False,
    **kwargs,
) -> bool:
    with repo.mutation_guard():
        return _build_sidecar_file(repo, output_path, force, **kwargs)


def _build_sidecar_file(
    repo: "Repository",
    output_path: Path,
    force: bool = False,
    *,
    commit_hash: str | None = None,
    compilation_context: CompilationContext | None = None,
    claim_checked_bundle: ClaimCheckedBundle | None = None,
    claim_files: tuple[ClaimFileEntry, ...] | None = None,
    claim_diagnostics: tuple[PassDiagnostic, ...] = (),
    concept_files: tuple[LoadedConcept, ...] | None = None,
    concept_diagnostics: tuple[PassDiagnostic, ...] = (),
    context_files: tuple[LoadedContext, ...] | None = None,
    context_diagnostics: tuple[PassDiagnostic, ...] = (),
    authoring_diagnostics: tuple[PassDiagnostic, ...] = (),
    on_embedding_snapshot: Callable[[EmbeddingSnapshotReport], None] | None = None,
) -> bool:
    """Build the SQLite sidecar from repository artifact families."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree = repo.tree(commit=commit_hash)

    if commit_hash is not None:
        source_revision = commit_hash
    else:
        source_revision = repo.require_git().head_sha()
        if source_revision is None:
            raise ValueError("build_sidecar requires a committed git repository or an explicit commit_hash")
    source_branch_tips = _source_branch_tips(repo)
    content_hash = world_sidecar_hash(
        source_revision,
        source_branch_tips=source_branch_tips,
    )

    form_result = run_form_pipeline(
        [
            LoadedForm(
                filename=handle.ref.name,
                document=handle.document,
            )
            for handle in repo.families.forms.iter_handles(commit=commit_hash)
        ]
    )
    if not isinstance(form_result.output, FormCheckedRegistry):
        errors = ", ".join(error.render() for error in form_result.errors)
        raise ValueError(f"form validation failed: {errors}")
    form_registry = form_result.output.registry
    form_diagnostics = form_result.diagnostics
    concepts = (
        list(concept_files)
        if concept_files is not None
        else [
            LoadedConcept(
                filename=handle.ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_concept_record_document(handle.document),
                document=handle.document,
            )
            for handle in repo.families.concepts.iter_handles(commit=commit_hash)
        ]
    )
    claim_entries = (
        list(claim_files)
        if claim_files is not None
        else [
            handle
            for handle in repo.families.claims.iter_handles(commit=commit_hash)
        ]
    )
    if context_files is None:
        context_files = tuple(
            LoadedContext(
                filename=handle.ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_context_record_document(handle.document),
            )
            for handle in repo.families.contexts.iter_handles(commit=commit_hash)
        )
    context_ids = {
        str(c.record.context_id)
        for c in (context_files or [])
        if c.record.context_id is not None
    }

    if compilation_context is None:
        compilation_context = build_compilation_context_from_loaded(
            concepts,
            form_registry=form_registry,
            claim_files=list(claim_entries) if claim_entries else None,
            context_ids=context_ids,
        )
    concept_registry = build_authored_concept_registry(
        concepts,
        form_registry=form_registry,
        require_form_definition=False,
    )
    claim_bundle = (
        None
        if claim_checked_bundle is None
        else claim_checked_bundle.bundle
    )
    recorded_claim_diagnostics = list(claim_diagnostics)
    if claim_bundle is None and claim_entries:
        claim_pipeline_result = run_claim_pipeline(
            ClaimAuthoredFiles.from_sequence(
                list(claim_entries),
                compilation_context,
                context_ids=context_ids if context_ids else None,
            )
        )
        if not isinstance(claim_pipeline_result.output, ClaimCheckedBundle):
            recorded_claim_diagnostics.extend(claim_pipeline_result.diagnostics)
        else:
            claim_checked_bundle = claim_pipeline_result.output
            claim_bundle = claim_checked_bundle.bundle
    normalized_claim_files = (
        list(claim_bundle.normalized_claim_files)
        if claim_bundle is not None
        else None
    )
    repository_checked_bundle = RepositoryCheckedBundle(
        concepts=concepts,
        form_registry=form_registry,
        context_files=tuple(context_files),
        context_ids=frozenset(context_ids),
        compilation_context=compilation_context,
        concept_registry=concept_registry,
        claim_checked_bundle=claim_checked_bundle,
        normalized_claim_files=(
            None
            if normalized_claim_files is None
            else tuple(normalized_claim_files)
        ),
    )
    sidecar_plan = compile_sidecar_build_plan(
        repository_checked_bundle,
        source_entries=(
            (
                handle.ref.name,
                handle.document,
            )
            for handle in repo.families.sources.iter_handles(commit=commit_hash)
        ),
        stance_entries=(
            (
                handle.ref.artifact_id,
                handle.document,
            )
            for handle in repo.families.stances.iter_handles(commit=commit_hash)
        ),
        justification_entries=(
            (
                handle.ref.artifact_id,
                handle.document,
            )
            for handle in repo.families.justifications.iter_handles(commit=commit_hash)
        ),
        micropub_entries=(
            (
                handle.ref.artifact_id,
                handle.document,
            )
            for handle in repo.families.micropubs.iter_handles(commit=commit_hash)
        ),
    )
    promotion_blocked_claim_rows, promotion_blocked_diagnostic_rows = (
        _compile_source_promotion_blocked_rows(repo)
    )

    embedding_snapshot = None
    if output_path.exists():
        snapshot_conn = None
        try:
            from propstore.heuristic.embed import _load_vec_extension, extract_embeddings

            snapshot_conn = connect_sidecar(output_path)
            snapshot_conn.row_factory = sqlite3.Row
            _load_vec_extension(snapshot_conn)
            embedding_snapshot = extract_embeddings(snapshot_conn)
            if embedding_snapshot is not None:
                claim_count = sum(
                    len(vectors) for vectors in embedding_snapshot.claim_vectors.values()
                )
                concept_count = sum(
                    len(vectors) for vectors in embedding_snapshot.concept_vectors.values()
                )
                if on_embedding_snapshot is not None:
                    on_embedding_snapshot(
                        EmbeddingSnapshotReport(
                            model_count=len(embedding_snapshot.models),
                            claim_vector_count=claim_count,
                            concept_vector_count=concept_count,
                        )
                    )
        except ImportError:
            pass
        finally:
            if snapshot_conn is not None:
                snapshot_conn.close()

    def _write_sidecar(target_path: Path) -> None:
        conn = connect_sidecar(target_path)
        try:
            write_schema_metadata(conn)
            create_tables(conn)
            create_context_tables(conn)
            create_grounded_fact_table(conn)
            populate_sources(
                conn,
                sidecar_plan.source_rows,
            )
            populate_concept_sidecar_rows(
                conn,
                sidecar_plan.concept_rows,
            )
            CONCEPT_FTS_PROJECTION.populate_from_source_query(conn)
            create_claim_tables(conn)
            ensure_embedding_tables(conn)
            _record_form_diagnostics(conn, form_diagnostics)
            _record_concept_diagnostics(conn, concept_diagnostics)
            _record_context_diagnostics(conn, context_diagnostics)
            _record_claim_diagnostics(conn, tuple(recorded_claim_diagnostics))
            _record_authoring_diagnostics(conn, authoring_diagnostics)
            _record_quarantine_diagnostics(conn, sidecar_plan.quarantine_diagnostics)
            create_micropublication_tables(conn)

            context_rows = (
                _filter_invalid_context_lifting_rows(sidecar_plan.context_rows)
                if context_diagnostics
                else sidecar_plan.context_rows
            )
            if context_rows.context_rows:
                populate_contexts(conn, context_rows)

            if sidecar_plan.claim_rows is not None:
                populate_claims(conn, sidecar_plan.claim_rows)

                if sidecar_plan.raw_id_quarantine_rows.claim_rows:
                    populate_raw_id_quarantine_records(
                        conn,
                        sidecar_plan.raw_id_quarantine_rows,
                    )
                _populate_promotion_blocked_rows(
                    conn,
                    promotion_blocked_claim_rows,
                    promotion_blocked_diagnostic_rows,
                )

                populate_conflicts(conn, sidecar_plan.conflict_rows)
                CLAIM_FTS_PROJECTION.populate_from_source_query(conn)
            else:
                _populate_promotion_blocked_rows(
                    conn,
                    promotion_blocked_claim_rows,
                    promotion_blocked_diagnostic_rows,
                )

            populate_micropublications(conn, sidecar_plan.micropublication_rows)

            grounded_bundle = build_grounded_bundle(
                repo,
                commit=commit_hash,
            )
            populate_grounded_facts(conn, grounded_bundle)

            if embedding_snapshot is not None:
                try:
                    from propstore.heuristic.embed import _load_vec_extension, restore_embeddings

                    conn.row_factory = sqlite3.Row
                    _load_vec_extension(conn)
                    restore_embeddings(conn, embedding_snapshot)
                    conn.row_factory = None
                except ImportError as exc:
                    _record_embedding_restore_diagnostic(conn, exc)
                    conn.row_factory = None
                except Exception as exc:
                    _record_embedding_restore_diagnostic(conn, exc)
                    conn.row_factory = None

            if sidecar_plan.claim_rows is not None:
                populate_stances(conn, sidecar_plan.stance_rows)
                populate_authored_justifications(
                    conn,
                    sidecar_plan.justification_rows,
                )

            conn.commit()
        except Exception as exc:
            try:
                _record_build_exception(conn, exc)
                conn.commit()
            except Exception as diagnostic_error:
                exc.add_note(f"failed to record build diagnostic: {diagnostic_error}")
            try:
                checkpoint_and_close_sqlite(conn)
            except Exception as close_error:
                exc.add_note(f"failed to close failed sidecar build: {close_error}")
            raise

        checkpoint_and_close_sqlite(conn)

    return materialize_sqlite_file(
        output_path,
        content_hash=content_hash,
        build=_write_sidecar,
        force=force,
        publish_failure_when_missing=True,
    ).built


def build_grounding_sidecar(
    repo: "Repository",
    output_path: Path,
    *,
    commit_hash: str | None = None,
) -> None:
    """Materialize the grounding substrate into a sidecar-shaped SQLite file."""

    def _write_grounding(target_path: Path) -> None:
        conn = connect_sidecar(target_path)
        try:
            write_schema_metadata(conn)
            create_grounded_fact_table(conn)
            grounded_bundle = build_grounded_bundle(
                repo,
                commit=commit_hash,
            )
            populate_grounded_facts(conn, grounded_bundle)
            conn.commit()
        except Exception:
            conn.close()
            raise
        checkpoint_and_close_sqlite(conn)

    materialize_sqlite_file(
        output_path,
        content_hash=None,
        build=_write_grounding,
        force=True,
    )
