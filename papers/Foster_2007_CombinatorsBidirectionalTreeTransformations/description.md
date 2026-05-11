---
tags: [bidirectional-transformation, lens-laws, projection, view-update, information-preservation]
---
Defines lenses as typed get/putback pairs for tree-structured data, with GetPut, PutGet, optional PutPut, and totality laws governing when a projection preserves enough information for safe update. Builds a compositional combinator language for identities, composition, constants, tree restructuring, map, copy, merge, conditionals, list lenses, flatten/pivot/join, and bookmark synchronization. Gives propstore a formal projection contract: rendered views should carry typed putback policies and round-trip tests instead of relying on informal claims that no information was lost.
