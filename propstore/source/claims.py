from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from propstore.core.conditions.registry import ConceptInfo
from propstore.families.claims.declaration import (
    ClaimSourceDocument,
    SOURCE_CLAIM_BATCH_SPEC,
)
from propstore.families.claims.lifecycle import normalize_source_claims_payload
from propstore.families.registry import SourceRef
from propstore.families.claims.types import ClaimType
from propstore.families.documents.sources import SourceProvenanceDocument
from propstore.repository import Repository, retry_live_branch_update
from quire.documents import (
    convert_document_value,
    decode_document_batch_bytes,
    document_to_payload,
)

from .common import (
    normalize_source_slug,
    source_tag_uri,
)
from propstore.families.documents.sources import ExtractionProvenanceDocument, SourceClaimDocument


def source_concept_handles(repo: Repository, source_name: str) -> set[str]:
    handles: set[str] = set()
    concepts_doc = repo.families.source_concepts.load(SourceRef(source_name))
    if concepts_doc is None:
        return handles
    for entry in concepts_doc:
        if entry.local_name:
            handles.add(entry.local_name)
        if entry.proposed_name:
            handles.add(entry.proposed_name)
    return handles


def iter_claim_concept_refs(claim: SourceClaimDocument) -> list[str]:
    refs: list[str] = []
    for value in (claim.concept, claim.target_concept):
        if isinstance(value, str):
            refs.append(value)
    refs.extend(claim.concepts)
    variables = claim.variables
    if isinstance(variables, tuple):
        refs.extend(variable.concept for variable in variables if isinstance(variable.concept, str))
    parameters = claim.parameters
    refs.extend(parameter.concept for parameter in parameters if isinstance(parameter.concept, str))
    return refs


def validate_source_claim_concepts(repo: Repository, source_name: str, data: tuple[SourceClaimDocument, ...]) -> None:
    known_handles = source_concept_handles(repo, source_name)
    unknown: set[str] = set()
    for claim in data:
        for concept_ref in iter_claim_concept_refs(claim):
            if concept_ref.startswith("ps:concept:") or concept_ref.startswith("tag:"):
                continue
            if concept_ref not in known_handles:
                unknown.add(concept_ref)
    if unknown:
        formatted = ", ".join(sorted(unknown))
        raise ValueError(f"unknown concept reference(s): {formatted}")


def _source_branch_cel_concepts(
    repo: Repository,
    source_name: str,
) -> list["ConceptInfo"]:
    """Build synthetic ConceptInfo entries for source-branch-proposed concepts.

    Returns one entry per proposal in the source's ``concepts.yaml`` keyed by
    ``proposed_name`` (preferred) or ``local_name``. Kind is inferred from the
    proposal's ``form`` via :func:`kind_type_from_form_name`; proposals
    without a usable handle are skipped silently (they will surface during
    promote/build).
    """
    from propstore.families.forms.stages import kind_type_from_form_name

    concepts_doc = repo.families.source_concepts.load(SourceRef(source_name))
    if concepts_doc is None:
        return []
    infos: list[ConceptInfo] = []
    seen_names: set[str] = set()
    for entry in concepts_doc:
        canonical = entry.proposed_name or entry.local_name
        if not isinstance(canonical, str) or not canonical:
            continue
        if canonical in seen_names:
            continue
        kind = kind_type_from_form_name(entry.form)
        if kind is None:
            # No form declared on the source proposal: the proposal is
            # incomplete, skip rather than fabricating a kind. Promote
            # path will reject it explicitly with a better error.
            continue
        synthetic_id = f"ps:source:{source_name}:concept:{canonical}"
        infos.append(
            ConceptInfo(
                id=synthetic_id,
                canonical_name=canonical,
                kind=kind,
            )
        )
        seen_names.add(canonical)
    return infos


