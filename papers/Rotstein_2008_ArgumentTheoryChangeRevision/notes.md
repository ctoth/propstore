---
title: "Argument Theory Change: Revision Upon Warrant"
authors: "Nicolás D. Rotstein, Martín O. Moguillansky, Marcelo A. Falappa, Alejandro J. García, Guillermo R. Simari"
year: 2008
venue: "COMMA 2008, Computational Models of Argument"
doi_url: null
produced_by:
  agent: "GPT-5 Codex"
  skill: "paper-reader"
  timestamp: "2026-03-28T08:34:46Z"
---
# Argument Theory Change: Revision Upon Warrant

## One-Sentence Summary
Introduces an abstract, belief-revision-inspired framework for changing structured argument systems so that a target argument becomes warranted by expanding the active argument set and then minimally deactivating selected attackers under preservation constraints. *(p.1, p.7-11)*

## Problem Addressed
Prior dynamic work on abstract argumentation mostly studies changes to abstract frameworks rather than revision over arguments with internal structure, and existing argument-revision proposals were either tied to particular implementations or only treated explanatory support indirectly. This paper asks how to define general argument-theory change operators that can revise a structured argument system so a chosen argument is warranted while preserving as much of the theory as possible. *(p.1, p.7)*

## Key Contributions
- Defines a dynamic abstract argumentation framework `DAF = (U, A, R, <=)` that distinguishes a universal argument pool from the currently active arguments and adds a subargument relation so partial argument deactivation can be modeled abstractly. *(p.2)*
- Introduces regular, atomic, potential, and equistructural arguments, allowing incomplete arguments to be represented before all evidence is available. *(p.2-4)*
- Builds a dynamic argumentation theory `DAT = (Phi, DC)` by combining the framework with dialectical constraints over acceptable argumentation lines. *(p.5-6)*
- Defines the machinery needed for argument change: attacking lines, argument selection functions, incision functions, collateral incision, cautiousness, preservation, strict preservation, and root preservation. *(p.7-10)*
- Defines three change operators: argument expansion, non-warrant argument contraction, and warrant-prioritized argument revision, and proves that the revision operator warrants the target argument. *(p.7, p.10-11)*
- Shows an argument-change identity analogous to Levi's identity: revision can be expressed as expansion followed by non-warrant contraction. *(p.11)*

## Study Design (empirical papers)
Not applicable; this is a theoretical paper that develops definitions, operators, properties, and proofs over structured abstract argumentation objects. *(p.1-12)*

## Methodology
The paper adapts AGM-style belief revision to a structured argumentation setting while remaining abstract about the underlying logic and semantics. It first defines a dynamic argument universe with active/inactive arguments and explicit subargument structure, then defines acceptable dialectical trees under configurable constraints, then characterizes which attacking lines must be altered to warrant a root argument, and finally constrains incision-based deactivation so the desired warrant can be obtained with minimal collateral change. *(p.1-11)*

## Key Equations / Statistical Models

$$
DAF = (U, A, R, \leq)
$$
Where `U` is the finite universal set of arguments, `A ⊆ U` is the set of active arguments, `R ⊆ U x U` is the attack relation, and `<=` is the subargument partial order. *(p.2)*

$$
A_e \in A \iff \forall A' \leq A_e,\; A' \in A
$$
Activeness propagation: an argument is active iff all of its subarguments are active, so inactivity propagates upward to every superargument. *(p.5)*

$$
DAT = (\Phi, DC)
$$
Where `Phi` is a `DAF` satisfying activeness propagation and `DC = {C_1, C_2, ..., C_n}` is a finite set of dialectical constraints over argumentation lines. *(p.5)*

$$
T +^{\Delta} A = ((U, A \cup \{A\}, R, \leq), DC)
$$
Argument expansion activates a regular argument `A`; because of activeness propagation this can also activate its superarguments automatically. *(p.10)*

$$
T -^{\omega} A = ((U, A \setminus \bigcup\{\sigma(\gamma(\lambda)) \mid \lambda \in Att(T_A)\}, R, \leq), DC)
$$
Non-warrant argument contraction deactivates the arguments selected for incision on attacking lines in the dialectical tree rooted at `A`. *(p.10)*

