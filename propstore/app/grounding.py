"""Application-layer grounding inspection workflows."""

from __future__ import annotations

from dataclasses import dataclass

from propstore.grounding.inspection import (
    GroundingArgumentsReport,
    GroundingExplainReport,
    GroundingInspectionError,
    GroundingQueryReport,
    GroundingShowReport,
    GroundingStatusReport,
    inspect_grounding_arguments,
    inspect_grounding_explain,
    inspect_grounding_query,
    inspect_grounding_show,
    inspect_grounding_status,
)
from propstore.repository import Repository


@dataclass(frozen=True)
class GroundingQueryRequest:
    atom: str


@dataclass(frozen=True)
class GroundingExplainRequest:
    atom: str


def grounding_status(repo: Repository) -> GroundingStatusReport:
    return inspect_grounding_status(repo)


def grounding_show(repo: Repository) -> GroundingShowReport:
    return inspect_grounding_show(repo)


def grounding_query(repo: Repository, request: GroundingQueryRequest) -> GroundingQueryReport:
    return inspect_grounding_query(repo, request.atom)


def grounding_arguments(repo: Repository) -> GroundingArgumentsReport:
    return inspect_grounding_arguments(repo)


def grounding_explain(
    repo: Repository,
    request: GroundingExplainRequest,
) -> GroundingExplainReport:
    return inspect_grounding_explain(repo, request.atom)


__all__ = [
    "GroundingArgumentsReport",
    "GroundingExplainReport",
    "GroundingExplainRequest",
    "GroundingInspectionError",
    "GroundingQueryReport",
    "GroundingQueryRequest",
    "GroundingShowReport",
    "GroundingStatusReport",
    "grounding_arguments",
    "grounding_explain",
    "grounding_query",
    "grounding_show",
    "grounding_status",
]
