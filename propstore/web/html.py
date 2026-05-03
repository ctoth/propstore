"""HTML presenters for app reports."""

from __future__ import annotations

from html import escape
from typing import NamedTuple
from urllib.parse import quote

from propstore.app.claim_views import ClaimSummaryReport, ClaimViewReport
from propstore.app.concepts import ConceptListReport, ConceptSearchReport
from propstore.app.concept_views import (
    ConceptClaimGroup,
    ConceptRelatedClaimLink,
    ConceptViewReport,
)
from propstore.app.neighborhoods import (
    SemanticEdge,
    SemanticMove,
    SemanticNeighborhoodReport,
    SemanticNeighborhoodRow,
    SemanticNode,
)
from propstore.app.rendering import RenderPolicySummary
from propstore.app.repository_overview import (
    InventoryRow,
    NotableConflicts,
    ProvenanceSummary,
    RecentActivity,
    RepositoryOverviewReport,
    SourcePointer,
)


class LinkRow(NamedTuple):
    link_text: str
    href: str
    cells: tuple[str, ...]


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
        LinkRow(
            entry.logical_id or entry.claim_id,
            f"/claim/{quote(entry.claim_id, safe='')}",
            (
                entry.concept_display,
                entry.claim_type,
                entry.value_display,
                entry.condition_display,
                entry.status_state.replace("_", " "),
            ),
        )
        for entry in report.entries
    ]
    return _page(
        title,
        f"""
<h1>Claims</h1>
{_filter_section(filter_rows)}
<section aria-labelledby="claims-heading">
  <h2 id="claims-heading">Claim Inventory</h2>
  {_link_table(
      ("Claim", "Concept(s)", "Type", "Value / Summary", "Conditions", "Status"),
      rows,
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
{_render_policy_section(report.render_policy, repository_state=report.repository_state)}
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
{_machine_ids_section([
      ("Claim ID", report.claim_id),
      ("Logical ID", report.logical_id or "missing"),
      ("Artifact ID", report.artifact_id or "missing"),
      ("Version ID", report.version_id or "missing"),
  ])}
""",
    )


def render_concept_page(report: ConceptViewReport) -> str:
    title = f"{report.heading} - propstore"
    return _page(
        title,
        f"""
<h1>{_text(report.heading)}</h1>
<section aria-labelledby="summary-heading">
  <h2 id="summary-heading">Summary</h2>
  {_dl([
      ("Status", f"{_state_label(report.status.state)}: {report.status.reason}"),
      ("Canonical name", report.canonical_name or "missing"),
      ("Definition", report.definition or "missing"),
      ("Domain", report.domain or "missing"),
      ("Kind", report.kind_type or "missing"),
      ("Form", f"{_state_label(report.form.state)}: {report.form.sentence}"),
  ])}
</section>
{_render_policy_section(report.render_policy, repository_state=report.repository_state)}
<section aria-labelledby="form-heading">
  <h2 id="form-heading">Form</h2>
  {_dl([
      ("State", _state_label(report.form.state)),
      ("Form name", report.form.form_name or "missing"),
      ("Unit", report.form.unit or "missing"),
      ("Range", report.form.range_text or "missing"),
      ("Sentence", report.form.sentence),
  ])}
</section>
<section aria-labelledby="value-heading">
  <h2 id="value-heading">Value Summary</h2>
  {_dl([
      ("State", _state_label(report.value_summary.state)),
      ("Claim count", str(report.value_summary.claim_count)),
      ("Unit", report.value_summary.unit or "missing"),
      ("Sentence", report.value_summary.sentence),
  ])}
</section>
<section aria-labelledby="uncertainty-heading">
  <h2 id="uncertainty-heading">Uncertainty</h2>
  {_dl([
      ("State", _state_label(report.uncertainty_summary.state)),
      ("Claim count", str(report.uncertainty_summary.claim_count)),
      ("Sentence", report.uncertainty_summary.sentence),
  ])}
</section>
<section aria-labelledby="provenance-heading">
  <h2 id="provenance-heading">Provenance</h2>
  {_dl([
      ("State", _state_label(report.provenance_summary.state)),
      ("Claim count", str(report.provenance_summary.claim_count)),
      ("Source count", str(report.provenance_summary.source_count)),
      ("Papers", ", ".join(report.provenance_summary.papers) or "none"),
      ("Sentence", report.provenance_summary.sentence),
  ])}
</section>
<section aria-labelledby="claims-heading">
  <h2 id="claims-heading">Claims By Type</h2>
  {_claim_groups(report.claim_groups)}
</section>
<section aria-labelledby="related-claims-heading">
  <h2 id="related-claims-heading">Related Claims</h2>
  {_related_claims_table(report.related_claim_links)}
</section>
{_machine_ids_section([
      ("Concept ID", report.concept_id),
      ("Logical ID", report.logical_id or "missing"),
      ("Artifact ID", report.artifact_id or "missing"),
      ("Version ID", report.version_id or "missing"),
  ])}
""",
    )


