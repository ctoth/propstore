---
title: "Towards Identity in Linked Data"
authors: "James P. McCusker and Deborah L. McGuinness"
year: 2010
venue: "OWL: Experiences and Directions (OWLED 2010)"
doi_url: null
pages: 10
produced_by:
  agent: "GPT-5 Codex"
  skill: "paper-reader"
  status: "stated"
  timestamp: "2026-05-02T00:42:29Z"
---
# Towards Identity in Linked Data

## One-Sentence Summary

McCusker and McGuinness argue that `owl:sameAs` is too strong for many Linked Data identity links and propose an Identity Ontology that separates identity-like relations by reflexivity, symmetry, and transitivity while allowing selective reconstruction of isomorphic inference. *(p.1, p.5-9)*

## Problem Addressed

Linked Data practice often uses `owl:sameAs` to connect entities across datasets, but the OWL semantics impose strict identity: if two resources are the same, all statements about one are inherited by the other. This produces problematic or catastrophic merges when provenance, context, incomplete representations, belief-like assertions, or domain-specific distinctions matter. *(p.1-3)*

The paper targets the gap between real Linked Data usage and formal identity semantics. The authors accept that some applications require inference, but they reject applying full isomorphism to every identity-like link. *(p.2, p.5)*

## Key Contributions

- Identifies isomorphic inference as the core technical hazard in broad `owl:sameAs` use: all predicates of one resource become predicates of the other, even when the link only meant "similar", "represents", "same cell line", or "more information about". *(p.1-3)*
- Gives biomedical biospecimen examples where `owl:sameAs(LA, LB)` merges creation dates, quantities, passages, provenance, and derivation edges across distinct specimens, making one specimen appear derived from itself. *(p.2-4)*
- Extends the critique beyond provenance to knowledge representation: assertions about Superman/Clark Kent and Istanbul/Constantinople show that substitution can corrupt contextual, belief-like, or temporal identity statements. *(p.4-5)*
- Proposes the Identity Ontology (IO), a set of eight identity-like properties derived from combinations of reflexivity, symmetry, and transitivity. *(p.5-8)*
- Maps existing `owl:sameAs`, `rdfs:seeAlso`, `skos:exactMatch`, `skos:closeMatch`, and `skos:related` into the IO hierarchy to support interoperability. *(p.5-6, p.8)*
- Shows how SPARQL query patterns and OWL 2 property chains can reconstruct isomorphic behavior only for selected identity relations and selected properties. *(p.8-9)*

## Study Design (empirical papers)

Not an empirical evaluation paper. The argument is a modeling and ontology-design paper supported by motivating examples from biomedical data integration, FOAF identity, and philosophical/epistemological substitution cases. *(p.1-10)*

## Methodology

The paper uses a problem-driven ontology design method:

1. Analyze `owl:sameAs` through the lens of mathematical identity and the indiscernibility of identicals. *(p.1)*
2. Collect failure modes where full substitutivity makes Linked Data integration less correct or less useful. *(p.2-5)*
3. Decompose `owl:sameAs` into three meta-properties: transitivity, symmetry, and reflexivity. *(p.5)*
4. Enumerate all eight combinations of those meta-properties as a small ontology of identity-like relations. *(p.5-6)*
5. Position existing OWL/RDFS/SKOS relations under the new hierarchy and describe domain-specific subproperties as the intended extension mechanism. *(p.5-8)*
6. Recover full or partial isomorphism only where explicitly requested, using SPARQL or OWL 2 property-chain axioms. *(p.8-9)*

## Key Equations / Statistical Models

The paper states Leibnizian identity / indiscernibility of identicals as the basis for `owl:sameAs` isomorphism:

$$
a = b \land p(a, x) \Rightarrow p(b, x)
$$

Where: `a` and `b` are entities/resources, `p` is any predicate, and `x` is an object/value; if `a` is identical to `b`, every true statement involving `a` is inherited by `b`. *(p.1)*

The paper gives a SPARQL pattern for recovering isomorphic statements from a reflexive identity relation:

