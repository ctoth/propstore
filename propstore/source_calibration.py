"""Source-level trust calibration derived from repository calibration claims."""

from __future__ import annotations

from propstore.repository import Repository
from propstore.artifacts.schema import convert_document_value
from propstore.source.common import load_source_metadata, normalize_source_slug
from propstore.artifacts.documents.sources import SourceDocument
from propstore.provenance import ProvenanceStatus


def _optional_dict(value: object, field_name: str) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"source trust field '{field_name}' must be a mapping")
    return dict(value)


def _source_bindings(
    source_doc: SourceDocument,
    metadata: dict[str, object] | None = None,
) -> dict[str, str | int | float | bool]:
    bindings: dict[str, str | int | float | bool] = {}
    if source_doc.kind:
        bindings["source_kind"] = source_doc.kind.value

    if source_doc.metadata is not None:
        for key, value in source_doc.metadata.to_payload().items():
            if isinstance(value, (str, int, float, bool)):
                bindings[key] = value

    if isinstance(metadata, dict):
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                bindings[key] = value

    if source_doc.origin.type:
        bindings["origin_type"] = source_doc.origin.type.value
    return bindings


def derive_source_trust(repo: Repository, source_doc: SourceDocument) -> SourceDocument:
    updated = source_doc.to_payload()
    trust = _optional_dict(updated.get("trust"), "trust")
    raw_quality = trust.get("quality")
    quality = (
        _optional_dict(raw_quality, "quality")
        if raw_quality is not None
        else {
            "status": ProvenanceStatus.VACUOUS.value,
            "b": 0.0,
            "d": 0.0,
            "u": 1.0,
            "a": 0.5,
        }
    )
    if "status" not in quality:
        quality["status"] = ProvenanceStatus.VACUOUS.value
    derived_from = list(trust.get("derived_from") or [])
    prior = float(trust.get("prior_base_rate", 0.5))
    trust["status"] = trust.get("status") or ProvenanceStatus.DEFAULTED.value

    if not repo.sidecar_path.exists():
        trust["prior_base_rate"] = prior
        trust["quality"] = quality
        trust["derived_from"] = derived_from
        updated["trust"] = trust
        return convert_document_value(updated, SourceDocument, source="source trust calibration")

    from propstore.world import WorldModel

    wm = WorldModel(repo)
    try:
        source_name = normalize_source_slug(
            source_doc.metadata.name if source_doc.metadata is not None else source_doc.id
        )
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
            trust["status"] = ProvenanceStatus.CALIBRATED.value
    finally:
        wm.close()

    if not derived_from and trust.get("status") == ProvenanceStatus.CALIBRATED.value:
        trust["status"] = ProvenanceStatus.DEFAULTED.value
    trust["prior_base_rate"] = prior
    trust["quality"] = quality
    trust["derived_from"] = derived_from
    updated["trust"] = trust
    return convert_document_value(updated, SourceDocument, source="source trust calibration")
