"""Repository-level compiler workflows.

This module owns validation/build orchestration. CLI modules are responsible
for presenting these reports, not for deciding which compiler passes run.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable
from quire.derived_store import (
    DerivedStoreHandle,
    derived_store_content_hash,
    materialize_sqlite_file,
    read_dependency_pins,
)
from quire.documents import DocumentSchemaError
from quire.sqlalchemy_store import create_sqlalchemy_store, populate_fts_index
from propstore.claims import LoadedClaimsFile, claim_file_payload
from propstore.compiler.context import (
    build_authored_concept_registry,
    build_compiler_claim_index,
    build_compilation_context_from_loaded,
    build_compilation_context_from_repo,
)
from propstore.compiler.errors import CompilerWorkflowError
from propstore.families.claims.passes import run_claim_pipeline
from propstore.families.claims.references import build_claim_file_reference_index
from propstore.families.claims.stages import ClaimAuthoredFiles, ClaimCheckedBundle, ClaimStage
from propstore.families.claims.declaration import (
    compile_authored_justification_models_with_diagnostics,
    compile_claim_models,
    compile_promotion_blocked_models,
    compile_raw_id_quarantine_models,
    write_promotion_blocked_models,
)
from propstore.families.concepts.passes import (
    ConceptPipelineContext,
    run_concept_pipeline,
)
from propstore.families.concepts.declaration import (
    compile_concept_sidecar_rows,
)
from propstore.families.contexts.passes import run_context_pipeline
from propstore.families.contexts.stages import (
    ContextCheckedGraph,
    ContextStage,
    LoadedContext,
    loaded_contexts_to_lifting_system,
    parse_context_record_document,
)
from propstore.families.contexts.declaration import (
    compile_context_models,
    filter_invalid_context_lifting_models,
)
from propstore.families.concepts.stages import (
    ConceptCheckedRegistry,
    ConceptStage,
    LoadedConcept,
    parse_concept_record_document,
)
from propstore.families.forms.passes import run_form_pipeline
from propstore.families.forms.stages import FormCheckedRegistry, FormStage, LoadedForm
from propstore.families.micropublications.declaration import (
    compile_micropublication_models_with_diagnostics,
)
from propstore.families.relations.declaration import (
    compile_authored_stance_models_with_diagnostics,
    compile_claim_embedded_stance_models_for_claims_with_diagnostics,
    compile_conflict_witness_models,
)
from propstore.families.registry import PropstoreFamily
from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY
from propstore.families.sources.declaration import compile_source_models
from propstore.families.diagnostics.declaration import (
    build_authoring_diagnostics,
    build_pass_diagnostics,
    build_quarantine_diagnostics,
    embedding_restore_diagnostic,
    sidecar_build_exception_diagnostic,
)
from propstore.families.embeddings.declaration import (
    EmbeddingSnapshotReport,
    extract_embedding_snapshot,
    restore_embedding_snapshot_to_session,
)
from propstore.families.world_charters import (
    PROPSTORE_WORLD_META_KEY,
    PROPSTORE_WORLD_SCHEMA_VERSION,
    WorldMeta,
    world_sqlalchemy_schema,
)
from propstore.grounding.loading import build_grounded_bundle
from propstore.repository import Repository
from propstore.semantic_passes.types import PassDiagnostic
from propstore.families.diagnostics.authoring_lints import collect_authoring_lints
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.families.claims.passes import register_claim_pipeline
from propstore.families.concepts.passes import register_concept_pipeline
from propstore.families.contexts.passes import register_context_pipeline
from propstore.families.forms.passes import register_form_pipeline
from propstore.source.promote import collect_all_source_promotion_blocked_facts
from propstore.families.rules.declaration import persist_grounded_bundle


@dataclass(frozen=True)
class RepositoryValidationSummary:
    concept_count: int
    claim_file_count: int
    messages: tuple[PassDiagnostic, ...]
    no_concepts: bool = False

    @property
    def errors(self) -> tuple[PassDiagnostic, ...]:
        return tuple(message for message in self.messages if message.level == "error")

    @property
    def warnings(self) -> tuple[PassDiagnostic, ...]:
        return tuple(message for message in self.messages if message.level == "warning")

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class BuildConflictLine:
    warning_class: str
    concept_id: str
    claim_a_id: str
    claim_b_id: str


@dataclass(frozen=True)
class BuildPhiGroup:
    key: str
    claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class BuildEmbeddingSnapshotReport:
    model_count: int
    claim_vector_count: int
    concept_vector_count: int


@dataclass(frozen=True)
class BuildDerivedStoreHandle:
    projection_id: str
    source_commit: str
    cache_key: str
    path: str


@dataclass(frozen=True)
class RepositoryBuildReport:
    concept_count: int
    claim_count: int
    conflict_count: int
    phi_node_count: int
    warning_count: int
    rebuilt: bool
    conflicts: tuple[BuildConflictLine, ...] = ()
    phi_groups: tuple[BuildPhiGroup, ...] = ()
    embedding_snapshot: BuildEmbeddingSnapshotReport | None = None
    derived_store: BuildDerivedStoreHandle | None = None
    messages: tuple[PassDiagnostic, ...] = ()
    no_concepts: bool = False
    sidecar_missing: bool = False


_WORLD_STORE_CACHE_DEPENDENCIES = (
    "argumentation",
    "ast-equiv",
    "bridgman",
    "gunray",
    "quire",
)


def build_repository_world_store(
    repo: Repository,
    *,
    force: bool = False,
    commit_hash: str | None = None,
    compilation_context=None,
    claim_checked_bundle: ClaimCheckedBundle | None = None,
    claim_files: tuple[LoadedClaimsFile, ...] | None = None,
    claim_diagnostics: tuple[PassDiagnostic, ...] = (),
    concept_files: tuple[LoadedConcept, ...] | None = None,
    concept_diagnostics: tuple[PassDiagnostic, ...] = (),
    context_files: tuple[LoadedContext, ...] | None = None,
    context_diagnostics: tuple[PassDiagnostic, ...] = (),
    authoring_diagnostics: tuple[PassDiagnostic, ...] = (),
    on_embedding_snapshot: Callable[[EmbeddingSnapshotReport], None] | None = None,
) -> tuple[DerivedStoreHandle, bool]:
    with repo.mutation_guard():
        source_revision = commit_hash or repo.require_git().head_sha()
        if source_revision is None:
            raise ValueError(
                "world store materialization requires a committed git repository"
            )
        content_hash = _world_store_content_hash(repo, str(source_revision))

        def build(target: Path) -> None:
            write_repository_world_store(
                repo,
                target,
                force=True,
                commit_hash=str(source_revision),
                compilation_context=compilation_context,
                claim_checked_bundle=claim_checked_bundle,
                claim_files=claim_files,
                claim_diagnostics=claim_diagnostics,
                concept_files=concept_files,
                concept_diagnostics=concept_diagnostics,
                context_files=context_files,
                context_diagnostics=context_diagnostics,
                authoring_diagnostics=authoring_diagnostics,
                on_embedding_snapshot=on_embedding_snapshot,
            )

        materialization = repo.derived_stores.materialize_with_report(
            projection_id="propstore.world",
            source_commit=str(source_revision),
            content_hash=content_hash,
            build=build,
            force=force,
        )
        return materialization.handle, materialization.built


def write_repository_world_store(
    repo: Repository,
    output_path: Path,
    *,
    force: bool = False,
    commit_hash: str | None = None,
    compilation_context=None,
    claim_checked_bundle: ClaimCheckedBundle | None = None,
    claim_files: tuple[LoadedClaimsFile, ...] | None = None,
    claim_diagnostics: tuple[PassDiagnostic, ...] = (),
    concept_files: tuple[LoadedConcept, ...] | None = None,
    concept_diagnostics: tuple[PassDiagnostic, ...] = (),
    context_files: tuple[LoadedContext, ...] | None = None,
    context_diagnostics: tuple[PassDiagnostic, ...] = (),
    authoring_diagnostics: tuple[PassDiagnostic, ...] = (),
    on_embedding_snapshot: Callable[[EmbeddingSnapshotReport], None] | None = None,
) -> bool:
    with repo.mutation_guard():
        source_revision = commit_hash or repo.require_git().head_sha()
        if source_revision is None:
            raise ValueError(
                "world store build requires a committed git repository or commit_hash"
            )
        content_hash = _world_store_content_hash(repo, str(source_revision))

        def build(target: Path) -> None:
            _write_repository_world_store_file(
                repo,
                target,
                source_revision=str(source_revision),
                commit_hash=commit_hash,
                compilation_context=compilation_context,
                claim_checked_bundle=claim_checked_bundle,
                claim_files=claim_files,
                claim_diagnostics=claim_diagnostics,
                concept_files=concept_files,
                concept_diagnostics=concept_diagnostics,
                context_files=context_files,
                context_diagnostics=context_diagnostics,
                authoring_diagnostics=authoring_diagnostics,
                on_embedding_snapshot=on_embedding_snapshot,
                content_hash=content_hash,
            )

        return materialize_sqlite_file(
            output_path,
            content_hash=content_hash,
            build=build,
            force=force,
            publish_failure_when_missing=True,
        ).built


def _world_store_content_hash(repo: Repository, source_revision: str) -> str:
    schema = world_sqlalchemy_schema()
    dependencies = read_dependency_pins(
        _repo_root() / "uv.lock",
        _WORLD_STORE_CACHE_DEPENDENCIES,
    )
    content_hash = derived_store_content_hash(
        projection_version=str(PROPSTORE_WORLD_SCHEMA_VERSION),
        schema_hash=schema.catalog_hash,
        dependencies=dependencies,
        extra_inputs={
            "source_revision": source_revision,
            "source_branch_tips": _source_branch_tips(repo),
            "generated_schema_version": schema.catalog_hash,
            "schema_catalog_hash": schema.catalog_hash,
            "passes": _semantic_pass_versions(),
            "family_contract_versions": _family_contract_versions(),
            "build_time_config": {
                "PROPSTORE_SIDECAR_CACHE_BUST": os.environ.get(
                    "PROPSTORE_SIDECAR_CACHE_BUST",
                    "",
                ),
            },
        },
    )
    return content_hash.removeprefix("sha256:")


def _source_branch_tips(repo: Repository) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (branch.name, branch.tip_sha)
            for branch in repo.snapshot.iter_branches()
            if branch.kind == "source"
        )
    )


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


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _write_repository_world_store_file(
    repo: Repository,
    output_path: Path,
    *,
    source_revision: str,
    commit_hash: str | None,
    compilation_context,
    claim_checked_bundle: ClaimCheckedBundle | None,
    claim_files: tuple[LoadedClaimsFile, ...] | None,
    claim_diagnostics: tuple[PassDiagnostic, ...],
    concept_files: tuple[LoadedConcept, ...] | None,
    concept_diagnostics: tuple[PassDiagnostic, ...],
    context_files: tuple[LoadedContext, ...] | None,
    context_diagnostics: tuple[PassDiagnostic, ...],
    authoring_diagnostics: tuple[PassDiagnostic, ...],
    on_embedding_snapshot: Callable[[EmbeddingSnapshotReport], None] | None,
    content_hash: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree = repo.tree(commit=commit_hash)
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
            LoadedClaimsFile(
                filename=handle.ref.artifact_id,
                artifact_path=tree / handle.address.require_path(),
                store_root=tree,
                document=handle.document,
            )
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
        for c in context_files
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
    claim_bundle = None if claim_checked_bundle is None else claim_checked_bundle.bundle
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
        tuple(claim_bundle.normalized_claim_files)
        if claim_bundle is not None
        else None
    )
    source_models = compile_source_models(
        (
            (handle.ref.name, handle.document)
            for handle in repo.families.sources.iter_handles(commit=commit_hash)
        )
    )
    source_slugs = frozenset(str(source.slug) for source in source_models)
    concept_models = compile_concept_sidecar_rows(
        concepts,
        form_registry,
        dict(compilation_context.cel_registry),
    )
    context_models = compile_context_models(context_files)
    if context_diagnostics:
        context_models = filter_invalid_context_lifting_models(context_models)
    raw_id_quarantine_models = compile_raw_id_quarantine_models(())
    claim_models = None
    conflict_models: tuple[object, ...] = ()
    stance_models: tuple[object, ...] = ()
    justification_models: tuple[object, ...] = ()
    quarantine_diagnostics = ()
    claim_index = build_claim_file_reference_index(())
    if normalized_claim_files is not None:
        if claim_checked_bundle is None:
            raise ValueError("checked claim bundle is required to populate claims")
        claim_index = build_claim_file_reference_index(normalized_claim_files)
        claim_models = compile_claim_models(
            claim_checked_bundle.bundle,
            concept_registry,
            form_registry=form_registry,
            source_slugs=source_slugs,
        )
        quarantine_diagnostics = claim_models.quarantine_diagnostics
        raw_id_quarantine_models = compile_raw_id_quarantine_models(
            claim_checked_bundle.raw_id_quarantine_records
        )
        lifting_system = (
            loaded_contexts_to_lifting_system(list(context_files))
            if context_files
            else None
        )
        conflict_models = compile_conflict_witness_models(
            list(normalized_claim_files),
            concept_registry,
            dict(compilation_context.cel_registry),
            lifting_system=lifting_system,
        )
        authored_stance_models, stance_quarantine = (
            compile_authored_stance_models_with_diagnostics(
                (
                    (handle.ref.artifact_id, handle.document)
                    for handle in repo.families.stances.iter_handles(commit=commit_hash)
                ),
                claim_index,
            )
        )
        embedded_stance_models, embedded_stance_quarantine = (
            compile_claim_embedded_stance_models_for_claims_with_diagnostics(
                (
                    semantic_claim
                    for semantic_file in claim_checked_bundle.bundle.semantic_files
                    for semantic_claim in semantic_file.claims
                ),
                claim_index,
            )
        )
        stance_models = authored_stance_models + embedded_stance_models
        justification_models, justification_quarantine = (
            compile_authored_justification_models_with_diagnostics(
                (
                    (handle.ref.artifact_id, handle.document)
                    for handle in repo.families.justifications.iter_handles(
                        commit=commit_hash
                    )
                ),
                claim_index,
            )
        )
        quarantine_diagnostics = (
            quarantine_diagnostics
            + stance_quarantine
            + embedded_stance_quarantine
            + justification_quarantine
        )
    micropublication_models, micropublication_quarantine = (
        compile_micropublication_models_with_diagnostics(
            (
                (handle.ref.artifact_id, handle.document)
                for handle in repo.families.micropubs.iter_handles(commit=commit_hash)
            ),
            claim_index,
        )
    )
    quarantine_diagnostics = quarantine_diagnostics + micropublication_quarantine
    promotion_blocked_models = compile_promotion_blocked_models(
        collect_all_source_promotion_blocked_facts(repo)
    )
    embedding_snapshot = extract_embedding_snapshot(
        output_path,
        on_snapshot=on_embedding_snapshot,
    )
    schema = world_sqlalchemy_schema()

    def write(target_path: Path) -> None:
        create_sqlalchemy_store(target_path, schema)
        build_handle = DerivedStoreHandle(
            projection_id="propstore.world",
            source_commit=source_revision,
            content_hash=content_hash,
            cache_key="direct-build",
            path=target_path,
        )
        try:
            with build_handle.writable_session(schema) as derived:
                derived.add(
                    WorldMeta(
                        key=PROPSTORE_WORLD_META_KEY,
                        schema_version=PROPSTORE_WORLD_SCHEMA_VERSION,
                    )
                )
                derived.add_all(source_models)
                derived.add_all(concept_models.form_rows)
                derived.add_all(concept_models.concept_rows)
                derived.add_all(concept_models.alias_rows)
                derived.add_all(concept_models.relationship_rows)
                derived.add_all(concept_models.relation_edge_rows)
                derived.add_all(concept_models.parameterization_rows)
                derived.add_all(concept_models.parameterization_group_rows)
                derived.add_all(concept_models.form_algebra_rows)
                contexts, assumptions, lifting_rules, lifting_materializations = (
                    context_models
                )
                derived.add_all(contexts)
                derived.add_all(assumptions)
                derived.add_all(lifting_rules)
                derived.add_all(lifting_materializations)
                if claim_models is not None:
                    derived.add_all(claim_models.claims)
                    derived.add_all(claim_models.numeric_payloads)
                    derived.add_all(claim_models.text_payloads)
                    derived.add_all(claim_models.algorithm_payloads)
                    derived.add_all(claim_models.source_assertions)
                    derived.add_all(claim_models.concept_links)
                derived.add_all(raw_id_quarantine_models.claims)
                derived.add_all(raw_id_quarantine_models.diagnostics)
                derived.add_all(conflict_models)
                micropublications, micropublication_claims = micropublication_models
                derived.add_all(micropublications)
                derived.add_all(micropublication_claims)
                derived.add_all(stance_models)
                derived.add_all(justification_models)
                derived.add_all(
                    build_pass_diagnostics(
                        form_result.diagnostics,
                        kind="form",
                        diagnostic_kind="form_validation",
                        prefer_filename=True,
                    )
                )
                derived.add_all(
                    build_pass_diagnostics(
                        concept_diagnostics,
                        kind="concept",
                        diagnostic_kind="concept_validation",
                    )
                )
                derived.add_all(
                    build_pass_diagnostics(
                        context_diagnostics,
                        kind="context",
                        diagnostic_kind="context_validation",
                    )
                )
                derived.add_all(
                    build_pass_diagnostics(
                        tuple(recorded_claim_diagnostics),
                        kind="claim",
                        diagnostic_kind="claim_validation",
                    )
                )
                derived.add_all(build_authoring_diagnostics(authoring_diagnostics))
                derived.add_all(build_quarantine_diagnostics(quarantine_diagnostics))
                write_promotion_blocked_models(derived, promotion_blocked_models)
                persist_grounded_bundle(
                    derived,
                    build_grounded_bundle(repo, commit=commit_hash),
                )
                derived.flush()
                populate_fts_index(derived, "concept_fts")
                if claim_models is not None:
                    populate_fts_index(derived, "claim_fts")
                if embedding_snapshot is not None:
                    try:
                        restore_embedding_snapshot_to_session(
                            derived,
                            embedding_snapshot,
                        )
                    except ImportError as exc:
                        derived.add(embedding_restore_diagnostic(exc))
                    except Exception as exc:
                        derived.add(embedding_restore_diagnostic(exc))
                derived.commit()
        except Exception as exc:
            try:
                with build_handle.writable_session(schema) as derived:
                    derived.rollback()
                    derived.add(sidecar_build_exception_diagnostic(exc))
                    derived.commit()
            except Exception as diagnostic_error:
                exc.add_note(f"failed to record build diagnostic: {diagnostic_error}")
            raise

    write(output_path)


def _workflow_diagnostic(
    family: PropstoreFamily,
    stage,
    message: str,
    *,
    code: str = "workflow.error",
) -> PassDiagnostic:
    return PassDiagnostic(
        level="error",
        code=code,
        message=message,
        family=family,
        stage=stage,
    )


def _enforce_cel_structural_invariants(
    claim_files,
    ctx_records,
    cel_registry,
) -> None:
    """Pre-pass: fail early if any CEL expression references a structural concept.

    This is a safety net for YAML that bypassed the CLI ingest boundary
    (direct file edits, migrations, external tooling). Mirrors the
    ingest-time check in ``propstore.source.claims.commit_source_claims_batch``
    and ``propstore.app.contexts.add_context`` so the same invariant is
    enforced uniformly regardless of how the artifact reached the tree.

    Raises :class:`CompilerWorkflowError` with one diagnostic per offense.
    """
    from propstore.cel_validation import (
        CelIngestValidationError,
        iter_claim_condition_expressions,
        iter_context_assumption_expressions,
        validate_cel_expressions,
    )
    from propstore.claims import claim_file_claims, claim_file_source_paper, claim_file_filename

    diagnostics: list[PassDiagnostic] = []

    def _record(family, stage, message: str, *, filename: str | None, artifact_id: str | None):
        diagnostics.append(
            PassDiagnostic(
                level="error",
                code="cel.structural_in_expression",
                message=message,
                family=family,
                stage=stage,
                filename=filename,
                artifact_id=artifact_id,
                pass_name="compiler.validate_cel_structural_invariants",
            )
        )

    for claim_file in claim_files or ():
        paper = claim_file_source_paper(claim_file)
        filename = claim_file_filename(claim_file)
        for claim in claim_file_claims(claim_file):
            if not claim.conditions:
                continue
            claim_label = claim.id or "<unnamed>"
            artifact_label = f"claim '{claim_label}' in paper '{paper}'"
            try:
                validate_cel_expressions(
                    iter_claim_condition_expressions(
                        [str(condition) for condition in claim.conditions],
                        artifact_label=artifact_label,
                    ),
                    cel_registry,
                )
            except CelIngestValidationError as exc:
                _record(
                    PropstoreFamily.CLAIMS,
                    ClaimStage.AUTHORED,
                    str(exc),
                    filename=filename,
                    artifact_id=claim.id,
                )

    for record in ctx_records or ():
        if not record.assumptions:
            continue
        context_id = (
            str(record.context_id)
            if record.context_id is not None
            else record.name or "<unnamed>"
        )
        artifact_label = f"context '{context_id}'"
        try:
            validate_cel_expressions(
                iter_context_assumption_expressions(
                    list(record.assumptions),
                    artifact_label=artifact_label,
                ),
                cel_registry,
            )
        except CelIngestValidationError as exc:
            _record(
                PropstoreFamily.CONTEXTS,
                ContextStage.AUTHORED,
                str(exc),
                filename=None,
                artifact_id=context_id,
            )

    if diagnostics:
        raise CompilerWorkflowError(
            f"Validation FAILED: {len(diagnostics)} error(s)",
            tuple(diagnostics),
        )


def _messages_from_pipeline_result(result) -> tuple[PassDiagnostic, ...]:
    return tuple(result.diagnostics)


def validate_repository(repo: Repository) -> RepositoryValidationSummary:
    tree = repo.tree()
    try:
        concepts: list[LoadedConcept] = []
        for handle in repo.families.concepts.iter_handles():
            concepts.append(
                LoadedConcept(
                    filename=handle.ref.name,
                    source_path=tree / handle.address.require_path(),
                    knowledge_root=tree,
                    record=parse_concept_record_document(handle.document),
                    document=handle.document,
                )
            )
    except DocumentSchemaError as exc:
        raise CompilerWorkflowError(
            "Validation FAILED: 1 error(s)",
            (
                _workflow_diagnostic(
                    PropstoreFamily.CONCEPTS,
                    ConceptStage.AUTHORED,
                    str(exc),
                ),
            ),
        ) from exc
    if not concepts:
        return RepositoryValidationSummary(
            concept_count=0,
            claim_file_count=0,
            messages=(),
            no_concepts=True,
        )

    messages: list[PassDiagnostic] = []

    form_files = [
        LoadedForm(filename=handle.ref.name, document=handle.document)
        for handle in repo.families.forms.iter_handles()
    ]
    form_result = run_form_pipeline(form_files)
    messages.extend(_messages_from_pipeline_result(form_result))
    form_registry = (
        form_result.output.registry
        if isinstance(form_result.output, FormCheckedRegistry)
        else {}
    )

    files = [
        LoadedClaimsFile(
            filename=handle.ref.artifact_id,
            artifact_path=tree / handle.address.require_path(),
            store_root=tree,
            document=handle.document,
        )
        for handle in repo.families.claims.iter_handles()
    ]

    concept_result = run_concept_pipeline(
        concepts,
        context=ConceptPipelineContext(
            form_registry=form_registry,
            claim_index=build_compiler_claim_index(files),
        ),
    )
    messages.extend(_messages_from_pipeline_result(concept_result))

    claim_error_count = 0
    claim_file_count = len(files)
    if files:
        try:
            context = build_compilation_context_from_repo(repo, claim_files=files)
            claim_pipeline_result = run_claim_pipeline(
                ClaimAuthoredFiles.from_sequence(files, context)
            )
        except DocumentSchemaError as exc:
            raise CompilerWorkflowError(
                "Validation FAILED: 1 error(s)",
                (
                    _workflow_diagnostic(
                        PropstoreFamily.CLAIMS,
                        ClaimStage.AUTHORED,
                        str(exc),
                    ),
                ),
            ) from exc
        messages.extend(_messages_from_pipeline_result(claim_pipeline_result))
        claim_error_count = len(claim_pipeline_result.errors)

    context_error_count = 0
    try:
        ctx_list = [
            LoadedContext(
                filename=handle.ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_context_record_document(handle.document),
            )
            for handle in repo.families.contexts.iter_handles()
        ]
    except DocumentSchemaError as exc:
        raise CompilerWorkflowError(
            "Validation FAILED: 1 error(s)",
            (
                _workflow_diagnostic(
                    PropstoreFamily.CONTEXTS,
                    ContextStage.AUTHORED,
                    str(exc),
                ),
            ),
        ) from exc
    if ctx_list:
        ctx_result = run_context_pipeline(ctx_list)
        messages.extend(_messages_from_pipeline_result(ctx_result))
        context_error_count = len(ctx_result.errors)

    # Pre-build CEL invariant check: reject structural concepts appearing
    # in any claim condition or context assumption. Fails early with the
    # offending artifact named so authors see one clear error — not a
    # Z3-wrapped message three layers deep at conflict-detection time.
    if isinstance(concept_result.output, ConceptCheckedRegistry):
        cel_registry = build_compilation_context_from_loaded(
            concepts,
            form_registry=form_registry,
            claim_files=files if files else None,
        ).cel_registry
        _enforce_cel_structural_invariants(
            files,
            [c.record for c in ctx_list],
            cel_registry,
        )

    total_errors = (
        len(concept_result.errors)
        + claim_error_count
        + len(form_result.errors)
        + context_error_count
    )
    if total_errors:
        return RepositoryValidationSummary(
            concept_count=len(concepts),
            claim_file_count=claim_file_count,
            messages=tuple(messages),
        )

    return RepositoryValidationSummary(
        concept_count=len(concepts),
        claim_file_count=claim_file_count,
        messages=tuple(messages),
    )


def build_repository(
    repo: Repository,
    *,
    force: bool = False,
    strict_authoring: bool = False,
) -> RepositoryBuildReport:
    hash_key = repo.require_git().head_sha()
    tree = repo.snapshot.tree(commit=hash_key)

    concepts: list[LoadedConcept] = []
    concept_schema_messages: list[PassDiagnostic] = []
    for ref in repo.families.concepts.iter(commit=hash_key):
        try:
            handle = repo.families.concepts.require_handle(
                ref,
                commit=hash_key,
            )
        except DocumentSchemaError as exc:
            concept_schema_messages.append(
                PassDiagnostic(
                    level="error",
                    code="concept.schema",
                    message=str(exc),
                    family=PropstoreFamily.CONCEPTS,
                    stage=ConceptStage.AUTHORED,
                    filename=ref.name,
                    artifact_id=ref.name,
                    pass_name="compiler.build_repository",
                )
            )
            continue
        concepts.append(
            LoadedConcept(
                filename=ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_concept_record_document(handle.document),
                document=handle.document,
            )
        )
    if not concepts:
        return RepositoryBuildReport(
            concept_count=0,
            claim_count=0,
            conflict_count=0,
            phi_node_count=0,
            warning_count=0,
            rebuilt=False,
            no_concepts=True,
        )

    build_messages: list[PassDiagnostic] = []
    form_files = [
        LoadedForm(
            filename=handle.ref.name,
            document=handle.document,
        )
        for handle in repo.families.forms.iter_handles(commit=hash_key)
    ]
    form_result = run_form_pipeline(form_files)
    form_messages = _messages_from_pipeline_result(form_result)
    if not isinstance(form_result.output, FormCheckedRegistry):
        raise CompilerWorkflowError(
            "Build aborted: form validation failed.",
            form_messages,
        )
    build_messages.extend(form_messages)
    form_registry = form_result.output.registry

    files: list[LoadedClaimsFile] = []
    claim_schema_messages: list[PassDiagnostic] = []
    for ref in repo.families.claims.iter(commit=hash_key):
        try:
            handle = repo.families.claims.require_handle(ref, commit=hash_key)
            files.append(
                LoadedClaimsFile(
                    filename=handle.ref.artifact_id,
                    artifact_path=tree / handle.address.require_path(),
                    store_root=tree,
                    document=handle.document,
                )
            )
        except DocumentSchemaError as exc:
            artifact_id = ref.artifact_id
            claim_schema_messages.append(
                PassDiagnostic(
                    level="error",
                    code="claim.schema",
                    message=str(exc),
                    family=PropstoreFamily.CLAIMS,
                    stage=ClaimStage.AUTHORED,
                    filename=repo.families.claims.address(ref, commit=hash_key).require_path(),
                    artifact_id=artifact_id,
                    pass_name="compiler.build_repository",
                )
            )

    concept_result = run_concept_pipeline(
        concepts,
        context=ConceptPipelineContext(
            form_registry=form_registry,
            claim_index=build_compiler_claim_index(files),
        ),
    )
    concept_messages = list(concept_schema_messages)
    concept_messages.extend(_messages_from_pipeline_result(concept_result))
    if not isinstance(concept_result.output, ConceptCheckedRegistry):
        raise CompilerWorkflowError(
            "Build aborted: concept validation failed.",
            tuple(concept_messages),
        )
    build_messages.extend(concept_messages)

    context_ids: set[str] = set()
    ctx_list: list[LoadedContext] = []
    context_messages: list[PassDiagnostic] = []
    for ref in repo.families.contexts.iter(commit=hash_key):
        try:
            handle = repo.families.contexts.require_handle(ref, commit=hash_key)
        except DocumentSchemaError as exc:
            context_messages.append(
                PassDiagnostic(
                    level="error",
                    code="context.schema",
                    message=str(exc),
                    family=PropstoreFamily.CONTEXTS,
                    stage=ContextStage.AUTHORED,
                    filename=ref.name,
                    artifact_id=ref.name,
                    pass_name="compiler.build_repository",
                )
            )
            continue
        ctx_list.append(
            LoadedContext(
                filename=ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_context_record_document(handle.document),
            )
        )
    if ctx_list:
        ctx_result = run_context_pipeline(ctx_list)
        context_messages.extend(_messages_from_pipeline_result(ctx_result))
        if not isinstance(ctx_result.output, ContextCheckedGraph):
            raise CompilerWorkflowError(
                "Build aborted: context validation failed.",
                tuple(context_messages),
            )
        context_ids = {
            str(c.record.context_id)
            for c in ctx_result.output.contexts
            if c.record.context_id is not None
        }
    build_messages.extend(context_messages)

    claim_files = files if files else None
    claim_messages = list(claim_schema_messages)
    compilation_context = build_compilation_context_from_loaded(
        concepts,
        form_registry=form_registry,
        context_ids=context_ids,
    )

    # Pre-build CEL invariant check: reject structural concepts in any
    # claim condition or context assumption before Z3 translation runs.
    # Same enforcement as ingest-time add-claim/context-add.
    _enforce_cel_structural_invariants(
        claim_files,
        [c.record for c in ctx_list],
        compilation_context.cel_registry,
    )

    claim_checked_bundle: ClaimCheckedBundle | None = None
    if files:
        try:
            compilation_context = build_compilation_context_from_loaded(
                concepts,
                form_registry=form_registry,
                claim_files=files,
                context_ids=context_ids if context_ids else None,
            )
            claim_pipeline_result = run_claim_pipeline(
                ClaimAuthoredFiles.from_sequence(
                    files,
                    compilation_context,
                    context_ids=context_ids if context_ids else None,
                )
            )
            claim_messages.extend(_messages_from_pipeline_result(claim_pipeline_result))
            if isinstance(claim_pipeline_result.output, ClaimCheckedBundle):
                claim_checked_bundle = claim_pipeline_result.output
        except DocumentSchemaError as exc:
            claim_messages.append(
                PassDiagnostic(
                    level="error",
                    code="claim.schema",
                    message=str(exc),
                    family=PropstoreFamily.CLAIMS,
                    stage=ClaimStage.AUTHORED,
                    filename=exc.source,
                    artifact_id=exc.source,
                    pass_name="compiler.build_repository",
                )
            )
    build_messages.extend(claim_messages)

    source_entries = tuple(
        (
            handle.ref.name,
            handle.document,
        )
        for handle in repo.families.sources.iter_handles(commit=hash_key)
    )
    stance_entries = tuple(
        (
            handle.ref.artifact_id,
            handle.document,
        )
        for handle in repo.families.stances.iter_handles(commit=hash_key)
    )
    authoring_lints = collect_authoring_lints(
        source_entries=source_entries,
        stance_entries=stance_entries,
        claim_files=tuple(files),
    )
    if strict_authoring and authoring_lints:
        authoring_errors = tuple(
            replace(diagnostic, level="error")
            for diagnostic in authoring_lints
        )
        raise CompilerWorkflowError(
            f"Build aborted: {len(authoring_errors)} authoring error(s)",
            authoring_errors,
        )
    build_messages.extend(authoring_lints)

    embedding_snapshots: list[BuildEmbeddingSnapshotReport] = []

    def _record_embedding_snapshot(report) -> None:
        embedding_snapshots.append(
            BuildEmbeddingSnapshotReport(
                model_count=report.model_count,
                claim_vector_count=report.claim_vector_count,
                concept_vector_count=report.concept_vector_count,
            )
        )

    handle, rebuilt = build_repository_world_store(
        repo,
        force=force,
        commit_hash=hash_key,
        compilation_context=compilation_context,
        claim_checked_bundle=claim_checked_bundle,
        claim_files=tuple(files),
        claim_diagnostics=tuple(claim_messages),
        concept_files=tuple(concepts),
        concept_diagnostics=tuple(concept_messages),
        context_files=tuple(ctx_list),
        context_diagnostics=tuple(context_messages),
        authoring_diagnostics=authoring_lints,
        on_embedding_snapshot=_record_embedding_snapshot,
    )

    warning_count = sum(1 for message in build_messages if message.is_warning)
    sidecar_missing = False
    try:
        from collections import defaultdict

        from propstore.conflict_detector import ConflictClass
        from propstore.world.model import WorldQuery

        wm = WorldQuery(repo, commit=hash_key)
        stats = wm.stats()
        claim_count = stats.claims
        conflicts = wm.conflicts()
        phi_groups: dict[str, set[str]] = defaultdict(set)
        phi_node_count = 0
        real_conflicts: list[BuildConflictLine] = []
        for conflict in conflicts:
            warning_class = conflict.warning_class
            if warning_class in (ConflictClass.PHI_NODE, ConflictClass.CONTEXT_PHI_NODE):
                key = f"{warning_class.value}: {conflict.concept_id}"
                phi_groups[key].add(str(conflict.claim_a_id))
                phi_groups[key].add(str(conflict.claim_b_id))
                phi_node_count += 1
            else:
                real_conflicts.append(
                    BuildConflictLine(
                        warning_class=str(warning_class),
                        concept_id=str(conflict.concept_id),
                        claim_a_id=str(conflict.claim_a_id),
                        claim_b_id=str(conflict.claim_b_id),
                    )
                )
        wm.close()
    except FileNotFoundError as exc:
        sidecar_missing = True
        build_messages.append(
            PassDiagnostic(
                level="error",
                code="sidecar.missing",
                message=str(exc),
                family=PropstoreFamily.CLAIMS,
                stage=ClaimStage.AUTHORED,
                pass_name="compiler.build_repository",
            )
        )
        claim_count = 0
        phi_node_count = 0
        real_conflicts = []
        phi_groups = {}
        if claim_files:
            for claim_file in claim_files:
                claim_count += len(claim_file_payload(claim_file).get("claims", []))

    return RepositoryBuildReport(
        concept_count=len(concepts),
        claim_count=claim_count,
        conflict_count=len(real_conflicts),
        phi_node_count=phi_node_count,
        warning_count=warning_count,
        rebuilt=rebuilt,
        conflicts=tuple(real_conflicts),
        phi_groups=tuple(
            BuildPhiGroup(key=key, claim_ids=tuple(sorted(claim_ids)))
            for key, claim_ids in phi_groups.items()
        ),
        embedding_snapshot=embedding_snapshots[-1] if embedding_snapshots else None,
        derived_store=BuildDerivedStoreHandle(
            projection_id=handle.projection_id,
            source_commit=handle.source_commit,
            cache_key=handle.cache_key,
            path=str(handle.path),
        ),
        messages=tuple(build_messages),
        sidecar_missing=sidecar_missing,
    )
