"""Repository-level compiler workflows: ``pks validate`` and ``pks build``.

Both workflows run the SAME per-family semantic pipelines and the SAME check set
over a repository's authored families, differing ONLY in their terminal sink
(PLAN.md §12.6): :func:`validate_repository` reports the diagnostics;
:func:`build_repository` additionally materialises the world sidecar. There is no
second validation path.

The Z1 abort-vs-quarantine split (gaps.md, PLAN.md §12.1) is realised here:

* A schema-undecodable document, or a form/concept/context *validation failure*
  (the family pipeline cannot produce a checked registry), or a *structural*
  concept appearing in a CEL expression, ABORTS with
  :class:`~propstore.compiler.errors.CompilerWorkflowError`.
* A semantically invalid *claim* (a failed type contract, a CEL type error, a
  dangling context reference) is QUARANTINED: it is retained as a ``blocked``
  checked claim with diagnostics, and the build proceeds.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from quire.documents import DocumentSchemaError

from propstore.cel_validation import structural_concepts_in_expression
from propstore.compiler.context import (
    CompilationContext,
    build_compilation_context,
)
from propstore.build_diagnostics import collect_authoring_lints, upgrade_lints_to_errors
from propstore.compiler.errors import CompilerWorkflowError
from propstore.compiler.ir import ClaimCheckedBundle
from propstore.derived_build import materialize_world_sidecar
from propstore.derived_build_plan import (
    RepositoryCheckedBundle,
    compile_sidecar_build_plan,
)
from propstore.families.claims import Claim
from propstore.families.claims_passes import (
    ClaimFiles,
    ClaimStage,
    LoadedClaim,
    run_claim_pipeline,
)
from propstore.families.concepts import Concept
from propstore.families.conflicts import ConflictProjection
from propstore.families.concepts_passes import (
    ConceptCheckedRegistry,
    ConceptPipelineContext,
    ConceptStage,
    LoadedConcept,
    run_concept_pipeline,
)
from propstore.families.contexts import Context, LiftingRule
from propstore.families.contexts_passes import (
    ContextCheckedGraph,
    ContextStage,
    LoadedContext,
    LoadedLiftingRule,
    run_context_pipeline,
)
from propstore.families.forms import FormDefinition
from propstore.families.forms_passes import (
    FormCheckedRegistry,
    FormStage,
    LoadedForm,
    run_form_pipeline,
)
from propstore.families.registry import PropstoreFamily
from propstore.families.relations import Stance
from propstore.repository import Repository
from propstore.semantic_passes.types import PassDiagnostic, StageId

# --------------------------------------------------------------------------- #
# Report types
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class RepositoryValidationSummary:
    concept_count: int
    claim_count: int
    messages: tuple[PassDiagnostic, ...]
    no_concepts: bool = False

    @property
    def errors(self) -> tuple[PassDiagnostic, ...]:
        return tuple(message for message in self.messages if message.is_error)

    @property
    def warnings(self) -> tuple[PassDiagnostic, ...]:
        return tuple(message for message in self.messages if message.is_warning)

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
    conflict_count: int = 0
    phi_node_count: int = 0
    warning_count: int = 0
    rebuilt: bool = False
    conflicts: tuple[BuildConflictLine, ...] = ()
    phi_groups: tuple[BuildPhiGroup, ...] = ()
    embedding_snapshot: BuildEmbeddingSnapshotReport | None = None
    derived_store: BuildDerivedStoreHandle | None = None
    messages: tuple[PassDiagnostic, ...] = ()
    no_concepts: bool = False
    sidecar_missing: bool = False

    @property
    def errors(self) -> tuple[PassDiagnostic, ...]:
        return tuple(message for message in self.messages if message.is_error)

    @property
    def blocked_claim_count(self) -> int:
        return sum(
            1
            for message in self.messages
            if message.is_error and message.family is PropstoreFamily.CLAIM
        )


# --------------------------------------------------------------------------- #
# Shared compilation (ONE check set for both workflows)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _CompiledRepository:
    concepts: tuple[Concept, ...]
    form_registry: Mapping[str, FormDefinition]
    context_ids: frozenset[str]
    loaded_contexts: tuple[Context, ...]
    loaded_lifting_rules: tuple[LiftingRule, ...]
    claim_bundle: ClaimCheckedBundle
    compilation_context: CompilationContext
    messages: tuple[PassDiagnostic, ...]
    concept_count: int
    claim_count: int
    no_concepts: bool = False


def _abort(
    family: PropstoreFamily,
    stage: StageId,
    summary: str,
    diagnostics: tuple[PassDiagnostic, ...],
) -> CompilerWorkflowError:
    if diagnostics:
        return CompilerWorkflowError(summary, diagnostics)
    return CompilerWorkflowError(
        summary,
        (
            PassDiagnostic(
                level="error",
                code="workflow.error",
                message=summary,
                family=family,
                stage=stage,
            ),
        ),
    )


def _load_documents(
    repo: Repository,
    family_name: str,
    *,
    commit: str | None,
    family: PropstoreFamily,
    stage: StageId,
) -> list[tuple[str, object]]:
    """Load (filename, document) for a family, aborting on a schema error.

    A document that fails to decode is a schema-structural failure — the Z1
    abort class — so it raises rather than quarantining.
    """

    try:
        return [
            (str(handle.ref), handle.document)
            for handle in repo.families.by_name(family_name).iter_handles(commit=commit)
        ]
    except DocumentSchemaError as exc:
        raise _abort(
            family,
            stage,
            f"Validation FAILED: could not decode {family_name} document",
            (
                PassDiagnostic(
                    level="error",
                    code=f"{family_name}.schema",
                    message=str(exc),
                    family=family,
                    stage=stage,
                    pass_name="compiler.load",
                ),
            ),
        ) from exc


def _enforce_cel_structural_invariants(
    loaded_claims: Sequence[LoadedClaim],
    loaded_contexts: Sequence[LoadedContext],
    cel_registry: Mapping[str, object],
) -> None:
    """Abort if a structural concept appears in any CEL expression.

    This is the narrow architectural invariant (a structural concept breaks Z3
    translation), shared by build and validate. Ordinary CEL type errors are NOT
    handled here — they quarantine through the claim pipeline.
    """

    from condition_ir import ConceptInfo

    typed_registry: Mapping[str, ConceptInfo] = {
        key: value for key, value in cel_registry.items() if isinstance(value, ConceptInfo)
    }
    diagnostics: list[PassDiagnostic] = []
    for loaded in loaded_claims:
        claim = loaded.claim
        for condition in claim.conditions:
            for name in structural_concepts_in_expression(condition, typed_registry):
                diagnostics.append(
                    PassDiagnostic(
                        level="error",
                        code="cel.structural_in_expression",
                        message=(
                            f"structural concept '{name}' cannot appear in a claim "
                            f"condition ({condition!r})"
                        ),
                        family=PropstoreFamily.CLAIM,
                        stage=ClaimStage.AUTHORED,
                        filename=loaded.filename,
                        artifact_id=claim.claim_id,
                        pass_name="compiler.validate_cel_structural_invariants",
                    )
                )
    for loaded_context in loaded_contexts:
        ctx = loaded_context.context
        for assumption in ctx.assumptions:
            for name in structural_concepts_in_expression(assumption, typed_registry):
                diagnostics.append(
                    PassDiagnostic(
                        level="error",
                        code="cel.structural_in_expression",
                        message=(
                            f"structural concept '{name}' cannot appear in a context "
                            f"assumption ({assumption!r})"
                        ),
                        family=PropstoreFamily.CONTEXT,
                        stage=ContextStage.AUTHORED,
                        filename=loaded_context.filename,
                        artifact_id=ctx.context_id,
                        pass_name="compiler.validate_cel_structural_invariants",
                    )
                )
    if diagnostics:
        raise CompilerWorkflowError(
            f"Validation FAILED: {len(diagnostics)} structural-concept error(s)",
            tuple(diagnostics),
        )


def _compile_repository(
    repo: Repository, *, commit: str | None
) -> _CompiledRepository:
    loaded_forms = [
        LoadedForm(form=document, filename=name)
        for name, document in _load_documents(
            repo, "form", commit=commit, family=PropstoreFamily.FORM, stage=FormStage.AUTHORED
        )
        if isinstance(document, FormDefinition)
    ]
    loaded_concepts = [
        LoadedConcept(concept=document, filename=name)
        for name, document in _load_documents(
            repo,
            "concept",
            commit=commit,
            family=PropstoreFamily.CONCEPT,
            stage=ConceptStage.AUTHORED,
        )
        if isinstance(document, Concept)
    ]
    if not loaded_concepts:
        empty_result = run_concept_pipeline([])
        if not isinstance(empty_result.output, ConceptCheckedRegistry):
            raise _abort(
                PropstoreFamily.CONCEPT,
                ConceptStage.CHECKED,
                "Build aborted: concept validation failed.",
                empty_result.errors,
            )
        empty_context = build_compilation_context(empty_result.output)
        return _CompiledRepository(
            concepts=(),
            form_registry={},
            context_ids=frozenset(),
            loaded_contexts=(),
            loaded_lifting_rules=(),
            claim_bundle=ClaimCheckedBundle(),
            compilation_context=empty_context,
            messages=(),
            concept_count=0,
            claim_count=0,
            no_concepts=True,
        )

    loaded_contexts = [
        LoadedContext(context=document, filename=name)
        for name, document in _load_documents(
            repo,
            "context",
            commit=commit,
            family=PropstoreFamily.CONTEXT,
            stage=ContextStage.AUTHORED,
        )
        if isinstance(document, Context)
    ]
    loaded_rules = [
        LoadedLiftingRule(rule=document, filename=name)
        for name, document in _load_documents(
            repo,
            "lifting_rule",
            commit=commit,
            family=PropstoreFamily.CONTEXT,
            stage=ContextStage.AUTHORED,
        )
        if isinstance(document, LiftingRule)
    ]
    loaded_claims = [
        LoadedClaim(claim=document, filename=name)
        for name, document in _load_documents(
            repo,
            "claim",
            commit=commit,
            family=PropstoreFamily.CLAIM,
            stage=ClaimStage.AUTHORED,
        )
        if isinstance(document, Claim)
    ]

    messages: list[PassDiagnostic] = []

    form_result = run_form_pipeline(loaded_forms)
    messages.extend(form_result.diagnostics)
    if not isinstance(form_result.output, FormCheckedRegistry):
        raise _abort(
            PropstoreFamily.FORM,
            FormStage.CHECKED,
            "Build aborted: form validation failed.",
            form_result.errors,
        )
    form_registry = form_result.output.registry

    concept_result = run_concept_pipeline(
        loaded_concepts,
        context=ConceptPipelineContext(form_registry=form_registry),
    )
    messages.extend(concept_result.diagnostics)
    if not isinstance(concept_result.output, ConceptCheckedRegistry):
        raise _abort(
            PropstoreFamily.CONCEPT,
            ConceptStage.CHECKED,
            "Build aborted: concept validation failed.",
            concept_result.errors,
        )

    context_ids: frozenset[str] = frozenset()
    if loaded_contexts or loaded_rules:
        context_result = run_context_pipeline(
            loaded_contexts, lifting_rules=loaded_rules
        )
        messages.extend(context_result.diagnostics)
        if not isinstance(context_result.output, ContextCheckedGraph):
            raise _abort(
                PropstoreFamily.CONTEXT,
                ContextStage.CHECKED,
                "Build aborted: context validation failed.",
                context_result.errors,
            )
        context_ids = context_result.output.context_ids

    compilation_context = build_compilation_context(
        concept_result.output,
        form_registry=form_registry,
        claims=tuple(loaded.claim for loaded in loaded_claims),
        context_ids=context_ids,
    )

    _enforce_cel_structural_invariants(
        loaded_claims, loaded_contexts, compilation_context.condition_registry
    )

    claim_result = run_claim_pipeline(
        ClaimFiles.from_sequence(loaded_claims, compilation_context)
    )
    messages.extend(claim_result.diagnostics)
    claim_bundle = (
        claim_result.output
        if isinstance(claim_result.output, ClaimCheckedBundle)
        else ClaimCheckedBundle()
    )

    return _CompiledRepository(
        concepts=tuple(loaded.concept for loaded in loaded_concepts),
        form_registry=form_registry,
        context_ids=context_ids,
        loaded_contexts=tuple(loaded.context for loaded in loaded_contexts),
        loaded_lifting_rules=tuple(loaded.rule for loaded in loaded_rules),
        claim_bundle=claim_bundle,
        compilation_context=compilation_context,
        messages=tuple(messages),
        concept_count=len(loaded_concepts),
        claim_count=len(loaded_claims),
    )


def compile_repository_checked_bundle(
    repo: Repository, *, commit: str | None
) -> RepositoryCheckedBundle | None:
    """Run the shared compiler and package the checked state for the sidecar build.

    Returns ``None`` when the repository has no concepts (nothing to project). This
    is the one bridge from the shared pass output to ``derived_build``; ``pks build``
    and ``pks validate`` still run the very same ``_compile_repository`` (PLAN.md
    §12.6), build only adding the materialize sink downstream of it.
    """

    compiled = _compile_repository(repo, commit=commit)
    if compiled.no_concepts:
        return None
    return RepositoryCheckedBundle(
        concepts=compiled.concepts,
        form_registry=compiled.form_registry,
        context_ids=compiled.context_ids,
        loaded_contexts=compiled.loaded_contexts,
        loaded_lifting_rules=compiled.loaded_lifting_rules,
        claim_bundle=compiled.claim_bundle,
        compilation_context=compiled.compilation_context,
        messages=compiled.messages,
    )


# --------------------------------------------------------------------------- #
# Terminal workflows (sink-only difference)
# --------------------------------------------------------------------------- #


def validate_repository(repo: Repository) -> RepositoryValidationSummary:
    """Run the shared semantic check set; report diagnostics, no sidecar write."""

    compiled = _compile_repository(repo, commit=None)
    if compiled.no_concepts:
        return RepositoryValidationSummary(
            concept_count=0, claim_count=0, messages=(), no_concepts=True
        )
    return RepositoryValidationSummary(
        concept_count=compiled.concept_count,
        claim_count=compiled.claim_count,
        messages=compiled.messages,
    )


_PHI_WARNING_CLASSES = frozenset({"PHI_NODE", "CONTEXT_PHI_NODE"})


def _stances(repo: Repository, commit: str | None) -> tuple[Stance, ...]:
    return tuple(
        handle.document
        for handle in repo.families.by_name("stance").iter_handles(commit=commit)
        if isinstance(handle.document, Stance)
    )


def _phi_groups(plan_conflicts: Sequence[object]) -> tuple[BuildPhiGroup, ...]:
    grouped: dict[str, list[str]] = {}
    for conflict in plan_conflicts:
        if not isinstance(conflict, ConflictProjection):
            continue
        if conflict.warning_class not in _PHI_WARNING_CLASSES:
            continue
        members = grouped.setdefault(conflict.concept_id, [])
        for claim_id in (conflict.claim_a_id, conflict.claim_b_id):
            if claim_id not in members:
                members.append(claim_id)
    return tuple(
        BuildPhiGroup(key=concept_id, claim_ids=tuple(sorted(members)))
        for concept_id, members in sorted(grouped.items())
    )


def build_repository(
    repo: Repository,
    *,
    force: bool = False,
    strict_authoring: bool = False,
) -> RepositoryBuildReport:
    """Run the shared check set, then materialise the world sidecar.

    The pipelines, the abort class, and the quarantine class are identical to
    :func:`validate_repository`; only the terminal sink differs (PLAN.md §12.6).
    After the shared compile, this materialises the content-addressed world sidecar
    (``derived_build.materialize_world_sidecar``) and summarises the conflict / phi
    compute from the build plan. The detailed sidecar-read stats (similar / history)
    remain a 9-1 ``WorldQuery`` seam; the conflict / phi summary here is taken from
    the plan, not fabricated.
    """

    commit = str(repo.require_git().head_sha())
    checked = compile_repository_checked_bundle(repo, commit=commit)
    if checked is None:
        return RepositoryBuildReport(
            concept_count=0, claim_count=0, no_concepts=True
        )

    authoring_lints = collect_authoring_lints(
        claims=checked.claims, stances=_stances(repo, commit)
    )
    if strict_authoring and authoring_lints:
        raise CompilerWorkflowError(
            f"Build aborted: {len(authoring_lints)} authoring error(s)",
            upgrade_lints_to_errors(authoring_lints),
        )

    plan = compile_sidecar_build_plan(repo, checked, commit=commit)
    handle, built = materialize_world_sidecar(
        repo, force=force, checked=checked, plan=plan, commit=commit
    )

    messages = (*checked.messages, *authoring_lints)
    warning_count = sum(1 for message in messages if message.is_warning)
    conflicts = tuple(
        BuildConflictLine(
            warning_class=conflict.warning_class,
            concept_id=conflict.concept_id,
            claim_a_id=conflict.claim_a_id,
            claim_b_id=conflict.claim_b_id,
        )
        for conflict in plan.conflicts
    )
    return RepositoryBuildReport(
        concept_count=len(checked.concepts),
        claim_count=len(checked.claims),
        conflict_count=plan.conflict_count,
        phi_node_count=plan.phi_node_count,
        warning_count=warning_count,
        rebuilt=built,
        conflicts=conflicts,
        phi_groups=_phi_groups(plan.conflicts),
        derived_store=BuildDerivedStoreHandle(
            projection_id=handle.projection_id,
            source_commit=handle.source_commit,
            cache_key=handle.cache_key,
            path=str(handle.path),
        ),
        messages=messages,
        sidecar_missing=False,
    )
