"""NLI stance classification via litellm — classify epistemic relationships between claims."""
from __future__ import annotations

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


def classify_stance(
    claim_a: dict,
    claim_b: dict,
    model_name: str,
) -> dict | None:
    """Classify the epistemic relationship between two claims via LLM.

    Returns dict with type/strength/note/conditions_differ, or None if no relationship.
    """
    litellm = _require_litellm()

    prompt = _CLASSIFICATION_PROMPT.format(
        source_a=claim_a.get("source_paper", "unknown"),
        statement_a=claim_a["text"],
        source_b=claim_b.get("source_paper", "unknown"),
        statement_b=claim_b["text"],
    )

    response = litellm.completion(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

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


def relate_claim(
    conn: sqlite3.Connection,
    claim_id: str,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    """Find similar claims and classify relationships."""
    from propstore.embed import find_similar, get_registered_models, _load_vec_extension

    _load_vec_extension(conn)

    if embedding_model is None:
        models = get_registered_models(conn)
        if not models:
            raise ValueError("No embeddings found. Run 'pks claim embed' first.")
        embedding_model = models[0]["model_name"]

    # Get source claim text
    claim_a = _get_claim_text(conn, claim_id)
    if not claim_a:
        raise ValueError(f"Claim {claim_id} not found")

    # Find similar claims
    candidates = find_similar(conn, claim_id, embedding_model, top_k=top_k)

    # Classify each candidate
    stances = []
    for candidate in candidates:
        claim_b = _get_claim_text(conn, candidate["id"])
        if not claim_b:
            continue
        stance = classify_stance(claim_a, claim_b, model_name)
        if stance:
            stances.append(stance)

    return stances


def relate_all(
    conn: sqlite3.Connection,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict:
    """Classify relationships for all claims."""
    all_claims = conn.execute("SELECT id FROM claim").fetchall()
    total = len(all_claims)

    total_stances = 0
    total_none = 0
    processed = 0
    all_stances: dict[str, list[dict]] = {}

    for row in all_claims:
        claim_id = row["id"]
        try:
            stances = relate_claim(conn, claim_id, model_name, embedding_model, top_k)
            if stances:
                all_stances[claim_id] = stances
                total_stances += len(stances)
            total_none += top_k - len(stances)
        except ValueError:
            pass
        processed += 1
        if on_progress:
            on_progress(processed, total)

    return {
        "claims_processed": processed,
        "stances_found": total_stances,
        "no_relation": total_none,
        "stances_by_claim": all_stances,
    }


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
