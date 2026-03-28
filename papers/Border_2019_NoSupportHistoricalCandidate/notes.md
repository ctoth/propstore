---
title: "No Support for Historical Candidate Gene or Candidate Gene-by-Interaction Hypotheses for Major Depression Across Multiple Large Samples"
authors: "Richard Border, Emma C. Johnson, Luke M. Evans, Andrew Smolen, Noah Berley, Patrick F. Sullivan, Matthew C. Keller"
year: 2019
venue: "American Journal of Psychiatry"
doi_url: "https://doi.org/10.1176/appi.ajp.2018.18070881"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-03-28T20:37:00Z"
---
# No Support for Historical Candidate Gene or Candidate Gene-by-Interaction Hypotheses for Major Depression Across Multiple Large Samples

## One-Sentence Summary
A large-scale preregistered replication study across samples of up to 443,264 individuals finds no evidence for any of the 18 most-studied candidate gene associations or gene-by-environment interactions for major depression, arguing that the prior candidate gene literature consists largely of false positives.

## Problem Addressed
Despite decades of research on candidate genes for depression (e.g., 5-HTTLPR/SLC6A4, BDNF, COMT, DRD4, MAOA, etc.), the validity of reported associations remained highly controversial. Hundreds of studies reported large genetic effects in small samples, but genome-wide association studies (GWAS) consistently failed to find these genes among top hits. This paper directly tests whether any of 18 historically prominent candidate genes show reproducible associations with depression in very large samples. *(p.1)*

## Key Contributions
- Empirically identified 18 candidate genes studied 10+ times for depression and tested them across multiple large population-based and case-control samples (N = 62,138 to 443,264) *(p.1)*
- Conducted preregistered analyses of polymorphism main effects, polymorphism-by-environment interactions, and gene-level effects across multiple depression phenotypes and environmental moderators *(p.1)*
- Found no clear evidence for any candidate gene polymorphism associations or GxE effects *(p.1)*
- Demonstrated that depression candidate genes as a set are no more associated with depression than non-candidate genes *(p.1)*
- Showed that phenotypic measurement error is unlikely to account for the null findings *(p.1)*
- Concluded that the large number of reported associations in prior literature are likely false positives *(p.1)*

## Study Design
- **Type:** Preregistered multi-sample replication study (observational, cross-sectional and longitudinal cohorts)
- **Population:** UK Biobank (N=502,682 total; subsamples vary by phenotype from ~62,138 to ~443,264); PGC GWAS data (N=443,264 for lifetime depression); also PGC case-control for subset analyses *(p.3-5)*
- **Intervention(s):** N/A — observational genetics study
- **Comparator(s):** Non-candidate genes as a comparison set; genome-wide significant loci from PGC GWAS as positive controls *(p.6)*
- **Primary endpoint(s):** Association between 18 candidate gene polymorphisms and multiple depression phenotypes *(p.4)*
- **Secondary endpoint(s):** Gene-by-environment interaction effects; gene-level association tests; replication of top PGC GWAS loci *(p.5-6)*
- **Follow-up:** Cross-sectional assessment in UK Biobank; PGC meta-analysis results *(p.5)*

## Methodology
The authors used the Biopyction bioinformatics package to identify 18 candidate genes studied 10+ times in depression literature. For each gene, they identified single polymorphisms comprising a large proportion of study foci (16 of 18 genes). Using UK Biobank data genotyped on the Affymetrix UK BiLEVE and UK Biobank Axiom arrays and imputed to the Haplotype Reference Consortium, they tested: (1) polymorphism main effects via generalized linear models controlling for age, sex, assessment center, genotyping batch, and 10 ancestry principal components; (2) polymorphism-by-environment interactions with multiple moderators; (3) gene-level tests using gene-wise and gene-set analyses via MAGMA. They also used PGC GWAS summary statistics for replication. All analyses were preregistered. *(p.3-5)*

