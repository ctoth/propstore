from __future__ import annotations

import copy
from collections import Counter
from itertools import product
from typing import Any, cast

from propstore.families.registry import (
    CONCEPT_ALIGNMENT_FAMILY,
    CONCEPT_FILE_FAMILY,
    ConceptAlignmentRef,
    ConceptFileRef,
)
from propstore.families.identity.concepts import normalize_canonical_concept_payload
from propstore.families.concepts.documents import ConceptDocument
from propstore.repository import Repository
from quire.documents import convert_document_value
from argumentation.partial_af import PartialArgumentationFramework
from argumentation.partial_af import credulously_accepted_arguments, skeptically_accepted_arguments
from propstore.families.documents.source_alignment import (
    AlignmentArgumentDocument,
    AlignmentDecisionDocument,
    AlignmentFrameworkDocument,
    AlignmentQueriesDocument,
    ConceptAlignmentArtifactDocument,
)
from propstore.core.lemon import (
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
    lexical_entry_identity_key,
    lexical_form_identity_key,
)
from propstore.uri import DEFAULT_URI_AUTHORITY, concept_tag_uri, source_tag_uri

from .common import load_document_from_branch, load_source_document
from propstore.families.documents.sources import SourceConceptsDocument


def alignment_slug(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value.strip().lower())
    cleaned = cleaned.strip("_-")
    return cleaned or "alignment"


def concept_proposal_branch(repo: Repository | None = None) -> str:
    return CONCEPT_ALIGNMENT_FAMILY.address_for(
        cast(Repository, object()) if repo is None else repo,
        ConceptAlignmentRef("placeholder"),
    ).branch


def _proposal_lexical_entry(proposal: dict[str, Any]) -> LexicalEntry:
    proposed_name = str(proposal["proposed_name"])
    proposed_uri = str(
        proposal.get("proposed_uri")
        or concept_tag_uri(proposed_name, authority=DEFAULT_URI_AUTHORITY)
    )
    return LexicalEntry(
        identifier=str(proposal["local_handle"]),
        canonical_form=LexicalForm(written_rep=proposed_name, language="und"),
        senses=(LexicalSense(reference=OntologyReference(uri=proposed_uri)),),
        physical_dimension_form=str(proposal["form"]),
    )


def classify_relation(left: dict[str, Any], right: dict[str, Any]) -> str:
    left_entry = _proposal_lexical_entry(left)
    right_entry = _proposal_lexical_entry(right)
    if lexical_entry_identity_key(left_entry) == lexical_entry_identity_key(right_entry):
        return "attack" if left["definition"] != right["definition"] else "non_attack"
    if lexical_form_identity_key(left_entry) == lexical_form_identity_key(right_entry):
        return "attack" if left["definition"] != right["definition"] else "non_attack"
    if left_entry.references == right_entry.references:
        return "non_attack"
    return "non_attack"


def build_alignment_artifact(
    proposals: list[dict[str, Any]],
    *,
    authority: str = DEFAULT_URI_AUTHORITY,
) -> ConceptAlignmentArtifactDocument:
    enriched: list[dict[str, Any]] = []
    id_counts: Counter[str] = Counter()
    for proposal in proposals:
        local_handle = str(proposal["local_handle"])
        base_id = f"alt_{alignment_slug(local_handle)}"
        id_counts[base_id] += 1
        arg_id = base_id if id_counts[base_id] == 1 else f"{base_id}_{id_counts[base_id]}"
        enriched.append(
            {
                "id": arg_id,
                "source": proposal["source"],
                "local_handle": local_handle,
                "proposed_name": proposal["proposed_name"],
                "proposed_uri": concept_tag_uri(proposal["proposed_name"], authority=authority),
                "definition": proposal["definition"],
                "form": proposal["form"],
            }
        )

    if not enriched:
        raise ValueError("Need at least one proposal")

    cluster_seed = enriched[0]["proposed_name"]
    cluster_id = f"align:{alignment_slug(cluster_seed)}"
    arguments = [argument["id"] for argument in enriched]
    attacks: list[tuple[str, str]] = []
    ignorance: list[tuple[str, str]] = []
    non_attacks: list[tuple[str, str]] = []

    by_id = {argument["id"]: argument for argument in enriched}
    for attacker, target in product(arguments, arguments):
        if attacker == target:
            non_attacks.append((attacker, target))
            continue
        relation = classify_relation(by_id[attacker], by_id[target])
        if relation == "attack":
            attacks.append((attacker, target))
        elif relation == "ignorance":
            ignorance.append((attacker, target))
        else:
            non_attacks.append((attacker, target))

    paf = PartialArgumentationFramework(
        arguments=frozenset(arguments),
        attacks=frozenset(attacks),
        ignorance=frozenset(ignorance),
        non_attacks=frozenset(non_attacks),
    )
    skeptical = sorted(skeptically_accepted_arguments(paf))
    credulous = sorted(credulously_accepted_arguments(paf))
    operator_scores = {
        operator: {argument: int(argument in credulous) for argument in arguments}
        for operator in ("sum", "max", "leximax")
    }

    return ConceptAlignmentArtifactDocument(
        kind="concept_alignment_framework",
        id=cluster_id,
        sources=tuple(str(argument["source"]) for argument in enriched),
        arguments=tuple(
            AlignmentArgumentDocument(
                id=str(argument["id"]),
                source=str(argument["source"]),
                local_handle=str(argument["local_handle"]),
                proposed_name=str(argument["proposed_name"]),
                proposed_uri=str(argument["proposed_uri"]),
                definition=str(argument["definition"]),
                form=str(argument["form"]),
            )
            for argument in enriched
        ),
        framework=AlignmentFrameworkDocument(
            attacks=tuple(attacks),
            ignorance=tuple(ignorance),
            non_attacks=tuple(non_attacks),
        ),
        queries=AlignmentQueriesDocument(
            skeptical_acceptance=tuple(skeptical),
            credulous_acceptance=tuple(credulous),
            operator_scores=operator_scores,
        ),
        decision=AlignmentDecisionDocument(
            status="open",
            accepted=(),
            rejected=(),
            promoted_concept=None,
        ),
    )


