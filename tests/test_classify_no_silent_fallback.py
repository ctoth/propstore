from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch


def _claim(id_: str) -> dict[str, str]:
    return {"id": id_, "text": f"{id_} text", "source_paper": "paper"}


def _response(payload: dict[str, object]) -> MagicMock:
    response = MagicMock()
    message = MagicMock()
    message.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = message
    response.choices = [choice]
    return response


def test_classify_rejects_bidirectional_shape_without_silent_forward_fallback() -> None:
    from propstore.heuristic.classify import classify_stance_async

    with patch("propstore.heuristic.classify._require_litellm") as require_litellm:
        litellm = MagicMock()
        litellm.acompletion = AsyncMock(
            side_effect=[
                _response({"forward": {"type": "supports", "strength": "strong"}}),
                _response({"reverse": {"type": "undercuts", "strength": "weak"}}),
            ]
        )
        require_litellm.return_value = litellm

        results = asyncio.run(
            classify_stance_async(
                _claim("claim-a"),
                _claim("claim-b"),
                "test-model",
                asyncio.Semaphore(1),
            )
        )

    assert litellm.acompletion.await_count == 2
    assert [result["type"] for result in results] == ["abstain", "abstain"]
    for result in results:
        resolution = result["resolution"]
        assert resolution["confidence"] is None
        assert resolution["opinion"]["provenance"]["status"] == "vacuous"
        assert resolution["opinion"]["provenance"]["operations"] == [
            "llm_output_shape_unknown"
        ]


def test_classify_missing_calibration_uses_null_confidence() -> None:
    from propstore.heuristic.classify import classify_stance_async

    with patch("propstore.heuristic.classify._require_litellm") as require_litellm:
        litellm = MagicMock()
        litellm.acompletion = AsyncMock(
            side_effect=[
                _response(
                    {
                        "type": "supports",
                        "strength": "strong",
                        "note": "forward",
                        "conditions_differ": None,
                    }
                ),
                _response(
                    {
                        "type": "undercuts",
                        "strength": "weak",
                        "note": "reverse",
                        "conditions_differ": None,
                    }
                ),
            ]
        )
        require_litellm.return_value = litellm

        results = asyncio.run(
            classify_stance_async(
                _claim("claim-a"),
                _claim("claim-b"),
                "test-model",
                asyncio.Semaphore(1),
            )
        )

    assert [result["type"] for result in results] == ["supports", "undercuts"]
    for result in results:
        assert result["resolution"]["opinion"] is None
        assert result["resolution"]["confidence"] is None
        assert result["resolution"]["unresolved_calibration"]["reason"] == "missing_base_rate"
