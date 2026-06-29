# Design: quire registrable projection-kind registry + worked Claim charter

Grounded in scout-quire-arch map (quire @ dba3493, declarative-charter-shape) and the 8-subsystem
consumer audit (SYNTHESIS.md). Goal: ONE canonical charter class per entity; every other
representation falls out of FIELD ANNOTATIONS via registered projection kinds. Bespoke compute stays
imperative behind one-type->IR->many-backend compilers.

## 1. The seam (from the arch map)
- No dispatch switchboard. Kind->output duplicated across 6 declaration sites + 2 consumer loops:
  - SQL/FTS/vector consumer: quire/sqlalchemy_schema.py:285-433 (per-flag `if field.<flag>`).
  - graph/artifact consumer: quire/projections.py:63-173 (`for field in charter.fields: if field.<flag>`).
- Both consumers iterate `charter.fields`. The inert `metadata: Mapping` carrier (charters.py:99)
  is threaded end-to-end but nothing dispatches on it. <- THIS is the registry hook.
- No existing kind-registry seam (ProjectionBuildStep is build ORDERING only).
- Edges strictly binary (projections.py:38-47). Contract hashing reads kind data via hand-enumerated
  keys in SchemaField.payload() (schema_ir.py:89-129) -> a registry MUST contribute deterministic payload there.

## 2. Core abstraction: ProjectionKind protocol
```python
# quire/projection_kinds.py  (new)
class ProjectionKind(Protocol):
    name: str                                   # stable id, used in schema payload + contract body
    def applies(self, field: CharterField) -> bool: ...
    def column_specs(self, field) -> tuple[ColumnSpec, ...]: ...      # SQL consumer contribution (may be empty)
    def emit(self, charter, record, field) -> Iterable[ProjectionOutput]: ...  # per-record consumer (graph/view/...)
    def schema_payload(self, field) -> Mapping[str, object]: ...      # DETERMINISTIC -> feeds SchemaField.payload()
```
- Registry: `register_projection_kind(kind)`; `iter_projection_kinds()`. Ordered by name for determinism.
- A field opts into a kind via the existing `metadata` dict / `Annotated[...]` markers (parsed at
  charter_class.py:371-388). e.g. `views: Annotated[str, View(state="known_missing", sentence=TEMPLATE)]`.

## 3. Refactor in 3 moves (deletion-first, no shims — per quire CLAUDE.md)
1. Introduce ProjectionKind + registry. Re-express the EXISTING built-ins (sql/index/unique, fts,
   vector, graph_node, graph_edge, fk, artifact) AS registered kinds. DELETE the hardcoded `if field.<flag>`
   branches in sqlalchemy_schema.py:285-433 and projections.py:63-173; replace with:
       for kind in iter_projection_kinds():
           if kind.applies(field): emit kind.column_specs / kind.emit
   The 6-way flag duplication (cleanup-debt #1) collapses: flags become kind markers in metadata.
2. SchemaField.payload() (schema_ir.py:89-129): replace hand-enumerated graph keys with
   `{k.name: k.schema_payload(field) for k in iter_projection_kinds() if k.applies(field)}`.
   Keeps schema_hash / contract bodies deterministic; contracts.py stays kind-agnostic.
3. Add GraphHyperedgeProjection (sources: tuple[ArtifactIdentity,...]) beside projections.py:38-47;
   register `hyperedge` kind with a collect-then-emit-one emitter (replaces per-value binary fan-out).
   Fixes the lossy N-ary flatten at propstore world/graph_projection.py:156-173.

## 4. New kinds we register (from SYNTHESIS bucket 2), each a THIN field-binding shell:
- view        : field-subset + per-field state(known/missing/vacuous/n-a/blocked) + NL sentence template.
                emit() builds the view struct; the STATE rule + sentence are declared, the value lookup is generic.
- hyperedge   : N antecedent fields -> 1 consequent field; emits GraphHyperedgeProjection. [argumentation, world]
- opinion     : names (confidence, sample_size, uncertainty, base_rate) fields -> Opinion(b,d,u,a)+dims;
                emit() calls the BESPOKE Jøsang transform (preference.py math), registry only binds fields. [argumentation, belief]
- embedding-text : ordered field coalesce + optional template glue -> the embed-input string. [embeddings]
- (singletons, register as needed): entrenchment-order, belief-formula-alphabet, jsonld-prov-graph.
RULE: a kind hosts field->transform BINDING only. The math/solver stays in the owner layer.

## 5. Worked proof — canonical Claim (ONE type, all projections fall out)
```python
@charter(family="claims", identity_field="claim_id")
class Claim:
    claim_id:    Annotated[str, Pk(), ContentId(("statement","conditions","context_id"))]
    statement:   Annotated[str, Fts(), View(sentence="{statement}"), EmbeddingText(order=1)]
    expression:  Annotated[str|None, EmbeddingText(order=2)]
    auto_summary:Annotated[str|None, EmbeddingText(order=0)]            # coalesce priority
    context_id:  Annotated[str, Fk("contexts")]
    conditions:  tuple[str, ...]                                        # CEL strings -> ConditionIR compiler (bespoke)
    confidence:  Annotated[float|None, Opinion(role="confidence"), View(state=True)]
    sample_size: Annotated[int|None,   Opinion(role="sample_size")]
    uncertainty: Annotated[float|None, Opinion(role="uncertainty"), View(state=True)]
    # argumentation: claim is an AF node; stance edges live on Stance via graph_edge/hyperedge
    af_label:    Annotated[str, GraphNode()]
```
Projections that now FALL OUT (zero hand-written parallel types):
- SQL row / index / FTS  -> sql+fts kinds  (kills ClaimRow, ClaimDocument, select_claim_embedding_rows)
- vector                 -> embedding-text kind feeds the vec store (kills claim_embedding_text + EmbeddingEntity glue)
- graph node + edges     -> graph/hyperedge (kills ClaimNode, ATMSClaimNode, ActiveClaim graph spellings)
- view                   -> view kind (kills ClaimViewReport/Value/Uncertainty/Condition/Status, ~10 render spellings)
- opinion                -> opinion kind binds fields; Jøsang math stays in owner (kills MetadataStrengthVector glue)
- content-hash identity  -> ContentId marker (kills hand-written assertion_id helpers)
Bespoke that STAYS (consumes Claim via compilers, not projections):
- conditions -> ConditionIR -> z3/sql/python backends; extension solving; ATMS; AGM; KNN; conflict detection.

## 6. Sequencing
P0 reconcile: repin propstore onto quire HEAD (dba3493) — already 90 commits ahead, linear. Confirm quire green.
P1 quire: land ProjectionKind registry + re-express built-ins + hyperedge + SchemaField.payload (moves 1-3).
   This also discharges quire cleanup-debt #1 (six-way flag dup) and #5 (binary edge) from the convergence workstream.
P2 propstore: author ONE canonical charter per family entity (start Claim, then Concept), register view/opinion/
   embedding-text/hyperedge kinds, DELETE the Document/Record/Loaded/Row/payload/coerce_ layer per entity.
P3 wire bespoke compute to consume canonical types via compilers; delete remaining coercion symptoms.
Reference 20e55cca is the FEATURE SPEC (3702 green tests) — port behavior, not the DTO shapes.
```
