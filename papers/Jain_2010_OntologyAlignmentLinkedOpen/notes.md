---
title: "Ontology Alignment for Linked Open Data"
authors: "Prateek Jain, Pascal Hitzler, Amit P. Sheth, Kunal Verma, Peter Z. Yeh"
year: 2010
venue: "ISWC 2010, The Semantic Web - ISWC 2010, LNCS 6496"
doi_url: "https://doi.org/10.1007/978-3-642-17746-0_26"
pages: "402-417"
---

# Ontology Alignment for Linked Open Data

## One-Sentence Summary
BLOOMS is a Java ontology/schema-alignment system that uses Wikipedia/DBpedia category trees as noisy bootstrapped background knowledge to discover subclass and equivalence links between Linked Open Data schemas, outperforming several contemporary matchers on LOD schema alignment. *(p.402, p.414)*

## Problem Addressed
Linked Open Data datasets were increasingly interlinked at the instance level, especially via `owl:sameAs`, but had sparse schema-level links, making cross-dataset applications difficult because class hierarchies were not aligned. *(p.402, p.403)* Existing ontology alignment systems performed acceptably on established benchmarks but poorly on LOD schema datasets, motivating a system specialized for the loose, heterogeneous, community-created LOD cloud. *(p.402, p.407)*

## Key Contributions
- Presents BLOOMS, a schema-alignment system that bootstraps from Wikipedia/DBpedia category hierarchy information rather than relying only on lexical/structural similarity of the input ontologies. *(p.402, p.404)*
- Defines a forest construction for candidate class names, compares BLOOMS trees via a normalized overlap function, and derives `rdfs:subClassOf` or `owl:equivalentClass` decisions from tree equality, overlap, and a threshold. *(p.404-p.406)*
- Adds post-processing through the Alignment API and Jena reasoner to keep high-confidence alignments and infer additional subclass alignments. *(p.406)*
- Evaluates BLOOMS against Alignment API, OMViaUO, S-Match, AROMA, and RiMOM on OAEI oriented/benchmark tracks and on LOD schema-alignment tasks. *(p.407-p.414)*
- Shows that BLOOMS gives substantially better average LOD schema-alignment performance than other evaluated systems, with average precision 0.48 and recall 0.54 versus S-Match 0.17/0.43, AROMA 0.25/0.04, Alignment API 0.07/0.01, and OMViaUO 0.17/0.00. *(p.412, p.414)*

## Study Design (empirical papers)
- **Type:** Comparative systems evaluation of ontology matching algorithms on benchmark and LOD schema-alignment datasets. *(p.407)*
- **Population:** OAEI 2009 oriented and benchmark tasks plus seven LOD schema-pair tasks derived from DBpedia, Geonames, Music Ontology, BBC Program, FOAF Profiles, SIOC, AKT Reference Ontology, and Semantic Web Conference Ontology. *(p.407, p.411, p.412)*
- **Intervention(s):** BLOOMS alignment workflow using Wikipedia/DBpedia category forests and post-processing. *(p.404-p.406)*
- **Comparator(s):** Alignment API, OMViaUO, S-Match, AROMA, and RiMOM, with availability constraints excluding some OAEI systems from LOD experiments. *(p.407, p.408)*
- **Primary endpoint(s):** Precision and recall for generated ontology/schema alignments. *(p.407, p.409-p.412)*
- **Secondary endpoint(s):** Qualitative failure analysis by schema pair and benchmark track. *(p.409-p.414)*
- **Follow-up:** None; the paper reports one evaluation and future-work directions. *(p.415-p.416)*

## Methodology
BLOOMS accepts two ontologies with schema information serialized in RDF/XML or OWL. It removes property restrictions, individuals, and properties, tokenizes class names into simple words after replacing underscores/hyphens and splitting capitalized terms, removes stop words, and uses each normalized class string as input to Wikipedia search. *(p.404, p.407)*

For each candidate class name `C`, BLOOMS obtains a set of Wikipedia pages from the Wikipedia Web service; disambiguation pages are removed and replaced by the pages they mention. The resulting pages are treated as senses `W_C` for `C`. For every sense, BLOOMS constructs a category tree rooted at the page, whose children are the Wikipedia categories of the page/category, continuing down subcategory links and cutting at level 4. The set of sense trees is the BLOOMS forest for `C`. *(p.404, p.405)*

