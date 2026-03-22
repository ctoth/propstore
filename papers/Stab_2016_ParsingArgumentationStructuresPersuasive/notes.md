---
title: "Parsing Argumentation Structures in Persuasive Essays"
authors: "Christian Stab, Iryna Gurevych"
year: 2017
venue: "Computational Linguistics, Volume 7, Number 7"
doi_url: "https://doi.org/10.1162/COLI_a_00295"
---

# Parsing Argumentation Structures in Persuasive Essays

## One-Sentence Summary
Presents an end-to-end pipeline for automatically parsing argumentation structures in persuasive essays, combining token-level sequence labeling for argument component identification with an ILP joint model that globally optimizes component types and argumentative relations.

## Problem Addressed
Prior approaches to argumentation structure parsing either focus on individual subtasks (component identification, classification, or relation identification) in isolation or rely on pipeline approaches that cannot enforce global structural constraints. There is also a lack of large annotated corpora for argumentation structures at the discourse level (across paragraphs).

## Key Contributions
- A novel annotation scheme for argumentation structures in persuasive essays, with annotation guidelines that achieve substantial inter-annotator agreement
- A new corpus of 402 persuasive essays annotated with discourse-level argumentation structures (major claims, claims, premises, support/attack relations)
- An argument component identification model using token-level sequence labeling (BIO tagging with CRF)
- An argument component classification model (SVM) for distinguishing major claims, claims, and premises
- An argumentative relation identification model (SVM) for detecting support/attack links between components
- An ILP joint model that globally optimizes component types and relations simultaneously, enforcing tree structure constraints
- Demonstration that the joint model significantly outperforms pipeline approaches and heuristic baselines

## Argumentation Model

The paper models argumentation structure of persuasive essays as a connected tree structure with two levels:
1. **Paragraph level**: Each paragraph has its own tree structure with argument components connected by argumentative relations
2. **Essay level**: The major claim in the introduction/conclusion connects to claims in body paragraphs

### Component Types
- **Major Claim (MC)**: The author's standpoint on the essay topic, stated in introduction/conclusion. Has a stance attribute: "for" or "against"
- **Claim (C)**: Central component of each argument in body paragraphs. Either supports or attacks the major claim
- **Premise (P)**: Supports claims. Each premise has exactly one outgoing relation (to a claim or another premise)

### Relation Types
- **Support**: A premise or claim provides evidence for another component
- **Attack**: A premise or claim contradicts or challenges another component

### Structural Constraints (enforced by ILP)
- Argumentation structure is a tree (each premise has exactly one outgoing relation)
- Each paragraph includes all its argument components in a single tree
- Claims can be convergent (independently supported by multiple premises) or linked (requiring multiple premises jointly)
- Essay writing typically follows a "claim-oriented" procedure: authors state standpoint, then justify with claims, then support claims with premises

## Methodology

### Pipeline Architecture (Figure 5, page 16)
1. **Argument Component Identification** (sequence labeling) - identifies boundaries of argument components from non-argumentative text
2. **Argument Component Classification** - classifies components as major claim, claim, or premise
3. **Argumentative Relation Identification** - determines which pairs of components are linked and whether the relation is support or attack
4. **Joint Model (ILP)** - globally optimizes the outputs of all three classifiers

### Preprocessing
- Tokenization and sentence boundaries using the Language/Tool segmenter
- Paragraphs identified by checking for line breaks
- POS tagging using Stanford tagger (Toutanova et al. 2003)
- Constituency and dependency parsing (Klein and Manning 2003)
- Discourse markers from PDTB (Prasad et al. 2008)

## Argument Component Identification (Section 5.1)

### Approach
- Sequence labeling at the token level using BIO scheme
- "Arg-B" = beginning of argument component
- "Arg-I" = inside argument component
- "O" = non-argumentative (outside)
- Uses CRF (Conditional Random Field) classifier

### Features (Table 7, page 17)

