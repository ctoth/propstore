# May 28 Recovery Commit Checklist

Branch under construction: `recovery/may-28-curated-good`

Source stack: `recovery/may-28-local-stack`

Base: `origin/master`

Rule:
- Do not cherry-pick a commit unless a subagent report for that exact commit says `KEEP`.
- Use one subagent per commit.
- `KEEP`: cherry-pick that commit, then continue.
- `DROP`: skip that commit, then continue.
- `NEEDS-HUMAN-REVIEW`: stop.
- Do not batch cherry-picks.
- Do not classify commits locally as the deciding gate.
- Delete any branch created by this process if it is later determined bad.

Definition of `KEEP`:
- The commit removes an old wrong production surface, or moves behavior to the named owner without preserving the old representation under another spelling.
- Propstore semantic runtime uses typed family/domain objects.
- Quire owns generated document/schema/storage/boundary mechanics.
- Flat dicts and `document_to_payload` appear only at real IO/YAML/JSON/SQLite boundary tests or implementations.
- No helper, shim, adapter, fallback, payload bridge, or mapping-shaped replacement.
- No test blesses an old semantic flat mapping path.

Checklist:
- [ ] `8679fcd5` Delete first handwritten document classes
- [ ] `b6360532` Delete source handwritten document classes
- [ ] `dd30a90a` Delete merge handwritten document classes
- [ ] `8986193e` Delete rule handwritten document classes
- [ ] `5bf7c74c` Delete worldline handwritten document classes
- [ ] `00f8e721` Delete concept handwritten document classes
- [ ] `60662ca9` Delete claim handwritten document classes
- [ ] `ee781167` Remove Any from stance declaration
- [ ] `9e31e3cd` Delete concept document payload helper
- [ ] `03ed1b05` Document concept family ownership model
- [ ] `b81abf86` Delete concept staging surface
- [ ] `60b6b0d9` Remove concept stage reexports
- [ ] `bcd612ab` Move concept domain object to family declaration
- [ ] `93e3b115` Delete concept artifact payload callbacks
- [ ] `d085ea97` Add concept family document boundary
- [ ] `eb429378` Use concept domain objects in compiler context
- [ ] `e4f60bc3` Use concept domain objects in CEL registry
- [ ] `2005d416` Use concept domain objects for parameterization groups
- [ ] `9816307c` Move concept stage vocabulary to concept types
- [ ] `2a340754` Replace concept stage pipeline with domain pipeline
- [ ] `433376c7` Use concept domain objects in compiler workflows
- [ ] `8951d2ec` Remove concept stage wrappers from contracts
- [ ] `40439f9b` Use concept domain objects in compiler app
- [ ] `f11b50b3` Use concept domain objects in form app
- [ ] `fb2aaa67` Use concept domain objects in concept lifecycle
- [ ] `55663f0e` Use concept domain objects in grounding
- [ ] `293e1868` Use concept domain objects in form algebra
- [ ] `bd73b663` Use concept domain objects in source promotion
- [ ] `a6d2e13f` Use concept domain objects in claim app validation
- [ ] `a8601f3e` Use concept domain objects in concept mutation app
- [ ] `5f67d8a3` Remove stale merge document reexports
- [ ] `c105e188` Use source provenance document for micropublications
- [ ] `27fa3f6a` Use inline context reference for micropublications
- [ ] `c83e242f` Remove stale source alignment document reexports
- [ ] `6a3c569d` Remove stale worldline document reexports
- [ ] `932e3cab` Use concept domain objects in test context
- [ ] `5df7ebef` Use stance family document in claim compiler
- [ ] `6887c085` Use concept domain objects in family test helpers
- [ ] `60eda638` Remove stale claim variable binding document import
- [ ] `25de6544` Remove resolution document relation path
- [ ] `bbf56d8f` Add rule value objects to family owner
- [ ] `3182ae73` Use rule value objects in grounding translator
- [ ] `b20491c9` Remove source claim document dependency
- [ ] `3b21db28` Remove claim logical id document path
- [ ] `8d882fc7` Remove micropublication evidence document path
- [ ] `ab160625` Read claim mappings in grounding facts
- [ ] `540e8c87` Use rule value objects in rule app
- [ ] `1a3dc85d` Use rule value objects in extraction
- [ ] `0fc4f8c5` Remove rule source document from app
- [ ] `89a0fb37` Remove rule source document from lifecycle
- [ ] `8a44d670` Validate generated concept lexical entry
- [ ] `9a89a0c6` Read source claim source mappings
- [ ] `08ddb755` Read promoted claim source mapping
- [ ] `d6993a38` Read concept lexical entry mappings
- [ ] `81c8b0e4` Import concept identity normalizer
- [ ] `7af2382c` Derive concept domain fields from document
- [ ] `1f2ed3f5` Read source claim provenance mappings
- [ ] `6159cb36` Read form nested mappings
- [ ] `73249b46` Read claim source paper mappings
- [ ] `6ab19d6e` Read claim file source mappings
- [ ] `ea7888c8` Read logical id reference mappings
- [ ] `de888f79` Encode provenance named graphs as mappings
- [ ] `715bb466` Read claim provenance mappings in lints
- [ ] `4e600cf8` Read claim context mappings
- [ ] `62770eae` Group parameterizations from concept registry
- [ ] `93ad6b96` Read micropublication context mappings
- [ ] `e6b9f2c3` Read promoted claim source mappings in test
- [ ] `e16581fe` Assert generated source document payloads
- [ ] `84da382d` Pass concept records to merge preview test
- [ ] `7edf932d` Update semantic contract manifest
- [ ] `75fead00` Read repository config as mapping
- [ ] `fd4cd261` Narrow parameterization registry payloads
- [ ] `bb8c6d2f` Remove form alternative document imports
- [ ] `0ba2c031` Type predicates through declaration interface
- [ ] `2e3400ab` Use mapping fields for concept alignment artifacts
- [ ] `c06353a3` Read worldline nested fields as mappings
- [ ] `3f84e832` Use concept entries in concept views
- [ ] `7f7f0274` Remove stale concept stages remediation test
- [ ] `f2a2e1c5` Use concept domain objects in grounding facts tests
- [ ] `37fd0fb3` Use domain rule and concept objects in gunray tests
- [ ] `8d73559f` Use concept domain objects in CEL checker tests
- [ ] `d5845d83` Use generated concept mappings in lemon tests
- [ ] `f865a505` Load git concepts through generated documents
- [ ] `d02105de` Load validator concepts through generated documents
