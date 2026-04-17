---
title: "Named Graphs, Provenance and Trust"
authors: "Jeremy J. Carroll, Christian Bizer, Pat Hayes, Patrick Stickler"
year: 2005
venue: "Proceedings of the 14th International Conference on World Wide Web (WWW '05), Chiba, Japan, May 10-14, 2005, pp. 613-622"
doi_url: "https://doi.org/10.1145/1060745.1060835"
pages: "613-622"
affiliations:
  - "Hewlett-Packard Labs, Bristol, UK (Carroll)"
  - "Freie Universität Berlin, Germany (Bizer)"
  - "IHMC, Florida, USA (Hayes)"
  - "Nokia, Finland (Stickler)"
publisher: "ACM"
citation: "ACM 1-59593-046-9/05/0005"
---

# Named Graphs, Provenance and Trust

## One-Sentence Summary
A minimal syntactic-and-semantic extension of RDF that promotes graphs to first-class URI-named entities, plus a Semantic Web Publishing (SWP) vocabulary for digital signatures, authorities, warrants, and performative assertion, so that information consumers can apply task-specific trust policies over provenance-bearing graphs. *(p.1)*

## Problem Addressed
RDF has no built-in mechanism for talking *about* graphs (provenance, intellectual-property rights, privacy, access control, signing, propositional attitudes, scoping of assertion/logic, ontology versioning/evolution) and RDF reification has well-known problems. Competing "quads" proposals use the fourth element inconsistently, and richer context theories (TRIPLE, Guha/Fikes) impose complex semantics that act as a barrier to deployment. *(p.1)*

## Key Contributions
- Formal abstract syntax and semantics for *Named Graphs*: a pair `ng = (n, g)` with `n ∈ U` (URIref) and `g` an RDF graph, extending RDF minimally while preserving backward compatibility. *(p.2)*
- Observation that the single feature of graph *naming* is sufficient — complex semantic theories of [37,40] "principally act as a barrier to deployment." *(p.1)*
- Three concrete syntaxes: TriX (XML), RDF/XML (with caveats), and TriG (Turtle-based compact syntax using `{ ... }` blocks). *(p.1, p.2)*
- Semantic Web Publishing (SWP) vocabulary: `swp:Warrant`, `swp:Authority`, `swp:authority`, `swp:assertedBy`, `swp:quotedBy`, `swp:digest`, `swp:digestMethod`, `swp:signature`, `swp:signatureMethod`, `swp:certificate`. *(p.5)*
- Performative-warrant machinery: a warrant graph that both describes and *is* the social act of assertion (Austin-style performative, footnote 2 "I promise to pay the bearer..."). *(p.5)*
- Illustrative trust algorithm for an information consumer to compute an accepted set A ⊆ domain(N). *(p.6)*
- Formal model-theoretic extension of RDF semantics [26] covering: persons in domain of discourse, certificate-based identification, performative semantics for `swp:assertedBy`, truth-conditional semantics for `swp:signature`. *(p.7, p.8)*
- Two concrete query languages demonstrated (RDFQ, TriQL) and a note that the then-draft SPARQL [36] would supersede both. *(p.3)*

## Study Design (empirical papers)
*Not an empirical paper — a formalism + vocabulary + semantics paper.* No RCT/cohort/benchmark.

## Methodology
- Abstract syntax defined set-theoretically on top of RDF's triple sets. *(p.1, p.2)*
- Semantics defined as an extension to the model theory of RDF/RDFS/OWL [26]: an interpretation `I` *conforms with* a set of Named Graphs `N` when, for every `ng ∈ N`, `name(ng)` is in `I`'s vocabulary and `I(name(ng)) = ng`. *(p.1-2)*
- Three concrete syntaxes designed as serializations of the abstract syntax. *(p.1, p.2)*
- Application vocabulary (SWP) built on top, layered deliberately thin. *(p.4)*
- Performative semantics added by constraining interpretations so that `swp:assertedBy`-triples become self-fulfilling in *authorizing interpretations*. *(p.7, p.8)*
- Trust algorithm presented as illustrative (not prescriptive) — a sketch to show how consumers can apply Named-Graph-aware policies. *(p.6)*

## Key Equations / Statistical Models

Abstract-syntax object universes:

$$
V = U \cup B \cup L, \qquad T = V \times U \times V
$$
Where: `U` = URIrefs, `B` = blank nodes, `L` = legal RDF literals, `T` = set of all RDF triples; `U, B, L` are pairwise disjoint; footnote 1 notes the legacy literal-subject restriction has been removed.
*(p.2)*

Named Graph definition:

$$
ng = (n, g), \quad n \in U,\ g \subseteq T,\ name(ng) = n,\ rdfgraph(ng) = g
$$
Where: a set of Named Graphs is a partial function `N : U ⇀ 2^T`; blank nodes are scope-isolated: `ng ≠ ng'` implies `blank(rdfgraph(ng)) ∩ blank(rdfgraph(ng')) = ∅`.
*(p.2)*

Conformance of an RDF(S) interpretation `I` with a set of Named Graphs `N`:

$$
\forall ng \in N:\ name(ng) \in \mathrm{vocab}(I)\ \wedge\ I(name(ng)) = ng
$$
Where: the Named Graph itself (not the RDF graph) is the denotation of the name; this is an *intensional* style in the sense of RDFS class-extension modeling, which lets several distinct Named Graphs share an underlying RDF graph without collapsing identity.
*(p.1)*

Graph-property examples (defined in the paper's extension):

$$
\langle f,g\rangle \in \mathrm{IEXT}(I(\mathtt{rdfg:subGraphOf})) \iff rdfgraph(f) \subseteq rdfgraph(g)
$$
Where: subset-hood holds up to blank-node renaming; formally there exists a renaming `m` on `blank(rdfgraph(f))` s.t. `m(rdfgraph(f)) ⊆ rdfgraph(g)`.
*(p.1)*

$$
\langle f,g\rangle \in \mathrm{IEXT}(I(\mathtt{rdfg:equivalentGraph})) \iff rdfgraph(f) = rdfgraph(g)
$$
Where: equality is again modulo blank-node renaming.
*(p.1)*

OWL imports closure over a set of Named Graphs `K`:

$$
K \text{ is imports-closed} \iff \forall (x\ \mathtt{owl:imports}\ u) \in \bigcup K:\ \exists g \in K.\ name(g) = u
$$
Where: using graph *names* (rather than URI retrieval) makes imports-closure well-defined under the open-world assumption; retrieval of `u` remains possible as a fallback.
*(p.2)*

Accepted-subset cardinality / meaning of "accepted" Named Graphs:

$$
|\mathrm{meanings}(N)| = 2^{|\mathrm{domain}(N)|},\qquad \mathrm{meaning}\langle A, N\rangle = \bigcup_{a\in A} rdfgraph(N(a))\ \text{interpreted with RDF semantics, subject to } I \models N
$$
Where: `A ⊆ domain(N)` is the consumer's accepted set; choice of `A` is a pragmatic / application-level decision, not a logical one.
*(p.4)*

RDF Dataset (SPARQL draft [36]):

$$
D = \{\, G,\ (u_1, G_1),\ (u_2, G_2),\ \dots,\ (u_n, G_n)\,\},\ u_i \text{ URIs, distinct},\ G_i \text{ RDF graphs}
$$
Where: `G` is the *background graph*; `G_i` are named graphs. The paper notes the background graph is the main innovation over their own framework — it adds backward-compatibility at the cost of potentially re-introducing provenance-merge difficulties.
*(p.3)*

SWP semantic rule — performative authorization:

$$
I \models (\mathtt{ex:a}\ \mathtt{swp:authority}\ \mathtt{ex:b}) \iff I(\mathtt{ex:a}) \text{ is a warrant authorized by } I(\mathtt{ex:b})
$$
Where: this is *primitive* — the remaining SWP semantics is defined in terms of this and the class-extensions of `swp:Authority`, `swp:Warrant`. *(p.7)*

SWP semantic rule — performative assertion (self-fulfilling):

$$
\text{If } ng \text{ is a warrant graph with } name(ng)\ \mathtt{swp:authority}\ bbb, \text{ and } aaa\ \mathtt{swp:assertedBy}\ bbb \in rdfgraph(ng), \text{ and } I(bbb) = ng, \text{ then } I \models rdfgraph(I(aaa))
$$
Where: the self-realizing quality of performatives extends to propositional-attitude triples in an authorized warrant graph. Same pattern applies to `swp:quotedBy`.
*(p.7)*

Trust propagation rule (semantic proposal, p.8):

$$
(I \models aaa\ \mathtt{swp:assertedBy}\ bbb)\ \wedge\ (I \models bbb\ \mathtt{swp:authority}\ ccc)\ \wedge\ I(ccc) \text{ trusted} \;\Rightarrow\; I \models rdfgraph(I(aaa))
$$
Where: expressed as a *trust policy* that a consumer may choose to adopt; not part of the core semantics.
*(p.8)*

`swp:digest` property extension (definitional):

$$
(g, d) \in \mathrm{IEXT}(\mathtt{swp:digest}) \iff \exists m:\ (g, m) \in \mathrm{IEXT}(\mathtt{swp:digestMethod}) \wedge \text{method}_m(I(g)) = d
$$
Where: `d` is a finite octet sequence; `m` is a URI dereferenceable to a document describing the algorithm; the digest is computed over `I(g)`.
*(p.8)*

`swp:signature` property extension (definitional):

$$
(w, s) \in \mathrm{IEXT}(\mathtt{swp:signature}) \iff \exists m, a, c, g.\ (w,m)\in\mathrm{IEXT}(\mathtt{swp:signatureMethod}) \wedge (w,a)\in\mathrm{IEXT}(\mathtt{swp:authority}) \wedge (a,c)\in\mathrm{IEXT}(\mathtt{swp:certificate}) \wedge ((g,w)\in\mathrm{IEXT}(\mathtt{swp:quotedBy}) \vee (g,w)\in\mathrm{IEXT}(\mathtt{swp:assertedBy})) \wedge \text{method}_m(I(g), c) = s
$$
Where: `c` is an X.509 or PGP certificate; `I(g)` must be a Named Graph; verification does not depend on trusting the certificate chain — that is done separately at acceptance time.
*(p.8)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| URIref set | U | set | — | infinite | 2 | universe of RDF URIs |
| Blank-node set | B | set | — | infinite | 2 | scoped per Named Graph |
| Literal set | L | set | — | infinite | 2 | legacy subject-literal restriction removed (fn 1) |
| Triple set | T | set | V × U × V | — | 2 | subject and object drawn from V=U∪B∪L |
| Named Graph | ng | (URI, graph) | — | — | 2 | `name(ng)∈U`, `rdfgraph(ng)⊆T` |
| Accepted set | A | set | ∅ (init in algo) | A ⊆ domain(N) | 4, 6 | consumer-chosen |
| Number of accepted-set meanings | — | count | — | 2^{\|domain(N)\|} | 4 | combinatorial meanings over N |
| Background graph | G | graph | — | — | 3 | SPARQL RDF Dataset extension |
| Digest input | d | octets | — | finite | 8 | computed over I(g) |
| Signature input | s | octets | — | finite | 8 | computed over I(g) with certificate c |
| Certificate | c | X.509 or PGP | — | — | 7, 8 | RFC 2253 DN for X.509 [43]; PGP per [44] |
| Example signature method | `swp:JjcRdfC14N-rsa-sha1` | URI | — | — | 5 | variant of graph canonicalization from [13] + XML-Signature digest/sig method |
| Example digest method | `swp:JjcRdfC14N-sha1` | URI | — | — | 5 | SHA-1 over canonicalized RDF |
| Certificate format | — | standards | X.509 [30] | X.509 or PGP | 5, 7 | PGP key material per [44] |

### SWP Vocabulary (property/class signature table)

| Term | Kind | Domain | Range | Page | Notes |
|------|------|--------|-------|------|-------|
| `swp:Warrant` | class | — | — | 4 | represents a warrant — social act |
| `swp:Authority` | class | — | — | 4 | legal/social entity that can perform acts |
| `swp:authority` | property (functional) | `swp:Warrant` | `swp:Authority` | 4 | OWL functional — at most one authority per warrant |
| `swp:assertedBy` | property | Named Graph | `swp:Warrant` | 4 | says warrant records an assertion |
| `swp:quotedBy` | property | Named Graph | `swp:Warrant` | 4 | says warrant merely quotes (no commitment) |
| `swp:signatureMethod` | property | `swp:Warrant` | URI | 4 | URI dereferenceable to method description |
| `swp:signature` | property | `swp:Warrant` | `xsd:base64Binary` | 4, 5 | actual binary signature |
| `swp:digestMethod` | property | `rdfg:Graph` | `swp:DigestMethod` | 5 | method for computing digest |
| `swp:digest` | property | `rdfg:Graph` | `xsd:base64Binary` | 5 | digest value |
| `swp:certificate` | property | `swp:Authority` | `xsd:base64Binary` | 5, 7 | X.509 or PGP binary |

## Effect Sizes / Key Quantitative Results
*Not applicable — formalism paper; no measured effects.*

## Methods & Implementation Details
- Three concrete syntaxes (TriX, TriG, RDF/XML) — TriG uses `{ ... }` Turtle-like block per graph, preceded by the graph name. *(p.1, p.2)*
- RDF/XML as a carrier: take the first `xml:base` declaration (or the document URL) as the Named Graph's name. Disadvantages flagged: one name per document, cannot serialize graphs with certain predicate URIs, cannot use literals as subjects in RDF/XML, and URI triple-use for three purposes (retrieval address / document identity / graph identity) creates confusion. None of these disadvantages apply to TriX or TriG. *(p.2)*
- Blank-node no-sharing global rule: enforced via renaming before merge. *(p.2)*
- Open-world framing: open-worldness applies at the description level, not the identification level; names rigidly identify graphs. *(p.2)*
- RDF reification treated as "a Named Graph containing a single triple" — semantics of this differ from RDF-recommendation reification's lack of semantics, and better serves provenance/quoting use cases. *(p.2)*
- OWL imports redefined in terms of Named Graphs: imports-closed iff for every `x owl:imports u` there is a graph in the collection named `u` (p.2). Retrieval of the URI remains a fallback. Introduces a consistency question: does a local/cached copy agree with the graph found by retrieval? *(p.2)*
- Two query languages exhibited:
  - **RDFQ** (turtle-serialized) with `:graph [...]`/`:target [...]` shape. *(p.3)*
  - **TriQL** (`SELECT ?x ?y WHERE ?graph (...) AND ...`) — pattern-based, graph-name-bound. *(p.3)*
  - Paper predicts SPARQL will supersede both. *(p.3)*
- NG4J: Jena-based Java implementation, provides `Set<NamedGraph>` manipulation and provenance-enabled Jena Model view; supports TriX, TriG, TriQL. *(p.3)*
- Jena MultiModel: faceted browser http://www.swed.org.uk/ used trust-based visual styling from graph source. *(p.3)*
- Trust-policy algorithm (Section 8.5, p.6) — non-deterministic backtracking search for accepted set `A`:

### Algorithm: Trust-policy accepted-set construction *(p.6)*
```
Input:
  K  — agent's RDF knowledge base (possibly empty)
  N  — incoming set of Named Graphs

1. A := ∅
2. Non-deterministically choose n ∈ domain(N) − A;
   if no choices remain, terminate.
3. K' := K ∪ rdfgraph(N(n))        -- provisionally assume N(n)
4. If K' entails (n swp:assertedBy _:w)
   then K := K'; A := A ∪ {n}
   else backtrack to step 2.
5. Repeat from 2.
```
- **Properties claimed:** sound with respect to the "only add explicitly-asserted graphs" goal (step 4 checks); *incomplete* against that same goal — two graphs that each assert the other would both satisfy the criterion if both accepted, but the algorithm misses that. Authors accept this trade-off ("mutually asserting graphs are less likely to be understood"). *(p.6)*
- **Edge cases noted:**
  - If `K` is initially empty, the first graph admitted must be self-asserting (contains its own warrant) with an arbitrary authority. *(p.6)*
  - The underscore-w is unconstrained at step 4, i.e. the default policy is "trust everybody"; tighter policies restrict `_:w` to named authorities or require the warrant graph to actually be a warrant graph. *(p.6)*
  - The algorithm does not handle consistency: step-3 merging can introduce inconsistency (undecidable in OWL Full; detectable in OWL Lite). Paper does *not* mandate a response — some apps ignore, others reject subsets, some use truth-maintenance. *(p.6)*
- PKI extension to the algorithm (Section 8.5.1, p.6-7): query for `?w1 swp:assertedBy ?w1 . ?w1 swp:authority ?s . ?w1 swp:signatureMethod ?method . ?w1 swp:signature ?sign . ?s swp:certificate ?certificate` and verify the signature with the indicated method; if verification fails reject; if succeeds check the certificate chain. A graph may have multiple warrants — which warrant to check is nondeterministic, consumer should consider any valid-chain warrant. *(p.7)*
- Graph-canonicalization + signing: include `:G1`'s `swp:digest` triple into `:G2` and sign `:G2`; that transitively protects `:G1`. The `swp:signature` triple itself must be excluded when forming the signature input (footnote 4). *(p.5)*

## Figures of Interest
- **Figure 1 (p.5) — "The Semantic Web Publishing Vocabulary":** Class/property diagram. Nodes: `rdfg:Graph`, `swp:Warrant`, `swp:Authority`, `swp:DigestMethod`, `swp:SignatureMethod`, `xsd:base64Binary` (×3). Edges: `swp:digest`, `swp:digestMethod`, `swp:assertedBy` / `swp:quotedBy` (Graph→Warrant), `swp:authority` (Warrant→Authority, cardinality 1), `swp:signature`, `swp:signatureMethod`, `swp:certificate`. *(p.5)*

## Results Summary
- Minimal extension achieves: provenance tracking, intent expression (`assertedBy` vs `quotedBy`), authority binding, cryptographic integrity (digest+signature), and compositional trust policy evaluation — all without leaving standard RDF tooling. *(p.1, p.3, p.5, p.8)*
- Backward-compatible: existing RDF tools continue to work; Named Graphs "provide a high-value but small and incremental change" to the Semantic Web Recommendations. *(p.3, p.8)*
- Comparable prior work (TRIPLE, Guha/Fikes contexts, ad-hoc reified quad-stores) is criticized as over-complex or unsafe for digital signatures. *(p.2, p.3, p.4)*
- Author-preferred policy: "the simple approach ... permits substantially quicker deployment ... is fully adequate for Semantic Web applications in the near future." *(p.3)*
- Implementations exist: NG4J, Jena MultiModel, the faceted browser at swed.org.uk. *(p.3)*

## Limitations
- Trust-acceptance algorithm is *sound but incomplete* against its own "only explicitly asserted" criterion (misses mutual-assertion cycles). *(p.6)*
- No account of consistency during graph merge — undecidable in OWL Full. Recommended to plug in an external consistency checker for OWL Lite; no prescription otherwise. *(p.6)*
- Warrant graphs whose authorization cannot be checked must be treated with caution — if not authorized by the claimed authority, the warrant graph must be false. *(p.5)*
- `rdfs:subPropertyOf` / `owl:equivalentProperty` aliasing of `swp:assertedBy` can be misleading — consumers should be suspicious of aliases unless also asserted by the same author introducing them. *(p.8)*
- A GIF-only PGP certificate photo cannot distinguish multiple people with the same appearance (fn 6) — motivates richer, machine-checkable identification. *(p.7)*
- Concrete-syntax limitation: the RDF/XML-as-Named-Graph mapping has three URI-overloading problems and inherits all RDF/XML literal-as-subject and predicate-URI restrictions. *(p.2)*
- Background graph in SPARQL's RDF Dataset may re-introduce provenance-merge difficulties when merging datasets from different repositories. *(p.3)*

## Arguments Against Prior Work
- **TRIPLE [40]:** bundles data representation, core RDF/DAML-OIL semantics, and application semantics all through Horn rules. "This must be seen as a weakness." Query-language WG indicates developers prefer specifications that don't mandate Horn implementations. Named Graphs take only the graph-naming aspect of TRIPLE. *(p.2)*
- **Guha & Fikes contexts [37]:** aggregate contexts use lifting rules with possibly non-monotonic combination; universal restrictions "built into the model theory"; this is "overly complex." Feigenbaum [22] is quoted: "the Path of maximal return is more knowledge not more logic." Named Graphs keep aggregation as a monotonic merge only, pushing choice of what to aggregate to application level. *(p.3)*
- **Context approaches [37, 40, 23]:** "fail to address digital signatures, vital for financially sensitive applications." *(p.4)*
- **Quads proposals [3, 20, 28, 33]:** vary in the semantic of the fourth element (information-source vs statement-ID vs context). Named Graphs are a cleaner reformulation where the fourth element is syntactically/semantically distinguished. *(p.1)*
- **RDF reification [26]:** "well-known problems" for provenance/quoting use cases; Named-Graph-containing-a-single-triple is a principled replacement. *(p.1, p.2)*
- **Domain-specific trust ratings [1, 7, 24]:** "assume explicit and domain-specific trust ratings. Providing such ratings and keeping them up-to-date puts an unrealistically heavy burden on information consumers in many application domains." *(p.6)*

## Design Rationale
- **Why names and not contexts?** Parsimony + incremental deployment. Web technology "needs to put a high value on simplicity, and on incremental steps." *(p.3)*
- **Why intensional identification of Named Graphs (name = denotation, not rdfgraph)?** Lets multiple copies with distinct names remain distinct entities; avoids accidental identification of similar-but-separate graphs. *(p.1)*
- **Why blank-node scoping is global (ng ≠ ng' ⇒ disjoint blank sets)?** Preserves RDF's blank-node semantics; enables merge without accidental coreference across graphs. *(p.2)*
- **Why performative warrants (social-act = graph)?** Captures "I assert G" as a self-fulfilling speech act in model theory, so that asserted-by triples inside authorized warrant graphs are automatically satisfied. *(p.5, p.7)*
- **Why `swp:authority` OWL-functional?** A warrant has at most one authority — simplifies reasoning about who said what. *(p.4)*
- **Why separate `assertedBy` and `quotedBy`?** Supports syndication use case: a syndicator may carry an article (quote) without endorsing it (assert). *(p.4)*
- **Why keep signatures outside core semantics but inside model theory?** Signatures modify *operational* semantics (who gets trusted), not *theoretical* semantics (truth value). *(p.6)*
- **Why trust policy is not part of the formal semantics?** Policies are application-specific (tolerance to error, variance, domain); unified formal approach would "overkill for some, yet miss key features required by another." *(p.4)*
- **Rejected alternative:** a special modal-logic semantics to reflect conflict between graphs — rejected in favor of reusing deployed RDF/OWL semantics. *(p.4)*

## Testable Properties
- Every URIref may name at most one graph in a given set of Named Graphs (partial function `N: U ⇀ 2^T`). *(p.2)*
- Blank nodes never shared across distinct Named Graphs in the same collection. *(p.2)*
- For imports-closed sets `K`, every `owl:imports` object URI must occur as the name of some graph in `K`. *(p.2)*
- A conforming interpretation `I` satisfies `I(name(ng)) = ng` for every `ng ∈ N`. *(p.1)*
- `swp:authority` is OWL-functional: each warrant has ≤ 1 authority. *(p.4)*
- A warrant graph asserting itself via `swp:assertedBy` must be true under any authorizing interpretation. *(p.7)*
- `swp:signature` on a graph must be verifiable by the method URI dereferenced to its spec, using the certificate reachable through `swp:authority` → `swp:certificate`. *(p.8)*
- Signature input must exclude the `swp:signature` triple itself (fn 4). *(p.5)*
- A graph whose digest triple is false has been tampered with. *(p.8)*
- Trust algorithm invariant: on termination, `A ⊆ domain(N)` and for every `a ∈ A` the entailment `rdfgraph(N(a)) ∪ K ⊨ (a swp:assertedBy _:w)` held at the moment `a` was added. *(p.6)*
- `swp:assertedBy` and `swp:quotedBy` are *not* semantically interchangeable — aliasing via `rdfs:subPropertyOf`/`owl:equivalentProperty` is discouraged. *(p.8)*

## Relevance to Project
**Direct substrate reference (P1 in the substrate plan).** propstore's design commits to keeping provenance *alongside* knowledge statements without collapsing disagreement at storage time. This paper is the foundational formal treatment of that exact pattern on the Semantic Web:

- **Named graph as a provenance carrier.** Every claim/stance/context in propstore should be associated with a named graph whose name is a first-class URIref (or stable ID). Carroll et al.'s `name(ng) ∈ U` discipline directly motivates the propstore source-branch / source-of-truth layer: each assertion lives in a named container with provenance as metadata about that container.
- **Asserted-vs-quoted.** Maps cleanly onto propstore's "proposals vs commitments" distinction — heuristic/LLM outputs are `quotedBy` the system, not `assertedBy`. The paper supplies the formal vocabulary (`swp:assertedBy`, `swp:quotedBy`, `swp:authority`) that PROV-O later partially absorbed and that should appear in propstore's render/trust layer.
- **Performative warrants.** Provides a model-theoretic foundation for the claim that "X asserted Y at time T" *is itself* the social act being recorded. Useful when propstore needs to represent agent-authored commitments (human edits, signed migrations) vs machine-generated proposals.
- **Trust policy at render time, not build time.** The paper's information-consumer algorithm (Section 8.5) explicitly runs *after* ingestion — it picks an `A ⊆ domain(N)`. This matches propstore's render-layer-filters-not-build-layer-filters principle exactly.
- **Backward compatibility path.** The observation that only naming (not richer context theory) is needed informs the propstore stance that provenance infrastructure should be minimally invasive — we should not demand richer context logics than necessary.
- **Caveats for propstore.** (a) Soundness-but-not-completeness of the trust algorithm shows that any practical trust filter will miss mutual-assertion cycles — worth documenting. (b) Consistency is explicitly *not* handled — propstore's IC-merge and argumentation layers must supply what this paper omits. (c) Signature exclusion rule (fn 4) is a concrete implementation detail if we ever sign propstore source branches.

## Open Questions
- [ ] Does propstore's source-branch layer already model one-named-graph-per-branch cleanly, or do we need per-claim sub-named-graphs to capture provenance at claim granularity?
- [ ] Should propstore's stance-provenance distinguish `assertedBy` vs `quotedBy` as structurally separate, or carry a stance-type field?
- [ ] How does the warrant-graph performative model compose with subjective-logic opinions' honest-ignorance discipline? (Vacuous opinion + unsigned warrant = totally ignored? Or recorded as "quoted, not asserted"?)
- [ ] Should propstore implement the "mutual assertion" completeness gap the paper documents, or deliberately keep the same sound-but-incomplete policy?
- [ ] Which canonicalization algorithm should we adopt if/when propstore signs source branches — `JjcRdfC14N` variant from [13] or something modern?

## Related Work Worth Reading
- [13] J. J. Carroll, *Signing RDF Graphs*, 2nd ISWC, 2003 — referenced for canonicalization + digest method. Direct predecessor.
- [26] P. Hayes, *RDF Semantics*, W3C 2004 — the model theory this paper extends.
- [32] G. Klyne & J. J. Carroll, *RDF: Concepts and Abstract Syntax*, 2004 — the RDF abstract syntax defined as sets of triples.
- [36] Prud'hommeaux & Seaborne, *SPARQL Query Language for RDF*, WD 2005 — RDF Dataset comes from here; propstore's query layer lives in this lineage.
- [37] R. M. R. Guha & R. Fikes, *Contexts for the Semantic Web*, ISWC 2004 — the main critique target; relevant for propstore context theory comparisons.
- [40] M. Sintek & S. Decker, *Triple — a query, inference, and transformation language*, ISWC 2002 — second critique target; Horn-rule-heavy.
- [1] Agrawal, Domingos, Richardson, *Trust Management for the Semantic Web*, ISWC 2003 — the domain-specific trust ratings approach this paper argues against.
- [11] Bizer & Oldakowski, *Using Context- and Content-Based Trust Policies on the Semantic Web*, WWW 2004 — source for the trust-policy taxonomy (first-hand / third-party / content / gathering-process).
- [21] Eastlake, Reagle, Solo, *XML-Signature Syntax and Processing*, RFC 3275 — signature-method basis.
- [30] ITU-T X.509, 1997 — certificate format reference.
- [23] Gangemi & Mika, *Understanding the Semantic Web through Descriptions and Situations*, 2003 — one of the three "context" approaches criticized for lacking signatures.
- [31] Klyne, *Circumstance, Provenance and Partial Knowledge*, 2002 — prefigures the partial-knowledge framing used throughout.
