"""World-query glue — bind / chain / intervene / observe over a ``WorldStore``.

This module holds the render-time *query behaviour* that turns a
:class:`~propstore.core.environment.WorldStore` into a bound belief space and
answers goal-directed queries over it. It is the 7a-world-C query glue, kept
deliberately separate from the concrete sidecar reader: the functions here take
the ``WorldStore`` protocol as an argument (substrate-style composition — a call,
not a conversion), so the Phase-9 repo-backed ``WorldQuery`` can satisfy the
protocol and reuse this glue unchanged rather than re-implementing it.

What lives here (7a-world-C):

* :func:`compiled_graph` / :func:`active_graph` — lower a store into the compiled
  semantic graph and activate it under an :class:`Environment`.
* :func:`bind` — build a :class:`~propstore.world.bound.BoundWorld` over a store
  and an environment (binding compilation + context lifting).
* :func:`intervene` / :func:`observe` — Pearl ``do()`` / deterministic
  observation worlds, built through the ``causal_models`` substrate package via
  :func:`propstore.world.causal.from_compiled_graph` (no ``world/scm`` mirror).
* :func:`chain_query` — backward-chaining derivation of a target concept over the
  bind + value/derived/resolved surface.

What does NOT live here:

* The concrete sqlite/sidecar reader (``WorldQuery.__init__`` / ``from_path`` /
  ``select_*`` / embeddings / diagnostics / form-algebra / grounding) — Phase 9.
  When it lands it implements the ``WorldStore`` protocol and its ``bind`` /
  ``chain_query`` / ``intervene`` / ``observe`` methods delegate straight to the
  functions here.
* The git-journal / worldline bridge (``at_journal_step``) — Phase 8
  (``support_revision``).
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from causal_models import InterventionWorld, ObservationWorld, Value
from condition_ir import ConditionSolver, to_cel_exprs, with_standard_synthetic_bindings
from quire.derived_runtime import (
    connect_sqlite_store_readonly,
    read_derived_store_schema_version,
)
from quire.sqlalchemy_store import readonly_session, validate_sqlalchemy_store

from propstore.conflict_detector.models import ConflictRecord
from propstore.core.activation import activate_compiled_world_graph
from propstore.core.active_claims import ActiveClaim
from propstore.core.environment import Environment, WorldStore
from propstore.core.graph_build import build_compiled_world_graph
from propstore.core.graph_types import (
    ActiveWorldGraph,
    CompiledWorldGraph,
    ParameterizationEdge,
    RelationEdge,
)
from propstore.core.id_types import to_concept_id
from propstore.core.labels import (
    compile_environment_assumptions,
    environment_assumption_ids,
)
from propstore.core.store_results import (
    ClaimSimilarityHit,
    ConceptSearchHit,
    ConceptSimilarityHit,
    WorldStoreStats,
)
from propstore.derived_schema import (
    WORLD_SIDECAR_SCHEMA_VERSION,
    build_world_sidecar_schema,
)
from propstore.families.claims import Claim, ClaimStatus
from propstore.families.concepts import Concept
from propstore.families.diagnostics import BuildDiagnostic
from propstore.families.forms import FormDefinition
from propstore.families.micropublications import Micropublication
from propstore.families.relations import Stance
from propstore.world.bound import BoundWorld
from propstore.world.causal import from_compiled_graph
from propstore.world.queries import (
    count_claims,
    count_concepts,
    count_conflicts,
    derive_parameterizations,
    resolve_claim_id,
    resolve_concept_id,
    search_concepts,
    select_build_diagnostics,
    select_claim,
    select_claims,
    select_concept,
    select_concepts,
    select_conflicts,
    select_contexts,
    select_forms,
    select_incident_stances,
    select_lifting_rules,
    select_micropublications,
    select_stances,
    select_stances_between,
)
from propstore.world.types import (
    ChainResult,
    ChainStep,
    ClaimView,
    DerivedResult,
    RenderPolicy,
    ResolutionStrategy,
    ValueResult,
    ValueStatus,
)

if TYPE_CHECKING:
    from quire.derived_store import DerivedStoreHandle
    from quire.sqlalchemy_schema import SqlAlchemySchema
    from quire.sqlalchemy_store import DerivedSession

    from propstore.context_lifting import LiftingSystem
    from propstore.repository import Repository
    from propstore.support_revision.history import TransitionJournal


def compiled_graph(store: WorldStore) -> CompiledWorldGraph:
    """Build the canonical compiled semantic graph from a store's charters."""

    return build_compiled_world_graph(store)