def validate_source_claim_cel_expressions(
    repo: Repository,
    source_name: str,
    data: tuple[SourceClaimDocument, ...],
) -> None:
    """Reject a batch whose CEL conditions reference unknown concepts.

    Runs before ``commit_source_claims_batch`` writes to the source branch, so
    a failing batch never reaches the sidecar or conflict detection. The CEL
    registry is the union of (a) master's canonical concepts (the
    authoritative source of concept kinds) and (b) the source branch's
    currently-proposed concepts. This lets ``pks source add-claim`` reference
    concepts that were just introduced via ``pks source propose-concept`` /
    ``pks source add-concepts`` on the same branch, while still honoring any
    previously-authored canonical declaration when names overlap (master
    wins, since it is layered first).
    """
    from propstore.cel_validation import (
        iter_claim_condition_expressions,
        validate_cel_expressions,
    )
    from propstore.compiler.context import build_compilation_context_from_repo
    from propstore.core.conditions.registry import (
        with_standard_synthetic_bindings,
        with_synthetic_concepts,
    )

    compilation_context = build_compilation_context_from_repo(repo)
    master_registry = compilation_context.cel_registry

    source_concepts = _source_branch_cel_concepts(repo, source_name)
    if source_concepts:
        # Master entries take precedence: with_synthetic_concepts overwrites
        # by canonical_name, so filter out any proposal whose name is
        # already in master to preserve the authored kind.
        non_overlapping = [
            info for info in source_concepts if info.canonical_name not in master_registry
        ]
        layered = with_synthetic_concepts(master_registry, non_overlapping)
        # If master was empty, the standard runtime synthetic bindings
        # ("source", "domain", ...) were never applied — apply them now
        # so source-only validation matches the master-present semantics.
        registry = (
            layered
            if master_registry
            else with_standard_synthetic_bindings(layered)
        )
    else:
        registry = dict(master_registry) if master_registry else {}

    if not registry:
        # No master concepts AND no source-branch proposals — nothing to
        # validate against. The batch may still reference unknown
        # concepts, which are type-checked at promote/build time. This is
        # the bootstrap path for a fresh repository.
        return

    paper = (
        data[0].source.paper
        if data and data[0].source is not None and data[0].source.paper
        else source_name
    )
    for claim in data:
        if not claim.conditions:
            continue
        claim_label = claim.source_local_id or claim.id or "<unnamed>"
        artifact_label = f"claim '{claim_label}' in paper '{paper}'"
        validate_cel_expressions(
            iter_claim_condition_expressions(
                [str(condition) for condition in claim.conditions],
                artifact_label=artifact_label,
            ),
            registry,
        )


def _source_branch_concept_form_map(
    repo: Repository,
    source_name: str,
) -> dict[str, str]:
    """Map source-branch-proposed concept handles → form name.

    Both ``proposed_name`` and ``local_name`` map to the same form so a
    claim can reference either spelling. Entries without a declared
    ``form`` are skipped (they fail later at promote/build).
    """
    concepts_doc = repo.families.source_concepts.load(SourceRef(source_name))
    if concepts_doc is None:
        return {}
    mapping: dict[str, str] = {}
    for entry in concepts_doc:
        if not isinstance(entry.form, str) or not entry.form:
            continue
        for handle in (entry.proposed_name, entry.local_name):
            if isinstance(handle, str) and handle:
                mapping[handle] = entry.form
    return mapping


def _form_bearing_concept_for_claim(claim: SourceClaimDocument) -> str | None:
    """Return the concept handle whose form's bounds apply to this claim's value(s).

    Source-side schema: parameter claims carry the form-bearing concept on
    ``concept`` (promote remaps to ``output_concept``). Measurement claims
    use ``target_concept``.
    """
    claim_type = claim.type.value if claim.type is not None else None
    if claim_type == "parameter":
        return claim.concept if isinstance(claim.concept, str) and claim.concept else None
    if claim_type == "measurement":
        return (
            claim.target_concept
            if isinstance(claim.target_concept, str) and claim.target_concept
            else None
        )
    return None


def _value_fields_for_claim(claim: SourceClaimDocument) -> list[tuple[str, float | int]]:
    """Numeric fields on a value-bearing claim that bounds must constrain."""
    fields: list[tuple[str, float | int]] = []
    if claim.value is not None:
        fields.append(("value", claim.value))
    if claim.lower_bound is not None:
        fields.append(("lower_bound", claim.lower_bound))
    if claim.upper_bound is not None:
        fields.append(("upper_bound", claim.upper_bound))
    return fields


