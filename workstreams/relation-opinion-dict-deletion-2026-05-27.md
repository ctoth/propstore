# Relation Opinion Dictionary Deletion Workstream - 2026-05-27

## Decision

The existing relationship family owns relation opinions.

Owner: `propstore.families.relations.declaration.RelationEdge` / `Stance`, declared by `RELATIONS_CHARTERS`.

Representation: a nullable typed `propstore.opinion.Opinion` value field named `opinion` on the existing `relation_edge` family and on `propstore.core.graph_types.RelationEdge`.

Not the representation:

- no new opinion family
- no opinion FK
- no getter helper
- no adapter helper
- no flat dictionary bridge
- no `opinion_belief` / `opinion_disbelief` / `opinion_uncertainty` / `opinion_base_rate` semantic columns
- no `ResolutionDocument.opinion`

Why this is the owner: the current repo has an existing relationship family and typed relation model. There is no existing opinion family. `Opinion` is already a typed value object used by claim graph nodes and source trust. Calibration evidence remains owned by existing calibration/source-trust surfaces; the computed relation opinion is the relation's value, deleted with the relation and not referenced independently.

## Final State

- `RelationEdge.opinion` is the only production source of a relation's opinion.
- `Stance.opinion` is inherited from the relation family model.
- `core.graph_types.RelationEdge.opinion` carries the typed value through compiled graphs.
- Argumentation consumes `RelationEdge` objects directly.
- `ProbabilisticRelation` is built directly from typed relation objects.
- Source/heuristic stance production writes a relation `opinion` value, not `resolution.opinion`.
- Resolution metadata may remain only as relation-owned scalar fields: `resolution_method`, `resolution_model`, `embedding_model`, `embedding_distance`, `pass_number`, `confidence`, and unresolved-calibration diagnostics.
- Flat dictionaries remain only at serialization boundaries: `to_dict` / `from_dict` and YAML/JSON/SQL edge codecs.

## Delete First

Delete these production surfaces before adding replacement wiring:

- `propstore.praf.engine.p_relation_from_stance`
- `propstore.praf.engine.p_defeat_from_stance`
- exports of both names from `propstore/praf/__init__.py`
- README mentions of both names in `propstore/praf/README.md`
- direct tests of those names:
  - `tests/test_from_probability_n_one_round_trip.py`
  - `tests/test_praf_raw_confidence_not_dogmatic.py`
  - the `p_defeat_from_stance` block in `tests/test_praf.py`
- `propstore.probabilistic_relations.provenance_from_row`
- `propstore.probabilistic_relations.relation_from_row`
- import and calls to `relation_from_row` in `propstore/argumentation.py`
- `_stance_row_from_edge` in `propstore/argumentation.py`
- `_graph_stance_rows` in `propstore/argumentation.py`
- `stance_rows: tuple[dict, ...]` in `SharedAnalyzerInput`
- production indexing of stance dicts in `_collect_claim_graph_relations`

## Replacement Wiring

1. `propstore.families.relations.declaration`
   - Add `from propstore.opinion import Opinion`.
   - Add `CharterField("opinion", Opinion, nullable=True)` to the `relation_edge` charter.
   - Remove `opinion_belief`, `opinion_disbelief`, `opinion_uncertainty`, and `opinion_base_rate` from the charter.
   - Remove those four fields from `RelationEdge.attribute_mapping`.
   - Keep relation-owned resolution scalar fields only.

2. `propstore.families.relations.declaration._resolution_attributes`
   - Stop reading nested `resolution.opinion`.
   - Return only relation-owned scalar resolution fields.
   - Delete mapping support for `opinion["b"]`, `opinion["d"]`, `opinion["u"]`, and `opinion["a"]`.

3. `propstore.families.claims.declaration`
   - Delete `OpinionDocument`.
   - Remove `opinion: OpinionDocument | None` from `ResolutionDocument`.
   - Remove `OpinionDocument` from the payload binding list.

4. `propstore.families.stances.declaration`
   - Add `opinion: Opinion | None` to `StanceDocument` through the stance charter.
   - Add `opinion: Opinion | None` to `SourceStanceEntryDocument` through the source stance charter.
   - Keep `resolution` for scalar resolution metadata only.

5. `propstore.source.promote`
   - Promote source stance `opinion` into canonical stance `opinion`.
   - Stop serializing `stance.resolution` to preserve nested opinion data.

6. `propstore.heuristic.classify`
   - Return stance payloads with top-level `opinion`.
   - Stop putting opinion under `resolution`.
   - Keep `resolution` for method/model/distance/confidence/unresolved-calibration metadata.

7. `propstore.core.graph_types.RelationEdge`
   - Add `opinion: Opinion | None = field(default=None, compare=False)`.
   - Serialize it in `to_dict` using `_opinion_to_dict`.
   - Decode it in `from_dict` using `_opinion_from_dict`.
   - Keep `attributes` for non-owned legacy graph metadata only until later deletion; do not use it for opinion.

8. `propstore.core.graph_build`
   - Construct `RelationEdge(opinion=stance.opinion, ...)` from the relationship family row.
   - Stop copying opinion through `stance.attribute_mapping()`.

9. `propstore.argumentation`
   - `_collect_claim_graph_relations` iterates typed `RelationEdge` objects.
   - Use `edge.source_id`, `edge.target_id`, `edge.relation_type`, and `edge.opinion`.
   - Build `ProbabilisticRelation(...)` directly when `edge.opinion is not None`.
   - Record no calibrated probabilistic relation when `edge.opinion is None`.
   - Synthetic conflict-derived attack edges have `opinion=None`.

10. `propstore.probabilistic_relations`
    - Delete row provenance helpers.
    - Keep `ProbabilisticRelation` and `RelationProvenance` only if populated from typed provenance.
    - Keep `relation_map`; it maps typed `ProbabilisticRelation` records, not dict rows.

## Search Gates

These must be zero production hits:

```powershell
rg -n -F "p_relation_from_stance" propstore
rg -n -F "p_defeat_from_stance" propstore
rg -n -F "relation_from_row" propstore
rg -n -F "provenance_from_row" propstore
rg -n -F "_stance_row_from_edge" propstore
rg -n -F "_graph_stance_rows" propstore
rg -n -F "OpinionDocument" propstore
rg -n -F "resolution.opinion" propstore
rg -n -F "opinion_belief" propstore
rg -n -F "opinion_disbelief" propstore
rg -n -F "opinion_uncertainty" propstore
rg -n -F "opinion_base_rate" propstore
```

These may remain only in boundary tests or generated historical artifacts until the final test cleanup slice:

```powershell
rg -n -F "opinion_belief" tests
rg -n -F "p_relation_from_stance" tests
```

## Verification Gates

Run in order:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label relation-opinion-dict-deletion tests/test_praf.py tests/test_praf_integration.py tests/test_argumentation_integration.py tests/test_relate_opinions.py tests/test_core_graph_types.py tests/test_source_promotion_alignment.py
uv run pks contract-manifest --write
uv run pyright propstore
uv tool install --upgrade --force .
pks init "$env:TEMP\propstore-pks-cli-smoke-20260527-relation-opinion"
```

After any passing substantial targeted test run, reread this workstream and continue with the next unchecked item.
