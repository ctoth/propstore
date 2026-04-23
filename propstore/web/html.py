"""HTML presenters for app reports."""

from __future__ import annotations

from html import escape
from urllib.parse import quote

from propstore.app.claim_views import ClaimViewReport
from propstore.app.neighborhoods import (
    SemanticEdge,
    SemanticMove,
    SemanticNeighborhoodReport,
    SemanticNeighborhoodRow,
    SemanticNode,
)


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


def render_neighborhood_page(report: SemanticNeighborhoodReport) -> str:
    title = f"Neighborhood for {report.focus.display_id} - propstore"
    claim_href = f"/claim/{quote(report.focus.focus_id, safe='')}"
    return _page(
        title,
        f"""
<h1>Neighborhood for {_text(report.focus.display_id)}</h1>
<section aria-labelledby="focus-heading">
  <h2 id="focus-heading">Focus</h2>
  <p>{_text(report.focus.sentence)}</p>
  {_dl([
      ("Focus kind", report.focus.kind),
      ("Focus ID", report.focus.focus_id),
      ("Status", f"{_state_label(report.status.state)}: {report.status.reason}"),
      ("Visible under policy", _bool_text(report.status.visible_under_policy)),
      ("Summary", report.prose_summary),
  ])}
  <p><a href="{_text(claim_href)}">Open claim view for this focus claim</a></p>
</section>
<section aria-labelledby="moves-heading">
  <h2 id="moves-heading">Available Moves</h2>
  {_moves_table(report.moves)}
</section>
<section aria-labelledby="supporters-heading">
  <h2 id="supporters-heading">Supporters</h2>
  {_rows_table(_section_rows(report, "supporters"))}
</section>
<section aria-labelledby="attackers-heading">
  <h2 id="attackers-heading">Attackers</h2>
  {_rows_table(_section_rows(report, "attackers"))}
</section>
<section aria-labelledby="conditions-heading">
  <h2 id="conditions-heading">Conditions</h2>
  {_rows_table(_section_rows(report, "conditions"))}
</section>
<section aria-labelledby="provenance-heading">
  <h2 id="provenance-heading">Provenance</h2>
  {_rows_table(_section_rows(report, "provenance"))}
</section>
<section aria-labelledby="shared-concept-heading">
  <h2 id="shared-concept-heading">Shared Concept</h2>
  {_rows_table(_section_rows(report, "shared_concept"))}
</section>
<section aria-labelledby="graph-heading">
  <h2 id="graph-heading">Raw Graph Projection</h2>
  {_edges_table(report.edges)}
  {_nodes_table(report.nodes)}
</section>
<section aria-labelledby="render-state-heading">
  <h2 id="render-state-heading">Render State</h2>
  {_dl([
      ("Reasoning backend", report.render_policy.reasoning_backend),
      ("Strategy", report.render_policy.strategy),
      ("Semantics", report.render_policy.semantics),
      ("Set comparison", report.render_policy.set_comparison),
      ("Include drafts", _bool_text(report.render_policy.include_drafts)),
      ("Include blocked", _bool_text(report.render_policy.include_blocked)),
      ("Show quarantined", _bool_text(report.render_policy.show_quarantined)),
  ])}
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


def _moves_table(moves: tuple[SemanticMove, ...]) -> str:
    return _table(
        ("Move", "State", "Count", "Sentence", "Targets"),
        [
            (
                move.kind.replace("_", " "),
                _state_label(move.state),
                str(move.target_count),
                move.sentence,
                ", ".join(move.target_ids) if move.target_ids else "none",
            )
            for move in moves
        ],
    )


def _rows_table(rows: tuple[SemanticNeighborhoodRow, ...]) -> str:
    return _table(
        ("Subject", "Relation", "Object", "State", "Sentence"),
        [
            (
                row.subject_id,
                row.relation,
                row.object_id,
                _state_label(row.state),
                row.sentence,
            )
            for row in rows
        ],
    )


def _edges_table(edges: tuple[SemanticEdge, ...]) -> str:
    return _table(
        ("Source", "Relation", "Target", "Sentence"),
        [
            (
                edge.source_id,
                edge.edge_kind,
                edge.target_id,
                edge.sentence,
            )
            for edge in edges
        ],
    )


def _nodes_table(nodes: tuple[SemanticNode, ...]) -> str:
    return _table(
        ("Kind", "Node ID", "Display ID", "Sentence"),
        [
            (
                node.kind,
                node.node_id,
                node.display_id,
                node.sentence,
            )
            for node in nodes
        ],
    )


def _table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    head = "".join(f"<th scope=\"col\">{_text(header)}</th>" for header in headers)
    body_rows = rows or (("none",) + ("not applicable",) * (len(headers) - 1),)
    body = "\n".join(
        "<tr>" + "".join(f"<td>{_text(cell)}</td>" for cell in row) + "</tr>"
        for row in body_rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>\n{body}\n</tbody></table>"


def _section_rows(
    report: SemanticNeighborhoodReport,
    section: str,
) -> tuple[SemanticNeighborhoodRow, ...]:
    return tuple(row for row in report.table_rows if row.section == section)


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