def active_graph(
    store: WorldStore,
    environment: Environment,
    *,
    lifting_system: LiftingSystem | None = None,
) -> ActiveWorldGraph:
    """Activate the store's compiled graph under ``environment``."""

    return activate_compiled_world_graph(
        compiled_graph(store),
        environment=environment,
        solver=store.condition_solver(),
        lifting_system=lifting_system,
    )


def bind(
    store: WorldStore,
    environment: Environment | None = None,
    *,
    policy: RenderPolicy | None = None,
    lifting_system: LiftingSystem | None = None,
    **conditions: str | int | float | bool,
) -> BoundWorld:
    """Bind ``store`` to an environment and return the live belief space.

    ``conditions`` are convenience keyword bindings merged into ``environment``'s
    bindings. When the environment names a context and a ``lifting_system`` is
    supplied, the context's effective assumptions are lifted into the frame
    before the binding/context assumptions are compiled.
    """

    if environment is None:
        environment = Environment(bindings=dict(conditions))
    elif conditions:
        merged = dict(environment.bindings)
        merged.update(conditions)
        environment = Environment(
            bindings=merged,
            context_id=environment.context_id,
            effective_assumptions=tuple(environment.effective_assumptions),
            assumptions=tuple(environment.assumptions),
        )

    if environment.context_id is not None and lifting_system is not None:
        environment = Environment(
            bindings=environment.bindings,
            context_id=environment.context_id,
            effective_assumptions=to_cel_exprs(
                lifting_system.effective_assumptions(str(environment.context_id))
            ),
            assumptions=tuple(environment.assumptions),
        )

    environment = Environment(
        bindings=environment.bindings,
        context_id=environment.context_id,
        effective_assumptions=tuple(environment.effective_assumptions),
        assumptions=compile_environment_assumptions(
            bindings=environment.bindings,
            effective_assumptions=environment.effective_assumptions,
            context_id=environment.context_id,
        ),
    )

    return BoundWorld(
        store,
        environment=environment,
        lifting_system=lifting_system,
        policy=policy,
        active_graph=active_graph(store, environment, lifting_system=lifting_system),
    )


def intervene(
    store: WorldStore,
    assignment: Mapping[str, Value],
    *,
    exogenous_assignment: Mapping[str, Value] | None = None,
) -> InterventionWorld:
    """Return a Pearl-style intervention world over the store's compiled graph."""

    scm = from_compiled_graph(
        compiled_graph(store),
        exogenous_assignment=exogenous_assignment,
    )
    return InterventionWorld(scm, assignment)


def observe(
    store: WorldStore,
    assignment: Mapping[str, Value],
    *,
    exogenous_assignment: Mapping[str, Value] | None = None,
) -> ObservationWorld:
    """Return a deterministic observation world over the store's compiled graph."""

    scm = from_compiled_graph(
        compiled_graph(store),
        exogenous_assignment=exogenous_assignment,
    )
    return ObservationWorld(scm, assignment)


