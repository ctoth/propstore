from __future__ import annotations

from typing import get_type_hints

from propstore.world.bound import BoundWorld
from propstore.world.types import (
    ATMSConceptFutureStatusEntry,
    ATMSConceptInterventionPlan,
    ATMSConceptRelevanceReport,
    ATMSConceptRelevanceState,
    ATMSConceptStabilityReport,
    ATMSNodeExplanation,
    ATMSNodeStatus,
    ValueStatus,
)
from propstore.core.labels import SupportQuality


def test_atms_concept_status_annotations_use_value_status() -> None:
    assert get_type_hints(ATMSConceptFutureStatusEntry)["status"] is ValueStatus
    assert get_type_hints(ATMSConceptStabilityReport)["current_status"] is ValueStatus
    assert get_type_hints(ATMSConceptRelevanceState)["status"] is ValueStatus
    assert get_type_hints(ATMSConceptRelevanceReport)["current_status"] is ValueStatus
    assert get_type_hints(ATMSConceptInterventionPlan)["current_status"] is ValueStatus
    assert get_type_hints(ATMSConceptInterventionPlan)["target_status"] is ValueStatus
    assert get_type_hints(ATMSConceptInterventionPlan)["result_status"] is ValueStatus
    assert get_type_hints(BoundWorld.concept_interventions)["target_value_status"] is ValueStatus
    assert get_type_hints(BoundWorld.concept_next_queryables)["target_value_status"] is ValueStatus


def test_atms_node_status_annotations_use_enums() -> None:
    assert get_type_hints(ATMSNodeExplanation)["status"] is ATMSNodeStatus
    assert get_type_hints(ATMSNodeExplanation)["support_quality"] is SupportQuality
    assert get_type_hints(BoundWorld.claim_interventions)["target_status"] is ATMSNodeStatus
    assert get_type_hints(BoundWorld.claim_next_queryables)["target_status"] is ATMSNodeStatus
