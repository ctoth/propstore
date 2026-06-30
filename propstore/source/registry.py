"""Primary-branch concept registry reads for source promotion.

Promotion must decide, for every concept a source branch proposes, whether it
already exists canonically (reuse its id) or is new (mint one). These readers
project the master-branch concept family into the lookups that decision needs —
by artifact id and by normalised canonical name. They never mutate; the promote
subsystem composes them.

The parameterization-group merge *preview* (a heuristic projection over concept
parameterization relationships) is not modelled on the flat rewrite ``Concept``
charter yet and is deferred with the rest of the render-time preview surface;
see ``docs/rewrite/deferred-tests.md``.
"""

from __future__ import annotations

from propstore.families.concepts import Concept
from propstore.families.sources import SourceConceptRegistryMatchDocument
from propstore.repository import Repository

from .common import normalize_source_slug


def _primary_tip(repo: Repository) -> str | None:
    git = repo.git
    if git is None:
        return None
    return git.branch_sha(git.primary_branch_name())


def load_primary_branch_concepts(repo: Repository) -> dict[str, Concept]:
    """Return every canonical concept on the primary branch, keyed by id."""

    tip = _primary_tip(repo)
    if tip is None:
        return {}
    concepts: dict[str, Concept] = {}
    for handle in repo.families.concept.iter_handles(commit=tip):
        concept = handle.document
        if isinstance(concept, Concept):
            concepts[concept.concept_id] = concept
    return concepts


def primary_branch_concept_id_by_name(repo: Repository) -> dict[str, str]:
    """Map each canonical concept's normalised name to its id (last wins).

    The normalised-name key is ``normalize_source_slug(canonical_name)`` folded to
    lower case, the same key :func:`primary_branch_concept_match` compares, so a
    source handle resolves to an existing concept by name rather than by minting a
    rival id for a concept that already exists.
    """

    mapping: dict[str, str] = {}
    for concept in load_primary_branch_concepts(repo).values():
        mapping[normalize_source_slug(concept.canonical_name).casefold()] = (
            concept.concept_id
        )
    return mapping


def primary_branch_concept_match(
    repo: Repository, name: str
) -> SourceConceptRegistryMatchDocument | None:
    """Return the canonical concept matching *name* by canonical name, or ``None``."""

    target = normalize_source_slug(name).casefold()
    for concept in load_primary_branch_concepts(repo).values():
        if normalize_source_slug(concept.canonical_name).casefold() == target:
            return SourceConceptRegistryMatchDocument(
                artifact_id=concept.concept_id,
                canonical_name=concept.canonical_name,
            )
    return None
