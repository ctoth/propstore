"""Semantic IR for claim compilation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from propstore.claim_files import LoadedClaimFile
from propstore.diagnostics import SemanticDiagnostic, ValidationResult, diagnostics_to_validation_result


@dataclass(frozen=True)
class ResolvedReference:
    """A bound reference together with its resolution provenance."""

    raw_text: str
    target_kind: str
    resolved_id: str | None
    matched_by: str | None
    matched_text: str | None
    ambiguous_candidates: tuple[str, ...] = ()


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
    resolved_claim: dict[str, Any]
    concept_ref: ResolvedReference | None = None
    target_concept_ref: ResolvedReference | None = None
    concept_refs: tuple[ResolvedReference, ...] = ()
    variable_refs: tuple[ResolvedReference, ...] = ()
    parameter_refs: tuple[ResolvedReference, ...] = ()
    stances: tuple[SemanticStance, ...] = ()


@dataclass(frozen=True)
class SemanticClaimFile:
    """Semantic view of a single authored claim file."""

    loaded_entry: LoadedClaimFile
    normalized_entry: LoadedClaimFile
    claims: tuple[SemanticClaim, ...] = ()


@dataclass(frozen=True)
class ClaimCompilationBundle:
    """The result of compiling authored claim files into semantic IR."""

    context: Any
    normalized_claim_files: tuple[LoadedClaimFile, ...]
    semantic_files: tuple[SemanticClaimFile, ...]
    diagnostics: tuple[SemanticDiagnostic, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return all(not diagnostic.is_error for diagnostic in self.diagnostics)

    def to_validation_result(self) -> ValidationResult:
        return diagnostics_to_validation_result(list(self.diagnostics))
