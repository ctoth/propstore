"""WorldQuery — read-only reasoner over a compiled sidecar."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import aliased, selectinload
from quire.derived_store import DerivedStoreHandle
from quire.sqlalchemy_store import FtsQuerySyntaxError, search_fts_index
from quire.sqlalchemy_store import validate_sqlalchemy_store
from propstore.core.conditions.registry import (
    ConceptInfo,
    KindType,
    with_standard_synthetic_bindings,
)
from propstore.cel_registry import build_store_cel_registry
from propstore.families.contexts.declaration import load_lifting_system
from propstore.core.id_types import (
    to_claim_id,
    to_concept_id,
    to_context_id,
)
from propstore.core.justifications import CanonicalJustification
from propstore.core.labels import compile_environment_assumptions
from propstore.core.relations import ClaimConceptLinkRole
from propstore.core.store_results import (
    WorldStoreStats,
    ClaimSimilarityHit,
    ConceptSearchHit,
    ConceptSimilarityHit,
)
from propstore.families.claims.declaration import (
    Claim,
    count_authored_justifications,
    select_authored_justifications,
)
from propstore.families.diagnostics.declaration import (
    build_diagnostics,
)
from propstore.families.relations.declaration import (
    ConceptRelation,
    ConflictWitness,
    Stance,
)
from propstore.families.micropublications.declaration import Micropublication
from propstore.families.concepts.declaration import (
    Concept,
    ConceptSearchQuerySyntaxError,
    Parameterization,
)
from propstore.families.world_charters import (
    PROPSTORE_WORLD_META_KEY,
    PROPSTORE_WORLD_SCHEMA_VERSION,
    world_sqlalchemy_schema,
)
from quire.tree_path import FilesystemTreePath as FilesystemKnowledgePath, TreePath as KnowledgePath
from propstore.core.conditions.solver import ConditionSolver

if TYPE_CHECKING:
    from propstore.support_revision.history import TransitionJournal
    from propstore.repository import Repository
    from propstore.world.bound import BoundWorld
    from propstore.context_lifting import LiftingSystem
from propstore.world.resolution import resolve
from propstore.world.types import (
    WorldStore,
    ClaimView,
    Environment,
    ChainResult,
    ChainStep,
    DerivedResult,
    RenderPolicy,
    ResolutionStrategy,
    ValueResult,
    ValueStatus,
)


_KIND_TYPE_MAP = {
    "category": KindType.CATEGORY,
    "boolean": KindType.BOOLEAN,
    "structural": KindType.STRUCTURAL,
    "quantity": KindType.QUANTITY,
    "timepoint": KindType.TIMEPOINT,
}

@dataclass(frozen=True)
class _BoundView:
    """Observable artifact returned by ``WorldQuery.bind_for_view``.

    Exists so ``at_journal_step(..., rebind=True)`` returns a
    ``ClaimView`` whose ``bound`` field is observably non-None and
    distinct from the flat ``rebind=False`` view. Carries the live
    ``BoundWorld`` plus the claim-id restriction set the snapshot
    implies.
    """

    bound: BoundWorld
    restricted_to: frozenset[str]


class WorldQuery(WorldStore):
    """Read-only reasoner over a compiled sidecar."""

    @classmethod
    def from_path(cls, knowledge_dir: str | Path) -> WorldQuery:
        """Open a world model from a knowledge directory path."""
        from propstore.repository import Repository

        return cls(Repository(Path(knowledge_dir)))

    def __init__(
        self,
        repo: Repository | None = None,
        *,
        derived_store: DerivedStoreHandle | None = None,
        commit: str | None = None,
    ) -> None:
        if derived_store is None:
            if repo is None:
                raise TypeError(
                    "WorldQuery requires either derived_store or repo argument"
                )
            from propstore.derived_build import materialize_world_sidecar

            derived_store, _rebuilt = materialize_world_sidecar(
                repo,
                commit_hash=commit,
            )
        if not derived_store.path.exists():
            raise FileNotFoundError(
                f"Derived store not found at {derived_store.path}. Run 'pks build' first."
            )
        self._conn = derived_store.open_readonly()
        self._conn.row_factory = sqlite3.Row
        knowledge_root: KnowledgePath = FilesystemKnowledgePath.from_filesystem_path(
            derived_store.path.parent
        )
        if repo is not None and hasattr(repo, "tree"):
            knowledge_root = repo.tree(commit=commit)
        self._repo = repo
        self._source_commit = commit
        self._derived_store = derived_store
        self._derived_store_path = derived_store.path
        self._knowledge_root = knowledge_root
        self._grounding_bundle_cache = None
        self._solver: ConditionSolver | None = None
        self._registry: dict[str, ConceptInfo] | None = None
        self._lifting_system: LiftingSystem | None = None
        self._lifting_system_loaded = False
        self._compiled_graph_cache = None
        self._active_graph_cache: dict[str, Any] = {}
        self._logical_id_indexes: dict[str, dict[str, str]] = {}
        self._validate_schema()

    def __enter__(self) -> WorldQuery:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @contextmanager
    def historical_query(self, commit_sha: str) -> Iterator[WorldQuery]:
        """Open a temporary ``WorldQuery`` rebuilt from ``commit_sha``.

        The live repository worktree is not checked out. The sidecar is built
        from the Git tree for the requested commit into a temporary directory,
        then opened read-only for the lifetime of the context manager.
        """
        if self._repo is None:
            raise ValueError(
                "WorldQuery.historical_query requires a repository-backed query"
            )
        from propstore.derived_build import materialize_world_sidecar

        handle, _rebuilt = materialize_world_sidecar(
            self._repo,
            commit_hash=commit_sha,
        )
        with WorldQuery(
            self._repo,
            derived_store=handle,
            commit=commit_sha,
        ) as historical:
            yield historical

    def close(self) -> None:
        self._compiled_graph_cache = None
        self._active_graph_cache.clear()
        self._grounding_bundle_cache = None
        self._conn.close()

    def grounding_bundle(self):
        """Return the grounded-rule bundle materialized in this sidecar."""

        if self._grounding_bundle_cache is None:
            from propstore.families.rules.declaration import read_grounded_bundle

            self._grounding_bundle_cache = read_grounded_bundle(self._conn)
        return self._grounding_bundle_cache

    def _validate_schema(self) -> None:
        validate_sqlalchemy_store(self._derived_store_path, world_sqlalchemy_schema())
        meta_row = self._conn.execute(
            "SELECT schema_version FROM meta WHERE key = ?",
            (PROPSTORE_WORLD_META_KEY,),
        ).fetchone()
        if meta_row is None:
            raise ValueError(
                f"Unsupported SQLAlchemy store: missing metadata row {PROPSTORE_WORLD_META_KEY!r}."
            )
        schema_version = int(meta_row[0])
        if schema_version != PROPSTORE_WORLD_SCHEMA_VERSION:
            raise ValueError(
                "Unsupported SQLAlchemy store schema version "
                f"{schema_version}; expected {PROPSTORE_WORLD_SCHEMA_VERSION}."
            )

    # ── Lazy Z3 setup ────────────────────────────────────────────────

    def _ensure_solver(self) -> ConditionSolver:
        if self._solver is not None:
            return self._solver
        registry = self._build_registry()
        self._solver = ConditionSolver(registry)
        return self._solver

    def _build_registry(self) -> dict[str, ConceptInfo]:
        if self._registry is not None:
            return self._registry
        schema = world_sqlalchemy_schema()
        concept = schema.model("concept")
        with self._derived_store.readonly_session(schema) as derived:
            normalized_rows = list(derived.execute(select(concept)).scalars())
        registry = with_standard_synthetic_bindings(
            build_store_cel_registry(normalized_rows)
        )
        self._registry = registry
        return registry

    def condition_solver(self) -> ConditionSolver:
        return self._ensure_solver()

    def _load_lifting_system(self) -> LiftingSystem | None:
        if self._lifting_system_loaded:
            return self._lifting_system
        self._lifting_system_loaded = True

        self._lifting_system = load_lifting_system(self._derived_store)
        return self._lifting_system

    # ── Unbound queries ──────────────────────────────────────────────

    def get_concept(self, concept_id: str) -> Concept | None:
        schema = world_sqlalchemy_schema()
        concept_model = schema.model("concept")
        with self._derived_store.readonly_session(schema) as derived:
            concept = derived.execute(
                select(concept_model).where(concept_model.id == concept_id)
            ).scalar_one_or_none()
            if concept is None:
                resolved = self.resolve_concept(concept_id)
                if resolved is None or resolved == concept_id:
                    return None
                concept = derived.execute(
                    select(concept_model).where(concept_model.id == resolved)
                ).scalar_one_or_none()
        if concept is None:
            return None
        return concept

    def concept_name(self, concept_id: str) -> str | None:
        """Return the canonical name for a concept, or None if not found."""
        concept = self.get_concept(concept_id)
        return concept.canonical_name if concept else None

    def concept_names(self) -> dict[str, str]:
        """Return ``{concept_id: canonical_name}`` for all concepts."""
        return {
            str(concept.concept_id): concept.canonical_name
            for concept in self.all_concepts()
        }

    def get_claim(self, claim_id: str) -> Claim | None:
        schema = world_sqlalchemy_schema()
        claim = schema.model("claim_core")
        with self._derived_store.readonly_session(schema) as derived:
            resolved_claim_id = (
                schema.resolve_reference_id(
                    derived.session,
                    "claim_core",
                    claim_id,
                )
                or self._get_logical_id_index("claim_core").get(claim_id)
                or claim_id
            )
            return derived.execute(
                select(claim).where(claim.id == resolved_claim_id)
            ).scalar_one_or_none()

    def _build_logical_id_index(self, table: str) -> dict[str, str]:
        """Return a ``name → artifact_id`` map for one of ``claim_core``/``concept``.

        Both composite ``"namespace:value"`` keys AND bare ``"value"``
        keys populate the same map so the cache covers every form the
        pre-memoized fallback already supported. A single query plus a
        Python pass replaces per-miss full-table scans. WorldQuery is
        immutable per open sidecar (all rows live under a read-only
        connection, cleared only by ``close()``), so the index is safe
        to build once and reuse for the lifetime of the instance.
        """

        if table not in ("claim_core", "concept"):
            raise ValueError(f"unsupported logical-id table: {table}")
        index: dict[str, str] = {}
        schema = world_sqlalchemy_schema()
        model = schema.model(table)
        with self._derived_store.readonly_session(schema) as derived:
            rows = derived.execute(
                select(
                    model.id,
                    model.primary_logical_id,
                    model.logical_ids_json,
                )
            )
            for artifact_id, primary_logical_id, logical_ids_json in rows:
                artifact_id_text = str(artifact_id)
                if isinstance(primary_logical_id, str) and primary_logical_id:
                    index.setdefault(primary_logical_id, artifact_id_text)
                if not isinstance(logical_ids_json, str) or not logical_ids_json:
                    continue
                try:
                    logical_ids = json.loads(logical_ids_json)
                except json.JSONDecodeError:
                    continue
                if not isinstance(logical_ids, list):
                    continue
                for entry in logical_ids:
                    if not isinstance(entry, dict):
                        continue
                    namespace = entry.get("namespace")
                    value = entry.get("value")
                    if isinstance(namespace, str) and isinstance(value, str):
                        index.setdefault(f"{namespace}:{value}", artifact_id_text)
                        index.setdefault(value, artifact_id_text)
        return index

    def _get_logical_id_index(self, table: str) -> dict[str, str]:
        if table not in self._logical_id_indexes:
            self._logical_id_indexes[table] = self._build_logical_id_index(table)
        return self._logical_id_indexes[table]

    def resolve_alias(self, alias: str) -> str | None:
        schema = world_sqlalchemy_schema()
        alias_model = schema.model("alias")
        with self._derived_store.readonly_session(schema) as derived:
            row = derived.execute(
                select(alias_model.concept_id).where(alias_model.alias_name == alias)
            ).first()
            return None if row is None else str(row[0])

    def resolve_concept(self, name: str) -> str | None:
        """Resolve a concept by alias, artifact ID, logical ID, or canonical name."""
        resolved = self.resolve_alias(name)
        if resolved:
            return resolved

        schema = world_sqlalchemy_schema()
        concept = schema.model("concept")
        with self._derived_store.readonly_session(schema) as derived:
            for field_name in ("id", "primary_logical_id"):
                row = derived.execute(
                    select(concept.id).where(getattr(concept, field_name) == name)
                ).first()
                if row is not None:
                    return str(row[0])

            cached = self._get_logical_id_index("concept").get(name)
            if cached is not None:
                return cached

            row = derived.execute(
                select(concept.id).where(concept.canonical_name == name)
            ).first()
            return None if row is None else str(row[0])

    def claims_for(self, concept_id: str | None) -> list[Claim]:
        resolved_concept_id = (
            None
            if concept_id is None
            else self.resolve_concept(concept_id) or concept_id
        )
        schema = world_sqlalchemy_schema()
        claim = schema.model("claim_core")
        link = schema.model("claim_concept_link")
        with self._derived_store.readonly_session(schema) as derived:
            statement = select(claim).order_by(claim.id)
            if resolved_concept_id is not None:
                statement = (
                    statement.join(link, link.claim_id == claim.id)
                    .where(link.concept_id == resolved_concept_id)
                    .where(link.role.in_((ClaimConceptLinkRole.OUTPUT, ClaimConceptLinkRole.TARGET)))
                    .distinct()
                )
            return list(derived.execute(statement).scalars())

    def claims_related_to_concept(self, concept_id: str | None) -> list[Claim]:
        resolved_concept_id = (
            None
            if concept_id is None
            else self.resolve_concept(concept_id) or concept_id
        )
        schema = world_sqlalchemy_schema()
        claim = schema.model("claim_core")
        link = schema.model("claim_concept_link")
        with self._derived_store.readonly_session(schema) as derived:
            statement = select(claim).order_by(claim.id)
            if resolved_concept_id is not None:
                statement = (
                    statement.join(link, link.claim_id == claim.id)
                    .where(link.concept_id == resolved_concept_id)
                    .distinct()
                )
            return list(derived.execute(statement).scalars())

    def _render_policy_predicates(
        self, policy: RenderPolicy
    ) -> tuple[list[str], tuple[Any, ...]]:
        """Translate a ``RenderPolicy`` into SQL ``WHERE`` predicates on
        ``claim_core``'s lifecycle columns.

        Per axis-1 findings 3.1 / 3.2 / 3.3 (closed in
        ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``):

        - ``stage = 'draft'`` rows are hidden unless ``include_drafts=True``.
        - ``build_status = 'blocked'`` rows are hidden unless
          ``include_blocked=True`` (raw-id quarantine, Phase 3 Gate 1).
        - ``promotion_status = 'blocked'`` rows are hidden unless
          ``include_blocked=True`` (partial-promote mirror, Phase 3 Gate 3).

        A policy with all three flags at their default ``False`` produces
        three predicates that together preserve the "don't show problems
        by default" posture required by the CLAUDE.md design checklist.
        """
        predicates: list[str] = []
        params: list[Any] = []
        if not policy.include_drafts:
            predicates.append("(core.stage IS NULL OR core.stage != 'draft')")
        if not policy.include_blocked:
            predicates.append(
                "(core.build_status IS NULL OR core.build_status != 'blocked')"
            )
            predicates.append(
                "(core.promotion_status IS NULL "
                "OR core.promotion_status != 'blocked')"
            )
        return predicates, tuple(params)

    def _render_policy_predicates_for_alias(
        self,
        policy: RenderPolicy,
        alias: str,
    ) -> tuple[list[str], tuple[Any, ...]]:
        predicates, params = self._render_policy_predicates(policy)
        return [predicate.replace("core.", f"{alias}.") for predicate in predicates], params

    def claims_with_policy(
        self,
        concept_id: str | None,
        policy: RenderPolicy,
    ) -> list[Claim]:
        """Return claim rows filtered by the lifecycle visibility flags
        on ``policy``.

        Implements the render-time contract described in
        ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``
        (axis-1 findings 3.1 / 3.2 / 3.3): the source-of-truth sidecar
        holds every row, and the render layer picks what to show based
        on explicit user policy. Default policy preserves the
        pre-render-gate-removal visibility — drafts and blocked rows
        stay out of the default view but remain queryable through opt-in
        flags.
        """
        resolved_concept_id = (
            None
            if concept_id is None
            else self.resolve_concept(concept_id) or concept_id
        )
        schema = world_sqlalchemy_schema()
        claim = schema.model("claim_core")
        link = schema.model("claim_concept_link")
        with self._derived_store.readonly_session(schema) as derived:
            statement = select(claim).order_by(claim.id)
            if resolved_concept_id is not None:
                statement = (
                    statement.join(link, link.claim_id == claim.id)
                    .where(link.concept_id == resolved_concept_id)
                    .distinct()
                )
            if not policy.include_drafts:
                statement = statement.where(or_(claim.stage.is_(None), claim.stage != "draft"))
            if not policy.include_blocked:
                statement = statement.where(
                    or_(claim.build_status.is_(None), claim.build_status != "blocked")
                ).where(
                    or_(
                        claim.promotion_status.is_(None),
                        claim.promotion_status != "blocked",
                    )
                )
            return list(derived.execute(statement).scalars())

    def build_diagnostics(self, policy: RenderPolicy) -> list[dict[str, Any]]:
        """Return ``build_diagnostics`` rows when ``policy.show_quarantined``
        is ``True``; an empty list otherwise.

        Per axis-1 findings 3.1 / 3.2 / 3.3: the ``build_diagnostics``
        table is the quarantine surface for rows the sidecar accepted
        but flagged as problematic. The render layer surfaces these rows
        only under explicit opt-in, preserving the
        ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``
        exit-criterion that "the default view matches pre-fix behaviour
        for clean trees."
        """
        if not policy.show_quarantined:
            return []
        with self._derived_store.readonly_session(world_sqlalchemy_schema()) as derived:
            return build_diagnostics(derived)

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, Claim]:
        if not claim_ids:
            return {}
        schema = world_sqlalchemy_schema()
        claim = schema.model("claim_core")
        with self._derived_store.readonly_session(schema) as derived:
            resolved_ids = {
                schema.resolve_reference_id(
                    derived.session,
                    "claim_core",
                    claim_id,
                )
                or claim_id
                for claim_id in claim_ids
            }
            rows = derived.execute(
                select(claim).where(claim.id.in_(resolved_ids))
            ).scalars()
            return {str(row.id): row for row in rows}

    def at_journal_step(
        self,
        journal: TransitionJournal,
        k: int,
        *,
        rebind: bool = False,
        heavy: bool = False,
    ) -> ClaimView:
        """Project the claims accepted at step ``k`` of the journal.

        Bridge surface defined in
        ``quire/plans/worldline-journal-bridge-2026-05-02.md``. Per Bonanno
        [2007, 2010] (branching-time AGM with PLS) and Dixon [1993] (ATMS
        into AGM behavioural equivalence), this projection is behaviourally
        equivalent to running the journal's operations against the live
        store, modulo the lossy projection at the AGM boundary.

        Delegates to ``propstore.world.bridge.at_journal_step``; the same
        function is used by the property suite against a synthetic belief
        space, so this method's behaviour is the same shape as the
        property tests.
        """
        from propstore.world.bridge import at_journal_step as _at_journal_step

        return _at_journal_step(self, journal, k, rebind=rebind, heavy=heavy)

    def bind_for_view(
        self,
        *,
        bindings: Mapping[str, Any],
        context_id: str | None,
        restricted_to: frozenset[str],
    ) -> _BoundView:
        """Rebind under a snapshot's scope, restricted to a claim-id set.

        Returns a real ``BoundWorld`` so callers of ``at_journal_step(...,
        rebind=True)`` see an observably-different view than the flat
        ``rebind=False`` path. The restricted_to set is propagated as the
        environment's effective claim scope.
        """
        env = Environment(
            bindings=dict(bindings),
            context_id=None if context_id is None else to_context_id(context_id),
        )
        bound = self.bind(environment=env)
        # BoundWorld carries _environment; expose the restriction set on the
        # view so the bridge tests can observe it.
        return _BoundView(bound=bound, restricted_to=restricted_to)

    def stances_between(self, claim_ids: set[str]) -> list[Stance]:
        if not claim_ids:
            return []
        schema = world_sqlalchemy_schema()
        stance_model = schema.polymorphic_model("relation_edge", "claim")
        with self._derived_store.readonly_session(schema) as derived:
            resolved_ids = {
                schema.resolve_reference_id(
                    derived.session,
                    "claim_core",
                    claim_id,
                )
                or claim_id
                for claim_id in claim_ids
            }
            statement = (
                select(stance_model)
                .where(stance_model.source_id.in_(resolved_ids))
                .where(stance_model.target_id.in_(resolved_ids))
                .order_by(stance_model.source_id, stance_model.target_id, stance_model.relation_type)
            )
            return list(derived.execute(statement).scalars())

    def conflicts(self, concept_id: str | None = None) -> list[ConflictWitness]:
        schema = world_sqlalchemy_schema()
        conflict = schema.model("conflict_witness")
        with self._derived_store.readonly_session(schema) as derived:
            statement = select(conflict).order_by(conflict.claim_a_id, conflict.claim_b_id)
            if concept_id is not None:
                statement = statement.where(conflict.concept_id == concept_id)
            return list(derived.execute(statement).scalars())

    def all_concepts(self) -> list[Concept]:
        schema = world_sqlalchemy_schema()
        concept = schema.model("concept")
        with self._derived_store.readonly_session(schema) as derived:
            return list(derived.execute(select(concept)).scalars())

    def all_parameterizations(self) -> list[Parameterization]:
        schema = world_sqlalchemy_schema()
        parameterization = schema.model("parameterization")
        with self._derived_store.readonly_session(schema) as derived:
            return list(derived.execute(select(parameterization)).scalars())

    def all_relationships(self) -> list[ConceptRelation]:
        schema = world_sqlalchemy_schema()
        relation = schema.polymorphic_model("relation_edge", "concept")
        with self._derived_store.readonly_session(schema) as derived:
            statement = select(relation).order_by(
                relation.source_id,
                relation.target_id,
                relation.relation_type,
            )
            return list(derived.execute(statement).scalars())

    def all_claim_stances(self) -> list[Stance]:
        schema = world_sqlalchemy_schema()
        stance = schema.polymorphic_model("relation_edge", "claim")
        with self._derived_store.readonly_session(schema) as derived:
            statement = select(stance).order_by(
                stance.source_id,
                stance.target_id,
                stance.relation_type,
            )
            return list(derived.execute(statement).scalars())

    def all_authored_justifications(self) -> tuple[CanonicalJustification, ...]:
        return select_authored_justifications(self._conn)

    def justifications_for_claim_scope(
        self,
        claim_ids: set[str],
    ) -> tuple[CanonicalJustification, ...]:
        if not claim_ids:
            return ()
        schema = world_sqlalchemy_schema()
        with self._derived_store.readonly_session(schema) as derived:
            resolved_ids = {
                schema.resolve_reference_id(
                    derived.session,
                    "claim_core",
                    claim_id,
                )
                or claim_id
                for claim_id in claim_ids
            }
        return tuple(
            justification
            for justification in self.all_authored_justifications()
            if justification.conclusion_claim_id in resolved_ids
            and all(
                premise_id in resolved_ids
                for premise_id in justification.premise_claim_ids
            )
        )

    def claim_stances_with_policy(
        self,
        focus_claim_id: str,
        policy: RenderPolicy,
    ) -> list[Stance]:
        schema = world_sqlalchemy_schema()
        relation = schema.model("relation_edge")
        claim = schema.model("claim_core")
        source_claim = aliased(claim)
        target_claim = aliased(claim)
        with self._derived_store.readonly_session(schema) as derived:
            resolved_focus_claim_id = (
                schema.resolve_reference_id(
                    derived.session,
                    "claim_core",
                    focus_claim_id,
                )
                or focus_claim_id
            )
            statement = (
                select(relation)
                .join(source_claim, relation.source_id == source_claim.id)
                .join(target_claim, relation.target_id == target_claim.id)
                .where(relation.source_kind == "claim")
                .where(relation.target_kind == "claim")
                .where(
                    or_(
                        relation.source_id == resolved_focus_claim_id,
                        relation.target_id == resolved_focus_claim_id,
                    )
                )
            )
            for claim_alias in (source_claim, target_claim):
                if not policy.include_drafts:
                    statement = statement.where(
                        or_(claim_alias.stage.is_(None), claim_alias.stage != "draft")
                    )
                if not policy.include_blocked:
                    statement = statement.where(
                        or_(
                            claim_alias.build_status.is_(None),
                            claim_alias.build_status != "blocked",
                        )
                    ).where(
                        or_(
                            claim_alias.promotion_status.is_(None),
                            claim_alias.promotion_status != "blocked",
                        )
                    )
            return list(derived.execute(statement).scalars())

    def all_micropublications(self) -> list[Micropublication]:
        schema = world_sqlalchemy_schema()
        micropublication = schema.model("micropublication")
        with self._derived_store.readonly_session(schema) as derived:
            statement = (
                select(micropublication)
                .options(selectinload(micropublication.claim_links))
                .order_by(micropublication.id)
            )
            return list(derived.execute(statement).scalars())

    def concept_ids_for_group(self, group_id: int) -> set[str]:
        schema = world_sqlalchemy_schema()
        parameterization_group = schema.model("parameterization_group")
        with self._derived_store.readonly_session(schema) as derived:
            rows = derived.execute(
                select(parameterization_group.concept_id).where(
                    parameterization_group.group_id == group_id
                )
            )
            return {str(row[0]) for row in rows}

    def search(self, query: str) -> list[ConceptSearchHit]:
        schema = world_sqlalchemy_schema()
        concept = schema.model("concept")
        with self._derived_store.readonly_session(schema) as derived:
            try:
                hits = search_fts_index(derived, "concept_fts", query)
            except FtsQuerySyntaxError as exc:
                raise ConceptSearchQuerySyntaxError(query) from exc
            concept_ids = tuple(hit.entity_id for hit in hits)
            if not concept_ids:
                return []
            rows = derived.execute(
                select(concept).where(concept.id.in_(concept_ids))
            ).scalars()
            concepts_by_id = {row.id: row for row in rows}
            return [
                ConceptSearchHit(concept_id=concepts_by_id[concept_id].concept_id)
                for concept_id in concept_ids
                if concept_id in concepts_by_id
            ]

    def similar_claims(
        self,
        claim_id: str,
        model_name: str | None = None,
        top_k: int = 10,
    ) -> list[ClaimSimilarityHit]:
        """Find claims similar to the given claim by embedding distance.

        Requires pre-computed embeddings.
        """
        from propstore.families.embeddings.declaration import (
            find_similar,
            get_registered_models,
        )

        if model_name is None:
            models = get_registered_models(self._derived_store)
            if not models:
                return []
            model_name = models[0]["model_name"]

        assert model_name is not None  # narrowed above
        return [
            ClaimSimilarityHit.from_row_mapping(result)
            for result in find_similar(
                self._derived_store,
                claim_id,
                model_name,
                top_k=top_k,
            )
        ]

    def similar_concepts(
        self,
        concept_id: str,
        model_name: str | None = None,
        top_k: int = 10,
    ) -> list[ConceptSimilarityHit]:
        """Find concepts similar to the given concept by embedding distance.

        Requires pre-computed embeddings.
        """
        from propstore.families.embeddings.declaration import (
            find_similar_concepts,
            get_registered_models,
        )

        if model_name is None:
            models = get_registered_models(self._derived_store)
            if not models:
                return []
            model_name = models[0]["model_name"]

        assert model_name is not None  # narrowed above
        return [
            ConceptSimilarityHit.from_row_mapping(result)
            for result in find_similar_concepts(
                self._derived_store,
                concept_id,
                model_name,
                top_k=top_k,
            )
        ]

    # ── Form algebra queries ────────────────────────────────────────

    def forms_by_dimensions(self, dims: dict[str, int]) -> list[dict]:
        """Find all forms with matching SI dimensions."""
        from bridgman import dims_equal
        rows = self._all_form_rows()
        results = []
        for row in rows:
            row_dims_json = row["dimensions"]
            if row_dims_json is None:
                row_dims: dict[str, int] = {}
                if not row["is_dimensionless"]:
                    continue  # No dimensions and not dimensionless — skip
            else:
                row_dims = json.loads(row_dims_json)
            if dims_equal(row_dims, dims):
                results.append(dict(row))
        return results

    def form_algebra_for(self, form_name: str) -> list[dict]:
        """Get all algebra decompositions that produce *form_name*."""
        schema = world_sqlalchemy_schema()
        form_algebra = schema.model("form_algebra")
        with self._derived_store.readonly_session(schema) as derived:
            rows = derived.execute(
                select(form_algebra).where(form_algebra.output_form == form_name)
            ).scalars()
            return [self._model_row("form_algebra", row) for row in rows]

    def form_algebra_using(self, form_name: str) -> list[dict]:
        """Get all algebra entries where *form_name* is an input."""
        rows = self._all_form_algebra_rows()
        results = []
        for row in rows:
            input_forms = json.loads(row["input_forms"])
            if form_name in input_forms:
                results.append(row)
        return results

    def _all_form_rows(self) -> list[dict[str, Any]]:
        schema = world_sqlalchemy_schema()
        form = schema.model("form")
        with self._derived_store.readonly_session(schema) as derived:
            return [
                self._model_row("form", row)
                for row in derived.execute(select(form)).scalars()
            ]

    def _all_form_algebra_rows(self) -> list[dict[str, Any]]:
        schema = world_sqlalchemy_schema()
        form_algebra = schema.model("form_algebra")
        with self._derived_store.readonly_session(schema) as derived:
            return [
                self._model_row("form_algebra", row)
                for row in derived.execute(select(form_algebra)).scalars()
            ]

    @staticmethod
    def _model_row(table_name: str, row: object) -> dict[str, Any]:
        schema = world_sqlalchemy_schema()
        return {
            column.name: getattr(row, column.name)
            for column in schema.table(table_name).columns
        }

    def stats(self) -> WorldStoreStats:
        schema = world_sqlalchemy_schema()
        concept = schema.model("concept")
        claim = schema.model("claim_core")
        with self._derived_store.readonly_session(schema) as derived:
            concepts = int(
                derived.execute(select(func.count()).select_from(concept)).scalar_one()
            )
            claims = int(
                derived.execute(select(func.count()).select_from(claim)).scalar_one()
            )
        schema = world_sqlalchemy_schema()
        conflict = schema.model("conflict_witness")
        with self._derived_store.readonly_session(schema) as derived:
            conflicts = int(
                derived.execute(select(func.count()).select_from(conflict)).scalar_one()
            )
        return WorldStoreStats(
            concepts=int(concepts),
            claims=int(claims),
            conflicts=int(conflicts),
        )

    def authored_justification_count(self) -> int:
        return count_authored_justifications(self._conn)

    # ── Parameterization queries ─────────────────────────────────────

    def _parameterizations_for(self, concept_id: str) -> list[Parameterization]:
        """Get parameterization rows where output_concept_id matches."""
        resolved_concept_id = self.resolve_concept(concept_id) or concept_id
        schema = world_sqlalchemy_schema()
        parameterization = schema.model("parameterization")
        with self._derived_store.readonly_session(schema) as derived:
            return list(
                derived.execute(
                    select(parameterization).where(
                        parameterization.output_concept_id == resolved_concept_id
                    )
                ).scalars()
            )

    def parameterizations_for(self, concept_id: str) -> list[Parameterization]:
        return self._parameterizations_for(concept_id)

    def compiled_graph(self):
        """Build the canonical compiled semantic graph from the current sidecar."""
        from propstore.core.graph_types import CompiledWorldGraph
        from propstore.core.graph_build import build_compiled_world_graph

        if self._compiled_graph_cache is None:
            self._compiled_graph_cache = build_compiled_world_graph(
                self,
                prefer_logical_claim_ids=False,
            )
        return CompiledWorldGraph.from_dict(self._compiled_graph_cache.to_dict())

    def active_graph(
        self,
        environment: Environment,
        *,
        lifting_system: LiftingSystem | None = None,
    ):
        from propstore.core.activation import activate_compiled_world_graph
        from propstore.core.graph_types import ActiveWorldGraph

        resolved_lifting_system = lifting_system or self._load_lifting_system()
        cache_key = json.dumps(environment.to_dict(), sort_keys=True)
        if cache_key not in self._active_graph_cache:
            self._active_graph_cache[cache_key] = activate_compiled_world_graph(
                self.compiled_graph(),
                environment=environment,
                solver=self.condition_solver(),
                lifting_system=resolved_lifting_system,
            )
        cached = self._active_graph_cache[cache_key]
        return ActiveWorldGraph.from_dict(cached.to_dict())

    def _group_members(self, concept_id: str) -> list[str]:
        """Get all concept_ids in the same parameterization group."""
        resolved_concept_id = self.resolve_concept(concept_id) or concept_id
        schema = world_sqlalchemy_schema()
        parameterization_group = schema.model("parameterization_group")
        with self._derived_store.readonly_session(schema) as derived:
            group_row = derived.execute(
                select(parameterization_group.group_id).where(
                    parameterization_group.concept_id == resolved_concept_id
                )
            ).first()
            if group_row is None:
                return []
            rows = derived.execute(
                select(parameterization_group.concept_id).where(
                    parameterization_group.group_id == int(group_row[0])
                )
            )
            return [str(row[0]) for row in rows]

    def group_members(self, concept_id: str) -> list[str]:
        return self._group_members(concept_id)

    # ── Stance graph ─────────────────────────────────────────────────

    def explain(self, claim_id: str) -> list[Stance]:
        """Walk normalized claim relation edges breadth-first from claim_id."""
        schema = world_sqlalchemy_schema()
        stance = schema.polymorphic_model("relation_edge", "claim")
        result: list[Stance] = []
        queue = [claim_id]
        visited = {claim_id}
        with self._derived_store.readonly_session(schema) as derived:
            while queue:
                current = queue.pop(0)
                rows = list(
                    derived.execute(
                        select(stance)
                        .where(stance.source_id == current)
                        .order_by(stance.target_id, stance.relation_type)
                    ).scalars()
                )
                for row in rows:
                    result.append(row)
                    target = str(row.target_claim_id)
                    if target not in visited:
                        visited.add(target)
                        queue.append(target)
        return result

    # ── Condition binding ────────────────────────────────────────────

    def bind(
        self,
        environment: Environment | None = None,
        *,
        policy: RenderPolicy | None = None,
        **conditions: Any,
    ) -> BoundWorld:
        from propstore.world.bound import BoundWorld

        if environment is None:
            environment = Environment(bindings=conditions)
        else:
            merged = dict(environment.bindings)
            if conditions:
                merged.update(conditions)
            environment = Environment(
                bindings=merged,
                context_id=environment.context_id,
                effective_assumptions=tuple(environment.effective_assumptions),
                assumptions=tuple(environment.assumptions),
            )

        lifting_system = self._load_lifting_system()
        if environment.context_id is not None and lifting_system is not None:
            environment = Environment(
                bindings=environment.bindings,
                context_id=environment.context_id,
                effective_assumptions=tuple(
                    lifting_system.effective_assumptions(environment.context_id)
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
            self,
            environment=environment,
            lifting_system=lifting_system,
            policy=policy,
            active_graph=self.active_graph(
                environment,
                lifting_system=lifting_system,
            ),
        )

    def intervene(
        self,
        assignment: Mapping[str, Any],
        *,
        exogenous_assignment: Mapping[str, Any] | None = None,
    ):
        """Return a Pearl-style intervention world over this compiled graph."""
        from propstore.world.intervention import InterventionWorld
        from propstore.world.scm import StructuralCausalModel

        scm = StructuralCausalModel.from_compiled_graph(
            self.compiled_graph(),
            exogenous_assignment=exogenous_assignment,
        )
        return InterventionWorld(scm, assignment)

    def observe(
        self,
        assignment: Mapping[str, Any],
        *,
        exogenous_assignment: Mapping[str, Any] | None = None,
    ):
        """Return a deterministic observation world over this compiled graph."""
        from propstore.world.intervention import ObservationWorld
        from propstore.world.scm import StructuralCausalModel

        scm = StructuralCausalModel.from_compiled_graph(
            self.compiled_graph(),
            exogenous_assignment=exogenous_assignment,
        )
        return ObservationWorld(scm, assignment)

    # ── Chain query ──────────────────────────────────────────────────

    def chain_query(
        self,
        target_concept_id: str,
        strategy: ResolutionStrategy | None = None,
        **bindings: Any,
    ) -> ChainResult:
        """Traverse the parameter space to derive the target concept."""
        policy = RenderPolicy(strategy=strategy) if strategy is not None else None
        bound = self.bind(policy=policy, **bindings)
        steps: list[ChainStep] = []
        resolved_values: dict[str, float | str | None] = {}
        visited: set[str] = set()
        unresolved_conflicted: list[str] = []

        # Record initial bindings as steps
        for key, value in bindings.items():
            steps.append(ChainStep(concept_id=key, value=value, source="binding"))

        # Get parameterization group for target
        group = self._group_members(target_concept_id)
        if not group:
            group = [target_concept_id]

        # Iterative resolution: keep trying until no more progress
        changed = True
        while changed:
            changed = False
            for cid in group:
                if cid in visited:
                    continue

                # Try value_of first
                vr = bound.value_of(cid)
                if vr.status is ValueStatus.DETERMINED:
                    numeric_payload = vr.claims[0].numeric_payload if vr.claims else None
                    value = None if numeric_payload is None else numeric_payload.value
                    if value is not None:
                        resolved_values[cid] = value
                        steps.append(ChainStep(concept_id=cid, value=value, source="claim"))
                        visited.add(cid)
                        changed = True
                        continue

                # If conflicted and strategy given, try resolve
                if vr.status is ValueStatus.CONFLICTED and strategy is not None:
                    rr = bound.resolved_value(cid)
                    if rr.status is ValueStatus.RESOLVED and rr.value is not None:
                        resolved_values[cid] = rr.value
                        steps.append(ChainStep(concept_id=cid, value=rr.value, source="resolved"))
                        visited.add(cid)
                        changed = True
                        continue

                # Track conflicted concepts that could not be resolved
                if vr.status is ValueStatus.CONFLICTED and cid not in unresolved_conflicted:
                    unresolved_conflicted.append(cid)

                # Try derived_value
                dr = bound.derived_value(cid, override_values=resolved_values)
                if dr.status is ValueStatus.DERIVED and dr.value is not None:
                    resolved_values[cid] = dr.value
                    steps.append(ChainStep(concept_id=cid, value=dr.value, source="derived"))
                    visited.add(cid)
                    changed = True

        # Get the target's result
        if target_concept_id in resolved_values:
            # Find the step for the target to determine result type
            target_step = next(
                (s for s in steps if s.concept_id == target_concept_id), None
            )
            if target_step and target_step.source == "derived":
                dr = bound.derived_value(target_concept_id, override_values=resolved_values)
                result: ValueResult | DerivedResult = dr
            else:
                result = bound.value_of(target_concept_id)
        else:
            # Try one more time with all resolved values
            dr = bound.derived_value(target_concept_id, override_values=resolved_values)
            if dr.status is ValueStatus.DERIVED:
                result = dr
            else:
                result = bound.value_of(target_concept_id)

        return ChainResult(
            target_concept_id=to_concept_id(target_concept_id),
            result=result,
            steps=steps,
            bindings_used=bindings,
            unresolved_dependencies=[to_concept_id(concept_id) for concept_id in unresolved_conflicted],
        )
