"""ATMS-style global label and nogood propagation for a bound belief space.

This is a first real ATMS-style engine over the current labelled kernel.
It propagates exact labels globally across active claims and compatible
parameterization justifications, then prunes them with nogoods induced by
active conflicts. Run 4 exposes ATMS-native inspection over those labels:
TRUE/IN/OUT node status, essential support, justification traces, nogood
provenance, and label verification. It is not yet a full de Kleer runtime
or incremental ATMS, not Dung-extension semantics, and not stability or
relevance analysis.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field, replace
from itertools import product
from typing import TYPE_CHECKING, Any

from propstore.propagation import evaluate_parameterization
from propstore.world.labelled import (
    AssumptionRef,
    EnvironmentKey,
    Label,
    NogoodSet,
    combine_labels,
    merge_labels,
)
from propstore.world.labelled import SupportQuality
from propstore.world.types import ATMSInspection, ATMSNodeStatus

if TYPE_CHECKING:
    from propstore.world.bound import BoundWorld


@dataclass(frozen=True)
class ATMSNode:
    node_id: str
    kind: str
    payload: dict[str, Any]
    label: Label = field(default_factory=Label)
    justification_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ATMSJustification:
    justification_id: str
    antecedent_ids: tuple[str, ...]
    consequent_ids: tuple[str, ...]
    informant: str


class ATMSEngine:
    """Global exact-support propagation engine for one bound world."""

    def __init__(self, bound: BoundWorld) -> None:
        self._bound = bound
        self._nodes: dict[str, ATMSNode] = {}
        self._justifications: dict[str, ATMSJustification] = {}
        self._claim_node_ids: dict[str, str] = {}
        self._assumption_node_ids: dict[str, str] = {}
        self._all_parameterizations = tuple(self._sorted_parameterizations())
        self.nogoods = NogoodSet()
        self._nogood_provenance: dict[EnvironmentKey, tuple[dict[str, Any], ...]] = {}
        self._build()

    def claim_label(self, claim_id: str) -> Label | None:
        node_id = self._claim_node_ids.get(claim_id)
        if node_id is None:
            return None
        return self._label_or_none(self._nodes[node_id].label)

    def supported_claim_ids(self, concept_id: str | None = None) -> set[str]:
        supported: set[str] = set()
        for claim_id, node_id in self._claim_node_ids.items():
            node = self._nodes[node_id]
            if concept_id is not None and node.payload.get("concept_id") != concept_id:
                continue
            if node.label.environments:
                supported.add(claim_id)
        return supported

    def derived_label(self, concept_id: str, value: float | str | None) -> Label | None:
        if value is None:
            return None
        labels: list[Label] = []
        for node in self._nodes.values():
            if node.kind != "derived":
                continue
            if node.payload.get("concept_id") != concept_id:
                continue
            if self._normalize_value(node.payload.get("value")) != self._normalize_value(value):
                continue
            if node.label.environments:
                labels.append(node.label)
        if not labels:
            return None
        merged = merge_labels(labels, nogoods=self.nogoods)
        return self._label_or_none(merged)

    def node_status(self, node_id: str) -> ATMSInspection:
        node = self._nodes.get(node_id)
        if node is None:
            raise KeyError(f"Unknown ATMS node: {node_id}")

        label = self._label_or_none(node.label)
        status = self._status_from_label(node.label)
        support_quality = self._support_quality_for_node(node)
        return ATMSInspection(
            node_id=node_id,
            claim_id=node.payload.get("claim_id"),
            kind=node.kind,
            status=status,
            support_quality=support_quality,
            label=label,
            essential_support=self.essential_support(node_id),
            reason=self._reason_for_node(node, status, support_quality),
        )

    def claim_status(self, claim_id: str) -> ATMSInspection:
        node_id = self._claim_node_ids.get(claim_id)
        if node_id is None:
            raise KeyError(f"Unknown ATMS claim: {claim_id}")
        return self.node_status(node_id)

    def essential_support(
        self,
        node_id: str,
        environment: EnvironmentKey | tuple[str, ...] | list[str] | None = None,
    ) -> EnvironmentKey | None:
        node = self._nodes.get(node_id)
        if node is None:
            raise KeyError(f"Unknown ATMS node: {node_id}")
        if not node.label.environments:
            return None

        bound_environment = (
            self._bound_environment_key()
            if environment is None
            else self._coerce_environment_key(environment)
        )
        compatible = [
            env
            for env in node.label.environments
            if env.subsumes(bound_environment)
        ]
        if not compatible:
            return None

        shared = set(compatible[0].assumption_ids)
        for env in compatible[1:]:
            shared.intersection_update(env.assumption_ids)
        return EnvironmentKey(tuple(sorted(shared)))

    def nodes_in_environment(
        self,
        environment: EnvironmentKey | tuple[str, ...] | list[str],
    ) -> list[str]:
        environment_key = self._coerce_environment_key(environment)
        return sorted(
            node_id
            for node_id, node in self._nodes.items()
            if any(label_env.subsumes(environment_key) for label_env in node.label.environments)
        )

    def explain_node(self, node_id: str) -> dict[str, Any]:
        return self._explain_node(node_id, seen_nodes={node_id})

    def explain_nogood(
        self,
        environment_key: EnvironmentKey | tuple[str, ...] | list[str],
    ) -> dict[str, Any] | None:
        query = self._coerce_environment_key(environment_key)
        if query not in self.nogoods.environments:
            return None
        return self._serialize_nogood_detail(query)

    def verify_labels(self) -> dict[str, Any]:
        consistency_errors: list[str] = []
        minimality_errors: list[str] = []
        soundness_errors: list[str] = []
        completeness_errors: list[str] = []
        known_assumptions = set(self._assumption_node_ids)

        for node_id, node in sorted(self._nodes.items()):
            environments = node.label.environments
            for environment in environments:
                if self.nogoods.excludes(environment):
                    consistency_errors.append(
                        f"{node_id}: environment {environment.assumption_ids} is excluded by a nogood"
                    )
                unknown = [
                    assumption_id
                    for assumption_id in environment.assumption_ids
                    if assumption_id not in known_assumptions
                ]
                if unknown:
                    consistency_errors.append(
                        f"{node_id}: environment {environment.assumption_ids} references unknown assumptions {unknown}"
                    )

            for index, environment in enumerate(environments):
                for other in environments[index + 1:]:
                    if environment.subsumes(other) or other.subsumes(environment):
                        minimality_errors.append(
                            f"{node_id}: label contains non-minimal environments {environment.assumption_ids} and {other.assumption_ids}"
                        )

            expected = self._expected_label_for_node(node_id)
            actual_environments = set(environments)
            expected_environments = set(expected.environments)
            missing = sorted(expected_environments - actual_environments, key=lambda env: env.assumption_ids)
            extra = sorted(actual_environments - expected_environments, key=lambda env: env.assumption_ids)
            for environment in extra:
                soundness_errors.append(
                    f"{node_id}: environment {environment.assumption_ids} is not justified by the current ATMS graph"
                )
            for environment in missing:
                completeness_errors.append(
                    f"{node_id}: missing justified environment {environment.assumption_ids}"
                )

        return {
            "ok": not (
                consistency_errors
                or minimality_errors
                or soundness_errors
                or completeness_errors
            ),
            "consistency_errors": consistency_errors,
            "minimality_errors": minimality_errors,
            "soundness_errors": soundness_errors,
            "completeness_errors": completeness_errors,
        }

    def argumentation_state(self) -> dict[str, Any]:
        claim_inspections = {
            claim["id"]: self.claim_status(claim["id"])
            for claim in self._bound.active_claims()
            if claim.get("id") in self._claim_node_ids
        }
        return {
            "backend": "atms",
            "supported": sorted(self.supported_claim_ids()),
            "defeated": sorted(
                claim["id"]
                for claim in self._bound.active_claims()
                if claim.get("id") not in self.supported_claim_ids()
            ),
            "nogoods": [
                list(environment.assumption_ids)
                for environment in self.nogoods.environments
            ],
            "node_statuses": {
                inspection.node_id: inspection.status.value
                for inspection in claim_inspections.values()
            },
            "support_quality": {
                claim_id: inspection.support_quality.value
                for claim_id, inspection in claim_inspections.items()
            },
            "essential_support": {
                claim_id: self._serialize_environment_key(inspection.essential_support) or []
                for claim_id, inspection in claim_inspections.items()
            },
            "status_reasons": {
                claim_id: inspection.reason
                for claim_id, inspection in claim_inspections.items()
            },
            "nogood_details": [
                self._serialize_nogood_detail(environment)
                for environment in self.nogoods.environments
            ],
        }

    def _build(self) -> None:
        self._build_assumption_nodes()
        self._build_claim_nodes_and_justifications()

        while True:
            self._propagate_labels()
            added_justifications = self._materialize_parameterization_justifications()
            updated_nogoods = self._update_nogoods()
            if not added_justifications and not updated_nogoods:
                self._propagate_labels()
                break

    def _build_assumption_nodes(self) -> None:
        for assumption in sorted(
            self._bound._environment.assumptions,
            key=lambda item: item.assumption_id,
        ):
            node_id = f"assumption:{assumption.assumption_id}"
            node = ATMSNode(
                node_id=node_id,
                kind="assumption",
                payload={
                    "assumption": assumption,
                    "cel": assumption.cel,
                },
                label=Label.singleton(assumption),
            )
            self._nodes[node_id] = node
            self._assumption_node_ids[assumption.assumption_id] = node_id

    def _build_claim_nodes_and_justifications(self) -> None:
        for claim in sorted(self._bound.active_claims(), key=lambda row: row["id"]):
            claim_id = claim["id"]
            node_id = f"claim:{claim_id}"
            self._nodes[node_id] = ATMSNode(
                node_id=node_id,
                kind="claim",
                payload={
                    "claim_id": claim_id,
                    "concept_id": (
                        claim.get("concept_id")
                        or claim.get("concept")
                        or claim.get("target_concept")
                    ),
                    "value": claim.get("value"),
                    "claim": claim,
                },
            )
            self._claim_node_ids[claim_id] = node_id

            for antecedents in self._exact_antecedent_sets(
                claim.get("conditions_cel"),
                context_id=claim.get("context_id"),
            ):
                self._add_justification(
                    antecedent_ids=antecedents,
                    consequent_id=node_id,
                    informant=f"claim:{claim_id}",
                )

    def _propagate_labels(self) -> None:
        seeded_nodes = {
            node_id: node.label
            for node_id, node in self._nodes.items()
            if node.kind == "assumption"
        }
        for node_id, node in list(self._nodes.items()):
            if node.kind != "assumption":
                self._nodes[node_id] = replace(node, label=Label(()))

        for node_id, label in seeded_nodes.items():
            self._nodes[node_id] = replace(self._nodes[node_id], label=label)

        changed = True
        while changed:
            changed = False
            for justification_id in sorted(self._justifications):
                justification = self._justifications[justification_id]
                antecedent_labels: list[Label] = []
                supported = True
                for antecedent_id in justification.antecedent_ids:
                    label = self._nodes[antecedent_id].label
                    if not label.environments:
                        supported = False
                        break
                    antecedent_labels.append(label)
                if not supported:
                    continue

                candidate = combine_labels(*antecedent_labels, nogoods=self.nogoods)
                for consequent_id in justification.consequent_ids:
                    current = self._nodes[consequent_id].label
                    merged = merge_labels([current, candidate], nogoods=self.nogoods)
                    if merged != current:
                        self._nodes[consequent_id] = replace(
                            self._nodes[consequent_id],
                            label=merged,
                        )
                        changed = True

    def _materialize_parameterization_justifications(self) -> bool:
        added = False
        provider_ids_by_concept = self._provider_node_ids_by_concept()

        for index, param in enumerate(self._all_parameterizations):
            if not self._bound.is_param_compatible(param.get("conditions_cel")):
                continue

            condition_antecedents = self._exact_antecedent_sets(
                param.get("conditions_cel"),
            )
            if not condition_antecedents:
                continue

            output_concept_id = param["output_concept_id"]
            sympy_expr = param.get("sympy")
            if not sympy_expr:
                continue

            input_ids = json.loads(param["concept_ids"])
            effective_inputs = [concept_id for concept_id in input_ids if concept_id != output_concept_id]
            input_provider_sets = [provider_ids_by_concept.get(concept_id, ()) for concept_id in effective_inputs]
            if any(not provider_ids for provider_ids in input_provider_sets):
                continue

            for provider_combo in product(*input_provider_sets):
                input_values = {
                    concept_id: float(self._nodes[node_id].payload["value"])
                    for concept_id, node_id in zip(effective_inputs, provider_combo, strict=True)
                }
                derived_value = evaluate_parameterization(sympy_expr, input_values, output_concept_id)
                if derived_value is None:
                    continue

                derived_node_id = self._derived_node_id(output_concept_id, derived_value)
                if derived_node_id not in self._nodes:
                    self._nodes[derived_node_id] = ATMSNode(
                        node_id=derived_node_id,
                        kind="derived",
                        payload={
                            "concept_id": output_concept_id,
                            "value": derived_value,
                            "parameterization_index": index,
                            "formula": param.get("formula"),
                        },
                    )

                for condition_antecedent_ids in condition_antecedents:
                    antecedent_ids = tuple(condition_antecedent_ids + provider_combo)
                    added |= self._add_justification(
                        antecedent_ids=antecedent_ids,
                        consequent_id=derived_node_id,
                        informant=f"parameterization:{index}",
                    )

        return added

    def _update_nogoods(self) -> bool:
        environments: list[EnvironmentKey] = list(self.nogoods.environments)
        provenance: dict[EnvironmentKey, list[dict[str, Any]]] = defaultdict(list)
        for environment, details in self._nogood_provenance.items():
            provenance[environment].extend(details)
        for conflict in self._bound.conflicts():
            claim_a = conflict.get("claim_a_id")
            claim_b = conflict.get("claim_b_id")
            if not claim_a or not claim_b:
                continue

            label_a = self.claim_label(claim_a)
            label_b = self.claim_label(claim_b)
            if label_a is None or label_b is None:
                continue

            for env_a in label_a.environments:
                for env_b in label_b.environments:
                    nogood_environment = env_a.union(env_b)
                    environments.append(nogood_environment)
                    provenance[nogood_environment].append({
                        "claim_a_id": claim_a,
                        "claim_b_id": claim_b,
                        "concept_id": conflict.get("concept_id"),
                        "warning_class": conflict.get("warning_class"),
                        "environment_a": list(env_a.assumption_ids),
                        "environment_b": list(env_b.assumption_ids),
                    })

        updated = NogoodSet(tuple(environments))
        if updated == self.nogoods:
            return False
        self.nogoods = updated
        self._nogood_provenance = {
            environment: tuple(provenance.get(environment, ()))
            for environment in self.nogoods.environments
        }
        return True

    def _provider_node_ids_by_concept(self) -> dict[str, tuple[str, ...]]:
        providers: dict[str, list[str]] = defaultdict(list)
        for node_id, node in self._nodes.items():
            if node.kind not in {"claim", "derived"}:
                continue
            if not node.label.environments:
                continue
            concept_id = node.payload.get("concept_id")
            value = node.payload.get("value")
            if concept_id is None or value is None:
                continue
            providers[concept_id].append(node_id)
        return {
            concept_id: tuple(sorted(node_ids))
            for concept_id, node_ids in providers.items()
        }

    def _sorted_parameterizations(self) -> list[dict]:
        rows = getattr(self._bound._store, "all_parameterizations", lambda: [])()
        return sorted(
            rows,
            key=lambda row: (
                row.get("output_concept_id") or "",
                row.get("formula") or "",
                row.get("sympy") or "",
            ),
        )

    def _exact_antecedent_sets(
        self,
        conditions_cel: str | None,
        *,
        context_id: str | None = None,
    ) -> list[tuple[str, ...]]:
        if not conditions_cel:
            return [] if context_id is not None else [()]

        try:
            conditions = json.loads(conditions_cel)
        except (TypeError, json.JSONDecodeError):
            return []
        if not conditions:
            return [] if context_id is not None else [()]

        matching_node_groups: list[list[str]] = []
        for condition in conditions:
            matches = [
                node_id
                for node_id, node in self._nodes.items()
                if node.kind == "assumption"
                and isinstance(node.payload.get("assumption"), AssumptionRef)
                and node.payload["assumption"].cel == condition
            ]
            if not matches:
                return []
            matching_node_groups.append(sorted(matches))

        return [
            tuple(sorted(node_ids))
            for node_ids in product(*matching_node_groups)
        ]

    def _add_justification(
        self,
        *,
        antecedent_ids: tuple[str, ...],
        consequent_id: str,
        informant: str,
    ) -> bool:
        justification_id = self._justification_id(
            antecedent_ids=antecedent_ids,
            consequent_id=consequent_id,
            informant=informant,
        )
        if justification_id in self._justifications:
            return False

        justification = ATMSJustification(
            justification_id=justification_id,
            antecedent_ids=tuple(sorted(antecedent_ids)),
            consequent_ids=(consequent_id,),
            informant=informant,
        )
        self._justifications[justification_id] = justification

        node = self._nodes[consequent_id]
        self._nodes[consequent_id] = replace(
            node,
            justification_ids=tuple(sorted(node.justification_ids + (justification_id,))),
        )
        return True

    @staticmethod
    def _justification_id(
        *,
        antecedent_ids: tuple[str, ...],
        consequent_id: str,
        informant: str,
    ) -> str:
        joined = ",".join(sorted(antecedent_ids))
        return f"{informant}->{consequent_id}[{joined}]"

    @staticmethod
    def _derived_node_id(concept_id: str, value: float | str) -> str:
        return f"derived:{concept_id}:{ATMSEngine._value_key(value)}"

    @staticmethod
    def _value_key(value: float | str | None) -> str:
        normalized = ATMSEngine._normalize_value(value)
        return json.dumps(normalized, sort_keys=True, separators=(",", ":"), default=str)

    @staticmethod
    def _normalize_value(value: float | str | None) -> float | str | None:
        if isinstance(value, int | float) and not isinstance(value, bool):
            return float(value)
        return value

    def _status_from_label(self, label: Label) -> ATMSNodeStatus:
        if not label.environments:
            return ATMSNodeStatus.OUT
        if EnvironmentKey(()) in label.environments:
            return ATMSNodeStatus.TRUE
        return ATMSNodeStatus.IN

    def _support_quality_for_node(self, node: ATMSNode) -> SupportQuality:
        if node.kind != "claim":
            return SupportQuality.EXACT
        if node.label.environments:
            return SupportQuality.EXACT

        claim = node.payload.get("claim")
        claim_support = getattr(self._bound, "claim_support", None)
        if claim is not None and callable(claim_support):
            _label, quality = claim_support(claim)
            return quality
        return SupportQuality.SEMANTIC_COMPATIBLE

    def _reason_for_node(
        self,
        node: ATMSNode,
        status: ATMSNodeStatus,
        support_quality: SupportQuality,
    ) -> str:
        if status == ATMSNodeStatus.TRUE:
            return "label contains the empty environment"
        if status == ATMSNodeStatus.IN:
            return "label has surviving exact support under non-empty environments"
        if self._was_pruned_by_nogood(node.node_id):
            return "exact-support environments were pruned by nogoods"
        if node.kind != "claim":
            return "no surviving ATMS label environments"
        if support_quality == SupportQuality.CONTEXT_VISIBLE_ONLY:
            return "active only via context visibility; no exact ATMS label"
        if support_quality == SupportQuality.MIXED:
            return "active via mixed semantic/context activation; no exact ATMS label"
        if support_quality == SupportQuality.SEMANTIC_COMPATIBLE:
            return "active only via semantic compatibility; no exact ATMS label"
        if node.justification_ids:
            return "exact justifications exist but no surviving label environments"
        return "no exact ATMS justification produced a label"

    def _was_pruned_by_nogood(self, node_id: str) -> bool:
        node = self._nodes[node_id]
        if node.label.environments:
            return False
        for justification_id in node.justification_ids:
            justification = self._justifications[justification_id]
            raw = self._justification_candidate_label(justification, nogoods=None)
            pruned = self._justification_candidate_label(justification, nogoods=self.nogoods)
            if raw.environments and not pruned.environments:
                return True
        return False

    def _justification_candidate_label(
        self,
        justification: ATMSJustification,
        *,
        nogoods: NogoodSet | None,
    ) -> Label:
        antecedent_labels: list[Label] = []
        for antecedent_id in justification.antecedent_ids:
            antecedent = self._nodes[antecedent_id]
            if not antecedent.label.environments:
                return Label(())
            antecedent_labels.append(antecedent.label)
        return combine_labels(*antecedent_labels, nogoods=nogoods)

    def _expected_label_for_node(self, node_id: str) -> Label:
        node = self._nodes[node_id]
        if node.kind == "assumption":
            assumption = node.payload.get("assumption")
            if isinstance(assumption, AssumptionRef):
                return Label.singleton(assumption)
            return Label(())

        candidates = [
            self._justification_candidate_label(self._justifications[justification_id], nogoods=self.nogoods)
            for justification_id in node.justification_ids
        ]
        return merge_labels(candidates, nogoods=self.nogoods)

    def _bound_environment_key(self) -> EnvironmentKey:
        return EnvironmentKey(
            tuple(
                assumption.assumption_id
                for assumption in self._bound._environment.assumptions
            )
        )

    @staticmethod
    def _coerce_environment_key(
        environment: EnvironmentKey | tuple[str, ...] | list[str],
    ) -> EnvironmentKey:
        if isinstance(environment, EnvironmentKey):
            return environment
        return EnvironmentKey(tuple(environment))

    def _explain_justification(
        self,
        justification_id: str,
        *,
        seen_nodes: set[str],
    ) -> dict[str, Any] | None:
        justification = self._justifications[justification_id]
        candidate = self._justification_candidate_label(justification, nogoods=self.nogoods)
        consequent = self._nodes[justification.consequent_ids[0]]
        if not candidate.environments:
            return None
        if consequent.label.environments and not any(
            environment in consequent.label.environments
            for environment in candidate.environments
        ):
            return None

        antecedents: list[dict[str, Any]] = []
        for antecedent_id in justification.antecedent_ids:
            antecedent_node = self._nodes[antecedent_id]
            if antecedent_id in seen_nodes:
                antecedents.append({
                    "node_id": antecedent_id,
                    "kind": antecedent_node.kind,
                    "cycle": True,
                })
                continue
            if antecedent_node.kind == "assumption":
                antecedents.append({
                    "node_id": antecedent_id,
                    "kind": antecedent_node.kind,
                    "label": self._serialize_label(self._label_or_none(antecedent_node.label)),
                })
                continue

            nested_seen = set(seen_nodes)
            nested_seen.add(antecedent_id)
            antecedents.append(self._explain_node(antecedent_id, seen_nodes=nested_seen) | {
                "antecedent_of": justification.consequent_ids[0],
            })

        return {
            "node_id": consequent.node_id,
            "justification_id": justification.justification_id,
            "antecedent_ids": list(justification.antecedent_ids),
            "consequent_id": justification.consequent_ids[0],
            "informant": justification.informant,
            "support": self._serialize_label(candidate),
            "antecedents": antecedents,
        }

    def _explain_node(
        self,
        node_id: str,
        *,
        seen_nodes: set[str],
    ) -> dict[str, Any]:
        node = self._nodes.get(node_id)
        if node is None:
            raise KeyError(f"Unknown ATMS node: {node_id}")

        inspection = self.node_status(node_id)
        traces = [
            trace
            for justification_id in node.justification_ids
            if (trace := self._explain_justification(justification_id, seen_nodes=seen_nodes)) is not None
        ]
        return {
            "node_id": node_id,
            "claim_id": inspection.claim_id,
            "kind": node.kind,
            "status": inspection.status.value,
            "support_quality": inspection.support_quality.value,
            "label": self._serialize_label(inspection.label),
            "essential_support": self._serialize_environment_key(inspection.essential_support),
            "reason": inspection.reason,
            "traces": traces,
        }

    @staticmethod
    def _serialize_environment_key(environment: EnvironmentKey | None) -> list[str] | None:
        if environment is None:
            return None
        return list(environment.assumption_ids)

    @classmethod
    def _serialize_label(cls, label: Label | None) -> list[list[str]] | None:
        if label is None:
            return None
        return [
            cls._serialize_environment_key(environment) or []
            for environment in label.environments
        ]

    def _serialize_nogood_detail(self, environment: EnvironmentKey) -> dict[str, Any]:
        return {
            "environment": list(environment.assumption_ids),
            "provenance": [
                dict(detail)
                for detail in self._nogood_provenance.get(environment, ())
            ],
        }

    @staticmethod
    def _label_or_none(label: Label) -> Label | None:
        if not label.environments:
            return None
        return label
