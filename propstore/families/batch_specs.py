from __future__ import annotations

# NOTE: Temporary compatibility surface for source batch callers until Quire
# exposes generic ArtifactFamily batch IO from FamilyCharter.batch_specs.

from propstore.families.claims.declaration import (
    CLAIM_BATCH_SPEC,
    SOURCE_CLAIM_BATCH_SPEC,
    SOURCE_JUSTIFICATION_BATCH_SPEC,
)
from propstore.families.concepts.declaration import SOURCE_CONCEPT_BATCH_SPEC
from propstore.families.micropublications.declaration import SOURCE_MICROPUBLICATION_BATCH_SPEC
from propstore.families.stances.declaration import SOURCE_STANCE_BATCH_SPEC

__all__ = [
    "CLAIM_BATCH_SPEC",
    "SOURCE_CLAIM_BATCH_SPEC",
    "SOURCE_CONCEPT_BATCH_SPEC",
    "SOURCE_JUSTIFICATION_BATCH_SPEC",
    "SOURCE_MICROPUBLICATION_BATCH_SPEC",
    "SOURCE_STANCE_BATCH_SPEC",
]