## Key Equations / Statistical Models

Association models used generalized linear model framework (link functions in Table S4.1 of supplement):

For binary outcomes (e.g., lifetime depression diagnosis):
$$
\text{logit}(P(Y=1)) = \beta_0 + \beta_1 X_{\text{SNP}} + \boldsymbol{\beta}_c \mathbf{C}
$$
Where: Y = depression phenotype, X_SNP = candidate gene polymorphism dosage, C = covariates (age, sex, assessment center, genotyping batch, 10 ancestry PCs)
*(p.5)*

For continuous outcomes (e.g., current depression severity):
$$
Y = \beta_0 + \beta_1 X_{\text{SNP}} + \boldsymbol{\beta}_c \mathbf{C} + \epsilon
$$
*(p.5)*

For interaction models:
$$
Y = \beta_0 + \beta_1 X_{\text{SNP}} + \beta_2 E + \beta_3 (X_{\text{SNP}} \times E) + \boldsymbol{\beta}_c \mathbf{C} + \epsilon
$$
Where: E = environmental moderator (childhood maltreatment, SES adversity, stressful life events, etc.)
*(p.5)*

Gene-level analyses used MAGMA default settings (mean chi-square and top chi-square statistics, log-transformed sample size as covariate for competitive gene-set tests). *(p.5)*

Bonferroni-corrected significance threshold:
$$
\alpha_{\text{corrected}} = \frac{0.05}{18 \times 2.78 \times 10^5} \approx 9.99 \times 10^{-9}
$$
Where: 18 = number of candidate genes, 2.78 × 10^5 = estimated number of polymorphism-wise statistical tests across all GWAS outcomes
*(p.6)*

A liberal significance threshold was also used:
$$
\alpha_{\text{liberal}} = \frac{0.05}{5 \times 10^{-4}} \text{ (unadjusted in GWAS)} \text{ applied to candidate gene analyses}
$$
Actual threshold used: p < 5.0 × 10^-4 (unadjusted) *(p.6)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| UK Biobank total sample | N | — | 502,682 | — | 5 | Population sample, European ancestry |
| UK Biobank lifetime depression cases | — | — | 135,458 | — | 4 | Binary lifetime diagnosis |
| UK Biobank current depression severity N | — | — | 10,455 | — | 4 | Continuous severity score |
| PGC GWAS lifetime depression N | — | — | 443,264 | — | 5 | Summary statistics, incl. 120,201 cases |
| PGC case-control N | — | — | 323,063 | — | 5 | For controls subset |
| Number of candidate genes | — | — | 18 | — | 3 | Identified via Biopyction |
| Bonferroni threshold | α | — | ~10^-8 | — | 6 | 0.05/(18 × 2.78×10^5) |
| Liberal significance threshold | — | — | 5×10^-4 | — | 6 | Unadjusted in GWAS scan |
| Ancestry principal components | — | — | 10 | — | 5 | Included as covariates |
| Minimum studies per candidate gene | — | — | 10 | — | 1 | Inclusion criterion |
| Number of depression phenotypes | — | — | 8+ | — | 4 | See Table 1 |
| Number of environmental moderators | — | — | 5 | — | 4 | Childhood maltreatment, SES, trauma, etc. |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Candidate gene main effects (all 18 genes) | β | ~0 | varies | all >0.05 after correction | UK Biobank, all phenotypes | 6 |
| DRD2 main effect on lifetime depression | OR | significant pre-correction | — | significant at liberal threshold only | UK Biobank | 6 |
| COMT rs4680 on current depression | β | -0.017 | — | 0.007 | UK Biobank, only effect surviving liberal threshold for main effects | 7 |
| HTR2A rs6313 on estimated lifetime depression | β | 0.402 | — | — | Not significant | 7 |
| 5-HTTLPR on lifetime depression | β | ~0 | — | not significant | Multiple phenotypes | 7 |
| Gene-level effects (MAGMA) | p | all non-significant | — | >0.05 corrected | UK Biobank | 8 |
| Candidate genes vs non-candidate genes | comparison | no difference | — | — | UK Biobank | 6 |
| Top 16 PGC GWAS loci replication | — | mostly null | — | — | UK Biobank independent sample | 6 |
| PCLO (PGC locus) | p | significant | — | — | Only PGC locus replicating in UK Biobank | 6 |
| SLC6A4 (5-HTTLPR) × childhood maltreatment | interaction β | ~0 | — | not significant | UK Biobank | 7 |
| Measurement error sensitivity | OR (corrected) | 1.003-1.065 | — | — | Corrected for attenuation, still null | 9-10 |
| Power for OR=1.05 | — | 80% | — | at α=0.0005 | UK Biobank, MAF>0.05 | 7 |
| Power for OR=1.05 | — | 80% | — | at α=0.002 | BiLEVE sample, MAF>0.05 | 7 |

