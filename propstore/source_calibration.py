"""Source-level trust calibration derived from repository calibration claims."""

from __future__ import annotations

from typing import Any

from propstore.cli.repository import Repository


def _source_bindings(source_doc: dict[str, Any]) -> dict[str, Any]:
    bindings: dict[str, Any] = {}
    kind = source_doc.get("kind")
    if isinstance(kind, str) and kind:
        bindings["source_kind"] = kind

    metadata = source_doc.get("metadata")
    if isinstance(metadata, dict):
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                bindings[key] = value

    origin = source_doc.get("origin")
    if isinstance(origin, dict):
        origin_type = origin.get("type")
        if isinstance(origin_type, str) and origin_type:
            bindings["origin_type"] = origin_type
    return bindings


def derive_source_trust(repo: Repository, source_doc: dict[str, Any]) -> dict[str, Any]:
    updated = dict(source_doc)
    trust = dict(updated.get("trust") or {})
    quality = dict(trust.get("quality") or {"b": 0.0, "d": 0.0, "u": 1.0, "a": 0.5})
    derived_from = list(trust.get("derived_from") or [])
    prior = float(trust.get("prior_base_rate", 0.5))

    if not repo.sidecar_path.exists():
        trust["prior_base_rate"] = prior
        trust["quality"] = quality
        trust["derived_from"] = derived_from
        updated["trust"] = trust
        return updated

    from propstore.world import WorldModel

    wm = WorldModel(repo)
    try:
        bindings = {
            key: value
            for key, value in _source_bindings(updated).items()
            if wm.resolve_concept(key) is not None
        }
        concept_id = wm.resolve_concept("source_trust_base_rate") or wm.resolve_concept("base_replication_rate")
        if concept_id is None:
            trust["prior_base_rate"] = prior
            trust["quality"] = quality
            trust["derived_from"] = derived_from
            updated["trust"] = trust
            return updated

        result = wm.chain_query(concept_id, **bindings)
        resolved = result.result
        resolved_prior: float | None = None
        resolved_from: list[str] = []

        if getattr(resolved, "status", None) == "derived" and getattr(resolved, "value", None) is not None:
            resolved_prior = float(resolved.value)
            resolved_from = [str(step.concept_id) for step in result.steps if getattr(step, "source", None) != "binding"]
        elif getattr(resolved, "status", None) == "determined":
            claims = list(getattr(resolved, "claims", []) or [])
            if claims:
                claim = claims[0]
                value = claim.get("value")
                if isinstance(value, (int, float)):
                    resolved_prior = float(value)
                    claim_id = claim.get("artifact_id") or claim.get("id")
                    if isinstance(claim_id, str) and claim_id:
                        resolved_from = [claim_id]

        if resolved_prior is not None:
            prior = resolved_prior
            derived_from = resolved_from or derived_from
    finally:
        wm.close()

    trust["prior_base_rate"] = prior
    trust["quality"] = quality
    trust["derived_from"] = derived_from
    updated["trust"] = trust
    return updated
