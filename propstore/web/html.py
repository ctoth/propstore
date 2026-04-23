"""HTML presenters for app reports."""

from __future__ import annotations

from html import escape
from urllib.parse import quote

from propstore.app.claim_views import ClaimViewReport


def render_claim_page(report: ClaimViewReport) -> str:
    title = f"{report.heading} - propstore"
    neighborhood_href = f"/claim/{quote(report.claim_id, safe='')}/neighborhood"
    return _page(
        title,
        f"""
<h1>{_text(report.heading)}</h1>
<section aria-labelledby="summary-heading">
  <h2 id="summary-heading">Summary</h2>
  {_dl([
      ("Status", f"{_state_label(report.status.state)}: {report.status.reason}"),
      ("Claim type", report.claim_type),
      ("Statement", report.statement or "missing"),
      ("Concept", _concept_text(report)),
      ("Value", report.value.sentence),
      ("Uncertainty", report.uncertainty.sentence),
      ("Condition regime", report.condition.sentence),
  ])}
</section>
<section aria-labelledby="render-state-heading">
  <h2 id="render-state-heading">Render State</h2>
  {_dl([
      ("Repository state", report.repository_state),
      ("Reasoning backend", report.render_policy.reasoning_backend),
      ("Strategy", report.render_policy.strategy),
      ("Semantics", report.render_policy.semantics),
      ("Set comparison", report.render_policy.set_comparison),
      ("Include drafts", _bool_text(report.render_policy.include_drafts)),
      ("Include blocked", _bool_text(report.render_policy.include_blocked)),
      ("Show quarantined", _bool_text(report.render_policy.show_quarantined)),
  ])}
</section>
<section aria-labelledby="provenance-heading">
  <h2 id="provenance-heading">Provenance</h2>
  {_dl([
      ("State", _state_label(report.provenance.state)),
      ("Source slug", report.provenance.source_slug or "missing"),
      ("Source ID", report.provenance.source_id or "missing"),
      ("Source kind", report.provenance.source_kind or "missing"),
      ("Paper", report.provenance.paper or "missing"),
      ("Page", "missing" if report.provenance.page is None else str(report.provenance.page)),
      ("Origin type", report.provenance.origin_type or "missing"),
      ("Origin value", report.provenance.origin_value or "missing"),
  ])}
</section>
<section aria-labelledby="neighborhood-heading">
  <h2 id="neighborhood-heading">Neighborhood</h2>
  <p><a href="{_text(neighborhood_href)}">Open semantic neighborhood for this claim</a></p>
</section>
<section aria-labelledby="machine-ids-heading">
  <h2 id="machine-ids-heading">Machine IDs</h2>
  {_dl([
      ("Claim ID", report.claim_id),
      ("Logical ID", report.logical_id or "missing"),
      ("Artifact ID", report.artifact_id or "missing"),
      ("Version ID", report.version_id or "missing"),
  ])}
</section>
""",
    )


def render_error_page(title: str, message: str) -> str:
    return _page(
        title,
        f"""
<h1>{_text(title)}</h1>
<section aria-labelledby="error-heading">
  <h2 id="error-heading">Error</h2>
  <p>{_text(message)}</p>
</section>
""",
    )


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>{_text(title)}</title>
    <link rel="stylesheet" href="/static/web.css">
  </head>
  <body>
    <main>
{body}
    </main>
  </body>
</html>
"""


def _dl(rows: list[tuple[str, str]]) -> str:
    content = "\n".join(
        f"    <dt>{_text(label)}</dt><dd>{_text(value)}</dd>"
        for label, value in rows
    )
    return f"<dl>\n{content}\n  </dl>"


def _concept_text(report: ClaimViewReport) -> str:
    if report.concept.state == "known":
        name = report.concept.canonical_name or "unknown"
        concept_id = report.concept.concept_id or "unknown"
        return f"{name} ({concept_id})"
    if report.concept.state == "not_applicable":
        return "not applicable"
    return _state_label(report.concept.state)


def _state_label(state: str) -> str:
    return state.replace("_", " ")


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _text(value: str) -> str:
    return escape(value, quote=True)
