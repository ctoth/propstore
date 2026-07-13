"""The canonical render-time policy and its integrity constraints.

``RenderPolicy`` is *data*: the choices a render runs under. It lives in ``core``
rather than ``propstore.world`` because it is persisted — the ``worldlines``
charter stores the policy a materialized worldline was rendered under, and the
charter is read by the storage layer, which may never import ``world``
(``.importlinter``; ``propstore.families.registry`` imports the worldline
charter). Owning the policy here is what lets that charter field be typed rather
than a ``dict[str, Any]`` blob behind a hand-written codec.

:mod:`propstore.world.types` re-exports these for its existing consumers; there
is exactly one spelling of each.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, TypeGuard

from assignment_selection import MergeOperator
from condition_ir import CelExpr, to_cel_expr

from propstore.core.reasoning import (
    ArgumentationSemantics,
    ReasoningBackend,
    normalize_argumentation_semantics,
    normalize_reasoning_backend,
)
from propstore.families.concepts import ConceptStatus


def _is_mapping(value: object) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(value, Mapping)


def _optional_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not _is_mapping(value):
        raise ValueError(f"render policy field '{field_name}' must be a mapping")
    return value


class ResolutionStrategy(StrEnum):
    RECENCY = "recency"
    SAMPLE_SIZE = "sample_size"
    ARGUMENTATION = "argumentation"
    OVERRIDE = "override"
    ASSIGNMENT_SELECTION_MERGE = "assignment_selection_merge"


def normalize_merge_operator(value: MergeOperator | str) -> MergeOperator:
    """Narrow a sidecar/dict string to the canonical ``assignment_selection``
    ``MergeOperator``.

    The merge operator type is owned by the ``assignment_selection`` substrate
    package; propstore keeps only this string-narrowing coercer for the
    ``RenderPolicy.from_dict`` boundary, never a second spelling of the enum.
    """
    if isinstance(value, MergeOperator):
        return value
    try:
        return MergeOperator(str(value))
    except ValueError as exc:
        raise ValueError(f"Unknown merge_operator '{value}'") from exc


class IntegrityConstraintKind(StrEnum):
    RANGE = "range"
    CATEGORY = "category"
    CEL = "cel"
    CUSTOM = "custom"


@dataclass(frozen=True)
class IntegrityConstraint:
    kind: IntegrityConstraintKind
    concept_ids: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict[str, Any])
    cel: CelExpr | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_ids", tuple(self.concept_ids))
        object.__setattr__(self, "metadata", dict(self.metadata))
        if self.cel is not None:
            object.__setattr__(self, "cel", to_cel_expr(self.cel))
        if not self.concept_ids:
            raise ValueError("IntegrityConstraint requires at least one concept id")
        if len(set(self.concept_ids)) != len(self.concept_ids):
            raise ValueError("IntegrityConstraint has duplicate concept ids")
        if self.kind == IntegrityConstraintKind.CUSTOM:
            predicate = self.metadata.get("predicate")
            if not callable(predicate):
                raise TypeError("CUSTOM integrity constraint requires callable metadata['predicate']")


def integrity_constraint_from_dict(data: Mapping[str, Any]) -> IntegrityConstraint:
    return IntegrityConstraint(
        kind=(
            data["kind"]
            if isinstance(data["kind"], IntegrityConstraintKind)
            else IntegrityConstraintKind(str(data["kind"]))
        ),
        concept_ids=tuple(str(concept_id) for concept_id in data.get("concept_ids", ())),
        metadata=dict(_optional_mapping(data.get("metadata"), "metadata")),
        cel=None if data.get("cel") is None else to_cel_expr(str(data["cel"])),
        description=(
            None
            if data.get("description") is None
            else str(data["description"])
        ),
    )


def integrity_constraint_to_dict(constraint: IntegrityConstraint) -> dict[str, Any]:
    metadata = dict(constraint.metadata)
    if constraint.kind == IntegrityConstraintKind.CUSTOM and "predicate" in metadata:
        raise TypeError("CUSTOM integrity constraints with callable predicates are not serializable")
    return {
        "kind": constraint.kind.value,
        "concept_ids": list(constraint.concept_ids),
        "metadata": metadata,
        "cel": constraint.cel,
        "description": constraint.description,
    }


@dataclass(frozen=True)
class RenderPolicy:
    """Render-time policy — the single canonical render policy for the system.

    `reasoning_backend` selects the argumentation implementation used when
    `strategy` is ARGUMENTATION. `strategy` chooses a winner among active
    claims when a concept is conflicted at render time. The lifecycle
    visibility flags (`include_drafts`/`include_blocked`/`show_quarantined`)
    govern which non-default statuses surface — see :meth:`admits` for the
    concept-status projection used by ``propstore.render.render_concepts``.
    """

    reasoning_backend: ReasoningBackend = ReasoningBackend.CLAIM_GRAPH
    strategy: ResolutionStrategy | None = None
    semantics: ArgumentationSemantics = ArgumentationSemantics.GROUNDED
    comparison: str = "elitist"
    link: str = "last"
    # Decision criterion for interpreting opinion uncertainty at render time
    # Per Denoeux (2019, p.17-18): pignistic is the default (E(ω) = b + a·u)
    decision_criterion: str = "pignistic"
    # Hurwicz pessimism index α ∈ [0,1] — only used when criterion="hurwicz"
    # α=1.0 → pessimistic (lower bound), α=0.0 → optimistic (upper bound)
    # Per Denoeux (2019, p.17)
    pessimism_index: float = 0.5
    # Whether to include [Bel, Pl] uncertainty interval in output
    # Per Jøsang (2001, p.4): interval endpoints Bel=b, Pl=1-d
    show_uncertainty_interval: bool = False
    # PrAF-specific fields (Li et al. 2012, Popescu 2024)
    # All with defaults for backward compatibility.
    praf_strategy: str = "auto"  # "auto", "mc", "exact", "dfquad_quad", "dfquad_baf"
    praf_mc_epsilon: float = 0.01  # MC error tolerance (Li 2012, p.8)
    praf_mc_confidence: float = 0.95  # MC confidence level
    praf_treewidth_cutoff: int = 12  # max treewidth for exact DP (Popescu 2024, p.8)
    praf_mc_seed: int | None = None  # RNG seed (None = random)
    # assignment-selection merge fields for the assignment-level Konieczny-style adaptation.
    # merge_operator selects the aggregation family used by the global solver.
    merge_operator: MergeOperator = MergeOperator.SIGMA
    # branch_filter restricts which branches are included as sources.
    branch_filter: tuple[str, ...] | None = None
    # branch_weights assigns per-branch importance weights.
    branch_weights: Mapping[str, float] | None = None
    # explicit integrity constraints for global assignment-selection merge
    integrity_constraints: tuple[IntegrityConstraint, ...] = field(default_factory=tuple)
    future_queryables: tuple[str, ...] = field(default_factory=tuple)
    future_limit: int | None = None
    overrides: Mapping[str, str] = field(default_factory=dict[str, str])
    concept_strategies: Mapping[str, ResolutionStrategy] = field(
        default_factory=dict[str, ResolutionStrategy]
    )
    # Lifecycle visibility flags (WS-Z-gates Phase 4; axis-1 findings 3.1/3.2/3.3).
    # Default False preserves the "don't show problems by default" posture the
    # design checklist requires (see CLAUDE.md and
    # reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md).
    # - include_drafts: lifts the default filter that hides claim_core rows
    #   carrying stage='draft' (Phase 3 Gate 2; per
    #   propstore/compiler/passes.py draft traversal).
    # - include_blocked: lifts the default filter that hides rows with
    #   build_status='blocked' (raw-id quarantine; Phase 3 Gate 1) or
    #   promotion_status='blocked' (partial-promote mirror rows; Phase 3
    #   Gate 3).
    # - show_quarantined: surfaces build_diagnostics rows in render output.
    include_drafts: bool = False
    include_blocked: bool = False
    show_quarantined: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "semantics",
            normalize_argumentation_semantics(self.semantics),
        )
        object.__setattr__(
            self,
            "merge_operator",
            normalize_merge_operator(self.merge_operator),
        )
        if self.branch_filter is not None:
            object.__setattr__(
                self,
                "branch_filter",
                tuple(self.branch_filter),
            )
        if self.branch_weights is not None:
            object.__setattr__(
                self,
                "branch_weights",
                dict(self.branch_weights),
            )
        object.__setattr__(
            self,
            "integrity_constraints",
            tuple(self.integrity_constraints),
        )
        object.__setattr__(
            self,
            "future_queryables",
            tuple(self.future_queryables),
        )
        object.__setattr__(self, "overrides", dict(self.overrides))
        object.__setattr__(
            self,
            "concept_strategies",
            dict(self.concept_strategies),
        )

    def admits(self, status: ConceptStatus) -> bool:
        """Whether a concept of ``status`` is visible under this policy.

        The default policy hides ``DRAFT`` and ``BLOCKED`` concepts (present in
        storage but filtered at render time); ``include_drafts`` /
        ``include_blocked`` lift those filters. All other statuses are always
        visible. Used by ``propstore.render.render_concepts``.
        """
        if status is ConceptStatus.DRAFT:
            return self.include_drafts
        if status is ConceptStatus.BLOCKED:
            return self.include_blocked
        return True

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> RenderPolicy:
        """Parse a render policy from a genuinely untyped payload.

        This is the CLI/HTTP flag-and-query boundary, where the input really is
        decoded JSON authored outside the type system. The ``worldlines``
        charter does *not* go through here — it stores a typed ``RenderPolicy``
        and Quire decodes it (CLAUDE.md: crossing a boundary is a call, not a
        conversion).
        """
        if not data:
            return cls()

        strategy_value = data.get("strategy")
        reasoning_backend_value = data.get("reasoning_backend", ReasoningBackend.CLAIM_GRAPH)
        reasoning_backend = normalize_reasoning_backend(reasoning_backend_value)
        concept_strategies = {
            str(concept_id): (
                strategy
                if isinstance(strategy, ResolutionStrategy)
                else ResolutionStrategy(str(strategy))
            )
            for concept_id, strategy in _optional_mapping(
                data.get("concept_strategies"),
                "concept_strategies",
            ).items()
        }
        branch_weights = (
            None
            if data.get("branch_weights") is None
            else dict(_optional_mapping(data.get("branch_weights"), "branch_weights"))
        )
        return cls(
            reasoning_backend=reasoning_backend,
            strategy=(
                None
                if strategy_value is None
                else (
                    strategy_value
                    if isinstance(strategy_value, ResolutionStrategy)
                    else ResolutionStrategy(str(strategy_value))
                )
            ),
            semantics=normalize_argumentation_semantics(
                data.get("semantics", ArgumentationSemantics.GROUNDED)
            ),
            comparison=str(data.get("comparison", "elitist")),
            link=str(data.get("link", "last")),
            decision_criterion=str(data.get("decision_criterion", "pignistic")),
            pessimism_index=float(data.get("pessimism_index", 0.5)),
            show_uncertainty_interval=bool(data.get("show_uncertainty_interval", False)),
            praf_strategy=str(data.get("praf_strategy", "auto")),
            praf_mc_epsilon=float(data.get("praf_mc_epsilon", 0.01)),
            praf_mc_confidence=float(data.get("praf_mc_confidence", 0.95)),
            praf_treewidth_cutoff=int(data.get("praf_treewidth_cutoff", 12)),
            praf_mc_seed=(
                None
                if data.get("praf_mc_seed") is None
                else int(data["praf_mc_seed"])
            ),
            merge_operator=normalize_merge_operator(
                data.get("merge_operator", MergeOperator.SIGMA)
            ),
            branch_filter=(
                None
                if data.get("branch_filter") is None
                else tuple(data["branch_filter"])
            ),
            branch_weights=branch_weights,
            integrity_constraints=tuple(
                integrity_constraint_from_dict(item)
                for item in (data.get("integrity_constraints") or ())
            ),
            future_queryables=tuple(data.get("future_queryables") or ()),
            future_limit=(
                None
                if data.get("future_limit") is None
                else int(data["future_limit"])
            ),
            overrides=dict(_optional_mapping(data.get("overrides"), "overrides")),
            concept_strategies=concept_strategies,
            include_drafts=bool(data.get("include_drafts", False)),
            include_blocked=bool(data.get("include_blocked", False)),
            show_quarantined=bool(data.get("show_quarantined", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.reasoning_backend != ReasoningBackend.CLAIM_GRAPH:
            data["reasoning_backend"] = self.reasoning_backend.value
        if self.strategy is not None:
            data["strategy"] = self.strategy.value
        if self.semantics != ArgumentationSemantics.GROUNDED:
            data["semantics"] = self.semantics.value
        if self.comparison != "elitist":
            data["comparison"] = self.comparison
        if self.link != "last":
            data["link"] = self.link
        if self.decision_criterion != "pignistic":
            data["decision_criterion"] = self.decision_criterion
        if self.pessimism_index != 0.5:
            data["pessimism_index"] = self.pessimism_index
        if self.show_uncertainty_interval:
            data["show_uncertainty_interval"] = self.show_uncertainty_interval
        if self.praf_strategy != "auto":
            data["praf_strategy"] = self.praf_strategy
        if self.praf_mc_epsilon != 0.01:
            data["praf_mc_epsilon"] = self.praf_mc_epsilon
        if self.praf_mc_confidence != 0.95:
            data["praf_mc_confidence"] = self.praf_mc_confidence
        if self.praf_treewidth_cutoff != 12:
            data["praf_treewidth_cutoff"] = self.praf_treewidth_cutoff
        if self.praf_mc_seed is not None:
            data["praf_mc_seed"] = self.praf_mc_seed
        if self.merge_operator != MergeOperator.SIGMA:
            data["merge_operator"] = self.merge_operator
        if self.branch_filter is not None:
            data["branch_filter"] = list(self.branch_filter)
        if self.branch_weights is not None:
            data["branch_weights"] = dict(self.branch_weights)
        if self.integrity_constraints:
            data["integrity_constraints"] = [
                integrity_constraint_to_dict(constraint)
                for constraint in self.integrity_constraints
            ]
        if self.future_queryables:
            data["future_queryables"] = list(self.future_queryables)
        if self.future_limit is not None:
            data["future_limit"] = self.future_limit
        if self.overrides:
            data["overrides"] = dict(self.overrides)
        if self.concept_strategies:
            data["concept_strategies"] = {
                concept_id: strategy.value
                for concept_id, strategy in self.concept_strategies.items()
            }
        if self.include_drafts:
            data["include_drafts"] = self.include_drafts
        if self.include_blocked:
            data["include_blocked"] = self.include_blocked
        if self.show_quarantined:
            data["show_quarantined"] = self.show_quarantined
        return data


__all__ = [
    "IntegrityConstraint",
    "IntegrityConstraintKind",
    "RenderPolicy",
    "ResolutionStrategy",
    "integrity_constraint_from_dict",
    "integrity_constraint_to_dict",
    "normalize_merge_operator",
]