```sparql
select ?s, ?p, ?o
where {
  ?s id:identical ?x.
  ?x ?p ?o.
}
```

Where: `?s` is the source entity, `id:identical` can be replaced by another domain-specific identity property, and `?x ?p ?o` obtains statements from the related entity. *(p.8)*

The paper gives an OWL 2 property-chain pattern for selective isomorphism:

$$
SubObjectPropertyOf(ObjectPropertyChain(identical, p), p)
$$

Where: `identical` is an identity property and `p` is a property for which values should be propagated across that identity relation. This makes only chosen properties isomorphic instead of globally applying `owl:sameAs` semantics. *(p.9)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Identity meta-properties | - | count | 3 | reflexive, symmetric, transitive | 5 | The IO design space is generated from these three properties. |
| Identity Ontology properties | - | count | 8 | all combinations of reflexive/non-reflexive, symmetric/non-symmetric, transitive/intransitive | 6 | Listed in Table 1. |
| Patient A visit date | - | date | 7/8/09 | - | 3 | Biospecimen example provenance/data value. |
| Patient A date of birth | - | date | 2/3/45 | - | 3 | Biospecimen example. |
| Patient A diagnosis | - | diagnosis | Melanoma | - | 3 | Biospecimen example. |
| Tumor T creation date | - | date | 7/8/09 | - | 3 | Derived from Patient A. |
| Tumor T quantity | - | g | 5 | - | 3 | Source tumor quantity in Fig. 1. |
| Specimen LB creation date | - | date | 8/31/09 | 8/31/09 or 9/20/09 after sameAs merge | 3-4 | Becomes ambiguous after `owl:sameAs(LA, LB)`. |
| Specimen LB quantity | - | g | 5 | 5 or 10 after sameAs merge | 3-4 | Demonstrates unwanted isomorphic inheritance. |
| Specimen LB passage | - | count | 0 | 0 or 10 after sameAs merge | 3-4 | Demonstrates unwanted isomorphic inheritance. |
| Specimen LA creation date | - | date | 9/20/09 | 9/20/09 or 8/31/09 after sameAs merge | 3-4 | Becomes ambiguous after `owl:sameAs(LA, LB)`. |
| Specimen LA quantity | - | g | 10 | 10 or 5 after sameAs merge | 3-4 | Demonstrates unwanted isomorphic inheritance. |
| Specimen LA passage | - | count | 10 | 10 or 0 after sameAs merge | 3-4 | Demonstrates unwanted isomorphic inheritance. |
| ArrayExpress experiments integrated | - | count | 2 | E-TABM-65 and E-MEXP-1029 | 9 | Used in early IO application with NCI-60 cell lines. |

## Effect Sizes / Key Quantitative Results

No statistical effect sizes or empirical quantitative results are reported. The paper's quantitative content is confined to the ontology's eight-property design space and example data values. *(p.1-10)*

## Methods & Implementation Details

