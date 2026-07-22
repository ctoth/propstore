"""Author claim proposals onto a source branch.

A claim is extracted into the source branch with its source-local handle and
its derived canonical identity (``artifact_id`` / ``version_id`` /
``logical_ids``) stamped by :func:`normalize_source_claims_payload`. Three
authoring-edge guards run before a batch is written — they never gate storage of
a *valid* claim, they reject malformed input:

* the **reserved-namespace guard** (``assert_namespace_not_reserved``): a source
  branch may not mint into the canonical ``ps`` / ``propstore`` namespaces;
* the **unknown-concept guard**: every source-local concept reference must name a
  concept proposed on this branch (or already a canonical ``ps:concept:`` / tag);
* the **CEL + form-value guards** (via ``condition_ir`` and Claim contracts):
  a claim's CEL conditions must type-check against the known concept kinds, and
  its value fields must satisfy the owning concept's form semantics.

Non-commitment (CLAUDE.md): a well-formed claim flows straight into the source
branch with provenance; there is no truth-gate and no render-time filtering here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import msgspec
from condition_ir import ConceptInfo, KindType, check_cel_expression
from quire.documents import decode_document_path

from propstore.canonical_namespaces import assert_namespace_not_reserved
from propstore.claim_contracts import validate_claim_value_fields
from propstore.core.scalars import ScalarValue
from propstore.families.claims import ClaimType
from propstore.families.concepts import Concept
from propstore.families.concepts_passes import (
    ConceptCheckedRegistry,
    ConceptPipelineContext,
    LoadedConcept,
    run_concept_pipeline,
)
from propstore.families.forms import FormDefinition
from propstore.families.identity.claims import (
    compute_claim_version_id,
    derive_claim_artifact_id,
    stable_claim_logical_value,
)
from propstore.families.identity.logical_ids import normalize_logical_value
from propstore.families.registry import SourceRef
from propstore.families.sources import (
    ClaimSourceDocument,
    ClaimLogicalIdDocument,
    ExtractionProvenanceDocument,
    SourceClaimDocument,
    SourceClaimsDocument,
    SourceProvenanceDocument,
)
from propstore.repository import Repository

from .common import (
    current_source_branch_head,
    is_stale_branch_error,
    load_source_claims_document,
    load_source_concepts_document,
    load_source_document,
    normalize_source_slug,
    source_tag_uri,
)

_CANONICAL_CONCEPT_PREFIXES = ("ps:concept:", "tag:")


def coerce_claim_type(value: object) -> ClaimType:
    """Coerce a claim-type string/enum to the canonical :class:`ClaimType`."""

    if isinstance(value, ClaimType):
        return value
    return ClaimType(str(value))


def source_concept_handles(repo: Repository, source_name: str) -> set[str]:
    """Return every concept handle proposed on the source branch."""

    handles: set[str] = set()
    concepts_doc = load_source_concepts_document(repo, source_name)
    if concepts_doc is None:
        return handles
    for entry in concepts_doc.concepts:
        if entry.local_name:
            handles.add(entry.local_name)
        if entry.proposed_name:
            handles.add(entry.proposed_name)
    return handles


def iter_claim_concept_refs(claim: SourceClaimDocument) -> list[str]:
    """Collect every source-local concept reference carried by *claim*."""

    refs: list[str] = []
    for value in (claim.concept, claim.target_concept):
        if isinstance(value, str):
            refs.append(value)
    refs.extend(claim.concepts)
    refs.extend(variable.concept for variable in claim.variables)
    refs.extend(parameter.concept for parameter in claim.parameters)
    return refs


def _is_canonical_concept_ref(reference: str) -> bool:
    return any(reference.startswith(prefix) for prefix in _CANONICAL_CONCEPT_PREFIXES)


def validate_source_claim_concepts(
    repo: Repository, source_name: str, data: SourceClaimsDocument
) -> None:
    """Reject a batch referencing a concept handle not proposed on this branch."""

    known_handles = source_concept_handles(repo, source_name)
    unknown: set[str] = set()
    for claim in data.claims:
        for concept_ref in iter_claim_concept_refs(claim):
            if _is_canonical_concept_ref(concept_ref):
                continue
            if concept_ref not in known_handles:
                unknown.add(concept_ref)
    if unknown:
        formatted = ", ".join(sorted(unknown))
        raise ValueError(f"unknown concept reference(s): {formatted}")


def _concept_form_name(concept: Concept) -> str | None:
    entry = concept.lexical_entry
    if entry is None:
        return None
    form_name = entry.physical_dimension_form
    return form_name if isinstance(form_name, str) and form_name else None


def validate_source_claim_cel_expressions(
    repo: Repository, source_name: str, data: SourceClaimsDocument
) -> dict[str, ConceptInfo]:
    """Reject a batch whose CEL conditions fail to type-check.

    The registry is the union of master's canonical concepts and the source
    branch's proposed concepts (master wins on name overlap). With no concepts
    resolvable yet (a fresh repository), validation is skipped — conditions are
    type-checked again at promote/build.
    """

    forms = _forms_by_name(repo)
    primary_concepts = [
        handle.document
        for handle in repo.families.concept.iter_handles()
        if isinstance(handle.document, Concept)
    ]
    primary_result = run_concept_pipeline(
        [LoadedConcept(concept=concept) for concept in primary_concepts],
        context=ConceptPipelineContext(form_registry=forms),
    )
    if not isinstance(primary_result.output, ConceptCheckedRegistry):
        detail = "; ".join(
            diagnostic.message for diagnostic in primary_result.diagnostics
        )
        raise ValueError(f"primary concept validation failed: {detail}")
    registry = dict(primary_result.output.condition_registry)

    concepts_doc = load_source_concepts_document(repo, source_name)
    if concepts_doc is not None:
        for entry in concepts_doc.concepts:
            canonical_name = entry.proposed_name or entry.local_name
            if not isinstance(canonical_name, str) or not canonical_name:
                continue
            form = forms.get(entry.form) if entry.form is not None else None
            if form is None:
                continue
            form_parameters = entry.form_parameters
            info = ConceptInfo(
                id=(
                    f"ps:source:{normalize_source_slug(source_name)}:"
                    f"concept:{canonical_name}"
                ),
                canonical_name=canonical_name,
                kind=form.kind,
                category_values=(
                    list(form_parameters.values)
                    if form.kind is KindType.CATEGORY
                    and form_parameters is not None
                    and form_parameters.values is not None
                    else []
                ),
                category_extensible=(
                    form_parameters.extensible
                    if form.kind is KindType.CATEGORY
                    and form_parameters is not None
                    and form_parameters.extensible is not None
                    else True
                ),
            )
            for name in (entry.proposed_name, entry.local_name):
                if isinstance(name, str) and name and name not in registry:
                    registry[name] = info

    if not registry:
        return registry
    for claim in data.claims:
        if not claim.conditions:
            continue
        label = claim.source_local_id or claim.id or "<unnamed>"
        for condition in claim.conditions:
            errors = check_cel_expression(condition, registry)
            if errors:
                detail = "; ".join(str(error) for error in errors)
                raise ValueError(
                    f"claim {label!r} has an invalid CEL condition "
                    f"{condition!r}: {detail}"
                )
    return registry


def _form_bearing_concept_for_claim(claim: SourceClaimDocument) -> str | None:
    """Return the concept handle whose form bounds apply to this claim's values."""

    claim_type = claim.type.value if claim.type is not None else None
    if claim_type == "parameter":
        return (
            claim.concept if isinstance(claim.concept, str) and claim.concept else None
        )
    if claim_type == "measurement":
        return (
            claim.target_concept
            if isinstance(claim.target_concept, str) and claim.target_concept
            else None
        )
    return None


