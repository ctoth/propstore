---
title: "Relational Parametricity and Units of Measure"
authors: ["Andrew J. Kennedy"]
year: 1997
venue: "POPL 1997"
doi_url: "https://doi.org/10.1145/263699.263761"
pages: 15
---

# Relational Parametricity and Units of Measure

## Citation
Kennedy, Andrew J. "Relational Parametricity and Units of Measure." Proceedings of the 24th ACM Symposium on Principles of Programming Languages, Paris, France, January 1997, pp. 442-455.

## Problem
Programming languages normally treat numeric values as dimensionless even when scientific programs manipulate measured quantities with units such as kilograms, metres, seconds, inches, and newtons. Prior work extended type systems to check dimensions and infer units at compile time, but Kennedy studies the denotational semantics of unit polymorphism and proves that unit-parametric programs obey a representation-independence principle analogous to Reynolds relational parametricity. The central claim is that behavior should be invariant under changes of units of measure. *(p.1)*

## Core Thesis
Unit annotations are not just labels for dimensional checking. Quantification over units introduces a form of parametric polymorphism, and the type of a unit-polymorphic expression implies semantic facts about how it must scale under unit changes. This yields "theorems for free" for scientific programs and connects programming-language type isomorphisms to the Pi theorem from dimensional analysis. *(p.1, p.3, p.8-10)*

## Key Concepts
- **Unit of scale:** a reference quantity used for comparison and measurement; a single physical quantity can be measured in many unit systems, including nonlinear or non-zero-origin scales, though the paper focuses on multiplicative unit scaling. *(p.1)*
- **Dimension:** a class of isomorphic data representations; base dimensions such as mass, length, and time are fixed by convention, while derived dimensions are products of powers of base dimensions. *(p.2)*
- **Dimensional consistency:** additions, subtractions, and comparisons require matching dimensions; products and quotients combine dimensions by multiplication and division. Dimensional inconsistency indicates that a numerical formula is suspect. *(p.2)*
- **Dimensional invariance:** physical laws remain the same under changes of units. Kennedy formalizes this as a relation between denotations under scaling environments. *(p.2, p.5-7)*
- **Unit polymorphism:** types can quantify over unit variables, e.g. `Forall u. num u -> num u`, allowing a function to work uniformly over all units of a dimension. *(p.2-4)*
- **Unit erasure:** removal of unit abstractions/applications and replacement of `num u` with `num 1`; used in the relative full abstraction discussion. *(p.11)*

## Formal Language
Kennedy defines an explicitly typed lambda calculus `Lambda_u` with booleans, unit-indexed numeric types, functions, and universal quantification over units. Unit expressions are generated from unit variables, the dimensionless unit `1`, unit product, and unit inverse. Types include `bool`, `num mu`, `tau1 -> tau2`, and `Forall u. tau`. *(p.4)*

Unit expressions form an Abelian group under product and inverse, with axioms for commutativity, associativity, identity, and inverses. Every unit expression has a normal form as a product of distinct unit variables raised to non-zero integer powers. *(p.4)*

The typing rules include standard lambda-calculus rules plus:
- an equality/conversion rule allowing equivalent unit/type expressions;
- unit abstraction introduction;
- unit abstraction elimination/application. *(p.5)*

The standard operator environment assigns unit-polymorphic arithmetic types: zero is polymorphic over `num u`; one has type `num 1`; addition/subtraction and comparison require equal units; multiplication and division multiply/divide units in the result type. The base unit environment includes kilograms, metres, and seconds. *(p.5)*

The denotational semantics deliberately erases units from values: `bool` maps to booleans, `num mu` maps to rationals plus bottom, functions map to continuous functions, and `Forall u. tau` maps to the same domain as `tau`. Unit information is recovered semantically by a logical relation, not by carrying unit annotations in values. *(p.5)*

## Equations And Definitions

### Numerical Differentiation Example
Kennedy uses the central-difference approximation:

$$
f'(x) \approx \frac{f(x+h)-f(x-h)}{2h}
$$

The unit-polymorphic type is:

