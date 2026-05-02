# Abstract

## Original Text (Verbatim)

Linking between entities in different datasets is a crucial element of the Semantic Web architecture, since those links allow us to integrate datasets without having to agree on a uniform vocabulary. However, it is widely acknowledged that the owl:sameAs construct is too blunt a tool for this purpose. It entails full equality between two resources independent of context. But whether or not two resources should be considered equal depends not only on their intrinsic properties, but also on the purpose or task for which the resources are used. We present a system for constructing context-specific equality links. In a first step, our system generates a set of probable links between two given datasets. These potential links are decorated with rich metadata describing how, why, when and by whom they were generated. In a second step, a user then selects the links which are suited for the current task and context, constructing a context-specific "Lenticular Lens". Such lenses can be combined using operators such as union, intersection, difference and composition. We illustrate and validate our approach with a realistic application that supports researchers in social science.

---

## Our Interpretation

The paper treats identity as a contextual, provenance-bearing decision rather than a universal fact asserted by `owl:sameAs`. Its main contribution is a representation and workflow for generating candidate correspondences, annotating their provenance and justification, and constructing task-specific views over them with lens operators. This is useful for propstore because it supports identity reconciliation without premature canonical collapse.
