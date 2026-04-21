"""LLM stance classifier — pure classification of epistemic relationships between claims.

Separated from relate.py: this module is a pure function mapping
(claim_a, claim_b, context) -> [forward_stance, reverse_stance].

Single LLM call classifies both directions. Enrichment context is conditionally
included when embedding distance is below threshold.

Literature grounding:
- Josang 2001 (p.8, Def 9): vacuous opinion for total ignorance
- Josang 2001 (p.5, Def 6): E(w) = b + a*u
- Guo et al. 2017 (p.0): raw neural scores are miscalibrated
"""

from __future__ import annotations

import asyncio
import importlib
import json
import logging
from dataclasses import dataclass

from propstore.calibrate import categorical_to_opinion
from propstore.opinion import Opinion
from propstore.provenance import Provenance, ProvenanceStatus
from propstore.stances import VALID_STANCE_TYPES, StanceType


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


_CLASSIFICATION_PROMPT = """Given two propositional claims from scientific papers, classify their epistemic relationship in BOTH directions.

Claim A (from {source_a}):
  "{statement_a}"

Claim B (from {source_b}):
  "{statement_b}"

{enrichment_context}

Valid relationship types:
- rebuts: directly contradicts the other's conclusion
- undercuts: attacks the other's inference method or reasoning
- undermines: weakens the other's premise or evidence quality
- supports: provides corroborating evidence for the other
- explains: provides a mechanistic explanation for why the other is true
- supersedes: replaces the other entirely (newer data, better method, corrects error)
- none: no meaningful epistemic relationship

Classify BOTH directions:
1. "forward": the relationship FROM Claim A's perspective TOWARD Claim B
2. "reverse": the relationship FROM Claim B's perspective TOWARD Claim A

Respond with ONLY a JSON object (no markdown, no explanation):
{{"forward": {{"type": "<type or none>", "strength": "<strong|moderate|weak>", "note": "<1 sentence>", "conditions_differ": "<or null>"}}, "reverse": {{"type": "<type or none>", "strength": "<strong|moderate|weak>", "note": "<1 sentence>", "conditions_differ": "<or null>"}}}}"""


_ENRICHMENT_THRESHOLD_DEFAULT = 0.75


@dataclass(frozen=True)
class ClassifiedStance:
    stance_type: StanceType
    opinion: Opinion
    note: str = ""
    conditions_differ: str | None = None


def _vacuous_classifier_opinion(operation: str) -> Opinion:
    return Opinion.vacuous(
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

    stance_type = StanceType.NONE
    raw_type = raw.get("type")
    if raw_type in VALID_STANCE_TYPES:
        stance_type = StanceType(str(raw_type))

    if stance_type is StanceType.NONE:
        opinion = _vacuous_classifier_opinion("stance_classification_none")
    else:
        opinion = categorical_to_opinion(str(raw.get("strength", "moderate")), 1)
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


def _build_error_pair(
    claim_a_id: str,
    claim_b_id: str,
    model_name: str,
    embedding_model: str | None,
    embedding_distance: float | None,
    note: str,
) -> list[dict]:
    """Build a pair of error stances (forward + reverse)."""
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
        },
    }
    forward = {**base, "target": claim_b_id}
    reverse = {**base, "target": claim_a_id}
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


def _build_stance_dict(
    raw: dict,
    target_id: str,
    model_name: str,
    embedding_model: str | None,
    embedding_distance: float | None,
    reference_distances: list[float] | None,
    calibration_counts: dict[tuple[int, str], tuple[int, int]] | None,
) -> dict:
    """Build a single stance dict from raw LLM output for one direction."""
    stance_type = raw.get("type", "none")
    if stance_type not in VALID_STANCE_TYPES:
        stance_type = "none"

    strength = raw.get("strength", "moderate")
    if stance_type != "none":
        opinion = categorical_to_opinion(strength, 1, calibration_counts=calibration_counts)

        if reference_distances is not None and embedding_distance is not None and len(reference_distances) > 0:
            from propstore.calibrate import CorpusCalibrator
            from propstore.opinion import fuse
            corpus_cal = CorpusCalibrator(reference_distances)
            corpus_opinion = corpus_cal.to_opinion(embedding_distance)
            opinion = fuse(opinion, corpus_opinion)

        confidence = opinion.expectation()
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
    }

    return {
        "target": target_id,
        "type": stance_type,
        "strength": strength,
        "note": raw.get("note", ""),
        "conditions_differ": raw.get("conditions_differ"),
        "resolution": resolution,
    }


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
) -> list[dict]:
    """Classify epistemic relationship between two claims in both directions.

    Single LLM call, returns [forward_stance, reverse_stance].
    Forward: A's perspective toward B. Reverse: B's perspective toward A.
    """
    litellm = _require_litellm()

    if not enrichment_context and shared_concept_ids is not None:
        enrichment_context = build_enrichment_context(
            embedding_distance, enrichment_threshold, shared_concept_ids,
        )

    prompt = _CLASSIFICATION_PROMPT.format(
        source_a=claim_a.get("source_paper", "unknown"),
        statement_a=claim_a["text"],
        source_b=claim_b.get("source_paper", "unknown"),
        statement_b=claim_b["text"],
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
            logging.warning("Stance classification failed for %s vs %s: %s", claim_a["id"], claim_b["id"], exc)
            return _build_error_pair(claim_a["id"], claim_b["id"], model_name, embedding_model, embedding_distance, "classification failed")

    response_text = _response_content_text(response)
    if response_text is None:
        return _build_error_pair(claim_a["id"], claim_b["id"], model_name, embedding_model, embedding_distance, "missing response content")

    text = response_text.strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        return _build_error_pair(claim_a["id"], claim_b["id"], model_name, embedding_model, embedding_distance, "JSON parse failed")

    # Extract forward and reverse from bidirectional response
    forward_raw = result.get("forward", result)  # fallback: treat whole response as forward
    reverse_raw = result.get("reverse", {"type": "none", "strength": "weak", "note": "not classified", "conditions_differ": None})

    forward = _build_stance_dict(
        forward_raw, claim_b["id"], model_name, embedding_model, embedding_distance,
        reference_distances, calibration_counts,
    )
    reverse = _build_stance_dict(
        reverse_raw, claim_a["id"], model_name, embedding_model, embedding_distance,
        reference_distances, calibration_counts,
    )

    return [forward, reverse]


def classify_stance(
    claim_a: dict,
    claim_b: dict,
    model_name: str,
) -> list[dict]:
    """Classify the epistemic relationship between two claims via LLM (sync wrapper)."""
    sem = asyncio.Semaphore(1)
    from propstore.relate import _run_async
    return _run_async(classify_stance_async(claim_a, claim_b, model_name, sem))
