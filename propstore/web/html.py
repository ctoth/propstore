"""HTML presenters for app reports."""

from __future__ import annotations

from html import escape
from urllib.parse import quote

from propstore.app.claim_views import ClaimSummaryReport, ClaimViewReport
from propstore.app.concepts import ConceptListReport, ConceptSearchReport
from propstore.app.neighborhoods import (
    SemanticEdge,
    SemanticMove,
    SemanticNeighborhoodReport,
    SemanticNeighborhoodRow,
    SemanticNode,
)


def render_claim_index_page(
    report: ClaimSummaryReport,
    *,
    query: str | None,
    concept: str | None,
) -> str:
    title = "Claims - propstore"
    filter_rows = [
        ("Query", query or "none"),
        ("Concept filter", concept or "none"),
    ]
    rows = [
        (
            entry.logical_id or entry.claim_id,
            entry.concept_name or entry.concept_id or "missing",
            entry.claim_type,
            entry.value_display,
            entry.condition_display,
            entry.status_state.replace("_", " "),
            f"/claim/{quote(entry.claim_id, safe='')}",
        )
        for entry in report.entries
    ]
    return _page(
        title,
        f"""
<h1>Claims</h1>
<section aria-labelledby="filters-heading">
  <h2 id="filters-heading">Filters</h2>
  {_dl(filter_rows)}
</section>
<section aria-labelledby="claims-heading">
  <h2 id="claims-heading">Claim Inventory</h2>
  {_link_table(
      ("Claim", "Concept", "Type", "Value", "Conditions", "Status"),
      rows,
      link_column=0,
      href_column=6,
  )}
</section>
""",
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


def render_concept_index_page(
    report: ConceptListReport | ConceptSearchReport,
    *,
    query: str | None,
    domain: str | None,
    status: str | None,
) -> str:
    title = "Concepts - propstore"
    filter_rows = [
        ("Query", query or "none"),
        ("Domain filter", domain or "none"),
        ("Status filter", status or "none"),
    ]
    if isinstance(report, ConceptListReport):
        rows = [
            (
                entry.handle,
                entry.canonical_name,
                entry.status or "missing",
                f"/concept/{quote(entry.handle, safe='')}",
            )
            for entry in report.entries
        ]
        table = _link_table(
            ("Handle", "Canonical Name", "Status"),
            rows,
            link_column=0,
            href_column=3,
        )
    else:
        rows = [
            (
                hit.handle,
                hit.canonical_name,
                hit.status or "missing",
                hit.definition or "missing",
                f"/concept/{quote(hit.handle, safe='')}",
            )
            for hit in report.hits
        ]
        table = _link_table(
            ("Handle", "Canonical Name", "Status", "Definition"),
            rows,
            link_column=0,
            href_column=4,
        )
    return _page(
        title,
        f"""
<h1>Concepts</h1>
<section aria-labelledby="filters-heading">
  <h2 id="filters-heading">Filters</h2>
  {_dl(filter_rows)}
</section>
<section aria-labelledby="concepts-heading">
  <h2 id="concepts-heading">Concept Inventory</h2>
  {table}
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


def _link_table(
    headers: tuple[str, ...],
    rows: list[tuple[str, ...]],
    *,
    link_column: int,
    href_column: int,
) -> str:
    head = "".join(f"<th scope=\"col\">{_text(header)}</th>" for header in headers)
    if not rows:
        empty_row = tuple(
            "none" if index == 0 else "not applicable" for index in range(len(headers))
        )
        body = "<tr>" + "".join(f"<td>{_text(cell)}</td>" for cell in empty_row) + "</tr>"
        return f"<table><thead><tr>{head}</tr></thead><tbody>\n{body}\n</tbody></table>"

    body_rows: list[str] = []
    for row in rows:
        href = row[href_column]
        cells: list[str] = []
        visible_cells = [cell for index, cell in enumerate(row) if index != href_column]
        for index, cell in enumerate(visible_cells):
            if index == link_column:
                cells.append(f"<td><a href=\"{_text(href)}\">{_text(cell)}</a></td>")
            else:
                cells.append(f"<td>{_text(cell)}</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    body = "\n".join(body_rows)
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
