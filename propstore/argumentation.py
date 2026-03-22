"""Bridge between stance graph and Dung argumentation framework.

Converts raw attacks (from claim_stance table) into filtered defeats
(after preference ordering), builds a Dung AF, and computes extensions.

References:
    Modgil, S. & Prakken, H. (2018). Def 8 (attack types),
    Def 9 (defeat = attack surviving preference filter).
"""

from __future__ import annotations

import sqlite3

from propstore.dung import (
    ArgumentationFramework,
    grounded_extension,
    preferred_extensions,
    stable_extensions,
)
from propstore.preference import claim_strength, defeat_holds

_ATTACK_TYPES = frozenset({"rebuts", "undercuts", "undermines", "supersedes"})
_UNCONDITIONAL_TYPES = frozenset({"undercuts", "supersedes"})
_PREFERENCE_TYPES = frozenset({"rebuts", "undermines"})
_NON_ATTACK_TYPES = frozenset({"supports", "explains", "none"})


def build_argumentation_framework(
    conn: sqlite3.Connection,
    active_claim_ids: set[str],
    *,
    comparison: str = "elitist",
    confidence_threshold: float = 0.5,
) -> ArgumentationFramework:
    """Build a Dung AF from the stance graph filtered through preferences.

    Steps (per Def 9, p.12):
      1. Load stances between active claims with confidence >= threshold
      2. Undercutting/supersedes → always defeat
      3. Rebuts/undermines → defeat iff attacker NOT strictly weaker
      4. Supports/explains → excluded (not attacks)
    """
    # Load claim metadata for strength computation
    placeholders = ",".join("?" for _ in active_claim_ids)
    claim_rows = conn.execute(
        f"SELECT * FROM claim WHERE id IN ({placeholders})",  # noqa: S608
        list(active_claim_ids),
    ).fetchall()
    claims_by_id = {row["id"]: dict(row) for row in claim_rows}

    # Load stances between active claims above confidence threshold
    stances = conn.execute(
        f"SELECT claim_id, target_claim_id, stance_type, confidence "  # noqa: S608
        f"FROM claim_stance "
        f"WHERE claim_id IN ({placeholders}) "
        f"AND target_claim_id IN ({placeholders})",
        list(active_claim_ids) + list(active_claim_ids),
    ).fetchall()

    defeats: set[tuple[str, str]] = set()

    for stance in stances:
        attacker_id = stance["claim_id"]
        target_id = stance["target_claim_id"]
        stance_type = stance["stance_type"]
        confidence = stance["confidence"]

        if stance_type in _NON_ATTACK_TYPES:
            continue

        if confidence is not None and confidence < confidence_threshold:
            continue

        if stance_type in _UNCONDITIONAL_TYPES:
            defeats.add((attacker_id, target_id))
        elif stance_type in _PREFERENCE_TYPES:
            attacker_claim = claims_by_id.get(attacker_id, {})
            target_claim = claims_by_id.get(target_id, {})
            attacker_s = [claim_strength(attacker_claim)]
            target_s = [claim_strength(target_claim)]
            if defeat_holds(stance_type, attacker_s, target_s, comparison):
                defeats.add((attacker_id, target_id))

    return ArgumentationFramework(
        arguments=frozenset(active_claim_ids),
        defeats=frozenset(defeats),
    )


def compute_justified_claims(
    conn: sqlite3.Connection,
    active_claim_ids: set[str],
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
    confidence_threshold: float = 0.5,
) -> frozenset[str] | list[frozenset[str]]:
    """End-to-end: build AF, compute extensions, return justified claim IDs.

    For grounded: returns a single frozenset (the unique grounded extension).
    For preferred/stable: returns a list of frozensets.
    """
    af = build_argumentation_framework(
        conn, active_claim_ids,
        comparison=comparison,
        confidence_threshold=confidence_threshold,
    )

    if semantics == "grounded":
        return grounded_extension(af)
    elif semantics == "preferred":
        return [frozenset(e) for e in preferred_extensions(af)]
    elif semantics == "stable":
        return [frozenset(e) for e in stable_extensions(af)]
    else:
        raise ValueError(f"Unknown semantics: {semantics}")