## Methods & Implementation Details
- Candidate gene identification: Used Biopyction bioinformatics package (v.45) to search PubMed for biomedical literature; regular expressions to find articles corresponding to each gene; hand-verified counts of correctly classified articles *(p.3)*
- 18 candidate genes identified: SLC6A4, BDNF, DRD4, GNB3, HTR1A, MTHFR, SLC6A3, TPH1, APOE, DRD2, GR/NR3C1, HTR2A, MAOA, ACE, CRHR1, FKBP5, OXTR, DTNBP1 *(p.2-3)*
- Top polymorphism per gene selected (e.g., 5-HTTLPR for SLC6A4, Val66Met for BDNF, Val158Met for COMT) *(p.3)*
- UK Biobank genotyping: Affymetrix UK BiLEVE Axiom array and UK Biobank Axiom array; imputation to Haplotype Reference Consortium *(p.5)*
- VNTRs not directly genotyped in UK Biobank; VNTR proxy SNPs used with r^2>0.888 *(p.5)*
- 5-HTTLPR proxy: examined effects of several highly studied VNTR polymorphisms in large GWAS dataset, including 5-HTTLPR in SLC6A4, which was examined in 38.1% of depression candidate gene studies *(p.5)*
- PGC GWAS: Used summary statistics from PGC3 depression GWAS (excluding UK Biobank) as input for gene-level MAGMA analyses *(p.5)*
- Gene-wise association tests: MAGMA default — gene-wise analysis examines association between a phenotype and a set of genes rather than individual SNPs; competitive gene-set tests control for gene size *(p.5)*
- Covariates: age, sex, assessment center, genotyping batch, 10 ancestry PCs *(p.5)*
- Multiple testing correction: Bonferroni across all tests; also used liberal threshold of p<5×10^-4 *(p.6)*
- Interaction tests included all covariate-by-polymorphism and covariate-by-moderator terms as covariates (common in GxE literature per Keller 2014) *(p.5)*
- Controlled for potentially confounding influences of covariates on the interaction *(p.5)*
- Also tested interaction models that controlled only for main effects (insufficient but common in candidate gene literature) *(p.5)*

## Figures of Interest
- **Fig 1 (p.2):** Estimated lower bounds of studies per candidate gene. Panel A: Cumulative sum of estimated number of depression candidate gene studies from 1995-2018, showing exponential growth (~1,000+ studies for SLC6A4). Panel B: Number of studies per gene examining top polymorphism vs other polymorphisms.
- **Fig 2 (p.8):** Main effects and GxE effects of 16 candidate polymorphisms on estimated lifetime depression diagnosis and current depression severity in UK Biobank. Shows all effects near zero with confidence intervals crossing null. 80% power line at α=0.0005 shown.
- **Fig 3 (p.10):** Gene-wise statistics for effects of 18 candidate genes on primary depression outcomes in UK Biobank. All below genome-wide significance (α = 2.63×10^-6). Candidate genes indistinguishable from non-candidate genes.
- **Table 1 (p.4):** Depression and environmental moderator phenotypes with operational definitions and sample sizes.
- **Table 2 (p.7):** Minimum p-value across eight main effect models and 32 interaction effect models per polymorphism. Only COMT rs4680 shows p<0.01 on one phenotype.