$$
T *^{\omega} A = ((U, (A \cup \{A\}) \setminus \bigcup\{\sigma(\gamma(\lambda)) \mid \lambda \in Att(T +^{\Delta} A)\}, R, \leq), DC)
$$
Warrant-prioritized argument revision first expands by `A` and then removes the incised attackers needed to warrant `A`. *(p.11)*

$$
T *^{\omega} A = (T +^{\Delta} A) -^{\omega} A
$$
Argument-change identity: warrant-prioritized revision is the analog of Levi identity for this argumentation setting. *(p.11)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|

The paper is purely structural and does not introduce numeric thresholds, hyperparameters, or measured constants; its operative parameters are symbolic sets, functions, and constraints defined in the formalism. *(p.1-12)*

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|

Not applicable; the paper contains no empirical measurements or benchmark results. *(p.1-12)*

## Methods & Implementation Details
- A universal argument pool `U` represents every argument that can ever be considered, while `A` tracks the currently active arguments and `I = U \\ A` the inactive ones. This separation is what lets the theory model change without rebuilding the universe. *(p.2)*
- The subargument order is central: the authors explicitly need to be able to eliminate only some part of a given argument, so they distinguish subarguments from proper subarguments and use a partial order over arguments. *(p.2)*
- An argument is defined as a self-consistent, minimal set of interrelated knowledge pieces supporting a claim from evidence. Minimality excludes redundant proper subarguments that already support the claim. *(p.3)*
- Atomic arguments are arguments with no proper subarguments. The paper distinguishes atomic regular arguments from evidence-bearing arguments; a regular atomic argument is not itself evidence. *(p.3)*
- Potential arguments represent incomplete supporting structures whose claims cannot yet be derived because the needed evidence is unavailable. They inherit minimality and self-consistency indirectly through their completion into a regular argument. *(p.3)*
- The completion function `chi(A)` maps a potential argument to the regular argument composed only of the atomic arguments needed to support its claim. Multiple completions may exist conceptually, but the function fixes one completion to make the formal treatment concrete. *(p.3)*
- Regular and potential arguments are given a graphical triangle-based representation. Potential arguments carry "request" positions indicating where additional support must be supplied before the claim can be reached. *(p.4)*
- Equistructurality abstracts away from surface representation: two arguments are equistructural when they are built from the same set of atomic arguments, even if their internal arrangement differs. *(p.4)*
- Activeness propagation means deactivating one subargument deactivates every superargument that depends on it. This is one of the key dynamic mechanisms in the framework. *(p.5)*
- Argumentation lines alternate interference and supporting arguments according to position in the line; this parity distinction is later used to restrict which arguments can be selected for incision. *(p.5)*
- Dialectical constraints are Boolean conditions on argumentation lines. They formalize admissibility conditions on dialogues and let different domains impose additional restrictions over lines. *(p.5)*
- Acceptable argumentation lines are those satisfying all dialectical constraints and containing only usable regular arguments. Bundle sets collect non-redundant acceptable lines for a root argument. *(p.5-6)*
- Dialectical trees are built from bundle sets. Acceptable dialectical trees are then evaluated by a marking criterion that labels arguments as undefeated or defeated. Warrant is defined in terms of the root of such a tree being marked undefeated. *(p.6)*
- To change a theory, the paper isolates the attacking lines `Att(T, A)`: the minimal subset of lines whose removal would make the root argument `A` warranted in a hypothetical modified theory. *(p.7)*
- An argument selection function `gamma` chooses, for each attacking line, an interference argument to target. The paper insists selection should depend on interference arguments rather than supporting ones because supporting-argument deactivation can distort line status improperly. *(p.8)*
- An incision function `sigma` maps the selected argument to the set of arguments actually deactivated. This allows the theory to model collateral incision when shared structure causes one incision to affect other lines as well. *(p.8)*
- Cautiousness is the desirable case where a selected argument can be incised without collateral damage to other arguments. Non-cautious selections are allowed, but then preservation constraints become critical. *(p.8-9)*
- Preservation requires collateral incisions not to destroy higher-level structure in a way that invalidates the revision goal. Root-preservation is the special case that the root argument itself may never be collaterally incised. *(p.9)*
- A warranting incision function is simply an incision function that satisfies preservation, making it suitable for warrant-focused contraction and revision. *(p.9)*
- Argument expansion is intentionally simple: just add the target regular argument to the active set. The authors note this may reduce warranted consequences because newly active attackers can appear. *(p.10)*
- Non-warrant argument contraction is designed specifically to turn attacking lines into non-attacking ones by deactivating selected interference arguments or their subarguments. It is the key "repair" step used before revision. *(p.10)*
- Warrant-prioritized revision combines the two operations so the target argument is first made available, then the minimum needed set of attackers is incised to warrant it. *(p.10-11)*

