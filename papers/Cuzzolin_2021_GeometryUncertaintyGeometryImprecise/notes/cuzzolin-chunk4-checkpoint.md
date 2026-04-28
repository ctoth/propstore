# Chunk 4 Checkpoint (2026-04-27)

## Page-offset map observed
- pdf-256 = printed p.235 (Ch.4 §4.10 tail). Offset PDF=BOOK+21.
- pdf-257 = printed p.237 (Ch.5 opens). Offset PDF=BOOK+20.
- pdf-258 = p.238, 259=239, 260=240, 261=241, 262=242, 263=243, 264=244, 265=245, 266=246, 267=247, 268=248, 269=249, 270=250.
- Working offset: book = pdf - 20 within Ch.5.

## Pages read so far (pdf-256 .. pdf-270 = book pp.235..250)
Chapter 5 sections covered:
- §5.1 Clustering: 5.1.1 ECM/BCM (p.239-240) variants RECM/CECM/SECM/CCM/MECM; 5.1.2 EVCLUS (p.240-241), Ek-NNclus Algorithm 11 (p.241), Belief K-modes Algorithm 12 (p.242); 5.1.3 Clustering belief functions / Schubert metaconflict eq.(5.1) (p.243).
- §5.2 Classification: 5.2.1 Generalised Bayesian classifier with lower/upper expected losses (p.244); 5.2.2 Evidential k-NN (p.245-246), Fig 5.2 (p.245), partial-supervised extension via discounting (p.246), other k-NN variants (p.246); 5.2.3 TBM model-based classifier (p.246-247) using GBT chain ballooning+conjunctive+conditioning+marginalisation; 5.2.4 SVM classification Liu-Zheng (p.247-248) with mass formulae for positive/negative cases; 5.2.5 Classification with partial training data (p.248) — Denoeux 1997, Côme et al. 2009, Vannoorenberghe-Smets credal EM, Tabassian; 5.2.6 Decision trees (p.249-250) — Eq.(5.2) Shannon entropy, Eq.(5.3) info gain, Belief decision trees Algorithm 13, Denoeux-Bjanger m_Θ formula.

## Output file state
NOT YET CREATED. Will create now with skeleton + content for pp.235-250 then append as I read more.

## Plan
- Read pdf-271..285 next (book pp.251..265 — neural-net classifiers, ensemble classification, ranking, regression).
- Then 286..305 (book pp.266..285 — estimation, optimisation, end of Ch.5; likely Ch.6 begins).
- Then 306..353 (book pp.286..333 — Ch.6 imprecise probability landscape — high-value).

