---
title: "How citation distortions create unfounded authority: analysis of a citation network"
authors: "Steven A Greenberg"
year: 2009
venue: "BMJ (British Medical Journal)"
doi_url: "https://doi.org/10.1136/bmj.b2680"
---

# How citation distortions create unfounded authority: analysis of a citation network

## One-Sentence Summary
Empirically demonstrates how citation bias, amplification, and invention within a claim-specific citation network convert hypothesis into accepted fact, using the beta-amyloid/inclusion body myositis belief system as a case study with 242 papers and 675 citations.

## Problem Addressed
Biomedical knowledge arises from data across many papers, but how an entire belief system shared by a scientific community evolves from that data is not well understood. This paper shows that citation practices — not just data — can create unfounded authority for scientific claims through systematic distortions.

## Key Contributions
- Defines and operationalizes a "claim-specific citation network" — all papers and citations pertaining to a single scientific claim
- Identifies three distinct mechanisms of citation distortion: citation bias, amplification, and invention
- Provides a detailed taxonomy of invention subtypes: citation diversion, citation transmutation, back door invention, dead end citation, title invention
- Demonstrates that network authority (computed via social network theory) can diverge completely from data-supported truth
- Shows the same distortion phenomena extend into NIH grant proposals
- Proposes a computational methodology (Fig 7) for detecting these distortions

## Methodology
Complete citation network construction from PubMed-indexed English literature on the claim that β-amyloid is produced by and injures skeletal muscle in inclusion body myositis. 242 papers, 675 citations, 220,553 citation paths. Papers classified as: primary data (containing experimental data), myositis review, animal/cell culture model, or other. Citations classified as supportive, neutral, critical, or diversion. Network analysis using graph theory, centrality measures, and social network authority computation.

## Citation Distortion Taxonomy

### Citation Bias
Systematic ignoring of papers containing content conflicting with a claim. Measured as differing citation frequency: supportive primary data papers received 94% of 214 citations; six papers with weakening/refuting data received only 6% (P=0.01).

### Amplification
Expansion of belief system by papers presenting no primary data addressing the claim. Citations flow from primary data through reviews and models, increasing the number of supportive citations exponentially (sevenfold increase in supportive citations, 777-fold increase in citation paths between 1996-2007).

### Invention
Distinct from bias and amplification — types of fact created through the citation process itself:

| Subtype | Definition |
|---------|-----------|
| Citation diversion | Citing content but claiming it has a different meaning, diverting its implications |
| Citation transmutation | Conversion of hypothesis into fact through citation alone |
| Back door invention | Repeated misrepresentation of abstracts as peer-reviewed published methods and data |
| Dead end citation | Support of a claim with citation to papers containing no content addressing it |
| Title invention | Reporting "experimental results" in a paper's title even though it reports no such experiments |

## Key Quantitative Findings

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Total papers in network | - | count | 242 | - | All PubMed English papers on the claim |
| Total citations | - | count | 675 | - | Not counting duplicates |
| Citation paths | - | count | 220,553 | - | Chains of citations |
| Supportive citation paths | - | count | 220,609 | - | Flowing through supportive papers |
| Critical citation paths | - | count | 21 | - | Flowing through critical papers |
| Citation bias P-value | - | - | 0.01 | - | Difference in citation frequency to supportive vs critical data |
| Supportive citations share | - | % | 94 | - | Of citations to primary data papers |
| Critical citations share | - | % | 6 | - | Of citations to primary data papers |
| Network traffic through authority group | - | % | 97 | - | 8 key papers (7 by same lab) carry 97% of all network traffic |
| Citation paths growth (supportive) | - | fold | 777 | - | Between 1996-2007 |
| Papers with citation transmutation | - | count | 9 | - | Of 24% of citing papers |
| Grant proposals with distortions | - | count | 8 of 9 | - | NIH proposals containing citation bias or invention |

## Implementation Details — The Claim-Specific Citation Network Method (Fig 7)

1. **Collect papers** — all PubMed papers containing statements about the claim
2. **Extract text/citations** — identify all statements and their supporting citations
3. **Construct network** — papers as nodes, citations as directed edges
4. **Computational analysis:**
   - Identify **amplification** (papers without primary data that amplify the claim)
   - Identify **authorities** (high-centrality nodes via network theory)
5. **Manual analysis (requires reading):**
   - Identify **primary data** papers (which contain actual experimental evidence)
   - Identify **invention** (citation transmutation, diversion, back door invention)
6. **Compare** authorities against primary data to measure citation bias
7. **Remove citation bias** computationally to produce **balanced authority** — simulated network showing what authority status would be without bias
8. **Assess effects on network** — does removing bias change authority status?

## Figures of Interest
- **Fig 1 (page 2):** Full claim-specific citation network, color-coded by paper type and citation type, showing dominance of supportive citation paths
- **Fig 2 (page 3):** Citation bias quantified — bar chart showing supportive vs critical papers' citation counts
- **Fig 3 (page 4):** Citations from animal/cell model papers to primary data — 97% flow to supportive papers
- **Fig 4 (page 5):** Historical growth of supportive vs critical citations; lens effect of authority papers; computational removal of citation bias producing balanced authority
- **Fig 5 (page 6):** Citation transmutation network — conversion of hypothesis to fact through citation chains
- **Fig 6 (page 6):** Extension into NIH grant proposals showing same distortions
- **Fig 7 (page 7):** Overview methodology diagram — combined manual and computational approach

## Results Summary
In the β-amyloid/IBM belief system, unfounded authority was created through: (1) citation bias against 6 critical primary data papers, (2) amplification through ~200 papers presenting no primary data, and (3) multiple forms of invention converting hypothesis to accepted fact. The 10 most authoritative papers (by network analysis) all expressed the belief as true, yet only 4 of the 6 primary data papers providing evidence actually supported it, while the other 4 primary data papers refuted/weakened it. Removing citation bias computationally produced balanced authority of both support and refutation.

## Limitations
- Single case study (β-amyloid in IBM) — generalizability uncertain
- Manual classification of citation types requires domain expertise and reading of paper content
- The computational authority identification is straightforward but the invention detection requires manual content analysis
- Does not propose automated solutions for detecting all distortion types
- Relies on PubMed-indexed English literature only

## Testable Properties
- In a biased citation network, removing citation bias computationally should balance authority between supporting and refuting evidence
- Authority papers (high centrality) should not exclusively support the claim if the underlying data is mixed
- Citation transmutation can be detected by tracking the modal verb progression (hypothesis → likelihood → fact) across citation chains
- Amplification can be quantified as the ratio of non-data papers to data papers in citation paths

## Relevance to Project
This paper is foundational for the propstore's claim provenance tracking. It provides:
1. **Empirical evidence** that citation patterns can create false authority — exactly the problem a claim-level knowledge store aims to detect
2. **A taxonomy of distortion types** that maps directly to stance validation: citation bias = missing contradicted_by stances, amplification = unsupported claims propagating, invention = fabricated supported_by stances
3. **The claim-specific citation network concept** — the propstore IS a claim-specific citation network, just formalized differently
4. **The methodology (Fig 7)** for computationally detecting bias could be implemented as a propstore analysis tool

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
- Tatsioni A, Bonitsis NG, Ioannidis JPA: Persistence of contradicted claims in the literature (JAMA 2007) — complementary study on claim persistence
- Bikhchandani S, Hirshleifer D, Welch I: A theory of fads, fashion, custom, and cultural change as informational cascades (J Political Econ 1992) — information cascade theory underlying amplification
- Garfield E: Citation indexes for science (Science 1955) — foundational citation analysis
