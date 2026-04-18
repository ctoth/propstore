"""Summaries and lightweight analysis over stance and relation surfaces."""

from __future__ import annotations

from propstore.core.relation_types import NON_ATTACK_TYPES
from propstore.core.row_types import coerce_stance_row
from propstore.world.types import WorldStore


def stance_summary(
    store: WorldStore,
    active_claim_ids: set[str],
) -> dict:
    """Summarize stances used in argumentation-facing render explanations.

    Returns counts, opinion statistics, and model info so the render layer can
    explain which stances were included under what policy.

    All stances participate in AF construction regardless of opinion
    uncertainty, per Li et al. (2012, Def 2) and the CLAUDE.md design
    checklist (no gates before render time). Vacuous opinions
    (Josang 2001, p.8) are counted but not pruned; filtering is deferred
    to render and resolution time.
    """
    rows = store.stances_between(active_claim_ids)

    total = 0
    included = 0
    vacuous_count = 0
    excluded_non_attack = 0
    models: set[str] = set()
    uncertainties: list[float] = []

    for row_input in rows:
        row = coerce_stance_row(row_input)
        total += 1
        stype = row.stance_type
        model = row.attributes.get("resolution_model")
        opinion_u = row.attributes.get("opinion_uncertainty")

        if stype in NON_ATTACK_TYPES:
            excluded_non_attack += 1
            continue

        included += 1
        if isinstance(model, str) and model:
            models.add(model)
        if isinstance(opinion_u, int | float):
            opinion_value = float(opinion_u)
            uncertainties.append(opinion_value)
            if opinion_value > 0.99:
                vacuous_count += 1

    result: dict = {
        "total_stances": total,
        "included_as_attacks": included,
        "vacuous_count": vacuous_count,
        "excluded_non_attack": excluded_non_attack,
        "models": sorted(models),
    }
    if uncertainties:
        result["mean_uncertainty"] = sum(uncertainties) / len(uncertainties)

    return result
