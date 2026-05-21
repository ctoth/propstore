from __future__ import annotations

import asyncio
from collections.abc import Sequence

import pytest


def test_relate_perspective_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    from propstore.heuristic import relate

    claim_texts = {
        "claim-a": {
            "id": "claim-a",
            "source_paper": "paper-a",
            "statement": "A says alpha.",
            "text": "A says alpha.",
        },
        "claim-b": {
            "id": "claim-b",
            "source_paper": "paper-b",
            "statement": "B says beta.",
            "text": "B says beta.",
        },
    }

    def find_similar(claim_id: str, _model_name: str, *, top_k: int) -> list[dict]:
        if claim_id == "claim-a":
            return [{"id": "claim-b", "distance": 0.3}]
        if claim_id == "claim-b":
            return [{"id": "claim-a", "distance": 0.4}]
        return []

    async def classify_stance_async(
        claim_a: dict,
        claim_b: dict,
        *_args: object,
        **_kwargs: object,
    ) -> list[dict]:
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

    class Store:
        def load_embedding_extension(self) -> None:
            pass

        def get_registered_models(self) -> list[dict]:
            return [{"model_name": "embedder"}]

        def get_claim_text(self, claim_id: str) -> dict | None:
            return claim_texts.get(claim_id)

        def get_claim_texts(self, claim_ids: Sequence[str]) -> dict[str, dict]:
            return {
                claim_id: claim_texts[claim_id]
                for claim_id in claim_ids
                if claim_id in claim_texts
            }

        def all_claim_ids(self) -> list[str]:
            return list(claim_texts)

        def find_similar(
            self,
            claim_id: str,
            model_name: str,
            *,
            top_k: int,
        ) -> list[dict]:
            return find_similar(claim_id, model_name, top_k=top_k)

    monkeypatch.setattr(relate, "classify_stance_async", classify_stance_async)

    result = asyncio.run(
        relate.relate_all_async(
            Store(),
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
    assert forward["perspective_source_claim_id"] != reverse["perspective_source_claim_id"]
