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
A comprehensive survey of John Pollock's contributions to computational argumentation, covering his formalisms for defeasible reasoning (inference graphs, defeat, argument strength, self-defeat cycles) and their relationship to modern structured argumentation frameworks like ASPIC+. *(p.1)*

## Problem Addressed
After Pollock's death in 2009, this paper provides a systematic review and critical assessment of his contributions to computational argumentation, contextualizing his work within the broader field and identifying both its lasting impact and its limitations. *(p.1)*

## Key Contributions
- Comprehensive survey of Pollock's formal system for defeasible reasoning and argumentation *(p.1-2)*
- Critical comparison between Pollock's approach and modern structured argumentation frameworks (ASPIC+) *(p.13-14)*
- Identification of key design issues in argumentation semantics that Pollock addressed (self-defeat, argument strength, partial composition) *(p.7-13)*
- Assessment of what Pollock's work provides vs. what it lacks for current argumentation research *(p.15-16)*

## Methodology
Survey and critical analysis of Pollock's published work from 1967-2010, organized around his formal contributions: common features, semantics, argument strength, defeasible inference rules, and partial composition. Includes comparison with the ASPIC+ framework. *(p.2)*

## Key Concepts

### 1. Defeasible vs. Conclusive Reasons
Pollock distinguishes two types of inference rules: *(p.2)*
- **Conclusive (deductive) reasons**: Cannot be defeated
- **Defeasible reasons**: Can be defeated by new information
- Pollock emphasized that defeasible reasoning is not just exotic or exceptional but is in fact essential and omnipresent in cognitive life *(p.2)*
- Key quote: "we cannot get around the real-world reasoning if reasoning from plausible but unsure beliefs together with reasoning involving tentative (withdrawable/endorsement-sensitive defeasible steps)" *(p.2)*

### 2. Arguments as Inference Lines
An argument is a sequence of inference steps (a "line" in an inference graph). Each line has: *(p.4)*
- A proposition (conclusion)
- A set of support lines
- An inference rule (conclusive or defeasible)

**Definition 3.1 (Literal and Defeated Arguments)** *(p.4)*
An argument line (p, r, {c_1,...,c_n}) is a triple where p is a proposition, r is a reason, and c_1,...,c_n are the support lines. Arguments can be either linear (a single chain of lines) or can share subarguments.

