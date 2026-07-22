"""Semantic passes and stages for the ``claim`` family (flat charter).

The claim AUTHORED -> CHECKED pass does the real per-claim CHECKED compute: it
validates the claim against its type contract
(:mod:`propstore.claim_contracts`), type-checks its authored CEL conditions into
condition-ir's checked set (:mod:`propstore.claim_conditions`), checks its
``context_id`` against the known contexts, and normalises the claim (filling
``conditions_ir``).

Crucially, the claim pass ALWAYS returns a :class:`ClaimCheckedBundle` — even
when claims are invalid. A semantically invalid claim is retained as a
``blocked`` :class:`CheckedClaim` with its diagnostics; the runner never
short-circuits the claim pipeline, so ``build_repository`` does not abort. This
is the quarantine half of the Z1 split (claim/stance semantic invalidity
quarantines; form/concept/context validation failure aborts).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from propstore.claim_conditions import check_claim, check_claim_conditions
from propstore.claim_contracts import validate_claim
from propstore.compiler.context import CompilationContext
from propstore.compiler.ir import CheckedClaim, ClaimCheckedBundle
from propstore.families.claims import Claim, ClaimType
from propstore.families.registry import PropstoreFamily
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.runner import run_pipeline
from propstore.semantic_passes.types import (
    PassDiagnostic,
    PassResult,
    PipelineResult,
)

_FAMILY = PropstoreFamily.CLAIM


class ClaimStage(StrEnum):
    AUTHORED = "claim.authored"
    CHECKED = "claim.checked"


@dataclass(frozen=True)
class LoadedClaim:
    claim: Claim
    filename: str | None = None

    @property
    def claim_id(self) -> str:
        return self.claim.claim_id


@dataclass(frozen=True)
class ClaimFiles:
    claims: tuple[LoadedClaim, ...]
    context: CompilationContext

    @classmethod
    def from_sequence(
        cls,
        claims: Sequence[LoadedClaim],
        context: CompilationContext,
    ) -> ClaimFiles:
        return cls(claims=tuple(claims), context=context)


def _error(
    code: str,
    message: str,
    loaded: LoadedClaim,
    field: str | None,
) -> PassDiagnostic:
    return PassDiagnostic(
        level="error",
        code=code,
        message=message,
        family=_FAMILY,
        stage=ClaimStage.CHECKED,
        filename=loaded.filename,
        artifact_id=loaded.claim_id,
        pass_name="claim.check",
    )


def _check_one(
    loaded: LoadedClaim,
    context: CompilationContext,
) -> CheckedClaim:
    claim = loaded.claim
    diagnostics: list[PassDiagnostic] = []

    form = None
    concept_info = None
    form_concept_id = None
    if claim.claim_type is ClaimType.PARAMETER:
        form_concept_id = claim.output_concept
    elif claim.claim_type is ClaimType.MEASUREMENT:
        form_concept_id = claim.target_concept
    if form_concept_id is not None:
        concept = context.concepts_by_id.get(form_concept_id)
        if concept is not None and concept.lexical_entry is not None:
            form_name = concept.lexical_entry.physical_dimension_form
            if form_name is not None:
                form = context.form_registry.get(form_name)
                concept_info = context.condition_registry.get(concept.canonical_name)

    contract_report = validate_claim(
        claim,
        form=form,
        concept_info=concept_info,
    )
    for problem in contract_report.diagnostics:
        diagnostics.append(
            _error("claim.contract", problem.message, loaded, problem.field)
        )

    condition_report = check_claim_conditions(claim, context.condition_registry)
    for condition_problem in condition_report.diagnostics:
        diagnostics.append(
            _error(
                "claim.condition",
                f"{condition_problem.condition!r}: {condition_problem.message}",
                loaded,
                "conditions",
            )
        )

    if (
        claim.context_id is not None
        and context.context_ids
        and claim.context_id not in context.context_ids
    ):
        diagnostics.append(
            _error(
                "claim.context.dangling",
                f"claim '{claim.claim_id}' references unknown context "
                f"'{claim.context_id}'",
                loaded,
                "context_id",
            )
        )

    normalized = check_claim(claim, context.condition_registry)
    return CheckedClaim(
        claim=normalized,
        blocked=bool(diagnostics),
        diagnostics=tuple(diagnostics),
    )


class ClaimCheckPass:
    family = _FAMILY
    name = "claim.check"
    version = "1"
    input_stage = ClaimStage.AUTHORED
    output_stage = ClaimStage.CHECKED

    def run(self, value: ClaimFiles, context: object) -> PassResult[ClaimCheckedBundle]:
        checked = tuple(_check_one(loaded, value.context) for loaded in value.claims)
        bundle = ClaimCheckedBundle(claims=checked)
        return PassResult(output=bundle, diagnostics=bundle.diagnostics)


def register_claim_pipeline(registry: PipelineRegistry) -> None:
    registry.register(ClaimCheckPass, family=_FAMILY)


def run_claim_pipeline(value: ClaimFiles) -> PipelineResult[object]:
    registry = PipelineRegistry()
    register_claim_pipeline(registry)
    return run_pipeline(
        value,
        family=_FAMILY,
        start_stage=ClaimStage.AUTHORED,
        target_stage=ClaimStage.CHECKED,
        registry=registry,
        context=None,
    )