def chain_query(
    store: WorldStore,
    target_concept_id: str,
    strategy: ResolutionStrategy | None = None,
    *,
    lifting_system: LiftingSystem | None = None,
    **bindings: str | int | float | bool,
) -> ChainResult:
    """Backward-chain over the parameter space to derive ``target_concept_id``.

    Binds the store under ``bindings``, then iterates the target's
    parameterization group, resolving each concept by direct value, then by the
    chosen resolution ``strategy`` when conflicted, then by derivation from the
    values resolved so far, until no further progress is made.
    """

    policy = RenderPolicy(strategy=strategy) if strategy is not None else None
    bound = bind(
        store,
        Environment(bindings=dict(bindings)),
        policy=policy,
        lifting_system=lifting_system,
    )
    steps: list[ChainStep] = []
    resolved_values: dict[str, float | str | None] = {}
    visited: set[str] = set()
    unresolved_conflicted: list[str] = []

    for key, value in bindings.items():
        steps.append(ChainStep(concept_id=key, value=_as_scalar(value), source="binding"))

    group = store.group_members(target_concept_id)
    if not group:
        group = [target_concept_id]

    changed = True
    while changed:
        changed = False
        for concept_id in group:
            if concept_id in visited:
                continue

            value_result = bound.value_of(concept_id)
            if value_result.status is ValueStatus.DETERMINED:
                value = (
                    _claim_scalar(value_result.claims[0])
                    if value_result.claims
                    else None
                )
                if value is not None:
                    resolved_values[concept_id] = value
                    steps.append(ChainStep(concept_id=concept_id, value=value, source="claim"))
                    visited.add(concept_id)
                    changed = True
                    continue

            if value_result.status is ValueStatus.CONFLICTED and strategy is not None:
                resolved = bound.resolved_value(concept_id)
                if resolved.status is ValueStatus.RESOLVED and resolved.value is not None:
                    resolved_values[concept_id] = resolved.value
                    steps.append(
                        ChainStep(concept_id=concept_id, value=resolved.value, source="resolved")
                    )
                    visited.add(concept_id)
                    changed = True
                    continue

            if (
                value_result.status is ValueStatus.CONFLICTED
                and concept_id not in unresolved_conflicted
            ):
                unresolved_conflicted.append(concept_id)

            derived = bound.derived_value(concept_id, override_values=resolved_values)
            if derived.status is ValueStatus.DERIVED and derived.value is not None:
                resolved_values[concept_id] = derived.value
                steps.append(ChainStep(concept_id=concept_id, value=derived.value, source="derived"))
                visited.add(concept_id)
                changed = True

    result = _target_result(bound, target_concept_id, steps, resolved_values)

    return ChainResult(
        target_concept_id=to_concept_id(target_concept_id),
        result=result,
        steps=steps,
        bindings_used=dict(bindings),
        unresolved_dependencies=[
            to_concept_id(concept_id) for concept_id in unresolved_conflicted
        ],
    )


def _target_result(
    bound: BoundWorld,
    target_concept_id: str,
    steps: list[ChainStep],
    resolved_values: Mapping[str, float | str | None],
) -> ValueResult | DerivedResult:
    if target_concept_id in resolved_values:
        target_step = next(
            (step for step in steps if step.concept_id == target_concept_id), None
        )
        if target_step is not None and target_step.source == "derived":
            return bound.derived_value(target_concept_id, override_values=resolved_values)
        return bound.value_of(target_concept_id)

    derived = bound.derived_value(target_concept_id, override_values=resolved_values)
    if derived.status is ValueStatus.DERIVED:
        return derived
    return bound.value_of(target_concept_id)


def _claim_scalar(claim: ActiveClaim) -> float | str | None:
    """The scalar value an active claim carries."""

    return _as_scalar(claim.value)


def _as_scalar(value: object) -> float | str | None:
    """Narrow a keyword binding to the scalar a :class:`ChainStep` records."""

    if value is None or isinstance(value, str):
        return value
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return float(value)
    return str(value)


# The C3 query glue, bound here as private aliases so the repo-backed reader's
# same-named methods (``bind`` / ``active_graph`` / ...) DELEGATE to the free
# functions above rather than re-implementing them (CLAUDE.md substrate boundary:
# composition is a call, not a second spelling).
_bind = bind
_active_graph = active_graph
_compiled_graph = compiled_graph
_intervene = intervene
_observe = observe
_chain_query = chain_query


