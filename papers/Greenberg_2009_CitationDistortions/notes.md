---
title: "How citation distortions create unfounded authority: analysis of a citation network"
authors: "Steven A Greenberg"
year: 2009
venue: "BMJ (British Medical Journal)"
doi_url: "https://doi.org/10.1136/bmj.b2680"
---

# How citation distortions create unfounded authority: analysis of a citation network

## One-Sentence Summary
Empirically demonstrates how citation bias, amplification, and invention within a claim-specific citation network convert hypothesis into accepted fact, using the beta-amyloid/inclusion body myositis belief system as a case study with 242 papers and 675 citations. *(p.1)*

## Problem Addressed
Biomedical knowledge arises from data across many papers, but how an entire belief system shared by a scientific community evolves from that data is not well understood. *(p.1)* This paper shows that citation practices — not just data — can create unfounded authority for scientific claims through systematic distortions. *(p.1)*

## Key Contributions
- Defines and operationalizes a "claim-specific citation network" — all papers and citations pertaining to a single scientific claim *(p.1-2)*
- Identifies three distinct mechanisms of citation distortion: citation bias, amplification, and invention *(p.1)*
- Provides a detailed taxonomy of invention subtypes: citation diversion, citation transmutation, back door invention, dead end citation, title invention *(p.5-6)*
- Demonstrates that network authority (computed via social network theory) can diverge completely from data-supported truth *(p.5)*
- Shows the same distortion phenomena extend into NIH grant proposals *(p.6)*
- Proposes a computational methodology (Fig 7) for detecting these distortions *(p.7)*

## Methodology
Complete citation network construction from PubMed-indexed English literature on the claim that beta-amyloid is produced by and injures skeletal muscle in inclusion body myositis. *(p.1)* 242 papers, 675 citations, 220,553 citation paths. *(p.1)* Papers classified as: primary data (containing experimental data), myositis review, animal/cell culture model, or other. *(p.2)* Citations classified as supportive, neutral, critical, or diversion. *(p.2)* Network analysis using graph theory, centrality measures, and social network authority computation. *(p.2)*

The claim-specific citation network was constructed using graph theory tools in MATLAB with code from www.mathtools.net. *(p.2)* Authority was assessed according to the method of Kleinberg ("Authoritative sources in a hyperlinked environment") using a social network analysis method. *(p.2)* The network was visualized using Pajek (Batagelj/Mrvar). *(p.2)*

## Citation Distortion Taxonomy

### Citation Bias
Systematic ignoring of papers containing content conflicting with a claim. *(p.3)* Measured as differing citation frequency: supportive primary data papers received 94% of 214 citations; six papers with weakening/refuting data received only 6% (P=0.01). *(p.3)* Of the 10 most authoritative papers, all expressed the belief as true. *(p.3)* There were 16 primary data papers: of primary data, 4 of 6 strongest-data papers supported the claim and the other 4 contained data that either weakened or refuted it. *(p.3)*

### Amplification
Expansion of belief system by papers presenting no primary data addressing the claim. *(p.4)* Citations flow from primary data through reviews and models, increasing the number of supportive citations exponentially. *(p.4)* Sevenfold increase in supportive citations, 777-fold increase in citation paths between 1996-2007. *(p.5)* Critical citation paths numbered only 21 vs 220,609 supportive citation paths. *(p.5)* The 8 most authoritative papers (7 by same lab) carried 97% of all network traffic. *(p.5)*

A lens effect was present: a small number of highly influential review papers and model papers acted as a magnifying lens, collecting light from citation-biased papers and focusing it, while isolating others that weakened the claim. *(p.4)* Fig 3 shows that citations from animal/cell model papers to primary data flowed 97% to supportive papers. *(p.4)*

### Invention
Distinct from bias and amplification — types of fact created through the citation process itself: *(p.5)*

| Subtype | Definition | Page |
|---------|-----------|------|
| Citation diversion | Citing content but claiming it has a different meaning, diverting its implications | p.5 |
| Citation transmutation | Conversion of hypothesis into fact through citation alone | p.5 |
| Back door invention | Repeated misrepresentation of abstracts as peer-reviewed published methods and data | p.5 |
| Dead end citation | Support of a claim with citation to papers containing no content addressing it | p.5 |
| Title invention | Reporting "experimental results" in a paper's title even though it reports no such experiments | p.5 |