For candidate classes `C` and `D`, BLOOMS compares every tree in `T_C` with every tree in `T_D`. It prunes from one tree nodes whose parent appears in the other tree, then computes normalized overlap from the remaining tree. Equality of a pair of trees yields equivalence; otherwise a thresholded pair of asymmetric overlaps yields a subclass direction. *(p.405, p.406)*

The system then invokes the Alignment API on the original ontologies, keeps alignments with confidence at least 0.95, adds them to the BLOOMS output, and uses Jena reasoning to infer additional alignments, finally outputting results in Alignment API format. *(p.406)*

## Key Equations / Statistical Models

$$
T_C = \{T_s \mid s \in W_C\}
$$

Where: `W_C` is the set of Wikipedia senses/pages for class name `C`; `T_s` is the BLOOMS tree rooted at sense `s`; `T_C` is the BLOOMS forest for `C`. *(p.405)*

$$
o(T_g, T_t) = \frac{n}{k - 1}
$$

Where: before computing the score, nodes in `T_g` are removed when their parent node occurs in `T_t`; `n` is the number of nodes in the pruned `T_g'` that also occur in `T_t`; `k` is the total number of nodes in `T_g'`; the root is not counted. *(p.405)*

$$
T_g = T_t \Rightarrow C\ \text{owl:equivalentClass}\ D
$$

Where: exact equality of some compared BLOOMS trees for the two candidate class names is taken as class equivalence. *(p.406)*

$$
\min\{o(T_g,T_t), o(T_t,T_g)\} \ge x
$$

Where: `x` is a predefined threshold; if the threshold holds, BLOOMS creates a subclass relation, with `C rdfs:subClassOf D` when `o(T_g,T_t) <= o(T_t,T_g)` and `D rdfs:subClassOf C` when `o(T_g,T_t) > o(T_t,T_g)`. *(p.406)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Stop-word list size | - | words | 319 | - | 404 | Stop words from the Information Retrieval Research Group of Glasgow University. |
| BLOOMS tree depth cut | - | levels | 4 | - | 405 | Branches are cut at level 4, giving maximally 5 nodes including root. |
| Alignment API post-processing confidence cutoff | - | confidence | 0.95 | - | 406 | Alignments returned by Alignment API are kept if confidence is at least this value. |
| Same-domain BLOOMS overlap threshold | x | dimensionless | 0.8 | - | 408 | Used when ontologies belong to the same domain. |
| Abstract/domain-specific BLOOMS overlap threshold | x | dimensionless | 0.6 | - | 408 | Used when one ontology is abstract, such as DBpedia or SUMO. |
| RiMOM MatchThreshold range explored | - | dimensionless | - | 0.3-0.8 | 408 | Different parameter values yielded the same output; entries as low as 0.01 appeared in output. |
| AROMA lexicalThreshold | - | dimensionless | 0.6 | <0.5 to >0.8 discussed | 408 | Below 0.5 gave poor precision; above 0.8 gave few results. |
| Alignment API and OMViaUO threshold | - | dimensionless | 0.5 | - | 408 | Authors found changing threshold to 0 did not significantly improve LOD results. |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| BLOOMS OAEI oriented average | Precision / Recall | 0.84 / 0.78 | - | - | Oriented matching track, tests 1XX/2XX/3XX | 409 |
| RiMOM OAEI oriented average | Precision / Recall | 0.75 / 0.88 | - | - | Best comparator on oriented track average recall | 409 |
| BLOOMS OAEI benchmark average | Precision / Recall | 0.57 / 0.78 | - | - | Benchmark track, tests 1XX/2XX/3XX | 410 |
| AROMA OAEI benchmark average | Precision / Recall | 0.88 / 0.81 | - | - | Strong benchmark comparator | 410 |
| RiMOM OAEI benchmark average | Precision / Recall | 0.91 / 0.88 | - | - | Strong benchmark comparator | 410 |
| BLOOMS LOD schema average | Precision / Recall | 0.48 / 0.54 | - | - | Seven LOD schema pairs | 412 |
| S-Match LOD schema average | Precision / Recall | 0.17 / 0.43 | - | - | Best recall among non-BLOOMS systems except BLOOMS, but low precision | 412 |
| AROMA LOD schema average | Precision / Recall | 0.25 / 0.04 | - | - | Comparator on LOD schemas | 412 |
| Alignment API LOD schema average | Precision / Recall | 0.07 / 0.01 | - | - | Comparator on LOD schemas | 412 |
| OMViaUO LOD schema average | Precision / Recall | 0.17 / 0.00 | - | - | Comparator on LOD schemas | 412 |

