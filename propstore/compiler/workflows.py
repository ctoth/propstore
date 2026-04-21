"""Repository-level compiler workflows.

This module owns validation/build orchestration. CLI modules are responsible
for presenting these reports, not for deciding which compiler passes run.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quire.documents import DocumentSchemaError
from propstore.claims import ClaimFileEntry, claim_file_payload
from propstore.compiler.context import (
    build_compilation_context_from_loaded,
    build_compilation_context_from_repo,
)
from propstore.compiler.references import build_claim_reference_lookup
from propstore.families.claims.passes import run_claim_pipeline
from propstore.families.claims.stages import ClaimAuthoredFiles, ClaimCheckedBundle, ClaimStage
from propstore.families.concepts.passes import (
    ConceptPipelineContext,
    run_concept_pipeline,
)
from propstore.families.contexts.passes import run_context_pipeline
from propstore.families.contexts.stages import (
    ContextCheckedGraph,
    ContextStage,
    LoadedContext,
    parse_context_record_document,
)
from propstore.families.concepts.stages import (
    ConceptCheckedRegistry,
    ConceptStage,
    LoadedConcept,
    parse_concept_record_document,
)
from propstore.families.forms.passes import run_form_pipeline
from propstore.families.forms.stages import FormCheckedRegistry, FormStage, LoadedForm
from propstore.families.registry import PropstoreFamily
from propstore.repository import Repository
from propstore.semantic_passes.types import PassDiagnostic


class CompilerWorkflowError(Exception):
    def __init__(self, summary: str, messages: tuple[PassDiagnostic, ...]) -> None:
        super().__init__(summary)
        self.summary = summary
        self.messages = messages


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
class RepositoryBuildReport:
    concept_count: int
    claim_count: int
    conflict_count: int
    phi_node_count: int
    warning_count: int
    rebuilt: bool
    conflicts: tuple[BuildConflictLine, ...] = ()
    phi_groups: tuple[BuildPhiGroup, ...] = ()
    messages: tuple[PassDiagnostic, ...] = ()
    no_concepts: bool = False


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


def _messages_from_pipeline_result(result) -> tuple[PassDiagnostic, ...]:
    return tuple(result.diagnostics)


def validate_repository(repo: Repository) -> RepositoryValidationSummary:
    tree = repo.tree()
    try:
        concepts: list[LoadedConcept] = []
        for ref in repo.families.concepts.iter():
            handle = repo.families.concepts.require_handle(ref)
            concepts.append(
                LoadedConcept(
                    filename=ref.name,
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
        LoadedForm(filename=form_ref.name, document=repo.families.forms.require(form_ref))
        for form_ref in repo.families.forms.iter()
    ]
    form_result = run_form_pipeline(form_files)
    messages.extend(_messages_from_pipeline_result(form_result))
    form_registry = (
        form_result.output.registry
        if isinstance(form_result.output, FormCheckedRegistry)
        else {}
    )

    files = [
        repo.families.claims.require_handle(ref)
        for ref in repo.families.claims.iter()
    ]

    concept_result = run_concept_pipeline(
        concepts,
        context=ConceptPipelineContext(
            form_registry=form_registry,
            claim_reference_lookup=build_claim_reference_lookup(files),
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
                filename=ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_context_record_document(handle.document),
            )
            for ref in repo.families.contexts.iter()
            for handle in (repo.families.contexts.require_handle(ref),)
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
    output: str | None = None,
    force: bool = False,
) -> RepositoryBuildReport:
    from propstore.sidecar.build import build_sidecar

    hash_key = repo.snapshot.head_sha()
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
            filename=form_ref.name,
            document=repo.families.forms.require(form_ref, commit=hash_key),
        )
        for form_ref in repo.families.forms.iter(commit=hash_key)
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

    files: list[ClaimFileEntry] = []
    claim_schema_messages: list[PassDiagnostic] = []
    for ref in repo.families.claims.iter(commit=hash_key):
        try:
            files.append(repo.families.claims.require_handle(ref, commit=hash_key))
        except DocumentSchemaError as exc:
            claim_schema_messages.append(
                PassDiagnostic(
                    level="error",
                    code="claim.schema",
                    message=str(exc),
                    family=PropstoreFamily.CLAIMS,
                    stage=ClaimStage.AUTHORED,
                    filename=ref.name,
                    artifact_id=ref.name,
                    pass_name="compiler.build_repository",
                )
            )

    concept_result = run_concept_pipeline(
        concepts,
        context=ConceptPipelineContext(
            form_registry=form_registry,
            claim_reference_lookup=build_claim_reference_lookup(files),
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

    sidecar_path = Path(output) if output else repo.sidecar_path
    rebuilt = build_sidecar(
        repo,
        sidecar_path,
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
    )

    warning_count = len(concept_result.warnings)
    try:
        from collections import defaultdict

        from propstore.conflict_detector import ConflictClass
        from propstore.world import WorldModel

        wm = WorldModel(repo)
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
    except FileNotFoundError:
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
        messages=tuple(build_messages),
    )
