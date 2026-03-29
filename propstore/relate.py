"""NLI stance classification via litellm — classify epistemic relationships between claims."""
from __future__ import annotations

import asyncio
import importlib
import json
import logging
import sqlite3
from collections.abc import Callable
from datetime import date
from pathlib import Path

import yaml

from propstore.calibrate import categorical_to_opinion
from propstore.data_utils import write_yaml_file
from propstore.stances import VALID_STANCE_TYPES


def _require_litellm():
    try:
        return importlib.import_module("litellm")
    except ImportError:
        raise ImportError(
            "litellm is required for relate commands. "
            "Install with: uv pip install 'propstore[embeddings]'"
        )


_CLASSIFICATION_PROMPT = """Given two propositional claims from scientific papers, classify their epistemic relationship.

Claim A (from {source_a}):
  "{statement_a}"

Claim B (from {source_b}):
  "{statement_b}"

Classify the relationship from Claim A's perspective toward Claim B.
Choose exactly ONE of these types, or "none" if they are unrelated:

- rebuts: A directly contradicts B's conclusion
- undercuts: A attacks B's inference method or reasoning
- undermines: A weakens B's premise or evidence quality
- supports: A provides corroborating evidence for B
- explains: A provides a mechanistic explanation for why B is true
- supersedes: A replaces B entirely (newer data, better method, corrects error)
- none: No meaningful epistemic relationship

Respond with ONLY a JSON object (no markdown, no explanation):
{{"type": "<type or none>", "strength": "<strong|moderate|weak>", "note": "<1 sentence explaining why>", "conditions_differ": "<how conditions differ, or null>"}}"""


_SECOND_PASS_PROMPT = """These two claims from scientific papers are HIGHLY SIMILAR by embedding distance ({distance:.4f}) but a first-pass analysis found no epistemic relationship. Re-examine more carefully.

{shared_concepts_text}

Claim A (from {source_a}):
  "{statement_a}"

Claim B (from {source_b}):
  "{statement_b}"

Look specifically for subtle relationships:
- undermines: Does A weaken B's premise or evidence quality?
- undercuts: Does A attack B's inference method or reasoning?
- rebuts: Does A contradict B's conclusion?
- supports/explains: Does A provide evidence or mechanism for B?
- supersedes: Does A replace B?

Classify from Claim A's perspective toward Claim B.
Choose exactly ONE type, or "none" if truly unrelated:

Respond with ONLY a JSON object:
{{"type": "<type or none>", "strength": "<strong|moderate|weak>", "note": "<1 sentence>", "conditions_differ": "<or null>"}}"""


# _CONFIDENCE_MAP removed: fabricated lookup table replaced by categorical_to_opinion()
# Per Guo et al. (2017, p.0): raw neural scores are miscalibrated; fabricated scores are worse


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


def _find_shared_concepts(conn: sqlite3.Connection, claim_a_id: str, claim_b_id: str) -> list[str]:
    """Find concept names referenced by both claims."""
    a_concept = conn.execute(
        "SELECT concept_id FROM claim_core WHERE id = ?",
        (claim_a_id,),
    ).fetchone()
    b_concept = conn.execute(
        "SELECT concept_id FROM claim_core WHERE id = ?",
        (claim_b_id,),
    ).fetchone()
    shared = set()
    if a_concept and b_concept and a_concept[0] and b_concept[0]:
        if a_concept[0] == b_concept[0]:
            shared.add(a_concept[0])
    # Also check for concept overlap in auto_summary text (rough heuristic)
    return list(shared)