- `owl:sameAs` is treated as strict mathematical identity, not a loose link. Its entailment behavior makes statements of `a` and `b` shared by both. *(p.1)*
- Halpin and Hayes identify four Linked Data uses of `owl:sameAs`: same thing but different context, same thing but referentially opaque, represents, and very similar to. The authors argue these uses should not all be represented by a single full-identity predicate. *(p.2)*
- The biomedical example has Patient A, tumor specimen T, cell-line specimens LB and LA, and datasets D and E. D uses LB and E uses LA; asserting `owl:sameAs(LA, LB)` integrates the datasets but merges dates, quantities, passages, and derivation relationships. *(p.2-4)*
- Named graphs are rejected as a complete solution because identity statements may already be embedded in named graphs and users would need to extract and relocate identity statements. *(p.3)*
- OWL 2 annotations are rejected as a complete solution because many "provenance" facts are first-class data in the originating domain model; one user's provenance is another user's data. *(p.3)*
- The knowledge-representation examples translate belief/substitution puzzles into Semantic Web assertion contexts: "Lois Lane claims Superman can fly" plus "Superman and Clark Kent are the same person" can infer claims that contradict the original assertion context. *(p.4)*
- IO domain-specific properties should be created as subproperties of one of the eight IO properties. This preserves broad interoperability while letting domain experts retain precise semantics. *(p.5)*
- A mapping ontology aligns IO properties with RDFS, OWL, and SKOS properties, including `owl:sameAs`, `skos:exactMatch`, `skos:closeMatch`, `skos:related`, and `rdfs:seeAlso`. *(p.5-8)*
- `id:identical` is the most restrictive IO property and has `owl:sameAs` as a subproperty, preserving existing valid identity assertions while keeping other IO identity properties weaker. *(p.6)*
- `id:claimsIdentical` supports one entity claiming another without requiring inverse truth; a "representedBy" subproperty can model representation. *(p.7)*
- `id:matches` supports strong, intransitive matching inspired by `skos:exactMatch`; many current Linked Data identities would be better represented here than by `owl:sameAs`. *(p.7)*
- `id:similar` supports domain-specific similarity such as two biospecimens belonging to the same cell line; a `sameCellLineAs` subproperty is the suggested pattern. *(p.7)*
- `id:claimsSimilar` supports asymmetric substitutions, such as one drug/product being usable in place of another without reciprocity. *(p.8)*
- `id:related` supports symmetric association without identity, similarity, or matching claims; it is aligned with SKOS/OBO relatedness. *(p.8)*
- `id:claimsRelated` is the loosest relation and is aligned with `rdfs:seeAlso`; a depiction is the example of a non-symmetric, non-transitive, non-reflexive identity-like relation. *(p.8)*
- Selective isomorphism can be implemented by replacing `id:identical` in the SPARQL query with a domain-specific identity property or by defining OWL 2 property chains for specific propagated properties. *(p.8-9)*
- The authors report early usage of IO in biomedical datasets by integrating ArrayExpress experiments E-TABM-65 and E-MEXP-1029, converting data to RDF with MAGETAB2RDF, and aligning biological sources with `biomedidentity:sameAsBioSource`. *(p.9)*

## Figures of Interest

- **Fig. 1 (p.3):** Biospecimen derivation graph before `owl:sameAs`: Patient A yields tumor specimen T; T derives specimen LA; LA derives specimen LB; datasets D and E refer to different specimens in the same cell line.
- **Fig. 2 (p.4):** The same graph after `owl:sameAs(LA, LB)`: LA and LB inherit each other's creation dates, quantities, passages, dataset usages, and derivation edges, making LA appear derived from itself.
- **Table 1 (p.6):** The full IO design space: eight identity-like properties generated from reflexive/non-reflexive, symmetric/non-symmetric, and transitive/intransitive combinations.
- **Fig. 3 (p.6):** Subproperty hierarchy connecting IO relations with `owl:sameAs`, `skos:exactMatch`, `skos:closeMatch`, `skos:related`, and `rdfs:seeAlso`.

## Results Summary

The paper concludes that `owl:sameAs` is not wrong, but it is only one point in a larger identity design space. Many Linked Data identity links need weaker or more contextual relations to avoid unwanted isomorphic inference. IO provides additional identity properties and makes inference more granular: applications can retain inference where useful without globally merging all facts for linked resources. *(p.9-10)*

## Limitations

- The paper is primarily conceptual and example-driven; it does not provide a formal semantics beyond the property taxonomy and property-chain pattern. *(p.5-10)*
- The reported biomedical application is preliminary: the authors say they "have begun to use IO" and "plan to continue" investigating identity properties, so the implementation evidence is early. *(p.9)*
- Adoption is not solved. Existing datasets already using `owl:sameAs` must choose or migrate to more precise identity predicates for the model to have practical effect. *(p.1-10)*
- The paper does not provide an automatic classifier for choosing which IO relation applies to a given Linked Data link. *(p.5-10)*
- The property hierarchy risks semantic subtlety for publishers: users must understand reflexivity, symmetry, transitivity, and domain-specific subproperty design. *(p.5-8)*

## Arguments Against Prior Work