def validate_source_claim_value_bounds(
    repo: Repository,
    source_name: str,
    data: tuple[SourceClaimDocument, ...],
) -> None:
    """Reject a batch whose numeric fields fall outside the form's declared bounds.

    Resolves each claim's form-bearing concept against (a) master's canonical
    concepts and (b) the source branch's currently-proposed concepts, then
    looks up the matching ``FormDefinition`` in the master form registry. If
    the form declares ``min`` or ``max``, every numeric value/lower_bound/
    upper_bound on the claim must lie within those bounds.
    """
    from propstore.compiler.context import (
        build_compilation_context_from_repo,
        concept_form_definition,
    )

    compilation_context = build_compilation_context_from_repo(repo)
    form_registry = compilation_context.form_registry
    source_form_map = _source_branch_concept_form_map(repo, source_name)

    paper = (
        data[0].source.paper
        if data and data[0].source is not None and data[0].source.paper
        else source_name
    )

    for claim in data:
        concept_handle = _form_bearing_concept_for_claim(claim)
        if concept_handle is None:
            continue
        value_fields = _value_fields_for_claim(claim)
        if not value_fields:
            continue

        # Master takes precedence: if the handle resolves on master, honor
        # the canonical form. Otherwise fall back to the source-branch
        # proposal's declared form.
        form_def = concept_form_definition(concept_handle, compilation_context)
        if form_def is None:
            proposed_form_name = source_form_map.get(concept_handle)
            if proposed_form_name is None:
                continue
            form_def = form_registry.get(proposed_form_name)
            if form_def is None:
                continue
        if form_def.min is None and form_def.max is None:
            continue

        claim_label = claim.source_local_id or claim.id or "<unnamed>"
        for field_name, raw in value_fields:
            try:
                numeric = float(raw)
            except (TypeError, ValueError):
                continue
            if form_def.min is not None and numeric < form_def.min:
                raise ValueError(
                    f"claim '{claim_label}' in paper '{paper}' "
                    f"{field_name}={numeric} is below form '{form_def.name}' "
                    f"min={form_def.min} (concept '{concept_handle}')"
                )
            if form_def.max is not None and numeric > form_def.max:
                raise ValueError(
                    f"claim '{claim_label}' in paper '{paper}' "
                    f"{field_name}={numeric} is above form '{form_def.name}' "
                    f"max={form_def.max} (concept '{concept_handle}')"
                )


