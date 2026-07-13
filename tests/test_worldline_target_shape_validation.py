"""WS-J Step 8/J-M3: revision targets are validated at definition parse time."""

from __future__ import annotations

import pytest

from propstore.worldline.definition import WorldlineDefinition


def test_ws_j_worldline_revision_target_rejects_unprefixed_concept_names() -> None:
    codec = WorldlineDefinition.__charter__.document_codec()
    with pytest.raises(ValueError, match="some-concept-name"):
        codec.convert(
            {
                "id": "bad_revision_target",
                "targets": ["target"],
                "revision": {
                    "operation": "contract",
                    "target": "some-concept-name",
                },
            },
            WorldlineDefinition,
            source="test invalid worldline revision target",
        )
