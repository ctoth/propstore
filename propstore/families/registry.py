"""The propstore family registry — derived from charter annotations.

This module assembles the one :class:`~quire.families.FamilyRegistry` for the
store. Crucially, it is **charter-derived**: the family set, the foreign-key
graph, the placements, the identity fields, and the reference Ref types all fall
out of the ``@charter``-decorated document classes in this package. There is no
hand-authored ``FamilyDefinition`` table and — per PLAN.md §12.6 — no
``ForeignKeySpec`` literal lives outside a charter field annotation. The
foreign-key graph is lifted from each charter field's
``charter_field(foreign_key=...)`` declaration by
:func:`quire.charters.registry_from_charters`.

To add a family: author its ``@charter`` class and add it to
:data:`_CHARTER_MODELS`. To add a cross-family reference: annotate the
referencing field with a :class:`~quire.references.ForeignKeySpec`. Both flow
into the registry automatically; nothing here enumerates fields or edges by hand.
"""

from __future__ import annotations

from enum import StrEnum

from quire.charters import FamilyCharter, registry_from_charters
from quire.families import FamilyDefinition, FamilyRegistry
from quire.references import ForeignKeySpec
from quire.versions import VersionId

from propstore.families.alignment import ConceptAlignmentArtifact
from propstore.families.claims import Claim
from propstore.families.concepts import Concept
from propstore.families.conflicts import ConflictProjection
from propstore.families.contexts import Context, LiftingMaterialization, LiftingRule
from propstore.families.diagnostics import BuildDiagnostic
from propstore.families.forms import FormDefinition
from propstore.families.justifications import Justification
from propstore.families.micropublications import Micropublication
from propstore.families.predicates import Predicate, PredicateProposal
from propstore.families.relations import Stance, StanceProposal
from propstore.families.rules import DefeasibleRule, RuleSuperiority
from propstore.families.sameas import SameAs
from propstore.families.sources import (
    SourceClaimsDocument,
    SourceConceptsDocument,
    SourceDocument,
    SourceFinalizeReportDocument,
    SourceJustificationsDocument,
    SourceMicropublicationsDocument,
    SourceStancesDocument,
)

# Re-exported here so the source subsystem can use ``propstore.families.registry``
# as the one import site for source-branch refs and placement (matching the
# canonical-source/claim/etc. refs that also live with the registry).
from propstore.families.sources import SOURCE_BRANCH as SOURCE_BRANCH
from propstore.families.sources import SourceRef as SourceRef

PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION = VersionId(
    "2026.06.29", allow_placeholder=False
)
"""Wire-contract version of the assembled registry (stamped into bootstrap)."""

# The charter-bearing document classes, in authoring order. The registry's
# family set is exactly these charters; their ordering here is cosmetic — import
# order is derived from the foreign-key graph (see semantic_import_families).
_CHARTER_MODELS = (
    Concept,
    Claim,
    Context,
    LiftingRule,
    LiftingMaterialization,
    FormDefinition,
    Predicate,
    Stance,
    DefeasibleRule,
    RuleSuperiority,
    SameAs,
    ConceptAlignmentArtifact,
    PredicateProposal,
    StanceProposal,
    Justification,
    Micropublication,
    SourceDocument,
    SourceConceptsDocument,
    SourceClaimsDocument,
    SourceStancesDocument,
    SourceJustificationsDocument,
    SourceMicropublicationsDocument,
    SourceFinalizeReportDocument,
    # Derived-only projection families (never authored; populated by the build).
    ConflictProjection,
    BuildDiagnostic,
)

_CHARTERS: tuple[FamilyCharter, ...] = tuple(
    model.__charter__ for model in _CHARTER_MODELS
)

PROPSTORE_FAMILY_REGISTRY: FamilyRegistry[object, object] = registry_from_charters(
    *_CHARTERS,
    name="propstore",
    contract_version=PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION,
)
"""The one charter-derived family registry. ``.bind(owner, store)`` for access."""


class PropstoreFamily(StrEnum):
    """Stable identity for each canonical family the build pipeline projects.

    The members' *values* are exactly the quire family/table names derived from
    the ``@charter`` classes (singular: ``concept``, ``claim``, …). This enum is
    the typed handle the semantic-pass framework and diagnostics group work by;
    it is not a second source of truth for the family set. A drift test
    (``tests/test_semantic_passes.py``) asserts the member values equal the
    registry's family names, so adding a charter without adding a member here
    fails loudly rather than silently desyncing.
    """

    CONCEPT = "concept"
    CLAIM = "claim"
    CONTEXT = "context"
    LIFTING_RULE = "lifting_rule"
    LIFTING_MATERIALIZATION = "lifting_materialization"
    FORM = "form"
    PREDICATE = "predicate"
    STANCE = "stance"
    DEFEASIBLE_RULE = "defeasible_rule"
    RULE_SUPERIORITY = "rule_superiority"
    SAME_AS_ASSERTION = "same_as_assertion"
    CONCEPT_ALIGNMENT_FRAMEWORK = "concept_alignment_framework"
    PROPOSAL_PREDICATES = "proposal_predicates"
    PROPOSAL_STANCES = "proposal_stances"
    JUSTIFICATION = "justification"
    MICROPUBLICATION = "micropublication"
    SOURCE_DOCUMENTS = "source_documents"
    SOURCE_CONCEPTS = "source_concepts"
    SOURCE_CLAIMS = "source_claims"
    SOURCE_STANCES = "source_stances"
    SOURCE_JUSTIFICATIONS = "source_justifications"
    SOURCE_MICROPUBS = "source_micropubs"
    SOURCE_FINALIZE_REPORTS = "source_finalize_reports"
    CONFLICT = "conflict"
    BUILD_DIAGNOSTIC = "build_diagnostic"


