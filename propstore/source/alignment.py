"""Typed concept alignment over pinned repository-import snapshots.

The alignment owner reads canonical :class:`Concept` documents through Quire's
pinned family API.  Import provenance comes from the import commit's typed git
note, never from branch spelling.  Arguments retain both repository identities
and both commit boundaries, and relation classification uses ontology identity
only: matching names do not merge or attack independently authored concepts.
"""

from __future__ import annotations

from collections.abc import Sequence
import hashlib
from itertools import product
from pathlib import Path

from argumentation.frameworks.partial_af import (
    PartialArgumentationFramework,
    credulously_accepted_arguments,
    skeptically_accepted_arguments,
)
from doxa import Opinion
import msgspec

from propstore.core.lemon import LexicalEntry
from propstore.families.alignment import (
    AlignmentArgument,
    AlignmentDecision,
    AlignmentFramework,
    AlignmentQueries,
    CONCEPT_ALIGNMENT_BRANCH,
    ConceptAlignmentArtifact,
    ConceptAlignmentRef,
)
from propstore.families.concepts import Concept, ConceptStatus
from propstore.families.identity.concepts import derive_concept_artifact_id
from propstore.provenance import ProvenanceStatus, read_provenance_note
from propstore.repository import Repository
from propstore.source.common import normalize_source_slug
from propstore.source.stages import AlignRepositorySnapshotsRequest
from propstore.uri import concept_tag_uri


_OPERATORS = ("sum", "max", "leximax")
_VACUOUS_UNCERTAINTY = 0.99


def _ontology_uris(argument: AlignmentArgument) -> frozenset[str]:
    uris: set[str] = set()
    if argument.ontology_reference is not None:
        uris.add(argument.ontology_reference.uri)
    if argument.lexical_entry is not None:
        uris.update(reference.uri for reference in argument.lexical_entry.references)
    return frozenset(uris)


def classify_relation(
    left: AlignmentArgument,
    right: AlignmentArgument,
    *,
    opinion: Opinion | None = None,
) -> str:
    """Classify two typed arguments by shared ontology identity.

    A vacuous opinion records ignorance.  Otherwise only a shared ontology URI
    can make two arguments refer to the same entity; conflicting definitions for
    that entity attack.  Canonical names and lexical tokens never establish
    identity.
    """

    if opinion is not None and opinion.uncertainty > _VACUOUS_UNCERTAINTY:
        return "ignorance"
    shared_ontology = _ontology_uris(left) & _ontology_uris(right)
    if not shared_ontology:
        return "non_attack"
    return "non_attack" if left.definition == right.definition else "attack"


def build_alignment_artifact(
    arguments: Sequence[AlignmentArgument],
) -> ConceptAlignmentArtifact:
    """Build one deterministic open PAF proposal from typed arguments."""

    ordered = tuple(
        sorted(
            arguments,
            key=lambda argument: (
                argument.repository_origin,
                argument.source_commit,
                argument.import_branch,
                argument.import_commit,
                argument.concept_id,
                argument.id,
            ),
        )
    )
    if not ordered:
        raise ValueError("Need at least one alignment argument")
    arg_ids = tuple(argument.id for argument in ordered)
    if len(set(arg_ids)) != len(arg_ids):
        raise ValueError("Alignment argument ids must be unique")
    by_id = {argument.id: argument for argument in ordered}

    attacks: list[tuple[str, str]] = []
    ignorance: list[tuple[str, str]] = []
    non_attacks: list[tuple[str, str]] = []
    for attacker, target in product(arg_ids, arg_ids):
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
        arguments=frozenset(arg_ids),
        attacks=frozenset(attacks),
        ignorance=frozenset(ignorance),
        non_attacks=frozenset(non_attacks),
    )
    skeptical = tuple(sorted(skeptically_accepted_arguments(paf)))
    credulous = tuple(sorted(credulously_accepted_arguments(paf)))
    credulous_set = set(credulous)
    operator_scores = {
        operator: {arg_id: int(arg_id in credulous_set) for arg_id in arg_ids}
        for operator in _OPERATORS
    }
    alignment_digest = hashlib.sha256("\0".join(arg_ids).encode("utf-8")).hexdigest()

    return ConceptAlignmentArtifact(
        alignment_id=f"align:{alignment_digest}",
        sources=tuple(sorted({argument.repository_origin for argument in ordered})),
        arguments=ordered,
        framework=AlignmentFramework(
            attacks=tuple(attacks),
            ignorance=tuple(ignorance),
            non_attacks=tuple(non_attacks),
        ),
        queries=AlignmentQueries(
            skeptical_acceptance=skeptical,
            credulous_acceptance=credulous,
            operator_scores=operator_scores,
        ),
        decision=AlignmentDecision(),
    )


