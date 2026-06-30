"""The import subsystem: typed import contract + repository import.

An import is non-committal: every external row becomes a defeasible source-branch
claim with honest provenance, never a privileged canonical fact
([[feedback_imports_are_opinions]]). :mod:`contract` defines the typed manifest
an importer must provide; :mod:`repository_import` lands it on a source branch via
the ordinary source-authoring path; :mod:`machinery` is the lower-level per-row
authored-assertion compiler.
"""

from __future__ import annotations

from propstore.importing.contract import (
    ImportClaimRow,
    ImportConceptRow,
    ImportManifest,
    ImportResult,
    ImportStanceRow,
)
from propstore.importing.machinery import (
    AuthoredAssertionForm,
    AuthoredAssertionSurface,
    CompiledImportAssertion,
    EquivalenceWitness,
    EquivalenceWitnessStore,
    ExternalInferenceSurface,
    ImportAuthoredFormLens,
    ImportCompiler,
    ImportMetadata,
    SurfaceRoleBinding,
)
from propstore.importing.repository_import import (
    RepositoryImportPlan,
    RepositoryImportResult,
    commit_repository_import,
    import_manifest,
    plan_repository_import,
)

__all__ = [
    "AuthoredAssertionForm",
    "AuthoredAssertionSurface",
    "CompiledImportAssertion",
    "EquivalenceWitness",
    "EquivalenceWitnessStore",
    "ExternalInferenceSurface",
    "ImportAuthoredFormLens",
    "ImportClaimRow",
    "ImportCompiler",
    "ImportConceptRow",
    "ImportManifest",
    "ImportMetadata",
    "ImportResult",
    "ImportStanceRow",
    "RepositoryImportPlan",
    "RepositoryImportResult",
    "SurfaceRoleBinding",
    "commit_repository_import",
    "import_manifest",
    "plan_repository_import",
]
