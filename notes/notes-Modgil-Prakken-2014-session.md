# Session Notes: Modgil & Prakken 2014 Paper Processing

## Task
Process paper: Modgil, S. and Prakken, H. (2014). "The ASPIC+ framework for structured argumentation: a tutorial." Argument & Computation, 5(1), 31-62.
DOI: 10.1080/19462166.2013.869766

## Progress

### Step 1: Retrieval - DONE
- Deleted existing failed directory
- fetch_paper.py resolved metadata, created directory, but PDF was paywalled (fallback_needed: true)
- Used Chrome + sci-hub.st to retrieve PDF
- Downloaded from: https://sci-hub.st/storage/zero/3688/7e77875704c9d44eca57c327516ade7c/modgil2014.pdf
- PDF verified: 377KB, valid PDF-1.4, 34 pages
- Directory: papers/Modgil_2014_ASPICFrameworkStructuredArgumentation/
- Files: metadata.json, paper.pdf

### Step 2: Paper Reader - IN PROGRESS
- Converted to 34 page images
- Reading pages 0-11 so far

#### Paper Structure Observed:
- Pages 0-1: Cover page and copyright (Taylor & Francis, Lakehead University download)
- Page 2: Title page + abstract + Section 1 Introduction
  - ASPIC+ is a framework for structured argumentation (Dung 1995 style)
  - Based on two ideas: (1) conflicts between arguments are often resolved with preferences, (2) the process that reasons and the process that reasons about that process are the same
  - Premises only create a presumption in favour of their conclusion
- Page 3: Section 2 - ASPIC+ Design choices and overview
  - Example: John in Holland Park - witnesses, defeasible reasoning
  - Three ways to attack: undermine (attack premise), rebut (attack conclusion), undercut (attack inference step)
- Page 4: More on attack types, deductive vs defeasible inference
- Page 5: Section 3 - The framework defined: Special case with "ordinary" negation
  - Definition 3.1: Argumentation system AS = (L, R, n)
    - L = logical language with negation
    - R = Rs union Rd (strict and defeasible rules)
    - n = naming function for defeasible rules
  - Definition 3.2: Argumentation system is a triple AS = (L, R, n)
  - Definition 3.3: Knowledge base K = (Kn, Kp) - necessary and ordinary premises
- Page 6: Definition 3.4 (Consistency), argumentation systems, knowledge bases
  - Argumentation theory AT = AS + K
  - Arguments built from AT using inference rules chaining
- Page 7: Definition 3.5, 3.6 (Arguments)
  - Argument structure: Prem(A), Conc(A), Sub(A), DefRules(A), TopRule(A)
  - Four kinds: strict, defeasible, firm, plausible
  - Figure 1: argument tree diagram
  - Example 3.7: detailed knowledge base example with rules d1-d6, s1-s2
- Page 8: Definition 3.8 (Argument properties)
  - strict if DefRules(A) = empty set
  - defeasible if DefRules(A) != empty set
  - firm if Prem(A) subset Kn
  - plausible if Prem(A) intersect Kp != empty set
- Page 9: Section 3.3 Attack and defeat
  - Definition 3.10 (Attack): three types - undermining, rebutting, undercutting
  - Attack on ordinary premise, on defeasible inference step, on conclusion
  - Figure 2: argument attack diagram
- Page 10: Section 3.3.2 Defeat
  - Definition 3.12: successful rebuttal, undermining, and defeat
  - Ordering-based: attack succeeds as defeat based on preferences
  - Undercutting attacks always succeed regardless of preferences
- Page 11: Definition 3.14 (Structured argumentation framework)
  - A = smallest set of all finite arguments from KB in AS
  - Example 3.15: running example with arguments A1-A5, attacks

#### Pages 12-23 Content:
- Page 12: Section 3.4 Generating Dung-style abstract AFs
  - Definition 3.16 (Argumentation framework)
  - Justified extensions, credulous/sceptical justification
  - Example 3.17: grounded, preferred extensions
- Page 13: Section 3.5 More on argument orderings
  - Last-link and weakest-link orderings for comparing arguments
  - Definition 3.19 (Orderings on sets): Elitist and democratic set comparison
  - Definition 3.20 (Last defeasible rules)
- Page 14-15: Last link principle (Def 3.21), Weakest link principle (Def 3.23)
  - Examples 3.24, 3.25 comparing last-link vs weakest-link
  - Discussion of which is "better" - last-link gives better outcome when conflict is between two legal rules
  - Weakest-link seems better for empirical generalizations
- Page 16: Section 4 - Ways to use the framework
  - Section 4.1: Choosing strict rules, axioms, and defeasible rules
  - 4.1.1: Domain-specific strict inference rules
  - Example with marriage/bigamy domain
  - Closure under transposition important for consistency
- Page 17: Definition 4.3 - Closed under transposition
  - AT is closed under transposition iff for every strict rule, all transpositions are also strict rules
  - Section 4.1.2: Strict inference rules and axioms based on deductive logic
  - Two approaches: strict rules = all valid inferences of logic, or materialized approach
- Page 18: Section 4.1.3: Choosing defeasible inference rules
  - Discusses philosophical approaches to defeasible rules
  - Reiter's default logic, Pollock's inference scheme
  - Can choose domain-specific defeasible inference rules or general logical patterns
- Page 19: Section 4.1.4: Choosing defeasible modus ponens
  - Adding defeasible rules for conditionals in object language
  - Two approaches: domain-specific vs classical logic-based
- Page 20: Section 4.2: Satisfying rationality postulates
  - Sub-argument closure, closure under strict rules, consistency
  - Direct/indirect consistency requirements
  - These constrain how ASPIC+ should be instantiated
- Page 21: Example 4.4 revisiting Example 3.7 showing closure issues
  - Importance of transposition and well-formed orderings
- Page 22: Section 4.3: Using ASPIC+ to model argument schemes
  - Pollock's defeasible reasons and Walton's argument schemes
  - Position-to-know scheme with premises, perception, memory
- Page 23: Detailed Walton-style argument scheme example
  - Knowledge base for robbery/witness example with position-to-know scheme
  - Arguments formalized with scheme predicates

#### Pages 24-33 Content:
- Pages 24-25: Section 4.4 Instantiation with/without defeasible rules
  - Tweety example formalized both ways
- Pages 26-27: More on Tweety, argument schemes in practice
- Page 28: Section 4.6 Representing facts, Section 4.7 Summary of instantiation choices
- Pages 29-30: Section 5 - Generalizing the framework with contrariness function
  - Definition 5.1: contrariness function, contraries vs contradictories
  - Contrary attacks always succeed (like undercutting)
  - Can model ABA within generalized ASPIC+
- Page 31: Section 6 - Relationship to other approaches (Dung, ABA, Besnard/Hunter, Carneades, Pollock)
- Page 32: Section 6 continued, Notes section
- Page 33: References (full bibliography)

### Step 2: Paper Reader - DONE
- notes.md written (comprehensive, all definitions, all sections)
- description.md written
- abstract.md - TODO (next)
- citations.md - TODO (next)

### Step 3: Clean Up - N/A (source was URL, not local file)

### Step 4: Extract Claims - TODO (after reader completes)

### Step 5: Report - TODO
- Write to ./reports/lead-Modgil-Prakken-2014-report.md
