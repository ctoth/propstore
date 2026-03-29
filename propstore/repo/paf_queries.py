"""Completion-based query semantics for partial argumentation frameworks."""
from __future__ import annotations

from propstore.dung import (
    ArgumentationFramework,
    grounded_extension,
    preferred_extensions,
    stable_extensions,
)
from propstore.repo.merge_framework import (
    PartialArgumentationFramework,
    enumerate_paf_completions,
)


def _extensions_for_completion(
    completion: ArgumentationFramework,
    *,
    semantics: str,
) -> list[frozenset[str]]:
    if semantics == "grounded":
        return [grounded_extension(completion)]
    if semantics == "preferred":
        return [frozenset(extension) for extension in preferred_extensions(completion)]
    if semantics == "stable":
        return [frozenset(extension) for extension in stable_extensions(completion)]
    raise ValueError(f"Unknown semantics: {semantics}")


def skeptically_accepted_arguments(
    framework: PartialArgumentationFramework,
    *,
    semantics: str = "grounded",
) -> frozenset[str]:
    """Arguments accepted in every extension of every completion."""
    extensions = [
        extension
        for completion in enumerate_paf_completions(framework)
        for extension in _extensions_for_completion(completion, semantics=semantics)
    ]
    if not extensions:
        return frozenset()
    skeptical = set(framework.arguments)
    for extension in extensions:
        skeptical.intersection_update(extension)
    return frozenset(skeptical)


def credulously_accepted_arguments(
    framework: PartialArgumentationFramework,
    *,
    semantics: str = "grounded",
) -> frozenset[str]:
    """Arguments accepted in some extension of some completion."""
    credulous: set[str] = set()
    for completion in enumerate_paf_completions(framework):
        for extension in _extensions_for_completion(completion, semantics=semantics):
            credulous.update(extension)
    return frozenset(credulous)


__all__ = [
    "skeptically_accepted_arguments",
    "credulously_accepted_arguments",
]