## Results Summary
No clear evidence was found for any of the 18 candidate gene polymorphism associations with depression phenotypes or any polymorphism-by-environment moderator effects across all analyses. As a set, depression candidate genes were no more associated with depression phenotypes than non-candidate genes. Only one candidate gene polymorphism (COMT rs4680 on current depression severity) reached the liberal significance threshold, but this would not survive correction for multiple testing. The 5-HTTLPR — the most studied polymorphism — showed no association with any depression phenotype or interaction. Gene-level analyses via MAGMA confirmed null results. Replication of top PGC GWAS loci showed only one (PCLO/Piccolo) replicating, suggesting that even well-powered GWAS hits may be fragile. Sensitivity analyses for measurement error, using disattenuated effect sizes, confirmed that phenotypic measurement error cannot explain the null findings. *(p.6-10)*

## Limitations
- VNTRs (including 5-HTTLPR) were not directly genotyped; proxy SNPs were used (r^2 > 0.888 for best proxies) — though authors argue this actually favors detection since tag SNPs capture broader haplotype effects *(p.9)*
- UK Biobank sample is healthier than general population ("healthy volunteer" selection bias) *(p.9)*
- Some depression phenotypes used may not capture clinical diagnosis precisely (e.g., self-report questionnaires vs structured clinical interviews) *(p.9)*
- Current depression severity was based on widely used Patient Health Questionnaire-9, but this may not reflect lifetime severity *(p.9)*
- One of the nine DSM-5 depression symptoms (motor agitation/retardation) was omitted from UK Biobank online mental health follow-up questionnaire *(p.9)*
- Half of diagnoses and half of traumatic exposures were determined by coin toss (see Section S4.5 in supplement) — i.e., measurement error is present but shown insufficient to explain nulls *(p.10)*

## Arguments Against Prior Work
- The candidate gene literature for depression features hundreds of studies reporting large genetic effects in samples orders of magnitude smaller than those examined here — these are likely false positives *(p.1)*
- Previous candidate gene findings suggested effects far larger than what genome-wide studies have identified for complex traits *(p.1)*
- The exponential growth of candidate gene studies (Figure 1) occurred despite lack of replication in GWAS *(p.2)*
- Prior replication attempts: only 27% of replication attempts found significant results; replication attempts reporting null findings had larger sample sizes than those reporting positive findings (refs 15-17) *(p.3)*
- Selective publication and reporting practices can inflate type I errors and lead to biased representations of evidence for candidate gene hypotheses *(p.9)*
- Many prior studies did not properly control for population stratification, characteristic heterogeneity, or multiple testing *(p.3)*
- The "short" allele of 5-HTTLPR × stressful life events hypothesis (Caspi et al. 2003) generated enormous follow-up research but does not replicate *(p.2)*

## Design Rationale
- Used multiple operational definitions of depression to avoid the criticism that null results stem from phenotype choice *(p.4)*
- Used multiple environmental moderators for the same reason *(p.4)*
- Preregistered all analyses to prevent post-hoc analytical flexibility *(p.3)*
- Used both additive and multiplicative scales for interaction tests *(p.5)*
- Included both stringent (Bonferroni) and liberal significance thresholds *(p.6)*
- Used gene-level tests (MAGMA) in addition to single-SNP tests to capture effects of other polymorphisms within the gene *(p.5)*
- Tested candidate genes as a set against non-candidate genes to address whether they carry any signal at all *(p.6)*

