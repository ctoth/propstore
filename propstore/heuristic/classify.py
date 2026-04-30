"""LLM stance classifier — pure classification of epistemic relationships between claims.

Separated from relate.py: this module is a pure function mapping
(claim_a, claim_b, context) -> [forward_stance, reverse_stance].

Forward and reverse stances are classified with independent LLM calls. Enrichment
context is conditionally included when embedding distance is below threshold.

Literature grounding:
- Josang 2001 (p.8, Def 9): vacuous opinion for total ignorance
- Josang 2001 (p.5, Def 6): E(w) = b + a*u
- Guo et al. 2017 (p.0): raw neural scores are miscalibrated
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import json
import logging
from dataclasses import dataclass
from typing import Any

from propstore.heuristic.calibrate import CategoryPriorRegistry, categorical_to_opinion
from propstore.core.base_rates import BaseRateUnresolved
from propstore.opinion import Opinion
from propstore.provenance import Provenance, ProvenanceStatus
from propstore.stances import VALID_STANCE_TYPES, StanceType


_CLASSIFIER_ABSTAIN_BASE_RATE = 0.5


def _require_litellm():
    try:
        return importlib.import_module("litellm")
    except ImportError:
        raise ImportError(
            "litellm is required for relate commands. "
            "Install with: uv pip install 'propstore[embeddings]'"
        )


def _response_content_text(response: object) -> str | None:
    choices = getattr(response, "choices", None)
    if not isinstance(choices, list) or not choices:
        return None
    message = getattr(choices[0], "message", None)
    if message is None:
        return None
    content = getattr(message, "content", None)
    return content if isinstance(content, str) else None


_DIRECTIONAL_CLASSIFICATION_PROMPT = """Given two propositional claims from scientific papers, classify their epistemic relationship in exactly one direction.

Claim {source_label} (from {source_paper}):
  "{source_statement}"

Claim {target_label} (from {target_paper}):
  "{target_statement}"

{enrichment_context}

Valid relationship types:
- rebuts: directly contradicts the other's conclusion
- undercuts: attacks the other's inference method or reasoning
- undermines: weakens the other's premise or evidence quality
- supports: provides corroborating evidence for the other
- explains: provides a mechanistic explanation for why the other is true
- supersedes: replaces the other entirely (newer data, better method, corrects error)
- none: no meaningful epistemic relationship

Classify one direction only: FROM Claim {source_label}'s perspective TOWARD Claim {target_label}.