## Figures of Interest
- **Fig. 1 (p.4):** A graphical depiction of a potential argument showing the request positions that must be fulfilled for the claim to be reachable.
- **Fig. 2 (p.4):** Contrasts a regular argument configuration with the potential-argument case and illustrates how potentiality depends on the status of bottom subarguments.
- **Fig. 3 (p.6):** Shows a dynamic argumentation framework and a dialectical tree spanning from the root argument `A`; used to explain marking and warrant.
- **Fig. 4 (p.9):** Illustrates the preservation principle by showing how an incision in one branch can collaterally affect another branch and why upper-segment preservation matters.
- **Fig. 5 (p.11):** Worked example of non-warrant contraction and warrant-prioritized revision, including how line selection and preservation constraints lead to a warranted root.

## Results Summary
The paper's main result is constructive rather than empirical: it shows that a general abstract argumentation-change framework can be built on top of structured arguments, activeness propagation, and constrained incision, and that the warrant-prioritized revision operator obtained by combining expansion with non-warrant contraction does indeed warrant the target argument. The formal machinery also makes explicit where collateral incision and preservation must be controlled to avoid undermining the very argument one wants to warrant. *(p.7-11)*

## Limitations
- The framework keeps the underlying logic and argumentation semantics unspecified, which buys generality but leaves instantiation details to future work. *(p.1, p.12)*
- The paper only sketches operator properties and leaves stronger versions of the operators and explicit postulates for future research. *(p.12)*
- The current setup fixes the attack relation; future work is needed to support other forms of argument interaction and changes in the attack relation itself. *(p.12)*
- Preference criteria among arguments are not integrated yet; the authors suggest these could be handled as rules of the game, but do not develop that machinery here. *(p.12)*
- Composition of arguments from subarguments, especially with multiple representations, still needs further study to define equivalence and minimal-theory notions. *(p.12)*

## Arguments Against Prior Work
- Purely abstract dynamics such as Dung-style changes over attack graphs are not enough for the authors' goal because they do not expose the internal structure needed to deactivate only part of an argument. *(p.1-2)*
- Earlier work applying belief revision to argumentation had focused on explanations or implementation-specific operators, whereas this paper argues for a more general abstract treatment of argument-theory change. *(p.1, p.7)*
- A plain expansion operator is inadequate as a warrant-preserving revision operator because activating a new argument can also activate superarguments and diminish warranted consequences. *(p.10)*

## Design Rationale
- The authors deliberately keep the logic for constructing arguments and the argumentation semantics abstract so the framework can be reused across different structured argumentation settings. *(p.1)*
- They add a subargument relation precisely to support partial deactivation, which is necessary if contraction is supposed to remove only the parts of the theory responsible for a target argument's defeat. *(p.2)*
- Potential arguments are introduced to model incomplete argumentative structures that become regular once missing evidence arrives, making the dynamics sensitive to evidence availability. *(p.3-4)*
- Interference arguments, rather than supporting arguments, are chosen as incision targets because the objective is to neutralize attackers without distorting the support structure more than needed. *(p.8)*
- Preservation and root-preservation are justified as safeguards against collateral incision, ensuring that the revision process does not accidentally destroy the target argument or invalidate upper segments needed for the repair. *(p.9)*
- The final revision operator is defined as expansion followed by non-warrant contraction so it mirrors the Levi-style intuition from belief revision while remaining argument-structural. *(p.10-11)*