def align_sources(
    repo: Repository,
    source_branches: list[str],
) -> ConceptAlignmentArtifactDocument:
    proposals: list[dict[str, Any]] = []
    for branch in source_branches:
        concepts_doc = load_document_from_branch(repo, branch, "concepts.yaml", SourceConceptsDocument)
        branch_source_name = branch.split("/", 1)[1] if "/" in branch else branch
        source_doc = load_source_document(repo, branch_source_name)
        source_uri = str(source_doc.id or source_tag_uri(branch_source_name, authority=repo.uri_authority))
        for entry in (() if concepts_doc is None else concepts_doc.concepts):
            proposals.append(
                {
                    "source": source_uri,
                    "local_handle": str(entry.local_name or entry.proposed_name or "concept"),
                    "proposed_name": str(entry.proposed_name or entry.local_name or "concept"),
                    "definition": str(entry.definition or ""),
                    "form": str(entry.form or "structural"),
                }
            )
    artifact = build_alignment_artifact(proposals, authority=repo.uri_authority)
    repo.snapshot.ensure_branch(concept_proposal_branch(repo))
    slug = artifact.id.split(":", 1)[1]
    repo.families.concept_alignments.save(
        ConceptAlignmentRef(slug),
        artifact,
        message=f"Align concepts for {slug}",
    )
    return artifact


def load_alignment_artifact(
    repo: Repository,
    cluster_id: str,
) -> tuple[str, ConceptAlignmentArtifactDocument]:
    slug = cluster_id.split(":", 1)[1] if ":" in cluster_id else cluster_id
    artifact = repo.families.concept_alignments.load(ConceptAlignmentRef(slug))
    if artifact is None:
        raise FileNotFoundError(cluster_id)
    return slug, artifact


def save_alignment_artifact(
    repo: Repository,
    slug: str,
    artifact: ConceptAlignmentArtifactDocument,
    *,
    message: str,
) -> str:
    return repo.families.concept_alignments.save(
        ConceptAlignmentRef(slug),
        artifact,
        message=message,
    )


def decide_alignment(
    repo: Repository,
    cluster_id: str,
    *,
    accept: list[str],
    reject: list[str],
) -> ConceptAlignmentArtifactDocument:
    slug, artifact = load_alignment_artifact(repo, cluster_id)
    updated = copy.deepcopy(artifact)
    updated.decision = AlignmentDecisionDocument(
        status="decided",
        accepted=tuple(accept),
        rejected=tuple(reject),
        promoted_concept=artifact.decision.promoted_concept,
    )
    save_alignment_artifact(repo, slug, updated, message=f"Decide concept alignment {cluster_id}")
    return updated


def promote_alignment(
    repo: Repository,
    cluster_id: str,
) -> ConceptAlignmentArtifactDocument:
    slug, artifact = load_alignment_artifact(repo, cluster_id)
    accepted = list(artifact.decision.accepted)
    if not accepted:
        raise ValueError(f"No accepted alternatives recorded for {cluster_id}")
    accepted_id = accepted[0]
    selected = None
    for argument in artifact.arguments:
        if argument.id == accepted_id:
            selected = argument
            break
    if selected is None:
        raise ValueError(f"Accepted alternative {accepted_id!r} not found")

    canonical_name = selected.proposed_name
    local_handle = alignment_slug(canonical_name)
    concept_doc = normalize_canonical_concept_payload(
        {
            "canonical_name": canonical_name,
            "status": "accepted",
            "definition": selected.definition,
            "domain": "source",
            "form": selected.form or "structural",
        },
        local_handle=local_handle,
    )
    concept_ref = ConceptFileRef(local_handle)
    document = convert_document_value(
        concept_doc,
        ConceptDocument,
        source=repo.families.concepts.family.address_for(repo, concept_ref).require_path(),
    )
    repo.families.concepts.save(
        concept_ref,
        document,
        message=f"Promote concept alignment {cluster_id}",
    )
    repo.snapshot.sync_worktree()
    updated = copy.deepcopy(artifact)
    updated.decision = AlignmentDecisionDocument(
        status="promoted",
        accepted=artifact.decision.accepted,
        rejected=artifact.decision.rejected,
        promoted_concept=concept_tag_uri(local_handle, authority=repo.uri_authority),
    )
    save_alignment_artifact(repo, slug, updated, message=f"Record concept promotion {cluster_id}")
    return updated