Respond with ONLY a JSON object (no markdown, no explanation):
{{"type": "<type or none>", "strength": "<strong|moderate|weak>", "note": "<1 sentence>", "conditions_differ": "<or null>"}}"""


_ENRICHMENT_THRESHOLD_DEFAULT = 0.75


@dataclass(frozen=True)
class ClassifiedStance:
    stance_type: StanceType
    opinion: Opinion
    note: str = ""
    conditions_differ: str | None = None


def _vacuous_classifier_opinion(operation: str) -> Opinion:
    return Opinion.vacuous(
        _CLASSIFIER_ABSTAIN_BASE_RATE,
        provenance=Provenance(
            status=ProvenanceStatus.VACUOUS,
            witnesses=(),
            operations=(operation,),
        ),
    )


def classify_stance_from_llm_output(raw: dict) -> ClassifiedStance:
    """Classify a single LLM stance payload into an explicit domain object.

    Per Jøsang 2001, p.8, Def. 9, classifier failures are represented as a
    vacuous opinion rather than a fabricated negative or reverse stance.
    """
    if raw.get("type") == "error":
        return ClassifiedStance(
            stance_type=StanceType.ABSTAIN,
            opinion=_vacuous_classifier_opinion("stance_classification_error"),
            note=str(raw.get("note", "")),
            conditions_differ=raw.get("conditions_differ"),
        )

    confidence = raw.get("confidence")
    if confidence is None and isinstance(raw.get("resolution"), dict):
        confidence = raw["resolution"].get("confidence")
    try:
        confidence_value = None if confidence is None else float(confidence)
    except (TypeError, ValueError):
        confidence_value = None
    if confidence_value is None or confidence_value <= 0.0:
        operation = (
            "stance_classification_missing_confidence"
            if confidence_value is None
            else "stance_classification_zero_confidence"
        )
        return ClassifiedStance(
            stance_type=StanceType.ABSTAIN,
            opinion=_vacuous_classifier_opinion(operation),
            note=str(raw.get("note", "")),
            conditions_differ=raw.get("conditions_differ"),
        )

    stance_type = StanceType.NONE
    raw_type = raw.get("type")
    if raw_type in VALID_STANCE_TYPES:
        stance_type = StanceType(str(raw_type))

    if stance_type is StanceType.NONE or stance_type is StanceType.ABSTAIN:
        opinion = _vacuous_classifier_opinion("stance_classification_none")
    else:
        strength = raw.get("strength")
        if strength is None:
            return ClassifiedStance(
                stance_type=StanceType.ABSTAIN,
                opinion=_vacuous_classifier_opinion(
                    "stance_classification_missing_strength",
                ),
                note=str(raw.get("note", "")),
                conditions_differ=raw.get("conditions_differ"),
            )
        opinion = categorical_to_opinion(str(strength), 1)
        if isinstance(opinion, BaseRateUnresolved):
            return ClassifiedStance(
                stance_type=StanceType.ABSTAIN,
                opinion=_vacuous_classifier_opinion("stance_classification_missing_base_rate"),
                note=str(raw.get("note", "")),
                conditions_differ=raw.get("conditions_differ"),
            )
    return ClassifiedStance(
        stance_type=stance_type,
        opinion=opinion,
        note=str(raw.get("note", "")),
        conditions_differ=raw.get("conditions_differ"),
    )


def build_enrichment_context(
    distance: float | None,
    threshold: float,
    shared_concept_ids: list[str],
) -> str:
    """Build optional enrichment context for close claim pairs.

    Returns non-empty string iff distance is not None and distance < threshold.
    """
    if distance is None or distance >= threshold:
        return ""
    parts = [f"These claims are highly similar by embedding distance ({distance:.4f})."]
    if shared_concept_ids:
        parts.append(f"Shared concepts: {', '.join(shared_concept_ids)}")
    parts.append("Look specifically for subtle relationships that might not be obvious at first glance.")
    return " ".join(parts)


def _build_error_stance(
    target_id: str,
    model_name: str,
    embedding_model: str | None,
    embedding_distance: float | None,
    note: str,
    *,
    perspective_source_claim_id: str | None = None,
    prompt: str | None = None,
    raw_response: object | None = None,
    llm_call_id: str | None = None,
) -> dict:
    """Build a single error stance without inferring an unobserved direction."""
    base = {
        "type": "error",
        "strength": "weak",
        "note": note,
        "conditions_differ": None,
        "resolution": {
            "method": "nli",
            "model": model_name,
            "embedding_model": embedding_model,
            "embedding_distance": embedding_distance,
            "confidence": 0.0,
            "llm_call_id": llm_call_id,
            "prompt": prompt,
            "raw_response": raw_response,
        },
    }
    payload = {**base, "target": target_id}
    if perspective_source_claim_id is not None:
        payload["perspective_source_claim_id"] = perspective_source_claim_id
    return payload


def _build_error_pair(
    claim_a_id: str,
    claim_b_id: str,
    model_name: str,
    embedding_model: str | None,
    embedding_distance: float | None,
    note: str,
) -> list[dict]:
    """Build a pair of error stances when both directions failed equally."""
    forward = _build_error_stance(
        claim_b_id,
        model_name,
        embedding_model,
        embedding_distance,
        note,
    )
    reverse = _build_error_stance(
        claim_a_id,
        model_name,
        embedding_model,
        embedding_distance,
        note,
    )
    return [forward, reverse]


def _opinion_payload(opinion: Opinion | None) -> dict | None:
    if opinion is None:
        return None
    if opinion.provenance is None:
        raise ValueError("Resolution opinion must carry provenance")
    return {
        "b": float(opinion.b),
        "d": float(opinion.d),
        "u": float(opinion.u),
        "a": float(opinion.a),
        "provenance": opinion.provenance.to_payload(),
    }


def _unresolved_payload(unresolved: BaseRateUnresolved | None) -> dict | None:
    if unresolved is None:
        return None
    return {
        "reason": unresolved.reason,
        "missing_fields": list(unresolved.missing_fields),
    }


def _build_stance_dict(
    raw: dict,
    target_id: str,
    model_name: str,
    embedding_model: str | None,
    embedding_distance: float | None,
    reference_distances: list[float] | None,
    calibration_counts: dict[tuple[int, str], tuple[int, int]] | None,
    category_prior_registry: CategoryPriorRegistry | None,
    *,
    perspective_source_claim_id: str,
    prompt: str,
    raw_response: dict,
    llm_call_id: str,
) -> dict:
    """Build a single stance dict from raw LLM output for one direction."""
    stance_type = raw.get("type", "none")
    if stance_type not in VALID_STANCE_TYPES:
        stance_type = "none"

    strength = raw.get("strength", "moderate")
    unresolved: BaseRateUnresolved | None = None
    if stance_type != "none":
        category_opinion = categorical_to_opinion(
            strength,
            1,
            calibration_counts=calibration_counts,
            prior_registry=category_prior_registry,
        )
        if isinstance(category_opinion, BaseRateUnresolved):
            opinion = None
            unresolved = category_opinion
        else:
            opinion = category_opinion

        if opinion is not None and reference_distances is not None and embedding_distance is not None and len(reference_distances) > 0:
            from propstore.heuristic.calibrate import CorpusCalibrator
            from propstore.opinion import fuse
            corpus_cal = CorpusCalibrator(reference_distances, corpus_base_rate=opinion.a)
            corpus_opinion = corpus_cal.to_opinion(embedding_distance)
            opinion = fuse(opinion, corpus_opinion)

        confidence = 0.0 if opinion is None else opinion.expectation()
    else:
        confidence = 0.0
        opinion = None

    resolution = {
        "method": "nli",
        "model": model_name,
        "embedding_model": embedding_model,
        "embedding_distance": embedding_distance,
        "confidence": confidence,
        "opinion": _opinion_payload(opinion),
        "unresolved_calibration": _unresolved_payload(unresolved),
        "llm_call_id": llm_call_id,
        "prompt": prompt,
        "raw_response": raw_response,
    }

    return {
        "target": target_id,
        "perspective_source_claim_id": perspective_source_claim_id,
        "type": stance_type,
        "strength": strength,
        "note": raw.get("note", ""),
        "conditions_differ": raw.get("conditions_differ"),
        "resolution": resolution,
    }


def _directional_prompt(
    source_claim: dict,
    target_claim: dict,
    *,
    source_label: str,
    target_label: str,
    enrichment_context: str,
) -> str:
    return _DIRECTIONAL_CLASSIFICATION_PROMPT.format(
        source_label=source_label,
        source_paper=source_claim.get("source_paper", "unknown"),
        source_statement=source_claim["text"],
        target_label=target_label,
        target_paper=target_claim.get("source_paper", "unknown"),
        target_statement=target_claim["text"],
        enrichment_context=enrichment_context,
    )


def _llm_call_id(*, model_name: str, prompt: str, response_text: str) -> str:
    payload = json.dumps(
        {
            "model": model_name,
            "prompt": prompt,
            "response": response_text,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def _classify_one_direction(
    litellm: Any,
    *,
    source_claim: dict,
    target_claim: dict,
    source_label: str,
    target_label: str,
    model_name: str,
    semaphore: asyncio.Semaphore,
    embedding_model: str | None,
    embedding_distance: float | None,
    enrichment_context: str,
    reference_distances: list[float] | None,
    calibration_counts: dict[tuple[int, str], tuple[int, int]] | None,
    category_prior_registry: CategoryPriorRegistry | None,
) -> dict:
    prompt = _directional_prompt(
        source_claim,
        target_claim,
        source_label=source_label,
        target_label=target_label,
        enrichment_context=enrichment_context,
    )
    async with semaphore:
        try:
            response = await litellm.acompletion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
        except (ConnectionError, TimeoutError, OSError, ValueError) as exc:
            logging.warning(
                "Stance classification failed for %s vs %s: %s",
                source_claim["id"],
                target_claim["id"],
                exc,
            )
            return _build_error_stance(
                target_claim["id"],
                model_name,
                embedding_model,
                embedding_distance,
                "classification failed",
                perspective_source_claim_id=source_claim["id"],
                prompt=prompt,
            )

    response_text = _response_content_text(response)
    if response_text is None:
        return _build_error_stance(
            target_claim["id"],
            model_name,
            embedding_model,
            embedding_distance,
            "missing response content",
            perspective_source_claim_id=source_claim["id"],
            prompt=prompt,
        )

    text = response_text.strip()
    call_id = _llm_call_id(model_name=model_name, prompt=prompt, response_text=text)
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        return _build_error_stance(
            target_claim["id"],
            model_name,
            embedding_model,
            embedding_distance,
            "JSON parse failed",
            perspective_source_claim_id=source_claim["id"],
            prompt=prompt,
            raw_response=text,
            llm_call_id=call_id,
        )
    if not isinstance(result, dict):
        return _build_error_stance(
            target_claim["id"],
            model_name,
            embedding_model,
            embedding_distance,
            "non-object response",
            perspective_source_claim_id=source_claim["id"],
            prompt=prompt,
            raw_response=result,
            llm_call_id=call_id,
        )

    return _build_stance_dict(
        result,
        target_claim["id"],
        model_name,
        embedding_model,
        embedding_distance,
        reference_distances,
        calibration_counts,
        category_prior_registry,
        perspective_source_claim_id=source_claim["id"],
        prompt=prompt,
        raw_response=result,
        llm_call_id=call_id,
    )


async def classify_stance_async(
    claim_a: dict,
    claim_b: dict,
    model_name: str,
    semaphore: asyncio.Semaphore,
    *,
    embedding_model: str | None = None,
    embedding_distance: float | None = None,
    enrichment_context: str = "",
    shared_concept_ids: list[str] | None = None,
    enrichment_threshold: float = _ENRICHMENT_THRESHOLD_DEFAULT,
    reference_distances: list[float] | None = None,
    calibration_counts: dict[tuple[int, str], tuple[int, int]] | None = None,
    category_prior_registry: CategoryPriorRegistry | None = None,
) -> list[dict]:
    """Classify epistemic relationship between two claims in both directions.

    Two independent LLM calls, returns [forward_stance, reverse_stance].
    Forward: A's perspective toward B. Reverse: B's perspective toward A.
    """
    litellm = _require_litellm()

    if not enrichment_context and shared_concept_ids is not None:
        enrichment_context = build_enrichment_context(
            embedding_distance, enrichment_threshold, shared_concept_ids,
        )

    forward, reverse = await asyncio.gather(
        _classify_one_direction(
            litellm,
            source_claim=claim_a,
            target_claim=claim_b,
            source_label="A",
            target_label="B",
            model_name=model_name,
            semaphore=semaphore,
            embedding_model=embedding_model,
            embedding_distance=embedding_distance,
            enrichment_context=enrichment_context,
            reference_distances=reference_distances,
            calibration_counts=calibration_counts,
            category_prior_registry=category_prior_registry,
        ),
        _classify_one_direction(
            litellm,
            source_claim=claim_b,
            target_claim=claim_a,
            source_label="B",
            target_label="A",
            model_name=model_name,
            semaphore=semaphore,
            embedding_model=embedding_model,
            embedding_distance=embedding_distance,
            enrichment_context=enrichment_context,
            reference_distances=reference_distances,
            calibration_counts=calibration_counts,
            category_prior_registry=category_prior_registry,
        ),
    )

    return [forward, reverse]


def classify_stance(
    claim_a: dict,
    claim_b: dict,
    model_name: str,
) -> list[dict]:
    """Classify the epistemic relationship between two claims via LLM (sync wrapper)."""
    sem = asyncio.Semaphore(1)
    from propstore.heuristic.relate import _run_async
    return _run_async(classify_stance_async(claim_a, claim_b, model_name, sem))