def render_index_page(report: RepositoryOverviewReport) -> str:
    title = "propstore"
    return _page(
        f"{title} - propstore",
        f"""
<h1>{_text(title)}</h1>
<p>{_text(report.prose_summary)}</p>
{_render_policy_section(report.render_policy, repository_state=report.repository_state)}
<section aria-labelledby="inventory-heading">
  <h2 id="inventory-heading">Inventory</h2>
  {_inventory_table(report.inventory_rows)}
</section>
<section aria-labelledby="sources-heading">
  <h2 id="sources-heading">Sources</h2>
  {_source_pointers_table(report.source_pointers)}
</section>
<section aria-labelledby="recent-activity-heading">
  <h2 id="recent-activity-heading">Recent Activity</h2>
  {_recent_activity_section(report.recent_activity)}
</section>
<section aria-labelledby="notable-conflicts-heading">
  <h2 id="notable-conflicts-heading">Notable Conflicts</h2>
  {_notable_conflicts_section(report.notable_conflicts)}
</section>
<section aria-labelledby="provenance-heading">
  <h2 id="provenance-heading">Provenance</h2>
  {_provenance_summary_section(report.provenance_summary)}
</section>
<section aria-labelledby="navigation-heading">
  <h2 id="navigation-heading">Navigation</h2>
  <ul>
    <li><a href="/claims">Open the claim inventory</a></li>
    <li><a href="/concepts">Open the concept inventory</a></li>
  </ul>
</section>
""",
    )


def _inventory_table(rows: tuple[InventoryRow, ...]) -> str:
    if not rows:
        return _table(
            ("Kind", "Count", "State", "Sentence"),
            [("none", "not applicable", "not applicable", "not applicable")],
        )
    link_rows: list[LinkRow] = []
    plain_rows: list[tuple[str, ...]] = []
    for row in rows:
        cells = (str(row.count), _state_label(row.state), row.sentence)
        if row.href is not None:
            link_rows.append(LinkRow(row.kind, row.href, cells))
        else:
            plain_rows.append((row.kind, *cells))
    if not plain_rows:
        return _link_table(
            ("Kind", "Count", "State", "Sentence"),
            link_rows,
        )
    if not link_rows:
        return _table(
            ("Kind", "Count", "State", "Sentence"),
            plain_rows,
        )
    head = "".join(
        f"<th scope=\"col\">{_text(header)}</th>"
        for header in ("Kind", "Count", "State", "Sentence")
    )
    body_lines: list[str] = []
    for link_row in link_rows:
        cells = [
            f"<td><a href=\"{_text(link_row.href)}\">{_text(link_row.link_text)}</a></td>"
        ]
        cells.extend(f"<td>{_text(cell)}</td>" for cell in link_row.cells)
        body_lines.append("<tr>" + "".join(cells) + "</tr>")
    for row_tuple in plain_rows:
        cells = [f"<td>{_text(cell)}</td>" for cell in row_tuple]
        body_lines.append("<tr>" + "".join(cells) + "</tr>")
    body = "\n".join(body_lines)
    return f"<table><thead><tr>{head}</tr></thead><tbody>\n{body}\n</tbody></table>"


def _source_pointers_table(pointers: tuple[SourcePointer, ...]) -> str:
    if not pointers:
        return "<p>No sources are present in this repository.</p>"
    rows: list[tuple[str, ...]] = []
    for pointer in pointers:
        identifier = pointer.source_id or pointer.slug or "unknown"
        rows.append(
            (
                identifier,
                pointer.kind or "missing",
                _state_label(pointer.state),
                pointer.sentence,
            )
        )
    return _table(
        ("Source", "Kind", "State", "Sentence"),
        rows,
    )


def _recent_activity_section(activity: RecentActivity) -> str:
    if activity.state != "known":
        return f"<p>{_text(activity.sentence)}</p>"
    rows = [(entry.when, entry.what) for entry in activity.entries]
    return f"""<p>{_text(activity.sentence)}</p>
{_table(("When", "What"), rows)}"""


def _notable_conflicts_section(conflicts: NotableConflicts) -> str:
    if conflicts.state != "known":
        return f"<p>{_text(conflicts.sentence)}</p>"
    rows = [(entry.claim_id, entry.sentence) for entry in conflicts.entries]
    return f"""<p>{_text(conflicts.sentence)}</p>
{_table(("Claim", "Sentence"), rows)}"""


def _provenance_summary_section(summary: ProvenanceSummary) -> str:
    if summary.state != "known":
        return f"<p>{_text(summary.sentence)}</p>"
    rows = [(entry.state, str(entry.count)) for entry in summary.counts]
    return f"""<p>{_text(summary.sentence)}</p>
{_table(("Provenance State", "Count"), rows)}"""


