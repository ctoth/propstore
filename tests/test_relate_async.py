"""Tests for async/sync boundary in relate and classify modules.

Verifies _run_async works from sync context, and that async APIs are public.
"""

from __future__ import annotations

import asyncio


class TestRunAsyncFromSyncContext:
    def test_basic_coroutine(self):
        from propstore.heuristic.relate import _run_async

        async def coro():
            return 42

        assert _run_async(coro()) == 42


class TestPublicAsyncAPIs:
    def test_relate_claim_async_importable(self):
        from propstore.heuristic.relate import relate_claim_async
        assert asyncio.iscoroutinefunction(relate_claim_async)

    def test_relate_all_async_importable(self):
        from propstore.heuristic.relate import relate_all_async
        assert asyncio.iscoroutinefunction(relate_all_async)

    def test_classify_stance_async_importable(self):
        from propstore.heuristic.classify import classify_stance_async
        assert asyncio.iscoroutinefunction(classify_stance_async)
