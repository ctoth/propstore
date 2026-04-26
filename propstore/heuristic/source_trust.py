"""Source-level trust heuristics and repository calibration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from quire.documents import convert_document_value

from propstore.families.documents.sources import SourceDocument
from propstore.opinion import Opinion, consensus
from propstore.provenance import ProvenanceStatus
from propstore.repository import Repository
from propstore.source.common import load_source_metadata, normalize_source_slug
from propstore.world.types import DerivedResult, ValueResult, ValueStatus


def derive_source_trust(*, prior: Opinion, chain_opinion: Opinion) -> Opinion:
    """Combine caller prior and source-chain trust by Jøsang consensus.

    Jøsang 2001 (§4.1) combines independent opinions by consensus rather than
    choosing one source of trust and discarding the other.
    """

    return consensus(prior, chain_opinion)


def _optional_dict(value: object, field_name: str) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"source trust field '{field_name}' must be a mapping")
    return dict(value)


def _optional_present_dict(value: object, field_name: str) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(f"source trust field '{field_name}' must be a mapping")
    return dict(value)


def _optional_string_list(value: object, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"source trust field '{field_name}' must be a list")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"source trust field '{field_name}' must contain only strings")
    return list(value)


def _optional_float(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"source trust field '{field_name}' must be numeric")
    return float(value)


def _write_trust_fields(
    trust: dict[str, object],
    *,
    prior: float | None,
    quality: dict[str, object] | None,
    derived_from: list[str],
) -> None:
    if prior is None:
        trust.pop("prior_base_rate", None)
    else:
        trust["prior_base_rate"] = prior
    if quality is None:
        trust.pop("quality", None)
    else:
        trust["quality"] = quality
    trust["derived_from"] = derived_from


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


def derive_source_document_trust(repo: Repository, source_doc: SourceDocument) -> SourceDocument:
    updated = source_doc.to_payload()
    trust = _optional_dict(updated.get("trust"), "trust")
    raw_quality = trust.get("quality")
    quality = _optional_present_dict(raw_quality, "quality")
    if quality is not None and "status" not in quality:
        quality["status"] = ProvenanceStatus.VACUOUS.value
    derived_from = _optional_string_list(trust.get("derived_from"), "derived_from")
    prior = _optional_float(trust.get("prior_base_rate"), "prior_base_rate")
    trust["status"] = trust.get("status") or ProvenanceStatus.DEFAULTED.value

    if not repo.sidecar_path.exists():
        _write_trust_fields(trust, prior=prior, quality=quality, derived_from=derived_from)
        updated["trust"] = trust
        return convert_document_value(updated, SourceDocument, source="source trust calibration")

    from propstore.world import WorldModel

    wm = WorldModel(repo)
    try:
        source_name = normalize_source_slug(
            source_doc.metadata.name if source_doc.metadata is not None else source_doc.id
        )
        source_metadata = load_source_metadata(repo, source_name)
        bindings: dict[str, Any] = {
            key: value
            for key, value in _source_bindings(source_doc, source_metadata).items()
            if wm.resolve_concept(key) is not None
        }
        concept_id = wm.resolve_concept("source_trust_base_rate") or wm.resolve_concept("base_replication_rate")
        if concept_id is None:
            _write_trust_fields(trust, prior=prior, quality=quality, derived_from=derived_from)
            updated["trust"] = trust
            return convert_document_value(updated, SourceDocument, source="source trust calibration")

        result = wm.chain_query(concept_id, **bindings)
        resolved = result.result
        resolved_prior: float | None = None
        resolved_from: list[str] = []

        if (
            isinstance(resolved, DerivedResult)
            and resolved.status is ValueStatus.DERIVED
            and resolved.value is not None
        ):
            resolved_prior = float(resolved.value)
            resolved_from = [str(step.concept_id) for step in result.steps if getattr(step, "source", None) != "binding"]
        elif isinstance(resolved, ValueResult) and resolved.status is ValueStatus.DETERMINED:
            claims = list(resolved.claims)
            if claims:
                claim = claims[0]
                value = claim.value
                if isinstance(value, (int, float)):
                    resolved_prior = float(value)
                    claim_id = claim.artifact_id
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
    _write_trust_fields(trust, prior=prior, quality=quality, derived_from=derived_from)
    updated["trust"] = trust
    return convert_document_value(updated, SourceDocument, source="source trust calibration")
