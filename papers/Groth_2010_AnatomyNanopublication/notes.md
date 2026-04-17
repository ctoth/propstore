---
title: "The anatomy of a nanopublication"
authors: "Paul Groth, Andrew Gibson, Jan Velterop"
year: 2010
venue: "Information Services and Use"
pages: "51-56"
doi_url: "https://doi.org/10.3233/ISU-2010-0613"
affiliations:
  - "Free University Amsterdam, Amsterdam, The Netherlands"
  - "University of Amsterdam, Amsterdam, The Netherlands"
  - "Concept Web Alliance, NBIC, Nijmegen, The Netherlands"
publisher: "IOS Press"
citation: "Information Services & Use 30 (2010) 51-56"
---

# The anatomy of a nanopublication

## One-Sentence Summary
Defines nanopublications as the smallest citable unit of scientific communication — a single core scientific statement bundled with a community-agreed minimum set of annotations (provenance, attribution, authority) — and proposes a concrete RDF/Named-Graph realization reusing existing Semantic Web ontologies (SWAN, SWP, FOAF). *(p.51-53)*

## Problem Addressed
Scholarly communication has grown to the point where finding, connecting, and curating specific core scientific statements within full papers is impractical. *(p.51)* The same scientific assertion (e.g., "malaria is transmitted by mosquitoes") exists many times across the literature; without context it cannot be validated, and its attribution, quality, and provenance cannot be determined from the statement alone. *(p.51)* Traditionally the context of a scientific statement has been implicit in the enclosing publication — but reviewing each enclosing publication in full does not scale as the volume of literature grows. *(p.51)* The paper asks: what extra components must be attached to a bare statement so that the statement itself can stand as a publication — small enough to be called a "nanopublication"? *(p.52)*

## Key Contributions
- A layered conceptual model with six precise definitions: Concept, Triple, Statement, Annotation, Nanopublication, S-Evidence. *(p.52)*
- A set of core requirements any nanopublication format must satisfy (concept id, statement id, reference to all identified entities). *(p.52-53)*
- A concrete serialization of the model as RDF **Named Graphs** with a clear correspondence between the conceptual layers and the graph structure. *(p.53)*
- An annotation vocabulary built from the **SWAN** scientific-discourse ontology (provenance, annotation, versioning) extended via **FOAF** agents. *(p.54)*
- Attribution/review/citation via the **SWP (Semantic Web Publishing)** ontology's `assertedBy` relation, including support for digital signatures on graphs. *(p.54)*
- A TRIG-syntax example showing a real nanopublication about "malaria is transmitted by mosquitoes." *(p.55)*
- **S-Evidence**: the aggregation over all nanopublications about the same statement; the mechanism by which distributed claims can be combined to reason about veracity. *(p.52, p.55)*
- Three graded compatibility tiers (Transformation, Format, Concept Wiki) and the role of the Concept Wiki as a shared identifier repository. *(p.55-56)*
- An argument that the CWA should *not* invent new specifications — the role is to identify existing technology for the aggregation use case. *(p.56)*

## Study Design (empirical papers)

*Not applicable — this is a position/design paper. No empirical evaluation, no users, no benchmarks, no datasets.*

## Methodology
Pure conceptual modelling and standards reuse. The authors:
1. Identify requirements on a nanopublication format from existing peer-reviewed publication practice (citable, attributable, reviewable, curatable, aggregatable, identifiable across the Web, extensible). *(p.52)*
2. Derive a six-level definitional hierarchy (concept → triple → statement → annotation → nanopublication → S-Evidence). *(p.52)*
3. Exhibit a realization in RDF Named Graphs, showing a one-to-one correspondence between conceptual layers and graph artifacts. *(p.53)*
4. Pull annotation vocabulary from SWAN (and via SWAN, FOAF) rather than defining new terms. *(p.54)*
5. Pull attribution machinery from SWP. *(p.54)*
6. Provide a worked TRIG example. *(p.55)*
7. Discuss aggregation via S-Evidence and the Concept Wiki. *(p.55)*
8. Define three tiers of format compatibility to describe realistic adoption paths. *(p.55-56)*

