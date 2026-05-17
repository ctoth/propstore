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
from quire.derived_runtime import connect_sqlite_store
from quire.derived_runtime import write_derived_store_schema_metadata
from propstore.claims import ClaimFileEntry
from propstore.compiler.context import (
    build_compilation_context_from_loaded,
)
from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY
from propstore.families.claims.passes import register_claim_pipeline, run_claim_pipeline
from propstore.families.claims.stages import ClaimAuthoredFiles, ClaimCheckedBundle
from propstore.families.contexts.declaration import (
    filter_invalid_context_lifting_rows,
    populate_contexts,
)
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
from propstore.families.claims.declaration import (
    CLAIM_FTS_PROJECTION,
    compile_promotion_blocked_sidecar_rows,
    populate_authored_justifications,
    populate_claims,
    populate_conflicts,
    populate_promotion_blocked_claims,
    populate_raw_id_quarantine_records,
    populate_stances,
)
from propstore.derived_build_plan import RepositoryCheckedBundle, compile_sidecar_build_plan
from propstore.families.concepts.declaration import CONCEPT_FTS_PROJECTION, populate_concept_sidecar_rows
from propstore.families.diagnostics.declaration import (
    record_authoring_diagnostics,
    record_build_exception,
    record_embedding_restore_diagnostic,
    record_pass_diagnostics,
    record_quarantine_diagnostics,
)
from propstore.families.embeddings.declaration import (
    EmbeddingSnapshotReport,
    extract_embedding_snapshot_from_store,
    restore_embedding_snapshot,
)
from propstore.families.projection_catalog import (
    PROPSTORE_WORLD_META_KEY,
    PROPSTORE_WORLD_PROJECTION_SCHEMA,
    PROPSTORE_WORLD_SCHEMA_VERSION,
)
from propstore.families.micropublications.declaration import populate_micropublications
from propstore.families.rules.declaration import (
    create_grounded_fact_table,
    populate_grounded_facts,
)
from propstore.families.sources.declaration import populate_sources
from propstore.compiler.context import build_authored_concept_registry
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.types import PassDiagnostic
from propstore.source.promote import collect_all_source_promotion_blocked_facts

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


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def world_sidecar_hash_inputs(
    source_revision: str,
    *,
    source_branch_tips: tuple[tuple[str, str], ...] = (),
) -> dict[str, object]:
    repo_root = _repo_root()
    dependency_pins = read_dependency_pins(
        repo_root / "uv.lock",
        _SIDECAR_CACHE_DEPENDENCIES,
    )
    return {
        "source_revision": source_revision,
        "source_branch_tips": source_branch_tips,
        "sidecar_schema_version": PROPSTORE_WORLD_SCHEMA_VERSION,
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
        _repo_root() / "uv.lock",
        _SIDECAR_CACHE_DEPENDENCIES,
    )
    content_hash = derived_store_content_hash(
        projection_version=str(PROPSTORE_WORLD_SCHEMA_VERSION),
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
    promotion_blocked_rows = compile_promotion_blocked_sidecar_rows(
        collect_all_source_promotion_blocked_facts(repo)
    )

    embedding_snapshot = extract_embedding_snapshot_from_store(
        output_path,
        on_snapshot=on_embedding_snapshot,
    )

    def _write_sidecar(target_path: Path) -> None:
        conn = connect_sqlite_store(target_path)
        try:
            write_derived_store_schema_metadata(
                conn,
                schema_version=PROPSTORE_WORLD_SCHEMA_VERSION,
                key=PROPSTORE_WORLD_META_KEY,
            )
            PROPSTORE_WORLD_PROJECTION_SCHEMA.create_all(conn)
            populate_sources(
                conn,
                sidecar_plan.source_rows,
            )
            populate_concept_sidecar_rows(
                conn,
                sidecar_plan.concept_rows,
            )
            CONCEPT_FTS_PROJECTION.populate_from_source_query(conn)
            record_pass_diagnostics(
                conn,
                form_diagnostics,
                kind="form",
                diagnostic_kind="form_validation",
                prefer_filename=True,
            )
            record_pass_diagnostics(
                conn,
                concept_diagnostics,
                kind="concept",
                diagnostic_kind="concept_validation",
            )
            record_pass_diagnostics(
                conn,
                context_diagnostics,
                kind="context",
                diagnostic_kind="context_validation",
            )
            record_pass_diagnostics(
                conn,
                tuple(recorded_claim_diagnostics),
                kind="claim",
                diagnostic_kind="claim_validation",
            )
            record_authoring_diagnostics(conn, authoring_diagnostics)
            record_quarantine_diagnostics(conn, sidecar_plan.quarantine_diagnostics)
            context_rows = (
                filter_invalid_context_lifting_rows(sidecar_plan.context_rows)
                if context_diagnostics
                else sidecar_plan.context_rows
            )
            if context_rows.context_rows:
                populate_contexts(
                    conn,
                    context_rows=context_rows.context_rows,
                    assumption_rows=context_rows.assumption_rows,
                    lifting_rule_rows=context_rows.lifting_rule_rows,
                    lifting_materialization_rows=context_rows.lifting_materialization_rows,
                )

            if sidecar_plan.claim_rows is not None:
                populate_claims(conn, sidecar_plan.claim_rows)

                if sidecar_plan.raw_id_quarantine_rows.claim_rows:
                    populate_raw_id_quarantine_records(
                        conn,
                        sidecar_plan.raw_id_quarantine_rows,
                    )

                populate_promotion_blocked_claims(
                    conn,
                    promotion_blocked_rows.claim_rows,
                    promotion_blocked_rows.diagnostic_rows,
                )

                populate_conflicts(conn, sidecar_plan.conflict_rows)
                CLAIM_FTS_PROJECTION.populate_from_source_query(conn)
            else:
                populate_promotion_blocked_claims(
                    conn,
                    promotion_blocked_rows.claim_rows,
                    promotion_blocked_rows.diagnostic_rows,
                )

            populate_micropublications(conn, sidecar_plan.micropublication_rows)

            grounded_bundle = build_grounded_bundle(
                repo,
                commit=commit_hash,
            )
            populate_grounded_facts(conn, grounded_bundle)

            if embedding_snapshot is not None:
                try:
                    restore_embedding_snapshot(conn, embedding_snapshot)
                except ImportError as exc:
                    record_embedding_restore_diagnostic(conn, exc)
                except Exception as exc:
                    record_embedding_restore_diagnostic(conn, exc)

            if sidecar_plan.claim_rows is not None:
                populate_stances(conn, sidecar_plan.stance_rows)
                populate_authored_justifications(
                    conn,
                    sidecar_plan.justification_rows,
                )

            conn.commit()
        except Exception as exc:
            try:
                record_build_exception(conn, exc)
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
        conn = connect_sqlite_store(target_path)
        try:
            write_derived_store_schema_metadata(
                conn,
                schema_version=PROPSTORE_WORLD_SCHEMA_VERSION,
                key=PROPSTORE_WORLD_META_KEY,
            )
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