## Testable Properties
- If any subargument of an argument is inactive, the superargument must be inactive as well; conversely an active argument requires all of its subarguments to be active. *(p.5)*
- A dialectical tree warrants its root argument iff the chosen marking criterion marks that root as undefeated. *(p.6)*
- Selected arguments for incision should come from attacking lines and should be interference arguments, not supporting arguments. *(p.8)*
- A warranting incision function must satisfy preservation; in particular the root argument must never be collaterally incised. *(p.9)*
- Argument expansion activates the added regular argument and, by activeness propagation, every active superargument depending on it. *(p.10)*
- Warrant-prioritized revision is equivalent to argument expansion followed by non-warrant contraction and yields a theory in which the revised-by argument is warranted. *(p.11)*

## Relevance to Project
This paper is directly relevant to propstore because it turns AGM-style revision intuitions into explicit operations over structured arguments rather than only over propositions or bare Dung graphs. The selection/incision machinery is especially useful for any system that needs minimally invasive repair of defeated claims, provenance-aware deactivation of support, or dynamic update semantics for warrant rather than mere acceptability snapshots. *(p.1, p.7-11)*

## Open Questions
- [ ] How should the paper's abstract objects map onto propstore's concrete claim, support, and defeat representations? *(p.1-2, p.12)*
- [ ] What marking criterion should be used in a concrete implementation, and which dialectical constraints should be fixed by default? *(p.5-6)*
- [ ] How should collateral incision be represented in a provenance-rich store so shared subarguments are deactivated consistently? *(p.8-9)*
- [ ] Can the preservation conditions be turned into executable constraints or optimization objectives for minimal-change repair? *(p.9-11)*
- [ ] How should preference handling and mutable attack relations be integrated if the project wants richer dynamics than this paper directly provides? *(p.12)*

## Related Work Worth Reading
- Prakken and Vreeswijk on logical systems for defeasible argumentation, for the broader structured-argumentation background. *(p.12)*
- Dung 1995 on acceptability in abstract argumentation, which the paper treats as too coarse for this kind of internal revision. *(p.12)*
- Falappa, Simari, and Chesñevar 2002 on explanations, belief revision, and defeasible reasoning, since this paper explicitly extends that line toward full argument-theory change. *(p.12)*
- The authors' CACIC 2007 preliminary investigation on revision-based approaches to warrant status, which this paper generalizes. *(p.12)*
- Levi 1977 and Alchourrón, Gärdenfors, and Makinson 1985 for the belief-revision principles the paper adapts into argument change. *(p.12)*

## Collection Cross-References

### Already in Collection
- [[Alchourron_1985_TheoryChange]] — cited conceptually through AGM/Levi identity; this paper imports belief-revision ideas into structured argument change.
- [[Dung_1995_AcceptabilityArguments]] — explicitly treated as too coarse for the internal-structure-sensitive revision problem tackled here.
- [[Baumann_2010_ExpandingArgumentationFrameworksEnforcing]] — later collection paper that cites this as an AGM-style argumentation-dynamics approach complementary to enforcement by expansion.

### New Leads (Not Yet in Collection)
- Falappa, Simari, and Chesñevar (2002) — explanation/revision/defeasible-reasoning precursor extended here toward full argument-theory change.
- Levi (1977) — belief-revision identity background adapted here to warrant-prioritized revision.
- Alchourrón, Gärdenfors, and Makinson (1985) — AGM belief-revision postulate background for the revision analogy.

### Cited By (in Collection)
- [[Baumann_2010_ExpandingArgumentationFrameworksEnforcing]] — cites this as the AGM-style argumentation-revision counterpart to enforcement by adding arguments.

### Conceptual Links (not citation-based)
- [[Baumann_2010_ExpandingArgumentationFrameworksEnforcing]] — Strong. Both papers ask how to change an argumentation system minimally to achieve a target status, but Rotstein works over structured arguments and warrant while Baumann works over abstract AF expansion and enforcement.
- [[Boella_2009_DynamicsArgumentationSingleExtensions]] — Moderate. Boella studies invariance under deleting attacks or arguments, while Rotstein studies incision-based structured revision to make a target warranted.
- [[Alchourron_1985_TheoryChange]] — Moderate. This paper is one of the clearest attempts in the collection to transport AGM revision structure into an argumentation setting with internal support structure.
- [[Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic]] — **Strong.** Defines the epistemic entrenchment postulates that Rotstein's argument revision implicitly operationalizes — entrenchment determines which arguments/rules to retract when enforcing a target warrant status, directly corresponding to Rotstein's incision-based revision.
