"""Compile the checked repository into the world-sidecar build plan.

The reference tree compiled per-family ``compile_*_sidecar_rows`` into a large
``SidecarBuildPlan`` of ``ProjectionRow`` tuples. In the charter rewrite the
*projection rows vanish*: every authored family is projected directly from its
charter at materialize time (``session.add_family``), so this module only assembles
the **checked compute** that does not fall out of a charter:

* the detected pairwise :class:`~propstore.families.conflicts.ConflictProjection`
  rows (the conflict detector over the checked claim set, with the lifting system
  feeding cross-context phi detection);
* the :class:`~propstore.families.diagnostics.BuildDiagnostic` rows — semantic-pass
  diagnostics, blocked-claim errors, authoring lints, and the quarantined
  dangling stance / justification / micropublication references.

Quarantine, not reject (Z1): a stance / justification / micropublication that
references a claim absent from the build's claim set is **not** dropped. Its row
still inserts at materialize time (under advisory foreign keys); the plan only
records a blocking :class:`BuildDiagnostic` so render policy can hide it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from propstore.build_diagnostics import (
    QuarantineDiagnostic,
    collect_authoring_lints,
    pass_to_build_diagnostic,
    quarantine_to_build_diagnostic,
)
from propstore.compiler.context import CompilationContext
from propstore.compiler.ir import ClaimCheckedBundle
from propstore.conflict_detector import detect_conflicts
from propstore.conflict_detector.models import ConflictClaim, ConflictClass, ConflictRecord
from propstore.context_lifting import LiftingSystem
from propstore.core.graph_types import ParameterizationEdge
from propstore.families.claims import Claim
from propstore.families.concepts import Concept
from propstore.families.conflicts import ConflictProjection
from propstore.families.contexts import Context, LiftingRule
from propstore.families.diagnostics import BuildDiagnostic
from propstore.families.forms import FormDefinition
from propstore.families.justifications import Justification
from propstore.families.micropublications import Micropublication
from propstore.families.relations import Stance
from propstore.semantic_passes.types import PassDiagnostic
from propstore.world.queries import derive_parameterizations

if TYPE_CHECKING:
    from propstore.repository import Repository

_PHI_CLASSES = frozenset({ConflictClass.PHI_NODE, ConflictClass.CONTEXT_PHI_NODE})


@dataclass(frozen=True)
class RepositoryCheckedBundle:
    """The checked semantic state of a repository, ready to project.

    Assembled from the shared compiler pass output
    (:func:`propstore.compiler.workflows._compile_repository`) so ``pks build`` and
    ``pks validate`` share one check set (PLAN.md §12.6). It carries everything the
    plan compiler needs that is *not* re-readable trivially from the repo: the
    checked claim bundle (blocked claims included), the compilation context (CEL +
    concept registries), and the loaded contexts / lifting rules that drive lifting
    and cross-context conflict detection.
    """

    concepts: tuple[Concept, ...]
    form_registry: Mapping[str, FormDefinition]
    context_ids: frozenset[str]
    loaded_contexts: tuple[Context, ...]
    loaded_lifting_rules: tuple[LiftingRule, ...]
    claim_bundle: ClaimCheckedBundle
    compilation_context: CompilationContext
    messages: tuple[PassDiagnostic, ...]

    @property
    def claims(self) -> tuple[Claim, ...]:
        """Every checked claim's normalised document (blocked claims included)."""

        return tuple(checked.claim for checked in self.claim_bundle.claims)


@dataclass(frozen=True)
class SidecarBuildPlan:
    """The checked compute written into the world sidecar beyond raw projection.

    ``conflicts`` and ``diagnostics`` are the charter documents the build inserts
    via ``session.add_family``; ``quarantine_diagnostics`` is retained for the
    build report (it is already folded into ``diagnostics``).
    """

    conflicts: tuple[ConflictProjection, ...]
    diagnostics: tuple[BuildDiagnostic, ...]
    quarantine_diagnostics: tuple[QuarantineDiagnostic, ...]

    @property
    def conflict_count(self) -> int:
        return len(self.conflicts)

    @property
    def phi_node_count(self) -> int:
        return sum(
            1
            for conflict in self.conflicts
            if conflict.warning_class in {cls.value for cls in _PHI_CLASSES}
        )


