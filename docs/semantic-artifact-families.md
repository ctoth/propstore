# Semantic Artifact Families

Propstore canonical storage is artifact-shaped. Source-local authoring files may
be batch-shaped, but promotion must not carry that batch shape into master.

## Source-Local Batches

These files are source branch authoring state:

- `claims.yaml` as `SourceClaimsDocument`
- `justifications.yaml` as `SourceJustificationsDocument`
- `stances.yaml` as `SourceStancesDocument`
- `micropubs.yaml` as source composition state

They support ingestion, paper review, and source-local validation. They do not
define canonical artifact identity.

## Canonical Semantic Artifacts

Canonical/master storage uses one family artifact per semantic unit:

- `claim` stores one `ClaimDocument`
- `stance` stores one `StanceDocument`
- `justification` stores one `JustificationDocument`
- `micropublication` stores one `MicropublicationDocument`
- `same_as_assertion` stores one `SameAsAssertionDocument`

Sidecar compilation and verification read these first-class family artifacts
directly. They must not flatten entries hidden inside canonical bucket files.

## Intentional Sets

Rules and predicates remain file-shaped by design:

- `rules` is a source theory set. Its source block, ordered rules, and
  superiority relation are evaluated together.
- `predicates` is a Datalog schema set. Validation is defined over the
  declaration set, including duplicate checks and authored order.

The family registry records these as `aggregate_decision: intentional_set` with
the reason in contract metadata.

## Ownership Boundary

Quire owns schema-blind artifact mechanics: typed family stores, placements,
document codecs, canonical JSON, hashing, and contract manifests.

Propstore owns semantic identity: artifact id derivation, version payloads,
source-local field exclusion, cross-family verification, and source promotion.