def commit_source_claims_batch(
    repo: Repository,
    source_name: str,
    claims_file: Path,
    *,
    reader: str | None = None,
    method: str | None = None,
    default_context: str | None = None,
) -> str:
    """Ingest a claims-batch YAML onto a source branch.

    When ``default_context`` is provided, every claim in the batch whose
    ``context`` field is unset is stamped with that value. An inline
    ``context:`` in the YAML always wins over the default; this makes
    ``pks source add-claim --context <name>`` safe to use over batches
    produced by extraction pipelines that emit per-claim context
    overrides for some but not all entries.
    """
    from datetime import datetime, timezone

    source_doc = repo.families.source_documents.require(SourceRef(source_name))
    raw = decode_document_batch_bytes(
        claims_file.read_bytes(),
        SOURCE_CLAIM_BATCH_SPEC,
        source=str(claims_file),
    )
    if default_context is not None:
        if not isinstance(default_context, str) or not default_context:
            raise ValueError("default_context must be a non-empty string")
        injected: list[SourceClaimDocument] = []
        for index, claim in enumerate(raw, start=1):
            if claim.context is not None and claim.context != "":
                injected.append(claim)
                continue
            payload = cast(dict[str, Any], document_to_payload(claim))
            payload["context"] = default_context
            injected.append(
                convert_document_value(
                    payload,
                    SourceClaimDocument,
                    source=f"{source_name}:claims[{index}]",
                )
            )
        raw = tuple(injected)
    if reader is not None:
        produced_by = ExtractionProvenanceDocument(
            reader=reader,
            method=method,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        stamped: list[SourceClaimDocument] = []
        for claim in raw:
            payload = cast(dict[str, Any], document_to_payload(claim))
            payload["produced_by"] = document_to_payload(produced_by)
            stamped.append(convert_document_value(payload, SourceClaimDocument, source=source_name))
        raw = tuple(stamped)
    validate_source_claim_concepts(repo, source_name, raw)
    validate_source_claim_cel_expressions(repo, source_name, raw)
    validate_source_claim_value_bounds(repo, source_name, raw)
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
    statement: str | None = None,
    concept: str | None = None,
    value: float | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
    unit: str | None = None,
    context: str,
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
    branch = repo.families.source_claims.address(SourceRef(source_name)).branch
    source_doc = repo.families.source_documents.require(SourceRef(source_name))
    normalized_claim_type = ClaimType(claim_type)

    def update(expected_head: str | None) -> tuple[SourceClaimDocument, ...]:
        existing = repo.families.source_claims.load(SourceRef(source_name)) or ()
        claims = list(existing)

        norm_keys = {"source_local_id", "logical_ids", "artifact_id", "version_id"}
        restored: list[SourceClaimDocument] = []
        for claim in claims:
            if claim.source_local_id == claim_id or claim.id == claim_id:
                continue
            restored_claim = {
                key: value
                for key, value in cast(dict[str, Any], document_to_payload(claim)).items()
                if key not in norm_keys
            }
            local_id = claim.source_local_id
            if local_id:
                restored_claim["id"] = local_id
            restored.append(
                convert_document_value(
                    restored_claim,
                    SourceClaimDocument,
                    source=f"{branch}:claims proposal {claim_id}",
                )
            )
        claims = restored

        claim_payload: dict[str, object] = {
            "source": document_to_payload(
                ClaimSourceDocument(paper=normalize_source_slug(source_name))
            ),
            "id": claim_id,
            "type": normalized_claim_type.value,
            "context": context,
        }
        if statement is not None:
            claim_payload["statement"] = statement
        if concept is not None:
            claim_payload["concept"] = concept
        if concepts:
            claim_payload["concepts"] = list(concepts)
        if conditions:
            claim_payload["conditions"] = list(conditions)
        if value is not None:
            claim_payload["value"] = value
        if lower_bound is not None:
            claim_payload["lower_bound"] = lower_bound
        if upper_bound is not None:
            claim_payload["upper_bound"] = upper_bound
        if unit is not None:
            claim_payload["unit"] = unit
        if notes is not None:
            claim_payload["notes"] = notes
        if uncertainty is not None:
            claim_payload["uncertainty"] = uncertainty
        if uncertainty_type is not None:
            claim_payload["uncertainty_type"] = uncertainty_type
        if any(value is not None for value in (page, section, quote_fragment, table, figure)):
            claim_payload["provenance"] = SourceProvenanceDocument(
                paper=normalize_source_slug(source_name),
                page=page,
                section=section,
                quote_fragment=quote_fragment,
                table=table,
                figure=figure,
            )

        claims.append(
            convert_document_value(
                claim_payload,
                SourceClaimDocument,
                source=f"{branch}:claims proposal {claim_id}",
            )
        )
        data = tuple(claims)
        validate_source_claim_concepts(repo, source_name, data)
        validate_source_claim_cel_expressions(repo, source_name, data)
        validate_source_claim_value_bounds(repo, source_name, data)

        normalized, _ = normalize_source_claims_payload(
            data,
            source_uri=source_doc.id or source_tag_uri(repo, source_name),
            source_namespace=normalize_source_slug(source_name),
        )

        repo.families.source_claims.save(
            SourceRef(source_name),
            normalized,
            message=f"Propose claim for {normalize_source_slug(source_name)}",
            expected_head=expected_head,
        )
        return normalized

    normalized = retry_live_branch_update(repo, branch, update)
    for entry in normalized:
        if entry.source_local_id == claim_id:
            return entry
    return normalized[-1]