## Methods & Implementation Details
- Input ontologies are assumed to include schema information; BLOOMS uses RDF/XML or OWL serializations and parses with the Jena framework. *(p.407)*
- Preprocessing normalizes class names by replacing underscores and hyphens with spaces, splitting capitalized terms, and removing 319 stop words; stemming was not needed because Wikipedia search worked well on the resulting strings. *(p.404)*
- Wikipedia disambiguation pages are removed from candidate senses and replaced by all pages mentioned in the disambiguation page. *(p.404)*
- Each BLOOMS tree root is a Wikipedia sense/page; children are all Wikipedia categories the page is categorized in; deeper children are subcategories; trees are cut at level 4. *(p.405)*
- The comparison step removes nodes from the candidate source tree when a parent node is already present in the target tree, because such children add no essential comparison information under the BLOOMS construction. *(p.405)*
- Running example: Event and JazzFestival from DBpedia and Music Ontology produce `o(T_Event,T_JazzFestival)=3/4` and `o(T_JazzFestival,T_Event)=3/5`, yielding `Jazz Festival rdfs:subClassOf Event`. *(p.406)*
- Post-processing uses Alignment API plus Jena reasoning: high-confidence Alignment API alignments are added, then inferred alignments are found from subclass chains and existing alignments. *(p.406)*
- The authors created expert reference alignments for LOD schema evaluation because no standard LOD schema-alignment benchmarks or baselines existed; experts identified subclass and equivalence mappings using concept descriptions and references. *(p.411)*
- LOD schema selection excluded datasets whose schema was not explicitly provided to avoid unfair advantage from self-created schemas; the selection was made before evaluation and was not tailored to favor a system. *(p.412)*

## Figures of Interest
- **Fig. 1 (p.405):** BLOOMS trees for `Jazz Festival` with sense `Jazz Festival` and `Event` with sense `Event`; dark gray nodes are pruned in the running overlap example, and some categories are omitted to save space.
- **Table 1 (p.409):** OAEI oriented matching precision/recall for Alignment API, OMViaUO, S-Match, AROMA, RiMOM, and BLOOMS.
- **Table 2 (p.410):** OAEI benchmark track precision/recall; BLOOMS is competitive but trails AROMA/RiMOM in average benchmark precision and recall.
- **Table 3 (p.411):** LOD dataset/schema summary: schema, number of LOD datasets, taxonomic depth, number of classes, and linked datasets.
- **Table 4 (p.412):** LOD schema-alignment precision/recall; BLOOMS leads average precision and recall among evaluated systems.

## Results Summary
BLOOMS performs strongly on the OAEI oriented track, with average precision 0.84 and recall 0.78, close to RiMOM's 0.75 precision and 0.88 recall and ahead of most other systems. *(p.409)* On the OAEI benchmark track, BLOOMS retrieves all 1XX results but loses precision, performs better on 3XX than 2XX, and ranks behind RiMOM and AROMA in recall while maintaining decent precision. *(p.410)*

For LOD schema alignment, BLOOMS outperforms the other evaluated systems overall. It gives one of the highest recalls in 5 of 7 pairs and leads precision in 6 of 7 pairs; average precision/recall is 0.48/0.54, while other systems either have poor recall, poor precision, or fail on pairs. *(p.412, p.414)* The authors argue that S-Match can retrieve many correct relations but returns many incorrect mappings, making curation difficult; for Music Ontology/BBC Program it found 3120 relations, only 4% of which were correct. *(p.414)*