def concept_proposal_branch(repo: Repository | None = None) -> str:
    """Return the fixed branch that owns concept-alignment proposals."""

    del repo
    branch = CONCEPT_ALIGNMENT_BRANCH.fixed_branch
    if branch is None:
        raise ValueError("concept alignment branch placement must be fixed")
    return branch


def _alignment_slug(cluster_id: str) -> str:
    return cluster_id.split(":", 1)[1] if ":" in cluster_id else cluster_id


def align_repository_snapshots(
    repo: Repository,
    request: AlignRepositorySnapshotsRequest,
) -> ConceptAlignmentArtifact:
    """Pin imported branches, align their typed concepts, and save one proposal."""

    branches = tuple(sorted(set(request.import_branches)))
    if len(branches) < 2:
        raise ValueError("Repository snapshot alignment requires at least two branches")

    git = repo.require_git()
    arguments: list[AlignmentArgument] = []
    for import_branch in branches:
        import_commit = git.branch_sha(import_branch)
        if import_commit is None:
            raise FileNotFoundError(import_branch)
        provenance = read_provenance_note(git.raw_repo, import_commit)
        if provenance is None:
            raise ValueError(f"Import branch {import_branch!r} has no provenance note")
        if provenance.status is not ProvenanceStatus.STATED:
            raise ValueError(f"Import branch {import_branch!r} is not STATED")
        if provenance.operations != ("repository-import",):
            raise ValueError(
                f"Import branch {import_branch!r} is not a repository import"
            )
        if len(provenance.derived_from) != 1 or not provenance.witnesses:
            raise ValueError(
                f"Import branch {import_branch!r} has incomplete import provenance"
            )
        source_commit = provenance.derived_from[0]
        repository_origin = provenance.witnesses[0].source_artifact_code

        pinned_concepts = repo.families.concept.pin(
            branch=import_branch,
            commit=import_commit,
        )
        handles = sorted(pinned_concepts.iter_handles(), key=lambda item: str(item.ref))
        for handle in handles:
            concept_value = handle.document
            if not isinstance(concept_value, Concept):
                raise TypeError(f"Imported concept {handle.ref!s} is not a Concept")
            concept = concept_value
            argument_digest = hashlib.sha256(
                "\0".join(
                    (
                        repository_origin,
                        source_commit,
                        import_branch,
                        import_commit,
                        concept.concept_id,
                    )
                ).encode("utf-8")
            ).hexdigest()
            arguments.append(
                AlignmentArgument(
                    id=f"arg:{argument_digest}",
                    repository_origin=repository_origin,
                    source_commit=source_commit,
                    import_branch=import_branch,
                    import_commit=import_commit,
                    concept_id=concept.concept_id,
                    canonical_name=concept.canonical_name,
                    ontology_reference=concept.ontology_reference,
                    lexical_entry=concept.lexical_entry,
                    definition=concept.definition,
                    form=(
                        None
                        if concept.lexical_entry is None
                        else concept.lexical_entry.physical_dimension_form
                    ),
                )
            )

    artifact = build_alignment_artifact(arguments)
    proposal_branch = concept_proposal_branch(repo)
    if git.branch_sha(proposal_branch) is None:
        git.create_branch(proposal_branch)
    slug = _alignment_slug(artifact.alignment_id)
    repo.families.concept_alignments.save(
        ConceptAlignmentRef(slug),
        artifact,
        message=f"Align imported repository snapshots {slug}",
    )
    return artifact


