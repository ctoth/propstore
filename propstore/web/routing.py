"""Route registration for the web adapter."""

from __future__ import annotations

from typing import Literal, overload

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

from propstore.app.claim_views import (
    ClaimSummaryReport,
    ClaimViewBlockedError,
    ClaimViewReport,
    ClaimListRequest,
    ClaimSearchRequest,
    ClaimViewRequest,
    ClaimViewUnknownClaimError,
    build_claim_view,
    list_claim_views,
    search_claim_views,
)
from propstore.app.concept_views import (
    ConceptViewReport,
    ConceptViewRequest,
    ConceptViewUnknownConceptError,
    build_concept_view,
)
from propstore.app.concepts.display import ConceptSearchSyntaxError, search_concepts
from propstore.app.concepts.mutation import (
    ConceptListReport,
    ConceptListRequest,
    ConceptSearchReport,
    ConceptSearchRequest,
    ConceptSidecarMissingError,
    list_concepts,
)
from propstore.app.neighborhoods import (
    SemanticNeighborhoodReport,
    SemanticNeighborhoodRequest,
    SemanticNeighborhoodUnsupportedFocusError,
    build_semantic_neighborhood,
)
from propstore.app.repository_overview import (
    RepositoryOverviewReport,
    RepositoryOverviewRequest,
    build_repository_overview,
)
from propstore.app.repository_views import RepositoryViewUnsupportedStateError
from propstore.app.rendering import RenderPolicyValidationError
from propstore.app.world_revision import AppRevisionWorldRequest
from propstore.app.world import WorldSidecarMissingError
from propstore.repository import Repository
from propstore.web.html import render_error_page
from propstore.web.requests import (
    WebQueryParseError,
    parse_render_policy_request,
    parse_repository_view_request,
)

_EXPECTED_WEB_ERRORS = (
    WebQueryParseError,
    RenderPolicyValidationError,
    RepositoryViewUnsupportedStateError,
    ClaimViewUnknownClaimError,
    ConceptViewUnknownConceptError,
    ConceptSearchSyntaxError,
    SemanticNeighborhoodUnsupportedFocusError,
    ClaimViewBlockedError,
    WorldSidecarMissingError,
    ConceptSidecarMissingError,
)

_ERROR_RESPONSES: dict[type[Exception], tuple[str, int]] = {
    WebQueryParseError: ("Invalid Request", 400),
    RenderPolicyValidationError: ("Invalid Render Policy", 400),
    RepositoryViewUnsupportedStateError: ("Unsupported Repository State", 400),
    SemanticNeighborhoodUnsupportedFocusError: ("Unsupported Focus", 400),
    ClaimViewUnknownClaimError: ("Claim Not Found", 404),
    ClaimViewBlockedError: ("Not Found", 404),
    ConceptViewUnknownConceptError: ("Concept Not Found", 404),
    ConceptSearchSyntaxError: ("Invalid Search Query", 400),
    WorldSidecarMissingError: ("Sidecar Missing", 409),
    ConceptSidecarMissingError: ("Sidecar Missing", 409),
}


@overload
def _overview_report(
    request: Request,
    *,
    wants_json: Literal[True],
) -> RepositoryOverviewReport | JSONResponse: ...


@overload
def _overview_report(
    request: Request,
    *,
    wants_json: Literal[False],
) -> RepositoryOverviewReport | HTMLResponse: ...


def _overview_report(
    request: Request,
    *,
    wants_json: bool,
) -> RepositoryOverviewReport | JSONResponse | HTMLResponse:
    try:
        render_policy = parse_render_policy_request(dict(request.query_params))
        repository_view = parse_repository_view_request(dict(request.query_params))
        report = build_repository_overview(
            _repo_from_request(request),
            RepositoryOverviewRequest(
                render_policy=render_policy,
                repository_view=repository_view,
            ),
        )
    except _EXPECTED_WEB_ERRORS as exc:
        return _expected_error_response(exc, wants_json=wants_json)
    return report


