---
title: "An appreciation of John Pollock's work on the computational study of argument"
authors: "Henry Prakken, John Horty"
year: 2012
venue: "Argument & Computation"
doi_url: "https://doi.org/10.1080/19462166.2012.663409"
pages: 1-19
---

# An appreciation of John Pollock's work on the computational study of argument

## One-Sentence Summary
A comprehensive survey of John Pollock's contributions to computational argumentation, covering his formalisms for defeasible reasoning (inference graphs, defeat, argument strength, self-defeat cycles) and their relationship to modern structured argumentation frameworks like ASPIC+.

## Problem Addressed
After Pollock's death in 2009, this paper provides a systematic review and critical assessment of his contributions to computational argumentation, contextualizing his work within the broader field and identifying both its lasting impact and its limitations.

## Key Contributions
- Comprehensive survey of Pollock's formal system for defeasible reasoning and argumentation
- Critical comparison between Pollock's approach and modern structured argumentation frameworks (ASPIC+)
- Identification of key design issues in argumentation semantics that Pollock addressed (self-defeat, argument strength, partial composition)
- Assessment of what Pollock's work provides vs. what it lacks for current argumentation research

## Methodology
Survey and critical analysis of Pollock's published work from 1967-2010, organized around his formal contributions: common features, semantics, argument strength, defeasible inference rules, and partial composition. Includes comparison with the ASPIC+ framework.

## Key Concepts

### 1. Defeasible vs. Conclusive Reasons
Pollock distinguishes two types of inference rules:
- **Conclusive (deductive) reasons**: Cannot be defeated
- **Defeasible reasons**: Can be defeated by new information

### 2. Arguments as Inference Lines
An argument is a sequence of inference steps (a "line" in an inference graph). Each line has:
- A proposition (conclusion)
- A set of support lines
- An inference rule (conclusive or defeasible)

**Definition 3.1 (Literal and Defeated Arguments)**
- An argument line at level 0 is self-defeating if not supported by any argument at level 0
- An argument is ultimately undefeated if there is an even number n such that for every m >= n, the argument is undefeated at level m

