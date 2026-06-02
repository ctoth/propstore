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
from quire.documents import DocumentSchemaError, LoadedDocument
from quire.sqlalchemy_store import create_sqlalchemy_store, populate_fts_index
from propstore.claims import LoadedClaimsFile
from propstore.compiler.context import (
    build_compiler_claim_index,
    build_compilation_context_from_loaded,
    build_compilation_context_from_repo,
    concept_registry_for_context,
)
from propstore.compiler.errors import CompilerWorkflowError
from propstore.families.claims.passes import run_claim_pipeline
from propstore.families.claims.references import build_claim_file_reference_index
from propstore.families.claims.stages import (
    ClaimAuthoredFiles,
    ClaimCheckedBundle,
    ClaimStage,
)
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
    loaded_contexts_to_lifting_system,
)
from propstore.families.contexts.declaration import (
    ContextDocument,
    compile_context_models,
    filter_invalid_context_lifting_models,
)
from propstore.families.concepts.stages import (
    ConceptCheckedRegistry,
    ConceptStage,
)
from propstore.families.concepts.declaration import ConceptDocument
from propstore.families.forms.passes import run_form_pipeline
from propstore.families.forms.stages import FormCheckedRegistry, LoadedForm
from propstore.families.micropublications.declaration import (
    compile_micropublication_models_with_diagnostics,
)
from propstore.families.relations.declaration import (
    compile_authored_stance_models_with_diagnostics,
    compile_claim_embedded_stance_models_for_claims_with_diagnostics,
    compile_conflict_witness_models,
)
from propstore.families.registry import PropstoreFamily
from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY, world_schema
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
from propstore.families.meta.declaration import (
    PROPSTORE_WORLD_META_KEY,
    PROPSTORE_WORLD_SCHEMA_VERSION,
    WorldMeta,
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
    concept_files: tuple[LoadedDocument[ConceptDocument], ...] | None = None,
    concept_diagnostics: tuple[PassDiagnostic, ...] = (),
    context_files: tuple[LoadedDocument[ContextDocument], ...] | None = None,
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
    concept_files: tuple[LoadedDocument[ConceptDocument], ...] | None = None,
    concept_diagnostics: tuple[PassDiagnostic, ...] = (),
    context_files: tuple[LoadedDocument[ContextDocument], ...] | None = None,
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
    schema = world_schema()
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


def _claim_schema_diagnostic(
    exc: DocumentSchemaError,
    *,
    pass_name: str,
) -> PassDiagnostic:
    return PassDiagnostic(
        level="error",
        code="claim.schema",
        message=str(exc),
        family=PropstoreFamily.CLAIMS,
        stage=ClaimStage.AUTHORED,
        filename=exc.source,
        artifact_id=exc.source,
        pass_name=pass_name,
    )


def _enforce_cel_structural_invariants(
    claim_files,
    context_files,
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
    from propstore.claims import (
        claim_file_claims,
        claim_file_source_paper,
        claim_file_filename,
    )

    diagnostics: list[PassDiagnostic] = []

    def _record(
        family, stage, message: str, *, filename: str | None, artifact_id: str | None
    ):
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

    for context_file in context_files or ():
        document = context_file.document
        if not document.assumptions:
            continue
        context_id = str(document.id or document.name or "<unnamed>")
        artifact_label = f"context '{context_id}'"
        try:
            validate_cel_expressions(
                iter_context_assumption_expressions(
                    [str(assumption) for assumption in document.assumptions],
                    artifact_label=artifact_label,
                ),
                cel_registry,
            )
        except CelIngestValidationError as exc:
            _record(
                PropstoreFamily.CONTEXTS,
                ContextStage.AUTHORED,
                str(exc),
                filename=context_file.filename,
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
        concepts: list[LoadedDocument[ConceptDocument]] = []
        for handle in repo.families.concepts.iter_handles():
            concepts.append(
                LoadedDocument(
                    filename=handle.ref.name,
                    artifact_path=tree / handle.address.require_path(),
                    store_root=tree,
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
            LoadedDocument(
                filename=handle.ref.name,
                artifact_path=tree / handle.address.require_path(),
                store_root=tree,
                document=handle.document,
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
            ctx_list,
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
