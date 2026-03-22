"""NLI stance classification via litellm — classify epistemic relationships between claims."""
from __future__ import annotations

import asyncio
import json
import sqlite3
from collections.abc import Callable
from datetime import date
from pathlib import Path

import yaml


def _require_litellm():
    try:
        import litellm
        return litellm
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


VALID_STANCE_TYPES = {"rebuts", "undercuts", "undermines", "supports", "explains", "supersedes"}


def _get_claim_text(conn: sqlite3.Connection, claim_id: str) -> dict | None:
    """Get claim statement/expression and source paper."""
    row = conn.execute(
        "SELECT id, auto_summary, statement, expression, source_paper FROM claim WHERE id = ?",
        (claim_id,)
    ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["text"] = d.get("auto_summary") or d.get("statement") or d.get("expression") or claim_id
    return d


async def _classify_stance_async(
    claim_a: dict,
    claim_b: dict,
    model_name: str,
    semaphore: asyncio.Semaphore,
) -> dict | None:
    """Classify the epistemic relationship between two claims via async LLM call."""
    litellm = _require_litellm()

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
        except Exception:
            return None

    text = response.choices[0].message.content.strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        return None

    stance_type = result.get("type", "none")
    if stance_type == "none" or stance_type not in VALID_STANCE_TYPES:
        return None

    return {
        "target": claim_b["id"],
        "type": stance_type,
        "strength": result.get("strength", "moderate"),
        "note": result.get("note", ""),
        "conditions_differ": result.get("conditions_differ"),
    }


def classify_stance(
    claim_a: dict,
    claim_b: dict,
    model_name: str,
) -> dict | None:
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
) -> list[dict]:
    """Find similar claims and classify relationships concurrently."""
    from propstore.embed import find_similar, get_registered_models, _load_vec_extension

    _load_vec_extension(conn)

    if embedding_model is None:
        models = get_registered_models(conn)
        if not models:
            raise ValueError("No embeddings found. Run 'pks claim embed' first.")
        embedding_model = models[0]["model_name"]

    claim_a = _get_claim_text(conn, claim_id)
    if not claim_a:
        raise ValueError(f"Claim {claim_id} not found")

    candidates = find_similar(conn, claim_id, embedding_model, top_k=top_k)

    # Fetch all candidate texts
    candidate_claims = []
    for c in candidates:
        claim_b = _get_claim_text(conn, c["id"])
        if claim_b:
            candidate_claims.append(claim_b)

    # Classify all candidates concurrently
    tasks = [
        _classify_stance_async(claim_a, claim_b, model_name, semaphore)
        for claim_b in candidate_claims
    ]
    results = await asyncio.gather(*tasks)

    return [r for r in results if r is not None]


def relate_claim(
    conn: sqlite3.Connection,
    claim_id: str,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    """Find similar claims and classify relationships (sync entry point)."""
    sem = asyncio.Semaphore(10)
    return asyncio.run(
        _relate_claim_async(conn, claim_id, model_name, embedding_model, top_k, sem)
    )


async def _relate_all_async(
    conn: sqlite3.Connection,
    model_name: str,
    embedding_model: str | None,
    top_k: int,
    concurrency: int,
    on_progress: Callable[[int, int], None] | None,
) -> dict:
    """Classify relationships for all claims with concurrent LLM calls."""
    from propstore.embed import find_similar, get_registered_models, _load_vec_extension

    _load_vec_extension(conn)

    if embedding_model is None:
        models = get_registered_models(conn)
        if not models:
            raise ValueError("No embeddings found. Run 'pks claim embed' first.")
        embedding_model = models[0]["model_name"]

    all_claim_rows = conn.execute("SELECT id FROM claim").fetchall()
    total = len(all_claim_rows)

    # Phase 1: Gather all (claim_a, candidate_b) pairs from embeddings (fast, no LLM)
    pairs: list[tuple[dict, dict]] = []
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
                pairs.append((claim_a, claim_b))

    # Phase 2: Classify all pairs concurrently
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [
        _classify_stance_async(a, b, model_name, semaphore)
        for a, b in pairs
    ]

    all_stances: dict[str, list[dict]] = {}
    total_stances = 0
    total_none = 0
    done = 0

    # Process in chunks to report progress
    chunk_size = concurrency * 2
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i + chunk_size]
        chunk_pairs = pairs[i:i + chunk_size]
        results = await asyncio.gather(*chunk)

        for (claim_a, _claim_b), result in zip(chunk_pairs, results):
            cid = claim_a["id"]
            if result is not None:
                all_stances.setdefault(cid, []).append(result)
                total_stances += 1
            else:
                total_none += 1

        done += len(chunk)
        if on_progress:
            # Approximate claim progress from pair progress
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
    return asyncio.run(
        _relate_all_async(conn, model_name, embedding_model, top_k, concurrency, on_progress)
    )


def write_stance_file(
    stances_dir: Path,
    source_claim_id: str,
    stances: list[dict],
    model_name: str,
) -> Path:
    """Write stances to knowledge/stances/<claim_id>.yaml"""
    stances_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "source_claim": source_claim_id,
        "classification_model": model_name,
        "classification_date": str(date.today()),
        "stances": stances,
    }

    path = stances_dir / f"{source_claim_id}.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return path
