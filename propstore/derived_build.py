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

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from quire.derived_store import (
    DerivedStoreHandle,
    derived_store_content_hash,
    materialize_sqlite_file,
    read_dependency_pins,
)
from quire.sqlalchemy_store import (
    DerivedSession,
    create_sqlalchemy_store,
    populate_fts_index,
)
from quire.sqlite_vec_store import SqlAlchemyVecSnapshotStore
from sqlalchemy import delete
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
from propstore.families.claims.declaration import (
    PromotionBlockedModels,
    compile_promotion_blocked_models,
)
from propstore.families.diagnostics.declaration import delete_promotion_blocked_diagnostics
from propstore.derived_build_plan import (
    RepositoryCheckedBundle,
    WorldWriteBatch,
    compile_sidecar_build_plan,
)
from propstore.families.embeddings.declaration import (
    EmbeddingSnapshot,
    EmbeddingSnapshotReport,
    extract_embedding_snapshot_from_store,
)
from propstore.families.world_charters import (
    BuildDiagnostic,
    GroundedBundleInput,
    GroundedFact,
    GroundedFactEmptyPredicate,
    WorldMeta,
    PROPSTORE_WORLD_META_KEY,
    PROPSTORE_WORLD_SCHEMA_VERSION,
    world_records,
    world_sqlalchemy_schema,
)
from propstore.families.rules.declaration import (
    _SECTION_NAMES,
    _encode_bundle_input,
)
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
    schema = world_sqlalchemy_schema()
    dependency_pins = read_dependency_pins(
        repo_root / "uv.lock",
        _SIDECAR_CACHE_DEPENDENCIES,
    )
    return {
        "source_revision": source_revision,
        "source_branch_tips": source_branch_tips,
        "sidecar_schema_version": PROPSTORE_WORLD_SCHEMA_VERSION,
        "schema_catalog_hash": schema.catalog_hash,
        "passes": _semantic_pass_versions(),
        "family_contract_versions": _family_contract_versions(),
        "build_time_config": {
            "PROPSTORE_SIDECAR_CACHE_BUST": os.environ.get(
                "PROPSTORE_SIDECAR_CACHE_BUST",
                "",
            ),
        },
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
        schema_hash=str(inputs["schema_catalog_hash"]),
        dependencies=dependencies,
        extra_inputs={
            "source_revision": inputs["source_revision"],
            "source_branch_tips": inputs["source_branch_tips"],
            "schema_catalog_hash": inputs["schema_catalog_hash"],
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
    schema = world_sqlalchemy_schema()
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
        drop_invalid_context_lifting_rows=bool(context_diagnostics),
    )
    promotion_blocked_rows = compile_promotion_blocked_models(
        collect_all_source_promotion_blocked_facts(repo)
    )

    embedding_snapshot = extract_embedding_snapshot_from_store(
        output_path,
        on_snapshot=on_embedding_snapshot,
    )

    def _write_sidecar(target_path: Path) -> None:
        create_sqlalchemy_store(target_path, schema)
        build_handle = DerivedStoreHandle(
            projection_id="propstore.world",
            source_commit=str(source_revision),
            content_hash=content_hash,
            cache_key="direct-build",
            path=target_path,
        )
        try:
            with build_handle.writable_session(schema) as derived:
                derived.add(WorldMeta(
                    key=PROPSTORE_WORLD_META_KEY,
                    schema_version=PROPSTORE_WORLD_SCHEMA_VERSION,
                ))
                _add_write_batches(derived, sidecar_plan.write_batches)
                derived.add_all(_pass_diagnostic_records(
                    form_diagnostics,
                    kind="form",
                    diagnostic_kind="form_validation",
                    prefer_filename=True,
                ))
                derived.add_all(_pass_diagnostic_records(
                    concept_diagnostics,
                    kind="concept",
                    diagnostic_kind="concept_validation",
                ))
                derived.add_all(_pass_diagnostic_records(
                    context_diagnostics,
                    kind="context",
                    diagnostic_kind="context_validation",
                ))
                derived.add_all(_pass_diagnostic_records(
                    tuple(recorded_claim_diagnostics),
                    kind="claim",
                    diagnostic_kind="claim_validation",
                ))
                derived.add_all(_authoring_diagnostic_records(authoring_diagnostics))
                derived.add_all(_quarantine_diagnostic_records(
                    sidecar_plan.quarantine_diagnostics
                ))

                _flush_promotion_blocked_claims(derived, promotion_blocked_rows)

                grounded_bundle = build_grounded_bundle(
                    repo,
                    commit=commit_hash,
                )
                derived.add_all(_grounded_bundle_records(grounded_bundle))

                derived.flush()
                populate_fts_index(derived, "concept_fts")
                if sidecar_plan.has_claim_rows:
                    populate_fts_index(derived, "claim_fts")

                if embedding_snapshot is not None:
                    try:
                        _restore_embedding_snapshot(derived, embedding_snapshot)
                    except ImportError as exc:
                        derived.add(_embedding_restore_diagnostic_record(exc))
                    except Exception as exc:
                        derived.add(_embedding_restore_diagnostic_record(exc))

                derived.commit()
        except Exception as exc:
            try:
                with build_handle.writable_session(schema) as derived:
                    derived.rollback()
                    derived.add(_build_exception_record(exc))
                    derived.commit()
            except Exception as diagnostic_error:
                exc.add_note(f"failed to record build diagnostic: {diagnostic_error}")
            raise

    return materialize_sqlite_file(
        output_path,
        content_hash=content_hash,
        build=_write_sidecar,
        force=force,
        publish_failure_when_missing=True,
    ).built


def _add_write_batches(
    derived: DerivedSession,
    batches: tuple[WorldWriteBatch, ...],
) -> None:
    for batch in batches:
        derived.add_all(batch.objects)


def _pass_diagnostic_records(
    diagnostics: tuple[PassDiagnostic, ...],
    *,
    kind: str,
    diagnostic_kind: str,
    prefer_filename: bool = False,
) -> tuple[BuildDiagnostic, ...]:
    records: list[BuildDiagnostic] = []
    for diagnostic in diagnostics:
        if not diagnostic.is_error:
            continue
        artifact_id = (
            diagnostic.filename or diagnostic.artifact_id or "unknown"
            if prefer_filename
            else diagnostic.artifact_id or diagnostic.filename or "unknown"
        )
        records.append(_quarantine_record(
            artifact_id=artifact_id,
            kind=kind,
            diagnostic_kind=diagnostic_kind,
            message=diagnostic.render(),
            file=diagnostic.filename,
        ))
    return tuple(records)


def _authoring_diagnostic_records(
    diagnostics: tuple[PassDiagnostic, ...],
) -> tuple[BuildDiagnostic, ...]:
    return tuple(
        BuildDiagnostic(
            claim_id=diagnostic.artifact_id,
            source_kind="authoring",
            source_ref=diagnostic.artifact_id or diagnostic.filename,
            diagnostic_kind=diagnostic.code,
            severity=diagnostic.level,
            blocking=1 if diagnostic.is_error else 0,
            message=diagnostic.render(),
            file=diagnostic.filename,
            detail_json=None,
        )
        for diagnostic in diagnostics
    )


def _quarantine_diagnostic_records(
    diagnostics: tuple[object, ...],
) -> tuple[BuildDiagnostic, ...]:
    return tuple(
        _quarantine_record(
            artifact_id=str(getattr(diagnostic, "artifact_id")),
            kind=str(getattr(diagnostic, "kind")),
            diagnostic_kind=str(getattr(diagnostic, "diagnostic_kind")),
            message=str(getattr(diagnostic, "message")),
            file=getattr(diagnostic, "file"),
        )
        for diagnostic in diagnostics
    )


def _quarantine_record(
    *,
    artifact_id: str,
    kind: str,
    diagnostic_kind: str,
    message: str,
    file: str | None,
) -> BuildDiagnostic:
    return BuildDiagnostic(
        claim_id=artifact_id if kind == "claim" else None,
        source_kind=kind,
        source_ref=artifact_id,
        diagnostic_kind=diagnostic_kind,
        severity="error",
        blocking=1,
        message=message,
        file=file,
        detail_json=json.dumps(
            {
                "artifact_id": artifact_id,
                "kind": kind,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
    )


def _flush_promotion_blocked_claims(
    derived: DerivedSession,
    rows: PromotionBlockedModels,
) -> None:
    claim_objects_by_id = {
        str(getattr(row, "id")): row
        for row in world_records("claim_core", rows.claims)
    }
    claim_objects = tuple(claim_objects_by_id.values())
    diagnostic_objects = world_records("build_diagnostics", rows.diagnostics)
    if not claim_objects and not diagnostic_objects:
        return
    claim_ids = tuple(str(getattr(row, "id")) for row in claim_objects)
    diagnostic_claim_ids = tuple(
        sorted(
            {
                str(claim_id)
                for row in diagnostic_objects
                if getattr(row, "diagnostic_kind", None) == "promotion_blocked"
                for claim_id in (getattr(row, "claim_id", None),)
                if claim_id
            }
        )
    )
    if claim_ids:
        derived.flush()
        _delete_claim_children(derived, claim_ids)
    for claim_id in sorted(set(claim_ids) | set(diagnostic_claim_ids)):
        delete_promotion_blocked_diagnostics(derived, claim_id)
    derived.add_all(claim_objects)
    derived.add_all(diagnostic_objects)


def _delete_claim_children(
    derived: DerivedSession,
    claim_ids: tuple[str, ...],
) -> None:
    schema = derived.schema
    session = derived.session
    for table_name in (
        "claim_concept_link",
        "claim_numeric_payload",
        "claim_text_payload",
        "claim_algorithm_payload",
        "micropublication_claim",
    ):
        table = schema.tables.get(table_name)
        if table is None or "claim_id" not in table.c:
            continue
        session.execute(delete(table).where(table.c.claim_id.in_(claim_ids)))
    claim_core = schema.tables["claim_core"]
    session.execute(delete(claim_core).where(claim_core.c.id.in_(claim_ids)))
    diagnostics = schema.tables["build_diagnostics"]
    session.execute(
        delete(diagnostics).where(
            diagnostics.c.claim_id.in_(claim_ids),
            diagnostics.c.diagnostic_kind == "promotion_blocked",
        )
    )


def _grounded_bundle_records(bundle: object) -> tuple[object, ...]:
    records: list[object] = []
    sections = getattr(bundle, "sections")
    for section_name in _SECTION_NAMES:
        inner_map = sections.get(section_name)
        if inner_map is None:
            continue
        for predicate_id in sorted(inner_map.keys()):
            rows = inner_map[predicate_id]
            if not rows:
                records.append(GroundedFactEmptyPredicate(
                    section=section_name,
                    predicate=predicate_id,
                ))
                continue
            for encoded_arguments in sorted(json.dumps(list(arg_tuple)) for arg_tuple in rows):
                records.append(GroundedFact(
                    predicate=predicate_id,
                    arguments=encoded_arguments,
                    section=section_name,
                ))
    records.extend(_grounded_bundle_input_records(bundle))
    return tuple(records)


def _grounded_bundle_input_records(bundle: object) -> tuple[GroundedBundleInput, ...]:
    rows = (
        ("source_rule", getattr(bundle, "source_rules")),
        ("source_superiority", getattr(bundle, "source_superiority")),
        ("source_fact", getattr(bundle, "source_facts")),
        ("argument", getattr(bundle, "arguments")),
    )
    return tuple(
        GroundedBundleInput(
            kind=kind,
            position=position,
            payload=_encode_bundle_input(kind, value),
        )
        for kind, values in rows
        for position, value in enumerate(values)
    )


def _restore_embedding_snapshot(
    derived: DerivedSession,
    snapshot: EmbeddingSnapshot,
) -> object | None:
    caches = tuple(derived.schema.vector_caches.values())
    if not caches:
        return None
    return SqlAlchemyVecSnapshotStore(
        derived.session.connection(),
        caches,
    ).restore(snapshot.to_vec_snapshot())


def _embedding_restore_diagnostic_record(exc: Exception) -> BuildDiagnostic:
    return BuildDiagnostic(
        claim_id=None,
        source_kind="embedding",
        source_ref="restore",
        diagnostic_kind="embedding_restore",
        severity="warning",
        blocking=0,
        message=f"embedding restore failed: {exc}",
        file=None,
        detail_json=None,
    )


def _build_exception_record(exc: Exception) -> BuildDiagnostic:
    return BuildDiagnostic(
        claim_id=None,
        source_kind="sidecar_build",
        source_ref=None,
        diagnostic_kind="build_exception",
        severity="error",
        blocking=1,
        message=str(exc),
        file=None,
        detail_json=None,
    )


def build_grounding_sidecar(
    repo: "Repository",
    output_path: Path,
    *,
    commit_hash: str | None = None,
) -> None:
    """Materialize the grounding substrate into a sidecar-shaped SQLite file."""

    def _write_grounding(target_path: Path) -> None:
        schema = world_sqlalchemy_schema()
        create_sqlalchemy_store(target_path, schema)
        build_handle = DerivedStoreHandle(
            projection_id="propstore.world.grounding",
            source_commit="" if commit_hash is None else str(commit_hash),
            content_hash="",
            cache_key="direct-grounding-build",
            path=target_path,
        )
        with build_handle.writable_session(schema) as derived:
            derived.add(WorldMeta(
                key=PROPSTORE_WORLD_META_KEY,
                schema_version=PROPSTORE_WORLD_SCHEMA_VERSION,
            ))
            grounded_bundle = build_grounded_bundle(
                repo,
                commit=commit_hash,
            )
            derived.add_all(_grounded_bundle_records(grounded_bundle))
            derived.commit()

    materialize_sqlite_file(
        output_path,
        content_hash=None,
        build=_write_grounding,
        force=True,
    )
