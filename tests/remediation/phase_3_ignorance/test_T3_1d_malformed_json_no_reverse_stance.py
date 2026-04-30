import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from propstore.heuristic.classify import classify_stance_async


def _claim(claim_id: str) -> dict:
    return {"id": claim_id, "text": f"{claim_id} text", "source_paper": "test"}


def _malformed_response() -> MagicMock:
    response = MagicMock()
    message = MagicMock()
    message.content = "{not-json"
    choice = MagicMock()
    choice.message = message
    response.choices = [choice]
    return response


def test_malformed_json_produces_independent_directional_errors() -> None:
    with patch("propstore.heuristic.classify._require_litellm") as require_litellm:
        litellm = MagicMock()
        litellm.acompletion = AsyncMock(return_value=_malformed_response())
        require_litellm.return_value = litellm

        results = asyncio.run(
            classify_stance_async(
                _claim("claim-a"),
                _claim("claim-b"),
                "test-model",
                asyncio.Semaphore(1),
            ),
        )

    assert litellm.acompletion.await_count == 2
    assert len(results) == 2
    assert [result["target"] for result in results] == ["claim-b", "claim-a"]
    assert [result["type"] for result in results] == ["error", "error"]
    assert results[0]["resolution"]["llm_call_id"] != results[1]["resolution"]["llm_call_id"]
