import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from propstore.classify import classify_stance_async


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


def test_malformed_json_does_not_construct_reverse_stance() -> None:
    with patch("propstore.classify._require_litellm") as require_litellm:
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

    assert len(results) == 1
    assert results[0]["target"] == "claim-b"
    assert results[0]["type"] == "error"
