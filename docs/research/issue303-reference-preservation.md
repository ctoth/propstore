# Reference preservation in rival-claim merges

The current failure does not require an author to guess which rival a relation
supports. It first requires the merge to supply valid maps from its input
instances. The existing implementation cannot publish its proposed result when
those maps do not preserve foreign keys. This change rejects that result before
advancing its target ref, preserving both input instances.

## Construction and obligation

For branch `b`, family `X`, and FK `f: X -> Claim`, a structure-preserving result
map must satisfy

```
m_b,Claim(f_b(x)) = f_result(m_b,X(x)).
```

The map is indexed by the source branch/commit. It is not a multivalued map from
an unqualified claim ID to every rival. With two divergent endpoints, a branch
containing `(s_left, c_left)` and another containing `(s_right, c_right)` supply
two correlated input tuples, not the cross pairs `(s_left, c_right)` and
`(s_right, c_left)`.

An equal serialized relation `e -> c` in both branches does not establish a
valid shared relation image when `c` maps to two distinct retained alternatives.
If `m_left(e) = m_right(e)`, the single-valued result FK would force
`m_left(c) = m_right(c)`. Keeping the rivals distinct and identifying that
relation occurrence are therefore incompatible in this diagram. Keeping its
old endpoint `c` dangling is not a third solution.

## Paper evidence

These citations were checked against local page images. Printed page numbers
are used for Schultz and Clark; Hitzler's four-page workshop PDF and
Zimmermann's twelve-page author paper are numbered within those papers.

