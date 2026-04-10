"""Source-level trust calibration derived from repository calibration claims."""

from __future__ import annotations

from propstore.cli.repository import Repository
from propstore.document_schema import convert_document_value
from propstore.source.common import load_source_metadata, normalize_source_slug
from propstore.source.document_models import SourceDocument


def _source_bindings(
    source_doc: SourceDocument,
    metadata: dict[str, object] | None = None,
) -> dict[str, str | int | float | bool]:
    bindings: dict[str, str | int | float | bool] = {}
    if source_doc.kind:
        bindings["source_kind"] = source_doc.kind

    for key, value in source_doc.metadata.to_payload().items():
        if isinstance(value, (str, int, float, bool)):
            bindings[key] = value

    if isinstance(metadata, dict):
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                bindings[key] = value

    if source_doc.origin.type:
        bindings["origin_type"] = source_doc.origin.type
    return bindings


def derive_source_trust(repo: Repository, source_doc: SourceDocument) -> SourceDocument:
    updated = source_doc.to_payload()
    trust = dict(updated.get("trust") or {})
    quality = dict(trust.get("quality") or {"b": 0.0, "d": 0.0, "u": 1.0, "a": 0.5})
    derived_from = list(trust.get("derived_from") or [])
    prior = float(trust.get("prior_base_rate", 0.5))

    if not repo.sidecar_path.exists():
        trust["prior_base_rate"] = prior
        trust["quality"] = quality
        trust["derived_from"] = derived_from
        updated["trust"] = trust
        return convert_document_value(updated, SourceDocument, source="source trust calibration")

    from propstore.world import WorldModel

    wm = WorldModel(repo)
    try:
        source_name = normalize_source_slug(source_doc.metadata.name)
        source_metadata = load_source_metadata(repo, source_name)
        bindings = {
            key: value
            for key, value in _source_bindings(source_doc, source_metadata).items()
            if wm.resolve_concept(key) is not None
        }
        concept_id = wm.resolve_concept("source_trust_base_rate") or wm.resolve_concept("base_replication_rate")
        if concept_id is None:
            trust["prior_base_rate"] = prior
            trust["quality"] = quality
            trust["derived_from"] = derived_from
            updated["trust"] = trust
            return convert_document_value(updated, SourceDocument, source="source trust calibration")

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
                value = getattr(claim, "value", None)
                if isinstance(value, (int, float)):
                    resolved_prior = float(value)
                    claim_id = getattr(claim, "artifact_id", None) or getattr(claim, "id", None)
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
    return convert_document_value(updated, SourceDocument, source="source trust calibration")