**Citation transmutation** was found in 9 papers (24% of citing papers that could be evaluated). *(p.5)* The transmutation pattern: one paper states the claim as hypothesis, the next cites it as "reportedly" or "has been suggested," and subsequent papers cite it as established fact. *(p.5)* Fig 5 shows the citation transmutation network mapping the progression from hypothesis to fact. *(p.6)*

**Back door invention** involved a specific abstract published in 1992 that was repeatedly cited as peer-reviewed published data — this abstract was cited by 8 papers, receiving more citations than over half of the actual primary data papers. *(p.5)*

## Key Quantitative Findings

| Name | Symbol | Units | Default | Range | Notes | Page |
|------|--------|-------|---------|-------|-------|------|
| Total papers in network | - | count | 242 | - | All PubMed English papers on the claim | p.1 |
| Total citations | - | count | 675 | - | Not counting duplicates | p.1 |
| Citation paths | - | count | 220,553 | - | Chains of citations | p.1 |
| Supportive citation paths | - | count | 220,609 | - | Flowing through supportive papers | p.5 |
| Critical citation paths | - | count | 21 | - | Flowing through critical papers | p.5 |
| Citation bias P-value | - | - | 0.01 | - | Difference in citation frequency to supportive vs critical data | p.3 |
| Supportive citations share | - | % | 94 | - | Of citations to primary data papers | p.3 |
| Critical citations share | - | % | 6 | - | Of citations to primary data papers | p.3 |
| Network traffic through authority group | - | % | 97 | - | 8 key papers (7 by same lab) carry 97% of all network traffic | p.5 |
| Citation paths growth (supportive) | - | fold | 777 | - | Between 1996-2007 | p.5 |
| Papers with citation transmutation | - | count | 9 | - | Of 24% of citing papers | p.5 |
| Grant proposals with distortions | - | count | 8 of 9 | - | NIH proposals containing citation bias or invention | p.6 |
| Primary data papers | - | count | 16 | - | Papers containing experimental data addressing the claim | p.3 |
| Papers with no primary data | - | count | ~200 | - | Reviews, models, other papers amplifying the claim | p.1 |

## Implementation Details — The Claim-Specific Citation Network Method (Fig 7)

*(p.7)*

1. **Collect papers** — all PubMed papers containing statements about the claim *(p.2)*
2. **Extract text/citations** — identify all statements and their supporting citations *(p.2)*
3. **Construct network** — papers as nodes, citations as directed edges *(p.2)*
4. **Computational analysis:** *(p.7)*
   - Identify **amplification** (papers without primary data that amplify the claim)
   - Identify **authorities** (high-centrality nodes via network theory)
5. **Manual analysis (requires reading):** *(p.7)*
   - Identify **primary data** papers (which contain actual experimental evidence)
   - Identify **invention** (citation transmutation, diversion, back door invention)
6. **Compare** authorities against primary data to measure citation bias *(p.7)*
7. **Remove citation bias** computationally to produce **balanced authority** — simulated network showing what authority status would be without bias *(p.5, p.7)*
8. **Assess effects on network** — does removing bias change authority status? *(p.5)*

## Extension to NIH Grant Proposals

Analysis of 9 NIH grant proposals (identified via Freedom of Information Act) showed that 8 of 9 contained citation bias or invention, mirroring the same distortions found in the published literature. *(p.6)* Fig 6 shows the citation network extended to include grant proposals, with complex citation chains and citation invention present in funding applications. *(p.6)*

## Information Cascades and Broader Context

The author connects citation distortions to information cascade theory (Bikhchandani et al. 1992) — entities rationally deciding to copy behavior of predecessors rather than acting on their own private information. *(p.7)* Citation bias is identified as a form of information cascade, where authors cite what others have cited rather than independently evaluating primary data. *(p.7)* These cascades are fragile and fall apart quickly when exposed, but may not occur in biomedical belief systems where contradicted claims persist. *(p.7)*

The paper also notes that self-citation has social uses beyond scientific merit, both self-serving and as a tool for persuasion. *(p.8)*