@overload
def _claim_report(
    claim_id: str,
    request: Request,
    *,
    wants_json: Literal[True],
) -> ClaimViewReport | JSONResponse: ...


@overload
def _claim_report(
    claim_id: str,
    request: Request,
    *,
    wants_json: Literal[False],
) -> ClaimViewReport | HTMLResponse: ...


def _claim_report(
    claim_id: str,
    request: Request,
    *,
    wants_json: bool,
) -> ClaimViewReport | JSONResponse | HTMLResponse:
    try:
        render_policy = parse_render_policy_request(dict(request.query_params))
        repository_view = parse_repository_view_request(dict(request.query_params))
        report = build_claim_view(
            _repo_from_request(request),
            ClaimViewRequest(
                claim_id=claim_id,
                render_policy=render_policy,
                repository_view=repository_view,
            ),
        )
    except _EXPECTED_WEB_ERRORS as exc:
        return _expected_error_response(exc, wants_json=wants_json)
    return report


@overload
def _concept_report(
    concept_id: str,
    request: Request,
    *,
    wants_json: Literal[True],
) -> ConceptViewReport | JSONResponse: ...


@overload
def _concept_report(
    concept_id: str,
    request: Request,
    *,
    wants_json: Literal[False],
) -> ConceptViewReport | HTMLResponse: ...


def _concept_report(
    concept_id: str,
    request: Request,
    *,
    wants_json: bool,
) -> ConceptViewReport | JSONResponse | HTMLResponse:
    try:
        render_policy = parse_render_policy_request(dict(request.query_params))
        repository_view = parse_repository_view_request(dict(request.query_params))
        report = build_concept_view(
            _repo_from_request(request),
            ConceptViewRequest(
                concept_id_or_name=concept_id,
                render_policy=render_policy,
                repository_view=repository_view,
            ),
        )
    except _EXPECTED_WEB_ERRORS as exc:
        return _expected_error_response(exc, wants_json=wants_json)
    return report


@overload
def _claims_report(
    request: Request,
    *,
    wants_json: Literal[True],
) -> ClaimSummaryReport | JSONResponse: ...


@overload
def _claims_report(
    request: Request,
    *,
    wants_json: Literal[False],
) -> ClaimSummaryReport | HTMLResponse: ...


def _claims_report(
    request: Request,
    *,
    wants_json: bool,
) -> ClaimSummaryReport | JSONResponse | HTMLResponse:
    try:
        render_policy = parse_render_policy_request(dict(request.query_params))
        repository_view = parse_repository_view_request(dict(request.query_params))
        concept = _optional_query(request, "concept")
        limit = _parse_limit(request.query_params.get("limit"))
        query = _optional_query(request, "q")
        repo = _repo_from_request(request)
        if query is None:
            report = list_claim_views(
                repo,
                ClaimListRequest(
                    render_policy=render_policy,
                    concept=concept,
                    limit=limit,
                    repository_view=repository_view,
                ),
            )
        else:
            report = search_claim_views(
                repo,
                ClaimSearchRequest(
                    query=query,
                    render_policy=render_policy,
                    concept=concept,
                    limit=limit,
                    repository_view=repository_view,
                ),
            )
    except _EXPECTED_WEB_ERRORS as exc:
        return _expected_error_response(exc, wants_json=wants_json)
    return report


@overload
def _neighborhood_report(
    claim_id: str,
    request: Request,
    *,
    wants_json: Literal[True],
) -> SemanticNeighborhoodReport | JSONResponse: ...


@overload
def _neighborhood_report(
    claim_id: str,
    request: Request,
    *,
    wants_json: Literal[False],
) -> SemanticNeighborhoodReport | HTMLResponse: ...


