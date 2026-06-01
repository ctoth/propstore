"""Grounded-rule typed persistence and query contract.

This module persists the four gunray answer sections
(``yes`` / ``no`` / ``undecided`` / ``unknown``)
from a :class:`propstore.grounding.bundle.GroundedRulesBundle` into
the sidecar's Quire SQLAlchemy store. The grounding inputs are persisted with
explicit JSON payloads rather than Python object pickles because the
sidecar is a durable boundary, not an in-process cache.

The typed persistence functions are colocated with the rules family because
grounded facts are the derived read model for authored rule artifacts.

Non-commitment discipline anchor (project CLAUDE.md): storage never
silently collapses a grounded classification. All four section keys are always
present in the read result, even when the bundle is empty. The
primary key ``(predicate, arguments, section)`` lets a single ground
atom appear under multiple sections simultaneously when an upstream
answer surface does so, and the storage layer must not silently dedupe
it away.

Theoretical anchors:

    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - Section 3 (Definition 7, p.3): a Datalog program's fact base is
      a finite set of ground atoms keyed by predicate id. The
      grounded-fact table stores one row per ground atom per section;
      argument tuples are JSON-encoded into a single ``TEXT`` column
      so SQLite's primary-key mechanism can enforce set semantics
      across variable-arity atoms.
    - Section 3 (Definition 9): grounding is a deterministic function
      of the program and its fact base. The round-trip property
      loading after persisting a bundle must return the same sections
      hold for every bundle — that is the determinism pin for this
      persistence layer.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic
    Programming: An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3 (pp.3-4): the canonical DeLP example is
      ``bird(tweety) ∈ Facts`` with the defeasible rule
      ``flies(X) -< bird(X)``; grounding produces
      ``yes = {bird: {(tweety,)}, flies: {(tweety,)}}``. The
      persistence layer must round-trip that structure byte-for-byte.
    - Section 4 (p.25): the four-valued answer system
      ``{YES, NO, UNDECIDED, UNKNOWN}`` maps onto the four section
      names. All four sections are always returned by
      :func:`load_grounded_sections`, even when some are empty, because
      storage is forbidden from collapsing a grounded classification.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, Annotated, Any, Literal

import gunray
import msgspec
from argumentation.aspic import Scalar
from argumentation.aspic import GroundAtom as AspicGroundAtom
from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import FamilyCharter, FamilyModel
from quire.lifecycle import ConflictPolicy, FamilyState, FamilyTransition
from quire.sqlalchemy_store import DerivedSession
from quire.versions import VersionId
from sqlalchemy import select

# Garcia & Simari 2004 §4 (p.25): the four-valued answer system. The
# tuple order is the deterministic iteration order used when persisting
# grounded facts so row insertion is reproducible.
_SECTION_NAMES: tuple[str, ...] = (
    "yes",
    "no",
    "undecided",
    "unknown",
)

AUTHORED_RULES_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
_WORLD_CONTRACT_VERSION = VersionId("2026.05.20", allow_placeholder=False)


RuleKind = Literal["strict", "defeasible", "proper_defeater", "blocking_defeater"]
BodyLiteralKind = Literal["positive", "default_negated"]
TermKind = Literal["var", "const"]


if TYPE_CHECKING:
    # ``@charter`` generates these SQLAlchemy-mappable models at runtime (via
    # ``model_name=``) and binds them into this module's namespace; the static
    # stubs let this module and external importers type-check model construction
    # and attribute access while the runtime classes replace them.
    class AuthoredRule(FamilyModel): ...

    class RuleSuperiority(FamilyModel): ...

    class AuthoredRuleProposal(FamilyModel): ...

    class GroundedFact(FamilyModel): ...

    class GroundedFactEmptyPredicate(FamilyModel): ...

    class GroundedBundleInput(FamilyModel): ...


class TermDocument(CharterDoc, kw_only=True):
    kind: TermKind
    name: str | None = None
    value: str | int | float | bool | None = None


class AtomDocument(CharterDoc, kw_only=True):
    predicate: str
    terms: tuple[TermDocument, ...] = ()
    negated: bool = False


class BodyLiteralDocument(CharterDoc, kw_only=True):
    kind: BodyLiteralKind
    atom: AtomDocument


class RuleSourceDocument(CharterDoc, kw_only=True):
    paper: str


class RuleExtractionProvenance(CharterDoc, kw_only=True):
    operations: tuple[str, ...]
    agent: str
    model: str
    prompt_sha: str
    notes_sha: str
    predicates_sha: str
    status: str


@charter(
    key="authored_rule",
    name="authored_rule",
    contract_version=AUTHORED_RULES_FAMILY_CONTRACT_VERSION,
    placement=".derived/authored_rule",
    identity_field="id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-authored_rule",
    model_name="AuthoredRule",
)
class RuleDocument(CharterDoc, kw_only=True):
    id: Annotated[str, charter_field(primary_key=True)]
    kind: RuleKind
    head: Annotated[AtomDocument, charter_field(column_name="head_atom", json=True)]
    body: Annotated[
        tuple[BodyLiteralDocument, ...],
        charter_field(column_name="body_literals", json=True, default_sql="'[]'"),
    ] = ()
    strength: Annotated[str, charter_field(default_sql="''")] = ""
    source: Annotated[RuleSourceDocument | None, charter_field(json=True)] = None
    provenance: Annotated[dict[str, Any] | None, charter_field(json=True)] = None
    authoring_group: str | None = None
    promoted_from_sha: str | None = None


@charter(
    key="rule_superiority",
    name="rule_superiority",
    contract_version=AUTHORED_RULES_FAMILY_CONTRACT_VERSION,
    placement=".derived/rule_superiority",
    identity_field="superior_rule_id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-rule_superiority",
    model_name="RuleSuperiority",
)
class RuleSuperiorityDocument(CharterDoc, kw_only=True):
    superior_rule_id: Annotated[str, charter_field(primary_key=True)]
    inferior_rule_id: Annotated[str, charter_field(primary_key=True)]
    source: Annotated[RuleSourceDocument | None, charter_field(json=True)] = None
    authoring_group: str | None = None
    promoted_from_sha: str | None = None


@charter(
    key="authored_rule_proposal",
    name="authored_rule_proposal",
    contract_version=AUTHORED_RULES_FAMILY_CONTRACT_VERSION,
    placement=".derived/authored_rule_proposal",
    identity_field="rule_id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-authored_rule_proposal",
    model_name="AuthoredRuleProposal",
    states=(
        FamilyState("proposed", document_label="proposal"),
        FamilyState("canonical", document_label="canonical", terminal=True),
    ),
    transitions=(
        FamilyTransition(
            "promote_proposal",
            source="proposed",
            target="canonical",
            materializer="rule_proposal_to_canonical",
            conflict_policy=ConflictPolicy.REPLACE,
        ),
    ),
)
class AuthoredRuleProposalArtifact(CharterDoc, kw_only=True):
    source_paper: Annotated[str, charter_field(primary_key=True)]
    rule_id: Annotated[str, charter_field(primary_key=True)]
    proposed_rule: Annotated[RuleDocument, charter_field(json=True)]
    predicates_referenced: Annotated[tuple[str, ...], charter_field(json=True)]
    extraction_provenance: Annotated[RuleExtractionProvenance, charter_field(json=True)]
    extraction_date: str
    proposal_state: Annotated[str, charter_field(default_sql="'proposed'")] = "proposed"
    page_reference: str | None = None
    promoted_from_sha: str | None = None


@charter(
    key="grounded_fact",
    name="grounded_fact",
    contract_version=_WORLD_CONTRACT_VERSION,
    placement=".derived/grounded_fact",
    identity_field="predicate",
    semantic="propstore.world",
    artifact_family_name="propstore-world-grounded_fact",
    model_name="GroundedFact",
)
class Grounded_factDocument(CharterDoc):
    predicate: Annotated[str, charter_field(primary_key=True)]
    arguments: Annotated[str, charter_field(primary_key=True)]
    section: Annotated[str, charter_field(primary_key=True)]


@charter(
    key="grounded_fact_empty_predicate",
    name="grounded_fact_empty_predicate",
    contract_version=_WORLD_CONTRACT_VERSION,
    placement=".derived/grounded_fact_empty_predicate",
    identity_field="section",
    semantic="propstore.world",
    artifact_family_name="propstore-world-grounded_fact_empty_predicate",
    model_name="GroundedFactEmptyPredicate",
)
class Grounded_fact_empty_predicateDocument(CharterDoc):
    section: Annotated[str, charter_field(primary_key=True)]
    predicate: Annotated[str, charter_field(primary_key=True)]


@charter(
    key="grounded_bundle_input",
    name="grounded_bundle_input",
    contract_version=_WORLD_CONTRACT_VERSION,
    placement=".derived/grounded_bundle_input",
    identity_field="kind",
    semantic="propstore.world",
    artifact_family_name="propstore-world-grounded_bundle_input",
    model_name="GroundedBundleInput",
)
class Grounded_bundle_inputDocument(CharterDoc):
    kind: Annotated[str, charter_field(primary_key=True)]
    position: Annotated[int, charter_field(primary_key=True)]
    payload: bytes


AUTHORED_RULE_CHARTER: FamilyCharter = RuleDocument.__charter__
RULE_SUPERIORITY_CHARTER: FamilyCharter = RuleSuperiorityDocument.__charter__
AUTHORED_RULE_PROPOSAL_CHARTER: FamilyCharter = AuthoredRuleProposalArtifact.__charter__

AUTHORED_RULE_CHARTERS: tuple[FamilyCharter, ...] = (
    AUTHORED_RULE_CHARTER,
    AUTHORED_RULE_PROPOSAL_CHARTER,
    RULE_SUPERIORITY_CHARTER,
)

RULES_CHARTERS: tuple[FamilyCharter, FamilyCharter, FamilyCharter] = (
    Grounded_factDocument.__charter__,
    Grounded_fact_empty_predicateDocument.__charter__,
    Grounded_bundle_inputDocument.__charter__,
)


def persist_grounded_bundle(
    derived: DerivedSession,
    bundle: Any,
) -> int:
    """Persist every ground atom in ``bundle.sections`` through typed models.

    Iterates the four section keys in a deterministic order
    (``yes`` → ``no`` → ``undecided`` → ``unknown``). Within each section, predicates are iterated in
    sorted order and their argument tuples are iterated in a stable
    order derived by sorting on the JSON-encoded argument string, so
    the insert sequence is reproducible even though ``frozenset``
    iteration itself is unordered.

    Each object is added through SQLAlchemy without upsert behavior, so a
    duplicate materialization raises an integrity error at flush/commit. That
    guards against a careless re-materialization double-counting rows.

    Returns the total number of rows inserted, which must match the
    sum of inner-set sizes across all four sections.

    Diller, Borg, Bex 2025 §3 Definition 9: the grounder is a
    deterministic function of its inputs, so the number of persisted
    rows has to match the number of ground atoms in the bundle's
    ground model exactly — no duplicates, no drops.

    Garcia & Simari 2004 §4 (p.25): each four-valued grounded classification is
    itself a set of ground atoms; the composite primary key hardens
    that set semantics at the storage layer so duplicates within a
    grounded classification raise loudly instead of being silently coalesced.
    """
    inserted = 0
    derived.session.add_all(_grounded_bundle_input_models(bundle))
    sections = bundle.sections
    for section_name in _SECTION_NAMES:
        inner_map = sections.get(section_name)
        if inner_map is None:
            continue
        for predicate_id in sorted(inner_map.keys()):
            rows = inner_map[predicate_id]
            if not rows:
                # Predicate is mentioned in this section with zero
                # ground atoms (see Garcia & Simari 2004 §4 (p.25)
                # non-commitment discipline — an empty grounded classification is
                # still a grounded classification). Persist the presence record to
                # the companion table so the round-trip preserves
                # the predicate key. Empty-predicate markers do NOT
                # count toward the inserted total because they are
                # not ground atoms — the
                # ``test_populate_row_count_matches_section_content``
                # contract sums inner-set *sizes*, which are zero
                # for an empty frozenset.
                derived.session.add(
                    GroundedFactEmptyPredicate(
                        section=section_name,
                        predicate=predicate_id,
                    ),
                )
                continue
            # Pre-encode argument tuples so we can sort for a stable
            # insert order; ``frozenset`` iteration is unordered but
            # the determinism pin in Diller 2025 §3 Def 9 is about
            # the output set, not iteration order, so sorting the
            # JSON strings is safe and reproducible.
            encoded = sorted(json.dumps(list(arg_tuple)) for arg_tuple in rows)
            for encoded_arguments in encoded:
                derived.session.add(
                    GroundedFact(
                        predicate=predicate_id,
                        arguments=encoded_arguments,
                        section=section_name,
                    ),
                )
                inserted += 1
    return inserted


def _grounded_bundle_input_models(bundle: Any) -> tuple[GroundedBundleInput, ...]:
    rows = (
        ("source_rule", bundle.source_rules),
        ("source_superiority", bundle.source_superiority),
        ("source_fact", bundle.source_facts),
        ("argument", bundle.arguments),
    )
    return tuple(
        GroundedBundleInput(
            kind=kind,
            position=position,
            payload=_encode_bundle_input(kind, value),
        )
        for kind, values in rows
        for position, value in enumerate(values)
    )


def _load_bundle_inputs(derived: DerivedSession, kind: str) -> tuple[object, ...]:
    table = derived.schema.table("grounded_bundle_input")
    rows = derived.session.execute(
        select(GroundedBundleInput)
        .where(table.c.kind == kind)
        .order_by(table.c.position)
    ).scalars()
    return tuple(_decode_bundle_input(kind, getattr(row, "payload")) for row in rows)


def load_grounded_sections(
    derived: DerivedSession,
) -> Mapping[str, Mapping[str, frozenset[tuple[Scalar, ...]]]]:
    """Load grounded sections from typed `Grounded*` models.

    Returns an immutable mapping whose outer keys are exactly the
    four section names (always present, even when empty) and whose
    inner maps go ``predicate_id -> frozenset(arg_tuple)``. Argument
    tuples are decoded from the JSON column via ``json.loads`` and
    cast to :class:`tuple`; Python's ``json`` module preserves the
    :data:`~argumentation.aspic.Scalar` union (``str``/``int``/``float``/
    ``bool``) losslessly for the domain the Hypothesis strategy
    samples (NaN/Infinity are excluded at the strategy level so the
    round-trip is well defined).

    Garcia & Simari 2004 §4 (p.25) non-commitment discipline: all
    four section keys are always present in the read result. Storage
    never silently drops a grounded classification, so an empty bundle still yields
    four empty inner maps.

    Diller, Borg, Bex 2025 §3 Definition 9: the grounder is a
    deterministic function of its inputs, so the composition
    ``load ∘ persist`` on a fresh store must be the identity on
    the sections map. That determinism is what the round-trip
    property test pins.
    """
    result: dict[str, dict[str, set[tuple[Scalar, ...]]]] = {
        name: {} for name in _SECTION_NAMES
    }
    fact_rows = derived.session.execute(select(GroundedFact)).scalars()
    for row in fact_rows:
        section_name = getattr(row, "section")
        if section_name not in result:
            raise ValueError(f"grounded fact row has unknown section {section_name!r}")
        decoded = tuple(json.loads(getattr(row, "arguments")))
        predicate_bucket = result[section_name].setdefault(
            getattr(row, "predicate"),
            set(),
        )
        predicate_bucket.add(decoded)

    empty_rows = derived.session.execute(select(GroundedFactEmptyPredicate)).scalars()
    for row in empty_rows:
        section_name = getattr(row, "section")
        if section_name not in result:
            raise ValueError(
                f"grounded empty-predicate row has unknown section {section_name!r}"
            )
        result[section_name].setdefault(getattr(row, "predicate"), set())

    frozen: dict[str, Mapping[str, frozenset[tuple[Scalar, ...]]]] = {}
    for section_name in _SECTION_NAMES:
        inner_frozen: dict[str, frozenset[tuple[Scalar, ...]]] = {
            predicate_id: frozenset(rows)
            for predicate_id, rows in result[section_name].items()
        }
        frozen[section_name] = MappingProxyType(inner_frozen)
    return MappingProxyType(frozen)


def _encode_bundle_input(kind: str, value: object) -> bytes:
    payload = _bundle_input_payload(kind, value)
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _is_json_value(value: object) -> bool:
    if value is None or isinstance(value, str | int | float | bool):
        return True
    if isinstance(value, tuple | list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _is_json_value(item) for key, item in value.items()
        )
    return False


def _encode_gunray_atom(atom: gunray.GroundAtom) -> dict[str, object]:
    return {"predicate": atom.predicate, "arguments": list(atom.arguments)}


def _encode_gunray_rule(rule: gunray.GroundDefeasibleRule) -> dict[str, object]:
    return {
        "rule_id": rule.rule_id,
        "kind": rule.kind,
        "head": _encode_gunray_atom(rule.head),
        "body": [_encode_gunray_atom(atom) for atom in rule.body],
        "default_negated_body": [
            _encode_gunray_atom(atom) for atom in rule.default_negated_body
        ],
    }


def _rule_key(rule: gunray.GroundDefeasibleRule) -> tuple[str, str, str]:
    return (rule.rule_id, rule.kind, repr(rule.head))


def load_grounded_bundle(derived: DerivedSession) -> Any:
    """Rehydrate a runtime grounding bundle from persisted grounding inputs.

    The sidecar persists the source rule/fact inputs and the materialized
    four-status section map. Re-running the typed grounder here restores the
    Gunray inspection frame required by ASPIC projection, then verifies that
    the recomputed sections match the stored materialization.
    """

    from ...grounding.grounder import ground
    from ...grounding.predicates import PredicateRegistry

    stored_sections = load_grounded_sections(derived)
    bundle = ground(
        _load_source_rules(derived),
        _load_source_facts(derived),
        PredicateRegistry(()),
        superiority=_load_source_superiority(derived),
        return_arguments=True,
    )
    if bundle.sections != stored_sections:
        raise ValueError("persisted grounded facts diverge from grounded inputs")
    return bundle


def build_runtime_grounded_bundle(
    repo: Any,
    *,
    commit_hash: str | None = None,
) -> Any:
    """Build the runtime grounding bundle for a repository snapshot."""

    from ...grounding.loading import build_grounded_bundle

    return build_grounded_bundle(
        repo,
        commit=commit_hash,
        return_arguments=True,
    )


def _load_source_rules(derived: DerivedSession) -> tuple[RuleDocument, ...]:
    values = _load_bundle_inputs(derived, "source_rule")
    if not all(isinstance(value, RuleDocument) for value in values):
        raise TypeError("grounded source_rule inputs must be RuleDocument values")
    return tuple(value for value in values if isinstance(value, RuleDocument))


def _load_source_superiority(
    derived: DerivedSession,
) -> tuple[RuleSuperiorityDocument, ...]:
    values = _load_bundle_inputs(derived, "source_superiority")
    if not all(isinstance(value, RuleSuperiorityDocument) for value in values):
        raise TypeError(
            "grounded source_superiority inputs must be RuleSuperiorityDocument values"
        )
    return tuple(
        value for value in values if isinstance(value, RuleSuperiorityDocument)
    )


def _load_source_facts(derived: DerivedSession) -> tuple[AspicGroundAtom, ...]:
    values = _load_bundle_inputs(derived, "source_fact")
    if not all(isinstance(value, AspicGroundAtom) for value in values):
        raise TypeError("grounded source_fact inputs must be ASPIC GroundAtom values")
    return tuple(value for value in values if isinstance(value, AspicGroundAtom))