def serialize_claim_atms_label(
    world: WorldQuery, claim_id: str
) -> tuple[tuple[str, ...], ...] | None:
    """Serialize a claim's ATMS label as its environments' assumption-id tuples.

    This is the world-layer half of ``pks verify``'s recompute (A8, PLAN.md §12.6):
    the artifact-code recompute itself is storage-layer and world-free
    (:func:`propstore.verify.verify_source_artifact_codes`), while the ATMS-label
    walk needs the bound belief space, so it lives here and the audit/CLI surface
    composes the two. Returns ``None`` when the claim has no label; a supported
    claim under no assumptions serializes as ``((),)``.
    """

    label = world.bind(Environment()).atms_engine().claim_label(claim_id)
    if label is None:
        return None
    return tuple(
        tuple(str(assumption_id) for assumption_id in environment_assumption_ids(environment))
        for environment in label.environments
    )


def _admits_claim(policy: RenderPolicy, claim: Claim) -> bool:
    """Whether ``claim`` is visible under ``policy`` (default hides draft/blocked).

    The lifecycle gate is a *render-time* filter, never a storage one: every claim
    is present in the sidecar; a default policy hides ``DRAFT`` / ``BLOCKED`` rows
    while ``include_drafts`` / ``include_blocked`` lift those filters (CLAUDE.md
    non-commitment — present-but-hidden, not dropped).
    """

    if claim.status is ClaimStatus.DRAFT:
        return policy.include_drafts
    if claim.status is ClaimStatus.BLOCKED:
        return policy.include_blocked
    return True


