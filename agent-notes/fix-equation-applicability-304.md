# Equation applicability (#304)

## Goal
Retain canonical equation identity through runtime parameterizations, use its
activation decision, and require equation support in ATMS. One draft PR, no merge.

## State
Isolated branch fix/equation-applicability-304 based on da0b48b4. No user checkout
changes. No overlapping open PR was found before implementation.
Published draft PR: https://github.com/ctoth/propstore/pull/310.
Implementation commit 87633611623d3c2d511cb54a4b640dc05b8e7be0 passed full CI:
https://github.com/ctoth/propstore/actions/runs/39340784072.

## Decisions and why
Smallest fix: add an equation claim reference to ParameterizationEdge, populate
it in derive_parameterizations, consume BoundWorld.is_active, and make the ATMS
equation node an antecedent. Approximately 46 added production lines, plus tests.
The existing context/condition/activation owner remains canonical; no copied
scope, new activation policy or storage filter. Bare graph-native parameterization
edges still work as before; the repository-derived edge always names its claim.

The cleanup-refactor ownership checks apply to this boundary repair. The broken
dependency edge is a valid runtime capability with a representation missing the
canonical claim reference. Disposition: rewrite to the typed owner interface.
Keep graph topology, canonical claim, activation, solver and all runtime consumers.
No production file deletion or feature removal is required. Source storage and
the complete parameterization inventory remain intact. Stable graph sorting must
include origin and tolerate bare edges alongside claim-derived edges.

DerivedResult retains the selected equation ID so ordinary support includes the
equation, too. Complete evidence for rival derivations remains the separate #156.

## Surprises
The initial fixture triggered existing #154 (claim-value selection depends on
claim ordering); input sorts before equations in this bounded regression. Initial
CEL fixtures omitted typed concept forms, and raw authored conditions do not
create the checked IR activation consumes. The regression now declares real
quantity forms/lemon entries and supplies explicitly checked equation conditions.
No changes were made to those separate owners.

#142's existing conditional-lifting input issue remains outside this fix. The
gated lift uses a valid literal true condition, but without the solver input the
canonical lifting owner reports UNKNOWN; the equation must stay inactive.

The focused logged regression run passed 12 tests in 18.32 seconds:
logs/test-runs/issue-304-20261019-171634.log. Both backends exercise canonical
repository -> sidecar -> WorldQuery.bind. Coverage includes same-context use,
unrelated contexts, unconditional lift, undecided conditional lift, preserved
rival origins/scopes, missing referenced equation, mixed edge sorting, sensitivity,
and equation-condition applicability/support. Only this actively authored file
was run locally with uv --no-sync and the existing environment.

## Slice completion
The sole production ParameterizationEdge constructor (world/queries.py) now
retains the canonical claim ID. Compatibility uses BoundWorld.is_active and ATMS
uses its existing equation node. No competing context/condition owner was added.
The ordinary result retains that origin to compose its equation support label.
Existing standalone graph edges and all storage/query inventories remain usable.

## Parser-restoration integration
Merged default 62d4e3ad48717d793383dcf4fba2e8ce16b4a10c (PR308 parser
restoration) without conflicts or production edits. claim_contracts.py and the
restored test_algorithm_parse_admission.py exactly match that default commit.
The focused integration run passed 18 tests in 17.15 seconds:
logs/test-runs/issue-304-integrate-308-20261019-172630.log. The merge commit
will receive fresh full PR CI. Neither #310 nor #307 depends on the other;
each independently integrates the same default restoration.

## Combined ATMS/equation integration
The parent merged PR307 as dac0a7262dfddc455d0367d6ad45c644a100a80f.
Merged that default into this branch without conflicts or production edits.
Parser restoration and the ATMS classification regression exactly match default.
Added one bounded repository-backed regression in the existing equation test file:
context-separated parameter claims coexist without nogoods while the derived
value retains its equation's contextual support in the same ATMS engine.

The three combined regression files passed 27 tests in 23.13 seconds:
logs/test-runs/core-pairing-307-310-20261019-173215.log. Push this merge commit
for fresh full CI; the parent chooses subsequent merge order. Do not fetch/merge
later default changes automatically, including the unrelated PR309 cache work.

## Next step
Keep PR #310 in draft; do not merge or mark ready. This documentation update
records the completed implementation and terminal CI result. No implementation
work remains for #304. Related #142, #154 and #156 remain separate work; this
fix does not claim to close them.
