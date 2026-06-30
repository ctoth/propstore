"""The canonical CEL concept registry built from the concept + form families.

A CEL expression in a claim condition or context assumption refers to concepts
by their ``concept_id``; condition-ir type-checks the expression against a
``Mapping[str, ConceptInfo]`` keyed by exactly that id (see
``condition_ir.cel_frontend``). This module builds that mapping from authored
:class:`~propstore.families.concepts.Concept` charters, resolving each concept's
measurement :class:`~condition_ir.KindType` from its linked physical-dimension
:class:`~propstore.families.forms.FormDefinition`.

Substrate boundary (CLAUDE.md): the registry *is* condition-ir's own
``ConceptInfo`` keyed by id — there is no propstore registry type. The lowering
of a propstore ``Concept`` into ``ConceptInfo`` and the synthetic-binding
parameterisation both reuse :mod:`propstore.claim_conditions` (which composes
condition-ir directly); this module only resolves the per-concept ``kind`` and
category metadata from the form family.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from condition_ir import ConceptInfo, KindType

from propstore.claim_conditions import condition_registry, lower_concept
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition


def concept_kind(
    concept: Concept,
    form_registry: Mapping[str, FormDefinition],
) -> KindType:
    """Resolve a concept's measurement kind from its linked form.

    A concept carries its physical dimensions on the lemon entry side
    (``lexical_entry.physical_dimension_form``), which names a
    :class:`FormDefinition`; that form's ``kind`` is the concept's measurement
    kind. A concept with no dimensional form has no declared kind — it defaults
    to :attr:`KindType.CATEGORY` (an extensible category), the most permissive
    non-quantitative kind, so CEL type-checking can still proceed. This is honest
    ignorance, not a fabricated quantity.
    """

    entry = concept.lexical_entry
    if entry is not None and entry.physical_dimension_form:
        form = form_registry.get(entry.physical_dimension_form)
        if form is not None:
            return form.kind
    return KindType.CATEGORY


def _category_extensible(
    concept: Concept,
    form_registry: Mapping[str, FormDefinition],
) -> bool:
    """Whether a concept's category is extensible (defaults to ``True``).

    Read off the linked form's ``extensible`` parameter when present. Enumerated
    category value sets are not projected into the CEL registry in this slice —
    a category concept is treated as extensible with no fixed value set, which is
    the permissive (honest) default for type-checking.
    """

    entry = concept.lexical_entry
    if entry is None or not entry.physical_dimension_form:
        return True
    form = form_registry.get(entry.physical_dimension_form)
    if form is None:
        return True
    raw_extensible = form.parameters.get("extensible")
    return True if raw_extensible is None else bool(raw_extensible)


def concept_info_from_concept(
    concept: Concept,
    form_registry: Mapping[str, FormDefinition],
) -> ConceptInfo:
    """Lower one authored ``Concept`` into condition-ir's ``ConceptInfo``.

    The ``kind`` is resolved from the concept's linked form and the category's
    extensibility from that form's parameters. The lowering itself is
    :func:`propstore.claim_conditions.lower_concept` — this module never mirrors
    ``ConceptInfo``.
    """

    kind = concept_kind(concept, form_registry)
    return lower_concept(
        concept,
        kind,
        category_extensible=_category_extensible(concept, form_registry),
    )


def build_canonical_cel_registry(
    concepts: Iterable[Concept],
    form_registry: Mapping[str, FormDefinition],
    *,
    synthetic_binding_names: Iterable[str] = (),
) -> dict[str, ConceptInfo]:
    """Build the id-keyed CEL registry from concepts + forms, with synthetic bindings.

    The result is condition-ir's registry shape (``{concept_id: ConceptInfo}``)
    plus the requested synthetic bindings, ready to pass to
    ``check_cel_expression`` / the ``ConditionSolver``. Duplicate concept ids are
    detected and reported by the concept semantic pass, not here.
    """

    infos = [concept_info_from_concept(concept, form_registry) for concept in concepts]
    return condition_registry(infos, synthetic_binding_names=synthetic_binding_names)


__all__ = [
    "concept_kind",
    "concept_info_from_concept",
    "build_canonical_cel_registry",
]
