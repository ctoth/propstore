# Citations

## Reference List

[1] G. Antoniou, *Nonmonotonic Reasoning*, MIT Press, Cambridge, MA, 1997.

[2] G. Antoniou, D. Billington, M.J. Maher, "Normal forms for defeasible logic", in: Proceedings of the 1998 Joint International Conference and Symposium on Logic Programming, MIT Press, Cambridge, MA, 1998, pp. 160-174.

[3] D. Billington, "Defeasible logic is stable", *Journal of Logic and Computation* 3 (1993) 370-400.

[4] M.A. Covington, D. Nute, A. Vellino, *Prolog Programming in Depth*, Prentice-Hall, Englewood Cliffs, NJ, 1997.

[5] Y. Dimopoulos, A. Kakas, "Logic programming without negation as failure", in: Proceedings of the Fifth International Symposium on Logic Programming, MIT Press, Cambridge, MA, 1995, pp. 369-384.

[6] B.N. Grosof, "Prioritized conflict handling for logic programs", in: J. Maluszynski (Ed.), Proceedings of the International Logic Programming Symposium, MIT Press, Cambridge, MA, 1997, pp. 197-211.

[7] A.C. Kakas, P. Mancarella, P.M. Dung, "The acceptability semantics for logic programs", in: Proceedings of the 11th International Conference on Logic Programming (ICLP '94), MIT Press, Cambridge, MA, 1994, pp. 504-519.

[8] M.J. Maher, G. Antoniou, D. Billington, "A study of provability in defeasible logic", in: Proceedings of the 11th Australian Joint Conference on Artificial Intelligence, LNAI 1502, Springer, Berlin, 1998, pp. 215-226.

[9] D. Nute, "Defeasible reasoning", in: Proceedings of the 20th Hawaii International Conference on Systems Science, IEEE Press, New York, 1987, pp. 470-477.

[10] D. Nute, "Defeasible logic", in: D.M. Gabbay, C.J. Hogger, J.A. Robinson (Eds.), *Handbook of Logic in Artificial Intelligence and Logic Programming*, vol. 3, Oxford University Press, USA, 1994, pp. 353-395.

[11] D. Touretzky, J.F. Horty, R.H. Thomason, "A clash of intuitions: The current state of nonmonotonic multiple inheritance systems", in: Proceedings of the IJCAI-87, Morgan Kaufmann, Los Altos, CA, 1987, pp. 476-482.

[12] X. Wang, J. You, L. Yuan, "Nonmonotonic reasoning by monotonic inferences with priority constraints", in: J. Dix, P. Pereira, T. Przymusinski (Eds.), *Nonmonotonic Extensions of Logic Programming*, LNAI 1216, Springer, Berlin, 1997, pp. 91-109.

[13] X. Wang, J. You, L. Yuan, "Logic programming without default negation revisited", in: Proceedings of the IEEE International Conference on Intelligent Processing Systems, IEEE, 1997, pp. 1169-1174.

## Key Citations for Follow-up

- **[5] Dimopoulos & Kakas 1995 — Logic programming without negation as failure.** The LPwNF paper that this whole comparison rests on. Required reading to understand the type-A / type-B derivation structure and the argumentation-theoretic semantics that motivates the asymmetric `≮` / `>` admissibility conditions.

- **[2] Antoniou, Billington, Maher 1998 — Normal forms for defeasible logic.** Supplies Lemma 4.1 (`+∂q ⇒ -∂~q` for theories without strict rules) used in the main theorem. The structural-properties companion to this paper.

- **[8] Maher, Antoniou, Billington 1998 — A study of provability in defeasible logic.** Cited as the deeper analysis of the inference relation, representation results, and semantics. Together with [1] and [2] this is the propstore-relevant DL canon.

- **[6] Grosof 1997 — Prioritized conflict handling for logic programs (Courteous Logic Programs).** Captured by DL via Theorem 5.1 / `df(C)`. Important when integrating older argumentation-pipeline KBs that use CLP-style stratification.

- **[12, 13] Wang, You, Yuan 1997 — Priority logic.** Boundary marker: priority logic propagates ambiguity, DL does not. Useful for understanding which extension-based formalisms are *not* in the same school as DL/LPwNF/CLP.
