"""Cross-entity identity derivations.

Artifact-id and version-id derivations for the canonical families live here.
A source branch proposes claims and concepts in its own logical namespace; the
deterministic canonical identity (``ps:claim:…`` / ``ps:concept:…`` plus the
content version id) is derived from that logical handle and the claim content.
The source-authoring subsystem (:mod:`propstore.source`) stamps these onto each
proposed artifact so the same logical id survives promotion into ``master``.
"""

from __future__ import annotations
