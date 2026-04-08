---
title: "The FAIR Guiding Principles for scientific data management and stewardship"
authors: "Mark D. Wilkinson, Michel Dumontier, IJsbrand Jan Aalbersberg, Gabrielle Appleton, Myles Axton, Arie Baak, Niklas Blomberg, Jan-Willem Boiten, Luiz Olavo Bonino da Silva Santos, Philip E. Bourne, Jildau Bouwman, Anthony J. Brookes, Tim Clark, Mercè Crosas, Ingrid Dillo, Olivier Dumon, Scott Edmunds, Chris T. Evelo, Richard Finkers, Alejandra González-Beltrán, Alasdair J.G. Gray, Paul Groth, Carole Goble, Jeffrey S. Grethe, Jaap Heringa, Peter A.C. 't Hoen, Rob Hooft, Tobias Kuhn, Ruben Kok, Joost Kok, Scott J. Lusher, Maryann E. Martone, Albert Mons, Abel L. Packer, Bengt Persson, Philippe Rocca-Serra, Marco Roos, Rene van Schaik, Susanna-Assunta Sansone, Erik Schultes, Thierry Sengstag, Ted Slater, George Strawn, Morris A. Swertz, Mark Thompson, Johan van der Lei, Erik van Mulligen, Jan Velterop, Andra Waagmeester, Peter Wittenburg, Katherine Wolstencroft, Jun Zhao, Barend Mons"
year: 2016
venue: "Scientific Data"
doi_url: "https://doi.org/10.1038/sdata.2016.18"
produced_by:
  agent: "claude-opus-4-6-1m"
  skill: "paper-reader"
  timestamp: "2026-04-03T07:51:07Z"
---
# The FAIR Guiding Principles for scientific data management and stewardship

## One-Sentence Summary
Defines four foundational principles (Findable, Accessible, Interoperable, Reusable) for scientific data management, emphasizing machine-actionability as a prerequisite for automated discovery and integration of scholarly data assets.

## Problem Addressed
The existing digital ecosystem surrounding scholarly data publication is fragmented: data often cannot be found, accessed, interoperated across systems, or reused by either humans or machines. Despite growing requirements from funders and governments for data management plans, there was no concise, measurable, technology-agnostic set of principles for evaluating and improving data stewardship. *(p.0)*

## Key Contributions
- Defines the FAIR acronym: Findable, Accessible, Interoperable, Reusable as four independent, composable principles for data stewardship *(p.0)*
- Provides 15 specific sub-principles (F1-F4, A1-A2, I1-I3, R1-R1.3) as measurable guidelines *(p.3)*
- Emphasizes machine-actionability as equally important as human usability -- the principles specifically target the ability of machines to automatically find and use data *(p.0, p.2)*
- Distinguishes data from metadata and requires both to be FAIR *(p.3)*
- Provides exemplar implementations across multiple real-world data repositories *(p.4-5)*
- Establishes that FAIR is a spectrum/continuum, not a binary state *(p.3)*
- Coins the "FAIRness" concept as a progressive measure of compliance *(p.2)*

## Study Design
*Non-empirical paper (community consensus/commentary).*

## Methodology
A diverse set of stakeholders -- academia, industry, funding agencies, scholarly publishers -- convened through a series of workshops ("Jointly Designing a Data FAIRport") to jointly design and endorse the principles. The principles were subsequently elaborated by a FAIR working group selected by the FORCE11 community. *(p.2)*

## Key Equations / Statistical Models
*No formal equations. The contribution is a principle framework, not a mathematical model.*

## Parameters
*Not applicable -- this is a principles/guidelines paper, not a quantitative methods paper.*

## Effect Sizes / Key Quantitative Results
*Not applicable.*

## Methods & Implementation Details

### The FAIR Guiding Principles (Box 2, p.3)

**To be Findable:**
- F1: (meta)data are assigned a globally unique and persistent identifier *(p.3)*
- F2: data are described with rich metadata (defined by R1 below) *(p.3)*
- F3: metadata clearly and explicitly include the identifier of the data it describes *(p.3)*
- F4: (meta)data are registered or indexed in a searchable resource *(p.3)*

