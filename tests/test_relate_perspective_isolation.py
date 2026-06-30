"""relate_all keeps each direction's perspective source distinct (non-commitment).

A self-contained in-memory store stands in for the sidecar-backed claim store; the
classifier is stubbed so the test exercises orchestration, not the LLM.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any

import pytest


class _Store:
    def __init__(self) -> None:
        self._claims = {
            "claim-a": {"id": "claim-a", "text": "A says alpha.", "source_paper": "paper-a"},
            "claim-b": {"id": "claim-b", "text": "B says beta.", "source_paper": "paper-b"},
        }

    def load_embedding_extension(self) -> None:
        return None

    def get_registered_models(self) -> list[dict[str, Any]]:
        return [{"model_name": "embedder"}]

    def get_claim_text(self, claim_id: str) -> dict[str, Any] | None:
        claim = self._claims.get(claim_id)
        return dict(claim) if claim is not None else None

    def get_claim_texts(self, claim_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
        return {cid: dict(self._claims[cid]) for cid in claim_ids if cid in self._claims}

    def all_claim_ids(self) -> list[str]:
        return list(self._claims)

    def find_similar(
        self, claim_id: str, model_name: str, *, top_k: int
    ) -> list[dict[str, Any]]:
        if claim_id == "claim-a":
            return [{"id": "claim-b", "distance": 0.3}]
        if claim_id == "claim-b":
            return [{"id": "claim-a", "distance": 0.4}]
        return []


def test_relate_perspective_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    from propstore.heuristic import relate

    async def classify_stance_async(
        claim_a: dict[str, Any],
        claim_b: dict[str, Any],
        *_args: object,
        **_kwargs: object,
    ) -> list[dict[str, Any]]:
        return [
            {
                "target": claim_b["id"],
                "type": "supports",
                "strength": "strong",
                "note": "forward",
                "conditions_differ": None,
                "resolution": {},
            },
            {
                "target": claim_a["id"],
                "type": "undercuts",
                "strength": "weak",
                "note": "reverse",
                "conditions_differ": None,
                "resolution": {},
            },
        ]

    monkeypatch.setattr(relate, "classify_stance_async", classify_stance_async)

    result = asyncio.run(
        relate.relate_all_async(
            _Store(),
            model_name="classifier",
            embedding_model=None,
            top_k=1,
            concurrency=1,
            on_progress=None,
        )
    )

    forward = result["stances_by_claim"]["claim-a"][0]
    reverse = result["stances_by_claim"]["claim-b"][0]
    assert forward["target"] == "claim-b"
    assert reverse["target"] == "claim-a"
    assert forward["perspective_source_claim_id"] == "claim-a"
    assert reverse["perspective_source_claim_id"] == "claim-b"
    assert (
        forward["perspective_source_claim_id"]
        != reverse["perspective_source_claim_id"]
    )
