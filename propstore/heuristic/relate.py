"""Pair discovery and batch orchestration for stance classification.

Classification logic lives in :mod:`propstore.heuristic.classify`; this module
handles pair selection, bulk fetching, deduplication, and async orchestration.

Embedding-neighbour searches are directed: A's nearest-neighbour distance to B is
not interchangeable with B's distance to A. :func:`dedup_pairs` keeps one
unordered pair for LLM cost control but preserves both directed distances rather
than collapsing them to ``min(forward, reverse)``. Every classified stance keeps
its ``perspective_source_claim_id`` so the two directions never collapse into one
(CLAUDE.md non-commitment).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine, Sequence
from typing import Any, Protocol, TypeVar

from msgspec.structs import replace

from propstore.core.store_results import ClaimSimilarityHit
from propstore.heuristic.classify import classify_stance_async
from propstore.heuristic.relatable import RelatableClaim

_T = TypeVar("_T")


class ClaimRelationStore(Protocol):
    """What the relation heuristics need from a store — typed, end to end.

    Every method used to return ``dict[str, Any]``, and every value they carried
    already had a canonical type: a claim is a ``Claim`` charter document and a
    similarity candidate is a :class:`ClaimSimilarityHit`.
    ``registered_embedding_models`` returns model names because that is all the
    caller reads; the raw registry rows stay behind ``families.embeddings``,
    where the SQL boundary actually is.
    """

    def load_embedding_extension(self) -> None: ...
    def registered_embedding_models(self) -> list[str]: ...
    def get_claim(self, claim_id: str) -> RelatableClaim | None: ...
    def get_claims(self, claim_ids: Sequence[str]) -> dict[str, RelatableClaim]: ...
    def all_claim_ids(self) -> list[str]: ...
    def find_similar(
        self, claim_id: str, model_name: str, *, top_k: int
    ) -> list[ClaimSimilarityHit]: ...


def run_async(coro: Coroutine[Any, Any, _T]) -> _T:
    """Run a coroutine, handling both sync and already-running-loop contexts."""

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def dedup_pairs(
    pairs: list[tuple[str, str, float]],
) -> list[tuple[str, str, float, float | None]]:
    """Deduplicate directed pair distances while preserving mirror disagreement.

    The returned tuple is ``(a_id, b_id, forward_distance, reverse_distance)``:
    ``forward_distance`` is the best observed distance for ``a_id -> b_id`` in the
    representative orientation; ``reverse_distance`` is the best observed distance
    for ``b_id -> a_id`` when that mirror direction was present.
    """

    best: dict[frozenset[str], tuple[int, str, str, float, float | None]] = {}
    for index, (a, b, dist) in enumerate(pairs):
        key = frozenset({a, b})
        if key not in best:
            best[key] = (index, a, b, dist, None)
            continue

        first_index, left, right, forward, reverse = best[key]
        if (a, b) == (left, right):
            forward = min(forward, dist)
        elif (a, b) == (right, left):
            reverse = dist if reverse is None else min(reverse, dist)
        else:
            raise ValueError("dedup_pairs requires non-self unordered pairs")
        best[key] = (first_index, left, right, forward, reverse)

    return [
        (left, right, forward, reverse)
        for _index, left, right, forward, reverse in sorted(
            best.values(), key=lambda item: item[0]
        )
    ]


def _shared_concept_ids_from_pair(
    claim_a: RelatableClaim, claim_b: RelatableClaim
) -> list[str]:
    if claim_a.concept_id and claim_a.concept_id == claim_b.concept_id:
        return [str(claim_a.concept_id)]
    return []


async def relate_claim_async(
    store: ClaimRelationStore,
    claim_id: str,
    model_name: str,
    embedding_model: str | None,
    top_k: int,
    semaphore: asyncio.Semaphore,
) -> list[dict[str, Any]]:
    """Find similar claims and classify relationships concurrently.

    Single-pass bidirectional classification — each LLM pair returns A->B and B->A.
    """

    store.load_embedding_extension()

    if embedding_model is None:
        models = store.registered_embedding_models()
        if not models:
            raise ValueError("No embeddings found. Run 'pks claim embed' first.")
        embedding_model = models[0]

    claim_a = store.get_claim(claim_id)
    if claim_a is None:
        raise ValueError(f"Claim {claim_id} not found")

    candidates = store.find_similar(claim_id, embedding_model, top_k=top_k)

    candidate_claims: list[RelatableClaim] = []
    candidate_distances: dict[str, float] = {}
    for candidate in candidates:
        claim_b = store.get_claim(str(candidate.claim_id))
        if claim_b is None:
            continue
        # The candidate's concept comes from the similarity hit, not the claim
        # document: it is what the search actually matched on.
        candidate_claims.append(
            replace(
                claim_b,
                concept_id=None if candidate.concept_id is None else str(candidate.concept_id),
            )
        )
        candidate_distances[str(candidate.claim_id)] = candidate.distance

    tasks = [
        classify_stance_async(
            claim_a,
            claim_b,
            model_name,
            semaphore,
            embedding_model=embedding_model,
            embedding_distance=candidate_distances.get(claim_b.claim_id),
            shared_concept_ids=_shared_concept_ids_from_pair(claim_a, claim_b),
        )
        for claim_b in candidate_claims
    ]
    results_lists = await asyncio.gather(*tasks)

    all_stances: list[dict[str, Any]] = []
    for stance_pair in results_lists:
        all_stances.extend(stance_pair)
    return all_stances


def relate_claim(
    store: ClaimRelationStore,
    claim_id: str,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Find similar claims and classify relationships (sync entry point)."""

    sem = asyncio.Semaphore(10)
    return run_async(
        relate_claim_async(store, claim_id, model_name, embedding_model, top_k, sem)
    )