## Core Model Definitions *(p.52)*

1. **Concept** — "the smallest, unambiguous unit of thought. A concept is uniquely identifiable."
2. **Triple** — "a tuple of three concepts (subject, predicate, object)."
3. **Statement** — "a triple that is uniquely identifiable." (A statement is thus a *reifiable*, URI-addressable triple.)
4. **Annotation** — "a triple such that the subject of the triple is a statement." (Annotations talk *about* statements.)
5. **Nanopublication** — "a set of annotations that refer to the same statement and contains a minimum set of (community) agreed-upon annotations." (The minimum set is not specified in this paper; it is left to communities.)
6. **S-Evidence** — "all the nanopublications that refer [to] the same statement." (Aggregation artifact, not stored directly.)

Different communities can extend the minimum annotation set to produce subtypes of nanopublications — e.g., curated, observational, hypothetical — as suggested by Mons & Velterop [ref 4]. *(p.52)*

## Basic Format Requirements *(p.52-53)*

Any concrete format realizing the core model must provide:
- Ability to uniquely identify a concept. *(p.52)*
- Ability to uniquely identify a statement. *(p.52)*
- Ability to refer to all uniquely identified entities (the closure: whatever you identify must be referenceable). *(p.53)*

The paper emphasizes that **community agreement on the vocabulary of annotations is more important than the choice of format**. *(p.53)*

## Named Graphs Realization *(p.53)*

Named Graphs [ref 1] extend RDF by assigning a URI to an RDF graph. Named Graphs were designed for provenance tracking and context definition during aggregation — the exact use cases nanopublications require. Not yet a W3C standard at time of writing, but widely supported by quad stores: Virtuoso, 4store, NG4J. *(p.53)*