**To be Accessible:**
- A1: (meta)data are retrievable by their identifier using a standardized communications protocol *(p.3)*
  - A1.1: the protocol is open, free, and universally implementable *(p.3)*
  - A1.2: the protocol allows for an authentication and authorization procedure, where necessary *(p.3)*
- A2: metadata are accessible, even when the data are no longer available *(p.3)*

**To be Interoperable:**
- I1: (meta)data use a formal, accessible, shared, and broadly applicable language for knowledge representation *(p.3)*
- I2: (meta)data use vocabularies that follow FAIR principles *(p.3)*
- I3: (meta)data include qualified references to other (meta)data *(p.3)*

**To be Reusable:**
- R1: meta(data) are richly described with a plurality of accurate and relevant attributes *(p.3)*
  - R1.1: (meta)data are released with a clear and accessible data usage license *(p.3)*
  - R1.2: (meta)data are associated with detailed provenance *(p.3)*
  - R1.3: (meta)data meet domain-relevant community standards *(p.3)*

### Key Definitions and Distinctions

**"Data" in FAIR context:** Includes not just conventional data tables but also the algorithms, tools, and workflows used to produce that data. All digital scholarly research objects benefit from application of these principles. *(p.0)*

**Machine-actionability definition:** A computational agent's capacity to find, access, interoperate, and reuse data with none or minimal human intervention. The emphasis is not just on format readability but on the ability to make a useful decision regarding data without human help. *(p.2)*

**Machine-actionable vs machine-readable:** Machine-actionability has two contexts: (1) referring to contextual metadata surrounding a digital object (what is it?), and (2) referring to the content of the digital object itself (how do I process its contents?). Either or both may be machine-actionable. *(p.2)*

**FAIR is about data AND metadata:** The principles apply simultaneously to data objects and their descriptions. Metadata can and should be FAIR even when the data itself cannot be (e.g., restricted access data). *(p.3)*

**FAIR is a spectrum:** Being FAIR is a continuum -- there is an optimal state, but resources move along this continuum towards it. The principles do not demand complete openness. *(p.3)*

**Distinction between FAIR and Open:** FAIR is not synonymous with open data. A1.2 explicitly allows authentication/authorization. Data can be maximally FAIR without being open (e.g., sensitive data with rich discoverable metadata but restricted access). *(p.3)*

### Significance of Machine-Actionability (p.2)

The paper argues that machines are increasingly responsible for data discovery and analysis-driven activities, making machine-actionability a core focus. Key observations:
- Humans are less likely to make errors in the selection of appropriate data or other objects, although humans will always make different errors than machines *(p.2)*
- Capacity to operate at appropriate scale, speed necessitated by contemporary scientific data is beyond human capacity *(p.2)*
- Machines must be capable of autonomously and appropriately acting when faced with the wide range of digital objects (formats, types, standards) *(p.2)*
- Machines need to keep an explicit record of provenance so that the data trail being collected can be accurately and adequately kept *(p.2)*

### Exemplar Implementations (p.4-5)

The paper profiles several existing systems that demonstrate FAIR compliance to varying degrees:

**Dataverse** (http://dataverse.org): Open-source data repository software installed in dozens of institutions worldwide. Over 60,000 datasets at time of publication. Exports metadata using Dublin Core, DDI, schema.org. Uses persistent identifiers (Handle/DOI). Metadata remains accessible when dataset is published even if restricted. *(p.4)*

**FAIRDOM** (http://fair-dom.org): Integrates SEEK and openBIS platforms. Provides FAIR data and model management. ISA metadata standard. Registered with DOIs via DataCite. *(p.4)*

**ISA** (http://isa-tools.org): Community-driven metadata tracking framework. Standards-compliant collection, curation, management and reuse of life-science datasets. Structured metadata in Nature Scientific Data's Data Descriptor articles. *(p.4-5)*

**Open PHACTS** (http://www.openphacts.org): Data integration platform for drug discovery. Provides machine-accessible interface with multiple representations (RDF/HTML). *(p.5)*

**UniProt** (http://www.uniprot.org): Comprehensive resource for protein sequence and annotation data. Uses RDF, Core Ontology. CC0 license. 5 cross-reference formats (RDF, XML, text, FASTA, GFF). *(p.5)*

**wwPDB** (http://www.wwpdb.org): Worldwide Protein Data Bank. Uses PDBx/mmCIF dictionary. Entries represented as CIF, PDB format, XML. Each entry has a DOI. *(p.5)*

### The Role of Existing Initiatives (p.5)

The paper notes complementary efforts:
- **FAIR Data Initiative and the GO-FAIR** -- emerged from the Lorentz Workshop
- The FAIR Principles are also complementary to the **Data Seal of Approval** (DSA), the **DANS** guidelines, and provide a structure of three levels (mandatory, recommended, optional) that helps repositories systematically evaluate their compliance *(p.5)*

### FAIRness as Prerequisite for Data Stewardship (p.5-6)

The paper argues that stakeholders who stand to benefit from FAIRness include:
- Researchers wanting to share/get credit and reuse each other's data *(p.5)*
- Professional data publishers maintaining quality-controlled archives *(p.5)*
- Funding agencies (public and private) increasingly requiring compliance *(p.5)*
- Data processing services such as reusable workflows *(p.5)*

## Figures of Interest
- **Box 1 (p.1):** Table of terms and definitions: Accessibility, Data, FAIRPort, Findability, Identifier, Interoperability, Machine-actionable, Metadata, Metric, Reusability, Stakeholders, Stewardship
- **Box 2 (p.3):** The FAIR Guiding Principles -- the complete 15-principle specification
- **Box 3 (p.5):** Emergent communities/collaborations with FAIRness as a core focus or activity

## Results Summary
The paper successfully establishes 15 sub-principles organized under four categories (FAIR) that have since become the dominant framework for evaluating scientific data management practices. The principles are deliberately technology-agnostic and domain-independent, applicable across all scientific disciplines. *(p.3)*

## Limitations
- The principles are high-level and do not specify concrete implementation requirements -- they are guidance, not specifications *(p.3)*
- No formal compliance metric or scoring system is provided (this is explicitly noted as future work) *(p.2)*
- The paper acknowledges that "a machine can be capable of determining the data-type of a digital object, but not be capable of determining the licensing requirements related to the retrieval and/or use of that data" -- i.e., partial FAIRness is the norm *(p.2)*
- The principles were defined at a time when many existing metadata standards did not include the attributes necessary to achieve rich accessibility -- this was an acknowledged gap *(p.1)*

## Arguments Against Prior Work
- Existing data management initiatives focused on the human scholar rather than machine-actionability, which the authors argue is insufficient for modern data scales *(p.0)*
- The paper notes that "the existing digital ecosystem surrounding scholarly data publication" is inadequate for discovery and reuse *(p.0)*
- Prior ontology/vocabulary efforts are acknowledged but criticized as insufficient without the surrounding infrastructure for findability, accessibility, and reuse *(p.1)*

## Design Rationale
- **Technology-agnostic by design:** The principles deliberately avoid specifying particular technologies, formats, or standards so they can be applied across all domains and survive technology evolution *(p.3)*
- **Metadata separate from data:** A2 (metadata accessible even when data is not) was a deliberate choice to support discovery of restricted/sensitive datasets *(p.3)*
- **Authentication allowed:** A1.2 explicitly permits authentication/authorization so that FAIR does not require openness -- sensitive data can still be maximally FAIR *(p.3)*
- **Applied to both data and metadata:** The principles apply recursively -- metadata vocabularies should themselves be FAIR (I2), and metadata schemas should follow community standards (R1.3) *(p.3)*
- **Independent principles:** The four categories (F, A, I, R) are related but independent and separable; a resource may be maximally compliant with one and not another *(p.3)*
- **Focus on "qualified references" (I3):** Cross-references between data objects must be typed/qualified (e.g., "is-a", "was-derived-from") rather than bare links *(p.3)*

## Testable Properties
- A dataset with a globally unique persistent identifier is more findable than one without (F1) *(p.3)*
- Metadata should remain accessible even after the data itself is no longer available (A2) *(p.3)*
- Machine-actionable metadata in a formal knowledge representation language enables automated interoperation (I1) *(p.3)*
- Provenance metadata (R1.2) enables trust assessment and reuse decisions *(p.3)*
- FAIR compliance is a continuous spectrum, not binary -- incremental improvements are meaningful *(p.3)*
- The same principles apply equally to data, metadata, algorithms, tools, and workflows *(p.0)*

## Relevance to Project
The FAIR principles are directly relevant to propstore's architecture in several ways:
1. **Provenance tracking (R1.2):** propstore already implements provenance for claims and stances; FAIR formalizes what "detailed provenance" means at a data management level.
2. **Persistent identifiers (F1):** propstore's content-hash-addressed sidecar and git-backed storage align with FAIR's emphasis on persistent, unique identifiers for data objects.
3. **Machine-actionability:** propstore's core design -- semantic storage with render-time resolution -- is inherently machine-actionable in the FAIR sense.
4. **Qualified references (I3):** propstore's stance and justification relations between claims are precisely the kind of typed cross-references FAIR demands.
5. **Metadata even when data is unavailable (A2):** propstore's separation of claims/metadata from underlying source data aligns with A2's requirement.
6. **Non-commitment discipline:** FAIR's emphasis on preserving data in its richest form (not collapsing) echoes propstore's core design principle of holding multiple rival normalizations.

## Open Questions
- [ ] Could propstore's claim/concept registry be formally evaluated against FAIR sub-principles?
- [ ] How do FAIR's interoperability principles (I1-I3) map to propstore's form/dimension typing system?
- [ ] Is the propstore sidecar's content-hash addressing scheme sufficient for F1 (globally unique and persistent identifiers)?

## Related Work Worth Reading
- Borgman, C.L. *Big Data, Little Data, No Data: Scholarship in the Networked World* (MIT Press, 2015) -- broader context on data stewardship *(p.6)*
- Bechhofer, S. et al. "Why linked data is not enough for scientists" (Future Generation Computer Systems, 2013) -- limitations of linked data approach *(p.6)*
- Clark, T. et al. "Micropublications" (W3C, 2014) -- already in collection, related to claim/provenance modeling
- Starr, J. et al. "Achieving human and machine accessibility of cited data in scholarly publications" (PeerJ CS, 2015) -- data citation practices *(p.6)*

## Collection Cross-References

### Already in Collection
- [[Clark_2014_Micropublications]] — cited in Related Work Worth Reading; defines micropublication semantic model for scientific claims with provenance, directly related to FAIR's R1.2 (provenance) and I3 (qualified references)

### New Leads (Not Yet in Collection)
- Starr et al. (2015) — "Achieving human and machine accessibility of cited data in scholarly publications" — data citation practices complementing F1/F3 principles
- Bechhofer et al. (2013) — "Why linked data is not enough for scientists" — critiques linked-data-only approaches, argues for provenance/versioning/bundling infrastructure
- Buneman et al. (2001) — "Why and where: characterization of data provenance" — foundational provenance theory underpinning R1.2

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found — this paper postdates most collection papers on argumentation theory)

### Conceptual Links (not citation-based)
- [[Clark_2014_Micropublications]] — Both address the infrastructure for scholarly communication with provenance. Clark defines a claim-level semantic model with attribution and argumentation relations; Wilkinson defines the data management principles (FAIR) that govern how such claims and their evidence should be stored, found, and reused. Clark provides the "what" of scholarly assertion structure; FAIR provides the "how" of making those assertions findable and interoperable.
- [[Groth_2010_AnatomyNanopublication]] — Both address making scientific assertions machine-actionable with provenance metadata. Nanopublications implement FAIR's I1 (formal knowledge representation), F1 (persistent identifiers via DOI/URI), and R1.2 (provenance) at the individual assertion level. FAIR provides the evaluation framework; nanopublications provide a concrete serialization strategy.
