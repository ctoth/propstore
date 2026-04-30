from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


def _claim(id_: str, text: str) -> dict[str, str]:
    return {"id": id_, "text": text, "source_paper": f"paper-{id_}"}


def _response(payload: dict[str, object]) -> MagicMock:
    response = MagicMock()
    message = MagicMock()
    message.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = message
    response.choices = [choice]
    return response


def test_classify_forward_reverse_independent_llm_calls() -> None:
    from propstore.heuristic.classify import classify_stance_async

    forward_response = _response(
        {
            "type": "supports",
            "strength": "strong",
            "note": "A corroborates B.",
            "conditions_differ": None,
        }
    )
    reverse_response = _response(
        {
            "type": "undercuts",
            "strength": "weak",
            "note": "B challenges A's method.",
            "conditions_differ": None,
        }
    )
    with patch("propstore.heuristic.classify._require_litellm") as require_litellm:
        litellm = MagicMock()
        litellm.acompletion = AsyncMock(side_effect=[forward_response, reverse_response])
        require_litellm.return_value = litellm

        results = asyncio.run(
            classify_stance_async(
                _claim("a", "claim a"),
                _claim("b", "claim b"),
                "test-model",
                asyncio.Semaphore(1),
            )
        )

    assert litellm.acompletion.await_count == 2
    calls = litellm.acompletion.await_args_list
    prompts = [call.kwargs["messages"][0]["content"] for call in calls]
    assert prompts[0] != prompts[1]
    assert "FROM Claim A" in prompts[0]
    assert "FROM Claim B" in prompts[1]

    assert [stance["target"] for stance in results] == ["b", "a"]
    assert [stance["type"] for stance in results] == ["supports", "undercuts"]
    assert results[0]["resolution"]["llm_call_id"] != results[1]["resolution"]["llm_call_id"]
    assert results[0]["resolution"]["prompt"] == prompts[0]
    assert results[1]["resolution"]["prompt"] == prompts[1]
    assert results[0]["resolution"]["raw_response"] == json.loads(
        forward_response.choices[0].message.content
    )
    assert results[1]["resolution"]["raw_response"] == json.loads(
        reverse_response.choices[0].message.content
    )


@pytest.mark.property
@given(
    forward_type=st.sampled_from(["supports", "rebuts", "undercuts", "none"]),
    reverse_type=st.sampled_from(["supports", "rebuts", "undercuts", "none"]),
)
@settings(max_examples=32)
def test_classify_preserves_generated_directional_perspectives(
    forward_type: str,
    reverse_type: str,
) -> None:
    """WS-K property: reversing source/target cannot reuse the same payload."""
    from propstore.heuristic.classify import classify_stance_async

    forward_response = _response(
        {
            "type": forward_type,
            "strength": "moderate",
            "note": f"forward {forward_type}",
            "conditions_differ": None,
        }
    )
    reverse_response = _response(
        {
            "type": reverse_type,
            "strength": "weak",
            "note": f"reverse {reverse_type}",
            "conditions_differ": None,
        }
    )
    with patch("propstore.heuristic.classify._require_litellm") as require_litellm:
        litellm = MagicMock()
        litellm.acompletion = AsyncMock(side_effect=[forward_response, reverse_response])
        require_litellm.return_value = litellm

        results = asyncio.run(
            classify_stance_async(
                _claim("a", "claim a"),
                _claim("b", "claim b"),
                "test-model",
                asyncio.Semaphore(1),
            )
        )

    assert litellm.acompletion.await_count == 2
    assert [stance["target"] for stance in results] == ["b", "a"]
    assert [stance["type"] for stance in results] == [forward_type, reverse_type]
    assert results[0]["resolution"]["raw_response"] != results[1]["resolution"]["raw_response"]