## Testable Properties
- No individual candidate gene polymorphism among the 18 tested shows association with depression at genome-wide significance in samples >60,000 *(p.6)*
- 5-HTTLPR shows no main effect on any depression phenotype in N>400,000 *(p.6-7)*
- 5-HTTLPR × childhood maltreatment interaction is null in N>100,000 *(p.7)*
- Depression candidate genes as a set are no more associated with depression than random non-candidate genes *(p.6)*
- Measurement error attenuation cannot convert null findings to significant ones for these effect sizes *(p.9-10)*
- 80% power to detect OR=1.05 at α=0.0005 in UK Biobank sample for MAF>0.05 *(p.7)*
- Prior candidate gene studies reporting large effects in small samples (N<1,000) are expected to yield false positive rates consistent with the number of positive findings in the literature *(p.1)*

## Relevance to Project
This paper is relevant to propstore's argumentation and evidence evaluation framework in several ways:
1. **Replication crisis evidence:** Provides a canonical example of a large-scale failure to replicate an entire subfield's findings, directly relevant to meta-scientific reasoning about evidence quality.
2. **False positive reasoning:** The argument structure — testing whether an entire literature's findings are false positives by using much larger samples — is a pattern that could be modeled in the argumentation layer.
3. **Evidence weighting:** Demonstrates why sample size and statistical power should heavily weight evidence evaluation. A single large N study can defeat hundreds of small N studies.
4. **Candidate gene vs GWAS paradigm:** Illustrates the shift from hypothesis-driven to data-driven genetics, relevant to modeling scientific paradigm transitions.

## Open Questions
- [ ] How do the Camerer et al. 2016/2018 replication studies in the collection relate to this paper's findings about false positives?
- [ ] Could the argumentation framework model the defeat of hundreds of small-sample studies by one large-sample study?

## Collection Cross-References

### Already in Collection
- [[Aarts_2015_EstimatingReproducibilityPsychologicalScience]] — thematically related: provides base rates for replication failure that contextualize Border's finding that candidate gene studies are false positives
- [[Altmejd_2019_PredictingReplicabilitySocialScience]] — thematically related: predictors of replication success (effect size, p-value, sample size) directly explain why small-sample candidate gene studies failed to replicate
- [[Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments]] — thematically related: systematic replication methodology parallels Border's approach of testing prior findings in larger samples
- [[Camerer_2018_EvaluatingReplicabilitySocialScience]] — thematically related: replication deflation factor of 0.71 is consistent with Border's finding that prior candidate gene effects vanish entirely
- [[Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction]] — thematically related: base rate that studies with p<0.005 replicate at 76% contextualizes the fragility of candidate gene p-values

### New Leads (Not Yet in Collection)
- Caspi et al. (2003) — "Influence of life stress on depression: moderation by a polymorphism in the 5-HTT gene" — the original 5-HTTLPR × stress finding, directly refuted by Border 2019
- Wray et al. (2018) — "Genome-wide association analyses identify 44 risk variants" — the PGC3 GWAS providing the paradigm that supersedes candidate genes
- Duncan & Keller (2011) — "A critical review of the first 10 years of candidate gene-by-environment interaction research" — theoretical framework for why these findings are false positives
- Ioannidis (2005) — "Why most published research findings are false" — statistical framework explaining the false positive generation mechanism
- Keller (2014) — "Gene × environment interaction studies have not properly controlled for potential confounders" — identifies the specific methodological flaw

## Related Work Worth Reading
- Caspi et al. 2003 — Original 5-HTTLPR × stressful life events finding (the paper that launched a thousand replications)
- Sullivan et al. 2000/2009 — Genetic epidemiology of major depression reviews
- Wray et al. 2018 — Large GWAS of depression identifying real loci
- Culverhouse et al. 2018 — Independent null finding for 5-HTTLPR
- Munafò et al. 2009 — Candidate gene × environment interaction review
- Keller 2014 — Limitations of gene × environment studies
- Flint & Kendler 2014 — Genetics of major depression review
- Duncan & Keller 2011 — Critical assessment of candidate gene literature
