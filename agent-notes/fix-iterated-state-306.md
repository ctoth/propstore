# Propstore issue 306

## Goal
Preserve the belief-set ranking and vocabulary across iterated revision in a new draft PR. No dependency pin upgrades, merges, ready transitions, or changes in other workers' ATMS/context/merge/cache scopes.

## State
New isolated worktree propstore-306, branch fix/iterated-state-306, based on freshly fetched published master da0b48b4. User's active checkout remains unchanged and dirty work preserved. Read global/project AGENTS.md and CLAUDE.md, existing issue-10 and dependency-audit notes, issue #306, related open PRs, iterated/state/adapter/realization/history code, existing tests, and pinned Quire document code. No existing #306 PR found; open revision/epistemic search found only unrelated cache PR #309.

## Evidence
Existing _history_sensitive_base fixture has legacy supported jointly by left_path/right_path, plus left_dependent and right_dependent supported separately. Revising in new against legacy using lexicographic produces:

- formal accepted: left_path, right_path, left_dependent, right_dependent, new;
- support incision: right_path;
- realized accepted: left_path, left_dependent, new;
- realized rejected: right_path, legacy, right_dependent.

realization.py:58 chooses the cut; stabilization applies it; _rebuild_base at line 358 removes rejected atom records and support records. Retaining just the formal OCF would preserve beliefs absent from the realized support base; rebuilding the ranking would repeat #306. Retaining vocabulary also requires retaining exact typed rejected atom/proof records, not just IDs or hashes.

## Pending semantic decision
The next formal step must either continue the exact operator-produced OCF independently of the support realization, or incorporate support cuts into that OCF under an explicitly chosen reconciliation operator. These differ for a real existing fixture. No source or tests written while this choice is open, following the delegation's explicit instruction to report policy choices before coding.

## Persistence constraint
Pinned belief-set SpohnEpistemicState is a frozen dataclass with mappingproxy ranks keyed by frozenset worlds. Quire to_document_builtins leaves that standalone object unchanged. Direct msgspec lowering/JSON encoding reports that mappingproxy is unsupported. Current snapshots copy through Quire/msgspec and hash JSON-ready data. The project forbids introducing a second Propstore spelling of the package state; dependency pin upgrades are also excluded by this assignment. A permitted package-owned persistence route must be settled before claiming snapshot/replay preservation.

## Next step
Parent to resolve the formal-versus-realized state policy and permitted persistence owner. Then implement the minimal sequential regression, retained vocabulary/ranking flow, snapshot/replay proof, and draft PR with terminal CI. Current action is pending a policy decision, not denied or uncertain. Only this note and isolated UV cache have been written; no source/test edits, dependency changes, or PR creation.
