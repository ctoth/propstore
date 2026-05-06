# Proposal: First-Class Justifications in Propstore

**Date:** 2026-03-27
**Updated:** 2026-05-06
**Status:** Partially implemented; remaining work is runtime integration
**Grounded in:** current `propstore` source lifecycle, sidecar, and ASPIC bridge code

---

## Current State

First-class justifications are no longer only a proposal. The repository now has:

- Source-local `justifications.yaml` authoring on source branches.
- Canonical promoted `justifications/<source>.yaml` artifacts.
- A sidecar `justification` table populated from promoted authored justifications.
- A runtime `CanonicalJustification` domain object.
- A live ASPIC+ bridge that translates `CanonicalJustification` records into strict and defeasible ASPIC+ rules.
- `premise_kind` on claims for the ASPIC+ `K_n` / `K_p` partition.
- Targeted undercutting through `target_justification_id`.

The major remaining gap is narrower than the original proposal: the source and sidecar storage path exists, and the ASPIC+ rule translator exists, but the world/active-graph extraction path still does not harvest authored sidecar justifications into the normal runtime bridge. The normal projection path still synthesizes `reported:<claim_id>` plus `supports:<source>-><target>` / `explains:<source>-><target>` justifications from the active claim graph.

---

## Problem

Propstore needs authored inference structure to participate in the same runtime argumentation path as derived support/explanation edges.

The current split loses authored structure at runtime:

1. **Authored multi-premise rules are stored but not normally consumed.** Source-authored `justifications.yaml` entries compile into the sidecar `justification` table, but active world graph extraction has no `CompiledWorldGraph.justifications` surface and `_extract_justifications()` does not read `SidecarStore.justification` rows.

2. **Runtime synthesis remains single-edge.** `claim_justifications_from_active_graph()` derives one-premise justifications from active `supports` and `explains` relation edges. That preserves the old graph behavior, but it cannot represent authored multi-premise rules.

3. **The ASPIC+ bridge is ahead of the world extraction layer.** `justifications_to_rules()` already accepts strict/defeasible `CanonicalJustification` records, rejects empty-premise non-reported rules, and names defeasible rules by justification ID for undercutting. Direct bridge callers can pass authored justifications, but the normal world projection path does not yet supply them.

4. **The sidecar representation is queryable but not first-class in the semantic graph.** Authored justification rows exist as sidecar storage, with premises encoded as JSON, but there is no owner-layer API comparable to `all_claim_stances()` or `stances_between()` that returns typed canonical justifications for an active claim set.

The remaining work is therefore not "add justifications everywhere"; it is to connect the already-existing storage and bridge surfaces through a typed owner-layer runtime path.

---

## Implemented Surfaces

### Source Authoring

Source branches support batch and proposal authoring:

- `pks source add-justification <source> --batch <file>`
- `pks source propose-justification <source> ...`

The source document type is `SourceJustificationsDocument`, containing `SourceJustificationDocument` entries:

```yaml
justifications:
  - id: just1
    conclusion: claim_observation
    premises:
      - claim_parameter
    rule_kind: empirical_support
    rule_strength: defeasible
    provenance:
      page: 3
      section: Results
      quote_fragment: "..."
    attack_target:
      target_claim: claim_observation
      target_justification_id: just0
      target_premise_index: 0
```

Source-local claim references are resolved during source normalization. Promotion filters out justifications whose conclusion or premises do not resolve to promoted or primary claims.

### Canonical Storage

Promoted justifications are written under:

```text
justifications/<source>.yaml
```

They reuse `SourceJustificationsDocument` as the document type. This is a naming artifact of the current code, not a source-local semantic leak: promotion strips source-local claim fields from claims and writes resolved canonical claim IDs in justification `conclusion` and `premises`.

### Sidecar Storage

The sidecar has a single `justification` table:

