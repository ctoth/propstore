"""The ``Concept`` entity — Phase 1 walking-skeleton charter.

This is the *thinnest* end-to-end entity: enough of a concept to prove the
rewrite's central thesis — that authoring ONE quire charter class makes the
git-stored document, the SQL sidecar projection, and the serialized contract all
fall out of field annotations, with no hand-authored DTO/Record/Row/payload
mass. Phase 2 grows this into the full lemon model (entries/forms/senses, qualia,
proto-roles, description-kinds, temporal/coreference); none of that lives here.

Discipline anchored by this module (PLAN.md §12):

* ONE canonical ``Concept`` type. There is no ``ConceptDocument`` /
  ``ConceptRecord`` / ``ConceptRow`` / ``Loaded*`` second spelling and no
  ``to_payload`` / ``from_payload`` / ``coerce_`` conversion anywhere.
* Identity is the authored content keyed by ``concept_id``. Provenance is NOT a
  field of the concept and therefore can never enter concept identity.
* The stored form is the RAW authored form. No normalization is baked at
  storage time; any normalization is a render-time derivation.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from quire.charter_class import CharterDoc, charter, charter_field


class ConceptStatus(str, Enum):
    """Authoring lifecycle status of a concept.

    A concept's status never gates whether it reaches storage — every authored
    concept is stored and projected regardless of status (non-commitment). The
    status is read only at *render* time, where a :class:`RenderPolicy`
    (``propstore.render``) decides which statuses are visible. ``DRAFT`` and
    ``BLOCKED`` concepts are present in the sidecar but hidden by the default
    render policy; ``AUTHORED`` is the clean, default-visible state.
    """

    AUTHORED = "authored"
    DRAFT = "draft"
    BLOCKED = "blocked"


@charter(
    key="concept",
    name="concept",
    contract_version="2026.06.28",
    placement="concept",
    identity_field="concept_id",
    semantic="propstore.concept",
)
class Concept(CharterDoc):
    """A minimal semantic concept.

    The class *is* the document: its annotated attributes are exactly the stored
    document fields and the sidecar projection columns. ``concept_id`` is the
    identity (primary key); ``definition`` is optional. No provenance field
    exists, so identity is provenance-free by construction.
    """

    concept_id: Annotated[str, charter_field(primary_key=True)]
    canonical_name: str
    status: ConceptStatus = ConceptStatus.AUTHORED
    definition: str | None = None
