"""Pair discovery and batch orchestration for epistemic relationship classification.

Classification logic lives in propstore.heuristic.classify; this module handles pair selection,
bulk fetching, deduplication, and async orchestration.

Embedding-neighbor searches are directed: A's nearest-neighbor distance to B is
not interchangeable with B's distance to A. ``dedup_pairs`` keeps one unordered
pair for LLM cost control, but preserves the two directed distances separately
instead of collapsing them to ``min(forward, reverse)``.
"""
from __future__ import annotations

import asyncio
import sqlite3
from collections.abc import Callable

from propstore.heuristic.classify import classify_stance_async


def _run_async(coro):
    """Run coroutine, handling both sync and already-running-loop contexts."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # Already in an event loop (Jupyter, async CLI, etc.)
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def _get_claim_text(conn: sqlite3.Connection, claim_id: str) -> dict | None:
    """Get claim statement/expression and source paper."""
    row = conn.execute(
        """
        SELECT core.id, txt.auto_summary, txt.statement, txt.expression, core.source_paper
        FROM claim_core AS core
        LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
        WHERE core.id = ?
        """,
        (claim_id,)
    ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["text"] = d.get("auto_summary") or d.get("statement") or d.get("expression") or claim_id
    return d


def _bulk_get_claim_texts(conn: sqlite3.Connection, claim_ids: list[str]) -> dict[str, dict]:
    """Fetch claim texts for multiple IDs in a single query."""
    if not claim_ids:
        return {}
    placeholders = ",".join("?" * len(claim_ids))
    rows = conn.execute(
        f"""
        SELECT core.id, txt.auto_summary, txt.statement, txt.expression, core.source_paper
        FROM claim_core AS core
        LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
        WHERE core.id IN ({placeholders})
        """,
        claim_ids,
    ).fetchall()
    result: dict[str, dict] = {}
    for row in rows:
        d = dict(row)
        d["text"] = d.get("auto_summary") or d.get("statement") or d.get("expression") or d["id"]
        result[d["id"]] = d
    return result


def dedup_pairs(
    pairs: list[tuple[str, str, float]],
) -> list[tuple[str, str, float, float | None]]:
    """Deduplicate directed pair distances while preserving mirror disagreement.

    The returned tuple is ``(a_id, b_id, forward_distance, reverse_distance)``.
    ``forward_distance`` is the best observed distance for ``a_id -> b_id`` in
    the representative orientation; ``reverse_distance`` is the best observed
    distance for ``b_id -> a_id`` when that mirror direction was present.
    """

    best: dict[frozenset[str], tuple[int, str, str, float, float | None]] = {}
    for i, (a, b, dist) in enumerate(pairs):
        key = frozenset({a, b})
        if key not in best:
            best[key] = (i, a, b, dist, None)
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
            best.values(),
            key=lambda item: item[0],
        )
    ]


def _shared_concept_ids_from_pair(claim_a: dict, claim_b: dict) -> list[str]:
    """Extract shared concept IDs from claim dicts (concept_id field from find_similar)."""
    a_cid = claim_a.get("concept_id")
    b_cid = claim_b.get("concept_id")
    if a_cid and b_cid and a_cid == b_cid:
        return [a_cid]
    return []


async def relate_claim_async(
    conn: sqlite3.Connection,
    claim_id: str,
    model_name: str,
    embedding_model: str | None,
    top_k: int,
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    """Find similar claims and classify relationships concurrently.

    Single-pass bidirectional classification — each LLM call returns both A->B and B->A.
    """
    from propstore.heuristic.embed import find_similar, get_registered_models, _load_vec_extension

    _load_vec_extension(conn)

    if embedding_model is None:
        models = get_registered_models(conn)
        if not models:
            raise ValueError("No embeddings found. Run 'pks claim embed' first.")
        embedding_model = str(models[0]["model_name"])

    claim_a = _get_claim_text(conn, claim_id)
    if not claim_a:
        raise ValueError(f"Claim {claim_id} not found")

    candidates = find_similar(conn, claim_id, embedding_model, top_k=top_k)

    candidate_claims = []
    candidate_distances: dict[str, float] = {}
    for c in candidates:
        claim_b = _get_claim_text(conn, c["id"])
        if claim_b:
            # Carry concept_id from find_similar result for shared-concept check
            claim_b["concept_id"] = c.get("concept_id")
            candidate_claims.append(claim_b)
            candidate_distances[c["id"]] = c.get("distance", 1.0)

    tasks = [
        classify_stance_async(
            claim_a, claim_b, model_name, semaphore,
            embedding_model=embedding_model,
            embedding_distance=candidate_distances.get(claim_b["id"]),
            shared_concept_ids=_shared_concept_ids_from_pair(claim_a, claim_b),
        )
        for claim_b in candidate_claims
    ]
    results_lists = await asyncio.gather(*tasks)

    # Flatten: each call returns [forward, reverse]; collect all stances
    all_stances: list[dict] = []
    for stance_pair in results_lists:
        all_stances.extend(stance_pair)

    return all_stances


def relate_claim(
    conn: sqlite3.Connection,
    claim_id: str,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    """Find similar claims and classify relationships (sync entry point)."""
    sem = asyncio.Semaphore(10)
    return _run_async(
        relate_claim_async(conn, claim_id, model_name, embedding_model, top_k, sem)
    )


async def relate_all_async(
    conn: sqlite3.Connection,
    model_name: str,
    embedding_model: str | None,
    top_k: int,
    concurrency: int,
    on_progress: Callable[[int, int], None] | None,
) -> dict:
    """Classify relationships for all claims with concurrent bidirectional LLM calls."""
    from propstore.heuristic.embed import find_similar, get_registered_models, _load_vec_extension

    _load_vec_extension(conn)

    if embedding_model is None:
        models = get_registered_models(conn)
        if not models:
            raise ValueError("No embeddings found. Run 'pks claim embed' first.")
        embedding_model = str(models[0]["model_name"])

    all_claim_rows = conn.execute("SELECT id FROM claim_core").fetchall()
    all_claim_ids = [row["id"] for row in all_claim_rows]
    total = len(all_claim_ids)

    # Bulk-fetch all claim texts upfront
    text_cache = _bulk_get_claim_texts(conn, all_claim_ids)

    # Phase 1: Gather directed pairs from embeddings (fast, no LLM)
    directed_pairs: list[tuple[dict, dict, float]] = []
    candidate_ids_needed: set[str] = set()
    raw_candidates: list[tuple[str, list[dict]]] = []
    # Track concept_ids from find_similar for shared-concept checks
    concept_ids: dict[str, str | None] = {}

    for claim_id in all_claim_ids:
        if claim_id not in text_cache:
            continue
        try:
            candidates = find_similar(conn, claim_id, embedding_model, top_k=top_k)
        except ValueError:
            continue
        raw_candidates.append((claim_id, candidates))
        for c in candidates:
            concept_ids[c["id"]] = c.get("concept_id")
            if c["id"] not in text_cache:
                candidate_ids_needed.add(c["id"])

    if candidate_ids_needed:
        text_cache.update(_bulk_get_claim_texts(conn, list(candidate_ids_needed)))

    for claim_id, candidates in raw_candidates:
        claim_a = text_cache[claim_id]
        for c in candidates:
            claim_b = text_cache.get(c["id"])
            if claim_b:
                directed_pairs.append((claim_a, claim_b, c.get("distance", 1.0)))

    # Deduplicate mirror pairs
    raw_id_pairs = [(a["id"], b["id"], dist) for a, b, dist in directed_pairs]
    deduped = dedup_pairs(raw_id_pairs)
    pairs: list[tuple[dict, dict, float, float | None]] = [
        (text_cache[a_id], text_cache[b_id], forward_dist, reverse_dist)
        for a_id, b_id, forward_dist, reverse_dist in deduped
        if a_id in text_cache and b_id in text_cache
    ]

    # Collect all distances for corpus calibration (Josang 2001, Theorem 7)
    reference_distances = [
        distance
        for _, _, forward_dist, reverse_dist in pairs
        for distance in (forward_dist, reverse_dist)
        if distance is not None
    ]

    # Phase 2: Classify all pairs (single pass, bidirectional)
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [
        classify_stance_async(
            a, b, model_name, semaphore,
            embedding_model=embedding_model,
            embedding_distance=forward_dist,
            shared_concept_ids=_shared_concept_ids_from_pair(
                {**a, "concept_id": concept_ids.get(a["id"])},
                {**b, "concept_id": concept_ids.get(b["id"])},
            ),
            reference_distances=reference_distances,
        )
        for a, b, forward_dist, _reverse_dist in pairs
    ]

    all_stances: dict[str, list[dict]] = {}
    total_stances = 0
    total_none = 0
    done = 0

    chunk_size = concurrency * 2
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i + chunk_size]
        chunk_pairs = pairs[i:i + chunk_size]
        results = await asyncio.gather(*chunk)

        for (claim_a, claim_b, _forward_dist, _reverse_dist), stance_pair in zip(
            chunk_pairs,
            results,
        ):
            # Each result is [forward_stance, reverse_stance]
            for stance in stance_pair:
                # File under the source claim (the one whose perspective this is from)
                # Forward: A's perspective -> file under A
                # Reverse: B's perspective -> file under B
                source_id = claim_a["id"] if stance["target"] == claim_b["id"] else claim_b["id"]
                if stance["type"] != "none":
                    all_stances.setdefault(source_id, []).append(stance)
                    total_stances += 1
                else:
                    all_stances.setdefault(source_id, []).append(stance)
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
    conn: sqlite3.Connection,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
    concurrency: int = 20,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict:
    """Classify relationships for all claims (sync entry point)."""
    return _run_async(
        relate_all_async(conn, model_name, embedding_model, top_k, concurrency, on_progress)
    )