## Figures of Interest
- **Fig 1 (p.2):** Full claim-specific citation network, color-coded by paper type and citation type, showing dominance of supportive citation paths
- **Fig 2 (p.3):** Citation bias quantified — bar chart showing supportive vs critical papers' citation counts
- **Fig 3 (p.4):** Citations from animal/cell model papers to primary data — 97% flow to supportive papers
- **Fig 4 (p.5):** Historical growth of supportive vs critical citations; lens effect of authority papers; computational removal of citation bias producing balanced authority
- **Fig 5 (p.6):** Citation transmutation network — conversion of hypothesis to fact through citation chains
- **Fig 6 (p.6):** Extension into NIH grant proposals showing same distortions
- **Fig 7 (p.7):** Overview methodology diagram — combined manual and computational approach

## Arguments Against Prior Work

1. **Paper-level citation analysis misses claim-level distortions.** Traditional bibliometric analysis counts citations at the paper level but cannot detect whether citations accurately represent the cited paper's content. A paper can be cited "in support of" a claim it actually contradicts or does not address. Only claim-specific citation network analysis can reveal these distortions. *(p.1-2, p.7)*
2. **Citation counts conflate authority with popularity.** Standard citation metrics (impact factor, h-index) measure how often a paper is cited, not whether its citations are accurate or whether it contains relevant primary data. The 10 most authoritative papers in the beta-amyloid/IBM network all supported the claim, yet the underlying data was mixed. *(p.3, p.5)*
3. **Information cascade theory predicts fragility that does not materialize in biomedicine.** Bikhchandani et al. (1992) predicted that information cascades are fragile and fall apart quickly when exposed. However, biomedical belief systems built on citation distortions appear to persist even after contradictory data is published, suggesting that biomedical citation cascades have additional reinforcing mechanisms (grant funding, lab investments, career commitments). *(p.7)*
4. **Self-citation analysis alone is insufficient.** While self-citation is recognized as a potential bias, the distortions documented in this paper go far beyond self-citation. Citation diversion, transmutation, back door invention, and dead end citation are qualitatively different from self-citation and cannot be detected by self-citation metrics alone. *(p.7-8)*
5. **Peer review does not prevent citation distortions.** The documented distortions (citation transmutation converting hypothesis to fact, back door invention citing abstracts as peer-reviewed data) occurred in peer-reviewed journals, demonstrating that the peer review process is insufficient to catch these types of accuracy failures. *(p.5-6)*
6. **Grant proposal review perpetuates the same distortions.** Analysis of 9 NIH grant proposals showed that 8 of 9 contained citation bias or invention, meaning the distortions propagate from the literature into funding decisions, creating a self-reinforcing cycle of unfounded authority. *(p.6)*

## Design Rationale

1. **Claim-specific citation network as unit of analysis.** Rather than analyzing citations at the paper level, the paper constructs a network of all papers and citations pertaining to a single scientific claim. This allows tracking how a specific belief propagates through the literature. *(p.1-2)*
2. **Three-mechanism taxonomy (bias, amplification, invention).** The paper identifies three qualitatively distinct mechanisms of distortion, each with different detection methods and implications: bias is selective citation, amplification is propagation through non-data papers, and invention is creation of new "facts" through the citation process itself. *(p.1, p.3-6)*
3. **Five invention subtypes for fine-grained detection.** Invention is further divided into citation diversion, citation transmutation, back door invention, dead end citation, and title invention. Each subtype represents a different mechanism by which the citation process creates content that does not exist in the cited source. *(p.5-6)*
4. **Combined manual and computational methodology.** The paper uses computational methods for network construction, authority computation, and amplification detection, but requires manual reading for invention detection and primary data classification. This honest acknowledgment of what can and cannot be automated is itself a methodological contribution. *(p.7)*
5. **Social network authority via Kleinberg's method.** Authority is computed using the HITS algorithm (Kleinberg's "Authoritative sources in a hyperlinked environment"), treating the citation network as a social network where authority flows through hub-authority relationships. This provides a principled mathematical measure of citation-derived authority. *(p.2)*
6. **Balanced authority simulation.** The paper computationally removes citation bias to produce a "balanced authority" network showing what authority status would look like without systematic bias. This demonstrates that the observed authority is an artifact of citation patterns, not of underlying data strength. *(p.5, p.7)*
7. **Extension to grant proposals via FOIA.** By obtaining NIH grant proposals through the Freedom of Information Act and analyzing their citation patterns, the paper demonstrates that the same distortions propagate beyond the published literature into funding decisions, revealing the full scope of the problem. *(p.6)*
8. **Connection to information cascade theory.** By framing citation distortions as information cascades, the paper connects empirical bibliometric findings to established economic theory, providing a theoretical framework for understanding why citation distortions arise and persist. *(p.7)*

