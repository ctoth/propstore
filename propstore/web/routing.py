"""Route registration for the web adapter."""

from __future__ import annotations

from typing import Literal, overload

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from propstore.app.claim_views import (
    ClaimViewReport,
    ClaimViewRequest,
    ClaimViewUnknownClaimError,
    build_claim_view,
)
from propstore.app.neighborhoods import (
    SemanticNeighborhoodReport,
    SemanticNeighborhoodRequest,
    SemanticNeighborhoodUnsupportedFocusError,
    build_semantic_neighborhood,
)
from propstore.app.repository_views import RepositoryViewUnsupportedStateError
from propstore.app.rendering import RenderPolicyValidationError
from propstore.app.world import WorldSidecarMissingError
from propstore.repository import Repository
from propstore.web.html import (
    render_claim_page,
    render_error_page,
    render_neighborhood_page,
)
from propstore.web.requests import (
    parse_render_policy_request,
    parse_repository_view_request,
)
from propstore.web.serialization import to_json_compatible


def register_routes(app: FastAPI) -> None:
    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

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
    except ValueError as exc:
        return _error_response("Invalid Request", str(exc), 400, wants_json=wants_json)
    except RenderPolicyValidationError as exc:
        return _error_response("Invalid Render Policy", str(exc), 400, wants_json=wants_json)
    except RepositoryViewUnsupportedStateError as exc:
        return _error_response("Unsupported Repository State", str(exc), 400, wants_json=wants_json)
    except ClaimViewUnknownClaimError as exc:
        return _error_response("Claim Not Found", str(exc), 404, wants_json=wants_json)
    except WorldSidecarMissingError as exc:
        return _error_response("Sidecar Missing", str(exc), 409, wants_json=wants_json)
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
    except ValueError as exc:
        return _error_response("Invalid Request", str(exc), 400, wants_json=wants_json)
    except RenderPolicyValidationError as exc:
        return _error_response("Invalid Render Policy", str(exc), 400, wants_json=wants_json)
    except SemanticNeighborhoodUnsupportedFocusError as exc:
        return _error_response("Unsupported Focus", str(exc), 400, wants_json=wants_json)
    except RepositoryViewUnsupportedStateError as exc:
        return _error_response("Unsupported Repository State", str(exc), 400, wants_json=wants_json)
    except ClaimViewUnknownClaimError as exc:
        return _error_response("Claim Not Found", str(exc), 404, wants_json=wants_json)
    except WorldSidecarMissingError as exc:
        return _error_response("Sidecar Missing", str(exc), 409, wants_json=wants_json)
    return report


def _parse_limit(value: str | None) -> int:
    if value is None:
        return 50
    try:
        limit = int(value)
    except ValueError as exc:
        raise ValueError("limit must be an integer") from exc
    if limit < 1 or limit > 500:
        raise ValueError("limit must be between 1 and 500")
    return limit


def _repo_from_request(request: Request) -> Repository:
    start = request.app.state.repository_root
    return Repository.find(start)


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
