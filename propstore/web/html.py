"""HTML presenters for app reports."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

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

_TEMPLATE_DIR = Path(__file__).with_name("templates")
_TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(("html",)),
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
    body = _template(
        "pages/claim_index.html",
        filters=_filter_section(
            [
                ("Query", query or "none"),
                ("Concept filter", concept or "none"),
            ]
        ),
        table=_link_table(
            ("Claim", "Concept(s)", "Type", "Value / Summary", "Conditions", "Status"),
            rows,
        ),
    )
    return _page("Claims - propstore", body)


def render_claim_page(report: ClaimViewReport) -> str:
    neighborhood_href = f"/claim/{quote(report.claim_id, safe='')}/neighborhood"
    body = _template(
        "pages/claim.html",
        heading=report.heading,
        summary=_dl(
            [
                ("Status", _status_text(report.status.state, report.status.reason)),
                ("Claim type", report.claim_type),
                ("Statement", report.statement or "missing"),
                ("Concept", _concept_text(report)),
                ("Value", report.value.sentence),
                ("Uncertainty", report.uncertainty.sentence),
                ("Condition regime", report.condition.sentence),
            ]
        ),
        render_policy=_render_policy_section(
            report.render_policy,
            repository_state=report.repository_state,
        ),
        provenance=_dl(
            [
                ("State", _state_label(report.provenance.state)),
                ("Source slug", report.provenance.source_slug or "missing"),
                ("Source ID", report.provenance.source_id or "missing"),
                ("Source kind", report.provenance.source_kind or "missing"),
                ("Paper", report.provenance.paper or "missing"),
                (
                    "Page",
                    "missing"
                    if report.provenance.page is None
                    else str(report.provenance.page),
                ),
                ("Origin type", report.provenance.origin_type or "missing"),
                ("Origin value", report.provenance.origin_value or "missing"),
            ]
        ),
        neighborhood_href=neighborhood_href,
        machine_ids=_machine_ids_section(
            [
                ("Claim ID", report.claim_id),
                ("Logical ID", report.logical_id or "missing"),
                ("Artifact ID", report.artifact_id or "missing"),
                ("Version ID", report.version_id or "missing"),
            ]
        ),
    )
    return _page(f"{report.heading} - propstore", body)


def render_concept_page(report: ConceptViewReport) -> str:
    body = _template(
        "pages/concept.html",
        heading=report.heading,
        summary=_dl(
            [
                ("Status", _status_text(report.status.state, report.status.reason)),
                ("Canonical name", report.canonical_name or "missing"),
                ("Definition", report.definition or "missing"),
                ("Domain", report.domain or "missing"),
                ("Kind", report.kind_type or "missing"),
                ("Form", _status_text(report.form.state, report.form.sentence)),
            ]
        ),
        render_policy=_render_policy_section(
            report.render_policy,
            repository_state=report.repository_state,
        ),
        form=_dl(
            [
                ("State", _state_label(report.form.state)),
                ("Form name", report.form.form_name or "missing"),
                ("Unit", report.form.unit or "missing"),
                ("Range", report.form.range_text or "missing"),
                ("Sentence", report.form.sentence),
            ]
        ),
        value_summary=_dl(
            [
                ("State", _state_label(report.value_summary.state)),
                ("Claim count", str(report.value_summary.claim_count)),
                ("Unit", report.value_summary.unit or "missing"),
                ("Sentence", report.value_summary.sentence),
            ]
        ),
        uncertainty=_dl(
            [
                ("State", _state_label(report.uncertainty_summary.state)),
                ("Claim count", str(report.uncertainty_summary.claim_count)),
                ("Sentence", report.uncertainty_summary.sentence),
            ]
        ),
        provenance=_dl(
            [
                ("State", _state_label(report.provenance_summary.state)),
                ("Claim count", str(report.provenance_summary.claim_count)),
                ("Source count", str(report.provenance_summary.source_count)),
                ("Papers", ", ".join(report.provenance_summary.papers) or "none"),
                ("Sentence", report.provenance_summary.sentence),
            ]
        ),
        claim_groups=_claim_groups(report.claim_groups),
        related_claims=_related_claims_table(report.related_claim_links),
        machine_ids=_machine_ids_section(
            [
                ("Concept ID", report.concept_id),
                ("Logical ID", report.logical_id or "missing"),
                ("Artifact ID", report.artifact_id or "missing"),
                ("Version ID", report.version_id or "missing"),
            ]
        ),
    )
    return _page(f"{report.heading} - propstore", body)


def render_index_page(report: RepositoryOverviewReport) -> str:
    title = "propstore"
    body = _template(
        "pages/index.html",
        heading=title,
        summary=report.prose_summary,
        render_policy=_render_policy_section(
            report.render_policy,
            repository_state=report.repository_state,
        ),
        inventory=_inventory_table(report.inventory_rows),
        sources=_source_pointers_table(report.source_pointers),
        recent_activity=_recent_activity_section(report.recent_activity),
        notable_conflicts=_notable_conflicts_section(report.notable_conflicts),
        provenance=_provenance_summary_section(report.provenance_summary),
    )
    return _page(f"{title} - propstore", body)


def render_error_page(title: str, message: str) -> str:
    body = _template("pages/error.html", heading=title, message=message)
    return _page(f"{title} - propstore", body, main_labelledby="error-heading")


def render_concept_index_page(
    report: ConceptListReport | ConceptSearchReport,
    *,
    query: str | None,
    domain: str | None,
    status: str | None,
) -> str:
    if isinstance(report, ConceptListReport):
        rows = [
            LinkRow(
                entry.handle,
                f"/concept/{quote(entry.handle, safe='')}",
                (entry.canonical_name, entry.status or "missing"),
            )
            for entry in report.entries
        ]
        table = _link_table(("Handle", "Canonical Name", "Status"), rows)
    else:
        rows = [
            LinkRow(
                hit.handle,
                f"/concept/{quote(hit.handle, safe='')}",
                (hit.canonical_name, hit.status or "missing", hit.definition or "missing"),
            )
            for hit in report.hits
        ]
        table = _link_table(("Handle", "Canonical Name", "Status", "Definition"), rows)
    body = _template(
        "pages/concept_index.html",
        filters=_filter_section(
            [
                ("Query", query or "none"),
                ("Domain filter", domain or "none"),
                ("Status filter", status or "none"),
            ]
        ),
        table=table,
    )
    return _page("Concepts - propstore", body)


def render_neighborhood_page(report: SemanticNeighborhoodReport) -> str:
    claim_href = f"/claim/{quote(report.focus.focus_id, safe='')}"
    body = _template(
        "pages/neighborhood.html",
        display_id=report.focus.display_id,
        focus_sentence=report.focus.sentence,
        focus=_dl(
            [
                ("Focus kind", report.focus.kind),
                ("Focus ID", report.focus.focus_id),
                ("Status", _status_text(report.status.state, report.status.reason)),
                (
                    "Visible under policy",
                    _bool_text(report.status.visible_under_policy),
                ),
                ("Summary", report.prose_summary),
            ]
        ),
        claim_href=claim_href,
        moves=_moves_table(report.moves),
        supporters=_rows_table(_section_rows(report, "supporters")),
        attackers=_rows_table(_section_rows(report, "attackers")),
        conditions=_rows_table(_section_rows(report, "conditions")),
        provenance=_rows_table(_section_rows(report, "provenance")),
        shared_concept=_rows_table(_section_rows(report, "shared_concept")),
        edges=_edges_table(report.edges),
        nodes=_nodes_table(report.nodes),
        render_policy=_render_policy_section(report.render_policy),
    )
    return _page(f"Neighborhood for {report.focus.display_id} - propstore", body)


def _inventory_table(rows: tuple[InventoryRow, ...]) -> str:
    if not rows:
        return _table(
            ("Kind", "Count", "State", "Sentence"),
            [("none", "not applicable", "not applicable", "not applicable")],
        )
    mixed_rows: list[Markup] = []
    for row in rows:
        cells = (str(row.count), _state_label(row.state), row.sentence)
        if row.href is not None:
            mixed_rows.append(_link_row(row.kind, row.href, cells))
        else:
            mixed_rows.append(_plain_row((row.kind, *cells)))
    return _table_from_body(("Kind", "Count", "State", "Sentence"), mixed_rows)


def _source_pointers_table(pointers: tuple[SourcePointer, ...]) -> str:
    if not pointers:
        return _template(
            "components/message.html",
            sentence="No sources are present in this repository.",
        )
    return _table(
        ("Source", "Kind", "State", "Sentence"),
        [
            (
                pointer.source_id or pointer.slug or "unknown",
                pointer.kind or "missing",
                _state_label(pointer.state),
                pointer.sentence,
            )
            for pointer in pointers
        ],
    )


def _recent_activity_section(activity: RecentActivity) -> str:
    if activity.state != "known":
        return _template("components/message.html", sentence=activity.sentence)
    return _join_fragments(
        [
            _template("components/message.html", sentence=activity.sentence),
            _table(("When", "What"), [(entry.when, entry.what) for entry in activity.entries]),
        ]
    )


def _notable_conflicts_section(conflicts: NotableConflicts) -> str:
    if conflicts.state != "known":
        return _template("components/message.html", sentence=conflicts.sentence)
    return _join_fragments(
        [
            _template("components/message.html", sentence=conflicts.sentence),
            _table(
                ("Claim", "Sentence"),
                [(entry.claim_id, entry.sentence) for entry in conflicts.entries],
            ),
        ]
    )


def _provenance_summary_section(summary: ProvenanceSummary) -> str:
    if summary.state != "known":
        return _template("components/message.html", sentence=summary.sentence)
    return _join_fragments(
        [
            _template("components/message.html", sentence=summary.sentence),
            _table(
                ("Provenance State", "Count"),
                [(entry.state, str(entry.count)) for entry in summary.counts],
            ),
        ]
    )


def _page(title: str, body: str, *, main_labelledby: str | None = None) -> str:
    main_attrs = (
        Markup("")
        if main_labelledby is None
        else Markup(f' aria-labelledby="{_text(main_labelledby)}"')
    )
    return str(_template("layout.html", title=title, body=Markup(body), main_attrs=main_attrs))


def _dl(rows: list[tuple[str, str]]) -> str:
    rendered_rows = [
        _template("components/definition_row.html", label=label, value=value)
        for label, value in rows
    ]
    return _template("components/definition_list.html", rows=_join_fragments(rendered_rows))


def _filter_section(rows: list[tuple[str, str]]) -> str:
    return _template("components/filter_section.html", rows=_dl(rows))


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
    return _template("components/render_policy_section.html", rows=_dl(rows))


def _machine_ids_section(rows: list[tuple[str, str]]) -> str:
    return _template("components/machine_ids_section.html", rows=_dl(rows))


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
        [(edge.source_id, edge.edge_kind, edge.target_id, edge.sentence) for edge in edges],
    )


def _nodes_table(nodes: tuple[SemanticNode, ...]) -> str:
    return _table(
        ("Kind", "Node ID", "Display ID", "Sentence"),
        [(node.kind, node.node_id, node.display_id, node.sentence) for node in nodes],
    )


def _table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    body_rows = rows or (("none",) + ("not applicable",) * (len(headers) - 1),)
    return _table_from_body(headers, [_plain_row(row) for row in body_rows])


def _link_table(headers: tuple[str, ...], rows: list[LinkRow]) -> str:
    if not rows:
        empty_row = tuple(
            "none" if index == 0 else "not applicable" for index in range(len(headers))
        )
        return _table_from_body(headers, [_plain_row(empty_row)])
    rendered_rows = []
    for row in rows:
        if len(row.cells) != len(headers) - 1:
            raise ValueError(
                f"LinkRow has {len(row.cells) + 1} cells for {len(headers)} headers"
            )
        rendered_rows.append(_link_row(row.link_text, row.href, row.cells))
    return _table_from_body(headers, rendered_rows)


def _table_from_body(headers: tuple[str, ...], rows: list[Markup]) -> str:
    head = _join_fragments(
        [_template("components/table_header.html", header=header) for header in headers]
    )
    return _template(
        "components/table.html",
        head=head,
        body=_join_fragments(rows),
    )


def _plain_row(cells: tuple[str, ...]) -> Markup:
    return _template(
        "components/table_row.html",
        cells=_join_fragments(
            [_template("components/table_cell.html", cell=cell) for cell in cells]
        ),
    )


def _link_row(link_text: str, href: str, cells: tuple[str, ...]) -> Markup:
    rendered_cells = [
        _template("components/link_table_cell.html", href=href, text=link_text),
        *[_template("components/table_cell.html", cell=cell) for cell in cells],
    ]
    return _template("components/table_row.html", cells=_join_fragments(rendered_cells))


def _section_rows(
    report: SemanticNeighborhoodReport,
    section: str,
) -> tuple[SemanticNeighborhoodRow, ...]:
    return tuple(row for row in report.table_rows if row.section == section)


def _claim_groups(groups: tuple[ConceptClaimGroup, ...]) -> str:
    if not groups:
        return _template(
            "components/message.html",
            sentence="No claim groups are available.",
        )
    return _join_fragments(
        [
            _template(
                "components/claim_group.html",
                heading=group.claim_type,
                sentence=group.sentence,
                table=_link_table(
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
            )
            for group in groups
        ]
    )


def _related_claims_table(links: tuple[ConceptRelatedClaimLink, ...]) -> str:
    return _link_table(
        ("Claim", "Relation", "Sentence"),
        [
            LinkRow(
                link.logical_id or link.claim_id,
                f"/claim/{quote(link.claim_id, safe='')}",
                (link.relation, link.sentence),
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
    return str(escape(value))


def _join_fragments(fragments: Sequence[str | Markup]) -> Markup:
    return Markup("\n").join(Markup(fragment) for fragment in fragments)


def _template(name: str, **context: str | Markup) -> Markup:
    return Markup(_TEMPLATE_ENV.get_template(name).render(**context))