## Results Summary
In the beta-amyloid/IBM belief system, unfounded authority was created through: (1) citation bias against 6 critical primary data papers *(p.3)*, (2) amplification through ~200 papers presenting no primary data *(p.4)*, and (3) multiple forms of invention converting hypothesis to accepted fact *(p.5-6)*. The 10 most authoritative papers (by network analysis) all expressed the belief as true, yet only 4 of the 6 strongest primary data papers actually supported it, while the other 4 refuted/weakened it. *(p.3)* Removing citation bias computationally produced balanced authority of both support and refutation. *(p.5)*

## Limitations
- Single case study (beta-amyloid in IBM) — generalizability uncertain *(p.7)*
- Manual classification of citation types requires domain expertise and reading of paper content *(p.7)*
- The computational authority identification is straightforward but the invention detection requires manual content analysis *(p.7)*
- Does not propose automated solutions for detecting all distortion types *(p.7)*
- Relies on PubMed-indexed English literature only *(p.1)*

## Testable Properties
- In a biased citation network, removing citation bias computationally should balance authority between supporting and refuting evidence *(p.5)*
- Authority papers (high centrality) should not exclusively support the claim if the underlying data is mixed *(p.5)*
- Citation transmutation can be detected by tracking the modal verb progression (hypothesis -> likelihood -> fact) across citation chains *(p.5)*
- Amplification can be quantified as the ratio of non-data papers to data papers in citation paths *(p.4)*
- Information cascade theory predicts citation distortions are fragile and should collapse when exposed *(p.7)*
- Citation bias should appear in grant proposals at similar or higher rates than in published literature *(p.6)*

## Relevance to Project
This paper is foundational for the propstore's claim provenance tracking. It provides:
1. **Empirical evidence** that citation patterns can create false authority — exactly the problem a claim-level knowledge store aims to detect *(p.1)*
2. **A taxonomy of distortion types** that maps directly to stance validation: citation bias = missing contradicted_by stances, amplification = unsupported claims propagating, invention = fabricated supported_by stances *(p.5-6)*
3. **The claim-specific citation network concept** — the propstore IS a claim-specific citation network, just formalized differently *(p.2)*
4. **The methodology (Fig 7)** for computationally detecting bias could be implemented as a propstore analysis tool *(p.7)*

## Open Questions
- [ ] Can the citation distortion taxonomy be encoded as propstore stance validation rules?
- [ ] What is the computational cost of constructing claim-specific citation networks at scale?
- [ ] How does the balanced-authority simulation relate to the propstore's reconciliation of conflicting claims?

## Collection Cross-References

### Already in Collection
- (none — no cited papers are in the collection)

### Cited By (in Collection)
- [[Clark_2014_Micropublications]] — cites Greenberg's claim network (Fig 20) as motivation for micropublications; the citation distortion problem is the core reason why claim-level provenance tracking is needed

### Conceptual Links (not citation-based)
- [[Clark_2014_Micropublications]] — **Strong.** Greenberg provides the empirical problem (citation distortions create unfounded authority); Clark provides the structural solution (micropublications with explicit supports/challenges stances). The distortion taxonomy maps directly to stance validation rules in a claim store.

## Related Work Worth Reading
- Tatsioni A, Bonitsis NG, Ioannidis JPA: Persistence of contradicted claims in the literature (JAMA 2007) — complementary study on claim persistence *(ref 318, p.14)*
- Bikhchandani S, Hirshleifer D, Welch I: A theory of fads, fashion, custom, and cultural change as informational cascades (J Political Econ 1992) — information cascade theory underlying amplification *(ref 316, p.14)*
- Garfield E: Citation indexes for science (Science 1955) — foundational citation analysis *(ref 313, p.14)*
- Hengstman GJD, van Engelen BGM: Polymyositis, invasion of non-necrotic muscle fibres, and the art of repetition (BMJ 2004) — early commentary on repetition creating false authority in this domain *(ref 315, p.14)*
