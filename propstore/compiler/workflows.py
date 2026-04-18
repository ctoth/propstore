"""Repository-level compiler workflows.

This module owns validation/build orchestration. CLI modules are responsible
for presenting these reports, not for deciding which compiler passes run.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from quire.documents import DocumentSchemaError
from propstore.artifacts.families import CLAIMS_FILE_FAMILY, CONCEPT_FILE_FAMILY, FORM_FAMILY
from propstore.claims import claim_file_payload
from propstore.compiler.context import build_compilation_context_from_repo
from propstore.compiler.passes import compile_claim_files, validate_claims
from propstore.compiler.references import build_claim_reference_lookup
from propstore.core.concepts import LoadedConcept, parse_concept_record_document
from propstore.diagnostics import ValidationResult
from propstore.form_utils import parse_form
from propstore.repository import Repository
from propstore.validate_concepts import validate_concepts

if TYPE_CHECKING:
    from propstore.context_types import ContextInput


WorkflowMessageLevel = Literal["warning", "error"]


@dataclass(frozen=True)
class WorkflowMessage:
    level: WorkflowMessageLevel
    text: str
    scope: str | None = None


class CompilerWorkflowError(Exception):
    def __init__(self, summary: str, messages: tuple[WorkflowMessage, ...]) -> None:
        super().__init__(summary)
        self.summary = summary
        self.messages = messages


@dataclass(frozen=True)
class RepositoryValidationReport:
    concept_count: int
    claim_file_count: int
    messages: tuple[WorkflowMessage, ...]
    no_concepts: bool = False

    @property
    def errors(self) -> tuple[WorkflowMessage, ...]:
        return tuple(message for message in self.messages if message.level == "error")

    @property
    def warnings(self) -> tuple[WorkflowMessage, ...]:
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
    messages: tuple[WorkflowMessage, ...] = ()
    no_concepts: bool = False


def _messages_from_result(result, *, scope: str | None = None) -> tuple[WorkflowMessage, ...]:
    messages: list[WorkflowMessage] = []
    messages.extend(WorkflowMessage("warning", str(warning), scope) for warning in result.warnings)
    messages.extend(WorkflowMessage("error", str(error), scope) for error in result.errors)
    return tuple(messages)


def validate_repository(repo: Repository) -> RepositoryValidationReport:
    tree = repo.tree()
    try:
        concepts: list[LoadedConcept] = []
        for ref in repo.artifacts.list(CONCEPT_FILE_FAMILY):
            handle = repo.artifacts.require_handle(CONCEPT_FILE_FAMILY, ref)
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
            (WorkflowMessage("error", str(exc)),),
        ) from exc
    if not concepts:
        return RepositoryValidationReport(
            concept_count=0,
            claim_file_count=0,
            messages=(),
            no_concepts=True,
        )

    messages: list[WorkflowMessage] = []

    form_result = ValidationResult()
    form_registry = {
        document.name: parse_form(document.name, document)
        for form_ref in repo.artifacts.list(FORM_FAMILY)
        for document in (repo.artifacts.require(FORM_FAMILY, form_ref),)
    }
    for form_ref in repo.artifacts.list(FORM_FAMILY):
        document = repo.artifacts.require(FORM_FAMILY, form_ref)
        dims = document.dimensions
        is_dimless = document.dimensionless
        has_unit = document.unit_symbol is not None
        if dims is not None:
            for dimension_key in dims:
                if not dimension_key or not dimension_key[0].isalpha() or not dimension_key.isidentifier():
                    form_result.errors.append(
                        f"{form_ref.name}: dimension key '{dimension_key}' must be an identifier"
                    )
        if dims is not None and len(dims) > 0 and is_dimless:
            form_result.errors.append(
                f"{form_ref.name}: non-empty dimensions conflicts with dimensionless=true"
            )
        if dims is not None and len(dims) == 0 and not is_dimless and has_unit:
            form_result.errors.append(
                f"{form_ref.name}: empty dimensions conflicts with dimensionless=false for a quantity with unit_symbol"
            )
        if document.name != form_ref.name:
            form_result.errors.append(
                f"{form_ref.name}: 'name' field ('{document.name}') does not match filename '{form_ref.name}'"
            )
    messages.extend(_messages_from_result(form_result, scope="form"))

    files = [
        repo.artifacts.require_handle(CLAIMS_FILE_FAMILY, ref)
        for ref in repo.artifacts.list(CLAIMS_FILE_FAMILY)
    ]

    concept_result = validate_concepts(
        concepts,
        form_registry=form_registry,
        claim_reference_lookup=build_claim_reference_lookup(files),
    )
    messages.extend(_messages_from_result(concept_result))

    claim_error_count = 0
    claim_file_count = len(files)
    if files:
        try:
            context = build_compilation_context_from_repo(repo, claim_files=files)
            claim_result = validate_claims(files, context)
        except DocumentSchemaError as exc:
            raise CompilerWorkflowError(
                "Validation FAILED: 1 error(s)",
                (WorkflowMessage("error", str(exc)),),
            ) from exc
        messages.extend(_messages_from_result(claim_result))
        claim_error_count = len(claim_result.errors)

    context_error_count = 0
    if (tree / "contexts").exists():
        from propstore.validate_contexts import load_contexts, validate_contexts

        try:
            ctx_list = load_contexts(tree / "contexts")
        except DocumentSchemaError as exc:
            raise CompilerWorkflowError(
                "Validation FAILED: 1 error(s)",
                (WorkflowMessage("error", str(exc), "context"),),
            ) from exc
        if ctx_list:
            ctx_result = validate_contexts(cast("list[ContextInput]", ctx_list))
            messages.extend(_messages_from_result(ctx_result, scope="context"))
            context_error_count = len(ctx_result.errors)

    total_errors = (
        len(concept_result.errors)
        + claim_error_count
        + len(form_result.errors)
        + context_error_count
    )
    if total_errors:
        return RepositoryValidationReport(
            concept_count=len(concepts),
            claim_file_count=claim_file_count,
            messages=tuple(messages),
        )

    return RepositoryValidationReport(
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

    try:
        concepts: list[LoadedConcept] = []
        for ref in repo.artifacts.list(CONCEPT_FILE_FAMILY, commit=hash_key):
            handle = repo.artifacts.require_handle(
                CONCEPT_FILE_FAMILY,
                ref,
                commit=hash_key,
            )
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
            "Build aborted: schema validation failed.",
            (WorkflowMessage("error", str(exc)),),
        ) from exc
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

    form_result = ValidationResult()
    form_registry = {
        document.name: parse_form(document.name, document)
        for form_ref in repo.artifacts.list(FORM_FAMILY, commit=hash_key)
        for document in (repo.artifacts.require(FORM_FAMILY, form_ref, commit=hash_key),)
    }
    for form_ref in repo.artifacts.list(FORM_FAMILY, commit=hash_key):
        document = repo.artifacts.require(FORM_FAMILY, form_ref, commit=hash_key)
        dims = document.dimensions
        is_dimless = document.dimensionless
        has_unit = document.unit_symbol is not None
        if dims is not None:
            for dimension_key in dims:
                if not dimension_key or not dimension_key[0].isalpha() or not dimension_key.isidentifier():
                    form_result.errors.append(
                        f"{form_ref.name}: dimension key '{dimension_key}' must be an identifier"
                    )
        if dims is not None and len(dims) > 0 and is_dimless:
            form_result.errors.append(
                f"{form_ref.name}: non-empty dimensions conflicts with dimensionless=true"
            )
        if dims is not None and len(dims) == 0 and not is_dimless and has_unit:
            form_result.errors.append(
                f"{form_ref.name}: empty dimensions conflicts with dimensionless=false for a quantity with unit_symbol"
            )
        if document.name != form_ref.name:
            form_result.errors.append(
                f"{form_ref.name}: 'name' field ('{document.name}') does not match filename '{form_ref.name}'"
            )
    if not form_result.ok:
        raise CompilerWorkflowError(
            "Build aborted: form validation failed.",
            _messages_from_result(form_result, scope="form"),
        )

    files = [
        repo.artifacts.require_handle(CLAIMS_FILE_FAMILY, ref, commit=hash_key)
        for ref in repo.artifacts.list(CLAIMS_FILE_FAMILY, commit=hash_key)
    ]

    concept_result = validate_concepts(
        concepts,
        form_registry=form_registry,
        claim_reference_lookup=build_claim_reference_lookup(files),
    )
    if not concept_result.ok:
        raise CompilerWorkflowError(
            "Build aborted: concept validation failed.",
            tuple(
                WorkflowMessage("error", str(error))
                for error in concept_result.errors
            ),
        )

    from propstore.validate_contexts import load_contexts, validate_contexts

    build_messages: list[WorkflowMessage] = []
    context_ids: set[str] = set()
    if (tree / "contexts").exists():
        try:
            ctx_list = load_contexts(tree / "contexts")
        except DocumentSchemaError as exc:
            raise CompilerWorkflowError(
                "Build aborted: context validation failed.",
                (WorkflowMessage("error", str(exc), "context"),),
            ) from exc
        if ctx_list:
            ctx_result = validate_contexts(cast("list[ContextInput]", ctx_list))
            context_messages = _messages_from_result(ctx_result, scope="context")
            if not ctx_result.ok:
                raise CompilerWorkflowError(
                    "Build aborted: context validation failed.",
                    context_messages,
                )
            build_messages.extend(context_messages)
            context_ids = {
                str(c.record.context_id)
                for c in ctx_list
                if c.record.context_id is not None
            }

    claim_files = None
    compilation_context = build_compilation_context_from_repo(
        repo,
        context_ids=context_ids,
        commit=hash_key,
    )
    claim_bundle = None
    if files:
        try:
            compilation_context = build_compilation_context_from_repo(
                repo,
                claim_files=files,
                context_ids=context_ids if context_ids else None,
                commit=hash_key,
            )
            claim_bundle = compile_claim_files(
                files,
                compilation_context,
                context_ids=context_ids if context_ids else None,
            )
            claim_result = claim_bundle.to_validation_result()
            if not claim_result.ok:
                raise CompilerWorkflowError(
                    "Build aborted: claim validation failed.",
                    tuple(
                        WorkflowMessage("error", str(error))
                        for error in claim_result.errors
                    ),
                )
            claim_files = files
        except DocumentSchemaError as exc:
            raise CompilerWorkflowError(
                "Build aborted: claim validation failed.",
                (WorkflowMessage("error", str(exc)),),
            ) from exc

    sidecar_path = Path(output) if output else repo.sidecar_path
    rebuilt = build_sidecar(
        tree,
        sidecar_path,
        force=force,
        commit_hash=hash_key,
        compilation_context=compilation_context,
        claim_bundle=claim_bundle,
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
