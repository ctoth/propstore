"""Claim compiler front-end and middle-end helpers."""

from propstore.compiler.context import (
    CompilationContext,
    build_compilation_context_from_loaded,
    build_compilation_context_from_paths,
    build_compilation_context_from_repo,
    compilation_context_from_legacy_registry,
)
from propstore.compiler.ir import (
    ClaimCompilationBundle,
    ResolvedReference,
    SemanticClaim,
    SemanticClaimFile,
    SemanticDiagnostic,
    SemanticStance,
)
from propstore.compiler.passes import compile_claim_files

__all__ = [
    "ClaimCompilationBundle",
    "CompilationContext",
    "ResolvedReference",
    "SemanticClaim",
    "SemanticClaimFile",
    "SemanticDiagnostic",
    "SemanticStance",
    "build_compilation_context_from_loaded",
    "build_compilation_context_from_paths",
    "build_compilation_context_from_repo",
    "compilation_context_from_legacy_registry",
    "compile_claim_files",
]
