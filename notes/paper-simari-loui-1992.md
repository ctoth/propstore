# Paper Processing: Simari & Loui 1992

## Date: 2026-03-24

## GOAL
Process Simari & Loui 1992 "A Mathematical Treatment of Defeasible Reasoning and its Implementation" for the propstore paper collection.

## STATUS
- Retrieval: DONE (PDF downloaded via DOI 10.1016/0004-3702(92)90069-A, 1.1MB)
- Page images: DONE (52 pages, page-000 through page-051)
- Reading: DONE (all 52 pages read)
- Notes writing: DONE (notes.md, abstract.md, description.md, citations.md, metadata.json updated)
- Claim extraction: NEXT
- Report: NEXT

## FILES
- `papers/Simari_1992_MathematicalTreatmentDefeasibleReasoning/paper.pdf` — source PDF
- `papers/Simari_1992_MathematicalTreatmentDefeasibleReasoning/metadata.json` — from fetch script
- `papers/Simari_1992_MathematicalTreatmentDefeasibleReasoning/pngs/` — 52 page images

## KEY OBSERVATIONS SO FAR

### Metadata
- Title: "A Mathematical Treatment of Defeasible Reasoning and its Implementation"
- Authors: Guillermo R. Simari, Ronald P. Loui
- Tech report: WUCS-89-12, September 1989, Washington University in St. Louis
- Published: Artificial Intelligence journal, 1992
- DOI: 10.1016/0004-3702(92)90069-A

### Paper Structure (pages read so far)
- p.0-1: Repository cover page + complete abstract
- p.2: Inner title page (WUCS-89-12, submitted to AI Journal Jan 1990)
- p.3: Abstract page (same abstract text)
- p.4-5: Section 1 - Introduction. Combines Poole's specificity + Pollock's warrant theory. Arguments are prima facie proofs using non-monotonic relations.
- p.5-6: Knowledge = (K, Delta) where K = wffs (context), Delta = defeasible rules. K partitioned into necessary (K_N) and contingent (K_C). Defeasible rules: alpha >- beta.
- p.6: Defeasible consequence relation |~ defined. A is defeasible consequence of Gamma if derivation sequence B1...Bm exists where A=Bm and each Bi is axiom, in Gamma, or follows by modus ponens/instantiation.
- p.7: Transition to needing specificity criterion for preferring conclusions
- p.8: Section 2.1 - Arguments. Definition 2.1 (Preliminary): argument structure <T,h>_K where T subset of Delta^i, K union T |~ h, K union T not |~ bottom.
- p.9: Definition 2.2 (Revised): adds minimality condition (no T' subset T with K union T' |~ h). Subargument definition 2.3. Examples.
- p.10: Definition 2.4-2.5: An(T) = antecedents, Co(T) = consequents, Lit(<T,h>) = An(T) union Co(T) minus {h}
- p.11: Section 2.2 - Specificity. Definition 2.6: <T1,h1> >_spec <T2,h2> (strictly more specific) with activation conditions
- p.12: Definition 2.7 (equi-specific), Definition 2.8 (at least as specific). Examples 2.6, 2.7 showing specificity comparisons.
- p.13: Lemma 2.1 (subarguments are at least as specific), Lemma 2.2 (equi-specificity is equivalence relation), Lemma 2.3 (partial order on AStruc/~)
- p.14: Lemma 2.4 (reduced search space for specificity - can check via antecedents only)
- p.15: Lemma 2.5 (covering lemma - if T1 >= T2 and T2 has subargument <R,p>, then T1 contains <S,p> with S >= R)
- p.16: Section 3 - An Algebra of Arguments. Concordance (Definition 3.1): two arguments concordant if K union T1 union T2 not |~ bottom. Proposition 3.1: subarguments are pairwise concordant.

## NEXT
- Continue reading pages 20-51
- Write notes.md, abstract.md, description.md, citations.md
- Extract claims
- Write report
