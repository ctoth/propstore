"""Route registration for the web adapter."""

from __future__ import annotations

from typing import Literal, overload

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from propstore.app.claim_views import (
    ClaimViewReport,
    ClaimViewRequest,
    ClaimViewUnknownClaimError,
    ClaimViewUnsupportedStateError,
    build_claim_view,
)
from propstore.app.rendering import RenderPolicyValidationError
from propstore.app.world import WorldSidecarMissingError
from propstore.repository import Repository
from propstore.web.html import render_claim_page, render_error_page
from propstore.web.requests import parse_render_policy_request
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
        report = build_claim_view(
            _repo_from_request(request),
            ClaimViewRequest(
                claim_id=claim_id,
                render_policy=render_policy,
                branch=request.query_params.get("branch"),
                revision=request.query_params.get("rev"),
            ),
        )
    except ValueError as exc:
        return _error_response("Invalid Request", str(exc), 400, wants_json=wants_json)
    except RenderPolicyValidationError as exc:
        return _error_response("Invalid Render Policy", str(exc), 400, wants_json=wants_json)
    except ClaimViewUnsupportedStateError as exc:
        return _error_response("Unsupported Repository State", str(exc), 400, wants_json=wants_json)
    except ClaimViewUnknownClaimError as exc:
        return _error_response("Claim Not Found", str(exc), 404, wants_json=wants_json)
    except WorldSidecarMissingError as exc:
        return _error_response("Sidecar Missing", str(exc), 409, wants_json=wants_json)
    return report


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