def _forms_by_name(repo: Repository) -> dict[str, FormDefinition]:
    forms: dict[str, FormDefinition] = {}
    for handle in repo.families.form.iter_handles():
        form = handle.document
        if isinstance(form, FormDefinition):
            forms[form.name] = form
    return forms


def _master_concept_form_names(repo: Repository) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for handle in repo.families.concept.iter_handles():
        concept = handle.document
        if not isinstance(concept, Concept):
            continue
        form_name = _concept_form_name(concept)
        if form_name is not None:
            mapping[concept.canonical_name] = form_name
    return mapping


def _source_concept_form_names(repo: Repository, source_name: str) -> dict[str, str]:
    concepts_doc = load_source_concepts_document(repo, source_name)
    if concepts_doc is None:
        return {}
    mapping: dict[str, str] = {}
    for entry in concepts_doc.concepts:
        if not isinstance(entry.form, str) or not entry.form:
            continue
        for handle in (entry.proposed_name, entry.local_name):
            if isinstance(handle, str) and handle:
                mapping[handle] = entry.form
    return mapping


def normalize_source_claims_payload(
    data: SourceClaimsDocument,
    *,
    source_uri: str,
    source_namespace: str,
) -> tuple[SourceClaimsDocument, dict[str, str]]:
    """Stamp canonical identity onto every claim; return the normalized doc.

    Each claim gets a content-stable logical value, a derived ``artifact_id``
    (``ps:claim:<sha>``) and ``version_id`` (``sha256:<hex>``), and a logical id
    in the source's own namespace. The reserved-namespace guard runs on that
    namespace. Returns the normalized document plus a source-local-id ->
    stable-value map for downstream reference lowering.
    """

    namespace = normalize_source_slug(source_namespace)
    assert_namespace_not_reserved(namespace, context="source claims namespace")

    normalized_claims: list[SourceClaimDocument] = []
    local_to_canonical: dict[str, str] = {}
    for claim in data.claims:
        raw_local_id = claim.source_local_id or claim.id
        stable_value = stable_claim_logical_value(claim, source_uri=source_uri)
        logical_ids: list[ClaimLogicalIdDocument] = [
            ClaimLogicalIdDocument(namespace=namespace, value=stable_value)
        ]
        if isinstance(raw_local_id, str) and raw_local_id:
            local_to_canonical[raw_local_id] = stable_value
            local_value = normalize_logical_value(raw_local_id)
            if local_value != stable_value:
                logical_ids.append(
                    ClaimLogicalIdDocument(namespace=namespace, value=local_value)
                )
        else:
            raw_local_id = None
        normalized = msgspec.structs.replace(
            claim,
            id=stable_value,
            source_local_id=raw_local_id,
            artifact_code=None,
            logical_ids=tuple(logical_ids),
            artifact_id=derive_claim_artifact_id(namespace, stable_value),
            version_id=None,
        )
        normalized_claims.append(
            msgspec.structs.replace(
                normalized,
                version_id=compute_claim_version_id(normalized),
            )
        )

    return (
        SourceClaimsDocument(
            claims=tuple(normalized_claims),
            source=data.source,
            produced_by=data.produced_by,
        ),
        local_to_canonical,
    )


