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
        handle
        for handle in repo.families.claims.iter_handles()
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
