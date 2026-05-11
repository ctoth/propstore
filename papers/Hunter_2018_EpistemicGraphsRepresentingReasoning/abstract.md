# Abstract

## Original Text (Verbatim)

This paper introduces epistemic graphs as a generalization of the epistemic approach to probabilistic argumentation. In these graphs, an argument can be believed or disbelieved up to a given degree, thus providing a more fine-grained alternative to the standard Dung's approaches when it comes to determining the status of a given argument. Furthermore, the flexibility of the epistemic approach allows us to both model the rationale behind the existing semantics as well as completely deviate from them when required. Epistemic graphs can model both attack and support as well as relations that are neither support nor attack. The way other arguments influence a given argument is expressed by the epistemic constraints that can restrict the belief we have in an argument with a varying degree of specificity. The fact that we can specify the rules under which arguments should be evaluated and we can include constraints between unrelated arguments permits the framework to be more context-sensitive. It also allows for better modelling of imperfect agents, which can be important in multi-agent applications.

---

## Our Interpretation

The paper provides a formal graph-and-constraint architecture for modelling degrees of belief in arguments and the contextual influence relations among them. It is especially relevant where a system needs to keep graph structure, relation labels, source-local belief constraints, and solver-backed consequence checks separate rather than collapsing them into binary acceptance.