### 3. Defeat Relations
Two kinds of defeat:
- **Rebutting defeat**: An argument for the negation of a conclusion
- **Undercutting defeat**: An argument that the connection between premises and conclusion does not hold (unique to Pollock's framework)

Pollock emphasized undercutting defeat as a distinctive and important kind of defeat that other frameworks often lack.

### 4. Inference Graphs (not Trees)
Pollock uses inference graphs rather than argument trees. Key properties:
- Arguments share subarguments (subargument sharing)
- A proposition can be supported by multiple independent arguments
- The inference graph is the unit of evaluation, not individual arguments

### 5. Semantics: Partial Defeat Status Assignment
**Definition 3.3 (Partial defeat status assignment)**
An assignment of in/out to a subset of the nodes of an inference graph is a partial defeat status assignment if:
1. If a node is assigned in and out to all its defeaters, the node is assigned in
2. If a node has a defeater assigned in, the node is assigned out
3. Assignments on nodes not in the subset are unconstrained

A **preferred status assignment** is a maximal partial defeat status assignment that is admissible (no node assigned both in and out).

### 6. Self-Defeating Arguments
Two types identified:
- **Parallel self-defeat** (Figure 2): Two arguments that defeat each other symmetrically
- **Serial self-defeat** (Figure 3): An argument that defeats itself through a chain

Key insight: Self-defeating arguments should not be able to defeat other arguments. Pollock's semantics handles this by keeping self-defeating arguments from being ultimately undefeated.

### 7. Defeat Cycles
- **Even defeat cycles** (Figure 5): Two arguments defeat each other; neither can be justified; both should be undecided
- **Odd defeat cycles** (Figure 6): Three arguments in a cycle; Pollock's system does not handle these well (assigns all as ultimately undefeated)

### 8. Argument Strength
Pollock took argument strength seriously but his approach was not standard:
- Not based on Bayesian probability
- Degree of justification of a statement is a numerical value
- Strength of each conclusion is the minimum of the strengths of support and the strengths of the attacking/supporting arguments
- While these arguments can have various strengths, defeat is still all-or-nothing: a defeater that is weaker than its target cannot succeed

### 9. Suppositional Reasoning
Pollock extended his system with suppositional reasoning:
- Allows suppositions to be introduced and retracted
- Lines of argument from suppositions are treated as part of natural deduction
- This feature has not been taken up by others

### 10. Partial Composition
Pollock addressed partial composition: dealing with the interrelationship of the full system, not just atomic propositions but also the interaction of complex arguments composed of many subarguments.

## Figures of Interest
- **Fig 1 (page 5):** Example inference graph with birds/penguins/ostriches showing defeasible inference rules and defeat
- **Fig 2 (page 9):** Parallel self-defeat diagram
- **Fig 3 (page 9):** Serial self-defeat diagram
- **Fig 4 (page 10):** Self-defeating witness example
- **Fig 5 (page 11):** Even defeat cycle
- **Fig 6 (page 11):** Odd defeat cycle

## Section 3.4: Defeasible Inference Rules and Argumentation Schemes
- Pollock's defeasible inference rules include: perception, memory, induction, statistical syllogism, temporal persistence
- These are domain-specific epistemic rules, not general patterns
- Connection to argumentation schemes (Walton, Reed, Macagno 2008): argumentation schemes are stereotypical non-deductive patterns of reasoning with associated critical questions
- Critical questions challenge an argument's premise or provide counter-considerations
- Pollock's emphasis on defeasible reasons plus his rebutting/undercutting distinction provides a formal framework for modeling argumentation schemes

## Section 4: Critique — Comparison with Structured Argumentation
The authors argue Pollock's work is better understood within the context of modern structured argumentation frameworks rather than purely as non-monotonic logic:
- Much formal work on argumentation uses Dung's (1995) abstract framework
- ASPIC+ (Prakken 2010, Modgil and Prakken 2011) combines Pollock's ideas with structured argumentation
- Key distinction: Pollock never made a clear separation between attack and defeat (defeat = successful attack after considering strength), which leads to confusion
- Pollock's defeasible reasoning is really about handling default assumptions with exceptions, not about non-monotonic logic per se
- Typical reductions of defeasible reasoning to non-monotonic reasoning handle exceptions by embedding them as default assumptions with lower priority

## Section 5: Working Style
- Pollock's OSCAR system was a remarkable computational implementation
- He was primarily a philosopher who also programmed
- His formalism was designed for completeness rather than clarity for outside readers
- The relations between his work and Dung's (1995) abstract argumentation are not well understood because Pollock worked in isolation from the AI argumentation community

## Section 6: Summary of Pollock's Contributions
1. Proposed one of the first non-monotonic logics with explicit notions of argument and defeat
2. Was one of the important early (before Dung) thinkers on defeat/undercutting distinction
3. First to regard defeasible reasons as general principles of reasoning (not just legal/domain-specific)
4. Grounded his formalism in epistemology and laid basis for argumentation schemes
5. The grounding idea of his work on argumentation (derived from epistemology) was to model defeasible reasoning as general-purpose inference
6. Worked on argument strength seriously (though not fully resolved)
7. Addressed suppositional reasoning and practical cognition (decision-theoretic planning)

## Parameters

This is a survey/review paper and does not introduce quantitative parameters.

## Implementation Details
- Pollock's OSCAR system: implemented in Common Lisp
- Available at: http://oscarhome.soc-sci.arizona.edu/ftp/OSCAR-web-page/oscar.html (as of 2011)
- Graduate students on Pollock's team helped with coding
- The system is monolithic and not easy to extend or modify

## Results Summary
This is a survey paper. The key finding is that Pollock's work anticipated many concepts that became central to computational argumentation (inference graphs, undercutting defeat, argument strength, self-defeat handling) but remained somewhat isolated from the mainstream AI argumentation community.

## Limitations
- Pollock never clearly distinguished attack from defeat
- His treatment of argument strength was ad hoc and not axiomatically grounded
- Self-defeating arguments and odd defeat cycles are not handled optimally
- His work on suppositional reasoning has not been followed up
- The OSCAR system is difficult to use and extend
- Pollock worked in relative isolation from the structured argumentation community

## Testable Properties
- Undercutting defeat must be distinguishable from rebutting defeat in any implementation of Pollock's framework
- Self-defeating arguments must not be able to defeat non-self-defeating arguments
- In even defeat cycles, neither argument should be ultimately undefeated (both should be undecided)
- Argument strength must propagate: the strength of a conclusion cannot exceed the minimum strength of its supporting lines
- Partial defeat status assignments must be maximal and admissible

## Relevance to Project
This paper provides essential historical context for understanding the foundations of computational argumentation. Key relevances:
1. The rebutting vs. undercutting defeat distinction is fundamental for any argumentation system
2. Inference graphs (vs. trees) with subargument sharing are the right data structure for argumentation
3. The concept of partial defeat status assignment connects to modern labelling-based semantics
4. Argumentation schemes bridge Pollock's defeasible reasons to practical knowledge representation
5. The ASPIC+ framework (by the first author) is positioned as the modern successor that integrates Pollock's ideas

## Open Questions
- [ ] How does Pollock's notion of argument strength compare to probabilistic approaches (e.g., Bayesian)?
- [ ] Can Pollock's undercutting defeat be cleanly mapped to ASPIC+ undercuts?
- [ ] What is the relationship between Pollock's inference graphs and Dung's abstract argumentation frameworks?
- [ ] Has anyone successfully extended OSCAR or reimplemented Pollock's system in a modern language?

## Related Work Worth Reading
- Pollock (1995) "Cognitive Carpentry" - Pollock's main book on his system
- Pollock (2009/2010) - His last papers refining the system
- Dung (1995) "On the Acceptability of Arguments" - The foundational abstract argumentation paper
- Modgil and Prakken (2011) - ASPIC+ framework paper
- Walton, Reed, Macagno (2008) - Argumentation schemes
- Baroni and Giacomin (2009) - Survey of argumentation semantics
- Caminada (2006) - Labelling-based semantics
- Besnard and Hunter (2001, 2008) - Logic-based argumentation
- Vreeswijk (1997) - Abstract argumentation systems

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] -- cited extensively as the foundational abstract argumentation framework that Pollock's work is compared against; Prakken & Horty argue Pollock's system should be understood as generating Dung-style frameworks
- [[Pollock_1987_DefeasibleReasoning]] -- the primary subject paper; this survey reviews and extends the ideas introduced there
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] -- the ASPIC+ framework by co-author Prakken, positioned as the modern integration of Pollock's ideas with structured argumentation
- [[Walton_2015_ClassificationSystemArgumentationSchemes]] -- cited for argumentation schemes that connect to Pollock's defeasible inference rules
- [[Reiter_1980_DefaultReasoning]] -- cited as the parallel non-monotonic reasoning tradition that Pollock's work relates to but differs from