| Group | Feature | Description |
|-------|---------|-------------|
| Lexical | Token | Token in lowercase |
| | Dependency bigrams | Binary and hexational unigrams of the component and its covering sentence |
| | Token statistics | Various counts of number of tokens in covering sentence, distance to end |
| Structural | Position of covering sentence | Absolute and relative position of the token's covering sentence in the paragraph and essay |
| | Token position | Token precedes or follows any punctuation, full stop, question mark, or exclamation mark |
| | Component position | Compound text position features |
| Syntactic | Constituency parse tree | Position of token relative to root of parse tree |
| | Lexical | Constituency grammar production rules |
| | LCA types | The constituency parse tree LCA of the current token and the first/last token of covering sentence |
| Probability | Prob | Conditional probability of "Arg-B" given preceding tokens |

### Probability Feature
The probability feature is the conditional probability of the current token being the beginning of an argument component ("Arg-B") given its preceding tokens:

$$
argmax_{l} P(t_i = \text{"Arg-B"} | t_{i-n}, ..., t_{i-1})
$$

Where the maximum probability for preceding tokens at length up to n = 3. Estimated by dividing the number of times the preceding tokens precede a token labeled "Arg-B" by the total number of occurrences of the preceding tokens in the training data.

### Results
- CRF model with all features: macro F1 of .867 for identifying argument components
- F1 of .866 for identifying beginning of argument components ("Arg-B")
- Structural features best for separating argumentative from non-argumentative text
- Model identifies 1,277 argument components vs 1,266 in gold standard

## Argument Component Classification (Section 5.3)

### Approach
- SVM classifier to classify each identified argument component as major claim, claim, or premise
- Uses features from source and target components

### Features (Table 9, page 20-21)

| Group | Feature | Description |
|-------|---------|-------------|
| Lexical | Unigrams | Binary and hexational unigrams of the component and its covering sentence |
| | Dependency bigrams | Dependency relation + child token bigrams |
| | Token statistics | Number of tokens, number of positive/negative words, adverbs in component |
| Structural | Token statistics | Number of tokens in component and covering sentence |
| | Component statistics | Number of components in the covering paragraph |
| | Position features | Source and target positioned in same sentence, or in same/different paragraph |
| | Component position | Paragraph and document position of the component |
| Indicators | First-person indicators | First-person pronouns present in component |
| | Indicators content | Indicator type tokens or possible source or target in the component |
| Discourse | PDTB-style features | Presence of discourse connectives from PDTB: "because", "since", "furthermore" |
| Probability | Type probability | Conditional probability of the component being a major claim/claim/premise given context |
| Embedding | Combined word embeddings | Sum of the word vectors of each word of the component |

### Results
- Best macro F1 for component classification: .726
- Claims and major claims: best identified by structural features (position in document)
- Premises: best identified by indicator features
- Embedding features improve performance when combined with other features

## Argumentative Relation Identification (Section 5.3.2)

### Approach
- SVM classifier to determine if pairs of argument components are argumentatively related
- Binary classification: linked vs. not-linked
- For each pair, extracts features from both source and target components

### Features (Table 10, page 22)

| Group | Feature | Description |
|-------|---------|-------------|
| Lexical | Unigrams | Binary lemmatized unigrams of the source and target component |
| | Subcategory chain | Sequence of POS subcategory tags of source and target |
| Syntactic | Part-of-speech | Binary POS features of source and target components |
| | Production rules | Most frequent production rules from parse tree |
| Structural | Token statistics | Number of tokens in source and target |
| | Component statistics | Same/different paragraph, distance between source and target |
| | Position features | Source and target positioned in same/different paragraphs, same sentence |
| Indicators | Indicators context | Indicator type tokens or possible source or target in the component |
| Discourse | PDTB features | Potential mutual information from covering sentence or adjacent sentences |
| | PMI relations | PMI indicators based on assumption that particular words indicate incoming or outgoing relations |
| Embedding | Combined word embeddings | Sum of word vectors of source and target components |
| | Shared nouns | Shared entity features across source and target components |