### 3. Defeat Relations
Two kinds of defeat: *(p.4, 6)*
- **Rebutting defeat**: An argument for the negation of a conclusion — a defeater rebuts line l if it supports ~p where p is the conclusion of l *(p.6)*
- **Undercutting defeat**: An argument that the connection between premises and conclusion does not hold (unique to Pollock's framework) — a defeater undercuts line l if it supports ~r_i where r_i is a defeasible reason used in l *(p.4, 6)*

Pollock emphasized undercutting defeat as a distinctive and important kind of defeat that other frameworks often lack. *(p.2, 12)*

### 4. Inference Graphs (not Trees)
Pollock uses inference graphs rather than argument trees. Key properties: *(p.4-6)*
- Arguments share subarguments (subargument sharing) *(p.6)*
- A proposition can be supported by multiple independent arguments *(p.6)*
- The inference graph is the unit of evaluation, not individual arguments *(p.6)*
- In Figure 1, defeaters, rebutting-defeaters, defeasible inferences are visualized with, respectively, solid and dashed lines; within arrows, bold, while defeat relations are displayed with wavy arrows *(p.5)*

### 5. Defeasible Inference Rules
Pollock provides four main defeasible inference rules: *(p.5)*
- **r_1**: That an object looks like having property P is a defeasible reason for believing that the object has property P *(p.5)*
- **r_2**: That x is observed/has P's are Q's (where x is a P, 0.95) is a defeasible reason for believing that most P's are Q's *(p.5)*
- **r_3**: That most P's are Q's and x is a P is a defeasible reason for believing that x is a Q — the statistical syllogism *(p.5)*
- **r_4**: A subclass defeater for the statistical syllogism *(p.5)*
- Rule r_1 expresses that perceptions yield a defeasible reason for believing that what is perceived to be the case is indeed the case; rule r_3 captures enumerative induction; rule r_4 can be seen as a special case of the argumentation scheme from expert testimony *(p.5)*

### 6. Semantics: Partial Defeat Status Assignment
**Definition 3.2 (Semantics of Pollock 1987)** *(p.7)*
- (1) All arguments that are not self-defeating arguments are set at level 0
- (2) An argument is at level i + 1 if it is not defeated by any argument at level i
- An argument is ultimately undefeated if there is an n such that for every m >= n, the argument is undefeated at level m

**Definition 3.3 (Partial defeat status assignment)** *(p.7)*
An assignment of in/out to a subset of the nodes of an inference graph is a partial defeat status assignment if:
1. If a node is assigned in and out to all its defeaters, the node is assigned in
2. If a node has a defeater assigned in, the node is assigned out
3. Assignments on nodes not in the subset are unconstrained

A **preferred status assignment** is a maximal partial defeat status assignment that is admissible (no node assigned both in and out). *(p.7)*

Pollock later (1994, 1995) turned to a labelling-based approach which assigns labels in, out, or neither to every node in the inference graph. *(p.7)*

**Definition 3.4 (Labelling)** *(p.8)*
1. An argument is in if all arguments defeating it are out
2. An argument is out if it is defeated by an argument that is in
3. The labelling is based on defeat, not attack (successful attack after considering strength)

A labelling is preferred if it maximizes the set of in arguments, while it is grounded if it minimizes the set of in arguments. *(p.8)*

### 7. Self-Defeating Arguments
Two types identified: *(p.8-9)*
- **Parallel self-defeat** (Figure 2, p.9): Two arguments that defeat each other symmetrically — e.g., q leads to p via r_1, while r leads to ~p via r_2; both p and ~p then support contradictions via Ex Falso *(p.9)*
- **Serial self-defeat** (Figure 3, p.9): An argument that defeats itself through a chain — e.g., "Witness John says he is incredible" yields via r_1 "John is incredible" which undercuts the very reason r_1 used to derive it *(p.9)*

Key insight: Self-defeating arguments should not be able to defeat other arguments. *(p.8)* Pollock's semantics handles this: in Definition 3.1, a self-defeating argument is never ultimately undefeated at any level, so it cannot defeat other arguments. *(p.8)* However, in Definition 3.3 (partial status assignments), serial self-defeat is handled more carefully: the self-defeating argument line is still assigned out (defeated outright), retaining its ability to prevent other argument lines from being ultimately undefeated. *(p.9)*

**Figure 4 (p.10): Self-defeating witness** — shows a more complex example where Witness John says both that he is incredible AND that the suspect hit the victim; the argument for "suspect hit victim" should survive even though the credibility argument is self-defeating. *(p.10)*

### 8. Defeat Cycles
- **Even defeat cycles** (Figure 5, p.11): Two arguments defeat each other (Albert says Bob is incredible, Bob says Albert is incredible); neither can be justified; both should be undecided *(p.10-11)*
- **Odd defeat cycles** (Figure 6, p.11): Three arguments in a cycle; Pollock's system does not handle these well *(p.10-11)*

Pollock distinguishes between four treatments of even and odd defeat cycles: *(p.10)*
1. Assign all as ultimately undefeated
2. Assign none as ultimately undefeated
3. Different treatment for even vs. odd cycles
4. Use preferred or grounded semantics

In late publications (2009), Pollock revisited his semantics: invented by Baroni and Giacomin (2007), he related that even cycles should result in all arguments being undefeated while odd cycles should make some arguments defeated. *(p.10)*

**Complex defeat cycle example (p.10-11):** The Albert/Bob/Carole/Donald witness example demonstrates a chain of credibility attacks with both even and odd cycle structures; Pollock's analysis shows that line 8 is ultimately undefeated while line 10 is ultimately undefeated depending on semantics chosen. *(p.10-11)*

### 9. Argument Strength
Pollock took argument strength seriously but his approach was non-standard: *(p.11)*
- Not based on Bayesian probability — Pollock argued that degrees of belief and justification do not conform to the laws of probability theory *(p.11)*
- His argument: if 0.01 is a degree of justification, then we should be equally justified in believing Fermat's conjecture held and other Andrew Wiles proved it *(p.11)*
- Degree of justification of a statement is a numerical value *(p.11)*
- Strength of each conclusion is the minimum of the strengths of support and the strengths of the attacking/supporting arguments *(p.11)*
- Pollock seemed not fully sure that his 2002 account was the right one; in response to critique he noted "Let me stress that I do not regard this as a settled issue" *(p.11-12)*
- While arguments can have various strengths, defeat is still all-or-nothing: a defeater that is weaker than its target cannot succeed *(p.11)*
- In 1995, Pollock made justification of statements a numerical matter: being a function of the strengths of both supporting and defeating arguments *(p.11)*

### 10. Defeasible Inference Rules and Argumentation Schemes
- Pollock's defeasible inference rules include: perception, memory, induction, statistical syllogism, temporal persistence *(p.12)*
- These are domain-specific epistemic rules, not general patterns *(p.12)*
- Connection to argumentation schemes (Walton, Reed, Macagno 2008): argumentation schemes are stereotypical non-deductive patterns of reasoning with associated critical questions *(p.12)*
- Critical questions challenge an argument's premise or provide counter-considerations *(p.12)*
- Pollock's emphasis on defeasible reasons plus his rebutting/undercutting distinction provides a formal framework for modeling argumentation schemes *(p.12)*
- Some critical questions challenge an argument's premise and therefore point to rebutting attacks; others relate to undercutting attacks *(p.12)*
- Pollock's defeasible inference rules can in fact be seen as formalisations of some epistemic argumentation schemes *(p.12)*

### 11. Suppositional Reasoning
Pollock extended his system with suppositional reasoning: *(p.13)*
- In earlier work, he allowed for conjunctions to be introduced and extracted from lines of argument just as in natural deduction *(p.13)*
- This allows suppositions to be introduced and retracted *(p.13)*
- Lines of argument from suppositions are treated as part of natural deduction *(p.13)*
- This feature has not been taken up by others *(p.13)*

### 12. Partial Composition
Pollock addressed partial composition: dealing with the interrelationship of the full system, not just atomic propositions but also the interaction of complex arguments composed of many subarguments. *(p.13)*
- In his view, "justified", "unjustified", simply compute defeat status relative to the inference graph computed at a certain moment *(p.13)*
- Pollock also developed an alternative notion of adequacy of arguments for defeasible reasoning, given that to be tractable, they cannot be sound and complete with respect to the ideal *(p.13)*

### 13. Attack vs. Defeat Distinction
A key critique by the authors: Pollock never made a clear separation between attack and defeat. *(p.14)*
- In ASPIC+: attack is a structural relation (argument A attacks argument B), defeat is attack that succeeds after considering preferences/strength *(p.14)*
- Pollock did not include premise attack in his work; he was only interested in what can be defensibly derived from a consistent base of information *(p.14)*
- This means his system cannot deal with attacks on strict premises, since the premises are only supplied from a consistent knowledge base *(p.14)*
- The distinction matters because without it, formalising priority-based reasoning becomes confused *(p.14)*

### 14. Defeasible Reasoning vs. Non-monotonic Logic
The authors argue Pollock's work should not be viewed as non-monotonic logic: *(p.14)*
- Whether such a reduction is possible or not, it should at least be clear that it is a somewhat natural way to model defeasible reasoning *(p.14)*
- Typical reductions of defeasible reasoning to non-monotonic reasoning handle exceptions by adding default assumptions with a lower priority *(p.14)*
- Consider the Quakers example: it is certainly possible to accept that Quakers are normally pacifists, that Republicans are normally not pacifists, and that Nixon was both a Quaker and a Republican *(p.14)*
- In Pollock's framework, defeasible rules directly capture that 'if Q, then normally P' and 'if Q', taken together, do not deductively imply P, since things may turn out otherwise *(p.14)*
- There is a genuine philosophical distinction between plausible and defeasible reasoning: plausible reasoning is valid deductive reasoning from an uncertain basis, while defeasible reasoning is deductively invalid but rationally compelling *(p.14)*

## Figures of Interest
- **Fig 1 (p.5):** Example inference graph with birds/penguins/ostriches showing defeasible inference rules r1-r4 and defeat relations; includes defeaters, rebutting defeaters, defeasible inferences visualized distinctly
- **Fig 2 (p.9):** Parallel self-defeat diagram — two arguments q->p and r->~p lead to contradiction via Ex Falso
- **Fig 3 (p.9):** Serial self-defeat diagram — "Witness John says he is incredible" chain that undercuts itself
- **Fig 4 (p.10):** Self-defeating witness — extended example with both incredible-witness and suspect-hit-victim arguments
- **Fig 5 (p.11):** Even defeat cycle — Albert/Bob mutual incredibility
- **Fig 6 (p.11):** Odd defeat cycle — extended chain with Albert/Bob/Carole/Donald

## Section 4: Critique -- Comparison with Structured Argumentation
The authors argue Pollock's work is better understood within the context of modern structured argumentation frameworks rather than purely as non-monotonic logic: *(p.13-14)*
- Much formal work on argumentation uses Dung's (1995) abstract framework *(p.13)*
- ASPIC+ (Prakken 2010, Modgil and Prakken 2011) combines Pollock's ideas with structured argumentation *(p.13)*
- Key distinction: Pollock never made a clear separation between attack and defeat (defeat = successful attack after considering strength), which leads to confusion *(p.14)*
- Pollock's defeasible reasoning is really about handling default assumptions with exceptions, not about non-monotonic logic per se *(p.14)*
- The current ASPIC+ framework (Prakken 2010a, Modgil and Prakken 2011) further develops Pollock's ideas into a general framework for structured argumentation with both strict and defeasible inference rules *(p.13)*

## Section 5: Working Style
- Pollock's OSCAR system was a remarkable computational implementation *(p.15)*
- He was primarily a philosopher who also programmed *(p.15)*
- His formalism was designed for completeness rather than clarity for outside readers *(p.15)*
- The relations between his work and Dung's (1995) abstract argumentation are not well understood because Pollock worked in isolation from the AI argumentation community *(p.15)*
- It is sometimes said that Pollock's formalism for defeasible reasoning is too complex, but the authors note that this criticism is entirely fair: the main reason for the complexity is that Pollock's aim was to design complete and simple formalisms, but to make defeasible reasoning in its full complexity *(p.15)*
- However, on subordinate aspects of his writings, Pollock was always exceptionally clear and explicit about the reasons for and against his design choices *(p.15)*
- An admirable aspect of Pollock was his willingness to keep re-thinking and re-making his approach: he was always willing to re-think even the most fundamental aspects of his existing theories *(p.15)*

## Section 6: Summary of Pollock's Contributions
*(p.15-16)*
1. He proposed one of the first non-monotonic logics with explicit notions of argument and defeat *(p.16)*
2. He was one of the important and now familiar distinction between undercutting and rebutting defeaters *(p.16)*
3. He was the first in AI to regard defeasible reasons as general principles of reasoning. He thus grounded his formalism in his work on epistemology and laid the basis for formulating argumentation schemes. *(p.16)*
4. The grounding idea of his work on argumentation (derived from epistemology) was to model defeasible reasoning as general-purpose inference *(p.16)*
5. He took self-defeating arguments more seriously than anyone else *(p.16)*
6. Worked on argument strength seriously (though not fully resolved) *(p.16)*
7. He work argued that defeasible reasons can be arranged in a linear order of strength and newer thought of incorporating strengths or about defeasible reasoning about the strength of defeasible arguments *(p.16)*
8. Some aspects of his work have not survived: suppositional reasoning, and his work on practical reasoning (decision-theoretic planning) *(p.16)*
9. His work on argumentation only modified epistemic reasoning, not e.g. practical or deontic reasoning *(p.16)*
10. Pollock's work reminds us of the richness of the object of study — sometimes ignored in current work on abstract or deductive argumentation *(p.16)*

## Terminological Note
*(p.16-17)*
- Pollock tended to use his own terminology: in his earlier papers, he exclusively spoke of "conclusive" and "prima facie" reasons, while later he also referred to "deductive" and "defeasible" reasons *(p.16)*
- "Inference rules" (= "standards") = his tell analogues of deductive and defeasible reason relations/rules *(p.16)*
- By "classical argumentation" he means the special case of defeasible argumentation where the inference rules consist of all valid propositional or first-order inference rules *(p.17)*

## Parameters

This is a survey/review paper and does not introduce quantitative parameters.

## Implementation Details
- Pollock's OSCAR system: implemented in Common Lisp *(p.15)*
- Available at: http://oscarhome.soc-sci.arizona.edu/ftp/OSCAR-web-page/oscar.html (as of 2011) *(p.15)*
- Graduate students on Pollock's team helped with coding *(p.15)*
- The system is monolithic and not easy to extend or modify *(p.15)*

## Arguments Against Prior Work

These are Prakken and Horty's critiques of Pollock's system and its limitations relative to modern structured argumentation:

1. **Pollock never clearly distinguished attack from defeat.** In ASPIC+, attack is a structural relation (argument A attacks argument B), while defeat is attack that succeeds after considering preferences/strength. Pollock conflated these concepts, which leads to confusion when formalizing priority-based reasoning. *(p.14)*
2. **Pollock did not include premise attack (undermining).** He was only interested in what can be defeasibly derived from a consistent base of information, meaning his system cannot handle attacks on strict premises. *(p.14)*
3. **Pollock's argument strength approach was non-standard and unresolved.** He rejected Bayesian probability but his alternative (degree of justification as a numerical value, with strength of conclusion = minimum of support strengths) was not axiomatically grounded. Pollock himself acknowledged: "Let me stress that I do not regard this as a settled issue." *(p.11-12)*
4. **Pollock worked in isolation from the AI argumentation community.** The relations between his work and Dung's (1995) abstract argumentation are not well understood because Pollock developed his formalism independently. His OSCAR system was monolithic and difficult for others to extend or modify. *(p.15)*
5. **Pollock's formalism was designed for completeness rather than clarity.** His system aimed to model defeasible reasoning in its full complexity, making it overwhelmingly complex for outside readers. However, on subordinate aspects of his writing, Pollock was "always exceptionally clear and explicit about the reasons for and against his design choices." *(p.15)*
6. **Pollock only addressed epistemic reasoning, not practical or deontic reasoning.** His work on argumentation only modeled epistemic reasoning. His decision-theoretic planning work was separate and not integrated into his argumentation framework. *(p.16)*
7. **Suppositional reasoning was not adopted by others.** Pollock extended his system with suppositional reasoning (introducing and retracting suppositions as in natural deduction), but this feature has not been taken up by the argumentation community. *(p.13, p.16)*
8. **Self-defeat and odd defeat cycles were not fully resolved.** Pollock took self-defeating arguments more seriously than anyone else, but his treatment of odd defeat cycles remained problematic. He revisited his semantics late in his career but did not arrive at a definitive solution. *(p.8-11)*

## Design Rationale

These are the design principles behind Pollock's system as identified by Prakken and Horty:

1. **Defeasible reasoning is essential and omnipresent in cognitive life.** Pollock's foundational insight was that defeasible reasoning is not exotic or exceptional but is the dominant mode of real-world reasoning. We cannot get around "reasoning from plausible but unsure beliefs together with reasoning involving tentative (withdrawable) defeasible steps." *(p.2)*
2. **Inference graphs rather than argument trees.** Arguments share subarguments, and a proposition can be supported by multiple independent arguments. The inference graph is the unit of evaluation, not individual arguments. This captures the structure of real reasoning more faithfully than tree-based representations. *(p.4-6)*
3. **Rebutting and undercutting defeat as distinct types.** Pollock was the first to formalize undercutting defeat (attacking the inferential connection between premises and conclusion) as distinct from rebutting defeat (attacking the conclusion itself). This distinction became fundamental to all subsequent argumentation research. *(p.2, p.4, p.6)*
4. **Defeasible inference rules grounded in epistemology.** Pollock's defeasible rules (perception, memory, induction, statistical syllogism, temporal persistence) are domain-specific epistemic principles, not arbitrary patterns. He grounded his formalism in his philosophical work on epistemology, providing principled justification for each rule. *(p.5, p.12)*
5. **Partial defeat status assignments.** Rather than assigning a single global status to all arguments, Pollock developed partial defeat status assignments that label a subset of nodes as in/out, with preferred assignments maximizing the labelled set. This later evolved into a full labelling approach. *(p.7-8)*
6. **Self-defeating arguments must not defeat others.** Pollock took the principled position that self-defeating arguments (both parallel and serial) should not be able to defeat non-self-defeating arguments. His semantics ensures this: a self-defeating argument is never ultimately undefeated at any level. *(p.8-9)*
7. **Argument strength propagates via minimum.** The strength of a conclusion is the minimum of the strengths of its supporting lines and the strengths of the attacking/supporting arguments. While arguments can have various strengths, defeat is still all-or-nothing: a defeater that is weaker than its target cannot succeed. *(p.11)*
8. **Defeasible reasoning is philosophically distinct from non-monotonic logic.** Pollock maintained that plausible reasoning (valid deductive reasoning from an uncertain basis) and defeasible reasoning (deductively invalid but rationally compelling) are genuinely different. Typical reductions of defeasible reasoning to non-monotonic reasoning handle exceptions by adding default assumptions, which misses this distinction. *(p.14)*
9. **Willingness to revise fundamentals.** Pollock continuously re-examined and revised his own theories. "An admirable aspect of Pollock was his willingness to keep re-thinking and re-making his approach: he was always willing to re-think even the most fundamental aspects of his existing theories." *(p.15)*

## Results Summary
This is a survey paper. The key finding is that Pollock's work anticipated many concepts that became central to computational argumentation (inference graphs, undercutting defeat, argument strength, self-defeat handling) but remained somewhat isolated from the mainstream AI argumentation community. *(p.15-16)*

## Limitations
- Pollock never clearly distinguished attack from defeat *(p.14)*
- His treatment of argument strength was ad hoc and not axiomatically grounded *(p.11-12)*
- Self-defeating arguments and odd defeat cycles are not handled optimally *(p.10-11)*
- His work on suppositional reasoning has not been followed up *(p.13, 16)*
- The OSCAR system is difficult to use and extend *(p.15)*
- Pollock worked in relative isolation from the structured argumentation community *(p.15)*
- While Pollock took argument strength seriously, he did not explicitly distinguish between attack and defeat, which sometimes leads to confusion (this matter is fully discussed in Horty 2012) *(p.16)*

## Testable Properties
- Undercutting defeat must be distinguishable from rebutting defeat in any implementation of Pollock's framework *(p.4, 12)*
- Self-defeating arguments must not be able to defeat non-self-defeating arguments *(p.8)*
- In even defeat cycles, neither argument should be ultimately undefeated (both should be undecided) *(p.10-11)*
- Argument strength must propagate: the strength of a conclusion cannot exceed the minimum strength of its supporting lines *(p.11)*
- Partial defeat status assignments must be maximal and admissible *(p.7)*
- A serial self-defeating argument that is defeated outright should still retain its ability to prevent other argument lines from being ultimately undefeated *(p.9)*
- In the preferred labelling, the set of in arguments is maximized; in the grounded labelling, it is minimized *(p.8)*

## Relevance to Project
This paper provides essential historical context for understanding the foundations of computational argumentation. Key relevances:
1. The rebutting vs. undercutting defeat distinction is fundamental for any argumentation system *(p.2, 4, 12)*
2. Inference graphs (vs. trees) with subargument sharing are the right data structure for argumentation *(p.4-6)*
3. The concept of partial defeat status assignment connects to modern labelling-based semantics *(p.7-8)*
4. Argumentation schemes bridge Pollock's defeasible reasons to practical knowledge representation *(p.12)*
5. The ASPIC+ framework (by the first author) is positioned as the modern successor that integrates Pollock's ideas *(p.13)*
6. The attack vs. defeat distinction is critical for any system that handles preferences *(p.14)*

## Open Questions
- [ ] How does Pollock's notion of argument strength compare to probabilistic approaches (e.g., Bayesian)? *(cf. p.11)*
- [ ] Can Pollock's undercutting defeat be cleanly mapped to ASPIC+ undercuts? *(cf. p.13)*
- [ ] What is the relationship between Pollock's inference graphs and Dung's abstract argumentation frameworks? *(cf. p.7, 13)*
- [ ] Has anyone successfully extended OSCAR or reimplemented Pollock's system in a modern language? *(cf. p.15)*
- [ ] How should odd defeat cycles be handled — Pollock's late revision or Baroni/Giacomin's approach? *(cf. p.10-11)*

## Related Work Worth Reading
- Pollock (1995) "Cognitive Carpentry" - Pollock's main book on his system *(cited p.3, 7, 13)*
- Pollock (2009b) "A Recursive Semantics for Defeasible Reasoning" -- Pollock's last major technical paper in the Rahwan & Simari handbook *(cited p.10)*
- Dung (1995) "On the Acceptability of Arguments" - The foundational abstract argumentation paper *(cited p.3, 7)*
- Modgil and Prakken (2011) - ASPIC+ framework paper *(cited p.2, 13)*
- Walton, Reed, Macagno (2008) - Argumentation schemes *(cited p.12)*
- Baroni and Giacomin (2009) "Semantics of Abstract Argument Systems" -- comprehensive survey of argumentation semantics *(cited p.7, 10)*
- Caminada (2006) "On the Issue of Reinstatement in Argumentation" -- labelling-based semantics relevant to Pollock's defeat status assignments *(cited p.7)*
- Besnard and Hunter (2008) "Elements of Argumentation" -- logic-based deductive argumentation *(cited p.13)*
- Horty (2012) "Reasons as Defaults" -- discusses attack/defeat distinction in detail *(cited p.16)*
- Vreeswijk (1997) "Abstract Argumentation Systems" *(cited p.3)*

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] -- cited extensively as the foundational abstract argumentation framework that Pollock's work is compared against; Prakken & Horty argue Pollock's system should be understood as generating Dung-style frameworks *(p.3, 7, 13)*
- [[Pollock_1987_DefeasibleReasoning]] -- the primary subject paper; this survey reviews and extends the ideas introduced there *(p.3-4)*
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] -- the ASPIC+ framework by co-author Prakken, positioned as the modern integration of Pollock's ideas with structured argumentation *(p.2, 13)*
- [[Walton_2015_ClassificationSystemArgumentationSchemes]] -- cited for argumentation schemes that connect to Pollock's defeasible inference rules *(p.12)*
- [[Reiter_1980_DefaultReasoning]] -- cited as the parallel non-monotonic reasoning tradition that Pollock's work relates to but differs from *(p.3)*
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] -- cited as "Modgil and Prakken (2011)"; positioned as the modern ASPIC+ framework integrating Pollock's ideas with structured argumentation and preference-based defeat *(p.2, 13)*
- [[Prakken_2010_AbstractFrameworkArgumentationStructured]] -- cited as "Prakken 2010"; the original ASPIC framework paper combining Pollock's ideas (undercutting/rebutting) with structured argumentation and Dung's abstract framework *(p.2, 13)*