```sql
CREATE TABLE justification (
    id TEXT PRIMARY KEY,
    justification_kind TEXT NOT NULL,
    conclusion_claim_id TEXT NOT NULL,
    premise_claim_ids TEXT NOT NULL,
    source_relation_type TEXT,
    source_claim_id TEXT,
    provenance_json TEXT,
    rule_strength TEXT NOT NULL DEFAULT 'defeasible'
);
```

`premise_claim_ids` is a JSON array, not a separate premise table. That differs from the original 2026-03-27 proposal. The table is populated by `populate_authored_justifications()` from sidecar compilation rows.

### Runtime Domain Object

The runtime object is:

```python
@dataclass(frozen=True, order=True)
class CanonicalJustification:
    justification_id: str
    conclusion_claim_id: str
    premise_claim_ids: tuple[str, ...] = ()
    rule_kind: str = "reported_claim"
    rule_strength: str = "defeasible"
    provenance: ProvenanceRecord | None = None
    attributes: tuple[tuple[str, Any], ...] = ()
```

This is the bridge-facing shape. Decoded YAML and SQLite rows should be converted into this type at the IO boundary before they enter argumentation.

### ASPIC+ Bridge

The ASPIC+ bridge is implemented, not future work.

`justifications_to_rules()` maps canonical justifications as follows:

- `reported_claim` justifications are skipped as rules and feed `claims_to_kb()`.
- `rule_strength == "strict"` produces a strict ASPIC+ rule with no name.
- Any other rule strength currently produces a defeasible rule named by `justification_id`.
- Empty-premise non-reported justifications raise.
- Unknown active premises raise.

`stances_to_contrariness()` implements targeted undercutting:

- `undercuts` with `target_justification_id` targets matching named defeasible rules.
- If a grounded/transformed rule name has a suffix, matching can fall back to the base ID before `#`.
- An undercut against a claim with multiple matching defeasible justifications is ambiguous unless `target_justification_id` is provided.
- Undercutting strict rules is impossible because strict rules are unnamed.

`structured_projection.build_structured_projection()` delegates to the ASPIC+ bridge. The old flat structured-argument path is no longer the target architecture.

### Claim Premise Kind

Claims have:

```sql
premise_kind TEXT NOT NULL DEFAULT 'ordinary'
```

The bridge maps claims with `premise_kind == "necessary"` into `K_n`; all other reported claims go into `K_p`.

---

## Target Architecture

Justifications should be a normal semantic input to world argumentation:

```text
canonical justifications/<source>.yaml
        |
        v
sidecar justification rows
        |
        v
typed owner-layer loader
        |
        v
CanonicalJustification records filtered to active claims
        |
        v
ASPIC+ bridge T2/T4
```

The target is one production path:

1. Load authored justifications from canonical artifacts or sidecar rows through an owner-layer API.
2. Convert rows immediately to `CanonicalJustification`.
3. Filter to active claims.
4. Add exactly one `reported_claim` justification for each active directly asserted claim.
5. Decide whether support/explain stances still synthesize fallback justifications, and if so make that policy explicit at the owner layer.
6. Pass the final canonical justification set to the ASPIC+ bridge.

The preferred end state is not a compatibility bridge. If authored justifications are the source of inference rules, support/explain stance synthesis should either be deleted from the normal ASPIC+ path or kept only as an explicit derived-rule policy with a typed request/report. It should not remain hidden inside bridge extraction.

---

## Required Changes

### 1. Add an Owner-Layer Justification Loader

Add a typed API near the world/sidecar owner layer:

```python
def all_authored_justifications(self) -> tuple[CanonicalJustification, ...]: ...

def justifications_for_claim_scope(
    self,
    claim_ids: set[str],
) -> tuple[CanonicalJustification, ...]: ...
```

The loader should:

- Read `justification` rows.
- Decode `premise_claim_ids` JSON as a list of strings.
- Decode `provenance_json`.
- Convert immediately to `CanonicalJustification`.
- Reject malformed rows at the boundary instead of passing dicts into the core pipeline.

Do not expose loose `dict` rows as the runtime surface.