### Results
- Best macro F1 for relation identification: .751
- Structural and discourse features most effective for identifying relations
- Shared nouns also contribute meaningfully

## ILP Joint Model (Section 5.3.3)

### Formulation
The ILP joint model globally optimizes argument component types and argumentative relations. Given a paragraph including n argument components, the objective function is:

$$
argmax \sum_{i,j} x_{ij} c_{ij}
$$

Where:
- $x_{ij} \in \{0, 1\}$ indicates an argumentative relation from argument component $i$ to argument component $j$
- $c_{ij}$ is a weight (coefficient) of the relation, determined by incorporating the outcomes of the two base classifiers

### Constraints

**Tree structure constraint** - each component has at most one outgoing relation:

$$
\forall i: \sum_{j \neq i} x_{ij} \leq 1
$$

**Paragraph constraint** - a paragraph includes all of its nodes (no root node outside the paragraph):

$$
\forall i: x_{i0} = 0
$$

**No self-loops**:

$$
\forall i: x_{ii} = 0
$$

**Auxiliary variables for path detection** - prevents cycles by ensuring all paths have bounded length:

$$
\forall i,j: r_{ij} + r_{ji} = h_{ij} + h_{ji} \leq 1
$$

Where $r_{ij}$ represents reachability and $h_{ij}$ represents direct edges.

**Transitivity** - if there is a path from $i$ to $j$ and from $j$ to $k$, there is a path from $i$ to $k$:

$$
\forall i,j,k: h_{ij} + h_{jk} - h_{ik} \leq 1
$$

**Cycle prevention** - prevents cycles by bounding covered path lengths:

$$
\forall i: h_{ii} = 0
$$

### Claim Score
For each argument component $i$, the paper defines a claim score from the predicted relations:

$$
cs_i = \frac{r_{in}(c_i) \cdot r_{out}(c_i)}{r_{total}(c_i)}
$$

Where:
- $r_{in}(c_i)$ is the number of predicted incoming relations
- $r_{out}(c_i)$ is the number of predicted outgoing relations
- $r_{total}(c_i)$ is the total number of predicted relations

The claim score is positive for argument components with many incoming relations and few outgoing relations (characteristic of claims), and negative for components with many outgoing and few incoming (characteristic of premises).

### Weight Computation
The ILP objective function weights incorporate:
1. **Relation weights** ($c_{ij}$): higher weight assigned to relations pointing to components likely to be claims
2. **Claim score weights**: components with higher claim scores get higher weight as targets
3. **Component type weights**: the classification model's probabilities influence whether a component is labeled as claim or premise

### Stance Recognition
After joint optimization, a separate SVM classifies support vs. attack relations and stance of each claim relative to the major claim.

### Results (Table 12, page 27)
- ILP joint model significantly outperforms heuristic baselines for all tasks
- Average macro F1 across all tasks: .476 (ILP joint) vs. heuristic baselines
- Component classification: F1 .825 human upper bound, .726 model
- Relation identification: macro F1 .751
- Stance recognition: macro F1 .685

## Corpus Statistics (Table 6, page 15)

| Property | Value |
|----------|-------|
| Total argument components | 5,089 |
| Major claims | 751 |
| Claims | 1,506 |
| Premises | 3,832 |
| Non-argumentative text amount | 47,474 tokens (22.2%) |
| Sentences with several components | 361 (include components with different types) |
| Arguments with attack relations | 147 (only 10.7% have attack relations) |
| Arguments that are convergent | 2,261 (20.4%) |

## Inter-Annotator Agreement

### Component Identification
- Unitized alpha score (Krippendorff): α_U = .765
- Token-level kappa agreement improved by .163 compared to previous study (Stab and Gurevych 2014a)

### Component Classification
- 3-class agreement (major claim, claim, premise): κ = .724
- Binary class agreement (claim vs. premise): κ = .721