def registered_family_names() -> tuple[str, ...]:
    """Every family name in the assembled registry, in declaration order."""

    return tuple(charter.family.name for charter in _CHARTERS)


def registered_charters() -> tuple[FamilyCharter, ...]:
    """Every charter the registry was assembled from, in declaration order."""

    return _CHARTERS


def _is_semantic(charter: FamilyCharter) -> bool:
    """A family is semantic when its charter carries a ``semantic`` tag.

    The ``@charter(semantic=...)`` argument marks the authored-knowledge
    families (concepts, claims, contexts, …). Source/proposal/sidecar families
    omit it; they are present in the registry but excluded from the semantic
    selectors below.
    """

    return bool(charter.semantic_metadata.get("semantic"))


def _family_metadata_flag(charter: FamilyCharter, key: str, *, default: bool) -> bool:
    """Read a boolean override from the family-level metadata, or ``default``."""

    metadata = charter.family.metadata
    if metadata is None or key not in metadata:
        return default
    return bool(metadata[key])


def semantic_charters() -> tuple[FamilyCharter, ...]:
    """The charters of every semantic family."""

    return tuple(charter for charter in _CHARTERS if _is_semantic(charter))


def semantic_families() -> tuple[FamilyDefinition[object, object, object, object], ...]:
    """The :class:`FamilyDefinition` of every semantic family."""

    return tuple(charter.family for charter in semantic_charters())


def semantic_family_names() -> tuple[str, ...]:
    """The names of every semantic family."""

    return tuple(charter.family.name for charter in semantic_charters())


def semantic_foreign_keys() -> tuple[ForeignKeySpec, ...]:
    """Every foreign-key spec owned by a semantic family, sorted by spec name.

    These are the lifted, charter-derived specs as the registry sees them — not
    a separate literal table.
    """

    specs = [
        spec
        for name in semantic_family_names()
        for spec in PROPSTORE_FAMILY_REGISTRY.by_name(name).foreign_keys
    ]
    return tuple(sorted(specs, key=lambda spec: spec.name))


def semantic_init_roots() -> tuple[str, ...]:
    """Storage roots to initialize / clean-materialize for semantic families.

    A semantic family may opt out with ``family_metadata={"init_directory":
    False}``; the default is to initialize a directory.
    """

    roots: list[str] = []
    for charter in semantic_charters():
        if not _family_metadata_flag(charter, "init_directory", default=True):
            continue
        roots.append(charter.family.storage_root())
    return tuple(dict.fromkeys(roots))


def semantic_import_families() -> (
    tuple[FamilyDefinition[object, object, object, object], ...]
):
    """Importable semantic families in foreign-key dependency order.

    The order is derived from the charter foreign-key graph: a family is placed
    after every family it references (so an import never resolves a reference to
    a not-yet-imported target). Ties and any residual reference cycle are broken
    by family name for determinism. A semantic family may opt out of import with
    ``family_metadata={"importable": False}``.
    """

    importable = [
        charter
        for charter in semantic_charters()
        if _family_metadata_flag(charter, "importable", default=True)
    ]
    return tuple(charter.family for charter in _foreign_key_topo_order(importable))


def _foreign_key_topo_order(charters: list[FamilyCharter]) -> list[FamilyCharter]:
    by_name = {charter.family.name: charter for charter in charters}
    names = set(by_name)
    prerequisites: dict[str, set[str]] = {}
    for charter in charters:
        targets = {
            spec.target_family
            for spec in PROPSTORE_FAMILY_REGISTRY.by_name(
                charter.family.name
            ).foreign_keys
            if spec.target_family in names and spec.target_family != charter.family.name
        }
        prerequisites[charter.family.name] = targets

    ordered: list[str] = []
    placed: set[str] = set()
    remaining = set(by_name)
    while remaining:
        ready = sorted(
            name for name in remaining if prerequisites[name] <= placed
        )
        if not ready:
            # Residual cycle: break it deterministically by name so the order is
            # still total and stable.
            ready = [min(remaining)]
        for name in ready:
            ordered.append(name)
            placed.add(name)
            remaining.discard(name)
    return [by_name[name] for name in ordered]