### New Leads (Not Yet in Collection)
- Pollock (1995) "Cognitive Carpentry" -- Pollock's most comprehensive book on his OSCAR system; primary source for implementation details *(cited p.3, 7, 13)*
- Pollock (2009b) "A Recursive Semantics for Defeasible Reasoning" -- Pollock's last major technical paper in the Rahwan & Simari handbook *(cited p.10)*
- Baroni and Giacomin (2009) "Semantics of Abstract Argument Systems" -- comprehensive survey of argumentation semantics *(cited p.7, 10)*
- Besnard and Hunter (2008) "Elements of Argumentation" -- logic-based deductive argumentation *(cited p.13)*
- Horty (2012) "Reasons as Defaults" -- co-author's book-length treatment of the attack/defeat distinction *(cited p.16)*

### Now in Collection (previously listed as leads)
- [[Caminada_2006_IssueReinstatementArgumentation]] — Provides labelling-based characterization of Dung's semantics through reinstatement postulates, establishing exact bijection between complete extensions and reinstatement labellings (in/out/undec). Introduces semi-stable semantics (minimal undec). Directly relevant to Pollock's defeat status assignments discussed *(p.7)*: Caminada's three-valued labellings formalize the same in/out/undecided status that Pollock used informally in his inference graphs.

### Supersedes or Recontextualizes
- [[Pollock_1987_DefeasibleReasoning]] -- this survey contextualizes, extends, and critiques the 1987 paper's contributions from a 25-year retrospective, identifying limitations (unclear attack/defeat distinction, ad hoc argument strength) not visible in the original *(p.14-16)*

