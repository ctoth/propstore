# Repo Merge Papers

These are the additional papers we still need for the repo-merge / identity-reconciliation work.

The core merge theory already in the corpus is enough:

- IC merging: `Konieczny_2002_MergingInformationUnderConstraints`
- AF/PAF merging: `Coste-Marquis_2007_MergingDung'sArgumentationSystems`
- persistent identifiers / verification: `Juty_2020`, `Wilkinson_2016`, `Kuhn_2014`, `Kuhn_2017`
- statement-level provenance: `Groth_2010`
- anti-collapse identity warning: `Raad_2019`

What is still missing is a tighter literature base for weaker identity relations, identity repair, and large-scale error propagation.

## Need Next

1. **Halpin et al. (2010), _When owl:sameAs Isn't the Same_**
   Why: foundational critique of over-strong identity assertions; directly relevant to avoiding eager cross-repo collapse.

2. **de Melo (2013), _Not Quite the Same: Identity Constraints for the Web of Linked Data_**
   Why: gives a more nuanced identity-constraint vocabulary than binary same/not-same; useful for first-class identity relations.

3. **Beek et al. (2018), _sameAs.cc: The Closure of 500M owl:sameAs Statements_**
   Why: operational evidence about identity-closure growth and error propagation at scale; useful for repair and propagation limits.

## Priority

- **High:** Halpin 2010
- **High:** de Melo 2013
- **Medium:** Beek 2018

## Why These, Not More Merge Papers

We do **not** currently need more merge-operator papers before implementation.

The blocking gaps in the code are:

- repo-safe concept identity
- merged-repo semantic closure under divergence
- explicit weaker-than-collapse identity relations
- reconciliation workflow for semantic candidates

Those are identity-architecture problems more than merge-theory problems.
