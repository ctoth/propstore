# App Contracts

## Goal

Make concept reading consume app-owned typed reports instead of reusing the
current YAML-rendering surface.

This workstream also fixes the current repository-view mismatch before adding
the concept page as another reader.

## Contract 0 - Shared Repository View State

### Problem

Current reading surfaces are inconsistent:

- `ClaimViewRequest` carries `branch` and `revision` fields but rejects them;
- `SemanticNeighborhoodRequest` carries `branch`, `revision`, and `bindings`,
  but the current implementation does not converge those fields into a shared
  owner-layer repository-view contract;
- a concept page must not add a third variant.

### Target

Add a shared app-owned repository reading contract:

```text
propstore/app/repository_views.py
```

Types:

```python
@dataclass(frozen=True)
class AppRepositoryViewRequest:
    branch: str | None = None
    revision: str | None = None
```

Functions:

```python
def open_view_repository(
    repo: Repository,
    request: AppRepositoryViewRequest,
) -> Repository:
    ...
```

or an equivalent app-owned helper that gives claim, neighborhood, and concept
builders one shared repository-view entry point.

### Required Deletions

- Delete any unused `bindings` field from current reading-surface requests if
  the view does not depend on environment bindings.
- Delete duplicated per-view branch/revision normalization.
- Do not leave raw `branch` and `revision` fields scattered independently
  across reading reports if one shared request can own them.

## Contract 1 - Typed Concept View Report

### Problem

The current concept display surface is:

```python
@dataclass(frozen=True)
class ConceptShowReport:
    rendered: str
```

That is not a durable web/API contract. It is a rendered blob for CLI output.

### Target

Add:

```text
propstore/app/concept_views.py
```

with:

- `ConceptViewRequest`
- `ConceptViewReport`
- explicit supporting dataclasses for identity, state, form/unit, claim
  inventory, value summaries, uncertainty summaries, provenance summaries, and
  machine IDs
- `build_concept_view(repo, request)`

Initial request:

```python
@dataclass(frozen=True)
class ConceptViewRequest:
    concept_id_or_name: str
    repository_view: AppRepositoryViewRequest = field(
        default_factory=AppRepositoryViewRequest
    )
    render_policy: AppRenderPolicyRequest = field(
        default_factory=AppRenderPolicyRequest
    )
```

Initial report shape:

```python
@dataclass(frozen=True)
class ConceptViewReport:
    concept_id: str
    logical_id: str | None
    artifact_id: str | None
    version_id: str | None
    heading: str
    canonical_name: str | None
    definition: str | None
    domain: str | None
    kind_type: str | None
    form: ConceptViewForm
    status: ConceptViewStatus
    render_policy: RenderPolicySummary
    repository_state: str
    claim_groups: tuple[ConceptClaimGroup, ...]
    value_summary: ConceptValueSummary
    uncertainty_summary: ConceptUncertaintySummary
    provenance_summary: ConceptProvenanceSummary
    related_claim_links: tuple[ConceptRelatedClaimLink, ...]
```

Required literal states must include, where semantically applicable:

- `known`
- `unknown`
- `blocked`
- `missing`
- `vacuous`
- `underspecified`
- `not_applicable`

### Required Behavior

- Concept identity is explicit and copyable.
- The report exposes form and unit discipline without requiring the presenter to
  inspect raw concept payloads.
- Claim inventory is grouped by claim type and visibility under render policy.
- Value and uncertainty summaries are app-owned summaries, not presenter-side
  reductions over raw claim rows.
- Provenance summary is app-owned and explicit about missing or mixed state.
- Related claim links are app-owned reading links, not presenter-derived graph
  guesses.

### Required Non-Behavior

- No HTML, CSS, Click, Rich, FastAPI, or browser types in the report.
- No `dict[str, object]` semantic payloads in the core report.
- No raw YAML string as the primary concept view contract.

## Contract 2 - Error Surface

### Problem

Concept routes need the same honest error discipline as claim routes.

### Target

Add typed concept-view app failures as needed, for example:

- unknown concept;
- unsupported repository-view state;
- sidecar missing;
- invalid render policy.

Web may map those to HTTP responses, but app owns the typed meaning.

## Contract 3 - Entry Index Reports

### Problem

Object pages alone are not enough. A web reader needs collection entrypoints:

- `/claims` for claim discovery under render policy;
- `/concepts` for concept discovery and browsing.

### Target

Use app-owned list/search reports directly where they are already adequate, and
strengthen them only if the web entry routes reveal a missing typed field.

Current candidate surfaces:

- `ClaimListRequest`
- `ClaimSearchRequest`
- `ClaimSummaryReport`
- `ConceptListRequest`
- `ConceptSearchRequest`
- `ConceptListReport`
- `ConceptSearchReport`

### Required Implementation Notes

- Prefer one route family per object kind with query-parameter search and
  filtering, rather than separate ad hoc search-only endpoints.
- Do not add web-local summary builders over raw rows if the app report can own
  the needed field.
- If the current concept or claim summary reports lack a field the page needs,
  fix the app report type instead of teaching the web layer to infer it.

## Contract 4 - JSON Boundary

Use the existing strict web-local serializer unless the concept report reveals a
bad type.

If serialization fails, fix the app report. Do not add a concept-specific web
normalizer that hides an ill-typed app contract.
