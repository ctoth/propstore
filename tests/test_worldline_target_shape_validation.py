"""WS-J Step 8/J-M3: revision targets are validated at definition parse time."""

from __future__ import annotations

import pytest

from propstore.worldline import WorldlineDefinition
from propstore.worldline.definition import WorldlineRevisionTargetValidationError


def test_ws_j_worldline_revision_target_rejects_unprefixed_concept_names() -> None:
    with pytest.raises(WorldlineRevisionTargetValidationError, match="some-concept-name"):
        WorldlineDefinition.from_dict(
            {
                "id": "bad_revision_target",
                "targets": ["target"],
                "revision": {
                    "operation": "contract",
                    "target": "some-concept-name",
                },
            }
        )