def _neighborhood_report(
    claim_id: str,
    request: Request,
    *,
    wants_json: bool,
) -> SemanticNeighborhoodReport | JSONResponse | HTMLResponse:
    try:
        render_policy = parse_render_policy_request(dict(request.query_params))
        repository_view = parse_repository_view_request(dict(request.query_params))
        limit = _parse_limit(request.query_params.get("limit"))
        report = build_semantic_neighborhood(
            _repo_from_request(request),
            SemanticNeighborhoodRequest(
                focus_kind="claim",
                focus_id=claim_id,
                render_policy=render_policy,
                repository_view=repository_view,
                limit=limit,
            ),
        )
    except _EXPECTED_WEB_ERRORS as exc:
        return _expected_error_response(exc, wants_json=wants_json)
    return report


@overload
def _concepts_report(
    request: Request,
    *,
    wants_json: Literal[True],
) -> ConceptListReport | ConceptSearchReport | JSONResponse: ...


@overload
def _concepts_report(
    request: Request,
    *,
    wants_json: Literal[False],
) -> ConceptListReport | ConceptSearchReport | HTMLResponse: ...


def _concepts_report(
    request: Request,
    *,
    wants_json: bool,
) -> ConceptListReport | ConceptSearchReport | JSONResponse | HTMLResponse:
    try:
        repository_view = parse_repository_view_request(dict(request.query_params))
        query = _optional_query(request, "q")
        domain = _optional_query(request, "domain")
        status = _optional_query(request, "status")
        limit = _parse_limit(request.query_params.get("limit"))
        repo = _repo_from_request(request)
        if query is None:
            report = list_concepts(
                repo,
                ConceptListRequest(
                    domain=domain,
                    status=status,
                    limit=limit,
                    repository_view=repository_view,
                ),
            )
        else:
            report = search_concepts(
                repo,
                ConceptSearchRequest(
                    query=query,
                    limit=limit,
                    repository_view=repository_view,
                ),
            )
    except _EXPECTED_WEB_ERRORS as exc:
        return _expected_error_response(exc, wants_json=wants_json)
    return report


def _parse_limit(value: str | None) -> int:
    if value is None:
        return 50
    try:
        limit = int(value)
    except ValueError:
        raise WebQueryParseError("limit must be an integer") from None
    if limit < 1 or limit > 500:
        raise WebQueryParseError("limit must be between 1 and 500")
    return limit


def _repo_from_request(request: Request) -> Repository:
    start = request.app.state.repository_root
    return Repository.find(start)


def _optional_query(request: Request, name: str) -> str | None:
    value = request.query_params.get(name)
    if value is None or value == "":
        return None
    return value


def _world_revision_request(request: Request) -> AppRevisionWorldRequest:
    reserved = {"context"}
    return AppRevisionWorldRequest(
        bindings={
            key: value
            for key, value in request.query_params.items()
            if key not in reserved
        },
        context=_optional_query(request, "context"),
    )


@overload
def _expected_error_response(
    exc: Exception,
    *,
    wants_json: Literal[True],
) -> JSONResponse: ...


@overload
def _expected_error_response(
    exc: Exception,
    *,
    wants_json: Literal[False],
) -> HTMLResponse: ...


def _expected_error_response(
    exc: Exception,
    *,
    wants_json: bool,
) -> JSONResponse | HTMLResponse:
    for error_type, (title, status_code) in _ERROR_RESPONSES.items():
        if isinstance(exc, error_type):
            return _error_response(title, str(exc), status_code, wants_json=wants_json)
    raise TypeError(f"unmapped expected web error: {type(exc).__name__}")


@overload
def _error_response(
    title: str,
    message: str,
    status_code: int,
    *,
    wants_json: Literal[True],
) -> JSONResponse: ...


@overload
def _error_response(
    title: str,
    message: str,
    status_code: int,
    *,
    wants_json: Literal[False],
) -> HTMLResponse: ...


def _error_response(
    title: str,
    message: str,
    status_code: int,
    *,
    wants_json: bool,
) -> JSONResponse | HTMLResponse:
    if wants_json:
        return JSONResponse(
            {
                "error": {
                    "title": title,
                    "message": message,
                    "status_code": status_code,
                }
            },
            status_code=status_code,
        )
    return HTMLResponse(
        render_error_page(title, message),
        status_code=status_code,
    )