### Argumentative Relations
- Support and attack relations: κ-scores above .7
- Identification of attack relations: lower agreement (.53 for attack vs .70 for support)
- Only 10.7% of arguments include attack relations

## Key Indicators (Appendix C, pages 34)

### Forward Indicators (22 total)
- "As a consequence", "Because", "Clearly", "Consequently", "Considering"
- "For example", "For instance", "Furthermore", "Hence", "However"
- "In addition", "In conclusion", "In fact", "Moreover", "Nevertheless"
- "Obviously", "Since", "Such as", "That is why", "Therefore", "Thus"

### Backward Indicators (35 total)
- "Additionally", "As a matter of fact", "Because", "Besides", "But", "Clearly"
- "Consequently", "For example", "For instance", "Furthermore"
- "However", "In addition", "In fact", "Indeed", "Moreover", "Nevertheless"
- "Obviously", "Since", "Therefore", "Thus"

### Thesis Indicators (8 total)
- "All in all", "All things considered", "As far as I am concerned", "Based on"
- "For the reasons mentioned above", "From explanation above"
- "I advocate that", "I highly recommend", "I strongly believe that", "I think that"
- "In conclusion", "In my opinion", "In my personal point of view"
- "In summary", "Overall", "Personally", "To sum up"

### Rebuttal Indicators (10 total)
- "Admittedly", "Although", "Despite", "Even though", "However"
- "Nevertheless", "Nonetheless", "On the other hand", "Yet"

## Figures of Interest
- **Fig 1 (page 7):** Argument diagram notation - nodes are argument components, solid links are directed argumentative relations, dashed lines are stance attributes
- **Fig 2 (page 9):** Example argumentation structure of a full essay showing tree structure with major claim, claims, premises, and support/attack relations
- **Fig 3 (page 11):** Argumentation structure of the example essay - arrows are argumentative relations, arrows denote support/attack, dashed lines are stance relations
- **Fig 4 (page 16):** Architecture of the argumentation structure parser - four consecutive subtasks
- **Fig 5 (page 16):** Architecture of the argumentation structure parser pipeline
- **Fig 6a-c (page 29):** Influence of improving base classifiers on ILP joint model performance

## Results Summary
- The ILP joint model significantly outperforms heuristic baselines and pipeline approaches
- Argument component identification: macro F1 .867
- Argument component classification: macro F1 .726 (human upper bound .825)
- Argumentative relation identification: macro F1 .751
- Stance recognition: macro F1 .685
- The joint model effectively captures the natural relationship between argument component types and argumentative relations
- Structural features are most effective for component classification
- Discourse features are important for relation identification
- The model tends to identify argumentation structures that are more shallow than gold standard

## Limitations
- The model currently only handles persuasive essays (specific genre)
- Attack relations are underrepresented in the corpus (only 10.7% of arguments)
- The distinction between linked and convergent arguments is not modeled (collapsed following Freeman 2011)
- The model does not distinguish between convergent and serial argument structures
- Limited to essay-level tree structures; more complex graphs (e.g., in scientific text) are not supported
- Error analysis shows the model frequently labels non-argumentative sentences in the conclusion as argumentative
- The model misclassifies some claims as premises and vice versa, particularly at paragraph boundaries

## Testable Properties
- Argumentation structure must be a tree (each premise has exactly one outgoing relation)
- Each paragraph forms a subtree of the overall argumentation structure
- Major claims only appear in introduction or conclusion paragraphs
- Claims always have at least one incoming relation from a premise
- The number of claims should be approximately one per body paragraph
- The proportion of premises to claims should be approximately 2.5:1 (based on corpus statistics)
- Each body paragraph should have at least one claim
- Support relations should outnumber attack relations by approximately 9:1

## Relevance to Project
This paper provides a complete computational framework for automatically extracting argument components and their relations from text, which is directly relevant to the propstore's argument mining capabilities. The annotation scheme (major claim, claim, premise with support/attack relations) maps to the propstore's claim representation. The ILP joint model demonstrates how global structural constraints can improve local classification decisions. The corpus of 402 annotated essays and the indicator lexicons provide empirical grounding for argumentation structure patterns.