Mapping from the core model to Named Graphs: *(p.53)*
- Each triple is an RDF triple.
- Each statement is a separate Named Graph. (Each statement's graph contains one triple — the one being reified as a statement.)
- Each annotation has, as its subject, the URI of a Named Graph.
- All annotations belonging to a nanopublication are part of the same Named Graph.

**Minimum nanopublication shape:** two Named Graphs — one for the statement, one for the annotations about that statement. *(p.53)*

## Annotation Vocabulary (Section 4) *(p.54)*

Instead of inventing new terms, the paper adopts artifacts from prior work on scientific-discourse representation on the Web [ref 3]. Specifically it uses the **SWAN** series of ontologies [ref 2] and its mapping to SIOC [ref 6] as a comprehensive starting point, extracting a subset and extending only where necessary. *(p.54)*

Concrete adoption choices:
- All core statements are typed as a **SWAN Research Statement**. *(p.54)*
- SWAN's complex association capabilities for building larger discourse structures are *deliberately not used* for nanopublications, to decrease overhead on aggregators. *(p.54)*
- Instead, only SWAN's provenance, annotation, and versioning vocabulary is used. *(p.54)*

Example annotation terms (from `http://swan.mindinformatics.org/ontologies/1.2/pav.owl`): *(p.54)*
- `importedFromSource` — identifies where the research statement was extracted from.
- `importedBy` — identifies what entity is responsible for importing a statement.
- `authoredBy` — identifies the author of a research statement.

SWAN extends **FOAF** [ref 8], so people, organizations, and software agents can be represented. To understand a nanopublication, a system should understand the subclasses of `foaf:Agent` — `Person`, `Organization`, `Group`. *(p.54)*

## Attribution, Review, Citation (Section 5) *(p.54)*

Annotations describe things *about* a statement (who authored it, when, with what software). But sometimes you need to talk about a nanopublication *as a whole* — to claim attribution on it, to let a reviewer approve it, or to vote for or cite it. *(p.54)*

The SWAN provenance ontology covers annotations inside a nanopublication but **does not provide a good mechanism for claiming the contents of a nanopublication**. *(p.54)* To fill the gap, the paper proposes using the **Semantic Web Publishing (SWP)** ontology (at `http://www.w3.org/2004/03/trix/swp-1/`). *(p.54)*

Key SWP facilities:
- `assertedBy` — relates a Named Graph to an entity (an authority). An entity uses `assertedBy` to state that it asserts (and thus claims) a nanopublication. *(p.54)*
- Digital signatures can be expressed over each graph. Signatures may be important for verifying claims. *(p.54)*

Because there is often more than one nanopublication about the same statement, the `assertedBy` mechanism is what distinguishes the competing accounts of that statement — users (software or human) decide which they trust by whatever heuristics they use. *(p.54)* This notion of different views/accounts of the same statement is inspired by the **Open Provenance Model** [ref 5]. *(p.54)*

Attribution is called out as essential. Other metadata (e.g., reviews, institutional association, collection membership) is left open for communities. *(p.54)*

## Figure 2 — Worked TRIG Example *(p.55)*

```trig
@prefix swan: <http://swan.mindinformatics.org/ontologies/1.2/pav.owl> .
@prefix cw:   <http://conceptwiki.org/index.php/Concept>.
@prefix swp:  <http://www.w3.org/2004/03/trix/swp-1/>.
@prefix :     <http://www.example.org/thisDocument#> .

:G1  = { cw:malaria cw:isTransmittedBy cw:mosquitoes }

:G2  = { :G1 swan:importedBy cw:TextExtractor,
         :G1 swan:createdOn "2009-09-03"^^xsd:date,
         :G1 swan:authoredBy cw:BobSmith }

:G3  = { :G2 ann:assertedBy cw:SomeOrganization }

:G9  = { :G1 ann:isApprovedBy cw:JohnSmith }
:G10 = { :G9 ann:isAssertedBy cw:ApprovalTrackingSystem }
```

Reading the example *(p.55)*:
- `:G1` is the **statement graph** — the triple (malaria, isTransmittedBy, mosquitoes).
- `:G2` is the **annotation graph** on `:G1` — three provenance annotations about `:G1` (imported by a TextExtractor, created 2009-09-03, authored by Bob Smith).
- `:G3` asserts `:G2` by `cw:SomeOrganization` — i.e., SomeOrganization stands behind the whole annotation bundle for `:G1`. This is the nanopublication's top-level attribution.
- `:G9` records an approval annotation directly on the statement (John Smith approves `:G1`). `:G10` asserts `:G9` by an ApprovalTrackingSystem. This shows how review/approval layers stack on top of the statement via further graphs.

Syntax: TRIG [ref 9]. *(p.55)*

**Note:** the `ann:` prefix is used in the figure without a declaration; in the paper's text this is understood as "annotation" terms (e.g., SWP-style relations). This is a minor notational slip in the paper rather than a deliberate omission.

## Aggregation and the Concept Wiki (Section 7) *(p.55)*

The model introduces **S-Evidence** — all nanopublications about the same statement — as the unit over which aggregators operate. An aggregator's job:
- Find, filter, and combine evidence for a statement. *(p.55)*
- Ascertain the veracity of a statement from that evidence. *(p.55)*

Separating statements from annotations lets a consumer reason over only statements, only annotations, or condensed annotation summaries. *(p.55)*

The practical key to making S-Evidence work: **publishers must use the same identifiers for statements and concepts**. In the model this is not *required* — any Semantic Web resource can be used — but to make aggregation easy, publishers should follow Linked Data principles and point to resources already available on the Web. *(p.55)*

The CWA hosts the **Concept Wiki** — a repository of uniquely identifiable, unambiguous URLs for concepts. By referring to Concept Wiki URIs, nanopublication publishers make their output more aggregable. The CWA itself operates as an aggregator that maps resources used in nanopublications onto Concept Wiki concepts. Nanopublications that already use Concept Wiki URIs aggregate more easily. *(p.55)*

### Three Compatibility Levels *(p.55-56)*

1. **Transformation Compatible** — data can be transformed into CWA format via an existing tool. *(p.55)*
2. **Format Compatible** — nanopublications already use the CWA model and endorsed serialization. *(p.55-56)*
3. **Concept Wiki Compatible** — format compatible *and* use only Concept Wiki identifiers. *(p.56)*

The Concept Wiki additionally lets users easily create nanopublications, follows Linked Data principles, and exposes programmatic access in whatever format the CWA current specification stipulates. *(p.56)*

The paper notes hope for compatibility with **aTags** — a convention for representing annotated research statements using the SIOC vocabulary [ref 7] — and the existing tools that already work with aTags. *(p.56)*

## Conclusion (Section 8) *(p.56)*

The paper frames its contribution as "an initial model and format" for nanopublications, built on existing community ontologies. The CWA's format working group is to specify a minimal common format enabling aggregation and preservation of provenance. Explicitly: **the CWA working group aims not to develop new specifications** but to identify existing technology and formats suitable for aggregating nanopublications. *(p.56)*

## Key Equations / Statistical Models

*No mathematical equations or statistical models appear in the paper.* The formal content is logical/structural rather than quantitative.

## Parameters

*Small conceptual paper. The only structural "parameter" is the minimum graph count for a valid nanopublication. Numeric thresholds are not otherwise given.*

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Minimum Named Graphs per nanopublication | — | count | 2 | ≥2 | p.53 | Statement graph + annotation graph; further graphs for attribution/review stack on top. |
| Minimum annotations per nanopublication | — | count | unspecified | ≥ community-agreed min | p.52 | "A minimum set of (community) agreed-upon annotations"; concrete minimum left to communities. |

## Effect Sizes / Key Quantitative Results

*Not applicable — no empirical evaluation reported. No effect sizes, accuracies, CIs, or p-values are given.*

## Methods & Implementation Details
- Serialization medium: RDF Named Graphs. *(p.53)*
- Concrete syntax in examples: TRIG [ref 9]. *(p.55)*
- Annotation vocabulary source: SWAN provenance/annotation/versioning ontology (`pav.owl` at `http://swan.mindinformatics.org/ontologies/1.2/pav.owl`). *(p.54)*
- Agent vocabulary source: FOAF (via SWAN). Required subclasses: `Person`, `Organization`, `Group`. *(p.54)*
- Attribution vocabulary source: Semantic Web Publishing ontology at `http://www.w3.org/2004/03/trix/swp-1/`; key property `assertedBy`. *(p.54)*
- Concept URI source for interoperability: Concept Wiki (`http://conceptwiki.org/index.php/Concept`). *(p.55)*
- Supporting quad stores named in the paper: Virtuoso, 4store, NG4J. *(p.53)*
- Aggregation unit: **S-Evidence** — set of all nanopublications referring to the same statement. *(p.52, p.55)*
- Digital signatures: supported via SWP, applied per Named Graph. *(p.54)*
- Subtype extensibility: communities may define additional annotation sets to produce specialized nanopublication types (curated / observational / hypothetical per Mons & Velterop [ref 4]). *(p.52)*
- The paper does not specify (and explicitly defers): the minimum annotation set, versioning/retraction of nanopublications, or a normative identifier scheme beyond "use Linked Data principles." *(p.52, p.56)*

## Figures of Interest
- **Fig. 1 (p.53)** — "The nanopublication model." A stacked layered diagram: rows labelled *Concepts* (three colored diamonds = distinct concepts), *Triples* (one triple arrow linking three concepts), *Statements* (a triple boxed and labelled `S1`, making it a reifiable unit), *Annotations* (`S1 → blue diamond` — an annotation triple whose subject is `S1`), *Nano-publication* (one statement `S1` + three annotations on it, boxed together and labelled `N1`). A separate panel labelled **S-Evidence** shows three overlapping/nested boxes `N1`, `N2`, `N3` each containing an `S1` — visually encoding "all nanopublications about the same statement."
- **Fig. 2 (p.55)** — Worked TRIG example (reproduced in this notes file above). Shows two statement/annotation graphs (`G1`, `G2`), a top-level attribution graph (`G3`), and a stacked approval/tracking pair (`G9`, `G10`).

## Results Summary
Conceptual paper; no empirical evaluation is performed. The "result" is the model plus its RDF realization. The paper claims feasibility by construction: every required capability is supplied by an existing, implemented Semantic Web standard or ontology (Named Graphs, SWAN, SWP, FOAF, TRIG, quad stores). *(p.53-56)*

## Limitations
- No formal evaluation, user study, or implementation benchmark. *(implicit across paper; confirmed by absence through p.56)*
- The **minimum annotation set** that distinguishes a valid nanopublication is not specified — it is explicitly deferred to community agreement. *(p.52, p.54)*
- Named Graphs were not yet a W3C standard at time of publication. *(p.53)*
- No discussion of **versioning, update, or retraction** of nanopublications. *(p.56)*
- No specified mechanism for **identifier alignment** across publishers; the paper acknowledges that in practice any Semantic Web resource can be used and merely encourages Linked Data practice and Concept Wiki URIs. *(p.55)*
- The `ann:` prefix is used in Fig. 2 without a formal declaration. Minor but indicative — the paper is exhibiting a shape, not fixing a normative vocabulary.
- No formal attack semantics / conflict handling between competing nanopublications of the same statement beyond "users decide by whatever heuristics they use." *(p.54)* The paper lays groundwork for aggregation but not for argumentation.

## Arguments Against Prior Work

### Against the full scientific publication as the unit of communication *(p.51)*
- With literature volume growing, finding specific core statements inside full papers is increasingly impractical.
- Statements redundantly appear across many sources; attribution/quality/provenance cannot be assessed from the bare statement alone.
- Taking each statement "in full view of its context" (the full publication) is becoming a practical impossibility at scale.

### Against ad-hoc or tool-specific statement extraction *(p.52)*
- Many systems facilitate statement creation or extraction (RDFa, text extractors, de novo generators), and their number will grow.
- Without a common format that preserves context, these statements cannot be aggregated reliably — which is the point of extracting them in the first place.

### Against inventing new specifications *(p.53, p.56)*
- The CWA working group's explicit stance: identify existing technology, do not invent new specifications.
- The paper reuses Named Graphs, SWAN, SWP, FOAF, and TRIG rather than defining new ones — arguing that what matters is community convergence on an annotation vocabulary, not invention of novel formats.

### Against uncontextualized scientific claims *(p.51)*
- A scientific statement can be validated only with its context; making that context machine-readable (as annotations) is prerequisite to hypothesis-building from linked statements.

### Against aggregation without shared identifiers *(p.55)*
- Without shared concept/statement identifiers, S-Evidence collapses: you cannot tell that two nanopublications are "about the same statement." The Concept Wiki is proposed precisely to remove this ambiguity.

## Design Rationale

### Why a layered definitional hierarchy *(p.52)*
Each level of the hierarchy (concept → triple → statement → annotation → nanopublication → S-Evidence) adds exactly one capability: identifiability, composition, reifiability, meta-ness, bundling, aggregation. Each level is independently useful and reusable across communities, which keeps the model minimal while admitting extension per community.

### Why Named Graphs *(p.53)*
Named Graphs already provide the one primitive nanopublications need — assigning a URI to an RDF graph — with existing quad-store support. They were expressly designed for provenance and context-tracking during aggregation, which is the nanopublication use case. Choosing Named Graphs avoids inventing a new reification scheme and reuses infrastructure.

### Why SWAN for annotation vocabulary *(p.54)*
SWAN was already developed for scientific discourse representation, already includes provenance/annotation/versioning vocabulary, and already extends FOAF for agents. Reusing SWAN avoids vocabulary duplication and ensures compatibility with existing biomedical discourse tooling. The paper deliberately chooses a *subset* of SWAN (no complex discourse associations) to decrease aggregator overhead.

### Why SWP for attribution *(p.54)*
SWAN describes facts about annotations within a nanopublication but does not provide a clean "who stands behind this?" mechanism. SWP's `assertedBy` (Named-Graph → authority) fills this gap, and SWP brings graph-level digital signatures for verification. The design lets multiple authorities independently assert the same statement/nanopublication without editing its contents.

### Why S-Evidence as a distinct concept *(p.52, p.55)*
Aggregation of scientific claims is the point of making statements machine-addressable. S-Evidence names the aggregation unit (all nanopubs about a given statement), making it first-class so that aggregators, reasoners, and UIs can operate over it. Separating the *set* of nanopubs from each individual nanopub keeps the model compositional.

### Why three compatibility tiers *(p.55-56)*
Full adoption (Concept Wiki Compatible) is unrealistic in the short term. Tiering gives publishers a migration path: start transformable, move to format-native, eventually adopt the shared identifier space. The tiers also let aggregators report partial wins rather than all-or-nothing compatibility.

### Why Concept Wiki *(p.55-56)*
Identifier alignment is the hard coordination problem for cross-publisher aggregation. A centralized, Linked-Data-practicing concept repository solves the coordination problem without forcing every publisher onto one ontology — they can point to Concept Wiki URIs instead of minting their own.

### Why not specify the minimum annotation set *(p.52, p.54)*
Communities differ in their annotation needs (biomedical provenance differs from, e.g., software citations). Hard-coding the minimum would either bloat the model for communities that don't need it or exclude communities whose needs differ. The paper defers to community process on purpose.

## Testable Properties
- A valid nanopublication contains **at least two** Named Graphs (one statement, one annotation set). *(p.53)*
- Every annotation triple in a nanopublication has the URI of a Named Graph as its subject. *(p.53)*
- All annotations belonging to one nanopublication live in the same Named Graph. *(p.53)*
- A Statement is a uniquely identifiable Triple; a Triple is three Concepts; therefore every Statement transitively identifies three identifiable Concepts. *(p.52)*
- `S-Evidence(s) = { np | np contains statement s }` — i.e., S-Evidence for a statement `s` is exactly the set of nanopublications whose statement graph is `s`. *(p.52, p.55)*
- `assertedBy` on a Named Graph may carry/support a digital signature per SWP. *(p.54)*
- A nanopublication contains a "minimum set of (community) agreed-upon annotations" — the check is community-relative, not universal. *(p.52)*
- Distinct nanopublications *can* exist for the same statement and are distinguished by their `assertedBy` authorities. *(p.54)*
- Two nanopublications are in the same S-Evidence iff their statement graphs serialize the same triple under the publisher's chosen URIs. Shared URIs (Concept Wiki) make this check cheap. *(p.55)*

## Relevance to Project

**High.** This is the direct antecedent of the micropublications model (Clark 2014) that propstore's claim/provenance shape is aligned with. The shape of the substrate matches propstore in specific ways:

- **Statement graph / annotation graph separation** maps onto propstore's decomposition of a claim from its provenance + context. Each claim is citable and annotatable independently of the provenance bundle.
- **`assertedBy` for competing authorities** maps onto propstore's "never collapse disagreement in storage" discipline — multiple authorities can independently assert the same claim, and propstore stores all of them until render time.
- **S-Evidence = set of all nanopublications about the same statement** maps cleanly onto propstore's substrate where multiple stances, normalizations, and supersessions co-exist for the same underlying proposition. The nanopublication paper does not yet include attack/conflict structure — that is what argumentation frameworks supply on top.
- **Deliberate non-commitment on the minimum annotation set** mirrors propstore's philosophy of pushing commitments to render time rather than storage time.
- **Concept Wiki / Linked Data identifier discipline** corresponds to propstore's concept registry and frame-level vocabulary reconciliation (Fillmore 1982 / lemon / Buitelaar 2011).
- **Named Graphs as a concrete serialization substrate** are relevant to propstore's git-backed repo if/when an RDF interchange format is needed (e.g., for exporting branch-level assertions with provenance).

What this paper does **not** supply and propstore's argumentation/render layers must add:
- A formal notion of *conflict* between competing statements (Dung AF, ASPIC+).
- A notion of *preference ordering* or *supersession* of rival statements.
- A formal non-commitment discipline at storage time.
- Calibrated uncertainty / vacuous opinions (Jøsang 2001).

The nanopublication's storage shape is substantively useful as an interchange target; its argumentation shape is intentionally absent, which is correct for a "minimum citable unit" but means propstore cannot adopt the paper wholesale.

## Open Questions
- [ ] Which minimum annotation set (if any) did the CWA working group eventually converge on? (The paper defers this.)
- [ ] How does nanopublication **identity** behave when the same statement appears with different annotations — is the nanopub's identity the statement-URI + annotation-URI bundle, or statement-URI alone? The paper implies the former via "a set of annotations referring to the same statement" but does not give an explicit URI scheme for the nanopub itself.
- [ ] How should **retraction / versioning** work across nanopublications of the same statement? (Not addressed.)
- [ ] Given two nanopubs with the same statement but conflicting annotations (e.g., different `authoredBy`), is that a data problem, a provenance problem, or expected? (The paper shrugs and defers to user heuristics.)
- [ ] Does `ann:` in Fig. 2 correspond to SWP, or is it a distinct "annotation" vocabulary? The figure does not declare the prefix.
- [ ] How does this relate structurally to Clark et al. 2014 "Micropublications" — is the micropublication a strict superset (claim + argumentation) of the nanopublication (statement + provenance)?

## Related Work Worth Reading (from the paper's bibliography) *(p.56)*
- **[1] Carroll, Bizer, Hayes, Stickler (2005)** "Named graphs, provenance and trust" — the foundational Named Graphs paper. Already a likely lead from the Clark 2014 micropublications paper.
- **[2] Ciccarese, Wu, Wong, Ocana, Kinoshita, Ruttenberg, Clark (2008)** "The SWAN biomedical discourse ontology," *J. Biomed. Informatics* 41:739-751. Source ontology for the annotation vocabulary used here.
- **[3] Groza, Handschuh, Clark, Shum, Waard (2009)** "A short survey of discourse representation models," SWASD 2009. Surveys the landscape Groth 2010 is picking pieces from.
- **[4] Mons, Velterop (2009)** "Nano-publication in the e-science era," SWASD 2009. The *prior* nanopublication paper — the one that first proposes the concept, and the source of the "curated/observational/hypothetical" subtyping idea cited in Groth 2010.
- **[5] Open Provenance Model** — source of the "different accounts of the same statement" notion used in attribution.
- **[6] Passant, Ciccarese, Breslin, Clark (2009)** "SWAN/SIOC: aligning scientific discourse representation and social semantics," SWASD 2009. SWAN ↔ SIOC mapping referenced when setting up the annotation vocabulary.
- **[7] Samwald, Stenzhorn (2009)** "Simple, ontology-based representation of biomedical statements through fine-granular entity tagging and new web standards," Bio-Ontologies 2009. Source of the aTags convention the paper hopes to interoperate with.
- **[8] FOAF project** — the agent vocabulary.
- **[9] TriG** — the concrete syntax used in Fig. 2.