- The authors challenge the Linked Data convention of reusing `owl:sameAs` whenever two dataset entities are "the same", because its formal semantics imply full isomorphism rather than contextual linking. *(p.1)*
- They respond to the argument that applications rarely use inference by noting that some Linked Data applications, including their examples, benefit from and require inference. The problem is not inference itself but indiscriminate identity inference. *(p.2)*
- They cite erroneous `owl:sameAs` mappings in DBpedia/DBLP and issues combining FOAF profiles as evidence that `owl:sameAs` is already being stretched beyond strict identity. *(p.2)*
- Named graphs and OWL 2 annotations are criticized as limited remedies: they either require moving identity statements out of existing graph contexts or assume provenance can be cleanly segregated into annotations. *(p.3)*
- The paper critiques `owl:sameAs` as the single available mechanism for Halpin and Hayes's four uses, because "represents" and "very similar to" do not entail full substitutability. *(p.2, p.5-8)*

## Design Rationale

- The identity design space is based on combinations of reflexivity, symmetry, and transitivity because these are the meta-properties of `owl:sameAs` that determine how identity links propagate. *(p.5)*
- IO properties are organized as a hierarchy so stricter relations imply weaker relations where appropriate. For example, identity implies matching and similarity, but similarity does not imply identity. *(p.6-8)*
- Domain-specific subproperties are preferred over using IO properties directly for every domain distinction. This gives domain experts readable names such as `sameCellLineAs` while preserving machine-readable alignment to a general identity category. *(p.5, p.7)*
- Isomorphism is reconstructed rather than asserted globally. This lets users query or infer selected statements when warranted while preventing blanket inheritance of provenance or context-sensitive assertions. *(p.8-9)*
- Existing valid `owl:sameAs` assertions are preserved by making `owl:sameAs` a subproperty of `id:identical`; the new model is not a rejection of strict identity but a way to avoid overusing it. *(p.6)*

## Testable Properties

- If `owl:sameAs(a, b)` is used under OWL identity semantics, then statements about `a` are inherited by `b` and statements about `b` are inherited by `a`. *(p.1)*
- If `owl:sameAs(LA, LB)` is asserted in the biospecimen example, LA and LB inherit multiple creation dates, quantities, passages, and derivation relationships. *(p.2-4)*
- `id:identical` is reflexive, symmetric, and transitive. *(p.6)*
- `id:claimsIdentical` is reflexive and transitive but not symmetric. *(p.6-7)*
- `id:matches` is reflexive and symmetric but intransitive. *(p.6-7)*
- `id:claimsMatches` is reflexive only. *(p.6-7)*
- `id:similar` is reflexive and symmetric but intransitive. *(p.6-7)*
- `id:claimsSimilar` is reflexive only and supports non-reciprocal similarity claims. *(p.6-8)*
- `id:related` is symmetric only and does not imply similarity, matching, or identity. *(p.6, p.8)*
- `id:claimsRelated` has no reflexivity, symmetry, or transitivity and can model depiction or see-also-like relations. *(p.6, p.8)*
- A property-chain axiom of the form `SubObjectPropertyOf(ObjectPropertyChain(identical, p), p)` should propagate only property `p` across the chosen identity relation. *(p.9)*

## Relevance to Project

This paper is highly relevant to propstore's identity, concept reconciliation, and merge semantics. It gives a compact vocabulary for saying "same enough for this purpose" without collapsing all facts into a single canonical identity. That aligns with propstore's non-commitment discipline: source-local claims, context, and provenance should not be destroyed by a premature canonical merge. The selective-isomorphism pattern is especially relevant to render-time or query-time identity policies: a world may choose to propagate some predicates across an identity relation while keeping other predicates source-local or context-bound.

## Open Questions

- [ ] Should propstore represent identity-like relations with a fixed IO-style lattice, or with typed relation properties plus declared algebraic traits?
- [ ] How should propstore decide which claim predicates are safe to propagate across a given identity relation?
- [ ] Can provenance-bearing source-local claims be protected by default while still permitting selective canonical inference?
- [ ] Should concept reconciliation expose relations analogous to `id:matches`, `id:similar`, and `id:claimsRelated` instead of a binary merge/not-merge decision?
- [ ] How should conflicting source identity assertions be adjudicated when one source claims strict identity and another only claims similarity?