def save_alignment_artifact(artifact: ConceptAlignmentArtifact, path: Path) -> None:
    """Serialize an alignment artifact through its charter codec."""

    path.write_bytes(ConceptAlignmentArtifact.__charter__.document_codec().encode(artifact))


def load_alignment_artifact(path: Path) -> ConceptAlignmentArtifact:
    """Load an alignment artifact through its charter codec."""

    return ConceptAlignmentArtifact.__charter__.document_codec().decode(
        path.read_bytes(), ConceptAlignmentArtifact, source=str(path)
    )


def _load_repo_alignment(
    repo: Repository, cluster_id: str
) -> tuple[str, ConceptAlignmentArtifact]:
    slug = _alignment_slug(cluster_id)
    artifact = repo.families.concept_alignments.load(ConceptAlignmentRef(slug))
    if artifact is None:
        raise FileNotFoundError(cluster_id)
    if not isinstance(artifact, ConceptAlignmentArtifact):
        raise TypeError(f"alignment {cluster_id!r} is not a ConceptAlignmentArtifact")
    return slug, artifact


def decide_alignment(
    repo: Repository,
    cluster_id: str,
    *,
    accept: list[str],
    reject: list[str],
) -> ConceptAlignmentArtifact:
    """Record an explicit decision over a durable alignment proposal."""

    slug, artifact = _load_repo_alignment(repo, cluster_id)
    decided = msgspec.structs.replace(
        artifact,
        decision=AlignmentDecision(
            status="decided",
            accepted=tuple(accept),
            rejected=tuple(reject),
            promoted_concept=artifact.decision.promoted_concept,
        ),
    )
    repo.families.concept_alignments.save(
        ConceptAlignmentRef(slug),
        decided,
        message=f"Decide concept alignment {cluster_id}",
    )
    return decided


def _form_exists(repo: Repository, form: str | None) -> bool:
    if form is None:
        return False
    return any(str(ref) == form for ref in repo.families.form.iter_refs())


def promote_alignment(repo: Repository, cluster_id: str) -> ConceptAlignmentArtifact:
    """Promote one explicitly accepted typed alternative."""

    slug, artifact = _load_repo_alignment(repo, cluster_id)
    if not artifact.decision.accepted:
        raise ValueError(f"No accepted alternatives recorded for {cluster_id}")
    accepted_id = artifact.decision.accepted[0]
    selected = next(
        (argument for argument in artifact.arguments if argument.id == accepted_id),
        None,
    )
    if selected is None:
        raise ValueError(f"Accepted alternative {accepted_id!r} not found")

    handle = normalize_source_slug(selected.canonical_name)
    concept_id = derive_concept_artifact_id(handle)
    lexical_entry: LexicalEntry | None = selected.lexical_entry
    if (
        lexical_entry is not None
        and lexical_entry.physical_dimension_form is not None
        and not _form_exists(repo, lexical_entry.physical_dimension_form)
    ):
        lexical_entry = msgspec.structs.replace(
            lexical_entry,
            physical_dimension_form=None,
        )
    concept = Concept(
        concept_id=concept_id,
        canonical_name=selected.canonical_name,
        status=ConceptStatus.AUTHORED,
        definition=selected.definition,
        ontology_reference=selected.ontology_reference,
        lexical_entry=lexical_entry,
    )
    repo.families.concept.save(
        concept_id,
        concept,
        message=f"Promote concept alignment {cluster_id}",
    )

    promoted = msgspec.structs.replace(
        artifact,
        decision=AlignmentDecision(
            status="promoted",
            accepted=artifact.decision.accepted,
            rejected=artifact.decision.rejected,
            promoted_concept=concept_tag_uri(handle, authority=repo.uri_authority),
        ),
    )
    repo.families.concept_alignments.save(
        ConceptAlignmentRef(slug),
        promoted,
        message=f"Record concept promotion {cluster_id}",
    )
    return promoted