### 2. Carry Justifications Through the Active Graph or Extract Them Beside It

There are two principled options:

- Add `justifications: tuple[CanonicalJustification, ...]` to `CompiledWorldGraph`.
- Keep `CompiledWorldGraph` claim/relation-only, but have bridge extraction ask the store for authored justifications scoped to the active claim IDs.

The second option is smaller and keeps the graph focused on claim activation. The first option makes justifications visible in snapshots and deltas. Pick one owner boundary and delete the old hidden synthesis from the bridge once the target is implemented.

### 3. Replace Hidden Runtime Synthesis

`claim_justifications_from_active_graph()` currently creates:

- `reported:<claim_id>`
- `supports:<source_id>-><target_id>`
- `explains:<source_id>-><target_id>`

After authored justifications are loaded, this synthesis should not silently compete with authored rules. The production rule should be explicit:

- Always synthesize `reported_claim` premises for active claims unless a future direct-assertion artifact replaces that role.
- Do not synthesize support/explain inference rules in the normal ASPIC+ path when authored justifications are present for the same active scope.
- If support/explain fallback remains for un-authored repositories, put it behind a typed policy argument and make ambiguity observable.

No fallback reader for older data is required unless older repositories are explicitly declared in scope.

### 4. Align Rule Kind Validation

Current source validation allows:

- `causal_explanation`
- `comparison_based_inference`
- `definition_application`
- `empirical_support`
- `explains`
- `methodological_inference`
- `reported_claim`
- `scope_limitation`
- `statistical_inference`
- `supports`

The original proposal mentioned `expert_testimony` and `abductive_inference`, but current validation does not allow them. Either add them deliberately with tests or remove them from documentation that claims they are accepted.

### 5. Decide the Sidecar Premise Shape

The current sidecar stores premises as a JSON array in `justification.premise_claim_ids`. That is acceptable for current use because the row is an artifact projection, not a relational query surface.

Do not introduce `justification_premise` unless there is a concrete query or indexing requirement. If ordering and per-premise targeting become important in sidecar queries, then replace the JSON field with a normalized table and update every caller in one slice.

---

## Non-Goals

- Reintroducing the old flat structured argument builder.
- Adding backwards-compatibility shims for pre-justification repository states.
- Treating source-local readability metadata as canonical identity.
- Persisting synthesized support/explain justifications as if they were authored.
- Adding a separate premise table without a demonstrated owner-layer need.

---

## Verification Targets

The remaining implementation should be considered complete only when these observable checks pass:

1. A promoted authored multi-premise justification appears in `justifications/<source>.yaml`.
2. `pks build` writes that justification into the sidecar `justification` table.
3. The owner-layer loader returns a `CanonicalJustification` with all premise IDs intact.
4. A world ASPIC+ projection uses the authored multi-premise rule without requiring a `supports` or `explains` stance for each premise.
5. A targeted `undercuts` stance against that justification defeats only arguments using that defeasible rule.
6. A strict authored justification is not undercuttable.
7. If multiple defeasible rules conclude the same claim, an undercut without `target_justification_id` raises or reports an explicit ambiguity instead of choosing one silently.

Use the logged pytest wrapper for project tests, for example:

```powershell
powershell -File scripts/run_logged_pytest.ps1 tests/test_source_relations.py tests/test_aspic_bridge.py
```

For package type checking, use:

```powershell
uv run pyright propstore
```

---

## References

- Modgil & Prakken 2014/2018: ASPIC+ strict/defeasible rules, naming function, undercutting.
- Pollock 1987: rebutting and undercutting defeaters.
- Prakken 2010: structured argumentation and transposition closure.
- Current implementation references:
  - `propstore/families/documents/sources.py`
  - `propstore/source/relations.py`
  - `propstore/source/promote.py`
  - `propstore/sidecar/schema.py`
  - `propstore/sidecar/passes.py`
  - `propstore/core/justifications.py`
  - `propstore/aspic_bridge/translate.py`
  - `propstore/aspic_bridge/projection.py`