## Related Work Worth Reading

- Halpin and Hayes (2008), "When owl:sameAs isn't the Same": source of the four `owl:sameAs` usage categories and a foundational critique of identity links. *(p.2, p.10)*
- Ding et al. (2010), "An Empirical Study of owl:sameAs Use in Linked Data": empirical companion on real-world sameAs usage. *(p.2, p.10)*
- Jaffri et al. (2008), "URI Disambiguation in the Context of Linked Data": examples of erroneous mappings in DBpedia and DBLP. *(p.2, p.10)*
- SKOS Reference (2009): supplies `skos:exactMatch`, `skos:closeMatch`, and `skos:related`, which IO maps into its hierarchy. *(p.6-8, p.10)*
- OWL 2 Direct Semantics (2009): supplies the property-chain semantics used to reconstruct selective isomorphism. *(p.8-9, p.10)*

## Collection Cross-References

### Already in Collection

- [When owl:sameAs Isn't the Same: An Analysis of Identity in Linked Data](../Halpin_2010_OwlSameAsIsntSame/notes.md) — the ISWC version by overlapping authors develops the broader sameAs critique and empirical analysis; this OWLED paper is the companion ontology-design treatment that decomposes identity relations and selective isomorphism.

### New Leads (Not Yet in Collection)

- Bechhofer et al. (2004) — "OWL Web Ontology Language Reference" — primary specification for `owl:sameAs` semantics.
- Jaffri et al. (2008) — "URI Disambiguation in the Context of Linked Data" — examples of erroneous sameAs mappings in DBpedia and DBLP.
- Ding et al. (2010) — "An Empirical Study of owl:sameAs Use in Linked Data" — cited empirical study of sameAs usage; a partial paper directory exists locally but is missing standard artifacts and index coverage at this reading.
- SKOS Simple Knowledge Organization System Reference (2009) — source semantics for `skos:exactMatch`, `skos:closeMatch`, and `skos:related`.
- OWL 2 Direct Semantics (2009) — property-chain semantics needed for selective isomorphism.

### Cited By (in Collection)

- [When owl:sameAs Isn't the Same: An Analysis of Identity in Linked Data](../Halpin_2010_OwlSameAsIsntSame/notes.md) — cites this OWLED paper as companion work with deeper formal treatment of identity.
- [SameAs Networks and Beyond: Analyzing Deployment Status and Implications of owl:sameAs in Linked Data](../Ding_2010_SameAsNetworksBeyondAnalyzing/notes.md) — cites McCusker and McGuinness for provenance and ground-truth risks from strong identity assertions; the local directory is incomplete.

### Supersedes or Recontextualizes

- This paper complements rather than supersedes [When owl:sameAs Isn't the Same: An Analysis of Identity in Linked Data](../Halpin_2010_OwlSameAsIsntSame/notes.md): Halpin et al. emphasize empirical misuse and a Similarity Ontology, while this paper focuses on an Identity Ontology and selective reconstruction of isomorphism.

### Conceptual Links (not citation-based)

- [The sameAs Problem: A Survey on Identity Management in the Web of Data](../Raad_2019_SameAsProblemSurvey/notes.md) — Strong: the survey generalizes the sameAs problem space this paper formulates, including the need for alternatives to strict identity and the risks of transitive error propagation.
- [sameAs.cc: The Closure of 500M owl:sameAs Statements](../Beek_2018_SameAs.ccClosure500MOwl/notes.md) — Strong: sameAs.cc shows the large-scale closure consequences of the global identity semantics this paper warns against; IO-style relation typing is one way to avoid indiscriminate closure.
- [Not Quite the Same: Identity Constraints for the Web of Linked Data](../Melo_2013_NotQuiteSameIdentity/notes.md) — Strong: de Melo formalizes detecting erroneous identity constraints, while this paper provides a vocabulary for representing weaker-than-identity links instead of repairing them after collapse.