## Limitations
- The authors had not systematically investigated alternatives to Wikipedia/DBpedia as the bootstrapping source; alternatives such as Cyc, SUMO, WordNet, Open Directory Project, and YAGO are discussed only as possibilities. *(p.406)*
- Reference alignments for LOD schema evaluation were created by human experts and are acknowledged as subjective, although the authors argue there was no community-agreed alternative. *(p.411)*
- Some comparator systems could not be run on all datasets, e.g. RiMOM failed on several LOD pairs, and support requests had not been resolved at writing time. *(p.412, p.413)*
- The current BLOOMS relation space focuses on subclass/equivalence; the authors propose future work on partonomical relationships and disjointness. *(p.416)*
- The system's future scalability to ontologies larger than the evaluation schemas remains to be evaluated. *(p.416)*

## Arguments Against Prior Work
- Existing LOD interlinks are mainly instance-level and concentrated in thematic clusters; schema-level information is relatively scarce, so instance linking alone does not solve schema integration. *(p.403)*
- State-of-the-art ontology alignment systems that work on established benchmarks perform poorly on LOD schema datasets. *(p.402, p.407)*
- Systems relying primarily on lexical/syntactic matching struggle when concepts use uncommon domain language, ambiguous names, or weak structural cues, as in Geonames/DBpedia and Music Ontology/BBC Program examples. *(p.413)*
- S-Match can retrieve correct relations but generates many false positives, making output difficult to curate for practical use. *(p.414)*
- OMViaUO and Alignment API suffer in LOD settings because they fail to find required concepts or produce too many wrong mappings. *(p.410, p.413)*

## Design Rationale
- Wikipedia is chosen because it has broad thematic coverage, a community-built category hierarchy suited to community-built LOD data, and a search feature that can map input concept labels to relevant category trees without requiring controlled vocabulary matching. *(p.406)*
- BLOOMS cuts category trees at level 4 because deeper levels include very general categories such as "Humanities" that become ineffective for alignment. *(p.405)*
- The authors use higher thresholds for same-domain ontology pairs and lower thresholds when matching a domain-specific ontology to an abstract ontology, reflecting expected overlap patterns in the BLOOMS category trees. *(p.408)*
- LOD evaluation datasets were selected for known schema reuse, cross-domain coverage, and explicit public schemas, not after seeing system performance. *(p.412)*

## Testable Properties
- BLOOMS preprocessing must remove properties, property restrictions, and individuals before class-name alignment. *(p.404)*
- BLOOMS tree branches must be cut at level 4, i.e. at most 5 nodes including the root. *(p.405)*
- If any compared BLOOMS trees are equal, the output relation must be `owl:equivalentClass`. *(p.406)*
- If the minimum asymmetric overlap is below threshold `x`, the compared tree pair must not trigger a subclass relation. *(p.406)*
- If the threshold holds and `o(T_g,T_t) <= o(T_t,T_g)`, the output direction is `C rdfs:subClassOf D`; otherwise it is `D rdfs:subClassOf C`. *(p.406)*
- Alignment API post-processing should only keep returned alignments with confidence at least 0.95 before reasoning. *(p.406)*
- On the paper's LOD schema suite, BLOOMS average precision/recall should be approximately 0.48/0.54 under the described setup. *(p.412)*

## Relevance to Project
This paper is useful for propstore because it treats schema alignment as explicit relation construction with provenance-bearing decisions, thresholds, asymmetric evidence, post-processing, and expert reference alignments. BLOOMS' forest-overlap rule is a concrete candidate for representing alignment claims, supporting justifications, and preserving directional subclass/equivalence decisions rather than reducing alignment to untyped similarity scores. *(p.405-p.406, p.411-p.412)*

## Open Questions
- [ ] Would current LOD/knowledge-graph sources still make Wikipedia/DBpedia the best bootstrapping source, or would Wikidata, domain ontologies, embeddings, or curated upper ontologies dominate? *(p.406, p.416)*
- [ ] How should provenance distinguish noisy community category evidence from curated ontology evidence when both support the same alignment claim? *(p.406)*
- [ ] Can the asymmetric overlap decision rule be generalized into a typed argumentation or belief-revision surface for conflicting alignments? *(p.405-p.406)*
- [ ] How would BLOOMS behave on much larger ontologies than those in Table 3? *(p.416)*