## Lessons logged
- PDF-to-book offset is +20 in Ch.5 region (worker prompt says +25 but for this region it's +20). Use printed page numbers verbatim.
- Several algorithms numbered (Algorithm 11, 12, 13) — must capture inputs/outputs.

## Update after pdf-296..305 (book pp.276-285) — Ch.6 §6.1.7 - §6.5
- §6.1.7 BFs as coherent lower probabilities (Wang-Klir [1912]); natural extension ≤ Choquet integral (Prop 37); conceptual autonomy (Baroni-Vicig [94], Prop 38).
- §6.2 Capacities (Def 95-96, Prop 39 BFs are ∞-monotone, Möbius eq.6.6); Sugeno λ-measures eqs.6.7-6.8 with three regimes; Prop 40 probability intervals are 2-monotone (eq.6.9).
- §6.3 Probability intervals (Def 97 feasibility, eqs.6.10-6.11, Prop 41 minimal interval = (Bel,Pl), conditions for inverse).
- §6.4 Higher-order: Baron, Josang Dirichlet bijection, Gaifman HOP, Kyburg, Fung-Chong metaprobability with eq for p^2(p|D,Pr).
- §6.5 Fuzzy: Def 98 possibility, Prop 42 Pl=possibility iff consonant, Bel=necessity iff consonant; eq.6.13 BF on fuzzy sets via implication operator.

Pages remaining: pdf-306..353 = printed pp.286-(approx 333). Need to cover §6.5.2 finish + §6.6 logic frameworks (Saffiotti, Josang's subjective logic, Fagin-Halpern, probabilistic argumentation, default, Ruspini, modal logic, prob of provability), §6.7 rough sets, §6.8 p-boxes, §6.9 Spohn, §6.10 GTU, §6.11 Liu, §6.12 info-gap, §6.13 Vovk-Shafer, §6.14 other formalisms.

No blockers; pacing is good. Currently at ~50/98 pages read. Output file ~6800 words, will continue building.

## Update after pdf-306..325 (book pp.286-305) — Ch.6 §6.5.2 fuzzy ext through §6.9.1 Spohn epistemic
Captured into chapter-04 file:
- §6.5.2-6.5.4 fuzzy: Yen LP (eq.6.14), Wu Prop 43, Vague sets [669], intuitionistic [62], Zadeh's extension, Mahler FCDS, Lucas-Araabi, Aminravan IGIB, Def 100 fuzzy-valued belief structure.
- §6.6 Logic: Saffiotti BFL Defs 101-102; Josang subjective logic (consensus, recommendation); Fagin-Halpern axiomatisation [586]; Probabilistic argumentation systems Haenni-Lehmann ABEL; Default logic Wilson, Benferhat-Saffiotti-Smets ε-mass Def 103; Ruspini logical foundations Defs 104-105 + eq.6.15; Modal logic interpretation Resconi-Harmanec, Props 44-46, eq.6.16-6.17 SVA T-models; Probability of provability Pearl/Smets/Hajek; Other (incidence Def 106, Baldwin support logic, Provan, Penalty, Grosof, Cholvy, Benavoli, Narens, Bharadwaj CPR, Kroupa).
- §6.7 Rough sets Pawlak Defs/qualities, Props 47-48, modal logic S5 equivalence.
- §6.8 P-boxes Def 107, eq.6.18-6.20, Algorithm 14 Monte Carlo Alvarez, Generalised p-boxes Def 108, Fig 6.6 hierarchy.
- §6.9.1 Spohn Def 109, Prop 49.

Pages remaining: pdf-326..353 = printed pp.306-(approx 333). Need: §6.9.2 disbelief functions / α-cond, §6.10 GTU Zadeh, §6.11 Liu uncertainty theory, §6.12 info-gap, §6.13 Vovk-Shafer, §6.14 other formalisms.

Output file currently ~10000 words. Pace good.

## Update after pdf-271..275 (book pp.251-255)
- §5.2.7 Neural networks (p.251) — Denoeux 2000 [448] adaptive evidential k-NN as MLP with prototype hidden layer; RBF view [1436]; Fig.5.3 architecture; Binaghi neural fuzzy DS [155]; Fay et al. [593] hierarchical NN+belief ensembles with ramp normalisation; Loonis [1212] empirical comparison.
- §5.2.8 Other classification (p.252-254) — Bloch 1996 [171] (max bel, max pl, Wesley's average rule (Bel+Pl)/2 [1927]); Le Hégarat-Mascle [1106] unsupervised remote sensing; Modified DS / MDS Fixsen-Mahler [623,624] reduces to Bayes under independence; Fuzzy DS rule-based [156]; ICM Foucher [638] image MAP; Credal bagging François [641] aggregate via average m_B(A)=1/B Σ m_b(A); PDESCS Zhu-Basir [2127] Eq.(5.4) m({c_1,..,c_j}) = (s_j - s_{j+1})/s_1; Erkmen-Stephanou fractal [577]; Lefevre-Colot [1124,1117] attenuation factor; Vannoorenberghe [1846] minimisation of pignistic / lower expected loss; Perry-Stephanou [1421] divergence over aggregate BFs; Dempster-Chiu [427]; Trabelsi [1823,1824] rough sets; Fiche [610,609] α-stable feature distributions.
- §5.3 Ensemble classification (p.254): Xu-Krzyzak-Suen 1992 [1997] watershed paper. §5.3.1 Distance-based fusion. Fig.5.4 ensemble principle. Eq.(5.5) Xu's BPA from recognition rate $\epsilon^k_r$ and substitution rate $\epsilon^k_s$.
- Continuing onward — no blocker.

