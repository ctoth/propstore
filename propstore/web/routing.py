"""Route registration for the read-only web adapter.

Each route is a thin shell: parse the query parameters into a typed app request
(render policy via :func:`propstore.app.rendering.build_render_policy`), open the
world through :func:`propstore.app.world.open_app_world_model`, call the matching
Phase-10-0 owner-layer view-builder, and render the returned typed report as JSON
(:func:`propstore.reporting.json_ready`) or accessible HTML. The router holds no
domain logic; expected owner/parse failures map to HTTP 400/404/409.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from propstore.app.claim_views import (
    ClaimViewBlockedError,
    ClaimViewReport,
    ClaimViewUnknownClaimError,
    build_claim_view,
)
from propstore.app.claims import (
    ClaimSummaryReport,
    list_claim_views,
    search_claim_views,
)
from propstore.app.concept_views import (
    ConceptViewReport,
    ConceptViewUnknownConceptError,
    build_concept_view,
)
from propstore.app.concepts import (
    ConceptListReport,
    ConceptSearchReport,
    ConceptSearchSyntaxError,
    list_concepts,
    search_concepts,
)
from propstore.app.neighborhoods import (
    SemanticNeighborhoodReport,
    SemanticNeighborhoodUnsupportedFocusError,
    build_semantic_neighborhood,
)
from propstore.app.rendering import (
    RenderPolicyValidationError,
    build_render_policy,
)
from propstore.app.repository_overview import (
    RepositoryOverviewReport,
    build_repository_overview,
)
from propstore.app.world import WorldSidecarMissingError, open_app_world_model
from propstore.reporting import json_ready
from propstore.repository import Repository
from propstore.support_revision.workflows import (
    RevisionWorldRequest,
    revision_base,
    revision_entrenchment,
)
from propstore.web.html import (
    render_claim_index_page,
    render_claim_page,
    render_concept_index_page,
    render_concept_page,
    render_error_page,
    render_index_page,
    render_neighborhood_page,
)
from propstore.web.requests import (
    WebQueryParseError,
    parse_render_policy_request,
)
from propstore.world import RenderPolicy

_EXPECTED_WEB_ERRORS = (
    WebQueryParseError,
    RenderPolicyValidationError,
    ClaimViewUnknownClaimError,
    ClaimViewBlockedError,
    ConceptViewUnknownConceptError,
    ConceptSearchSyntaxError,
    SemanticNeighborhoodUnsupportedFocusError,
    WorldSidecarMissingError,
)

_ERROR_RESPONSES: dict[type[Exception], tuple[str, int]] = {
    WebQueryParseError: ("Invalid Request", 400),
    RenderPolicyValidationError: ("Invalid Render Policy", 400),
    SemanticNeighborhoodUnsupportedFocusError: ("Unsupported Focus", 400),
    ConceptSearchSyntaxError: ("Invalid Search Query", 400),
    ClaimViewUnknownClaimError: ("Claim Not Found", 404),
    ClaimViewBlockedError: ("Not Found", 404),
    ConceptViewUnknownConceptError: ("Concept Not Found", 404),
    WorldSidecarMissingError: ("Sidecar Missing", 409),
}


def register_routes(app: FastAPI) -> None:
    """Register every read-only route on ``app``.

    Module-level handlers (registered via :meth:`FastAPI.add_api_route`) keep the
    handlers referenced and individually type-checkable rather than closures the
    strict checker would flag as unused.
    """

    app.add_api_route("/healthz", healthz, include_in_schema=False)
    app.add_api_route("/index.json", index_json, methods=["GET"])
    app.add_api_route("/", index_html, methods=["GET"])
    app.add_api_route(
        "/world/revision/base.json", world_revision_base_json, methods=["GET"]
    )
    app.add_api_route("/claims.json", claims_json, methods=["GET"])
    app.add_api_route("/claims", claims_html, methods=["GET"])
    app.add_api_route("/concepts.json", concepts_json, methods=["GET"])
    app.add_api_route("/concepts", concepts_html, methods=["GET"])
    app.add_api_route("/concept/{concept_id}.json", concept_json, methods=["GET"])
    app.add_api_route("/concept/{concept_id}", concept_html, methods=["GET"])
    app.add_api_route("/claim/{claim_id}.json", claim_json, methods=["GET"])
    app.add_api_route(
        "/claim/{claim_id}/neighborhood.json", neighborhood_json, methods=["GET"]
    )
    app.add_api_route(
        "/claim/{claim_id}/neighborhood", neighborhood_html, methods=["GET"]
    )
    app.add_api_route(
        "/claim/{claim_id}/similar.json", claim_similar_json, methods=["GET"]
    )
    app.add_api_route(
        "/concept/{concept_id}/similar.json", concept_similar_json, methods=["GET"]
    )
    app.add_api_route("/claim/{claim_id}", claim_html, methods=["GET"])


# ── route handlers ───────────────────────────────────────────────────────────


def healthz() -> dict[str, str]:
    return {"status": "ok"}


def index_json(request: Request) -> Response:
    try:
        report = _overview_report(request)
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=True)
    return JSONResponse(json_ready(report))


def index_html(request: Request) -> Response:
    try:
        report = _overview_report(request)
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=False)
    return HTMLResponse(render_index_page(report))


def world_revision_base_json(request: Request) -> Response:
    try:
        revision_request = _revision_request(request)
        with open_app_world_model(_repo(request)) as world:
            payload = {
                "base": revision_base(world, revision_request),
                "entrenchment": revision_entrenchment(world, revision_request),
            }
            return JSONResponse(json_ready(payload))
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=True)


def claims_json(request: Request) -> Response:
    try:
        report = _claims_report(request)
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=True)
    return JSONResponse(json_ready(report))


def claims_html(request: Request) -> Response:
    try:
        report = _claims_report(request)
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=False)
    return HTMLResponse(
        render_claim_index_page(
            report,
            query=_optional(request, "q"),
            concept=_optional(request, "concept"),
        )
    )


def concepts_json(request: Request) -> Response:
    try:
        report = _concepts_report(request)
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=True)
    return JSONResponse(json_ready(report))


def concepts_html(request: Request) -> Response:
    try:
        report = _concepts_report(request)
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=False)
    return HTMLResponse(
        render_concept_index_page(
            report,
            query=_optional(request, "q"),
            domain=_optional(request, "domain"),
            status=_optional(request, "status"),
        )
    )


def concept_json(concept_id: str, request: Request) -> Response:
    try:
        report = _concept_report(concept_id, request)
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=True)
    return JSONResponse(json_ready(report))


def concept_html(concept_id: str, request: Request) -> Response:
    try:
        report = _concept_report(concept_id, request)
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=False)
    return HTMLResponse(render_concept_page(report))


def claim_json(claim_id: str, request: Request) -> Response:
    try:
        report = _claim_report(claim_id, request)
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=True)
    return JSONResponse(json_ready(report))


def neighborhood_json(claim_id: str, request: Request) -> Response:
    try:
        report = _neighborhood_report(claim_id, request)
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=True)
    return JSONResponse(json_ready(report))


def neighborhood_html(claim_id: str, request: Request) -> Response:
    try:
        report = _neighborhood_report(claim_id, request)
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=False)
    return HTMLResponse(render_neighborhood_page(report))


def claim_html(claim_id: str, request: Request) -> Response:
    try:
        report = _claim_report(claim_id, request)
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=False)
    return HTMLResponse(render_claim_page(report))


def claim_similar_json(claim_id: str, request: Request) -> Response:
    try:
        payload = _similar_claims_payload(claim_id, request)
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=True)
    return JSONResponse(json_ready(payload))


def concept_similar_json(concept_id: str, request: Request) -> Response:
    try:
        payload = _similar_concepts_payload(concept_id, request)
    except _EXPECTED_WEB_ERRORS as exc:
        return _error_response(exc, wants_json=True)
    return JSONResponse(json_ready(payload))


# ── report builders (open world, call owner view-builder) ────────────────────


def _overview_report(request: Request) -> RepositoryOverviewReport:
    policy = _policy(request)
    with open_app_world_model(_repo(request)) as world:
        return build_repository_overview(world, policy=policy)


def _claim_report(claim_id: str, request: Request) -> ClaimViewReport:
    policy = _policy(request)
    with open_app_world_model(_repo(request)) as world:
        return build_claim_view(world, claim_id, policy=policy)


def _concept_report(concept_id: str, request: Request) -> ConceptViewReport:
    policy = _policy(request)
    with open_app_world_model(_repo(request)) as world:
        return build_concept_view(world, concept_id, policy=policy)


def _claims_report(request: Request) -> ClaimSummaryReport:
    policy = _policy(request)
    concept = _optional(request, "concept")
    limit = _parse_limit(request.query_params.get("limit"))
    query = _optional(request, "q")
    with open_app_world_model(_repo(request)) as world:
        if query is None:
            return list_claim_views(world, policy=policy, concept=concept, limit=limit)
        return search_claim_views(
            world, query, policy=policy, concept=concept, limit=limit
        )


def _concepts_report(request: Request) -> ConceptListReport | ConceptSearchReport:
    policy = _policy(request)
    limit = _parse_limit(request.query_params.get("limit"))
    query = _optional(request, "q")
    with open_app_world_model(_repo(request)) as world:
        if query is None:
            return list_concepts(world, policy=policy, limit=limit)
        return search_concepts(world, query, policy=policy, limit=limit)


def _neighborhood_report(
    claim_id: str, request: Request
) -> SemanticNeighborhoodReport:
    policy = _policy(request)
    limit = _parse_limit(request.query_params.get("limit"))
    with open_app_world_model(_repo(request)) as world:
        return build_semantic_neighborhood(
            world, "claim", claim_id, policy=policy, limit=limit
        )


def _similar_claims_payload(claim_id: str, request: Request) -> dict[str, Any]:
    model = _optional(request, "model")
    top_k = _parse_limit(request.query_params.get("limit"))
    with open_app_world_model(_repo(request)) as world:
        hits = world.similar_claims(claim_id, model_name=model, top_k=top_k)
    return {
        "claim_id": claim_id,
        "model": model,
        "hits": [
            {
                "claim_id": str(hit.claim_id),
                "distance": hit.distance,
                "statement": hit.statement,
                "concept_id": None if hit.concept_id is None else str(hit.concept_id),
            }
            for hit in hits
        ],
    }


def _similar_concepts_payload(concept_id: str, request: Request) -> dict[str, Any]:
    model = _optional(request, "model")
    top_k = _parse_limit(request.query_params.get("limit"))
    with open_app_world_model(_repo(request)) as world:
        hits = world.similar_concepts(concept_id, model_name=model, top_k=top_k)
    return {
        "concept_id": concept_id,
        "model": model,
        "hits": [
            {
                "concept_id": str(hit.concept_id),
                "distance": hit.distance,
                "canonical_name": hit.canonical_name,
            }
            for hit in hits
        ],
    }


# ── request parsing helpers ──────────────────────────────────────────────────


def _policy(request: Request) -> RenderPolicy:
    return build_render_policy(parse_render_policy_request(dict(request.query_params)))


def _revision_request(request: Request) -> RevisionWorldRequest:
    reserved = {"context"}
    bindings = {
        key: value
        for key, value in request.query_params.items()
        if key not in reserved
    }
    return RevisionWorldRequest(
        bindings=bindings,
        context_id=_optional(request, "context"),
    )


def _repo(request: Request) -> Repository:
    return Repository.find(request.app.state.repository_root)


def _optional(request: Request, name: str) -> str | None:
    value = request.query_params.get(name)
    if value is None or value == "":
        return None
    return value


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


def _error_response(exc: Exception, *, wants_json: bool) -> Response:
    title, status_code = _resolve_error(exc)
    if wants_json:
        return JSONResponse(
            {
                "error": {
                    "title": title,
                    "message": str(exc),
                    "status_code": status_code,
                }
            },
            status_code=status_code,
        )
    return HTMLResponse(
        render_error_page(title, str(exc)),
        status_code=status_code,
    )


def _resolve_error(exc: Exception) -> tuple[str, int]:
    for error_type, response in _ERROR_RESPONSES.items():
        if isinstance(exc, error_type):
            return response
    raise TypeError(f"unmapped expected web error: {type(exc).__name__}")