def _claim_sources(
    micropubs: Iterable[Micropublication],
) -> dict[str, str | None]:
    """Per-claim source identity derived from micropublication bundles.

    The ``Claim`` charter is provenance-free, so the paper asserting a claim
    lives on the :class:`Micropublication` bundling it (``source``). A claim
    bundled under exactly one distinct source carries that source into the
    detector, where :meth:`ConflictClaim.with_source_condition` folds it into a
    ``source == …`` condition so the solver treats papers as disjoint regimes.
    A claim asserted by multiple sources gets none — conditions conjoin, and a
    multi-source claim genuinely is not source-gated. An unbundled claim
    honestly has no source (never fabricated).
    """

    sources: dict[str, set[str]] = {}
    for micropub in micropubs:
        if micropub.source is None:
            continue
        for claim_ref in micropub.claims:
            sources.setdefault(claim_ref, set()).add(micropub.source)
    return {
        claim_id: next(iter(papers)) if len(papers) == 1 else None
        for claim_id, papers in sources.items()
    }


def _conflict_claims(
    claims: tuple[Claim, ...], claim_sources: Mapping[str, str | None]
) -> list[ConflictClaim]:
    return [
        ConflictClaim.from_claim(
            claim, source_paper=claim_sources.get(claim.claim_id)
        ).with_source_condition()
        for claim in claims
        if claim.claim_id
    ]


def _parameterizations_by_output(
    claims: tuple[Claim, ...],
) -> dict[str, tuple[ParameterizationEdge, ...]]:
    """Canonical parameterization edges derived from EQUATION claims, by output."""

    grouped: dict[str, list[ParameterizationEdge]] = {}
    for edge in derive_parameterizations(claims):
        grouped.setdefault(str(edge.output_concept_id), []).append(edge)
    return {concept_id: tuple(edges) for concept_id, edges in grouped.items()}


def _conflict_row(record: ConflictRecord, *, index: int) -> ConflictProjection:
    return ConflictProjection(
        conflict_id=f"conflict:{index:08d}",
        warning_class=record.warning_class.value,
        concept_id=record.concept_id,
        claim_a_id=record.claim_a_id,
        claim_b_id=record.claim_b_id,
        value_a=record.value_a,
        value_b=record.value_b,
        derivation_chain=record.derivation_chain,
    )


def _compile_conflicts(
    checked: RepositoryCheckedBundle,
    micropubs: tuple[Micropublication, ...],
) -> tuple[ConflictProjection, ...]:
    conflict_claims = _conflict_claims(checked.claims, _claim_sources(micropubs))
    if not conflict_claims:
        return ()
    lifting_system = LiftingSystem(
        contexts=checked.loaded_contexts,
        lifting_rules=checked.loaded_lifting_rules,
    )
    records = detect_conflicts(
        conflict_claims,
        {str(concept.concept_id): concept for concept in checked.concepts},
        checked.compilation_context.cel_registry,
        lifting_system=lifting_system,
        forms=dict(checked.form_registry),
        parameterizations=_parameterizations_by_output(checked.claims),
    )
    return tuple(
        _conflict_row(record, index=index) for index, record in enumerate(records)
    )


def _iter_documents(repo: Repository, family_name: str, commit: str | None) -> list[object]:
    return [
        handle.document
        for handle in repo.families.by_name(family_name).iter_handles(commit=commit)
    ]


def _missing(claim_id: str | None, valid_claims: frozenset[str]) -> bool:
    return claim_id is None or claim_id not in valid_claims