### New Leads (Not Yet in Collection)
- Pollock (1995) "Cognitive Carpentry" -- Pollock's most comprehensive book on his OSCAR system; primary source for implementation details
- Pollock (2009b) "A Recursive Semantics for Defeasible Reasoning" -- Pollock's last major technical paper in the Rahwan & Simari handbook
- Baroni and Giacomin (2009) "Semantics of Abstract Argument Systems" -- comprehensive survey of argumentation semantics
- Caminada (2006) "On the Issue of Reinstatement in Argumentation" -- labelling-based semantics relevant to Pollock's defeat status assignments
- Besnard and Hunter (2008) "Elements of Argumentation" -- logic-based deductive argumentation

### Supersedes or Recontextualizes
- [[Pollock_1987_DefeasibleReasoning]] -- this survey contextualizes, extends, and critiques the 1987 paper's contributions from a 25-year retrospective, identifying limitations (unclear attack/defeat distinction, ad hoc argument strength) not visible in the original

### Cited By (in Collection)
- (none found -- this paper is cited by Modgil 2014 and Walton 2015 in their citations.md, but those cite other Prakken works, not this specific 2012 paper)

### Conceptual Links (not citation-based)
**Argumentation foundations:**
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] -- Cayrol's bipolar argumentation extends Dung's framework with support relations; Prakken & Horty's survey identifies the lack of support relations as a gap in Pollock's system, making bipolar frameworks a natural extension of the ideas discussed here
- [[Clark_2014_Micropublications]] -- Clark's micropublications model uses Toulmin-Verheij argumentation to structure scientific claims; Prakken & Horty's discussion of argumentation schemes and defeasible inference rules provides the theoretical grounding for Clark's claim-evidence-challenge structure
- [[Doyle_1979_TruthMaintenanceSystem]] -- Pollock's inference graphs and defeat status assignments are structurally related to Doyle's TMS dependency networks and belief revision; both systems face the same fundamental problem of maintaining consistent belief sets under new information
- [[deKleer_1986_AssumptionBasedTMS]] -- de Kleer's ATMS labels (environments under which conclusions hold) relate to Pollock's partial defeat status assignments; both track multiple simultaneous reasoning contexts, though from engineering vs epistemological perspectives
