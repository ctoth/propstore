# Citations

## Reference List

1. François Bancilhon and Nicolas Spyratos. Update semantics of relational views. *ACM Transactions on Database Systems*, 6(4):557-575, December 1981.

2. Umeshwar Dayal and Philip A. Bernstein. On the correct translation of update operations on relational views. *TODS*, 7(3):381-416, September 1982.

3. J. Nathan Foster, Michael B. Greenwald, Christian Kirkegaard, Benjamin C. Pierce, and Alan Schmitt. Exploiting schemas in data synchronization. In *Database Programming Languages (DBPL)*, August 2005.

4. J. Nathan Foster, Michael B. Greenwald, Jonathan T. Moore, Benjamin C. Pierce, and Alan Schmitt. Combinators for bi-directional tree transformations: A linguistic approach to the view update problem. In *ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages (POPL)*, Long Beach, California, pages 233-246, 2005.

5. G. Gottlob, P. Paolini, and R. Zicari. Properties and update semantics of consistent views. *ACM Transactions on Database Systems (TODS)*, 13(4):486-524, 1988.

6. Stephanie J. Hegner. An order-based theory of updates for closed database views. *Annals of Mathematics and Artificial Intelligence*, 40:63-125, 2004.

7. Soichiro Hidaka, Zhenjiang Hu, Hiroyuki Kato, and Keisuke Nakano. Algorithm for bidirectional transformations on the SXP universe (working draft). [implementation context — exact reference text varied across drafts of this paper].

8. Arthur M. Keller. Algorithms for translating view updates to database updates for views involving selections, projections, and joins. In *ACM Symposium on Principles of Database Systems (PODS)*, Portland, Oregon, 1985.

9. Arthur M. Keller. Comments on Bancilhon and Spyratos's "Update semantics and relational views". *ACM Transactions on Database Systems (TODS)*, 12(3):521-523, 1987.

10. Jens Lechtenbörger. The impact of the constant complement approach towards view updating. In *ACM SIGACT-SIGMOD-SIGART Symposium on Principles of Database Systems (PODS)*, Madison, Wisconsin, pages 49-55. ACM, June 9-12 2003.

> Note: The reference list extends across the bottom of p.352. Items above are reconstructed from the visible reference column. Refs 7 and any additional entries past the visible page may need re-verification from a higher-resolution scan if exact bibliographic detail is required.

## Key Citations for Follow-up

1. **Foster, Greenwald, Moore, Pierce, Schmitt — POPL 2005** (Ref 4): the predecessor "tree lens" paper. Establishes the well-behaved/very-well-behaved lens laws (GetPut, PutGet, PutPut) that this paper inherits. Mandatory reading to understand the bi-directional law system at full generality. Already prominent in propstore's migration-framework batch.

2. **Bancilhon, Spyratos — TODS 1981** (Ref 1): the view-complement formulation of the view-update problem. The relational-lens paper positions itself explicitly as an alternative to this approach. Useful for propstore as background on why the lens framework chose syntactic combinators over complement-based update determination.

3. **Dayal, Bernstein — TODS 1982** (Ref 2): the "correct translation" formulation. Together with Bancilhon-Spyratos, defines the prior-art landscape that lenses replace.

4. **Hegner — AMAI 2004** (Ref 6): order-based theory of updates for closed views. Closer in structure to lens combinators than Bancilhon-Spyratos and a useful comparison point.

5. **Keller — PODS 1985** (Ref 8): translating view updates for views involving σ, π, and ⋈ — exactly the same primitives this paper handles. The lens framework's position relative to Keller's algorithmic approach is a natural angle for further reading on migration determinacy.