## Collection Cross-References

### Already in Collection
- (none found among cited references; key cited works such as Euzenat 2004, Euzenat and Shvaiko 2007, Bizer et al. 2009, and UMBEL technical documentation were not found as collected papers.)

### Cited By (in Collection)
- [sameAs.cc: The Closure of 500M owl:sameAs Statements](../Beek_2018_SameAs.ccClosure500MOwl/notes.md) - cites this paper as prior work on ontology alignment for linked open data; Beek 2018 operates mainly at the instance identity-link layer, while BLOOMS targets schema/class alignment.
- [Not Quite the Same: Identity Constraints for the Web of Linked Data](../Melo_2013_NotQuiteSameIdentity/notes.md) - lists this paper as graph-based disambiguation/alignment work for Linked Data; Melo 2013 addresses identity-link repair, a complementary problem to BLOOMS' schema-link construction.

### New Leads (Not Yet in Collection)
- Euzenat (2004) - "An API for ontology alignment" - Alignment API used by BLOOMS for post-processing and output format.
- Euzenat and Shvaiko (2007) - "Ontology matching" - foundational ontology matching text cited for the field.
- Bizer, Heath, and Berners-Lee (2009) - "Linked data - the story so far" - Linked Data background for the LOD cloud problem framing.
- Bergman and Giasson - "UMBEL ontology, volume 1, technical documentation" - related schema-level reference framework for LOD.

### Supersedes or Recontextualizes
- (none identified; this paper is an early schema-alignment proposal rather than a direct correction of collected papers.)

### Conceptual Links (not citation-based)
- [When owl:sameAs Isn't the Same: An Analysis of Identity in Linked Data](../Halpin_2010_OwlSameAsIsntSame/notes.md) - Strong: same ISWC 2010 volume and same Web of Data context, but Halpin critiques overly strong instance identity while BLOOMS argues that LOD also needs schema-level subclass/equivalence links. Together they separate "what counts as the same individual" from "how class vocabularies align."
- [The sameAs Problem: A Survey on Identity Management in the Web of Data](../Raad_2019_SameAsProblemSurvey/notes.md) - Moderate: Raad 2019 surveys identity-link creation and repair, while BLOOMS creates schema-level links; both show that LOD integration needs typed, policy-aware links rather than undifferentiated similarity.
- [SameAs Networks and Beyond: Analyzing Deployment Status and Implications of owl:sameAs in Linked Data](../Ding_2010_SameAsNetworksBeyondAnalyzing/notes.md) - Strong: Ding 2010 uses sameAs networks and class-level similarity signals for ontology mapping/error detection, overlapping BLOOMS' goal of schema-level support but deriving evidence from identity-network structure rather than Wikipedia category forests.
- [Is my:sameAs the same as your:sameAs? Lenticular Lenses for Context-Specific Identity](../Idrissou_2017_LenticularLensesContextSpecificIdentity/notes.md) - Moderate: Lenticular Lenses makes identity links contextual and provenance-bearing; BLOOMS' directional schema alignments would benefit from the same context/provenance discipline rather than globally asserted class links.
- [Not Quite the Same: Identity Constraints for the Web of Linked Data](../Melo_2013_NotQuiteSameIdentity/notes.md) - Moderate: Melo 2013 provides graph constraints and repair for erroneous identity links, complementary to BLOOMS' construction of schema links; both imply that link quality must be evaluated, not just generated.

## Related Work Worth Reading
- Bizer, Heath, and Berners-Lee on Linked Data foundations. *(p.416)*
- Euzenat's Alignment API and Euzenat/Shvaiko's Ontology Matching text for ontology alignment foundations. *(p.416-p.417)*
- RiMOM, AROMA, CSR, S-Match, OMViaUO, and TaxoMap for comparator alignment strategies. *(p.407-p.408, p.417)*
- VoID and Silk for instance-level LOD link discovery context. *(p.415, p.417)*
- UMBEL as a unified reference framework for LOD schemas. *(p.415, p.417)*