async def _classify_stance_async(
    claim_a: dict,
    claim_b: dict,
    model_name: str,
    semaphore: asyncio.Semaphore,
    *,
    embedding_model: str | None = None,
    embedding_distance: float | None = None,
    pass_number: int = 1,
    shared_concepts: list[str] | None = None,
    reference_distances: list[float] | None = None,
    calibration_counts: dict[tuple[int, str], tuple[int, int]] | None = None,
) -> dict:
    """Classify the epistemic relationship between two claims via async LLM call.

    Always returns a dict — "none" verdicts included with type="none".
    """
    litellm = _require_litellm()

    if pass_number == 2 and embedding_distance is not None:
        shared_concepts_text = ""
        if shared_concepts:
            shared_concepts_text = f"Shared concepts: {', '.join(shared_concepts)}"
        prompt = _SECOND_PASS_PROMPT.format(
            distance=embedding_distance,
            shared_concepts_text=shared_concepts_text,
            source_a=claim_a.get("source_paper", "unknown"),
            statement_a=claim_a["text"],
            source_b=claim_b.get("source_paper", "unknown"),
            statement_b=claim_b["text"],
        )
    else:
        prompt = _CLASSIFICATION_PROMPT.format(
            source_a=claim_a.get("source_paper", "unknown"),
            statement_a=claim_a["text"],
            source_b=claim_b.get("source_paper", "unknown"),
            statement_b=claim_b["text"],
        )

    async with semaphore:
        try:
            response = await litellm.acompletion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
        except (ConnectionError, TimeoutError, OSError, ValueError) as exc:
            logging.warning("Stance classification failed for %s vs %s: %s", claim_a["id"], claim_b["id"], exc)
            return {
                "target": claim_b["id"],
                "type": "error",
                "strength": "weak",
                "note": "classification failed",
                "conditions_differ": None,
                "resolution": {
                    "method": f"nli_{'first' if pass_number == 1 else 'second'}_pass",
                    "model": model_name,
                    "embedding_model": embedding_model,
                    "embedding_distance": embedding_distance,
                    "pass_number": pass_number,
                    "confidence": 0.0,
                },
            }

    text = response.choices[0].message.content.strip()  # type: ignore[union-attr] # litellm ModelResponse content may be typed as optional but is always present for non-streaming
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        return {
            "target": claim_b["id"],
            "type": "error",
            "strength": "weak",
            "note": "JSON parse failed",
            "conditions_differ": None,
            "resolution": {
                "method": f"nli_{'first' if pass_number == 1 else 'second'}_pass",
                "model": model_name,
                "embedding_model": embedding_model,
                "embedding_distance": embedding_distance,
                "pass_number": pass_number,
                "confidence": 0.0,
            },
        }

    stance_type = result.get("type", "none")
    if stance_type not in VALID_STANCE_TYPES:
        stance_type = "none"

    strength = result.get("strength", "moderate")
    if stance_type != "none":
        # 1. Categorical opinion (Jøsang 2001, p.8)
        # Without calibration data, returns vacuous opinion (honest ignorance)
        opinion = categorical_to_opinion(strength, pass_number, calibration_counts=calibration_counts)

        # 2. Corpus-distance opinion: fuse via consensus (Jøsang 2001, Theorem 7, p.25)
        if reference_distances is not None and embedding_distance is not None and len(reference_distances) > 0:
            from propstore.calibrate import CorpusCalibrator
            from propstore.opinion import fuse
            corpus_cal = CorpusCalibrator(reference_distances)
            corpus_opinion = corpus_cal.to_opinion(embedding_distance)
            # fuse(method="auto") handles dogmatic inputs via CCF fallback
            # (Jøsang 2001, Theorem 7 for WBF; CCF for dogmatic edge cases)
            opinion = fuse(opinion, corpus_opinion)

        # Backward-compatible confidence = probability expectation (Jøsang 2001, p.5, Def 6)
        confidence = opinion.expectation()  # E(ω) = b + a·u
    else:
        confidence = 0.0
        opinion = None

    resolution = {
        "method": f"nli_{'first' if pass_number == 1 else 'second'}_pass",
        "model": model_name,
        "embedding_model": embedding_model,
        "embedding_distance": embedding_distance,
        "pass_number": pass_number,
        "confidence": confidence,
        "opinion_belief": opinion.b if opinion else 0.0,
        "opinion_disbelief": opinion.d if opinion else 0.0,
        "opinion_uncertainty": opinion.u if opinion else 0.0,
        "opinion_base_rate": opinion.a if opinion else 0.5,
    }

    return {
        "target": claim_b["id"],
        "type": stance_type,
        "strength": strength,
        "note": result.get("note", ""),
        "conditions_differ": result.get("conditions_differ"),
        "resolution": resolution,
    }