## Open Questions
- [ ] How well does this approach generalize to other genres (scientific papers, news, online discourse)?
- [ ] Can the ILP constraints be extended to handle graph structures rather than trees?
- [ ] How does this compare to more recent transformer-based approaches (e.g., Mayer et al. 2020)?
- [ ] Can the indicator lexicons be used to improve claim extraction in the propstore?

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — cited as foundational for argumentation frameworks; this paper's ILP model produces attack/support structures that are instances of Dung's abstract frameworks
- [[Walton_2015_ClassificationSystemArgumentationSchemes]] — cited indirectly through Walton et al. 2008 (Argumentation Schemes); Walton's scheme taxonomy provides the theoretical classification of argument types that this paper's classification model detects empirically
- [[Mayer_2020_Transformer-BasedArgumentMiningHealthcare]] — directly extends this paper's pipeline architecture, replacing CRF/SVM classifiers with transformer-based models for clinical trial argument mining

### Cited By (in Collection)
- [[Mayer_2020_Transformer-BasedArgumentMiningHealthcare]] — cites this as the dominant framework for component+relation AM pipelines and as a baseline comparison

### New Leads (Not Yet in Collection)
- Peldszus and Stede (2015) — "Joint prediction in MST-style discourse parsing for argumentation mining" — alternative joint modeling approach using minimum spanning trees
- Eger, Daxenberger, and Gurevych (2017) — "Neural end-to-end learning for computational argumentation mining" — direct neural successor to this work
- Habernal and Gurevych (2016) — "Argumentation mining in user-generated web discourse" — tests AM approaches on noisy web data
- Rinott et al. (2015) — "Context-dependent evidence detection" — complementary evidence detection approach

### Supersedes or Recontextualizes
- (none in collection)

### Conceptual Links (not citation-based)

**Argumentation theory grounding:**
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — **Strong.** ASPIC+ provides the formal framework for constructing structured arguments from premises and inference rules with three attack types (undermining, rebutting, undercutting). The argument components Stab extracts (major claims, claims, premises) and their relations (support, attack) map directly to ASPIC+ elements. ASPIC+ provides the theoretical semantics for evaluating the argumentation structures that Stab's pipeline identifies empirically.
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — **Moderate.** The full formal treatment of ASPIC+ with preferences; relevant for understanding how preference orderings could be applied to the extracted argumentation structures (e.g., weighting arguments by source credibility or evidence strength).
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — **Strong.** The argumentation structures extracted by Stab's pipeline are bipolar frameworks with both support and attack relations, exactly the structures Cayrol formalizes as BAFs. Cayrol's acceptability semantics (d-admissible, s-admissible, c-admissible) could be applied to determine which extracted arguments are jointly acceptable.

**Claim representation:**
- [[Clark_2014_Micropublications]] — **Moderate.** Clark's micropublications model provides a semantic representation for claims with supporting evidence and challenge relations, which could serve as a target schema for representing the output of Stab's argument mining pipeline.

**Computational argumentation mining:**
- [[Mayer_2020_Transformer-BasedArgumentMiningHealthcare]] — **Strong.** Direct methodological successor: Mayer replaces Stab's feature-engineered CRF/SVM pipeline with transformer-based models, demonstrating that the same pipeline architecture achieves significantly better performance with pretrained language models, especially for relation classification.

## Related Work Worth Reading
- Peldszus and Stede (2013, 2015): Argumentation mining in microtexts
- Habernal and Gurevych (2016): Argumentation mining in user-generated web discourse
- Rinott et al. (2015): Context-dependent evidence detection
- Persing and Ng (2016): End-to-end argumentation mining
- Stab and Gurevych (2014a): Annotating argument components and relations
- Eger, Daxenberger, and Gurevych (2017): Neural end-to-end learning for computational argumentation mining
