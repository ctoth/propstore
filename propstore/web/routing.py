"""Route registration for the web adapter."""

from __future__ import annotations

from typing import Literal, overload

from fastapi import FastAPI, Request
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
from propstore.app.concepts import (
    ConceptListReport,
    ConceptListRequest,
    ConceptSearchReport,
    ConceptSearchRequest,
    ConceptSearchSyntaxError,
    ConceptSidecarMissingError,
    list_concepts,
    search_concepts,
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
from propstore.app.world_revision import (
    AppRevisionWorldRequest,
    world_revision_base,
    world_revision_entrenchment,
)
from propstore.app.world import WorldSidecarMissingError
from propstore.repository import Repository
from propstore.web.html import (
    render_claim_index_page,
    render_claim_page,
    render_concept_page,
    render_concept_index_page,
    render_error_page,
    render_index_page,
    render_neighborhood_page,
)
from propstore.web.requests import (
    WebQueryParseError,
    parse_render_policy_request,
    parse_repository_view_request,
)
from propstore.web.serialization import to_json_compatible

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


def register_routes(app: FastAPI) -> None:
    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/index.json")
    def index_json(request: Request) -> JSONResponse:
        report_or_response = _overview_report(request, wants_json=True)
        if isinstance(report_or_response, JSONResponse):
            return report_or_response
        return JSONResponse(to_json_compatible(report_or_response))

    @app.get("/world/revision/base.json")
    def world_revision_base_json(request: Request) -> JSONResponse:
        try:
            app_request = _world_revision_request(request)
            repo = _repo_from_request(request)
            return JSONResponse(
                to_json_compatible(
                    {
                        "base": world_revision_base(repo, app_request),
                        "entrenchment": world_revision_entrenchment(repo, app_request),
                    }
                )
            )
        except _EXPECTED_WEB_ERRORS as exc:
            return _expected_error_response(exc, wants_json=True)

    @app.get("/")
    def index_html(request: Request) -> HTMLResponse:
        report_or_response = _overview_report(request, wants_json=False)
        if isinstance(report_or_response, HTMLResponse):
            return report_or_response
        return HTMLResponse(render_index_page(report_or_response))

    @app.get("/claims.json")
    def claims_json(request: Request) -> JSONResponse:
        report_or_response = _claims_report(request, wants_json=True)
        if isinstance(report_or_response, JSONResponse):
            return report_or_response
        return JSONResponse(to_json_compatible(report_or_response))

    @app.get("/claims")
    def claims_html(request: Request) -> HTMLResponse:
        report_or_response = _claims_report(request, wants_json=False)
        if isinstance(report_or_response, HTMLResponse):
            return report_or_response
        return HTMLResponse(
            render_claim_index_page(
                report_or_response,
                query=_optional_query(request, "q"),
                concept=_optional_query(request, "concept"),
            )
        )

    @app.get("/concepts.json")
    def concepts_json(request: Request) -> JSONResponse:
        report_or_response = _concepts_report(request, wants_json=True)
        if isinstance(report_or_response, JSONResponse):
            return report_or_response
        return JSONResponse(to_json_compatible(report_or_response))

    @app.get("/concepts")
    def concepts_html(request: Request) -> HTMLResponse:
        report_or_response = _concepts_report(request, wants_json=False)
        if isinstance(report_or_response, HTMLResponse):
            return report_or_response
        return HTMLResponse(
            render_concept_index_page(
                report_or_response,
                query=_optional_query(request, "q"),
                domain=_optional_query(request, "domain"),
                status=_optional_query(request, "status"),
            )
        )

    @app.get("/concept/{concept_id}.json")
    def concept_json(concept_id: str, request: Request) -> JSONResponse:
        report_or_response = _concept_report(concept_id, request, wants_json=True)
        if isinstance(report_or_response, JSONResponse):
            return report_or_response
        return JSONResponse(to_json_compatible(report_or_response))

    @app.get("/concept/{concept_id}")
    def concept_html(concept_id: str, request: Request) -> HTMLResponse:
        report_or_response = _concept_report(concept_id, request, wants_json=False)
        if isinstance(report_or_response, HTMLResponse):
            return report_or_response
        return HTMLResponse(render_concept_page(report_or_response))

    @app.get("/claim/{claim_id}.json")
    def claim_json(claim_id: str, request: Request) -> JSONResponse:
        report_or_response = _claim_report(claim_id, request, wants_json=True)
        if isinstance(report_or_response, JSONResponse):
            return report_or_response
        return JSONResponse(to_json_compatible(report_or_response))

    @app.get("/claim/{claim_id}/neighborhood.json")
    def neighborhood_json(claim_id: str, request: Request) -> JSONResponse:
        report_or_response = _neighborhood_report(claim_id, request, wants_json=True)
        if isinstance(report_or_response, JSONResponse):
            return report_or_response
        return JSONResponse(to_json_compatible(report_or_response))

    @app.get("/claim/{claim_id}/neighborhood")
    def neighborhood_html(claim_id: str, request: Request) -> HTMLResponse:
        report_or_response = _neighborhood_report(claim_id, request, wants_json=False)
        if isinstance(report_or_response, HTMLResponse):
            return report_or_response
        return HTMLResponse(render_neighborhood_page(report_or_response))

    @app.get("/claim/{claim_id}")
    def claim_html(claim_id: str, request: Request) -> HTMLResponse:
        report_or_response = _claim_report(claim_id, request, wants_json=False)
        if isinstance(report_or_response, HTMLResponse):
            return report_or_response
        return HTMLResponse(render_claim_page(report_or_response))


@overload
def _overview_report(
    request: Request,
    *,
    wants_json: Literal[True],
) -> RepositoryOverviewReport | JSONResponse:
    ...


@overload
def _overview_report(
    request: Request,
    *,
    wants_json: Literal[False],
) -> RepositoryOverviewReport | HTMLResponse:
    ...


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
) -> ClaimViewReport | JSONResponse:
    ...


@overload
def _claim_report(
    claim_id: str,
    request: Request,
    *,
    wants_json: Literal[False],
) -> ClaimViewReport | HTMLResponse:
    ...


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
) -> ConceptViewReport | JSONResponse:
    ...


@overload
def _concept_report(
    concept_id: str,
    request: Request,
    *,
    wants_json: Literal[False],
) -> ConceptViewReport | HTMLResponse:
    ...


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
) -> ClaimSummaryReport | JSONResponse:
    ...


@overload
def _claims_report(
    request: Request,
    *,
    wants_json: Literal[False],
) -> ClaimSummaryReport | HTMLResponse:
    ...


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
) -> SemanticNeighborhoodReport | JSONResponse:
    ...


@overload
def _neighborhood_report(
    claim_id: str,
    request: Request,
    *,
    wants_json: Literal[False],
) -> SemanticNeighborhoodReport | HTMLResponse:
    ...


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
) -> ConceptListReport | ConceptSearchReport | JSONResponse:
    ...


@overload
def _concepts_report(
    request: Request,
    *,
    wants_json: Literal[False],
) -> ConceptListReport | ConceptSearchReport | HTMLResponse:
    ...


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
) -> JSONResponse:
    ...


@overload
def _expected_error_response(
    exc: Exception,
    *,
    wants_json: Literal[False],
) -> HTMLResponse:
    ...


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
) -> JSONResponse:
    ...


@overload
def _error_response(
    title: str,
    message: str,
    status_code: int,
    *,
    wants_json: Literal[False],
) -> HTMLResponse:
    ...


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
