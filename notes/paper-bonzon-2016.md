# Paper Processing: Bonzon et al. 2016

## 2026-03-24

**GOAL:** Retrieve and process "A Comparative Study of Ranking-Based Semantics for Abstract Argumentation" by Bonzon, Delobelle, Konieczny & Maudet (2016).

**STATUS:** All 8 pages read. Writing output files.

**PAPER SUMMARY:**
- Compares 5 ranking-based semantics for abstract argumentation: Categoriser (Cat), Discussion-based (Dbs), Burden-based (Bbs), Matt & Toni (M&T), and Tuples* (Tup*)
- Defines 16 properties for ranking-based semantics (Abstraction, Independence, Void Precedence, Self-Contradiction, Cardinality Precedence, Quality Precedence, etc.)
- Key formal framework: ranking-based semantics = function sigma mapping AF to a ranking (preorder) on arguments
- Introduces Social Abstract Argumentation Frameworks (SAFs) to give formal semantics to some properties
- Creates comprehensive Table 2 showing which properties each semantics satisfies
- Key finding: no single semantics satisfies all properties; different semantics exhibit fundamentally different behaviors

**KEY DEFINITIONS:**
- Argumentation framework: F = (A, R) where A = set of arguments, R = attack relation
- Ranking-based semantics: sigma maps F to a preorder on A (ranking from most to least acceptable)
- Defense branch: path a1 R a2 R ... R a_2n+1 where a1 is the root
- Attack branch: path a1 R a2 R ... R a_2n where a1 is the root
- Categoriser function (Besnard & Hunter 2001): Cat(a) = 1 if no attackers, else 1/(1 + sum of Cat(attackers))
- Discussion-based: counts all defenders/attackers in non-attacked sub-branches
- Burden-based: iterative Burden_i computation converging to Burden_inf
- M&T: game-theoretic, two-person zero-sum strategic game computing argument strength
- Tuples*: lexicographic ordering of sorted attack/defense tuples

**PROPERTIES DEFINED (16 total):**
Abstraction, Independence, Void Precedence, Self-Contradiction, Cardinality Precedence, Quality Precedence, Copy, Non-attacked Equivalence, Increase of Attack, Strict Counter-transitivity, Addition of Defense Branch, Addition of Attack Branch, Increase of Attack Branch, Increase of Defense Branch, DDP (Distributed Defense Precedence), Counter-transitivity

**TABLE 2 RESULTS (which semantics satisfy which properties):**
- Cat: Abs, VP+, DP, CT, SCT, CP, DDP, TAB, TDB, +AB, Ext, Ind, Null
- Dbs: Abs, VP+, CT, SCT, CP, DDP, TAB, TDB, +AB, Ext, Ind, Null
- Bbs: Abs, VP, DP, CT, DDP, TAB, +DB, +AB, Ext, Ind, Null
- M&T: Abs, VP+, DP, SCT, TAB, TDB, +AB, Ext, Ind, Null
- Tup*: very recently proposed, most properties

**KEY OBSERVATIONS:**
- Void Precedence (VP) comes in two forms: basic VP and VP+ (Abs, In satisfy VP+ but Bbs only satisfies VP)
- No semantics satisfies all properties simultaneously
- Cat and Dbs often return same result but differ fundamentally: Dbs produces Strict CT but not DP
- Properties form natural clusters that separate semantics families
- Counter-Transitivity and Distributed Defense Precedence are distinguishing properties

**DONE:**
- Fetched paper from arXiv (1602.01059), 153KB PDF, 8 pages
- Converted to page images (page-000 through page-007)
- Read all 8 pages
- Wrote notes.md, description.md, abstract.md, citations.md

**CROSS-REFERENCES IDENTIFIED:**
- Cites Dung 1995 (in collection)
- Cites Baroni & Giacomin 2007 (in collection as Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation)
- Cites Cayrol & Lagasquie-Schiex 2005 (in collection as Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation)
- Cites Gabbay 2012 (in collection as Gabbay_2012_EquationalApproachArgumentationNetworks)
- Cites Leite & Martins 2011 (mentioned in SAF definition)
- Cites Amgoud & Ben-Naim 2013 (Amgoud_2011 in collection is different paper)
- Cites Besnard & Hunter 2001 (not in collection)
- Cites Matt & Toni 2008 (not in collection)
- Cites Pu et al. 2014 (not in collection)

**NEXT:** Run reconcile, update index.md, extract claims, write report
