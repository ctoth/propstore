"""Source-of-truth storage for a propstore knowledge repository.

This is the bottom architectural layer. The canonical multi-family storage
surface is :class:`propstore.repository.Repository` (git + bound family registry
+ snapshot); this package owns the git policy, the branch/materialize snapshot,
and the concept sidecar-build helper.
"""

from __future__ import annotations

from propstore.storage.concept_repository import ConceptRepository
from propstore.storage.git_policy import PROPSTORE_GIT_POLICY

__all__ = ["PROPSTORE_GIT_POLICY", "ConceptRepository"]