class WorldQuery(WorldStore):
    """Concrete repo-backed reader over the materialized world sidecar.

    Satisfies the :class:`~propstore.core.environment.WorldStore` protocol (it is
    declared as a subclass so pyright verifies every method) by reading the
    content-addressed sidecar that :func:`propstore.derived_build.materialize_world_sidecar`
    builds, through quire's charter-derived SQLAlchemy schema. Each ``select_*``
    (in :mod:`propstore.world.queries`) rebuilds the ONE canonical charter / value
    type for a row — there is no ``*Row`` second spelling.

    The render-time query surface — :meth:`bind`, :meth:`active_graph`,
    :meth:`compiled_graph`, :meth:`intervene`, :meth:`observe`,
    :meth:`chain_query` — DELEGATES to the C3 free functions in this module
    (passing ``self`` as the ``WorldStore``); the reader does not re-implement the
    glue.

    Honesty / non-commitment: a not-yet-built sidecar raises
    :class:`FileNotFoundError` (the cause — "run pks build" — is surfaced, never
    collapsed to an empty/zero result), and the storage methods return *every*
    row regardless of lifecycle status; the policy-aware :meth:`claims_with_policy`
    / :meth:`build_diagnostics` views are where draft/blocked/quarantine rows are
    hidden at render time.

    Each open reader holds its own charter schema and schema-local mapped classes,
    so readers over independently built sidecars can coexist safely.
    """

    @classmethod
    def from_path(cls, path: str | Path) -> WorldQuery:
        """Open a reader over the repository rooted at ``path``."""

        from propstore.repository import Repository

        return cls(Repository(Path(path)))

    def __init__(
        self,
        repo: Repository | None = None,
        *,
        derived_store: DerivedStoreHandle | None = None,
        commit: str | None = None,
    ) -> None:
        if derived_store is None:
            if repo is None:
                raise TypeError("WorldQuery requires either a repo or a derived_store")
            from propstore.derived_build import materialize_world_sidecar

            derived_store, _ = materialize_world_sidecar(repo, commit=commit)
        path = Path(derived_store.path)
        if not path.exists():
            raise FileNotFoundError(
                f"World sidecar not found at {path}. Run 'pks build' first."
            )
        self._repo = repo
        self._source_commit = commit
        self._path = path
        self._schema: SqlAlchemySchema = build_world_sidecar_schema()
        self._validate_schema()
        self._session_cm = readonly_session(path, self._schema)
        self._session: DerivedSession = self._session_cm.__enter__()
        self._solver: ConditionSolver | None = None
        self._lifting: LiftingSystem | None = None
        self._lifting_loaded = False
        self._parameterizations: tuple[ParameterizationEdge, ...] | None = None

    def __enter__(self) -> WorldQuery:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @property
    def sidecar_path(self) -> Path:
        """The materialized world-sidecar sqlite file backing this reader.

        Exposed so an embedding writer (a separate vec-enabled connection) can
        target the same content-addressed sidecar file this reader reads.
        """

        return self._path

    def close(self) -> None:
        """Close the held read session."""

        self._session_cm.__exit__(None, None, None)

    @contextmanager
    def historical_query(self, commit_sha: str) -> Iterator[WorldQuery]:
        """Open a temporary reader rebuilt from ``commit_sha``.

        The live worktree is not touched: the sidecar for ``commit_sha`` is
        materialized (built if absent, reused if already cached) and opened
        read-only for the lifetime of the context manager.
        """

        if self._repo is None:
            raise ValueError("historical_query requires a repository-backed reader")
        from propstore.derived_build import materialize_world_sidecar

        handle, _ = materialize_world_sidecar(self._repo, commit=commit_sha)
        with WorldQuery(self._repo, derived_store=handle, commit=commit_sha) as reader:
            yield reader

    def _validate_schema(self) -> None:
        try:
            validate_sqlalchemy_store(self._path, self._schema)
        except ValueError as error:
            raise ValueError(
                f"Unsupported sidecar schema: {error} Rebuild with 'pks build'."
            ) from error
        conn = connect_sqlite_store_readonly(self._path)
        try:
            version = read_derived_store_schema_version(conn, key="sidecar")
        finally:
            conn.close()
        if version != WORLD_SIDECAR_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported sidecar schema version {version}; expected "
                f"{WORLD_SIDECAR_SCHEMA_VERSION}. Rebuild with 'pks build'."
            )

    # ── concepts ─────────────────────────────────────────────────────────────

    def get_concept(self, concept_id: str) -> Concept | None:
        concept = select_concept(self._session, concept_id)
        if concept is not None:
            return concept
        resolved = self.resolve_concept(concept_id)
        if resolved is None or resolved == concept_id:
            return None
        return select_concept(self._session, resolved)

    def all_concepts(self) -> Sequence[Concept]:
        return select_concepts(self._session)

    def all_forms(self) -> Sequence[FormDefinition]:
        return select_forms(self._session)

    def resolve_alias(self, alias: str) -> str | None:
        # The charter rewrite authors no concept-alias projection, so there is no
        # alias table to consult; alias resolution is honest-empty rather than a
        # fabricated match. Name/id resolution lives in ``resolve_concept``.
        return None

    def resolve_concept(self, name: str) -> str | None:
        return resolve_concept_id(self._session, name)

    def concept_ids_for_group(self, group_id: int) -> set[str]:
        groups = self._parameterization_groups()
        if 0 <= group_id < len(groups):
            return set(groups[group_id])
        return set()

    def group_members(self, concept_id: str) -> list[str]:
        resolved = self.resolve_concept(concept_id) or concept_id
        for group in self._parameterization_groups():
            if resolved in group:
                return sorted(group)
        return []

    def search(self, query: str) -> list[ConceptSearchHit]:
        return search_concepts(self._session, query)

    # ── claims ───────────────────────────────────────────────────────────────

    def get_claim(self, claim_id: str) -> Claim | None:
        claim = select_claim(self._session, claim_id)
        if claim is not None:
            return claim
        resolved = self.resolve_claim(claim_id)
        if resolved is None or resolved == claim_id:
            return None
        return select_claim(self._session, resolved)

    def resolve_claim(self, name: str) -> str | None:
        return resolve_claim_id(self._session, name)

    def claims_for(self, concept_id: str | None) -> Sequence[Claim]:
        claims = select_claims(self._session)
        if concept_id is None:
            return claims
        resolved = self.resolve_concept(concept_id) or concept_id
        return [
            claim
            for claim in claims
            if resolved in (claim.output_concept, claim.target_concept, *claim.concepts)
        ]

    def claims_by_ids(self, claim_ids: set[str]) -> Mapping[str, Claim]:
        if not claim_ids:
            return {}
        resolved = {self.resolve_claim(claim_id) or claim_id for claim_id in claim_ids}
        return {
            str(claim.claim_id): claim
            for claim in select_claims(self._session)
            if claim.claim_id in resolved
        }

    def at_journal_step(
        self,
        journal: TransitionJournal,
        k: int,
        *,
        heavy: bool = False,
    ) -> ClaimView:
        """Project the claims accepted at step ``k`` of the journal.

        Bridge surface defined in
        ``quire/plans/worldline-journal-bridge-2026-05-02.md``. Per Bonanno
        [2007, 2010] (branching-time AGM with PLS) and Dixon [1993] (ATMS into
        AGM behavioural equivalence), this projection is behaviourally equivalent
        to running the journal's operations against the live store, modulo the
        lossy projection at the AGM boundary.

        Delegates to :func:`propstore.world.bridge.at_journal_step`; the same
        function is used by the property suite against a synthetic belief space,
        so this method's behaviour has the same shape as the property tests.
        """
        from propstore.world.bridge import at_journal_step as _at_journal_step

        return _at_journal_step(self, journal, k, heavy=heavy)

    def claims_with_policy(
        self, concept_id: str | None, policy: RenderPolicy
    ) -> list[Claim]:
        """Claims for ``concept_id`` filtered by the policy's lifecycle flags.

        The render-time counterpart of :meth:`claims_for`: every claim is present
        in storage, and this view hides ``DRAFT`` / ``BLOCKED`` rows unless the
        policy opts them in.
        """

        return [
            claim
            for claim in self.claims_for(concept_id)
            if _admits_claim(policy, claim)
        ]

    # ── stances ──────────────────────────────────────────────────────────────

    def stances_between(self, claim_ids: set[str]) -> Sequence[Stance]:
        if not claim_ids:
            return []
        resolved = {self.resolve_claim(claim_id) or claim_id for claim_id in claim_ids}
        return select_stances_between(self._session, resolved)

    def all_claim_stances(self) -> Sequence[Stance]:
        return select_stances(self._session)

    def explain(self, claim_id: str) -> Sequence[Stance]:
        resolved = self.resolve_claim(claim_id) or claim_id
        return select_incident_stances(self._session, resolved)

    # ── relations + parameterizations ────────────────────────────────────────

    def all_relationships(self) -> Sequence[RelationEdge]:
        # Concept-to-concept relations are not a stored family in the charter
        # rewrite; the world graph's relation edges come from stances. Honest
        # empty rather than a fabricated edge set.
        return []

    def _all_parameterizations(self) -> tuple[ParameterizationEdge, ...]:
        if self._parameterizations is None:
            self._parameterizations = tuple(
                derive_parameterizations(select_claims(self._session))
            )
        return self._parameterizations

    def all_parameterizations(self) -> Sequence[ParameterizationEdge]:
        return self._all_parameterizations()

    def parameterizations_for(self, concept_id: str) -> Sequence[ParameterizationEdge]:
        resolved = self.resolve_concept(concept_id) or concept_id
        return [
            edge
            for edge in self._all_parameterizations()
            if str(edge.output_concept_id) == resolved
        ]

    def _parameterization_groups(self) -> list[frozenset[str]]:
        from propstore.parameterization import build_parameterization_groups

        edges = {
            str(edge.output_concept_id): tuple(
                str(input_id) for input_id in edge.input_concept_ids
            )
            for edge in self._all_parameterizations()
        }
        components = build_parameterization_groups(edges)
        return sorted(
            (frozenset(component) for component in components),
            key=lambda component: min(component) if component else "",
        )

    # ── micropublications + conflicts ────────────────────────────────────────

    def all_micropublications(self) -> Sequence[Micropublication]:
        return select_micropublications(self._session)

    def conflicts(self) -> Sequence[ConflictRecord]:
        return select_conflicts(self._session)

    def build_diagnostics(self, policy: RenderPolicy) -> list[BuildDiagnostic]:
        """Quarantine diagnostics, surfaced only when ``policy.show_quarantined``.

        The diagnostics are always present in the sidecar; the default policy
        keeps them out of the rendered view (the "don't show problems by default"
        posture), and ``show_quarantined`` opts them in.
        """

        if not policy.show_quarantined:
            return []
        return select_build_diagnostics(self._session)

    # ── stats ────────────────────────────────────────────────────────────────

    def stats(self) -> WorldStoreStats:
        return WorldStoreStats(
            concepts=count_concepts(self._session),
            claims=count_claims(self._session),
            conflicts=count_conflicts(self._session),
        )

    # ── embedding similarity (Phase 10) ──────────────────────────────────────

    def similar_claims(
        self, claim_id: str, model_name: str | None = None, top_k: int = 10
    ) -> list[ClaimSimilarityHit]:
        """Embedding-nearest claims, with each hit's vector distance as its score.

        A heuristic signal, not truth: an absent embedding index, an unknown
        ``claim_id``, or a claim with no embedding yields ``[]`` — never a
        fabricated distance. The embedding extra (``sqlite-vec``) being absent also
        resolves to the honest-empty result.
        """

        from propstore.families.embeddings.declaration import world_similar_claims

        return world_similar_claims(
            self._path, self.claims_for(None), claim_id, model_name, top_k
        )

    def similar_concepts(
        self, concept_id: str, model_name: str | None = None, top_k: int = 10
    ) -> list[ConceptSimilarityHit]:
        """Embedding-nearest concepts (heuristic; honest-empty — see ``similar_claims``)."""

        from propstore.families.embeddings.declaration import world_similar_concepts

        return world_similar_concepts(
            self._path, self.all_concepts(), concept_id, model_name, top_k
        )

    # ── condition solving ────────────────────────────────────────────────────

    def condition_solver(self) -> ConditionSolver:
        if self._solver is None:
            from propstore.cel_registry import build_canonical_cel_registry

            form_registry = {form.name: form for form in select_forms(self._session)}
            registry = with_standard_synthetic_bindings(
                build_canonical_cel_registry(self.all_concepts(), form_registry)
            )
            self._solver = ConditionSolver(registry)
        return self._solver

    def _lifting_system(self) -> LiftingSystem | None:
        if self._lifting_loaded:
            return self._lifting
        self._lifting_loaded = True
        from propstore.context_lifting import LiftingSystem

        contexts = tuple(select_contexts(self._session))
        rules = tuple(select_lifting_rules(self._session))
        context_ids = {context.context_id for context in contexts}
        # A lifting rule whose source or target context is absent cannot lift; it
        # is excluded so the system stays consistent (the absent context is itself
        # a build-surfaced condition, not silently completed here).
        valid_rules = tuple(
            rule
            for rule in rules
            if rule.source_context in context_ids and rule.target_context in context_ids
        )
        self._lifting = (
            LiftingSystem(contexts=contexts, lifting_rules=valid_rules)
            if contexts or valid_rules
            else None
        )
        return self._lifting

    # ── render-time query glue (delegates to the C3 free functions) ───────────

    def compiled_graph(self) -> CompiledWorldGraph:
        return _compiled_graph(self)

    def active_graph(
        self,
        environment: Environment,
        *,
        lifting_system: LiftingSystem | None = None,
    ) -> ActiveWorldGraph:
        return _active_graph(
            self,
            environment,
            lifting_system=lifting_system or self._lifting_system(),
        )

    def bind(
        self,
        environment: Environment | None = None,
        *,
        policy: RenderPolicy | None = None,
        **conditions: str | int | float | bool,
    ) -> BoundWorld:
        return _bind(
            self,
            environment,
            policy=policy,
            lifting_system=self._lifting_system(),
            **conditions,
        )

    def intervene(
        self,
        assignment: Mapping[str, Value],
        *,
        exogenous_assignment: Mapping[str, Value] | None = None,
    ) -> InterventionWorld:
        return _intervene(self, assignment, exogenous_assignment=exogenous_assignment)

    def observe(
        self,
        assignment: Mapping[str, Value],
        *,
        exogenous_assignment: Mapping[str, Value] | None = None,
    ) -> ObservationWorld:
        return _observe(self, assignment, exogenous_assignment=exogenous_assignment)

    def chain_query(
        self,
        target_concept_id: str,
        strategy: ResolutionStrategy | None = None,
        **bindings: str | int | float | bool,
    ) -> ChainResult:
        return _chain_query(
            self,
            target_concept_id,
            strategy,
            lifting_system=self._lifting_system(),
            **bindings,
        )