### Cited By (in Collection)
- (none found -- no collection paper cites this specific 2012 appreciation paper)

### Now in Collection (previously unlisted)
- [[Prakken_2006_FormalSystemsPersuasionDialogue]] — Same author's earlier review of formal persuasion dialogue systems; provides the speech act taxonomy (claim/why/since/concede/retract) and commitment store framework that connects to the structured argumentation discussed in this appreciation paper. The dialogue protocol design space complements the ASPIC+-based argumentation framework perspective taken here.

### Conceptual Links (not citation-based)
**Argumentation foundations:**
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] -- Cayrol's bipolar argumentation extends Dung's framework with support relations; Prakken & Horty's survey identifies the lack of support relations as a gap in Pollock's system, making bipolar frameworks a natural extension of the ideas discussed here
- [[Clark_2014_Micropublications]] -- Clark's micropublications model uses Toulmin-Verheij argumentation to structure scientific claims; Prakken & Horty's discussion of argumentation schemes and defeasible inference rules provides the theoretical grounding for Clark's claim-evidence-challenge structure
- [[Doyle_1979_TruthMaintenanceSystem]] -- Pollock's inference graphs and defeat status assignments are structurally related to Doyle's TMS dependency networks and belief revision; both systems face the same fundamental problem of maintaining consistent belief sets under new information
- [[deKleer_1986_AssumptionBasedTMS]] -- de Kleer's ATMS labels (environments under which conclusions hold) relate to Pollock's partial defeat status assignments; both track multiple simultaneous reasoning contexts, though from engineering vs epistemological perspectives