$$
\forall u_1.\forall u_2.\ \mathrm{num}\ u_1 \to (\mathrm{num}\ u_1 \to \mathrm{num}\ u_2) \to (\mathrm{num}\ u_1 \to \mathrm{num}\ u_2 \cdot u_1^{-1})
$$

The function accepts an increment, a function, and an argument, returning an approximate derivative whose result unit is output-unit divided by input-unit. *(p.3)*

### Newton Iteration Example

$$
x_{n+1}=x_n-\frac{f(x_n)}{f'(x_n)}
$$

The associated type is:

$$
\forall u_1.\forall u_2.\ (\mathrm{num}\ u_1 \to \mathrm{num}\ u_2)
\to(\mathrm{num}\ u_1 \to \mathrm{num}\ u_2 \cdot u_1^{-1})
\to \mathrm{num}\ u_1 \to \mathrm{num}\ 1 \to \mathrm{num}\ u_1
$$

The relative accuracy parameter has dimensionless type `num 1`; the root approximation has the same unit as the input variable. *(p.3)*

### Parametricity Relation
For each type `tau` and scaling environment `psi`, the paper defines a relation:

$$
R_\tau^\psi \subseteq \llbracket\tau\rrbracket \times \llbracket\tau\rrbracket
$$

The key cases are identity for booleans, a scaling relation for `num mu`, function-space lifting, and intersection over all extensions for unit-polymorphic types. *(p.6)*

### Parametricity Theorem

$$
\mathcal{V};\Gamma \vdash e:\tau \Rightarrow \mathcal{V};\Gamma \vDash e:\tau
$$

If two value environments are related under a scaling environment, then the meanings of the expression under those environments are related at the expression's type. The proof is by induction on the typing derivation. *(p.7)*

### Completeness Of The Standard Scaling Environment
For the standard arithmetic constants, Kennedy characterizes the largest class of scaling environments preserving the operator environment. Each such environment is determined by a subgroup `G` of unit expressions and a homomorphism from `G` to positive rationals. *(p.7)*

### Powers Theorem-For-Free
For an expression with type:

$$
\Gamma_{\mathrm{ops}} \vdash e:\forall u.\ \mathrm{num}\ u \to \mathrm{num}\ u^n
$$

the scaling law is:

$$
e(kx) \approx k^n e(x)
$$

for any positive scale factor `k`. *(p.8)*

### Differentiation Scaling Law
For the differentiation type from the motivating example:

$$
e\ h\ f\ x \approx \frac{k_2}{k_1}\ e\left(\frac{h}{k_1}\right)
\left(\lambda x.\frac{f(xk_1)}{k_2}\right)
\left(\frac{x}{k_1}\right)
$$

where `k1` and `k2` are positive scale factors for the input and output units. *(p.8)*

### First-Order Type Inhabitation Criterion
For first-order types of the form:

$$
\forall u_1 \ldots \forall u_m.\ \mathrm{num}\ \mu_1 \to \cdots \to \mathrm{num}\ \mu_n \to \mathrm{num}\ \mu
$$

where each input unit expression and the output unit expression is represented by integer exponents over the quantified units, there is a non-trivial term of this type iff there is an integer solution to the linear system:

$$
a_{11}z_1+\cdots+a_{1n}z_n=b_1
$$

$$
\vdots
$$

$$
a_{m1}z_1+\cdots+a_{mn}z_n=b_m
$$

This states that a result with the requested unit can be built from integer powers of the input units. *(p.9)*

### Pi Theorem
For `m` base dimensions and `n` variables with dimension matrix `A`, any dimensionally invariant relation:

$$
f(x_1,\ldots,x_n)=0
$$

is equivalent to:

$$
f'(\Pi_1,\ldots,\Pi_{n-r})=0
$$

where `r` is the rank of `A` and the `Pi_i` are dimensionless power-products of the variables. *(p.10)*

### Pi Theorem For `Lambda_u`
For a closed type:

$$
\forall u_1 \ldots \forall u_m.\ \mathrm{num}\ \mu_1 \to \cdots \to \mathrm{num}\ \mu_n \to \mathrm{num}\ \mu_0
$$

let `A` be the matrix of unit exponents in the input unit expressions, and `B` the vector of output exponents. If `AX = B` is solvable over integers, then the type is isomorphic over positive values to a function over `n-r` dimensionless numeric arguments:

$$
\tau \cong^+ \mathrm{num}\ 1 \to \cdots \to \mathrm{num}\ 1 \to \mathrm{num}\ 1
$$

where `r = rank(A)`. *(p.10, p.13-14)*

## Main Results
- **Parametricity theorem:** unit-polymorphic terms preserve the logical relation induced by scaling environments. *(p.7)*
- **Completeness of standard arithmetic constants:** preserving the standard constants forces scaling environments into a homomorphic positive-scaling form over a subgroup of unit expressions. *(p.7)*
- **Theorems for free:** unit-polymorphic types imply concrete scaling laws without inspecting term definitions. *(p.8)*
- **Type inhabitation:** first-order unit-polymorphic numeric types have non-trivial inhabitants exactly when the corresponding exponent linear system has an integer solution. *(p.9)*
- **Type isomorphisms:** many unit-polymorphic types are isomorphic to lower-arity dimensionless types over positive values; this is the programming-language analogue of dimensional-analysis reduction. *(p.9-10)*
- **Relative definability:** some dimensionless definitions can be lifted back to unit-polymorphic definitions by choosing a representative magnitude from an input structure, scaling to dimensionless form, applying the dimensionless function, and scaling back. *(p.10-11)*
- **Relative full abstraction direction:** Kennedy proposes quotienting the underlying semantics by the scaling relation to identify meanings that differ only in unit representation. *(p.11-12)*

## Methods And Implementation Details
- Unit expressions use integer exponents only; fractional unit powers are rejected as a design choice because they imply changing the base unit set instead. *(p.2)*
- Arithmetic constants are typed so addition/subtraction/comparison are unit-preserving, while multiplication/division compose unit expressions. *(p.5)*
- Bottom/divergence is part of the semantics; recursive definitions are interpreted through least upper bounds of chains in complete partial orders. *(p.5-6)*
- Scaling environments map unit expressions to binary relations on rationals. The standard arithmetic constants restrict admissible nonzero scaling relations to positive scalar multiplication, with `(0,0)` always present. *(p.6-8, p.13)*
- Type-isomorphism proofs reduce unit-exponent matrices by elementary row and column operations; the appendix explicitly connects these operations to Smith normal form. *(p.13-14)*

## Figures Of Interest
- **Figure 1:** Typing rules for `Lambda_u`, including unit abstraction and application. *(p.5)*
- **Figure 2:** Standard operator and base-unit type environments. *(p.5)*
- **Figure 3:** Underlying unit-erased denotational semantics. *(p.6)*
- **Figure 4:** Family of scaling relations induced by a class of scaling environments. *(p.6)*
- **Figure 5:** Scaling environments preserving the standard arithmetic constants. *(p.7)*

## Results Summary
Kennedy proves that unit polymorphism gives an operationally useful invariance theorem: a term's unit-polymorphic type constrains how the term can behave under changes of scale. The paper then cashes this out as concrete scaling laws, non-inhabitability results, first-order inhabitation criteria, and a typed analogue of the Pi theorem. For `bridgman`, this means the dimension vector is not only a consistency check; it can also be the input to derived invariance obligations and dimensionless reduction witnesses. *(p.7-12)*

## Limitations
- The formalism focuses on multiplicative unit changes and positive scale factors when comparisons are present; negative or zero unit scales are excluded because they break ordering behavior. *(p.7-8)*
- Nonlinear and non-zero-origin units such as decibels or degrees Celsius are acknowledged in the motivation but not modeled in the core calculus. *(p.1)*
- Fractional unit powers are not supported; Kennedy treats them as motivation to revise the set of base units instead. *(p.2)*
- Full abstraction is not completed; the proposed quotient/PER construction is sketched and left partly open. *(p.11-12)*
- The paper models unit dimensions, not semantic quantity kinds such as energy vs torque. Bridgman's current kind layer is therefore complementary rather than derived directly from Kennedy. *(p.2-4)*

## Arguments Against Prior Work
- Dimension checking without polymorphism catches errors but has limited expressive power: even square-root functions need to be polymorphic if applied across units. *(p.2)*
- Implicit-typing ML-style systems can infer unit-polymorphic types but restrict quantification to outermost type positions; Kennedy studies explicit System-F-style unit quantification because it permits units inside types. *(p.2-3)*
- Plain denotational semantics erases unit annotations, so it cannot by itself distinguish meanings that differ only in unit behavior. The logical relation supplies that missing constraint. *(p.5-7)*

## Design Rationale
- Unit expressions are an Abelian group because dimension algebra requires product, inverse, identity, commutativity, and associativity. *(p.4)*
- Numeric values erase unit annotations so ordinary mathematical semantics remain simple; invariance is proved through relations rather than extra runtime data. *(p.5-6)*
- Arithmetic constants determine which scaling relations are admissible. This makes operator semantics the bridge between syntax-level unit annotations and semantic invariance. *(p.7)*
- Positive-value restrictions are introduced because functions over signed values can branch on sign in ways that have no analogue after dimensionless reduction. *(p.10)*

## Testable Properties
- If `pow_dims` or any unit-expression exponent mechanism accepts non-integer powers, it violates Kennedy's integer-exponent design for unit expressions. *(p.2, p.4)*
- Addition, subtraction, and comparison over measured quantities should require equal unit/kind annotations; multiplication and division should combine annotations structurally. *(p.2, p.5)*
- A type/form `num u -> num u^n` implies the scaling property `e(kx) ~= k^n e(x)` for positive `k`. *(p.8)*
- First-order derived quantity construction should be reducible to solving an integer linear system over exponent matrices. *(p.9)*
- Any dimensionally invariant first-order relation over `n` variables and rank-`r` dimension matrix should admit a dimensionless representation over `n-r` Pi terms. *(p.10)*
- Smith-normal-form-like row/column operations over the exponent matrix should preserve the isomorphism class used for dimensionless reduction. *(p.13-14)*

## Relevance To This Project
This paper is directly relevant to `bridgman`, `physgen`, and `propstore`. `bridgman` already implements the Abelian-group-like dimension arithmetic and integer exponent guards; Kennedy supplies the next semantic layer: proof obligations and witnesses that a typed formula is invariant under unit scaling. `physgen` can use this to generate language-specific compile-time guarantees and examples beyond "does the dimension match." `propstore` can use it to enrich equation claims: a validated equation can carry a dimension matrix, Pi-basis reduction, and scaling-law diagnostics as provenance-bearing artifacts rather than only a boolean dimensional status. *(p.2-12)*

## Open Questions
- [ ] Should `bridgman` expose a matrix/nullspace or Smith-normal-form API for dimensionless Pi terms, or should that live in a downstream package? *(p.10, p.13-14)*
- [ ] How should affine units such as Celsius be represented when Kennedy's core calculus assumes multiplicative positive scaling? *(p.1, p.7-8)*
- [ ] Can `bridgman` express scaling-law witnesses without becoming a full typed language implementation? *(p.5-8)*
- [ ] How should quantity-kind distinctions interact with Kennedy's unit-parametricity, since the paper does not distinguish semantic twins beyond dimensions? *(p.2-4)*

## Related Work Worth Reading
- Wand and O'Keefe 1991, "Automatic dimensional inference" - cited as prior dimension/unit inference work. *(p.12)*
- Kennedy 1994, "Dimension types" - earlier dimension-type paper. *(p.12)*
- Kennedy 1995, "Programming Languages and Dimensions" - PhD thesis, likely fuller development. *(p.12)*
- Rittri 1995, "Dimension inference under polymorphic recursion" - used in relative definability. *(p.12)*
- Birkhoff 1960, "Hydrodynamics: A Study in Logic, Fact and Similitude" - cited source for the Pi theorem. *(p.10, p.12)*

## Provenance
Read directly from page images `pngs/page-000.png` through `pngs/page-014.png` on 2026-05-12 using the `research-papers:paper-reader` workflow. No PDF text extraction was used.
