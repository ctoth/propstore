"""Concept alignment math — vocabulary reconciliation by lemon identity.

When several sources each propose a concept, this module decides how the proposals
relate and packages them into a :class:`~propstore.families.alignment.ConceptAlignmentArtifact`.
Two disciplines from CLAUDE.md govern it:

* **Identity, never string tokens.** :func:`classify_relation` decides whether two
  proposals conflict by comparing their lemon *identity keys*
  (:func:`~propstore.core.lemon.lexical_entry_identity_key`,
  :func:`~propstore.core.lemon.lexical_form_identity_key`) and their
  :class:`~propstore.core.lemon.OntologyReference` references — never by Jaccard /
  token / difflib similarity. Two proposals are the "same word" only when their
  lemon identity coincides.
* **Proposal, never mutation.** :func:`build_alignment_artifact` produces an
  artifact (heuristic layer); it never writes a source concept. The decision to
  accept/reject/promote is a separate, explicit, later step (Phase 8).

The argumentation comes from the substrate directly: candidate proposals are the
arguments of an :class:`argumentation.frameworks.partial_af.PartialArgumentationFramework`,
and acceptance is the package's own skeptical/credulous computation — there is no
propstore mirror of the framework.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from itertools import product
from pathlib import Path

from argumentation.frameworks.partial_af import (
    PartialArgumentationFramework,
    credulously_accepted_arguments,
    skeptically_accepted_arguments,
)
import msgspec
from doxa import Opinion

from propstore.core.lemon import (
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
    lexical_entry_identity_key,
    lexical_form_identity_key,
)
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
from propstore.repository import Repository
from propstore.source.common import (
    load_source_concepts_document,
    load_source_document,
    normalize_source_slug,
)
from propstore.uri import DEFAULT_URI_AUTHORITY, concept_tag_uri
from propstore.uri_authority import TaggingAuthority

_OPERATORS = ("sum", "max", "leximax")
_VACUOUS_UNCERTAINTY = 0.99


def alignment_slug(value: str) -> str:
    """Reduce ``value`` to a stable slug for alignment ids (alnum, ``_-``)."""

    cleaned = "".join(
        ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value.strip().lower()
    )
    cleaned = cleaned.strip("_-")
    return cleaned or "alignment"


def _proposal_field(proposal: object, key: str) -> object:
    """Read one field from a proposal mapping as ``object``.

    Proposals arrive as a genuinely untyped dict / JSON surface (LLM output).
    This is the one narrowing point that reads a named field without committing
    to element types; every value it yields is immediately narrowed by
    ``str(...)`` or ``isinstance`` at the call site, so no ``Any`` escapes into
    the module.
    """

    getter = getattr(proposal, "get", None)
    if callable(getter):
        return getter(key)
    return None


def _is_mapping(value: object) -> bool:
    return isinstance(value, Mapping)


def _entry_from_fields(
    *,
    local_handle: str,
    proposed_name: str,
    proposed_uri: str,
    form: str,
) -> LexicalEntry:
    """Build the lemon entry whose identity keys decide proposal sameness."""

    return LexicalEntry(
        identifier=local_handle,
        canonical_form=LexicalForm(written_rep=proposed_name, language="und"),
        senses=(LexicalSense(reference=OntologyReference(uri=proposed_uri)),),
        physical_dimension_form=form,
    )


def _proposal_lexical_entry(proposal: object) -> LexicalEntry:
    proposed_name = str(_proposal_field(proposal, "proposed_name"))
    proposed_uri_value = _proposal_field(proposal, "proposed_uri")
    proposed_uri = (
        str(proposed_uri_value)
        if proposed_uri_value
        else concept_tag_uri(proposed_name, authority=DEFAULT_URI_AUTHORITY)
    )
    return _entry_from_fields(
        local_handle=str(_proposal_field(proposal, "local_handle")),
        proposed_name=proposed_name,
        proposed_uri=proposed_uri,
        form=str(_proposal_field(proposal, "form")),
    )


def _classify_entries(
    left_entry: LexicalEntry,
    right_entry: LexicalEntry,
    *,
    definitions_match: bool,
) -> str:
    """Decide ``attack`` / ``non_attack`` from lemon identity coincidence.

    Two proposals that share a lemon identity (entry key, form key, or the same
    ontology references) are the *same word*: they conflict (``attack``) only when
    their definitions disagree, otherwise they corroborate (``non_attack``). When
    no identity coincides the proposals are about different words and never attack.
    """

    same_word = (
        lexical_entry_identity_key(left_entry) == lexical_entry_identity_key(right_entry)
        or lexical_form_identity_key(left_entry) == lexical_form_identity_key(right_entry)
        or left_entry.references == right_entry.references
    )
    if not same_word:
        return "non_attack"
    return "non_attack" if definitions_match else "attack"


def classify_relation(
    left: Mapping[str, object],
    right: Mapping[str, object] | None = None,
) -> str:
    """Classify a proposal pair as ``attack`` / ``non_attack`` / ``ignorance``.

    Two call shapes: ``classify_relation(left, right)`` compares two proposals
    directly; ``classify_relation(relation)`` reads ``relation['left']`` /
    ``relation['right']`` and an optional ``relation['opinion']``. A vacuous opinion
    (Jøsang 2001, p.8 — ``uncertainty > 0.99``) means the heuristic does not know,
    and the pair is honestly recorded as ``ignorance`` rather than forced into a
    verdict.
    """

    left_proposal: object = left
    right_proposal: object = right
    relation_opinion: Opinion | None = None
    if right is None:
        left_proposal = _proposal_field(left, "left")
        right_proposal = _proposal_field(left, "right")
        if not _is_mapping(left_proposal) or not _is_mapping(right_proposal):
            raise TypeError(
                "alignment relation must contain mapping left/right proposals"
            )
        opinion_value = _proposal_field(left, "opinion")
        if isinstance(opinion_value, Opinion):
            relation_opinion = opinion_value

    if relation_opinion is not None and relation_opinion.uncertainty > _VACUOUS_UNCERTAINTY:
        return "ignorance"

    return _classify_entries(
        _proposal_lexical_entry(left_proposal),
        _proposal_lexical_entry(right_proposal),
        definitions_match=(
            _proposal_field(left_proposal, "definition")
            == _proposal_field(right_proposal, "definition")
        ),
    )


def _classify_arguments(left: AlignmentArgument, right: AlignmentArgument) -> str:
    return _classify_entries(
        _entry_from_fields(
            local_handle=left.local_handle,
            proposed_name=left.proposed_name,
            proposed_uri=left.proposed_uri,
            form=left.form,
        ),
        _entry_from_fields(
            local_handle=right.local_handle,
            proposed_name=right.proposed_name,
            proposed_uri=right.proposed_uri,
            form=right.form,
        ),
        definitions_match=left.definition == right.definition,
    )


def build_alignment_artifact(
    proposals: Sequence[Mapping[str, object]],
    *,
    authority: str | TaggingAuthority = DEFAULT_URI_AUTHORITY,
) -> ConceptAlignmentArtifact:
    """Build a PAF-backed alignment proposal over candidate concept proposals.

    Each proposal becomes one argument; every ordered pair is classified by lemon
    identity into the framework's attack / ignorance / non-attack partition; and the
    substrate's skeptical/credulous acceptance is recorded. No proposal is dropped
    and no source is mutated — the artifact holds every rival candidate.
    """

    arguments: list[AlignmentArgument] = []
    id_counts: Counter[str] = Counter()
    for proposal in proposals:
        local_handle = str(_proposal_field(proposal, "local_handle"))
        base_id = f"alt_{alignment_slug(local_handle)}"
        id_counts[base_id] += 1
        arg_id = base_id if id_counts[base_id] == 1 else f"{base_id}_{id_counts[base_id]}"
        proposed_name = str(_proposal_field(proposal, "proposed_name"))
        arguments.append(
            AlignmentArgument(
                id=arg_id,
                source=str(_proposal_field(proposal, "source")),
                local_handle=local_handle,
                proposed_name=proposed_name,
                proposed_uri=concept_tag_uri(proposed_name, authority=authority),
                definition=str(_proposal_field(proposal, "definition")),
                form=str(_proposal_field(proposal, "form")),
            )
        )

    if not arguments:
        raise ValueError("Need at least one proposal")

    cluster_id = f"align:{alignment_slug(arguments[0].proposed_name)}"
    arg_ids = [argument.id for argument in arguments]
    by_id = {argument.id: argument for argument in arguments}

    attacks: list[tuple[str, str]] = []
    ignorance: list[tuple[str, str]] = []
    non_attacks: list[tuple[str, str]] = []
    for attacker, target in product(arg_ids, arg_ids):
        if attacker == target:
            non_attacks.append((attacker, target))
            continue
        relation = _classify_arguments(by_id[attacker], by_id[target])
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

    return ConceptAlignmentArtifact(
        alignment_id=cluster_id,
        kind="concept_alignment_framework",
        sources=tuple(argument.source for argument in arguments),
        arguments=tuple(arguments),
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


def save_alignment_artifact(artifact: ConceptAlignmentArtifact, path: Path) -> None:
    """Serialize an alignment artifact to ``path`` via its charter codec."""

    codec = ConceptAlignmentArtifact.__charter__.document_codec()
    path.write_bytes(codec.encode(artifact))


def load_alignment_artifact(path: Path) -> ConceptAlignmentArtifact:
    """Load an alignment artifact from ``path`` via its charter codec."""

    codec = ConceptAlignmentArtifact.__charter__.document_codec()
    return codec.decode(
        path.read_bytes(), ConceptAlignmentArtifact, source=str(path)
    )


# ---------------------------------------------------------------------------
# Repository-bound alignment lifecycle (propose / decide / promote)
# ---------------------------------------------------------------------------
#
# This is the propose→decide→promote workflow of CLAUDE.md layer 3. None of these
# functions mutate the canonical corpus by *proposing*: ``align_sources`` records a
# proposal artifact on the ``proposal/concepts`` branch only; ``decide_alignment``
# records an accept/reject decision on that same artifact. The single point where a
# heuristic output becomes (proposed) canonical source content is
# ``promote_alignment`` — and only for an explicitly accepted alternative.


def concept_proposal_branch(repo: Repository | None = None) -> str:
    """Return the branch every concept-alignment proposal is stored on.

    ``repo`` is accepted (and ignored) so callers can pass their repository
    uniformly; the branch is fixed by the alignment family placement, not by repo
    state. Raises if the placement is somehow not fixed-branch.
    """

    branch = CONCEPT_ALIGNMENT_BRANCH.fixed_branch
    if branch is None:
        raise ValueError("concept alignment branch placement must be fixed")
    return branch


def _alignment_slug(cluster_id: str) -> str:
    """Reduce a ``align:<slug>`` cluster id to its storage slug."""

    return cluster_id.split(":", 1)[1] if ":" in cluster_id else cluster_id


def _form_exists(repo: Repository, form: str | None) -> bool:
    """Whether *form* names a form already on the canonical (master) corpus."""

    if not form:
        return False
    return any(str(ref) == form for ref in repo.families.form.iter_refs())


def _load_repo_alignment(
    repo: Repository, cluster_id: str
) -> tuple[str, ConceptAlignmentArtifact]:
    """Load a stored alignment proposal by cluster id; raise if absent."""

    slug = _alignment_slug(cluster_id)
    artifact = repo.families.concept_alignments.load(ConceptAlignmentRef(slug))
    if artifact is None:
        raise FileNotFoundError(cluster_id)
    if not isinstance(artifact, ConceptAlignmentArtifact):  # pragma: no cover - typing
        raise TypeError(f"alignment {cluster_id!r} is not a ConceptAlignmentArtifact")
    return slug, artifact


def align_sources(
    repo: Repository, source_branches: list[str]
) -> ConceptAlignmentArtifact:
    """Propose a concept alignment across several source branches.

    Reads each source branch's proposed concepts, classifies every candidate pair
    by lemon identity (:func:`build_alignment_artifact`), and records the resulting
    proposal artifact on the proposal branch. No source concept is written; the
    artifact holds every rival candidate with its skeptical/credulous verdicts.
    """

    proposals: list[Mapping[str, object]] = []
    for branch in source_branches:
        name = branch.split("/", 1)[1] if "/" in branch else branch
        concepts_doc = load_source_concepts_document(repo, name)
        source_doc = load_source_document(repo, name)
        source_uri = str(source_doc.id or name)
        entries = () if concepts_doc is None else concepts_doc.concepts
        for entry in entries:
            proposals.append(
                {
                    "source": source_uri,
                    "local_handle": str(
                        entry.local_name or entry.proposed_name or "concept"
                    ),
                    "proposed_name": str(
                        entry.proposed_name or entry.local_name or "concept"
                    ),
                    "definition": str(entry.definition or ""),
                    "form": str(entry.form or "structural"),
                }
            )

    artifact = build_alignment_artifact(proposals, authority=repo.uri_authority)
    git = repo.require_git()
    proposal_branch = concept_proposal_branch(repo)
    if git.branch_sha(proposal_branch) is None:
        git.create_branch(proposal_branch)
    slug = _alignment_slug(artifact.alignment_id)
    repo.families.concept_alignments.save(
        ConceptAlignmentRef(slug),
        artifact,
        message=f"Align concepts for {slug}",
    )
    return artifact


def decide_alignment(
    repo: Repository,
    cluster_id: str,
    *,
    accept: list[str],
    reject: list[str],
) -> ConceptAlignmentArtifact:
    """Record an accept/reject decision over an alignment proposal.

    A decision is itself a non-committal annotation: it marks which alternatives a
    later promotion is allowed to canonicalize, without writing any source concept.
    """

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


def promote_alignment(repo: Repository, cluster_id: str) -> ConceptAlignmentArtifact:
    """Promote an accepted alignment alternative into a canonical concept.

    This is the one proposal→source boundary for alignment: the first accepted
    alternative becomes a canonical :class:`~propstore.families.concepts.Concept`
    authored to the primary branch, and the artifact's decision is stamped
    ``promoted`` with the resulting concept URI. Raises if nothing was accepted.
    """

    slug, artifact = _load_repo_alignment(repo, cluster_id)
    accepted = list(artifact.decision.accepted)
    if not accepted:
        raise ValueError(f"No accepted alternatives recorded for {cluster_id}")
    accepted_id = accepted[0]
    selected = next(
        (argument for argument in artifact.arguments if argument.id == accepted_id),
        None,
    )
    if selected is None:
        raise ValueError(f"Accepted alternative {accepted_id!r} not found")

    canonical_name = selected.proposed_name
    handle = normalize_source_slug(canonical_name)
    concept_id = derive_concept_artifact_id(handle)
    # Only carry the dimensional form onto the canonical concept when it already
    # resolves to a master form. A proposed form that has no canonical counterpart
    # is left absent (None) rather than written as a dangling foreign key — honest
    # absence over a fabricated reference (CLAUDE.md non-commitment + the FK gate).
    proposed_form = selected.form or None
    form = proposed_form if _form_exists(repo, proposed_form) else None
    concept = Concept(
        concept_id=concept_id,
        canonical_name=canonical_name,
        status=ConceptStatus.AUTHORED,
        definition=selected.definition or None,
        lexical_entry=LexicalEntry(
            identifier=handle,
            canonical_form=LexicalForm(written_rep=canonical_name, language="und"),
            senses=(
                LexicalSense(
                    reference=OntologyReference(
                        uri=concept_tag_uri(
                            canonical_name, authority=repo.uri_authority
                        )
                    )
                ),
            ),
            physical_dimension_form=form,
        ),
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