def _quarantine_dangling_references(
    repo: Repository, *, commit: str | None, valid_claims: frozenset[str]
) -> tuple[QuarantineDiagnostic, ...]:
    """Find stance / justification / micropublication refs to absent claims.

    The referencing rows still insert at materialize time; this only records the
    blocking diagnostics so render policy can hide them.
    """

    diagnostics: list[QuarantineDiagnostic] = []
    for document in _iter_documents(repo, "stance", commit):
        stance = document
        if not isinstance(stance, Stance):
            continue
        for label, ref in (
            ("source", stance.source_claim_id),
            ("target", stance.target_claim_id),
        ):
            if _missing(ref, valid_claims):
                diagnostics.append(
                    QuarantineDiagnostic(
                        artifact_id=stance.stance_id,
                        kind="stance",
                        diagnostic_kind="stance_validation",
                        message=(
                            f"stance {stance.stance_id!r} references nonexistent "
                            f"{label} claim {ref!r}"
                        ),
                    )
                )
    for document in _iter_documents(repo, "justification", commit):
        justification = document
        if not isinstance(justification, Justification):
            continue
        if _missing(justification.conclusion, valid_claims):
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=justification.justification_id,
                    kind="justification",
                    diagnostic_kind="justification_validation",
                    message=(
                        f"justification {justification.justification_id!r} references "
                        f"nonexistent conclusion {justification.conclusion!r}"
                    ),
                )
            )
        for premise in justification.premises:
            if _missing(premise, valid_claims):
                diagnostics.append(
                    QuarantineDiagnostic(
                        artifact_id=justification.justification_id,
                        kind="justification",
                        diagnostic_kind="justification_validation",
                        message=(
                            f"justification {justification.justification_id!r} references "
                            f"nonexistent premise {premise!r}"
                        ),
                    )
                )
    for document in _iter_documents(repo, "micropublication", commit):
        micropub = document
        if not isinstance(micropub, Micropublication):
            continue
        for claim_ref in micropub.claims:
            if _missing(claim_ref, valid_claims):
                diagnostics.append(
                    QuarantineDiagnostic(
                        artifact_id=micropub.artifact_id,
                        kind="micropublication",
                        diagnostic_kind="micropublication_validation",
                        message=(
                            f"micropublication {micropub.artifact_id!r} references "
                            f"nonexistent claim {claim_ref!r}"
                        ),
                    )
                )
    return tuple(diagnostics)


def _stances(repo: Repository, commit: str | None) -> tuple[Stance, ...]:
    return tuple(
        document
        for document in _iter_documents(repo, "stance", commit)
        if isinstance(document, Stance)
    )


def compile_sidecar_build_plan(
    repo: Repository,
    checked: RepositoryCheckedBundle,
    *,
    commit: str | None,
) -> SidecarBuildPlan:
    """Assemble the conflict + diagnostic compute for the world sidecar.

    The authored families are projected directly from their charters at materialize
    time, so they do not appear here; this returns only the derived compute that
    must be written alongside them.
    """

    micropubs = tuple(
        document
        for document in _iter_documents(repo, "micropublication", commit)
        if isinstance(document, Micropublication)
    )
    conflicts = _compile_conflicts(checked, micropubs)
    valid_claims = frozenset(claim.claim_id for claim in checked.claims)
    quarantine = _quarantine_dangling_references(
        repo, commit=commit, valid_claims=valid_claims
    )
    authoring_lints = collect_authoring_lints(
        claims=checked.claims, stances=_stances(repo, commit)
    )

    diagnostics: list[BuildDiagnostic] = []
    counter = 0
    for message in (*checked.messages, *authoring_lints):
        diagnostics.append(
            pass_to_build_diagnostic(message, diagnostic_id=f"diag:{counter:08d}")
        )
        counter += 1
    for quarantine_diagnostic in quarantine:
        diagnostics.append(
            quarantine_to_build_diagnostic(
                quarantine_diagnostic, diagnostic_id=f"diag:{counter:08d}"
            )
        )
        counter += 1

    return SidecarBuildPlan(
        conflicts=conflicts,
        diagnostics=tuple(diagnostics),
        quarantine_diagnostics=quarantine,
    )