def render_error_page(title: str, message: str) -> str:
    return _page(
        f"{title} - propstore",
        f"""
<h1 id="error-heading">{_text(title)}</h1>
<section aria-labelledby="error-message-heading">
  <h2 id="error-message-heading">What happened</h2>
  <p>{_text(message)}</p>
  <p><a href="/claims">Open the claim index</a></p>
  <p><a href="/concepts">Search concepts</a></p>
</section>
""",
        main_labelledby="error-heading",
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
            LinkRow(
                entry.handle,
                f"/concept/{quote(entry.handle, safe='')}",
                (
                    entry.canonical_name,
                    entry.status or "missing",
                ),
            )
            for entry in report.entries
        ]
        table = _link_table(
            ("Handle", "Canonical Name", "Status"),
            rows,
        )
    else:
        rows = [
            LinkRow(
                hit.handle,
                f"/concept/{quote(hit.handle, safe='')}",
                (
                    hit.canonical_name,
                    hit.status or "missing",
                    hit.definition or "missing",
                ),
            )
            for hit in report.hits
        ]
        table = _link_table(
            ("Handle", "Canonical Name", "Status", "Definition"),
            rows,
        )
    return _page(
        title,
        f"""
<h1>Concepts</h1>
{_filter_section(filter_rows)}
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
{_render_policy_section(report.render_policy)}
""",
    )


def _page(title: str, body: str, *, main_labelledby: str | None = None) -> str:
    main_attrs = "" if main_labelledby is None else f" aria-labelledby=\"{_text(main_labelledby)}\""
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>{_text(title)}</title>
    <link rel="stylesheet" href="/static/web.css">
  </head>
  <body>
    <main{main_attrs}>
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


def _filter_section(rows: list[tuple[str, str]]) -> str:
    return f"""<section aria-labelledby="filters-heading">
  <h2 id="filters-heading">Filters</h2>
  {_dl(rows)}
</section>"""


def _status_text(state: str, reason: str) -> str:
    return f"{_state_label(state)}: {reason}"


def _render_policy_rows(summary: RenderPolicySummary) -> list[tuple[str, str]]:
    return [
        ("Reasoning backend", summary.reasoning_backend),
        ("Strategy", summary.strategy),
        ("Semantics", summary.semantics),
        ("Set comparison", summary.set_comparison),
        ("Include drafts", _bool_text(summary.include_drafts)),
        ("Include blocked", _bool_text(summary.include_blocked)),
        ("Show quarantined", _bool_text(summary.show_quarantined)),
    ]


def _render_policy_section(
    summary: RenderPolicySummary,
    *,
    repository_state: str | None = None,
) -> str:
    rows = _render_policy_rows(summary)
    if repository_state is not None:
        rows = [("Repository state", repository_state), *rows]
    return f"""<section aria-labelledby="render-state-heading">
  <h2 id="render-state-heading">Render State</h2>
  {_dl(rows)}
</section>"""


def _machine_ids_section(rows: list[tuple[str, str]]) -> str:
    return f"""<section aria-labelledby="machine-ids-heading">
  <h2 id="machine-ids-heading">Machine IDs</h2>
  {_dl(rows)}
</section>"""


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
    rows: list[LinkRow],
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
        if len(row.cells) != len(headers) - 1:
            raise ValueError(
                f"LinkRow has {len(row.cells) + 1} cells for {len(headers)} headers"
            )
        cells = [f"<td><a href=\"{_text(row.href)}\">{_text(row.link_text)}</a></td>"]
        cells.extend(f"<td>{_text(cell)}</td>" for cell in row.cells)
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    body = "\n".join(body_rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>\n{body}\n</tbody></table>"


def _section_rows(
    report: SemanticNeighborhoodReport,
    section: str,
) -> tuple[SemanticNeighborhoodRow, ...]:
    return tuple(row for row in report.table_rows if row.section == section)


def _claim_groups(groups: tuple[ConceptClaimGroup, ...]) -> str:
    if not groups:
        return "<p>No claim groups are available.</p>"
    sections: list[str] = []
    for group in groups:
        sections.append(
            "\n".join(
                [
                    f"<h3>{_text(group.claim_type)}</h3>",
                    f"<p>{_text(group.sentence)}</p>",
                    _link_table(
                        ("Claim", "Type", "Value", "Conditions", "Status", "Reason"),
                        [
                            LinkRow(
                                entry.logical_id or entry.claim_id,
                                f"/claim/{quote(entry.claim_id, safe='')}",
                                (
                                    entry.claim_type,
                                    entry.value_display,
                                    entry.condition_display,
                                    _state_label(entry.status_state),
                                    entry.status_reason,
                                ),
                            )
                            for entry in group.entries
                        ],
                    ),
                ]
            )
        )
    return "\n".join(sections)


def _related_claims_table(links: tuple[ConceptRelatedClaimLink, ...]) -> str:
    return _link_table(
        ("Claim", "Relation", "Sentence"),
        [
            LinkRow(
                link.logical_id or link.claim_id,
                f"/claim/{quote(link.claim_id, safe='')}",
                (
                    link.relation,
                    link.sentence,
                ),
            )
            for link in links
        ],
    )


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