def classify_stance(
    claim_a: dict,
    claim_b: dict,
    model_name: str,
) -> dict:
    """Classify the epistemic relationship between two claims via LLM (sync wrapper)."""
    sem = asyncio.Semaphore(1)
    return asyncio.run(_classify_stance_async(claim_a, claim_b, model_name, sem))


async def _relate_claim_async(
    conn: sqlite3.Connection,
    claim_id: str,
    model_name: str,
    embedding_model: str | None,
    top_k: int,
    semaphore: asyncio.Semaphore,
    second_pass_threshold: float = 0.75,
) -> list[dict]:
    """Find similar claims and classify relationships concurrently, with two-pass NLI."""
    from propstore.embed import find_similar, get_registered_models, _load_vec_extension

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

    # Fetch all candidate texts with distances
    candidate_claims = []
    candidate_distances: dict[str, float] = {}
    for c in candidates:
        claim_b = _get_claim_text(conn, c["id"])
        if claim_b:
            candidate_claims.append(claim_b)
            candidate_distances[c["id"]] = c.get("distance", 1.0)

    # Phase 1: First-pass classify all candidates
    tasks = [
        _classify_stance_async(
            claim_a, claim_b, model_name, semaphore,
            embedding_model=embedding_model,
            embedding_distance=candidate_distances.get(claim_b["id"]),
            pass_number=1,
        )
        for claim_b in candidate_claims
    ]
    first_pass_results = await asyncio.gather(*tasks)

    # Phase 2: Second pass for "none" verdicts with high similarity
    second_pass_indices = []
    for i, result in enumerate(first_pass_results):
        if result["type"] == "none":
            target_id = result["target"]
            dist = candidate_distances.get(target_id, 1.0)
            if dist < second_pass_threshold:
                second_pass_indices.append(i)

    if second_pass_indices:
        second_tasks = []
        for i in second_pass_indices:
            target_id = first_pass_results[i]["target"]
            claim_b = next((cb for cb in candidate_claims if cb["id"] == target_id), None)
            if claim_b is None:
                continue
            shared = _find_shared_concepts(conn, claim_id, target_id)
            second_tasks.append((i, _classify_stance_async(
                claim_a, claim_b, model_name, semaphore,
                embedding_model=embedding_model,
                embedding_distance=candidate_distances.get(target_id),
                pass_number=2,
                shared_concepts=shared,
            )))

        results_list = list(first_pass_results)
        for idx, task in second_tasks:
            second_result = await task
            # Replace first-pass "none" with second-pass result
            results_list[idx] = second_result
        first_pass_results = results_list

    return list(first_pass_results)


def relate_claim(
    conn: sqlite3.Connection,
    claim_id: str,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
    second_pass_threshold: float = 0.75,
) -> list[dict]:
    """Find similar claims and classify relationships (sync entry point)."""
    sem = asyncio.Semaphore(10)
    return asyncio.run(
        _relate_claim_async(conn, claim_id, model_name, embedding_model, top_k, sem,
                            second_pass_threshold=second_pass_threshold)
    )