def validate_source_claims(
    repo: Repository, source_name: str, data: SourceClaimsDocument
) -> None:
    """Validate source claims against references, CEL, and Claim form semantics."""

    validate_source_claim_concepts(repo, source_name, data)
    concept_infos = validate_source_claim_cel_expressions(repo, source_name, data)
    forms = _forms_by_name(repo)
    master_concept_forms = _master_concept_form_names(repo)
    source_concept_forms = _source_concept_form_names(repo, source_name)
    for claim in data.claims:
        concept_handle = _form_bearing_concept_for_claim(claim)
        if concept_handle is None:
            continue
        form_name = master_concept_forms.get(
            concept_handle
        ) or source_concept_forms.get(concept_handle)
        if form_name is None:
            continue
        form = forms.get(form_name)
        if form is None:
            continue
        problems = validate_claim_value_fields(
            value=claim.value,
            lower_bound=claim.lower_bound,
            upper_bound=claim.upper_bound,
            form=form,
            concept_info=concept_infos.get(concept_handle),
        )
        if problems:
            label = claim.source_local_id or claim.id or "<unnamed>"
            detail = "; ".join(problem.message for problem in problems)
            raise ValueError(f"claim {label!r} {detail} (concept {concept_handle!r})")


def commit_source_claims_batch(
    repo: Repository,
    source_name: str,
    claims_file: Path,
    *,
    reader: str | None = None,
    method: str | None = None,
    default_context: str | None = None,
) -> str:
    """Ingest a claims-batch YAML onto a source branch; return commit sha.

    When ``default_context`` is provided, every claim whose ``context`` is unset
    is stamped with it (an inline ``context:`` always wins).
    """

    source_doc = load_source_document(repo, source_name)
    raw = decode_document_path(claims_file, SourceClaimsDocument)
    if default_context is not None:
        if not default_context:
            raise ValueError("default_context must be a non-empty string")
        injected: list[SourceClaimDocument] = []
        for claim in raw.claims:
            if claim.context:
                injected.append(claim)
                continue
            injected.append(msgspec.structs.replace(claim, context=default_context))
        raw = msgspec.structs.replace(raw, claims=tuple(injected))
    if reader is not None:
        raw = msgspec.structs.replace(
            raw,
            produced_by=ExtractionProvenanceDocument(
                reader=reader,
                method=method,
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        )
    validate_source_claims(repo, source_name, raw)
    normalized, _ = normalize_source_claims_payload(
        raw,
        source_uri=source_doc.id or source_tag_uri(repo, source_name),
        source_namespace=normalize_source_slug(source_name),
    )
    return repo.families.source_claims.save(
        SourceRef(source_name),
        normalized,
        message=f"Write claims for {normalize_source_slug(source_name)}",
    )


def commit_source_claim_proposal(
    repo: Repository,
    source_name: str,
    *,
    claim_id: str,
    claim_type: ClaimType,
    context: str,
    statement: str | None = None,
    concept: str | None = None,
    value: ScalarValue | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
    unit: str | None = None,
    concepts: tuple[str, ...] = (),
    conditions: tuple[str, ...] = (),
    notes: str | None = None,
    uncertainty: float | None = None,
    uncertainty_type: str | None = None,
    page: int | None = None,
    section: str | None = None,
    quote_fragment: str | None = None,
    table: str | None = None,
    figure: str | None = None,
) -> SourceClaimDocument:
    """Propose one claim onto a source branch (compare-and-swap retry).

    Replaces any existing claim sharing ``claim_id`` (by source-local handle).
    Returns the normalized claim as stored.
    """

    normalized_claim_type = coerce_claim_type(claim_type)
    source_doc = load_source_document(repo, source_name)
    paper = normalize_source_slug(source_name)
    last_normalized: SourceClaimsDocument | None = None

    provenance: SourceProvenanceDocument | None = None
    if any(item is not None for item in (page, section, quote_fragment, table, figure)):
        provenance = SourceProvenanceDocument(
            paper=paper,
            page=page,
            section=section,
            quote_fragment=quote_fragment,
            table=table,
            figure=figure,
        )

    new_claim = SourceClaimDocument(
        id=claim_id,
        type=normalized_claim_type,
        context=context,
        statement=statement,
        concept=concept,
        concepts=concepts,
        conditions=conditions,
        value=value,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        unit=unit,
        notes=notes,
        uncertainty=uncertainty,
        uncertainty_type=uncertainty_type,
        provenance=provenance,
    )

    for attempt in range(8):
        expected_head = current_source_branch_head(repo, source_name)
        existing = load_source_claims_document(
            repo, source_name
        ) or SourceClaimsDocument(source=ClaimSourceDocument(paper=paper), claims=())
        kept: list[SourceClaimDocument] = []
        for claim in existing.claims:
            if claim.source_local_id == claim_id or claim.id == claim_id:
                continue
            kept.append(_restore_authored_claim(claim))
        kept.append(new_claim)
        data = SourceClaimsDocument(
            source=existing.source or ClaimSourceDocument(paper=paper),
            claims=tuple(kept),
        )
        validate_source_claims(repo, source_name, data)
        normalized, _ = normalize_source_claims_payload(
            data,
            source_uri=source_doc.id or source_tag_uri(repo, source_name),
            source_namespace=paper,
        )
        try:
            repo.families.source_claims.save(
                SourceRef(source_name),
                normalized,
                message=f"Propose claim for {paper}",
                expected_head=expected_head,
            )
        except ValueError as exc:
            if attempt == 7 or not is_stale_branch_error(exc):
                raise
            continue
        last_normalized = normalized
        break

    if last_normalized is not None:
        for entry in last_normalized.claims:
            if entry.source_local_id == claim_id:
                return entry
        return last_normalized.claims[-1]
    raise ValueError(f"could not write claim proposal {claim_id!r}")


def _restore_authored_claim(claim: SourceClaimDocument) -> SourceClaimDocument:
    """Strip derived identity from a stored claim, restoring its authored form.

    The source-local handle is moved back to ``id`` so re-normalizing the batch
    re-derives a stable identity rather than chaining off the previous one.
    """

    return msgspec.structs.replace(
        claim,
        id=claim.source_local_id or claim.id,
        source_local_id=None,
        logical_ids=(),
        artifact_id=None,
        version_id=None,
    )
