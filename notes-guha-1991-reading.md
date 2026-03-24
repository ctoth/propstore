# Reading: Guha 1991 - Contexts: A Formalization and Some Applications

## GOAL
Process Guha's 1991 PhD thesis on formalizing contexts for propstore paper-process pipeline.

## DONE
- Retrieved PDF from UNAM mirror (147 pages, 695KB)
- Created metadata.json
- Converted to 147 page images
- Read pages 0-19 (Chapter 1 Introduction + start of Chapter 2)

## KEY FINDINGS SO FAR

### Structure
- Title page says "February 10, 1995" (revised version of 1991 thesis)
- Chapter 1: Introduction (pp.3-15)
- Chapter 2: The Logic of Contexts and Lifting (starts p.17)
- Chapter 3: Uses of contexts (Cyc system examples)
- Chapter 4: Natural language understanding
- Appendix A: Cyc application script

### Core Concepts (Chapter 1)
- KB = set of expressions (sentences) in a vocabulary, each conveying truth about domain (p.3)
- Problem: KB sentences assumed decontextualized but actually context-dependent (p.3)
- Key insight: vocabulary choice itself makes assumptions (p.5-6)
- Solution: introduce `ist(context, formula)` - "is true in context" (p.7)
- Contexts are first-class objects, not just labels (p.8)
- Context = partial description of context dependencies of sentences (p.8)
- Entering/Exiting contexts serve two purposes: problem solving focus + interaction context (p.10)
- Lifting = transferring information between contexts (p.9-10)
- Relative decontextualization = saying a domain has been Partially/Relatively Decontextualized (p.9)

### Desired Logical Properties (Chapter 2, p.17-19)
1. Contexts are first-class objects, ist formulas are first-class formulas
2. Different contexts can use different languages (vocabulary depends on context)
3. FOL with extensions should suffice for each context's internal theory
4. Symbols should be referentially opaque in ist (related to modalities)
5. Nested contexts / nesting of ist: ist(c_i, ist(c_j, alpha)) allowed
6. Lifting rules transfer facts between contexts

### Key Formulas
- `ist(c, F)` - formula F is true in context c (p.7)
- `ist(c0, ist(C1, (mass(m1)=mass(m2) ∧ (vv(x)>vv(y))))) ⇒ ist(C2, ((mom(x)>mom(y)) ∧ (en(x)>en(y))))` - lifting rule example (p.19)

## FILES
- papers/Guha_1991_ContextsFormalization/paper.pdf - source
- papers/Guha_1991_ContextsFormalization/metadata.json - metadata
- papers/Guha_1991_ContextsFormalization/pngs/ - 147 page images
- papers/Guha_1991_ContextsFormalization/chunks/ - empty, to be filled

## SESSION 2 STATUS
- Discovered two directories exist: `Guha_1991_ContextsFormalization` (prior session, partial) and `Guha_1991_ContextsFormalizationApplications` (current session)
- Both have paper.pdf and pngs/ converted (147 pages each)
- Neither has notes.md yet
- Using `ContextsFormalizationApplications` directory (full title name) as canonical
- Prior session read pages 0-19 and captured notes above
- Current session re-read pages 0-9 and confirmed same content
- Now continuing from page 10 onward

### Chapter 2: The Logic of Contexts and Lifting (p.17-29+)

**2.1.1 Desired Logical Properties** (p.17-19)
1. Contexts are first-class objects, ist formulas are first-class formulas
2. Different contexts can use different languages
3. FOL with extensions should suffice for each context's internal theory
4. Symbols referentially opaque in ist (related to modalities)
5. Nested ist: `ist(c_i, ist(c_j, alpha))` allowed
6. Lifting rules transfer facts between contexts

**2.1.2 Syntax and Semantics** (p.20-24)
- "Total Vocabulary" = set of constant symbols
- Base parameters: V, =, OR, ist, and variable symbols
- Grammatical formation rules for formulas (i-viii)
- Language = subset of total vocabulary with designated constants (predicate/function/individual) and fixed arities
- Context Structure CS: assigns to each context C:
  - A Language L(C)
  - A set of structures CM(C) (models of that context)
- Formula F meaningful in context C iff every symbol not within an ist is part of L(C) and used appropriately
- **Satisfaction** (p.22): `<U, CS, S>` satisfies F in C iff U in CM(C), F meaningful in C under CS, and truth recursion of FOL holds
- **ist satisfaction**: `ist(ck, P)` satisfied in C by `<U, CS, S>` iff Ck is a context AND for every U_j in CM(Ck), for every variable in P assigned to element of D_j, P is satisfied in Ck by `<U_j, CS, S>`
- **Entailment** (p.23): F entails G in C iff every tuple satisfying F also satisfies G
- **Defined predicates**: `presentIn(c A)` iff `forall z (= A z) => ist(c (exists y z = y))`
- **corefer(C1, A, C2, B)** iff `forall z ist(C1 (= A z)) <=> ist(C2 (= B z))`
- **value(c, A) = z** iff `forall x (= z A) => ist(c (= B x))`
- CM defines directed acyclic graphs of contexts: `forall ci: not presentIn(ci, ci)` (p.23)
- **Nonmonotonicity** (p.23): uses circumscription (pointwise, prioritized). Predicates starting with 'ab' minimized. Cyc implementation uses Argumentation Based Default Reasoning.
- **Non-Axioms** (p.24): `ist(c, p v q) => ist(c,p) v ist(c,q)` is NOT valid. `not ist(c,p) => ist(c, not p)` is NOT valid. But if theory of c is complete, both become valid.
- Barkan formula `ist(c (forall x p(x))) <=> (forall x ist(c p(x)))` does NOT hold (p.24)
- Assumption for rest of thesis: domain of outer context larger than inner contexts