- Hitzler, Kroetzsch, Ehrig & Sure (2005), [*What Is Ontology Merging?*](https://cdn.aaai.org/Workshops/2005/WS-05-01/WS05-01-017.pdf),
  p.3 Definition 2: a pushout contains the input morphisms and a commuting square,
  with unique factorization. pp.3–4, practical workflow steps 1–4, require the
  concrete representation, morphisms and alignment before algorithmizing the
  construction. This is not a theorem that raw equal artifact IDs determine
  the overlap instance.
- Zimmermann et al. (2006), [*Formalizing Ontology Alignment and its Operations
  with Category Theory*](https://corescholar.libraries.wright.edu/cse/201/),
  §§2.1–2.2 pp.3–4: V-alignments are spans of morphisms and merge is a pushout.
  §4.1 Definitions 4.1–4.2 p.7: W-alignments explicitly add a bridge ontology;
  merge is the diagram's colimit. §5 and Property 5.5 pp.9–10 distinguish
  relational alignment composition from guarantees about pushout-as-merge.
- Schultz & Wisnesky, [*Algebraic Data Integration*](https://arxiv.org/abs/1503.03571),
  local v8, 31 March 2025 revision of JFP27:e24 (2017): §3.2 p.11 defines
  symbol-commuting algebra morphisms; §4.1 pp.12–14 defines FK functions and
  instance transforms, fixing the schema/type side. §6.1 pp.34–35 constructs
  instance pushouts from source generators/equations and equations supplied by
  overlap transforms. §6.5 pp.37–39 separates record-link evidence from the
  equivalence classes computed by integration. Scope read: pp.10–15,34–39.
- Kuhn & Dumontier (2014), [*Trusty URIs*](https://arxiv.org/abs/1401.5775),
  pp.1–3 and §3 pp.5–7: content changes create a new artifact URI; self-reference
  abstraction is reversible and does not authorize changing a referenced
  identifier while retaining the original content identity. Their expanded
  [2015 treatment](https://arxiv.org/abs/1507.01697), pp.1–2, §3 p.4 and
  §4 pp.5–7, states the reference-tree and verification obligations. Propstore
  explicitly uses a typed JSON/ni payload, not the papers' RDF module encoding.
- Clark, Ciccarese & Goble (2014), *Micropublications*, §3.2.3 p.19:
  `MP = (A_mp, c, A_c, Phi, R)`, with principal `c` in `Phi` and support/challenge
  relation `R` over its elements. A transport must preserve membership, the
  principal, incidence and attribution together; changing only a claims list
  is insufficient. Scope read: pp.19–21; p.19 was rerendered locally because
  the existing collection image obscured the definition.

## Current contracts and ownership

The code paths below were checked at Propstore `8c7b06af` and its exact Quire
pin `d1daeed8`.

| Family | References affected | Identity owner/obligation |
| --- | --- | --- |
| stance | source and target claim | `families/identity/stances.py:14`; source promotion derives an ID from both endpoints and stance type. A changed endpoint can require a different ID. |
| justification | conclusion and premise set | `families/identity/justifications.py:17`; conclusion, sorted premises and rule fields determine promoted identity. Preserve the whole premise tuple from one input occurrence. |
| micropublication | claims membership; also explicit principal semantics | `families/identity/micropubs.py:53,96`; finalize hashes the typed source bundle. Canonical `Micropublication` additionally has `principal_claim` (`micropublications.py:141`) and checks membership. That field is not a declared FK. |
| description temporal anchor | claim | Authored `anchor_id`, provenance, frame and interval must be preserved together. No registered canonical transport/reidentity hook. |
| happens-before edge | earlier and later claim | Authored `edge_id` and provenance; preserve paired endpoints, not every rival combination. No registered canonical transport/reidentity hook. |
| coreference proposal | supports and description claim sets | Authored `argument_id`, provenance and proposal content; no registered canonical transport/reidentity hook. |

The registry exposes these FKs from charters. A runtime probe of the repaired
pin found `identity_policy=None` and `normalize_for_write=None` for all six
families. `FamilyIdentityPolicy` is descriptive metadata, not an executable
graph-transport operation. Quire owns generic FK reading/validation; no generic
reference rewriting operation exists in the inspected pinned package. Source
promotion's explicit stance/justification derivations are not a canonical
all-family transport API, and the source micropub type does not contain the
canonical bundle's explicit principal.

The federation slice-2 contract also explicitly requires branch-local valid
references and pinned source commits; it does not claim that concept-alignment
arguments or accepted alternatives are record-level overlap transforms for
this storage merge. `source/alignment.py` reads immutable imported snapshots and
promotes selected concepts. Borrowing that selection as a reference map would
introduce a different semantic operation.

## Implemented boundary and executable regression

`merge/merge_commit.py` now returns the exact prepared claim documents from
materialization and uses their charter-derived reference index. For every
input family with an FK targeting claims, it calls Quire's
`validate_foreign_key` on the retained document before `commit_flat_tree`.
An unresolved image raises `MergeReferenceConflict`, carrying the source commit,
family/ref, original `ForeignKeySpec` and validator detail. The target ref is
never advanced. The check does not assign endpoints, rewrite content identities,
select a winner, add relations or delete evidence.

The minimal executable example is
`tests/test_merge_reference_preservation.py`: initialize `c=250`, `s=100` and an
unchanged stance `s -> c`; branch; change `c` to 300/150; merge. Both inputs pass
the production verifier. The proposed result removes `c`, so the unchanged
stance has no valid image. Tests also cover the source endpoint, justification
premises/conclusion, micropublication membership, existing/absent result refs,
unchanged original documents, and an ordinary successful merge where both
branches retain one claim identity.

The corrected pre-fix run had ten behavioral failures (`DID NOT RAISE`) and one
passing control. After the boundary correction all eleven passed with the
three exact merged dependency pins. Logs are recorded in the task note.

## Exact remaining premise for successful transport

A successful transported result requires an actual family-instance diagram:
which branch-qualified occurrences are identified in the overlap, the induced
single-valued maps for every FK path, and family-owned normalization that
recomputes changed content identities and their dependent references while
retaining source-commit attribution. The equations above constrain that
diagram; they do not supply the currently absent canonical transport and
identity operations. In particular, plain byte equality of a row is not a
valid overlap witness when its resolved endpoint images differ.

That is a concrete missing owner contract, rather than a request for an author
to guess a relation's preferred rival. The boundary fix is intentionally not
described as completion of an all-family categorical merge.
