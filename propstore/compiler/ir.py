"""Semantic IR for claim compilation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quire.references import ReferenceResolution as ResolvedReference

from propstore.cel_types import CheckedCelConditionSet
from propstore.claims import ClaimFileEntry
from propstore.diagnostics import SemanticDiagnostic, ValidationResult, diagnostics_to_validation_result
from propstore.families.claims.documents import ClaimDocument


@dataclass(frozen=True)
class SemanticStance:
    """Semantic view of a claim stance after binding."""

    data: dict[str, Any]
    target_ref: ResolvedReference


@dataclass(frozen=True)
class SemanticClaim:
    """Semantic claim after normalization and binding."""

    filename: str
    source_paper: str
    artifact_id: str | None
    claim_type: str | None
    authored_claim: dict[str, Any]
    resolved_claim: ClaimDocument
    concept_ref: ResolvedReference | None = None
    target_concept_ref: ResolvedReference | None = None
    concept_refs: tuple[ResolvedReference, ...] = ()
    variable_refs: tuple[ResolvedReference, ...] = ()
    parameter_refs: tuple[ResolvedReference, ...] = ()
    stances: tuple[SemanticStance, ...] = ()
    checked_conditions: CheckedCelConditionSet | None = None


@dataclass(frozen=True)
class SemanticClaimFile:
    """Semantic view of a single authored claim file."""

    loaded_entry: ClaimFileEntry
    normalized_entry: ClaimFileEntry
    claims: tuple[SemanticClaim, ...] = ()


@dataclass(frozen=True)
class ClaimCompilationBundle:
    """The result of compiling authored claim files into semantic IR."""

    context: Any
    normalized_claim_files: tuple[ClaimFileEntry, ...]
    semantic_files: tuple[SemanticClaimFile, ...]
    diagnostics: tuple[SemanticDiagnostic, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return all(not diagnostic.is_error for diagnostic in self.diagnostics)

    def to_validation_result(self) -> ValidationResult:
        return diagnostics_to_validation_result(list(self.diagnostics))