**2.1.3 Proof Theory** (p.25-27)
- Proof = finite sequence of statements with context sequences
- Each line has associated context sequence [C1, C2, ..., Cn]
- Lines are: formulas, Enter ci, or Exit
- Enter pushes context onto sequence, Exit pops
- Inference rules (a)-(l):
  - (a) All FOL rules for non-ist formulas
  - (b) Modus ponens, modus tolens, propositional rules
  - (c) Logical connective combination within contexts
  - (d) Modus ponens from outside: `ist(Ci, a=>g)` + `ist(Ci, a)` / `ist(Ci, g)`
  - (e) Conjunction splitting: `ist(Ci, a ^ g)` / `ist(Ci, a) ^ ist(Ci, g)`
  - (f) Consistency: `ist(ci, a)` / `not ist(ci, not a)`
  - (g) Skolemization
  - (h) Modified Universal Instantiation (since ist is referentially opaque, standard UI doesn't hold - must use value/corefer)
  - (i) Universal export from context: `ist(c (forall x g(x)))` / `forall x presentIn(c,x) => ist(c g(x))`
  - (j) Implication export: `ist(c p=>q)` / `ist(c p) => ist(c q)`
  - (k) Universal import to context (with domain assumption): `forall x presentIn(c,x) => ist(c g(x))` / `ist(c (forall x g(x)))`
  - (l) Implication import with domain assumption

**2.2 Example Axioms** (p.28-29)
- Standard syntactically characterizable differences between contexts:
  1. Dropping argument to predicate: `forall x ist(C1 Tall(x)) <=> ist(C2 Tall(x Person))`
  2. Dropping argument to function: cost unary in C1, binary in C2
  3. Domain assumption: fixtures assumed installed in C1 but not C2
  4. Fixing time: `fix-time(ci, ti)` = snapshot of context at time ti
  5. Indexicals: `corefer(C1, Now, C2, T1)` for temporal lifting

**2.3 Sample Proofs** (p.29)
- Proof involving lifting axiom for Tall predicate
- Shows that standard UI doesn't work across contexts - need corefer/value

### Pages 30-49: Rest of Ch2 + Start of Ch3

**2.3-2.5 Sample Proofs and Lifting Examples** (p.29-35)
- Detailed Enter/Exit proof mechanics with Tall(Fred) *(p.29-30)*
- Domain restriction proof with fixtures *(p.30-31)*
- Basketball/Tall lifting example using DCR *(p.35)*

**2.6 Model Theoretic Account of Lifting** (p.36-38)
- Context dependence of utterance: each context has associated theory *(p.36)*
- Relative decontextualization formalized via model restriction *(p.37-38)*

**2.7 Discussion** (p.39-40)
- Containment vs biconditional; containment is stronger *(p.39-40)*
- Default biconditionals with circumscription needed *(p.40)*

**Chapter 3: Applications of Contexts** (p.41-49)
- 6 different uses of contexts enumerated *(p.41-46)*
- Lifting Rules: DCR-T, DCR-P, DCR-F, compositional rule CR *(p.47-48)*
- Problem solving: Lift-and-Solve vs Shift-and-Solve *(p.49)*

### Pages 50-59: Ch3 continued (Lift and Solve, Car Selection, Examples)

**3.3.1 Lift and Solve** (p.50-52)
- Lift assertions from other contexts into PSC, then use conventional solver *(p.50)*
- Access Module: responsible for indexing and accessing expressions from KB *(p.50)*
- Inferencing Module: uses expressions given by access module to derive conclusions *(p.50)*
- Lifting module determines what to lift, and handles lifting *(p.50)*
- Two factors for determining whether assertion P should be imported from c_i to c_j *(p.51)*:
  - **Relevance**: is info in c_i relevant at all to goals of c_j?
  - **Appropriateness**: is theory in c_i accurate enough for goals of c_j?
- Policy of "risky" lifting followed - system does consistency checking for recovery *(p.52)*
- **Ambiguity/conflicts in lifting** (p.53): three cases where system can lift P from c_i OR G from c_j but not both

**3.4 Preliminaries to Examples** (p.54)
- Cyc KB not geared toward particular applications *(p.54)*

**3.4.1 Car Selection Program (CSP)** (p.54-55)
- Accepts info about user and makes car suggestions *(p.54)*
- Uses contexts for common-sense representation and reasoning *(p.54)*
- Creates Problem Solving Context (CSPSC) for user+car *(p.55)*

**3.5 Examples of Uses of Contexts** (p.55-56)
- 21 examples listed covering: time, temporal qualifications, hypothetical reasoning, scope, granularity, database integration *(p.55-56)*

**3.6 Example 1: Fixing time implicitly to "Now"** (p.56-59)
- Temporal reasoning with implicit "now" *(p.56)*
- HumanKinshipMt: rules about human relations *(p.57)*
- Temporal qualification: `holds(t, spouse(x,y))` *(p.57)*
- Structuring representation: static vs dynamic parts *(p.58)*
- Complications: marriage changes status, affects living arrangements *(p.58-59)*
- Temporal qualifications of contexts: blanket temporal scopes *(p.59)*

## NEXT
- Continue reading pages 060-099 (rest of chunk 2)
- Then chunk 3 (100-146)
- Write chunk 2 notes, chunk 3 notes
- Synthesize into notes.md
