"""Repository-facing summaries for merge frameworks."""

from __future__ import annotations

from collections import defaultdict

from propstore.merge.merge_classifier import RepositoryMergeFramework
from argumentation.partial_af import enumerate_completions
from argumentation.partial_af import (
    credulously_accepted_arguments,
    skeptically_accepted_arguments,
)


__all__ = ["semantic_candidate_details", "summarize_merge_framework"]