async def relate_all_async(
    store: ClaimRelationStore,
    model_name: str,
    embedding_model: str | None,
    top_k: int,
    concurrency: int,
    on_progress: Callable[[int, int], None] | None,
) -> dict[str, Any]:
    """Classify relationships for all claims with concurrent bidirectional calls."""

    store.load_embedding_extension()

    if embedding_model is None:
        models = store.registered_embedding_models()
        if not models:
            raise ValueError("No embeddings found. Run 'pks claim embed' first.")
        embedding_model = models[0]

    all_claim_ids = store.all_claim_ids()
    total = len(all_claim_ids)
    text_cache = store.get_claims(all_claim_ids)

    raw_candidates: list[tuple[str, list[ClaimSimilarityHit]]] = []
    candidate_ids_needed: set[str] = set()
    concept_ids: dict[str, str | None] = {}
    for claim_id in all_claim_ids:
        if claim_id not in text_cache:
            continue
        try:
            candidates = store.find_similar(claim_id, embedding_model, top_k=top_k)
        except ValueError:
            continue
        raw_candidates.append((claim_id, candidates))
        for candidate in candidates:
            candidate_id = str(candidate.claim_id)
            concept_ids[candidate_id] = (
                None if candidate.concept_id is None else str(candidate.concept_id)
            )
            if candidate_id not in text_cache:
                candidate_ids_needed.add(candidate_id)

    if candidate_ids_needed:
        text_cache.update(store.get_claims(list(candidate_ids_needed)))

    directed_pairs: list[tuple[RelatableClaim, RelatableClaim, float]] = []
    for claim_id, candidates in raw_candidates:
        claim_a = text_cache[claim_id]
        for candidate in candidates:
            claim_b = text_cache.get(str(candidate.claim_id))
            if claim_b is not None:
                directed_pairs.append((claim_a, claim_b, candidate.distance))

    raw_id_pairs = [(a.claim_id, b.claim_id, dist) for a, b, dist in directed_pairs]
    deduped = dedup_pairs(raw_id_pairs)
    pairs: list[tuple[RelatableClaim, RelatableClaim, float, float | None]] = [
        (text_cache[a_id], text_cache[b_id], forward_dist, reverse_dist)
        for a_id, b_id, forward_dist, reverse_dist in deduped
        if a_id in text_cache and b_id in text_cache
    ]

    reference_distances = [
        distance
        for _, _, forward_dist, reverse_dist in pairs
        for distance in (forward_dist, reverse_dist)
        if distance is not None
    ]

    semaphore = asyncio.Semaphore(concurrency)
    tasks = [
        classify_stance_async(
            a,
            b,
            model_name,
            semaphore,
            embedding_model=embedding_model,
            embedding_distance=forward_dist,
            shared_concept_ids=_shared_concept_ids_from_pair(
                replace(a, concept_id=concept_ids.get(a.claim_id)),
                replace(b, concept_id=concept_ids.get(b.claim_id)),
            ),
            reference_distances=reference_distances,
        )
        for a, b, forward_dist, _reverse_dist in pairs
    ]

    all_stances: dict[str, list[dict[str, Any]]] = {}
    total_stances = 0
    total_none = 0
    done = 0

    chunk_size = concurrency * 2
    for offset in range(0, len(tasks), chunk_size):
        chunk = tasks[offset : offset + chunk_size]
        chunk_pairs = pairs[offset : offset + chunk_size]
        results = await asyncio.gather(*chunk)

        for (claim_a, claim_b, _forward_dist, _reverse_dist), stance_pair in zip(
            chunk_pairs, results, strict=True
        ):
            for index, stance in enumerate(stance_pair):
                source_id = claim_a.claim_id if index == 0 else claim_b.claim_id
                stance = {**stance, "perspective_source_claim_id": source_id}
                all_stances.setdefault(source_id, []).append(stance)
                if stance["type"] != "none":
                    total_stances += 1
                else:
                    total_none += 1

        done += len(chunk)
        if on_progress:
            claims_done = min(total, (done * total) // max(len(pairs), 1))
            on_progress(claims_done, total)

    if on_progress:
        on_progress(total, total)

    return {
        "claims_processed": total,
        "stances_found": total_stances,
        "no_relation": total_none,
        "stances_by_claim": all_stances,
    }


def relate_all(
    store: ClaimRelationStore,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
    concurrency: int = 20,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    """Classify relationships for all claims (sync entry point)."""

    return run_async(
        relate_all_async(
            store, model_name, embedding_model, top_k, concurrency, on_progress
        )
    )