async def _relate_all_async(
    conn: sqlite3.Connection,
    model_name: str,
    embedding_model: str | None,
    top_k: int,
    concurrency: int,
    on_progress: Callable[[int, int], None] | None,
    second_pass_threshold: float = 0.75,
) -> dict:
    """Classify relationships for all claims with concurrent LLM calls and two-pass NLI."""
    from propstore.embed import find_similar, get_registered_models, _load_vec_extension

    _load_vec_extension(conn)

    if embedding_model is None:
        models = get_registered_models(conn)
        if not models:
            raise ValueError("No embeddings found. Run 'pks claim embed' first.")
        embedding_model = str(models[0]["model_name"])

    all_claim_rows = conn.execute("SELECT id FROM claim_core").fetchall()
    total = len(all_claim_rows)

    # Phase 1: Gather all (claim_a, candidate_b, distance) pairs from embeddings (fast, no LLM)
    pairs: list[tuple[dict, dict, float]] = []
    for row in all_claim_rows:
        claim_id = row["id"]
        claim_a = _get_claim_text(conn, claim_id)
        if not claim_a:
            continue
        try:
            candidates = find_similar(conn, claim_id, embedding_model, top_k=top_k)
        except ValueError:
            continue
        for c in candidates:
            claim_b = _get_claim_text(conn, c["id"])
            if claim_b:
                pairs.append((claim_a, claim_b, c.get("distance", 1.0)))

    # Phase 2: First-pass classify all pairs concurrently
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [
        _classify_stance_async(
            a, b, model_name, semaphore,
            embedding_model=embedding_model,
            embedding_distance=dist,
            pass_number=1,
        )
        for a, b, dist in pairs
    ]

    all_stances: dict[str, list[dict]] = {}
    total_stances = 0
    total_none = 0
    done = 0

    # Process in chunks to report progress
    chunk_size = concurrency * 2
    first_pass_results: list[tuple[dict, dict, float, dict]] = []

    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i + chunk_size]
        chunk_pairs = pairs[i:i + chunk_size]
        results = await asyncio.gather(*chunk)

        for (claim_a, claim_b, dist), result in zip(chunk_pairs, results):
            first_pass_results.append((claim_a, claim_b, dist, result))

        done += len(chunk)
        if on_progress:
            claims_done = min(total, (done * total) // max(len(pairs), 1))
            on_progress(claims_done, total)

    # Phase 3: Second pass for "none" verdicts below threshold
    second_pass_items = []
    for idx, (claim_a, claim_b, dist, result) in enumerate(first_pass_results):
        if result["type"] == "none" and dist < second_pass_threshold:
            shared = _find_shared_concepts(conn, claim_a["id"], claim_b["id"])
            second_pass_items.append((idx, claim_a, claim_b, dist, shared))

    if second_pass_items:
        second_tasks = [
            _classify_stance_async(
                claim_a, claim_b, model_name, semaphore,
                embedding_model=embedding_model,
                embedding_distance=dist,
                pass_number=2,
                shared_concepts=shared,
            )
            for _, claim_a, claim_b, dist, shared in second_pass_items
        ]
        second_results = await asyncio.gather(*second_tasks)

        for (idx, claim_a, claim_b, dist, _shared), second_result in zip(second_pass_items, second_results):
            # Replace first-pass result
            first_pass_results[idx] = (claim_a, claim_b, dist, second_result)

    # Collect final results
    for claim_a, _claim_b, _dist, result in first_pass_results:
        cid = claim_a["id"]
        if result["type"] != "none":
            all_stances.setdefault(cid, []).append(result)
            total_stances += 1
        else:
            all_stances.setdefault(cid, []).append(result)
            total_none += 1

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
    second_pass_threshold: float = 0.75,
) -> dict:
    """Classify relationships for all claims (sync entry point)."""
    return asyncio.run(
        _relate_all_async(conn, model_name, embedding_model, top_k, concurrency, on_progress,
                          second_pass_threshold=second_pass_threshold)
    )


def write_stance_file(
    stances_dir: Path,
    source_claim_id: str,
    stances: list[dict],
    model_name: str,
) -> Path:
    """Write stances to knowledge/proposals/stances/<claim_id>.yaml

    Heuristic output is written to proposals/, never directly to
    source-of-truth storage (F17).
    """
    # Route output through proposals/ subdirectory of the parent
    proposals_dir = stances_dir.parent / "proposals" / stances_dir.name
    proposals_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "source_claim": source_claim_id,
        "classification_model": model_name,
        "classification_date": str(date.today()),
        "stances": stances,
    }

    # Replace colons with double-underscores for Windows path compatibility
    safe_name = source_claim_id.replace(":", "__")
    path = proposals_dir / f"{safe_name}.yaml"
    write_yaml_file(path, data)

    return path
