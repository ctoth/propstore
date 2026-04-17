# Justifiable Exceptions

Propstore implements WS-C defeasibility as CKR-style contextual exceptions plus ASPIC+ structural argumentation.

## Layer Boundary

`propstore.defeasibility` answers whether a contextual claim use is excepted:

```text
ist(context, claim)
```

The exception layer owns:

- `JustifiableException`: target claim, CEL exception pattern, justification claims, context, `SupportEvidence`, and decidability status.
- `evaluate_contextual_claim(...)`: local-or-lifted exception applicability over live support.
- `apply_exception_defeats_to_csaf(...)`: CKR-derived defeat injection into an existing ASPIC+ CSAF.

ASPIC+ owns:

- recursive argument construction from premises and rules;
- attack construction;
- preference filtering over authored strict partial orders;
- Dung framework construction.

Datalog grounding owns:

- rule/fact substitution through gunray;
- four-valued grounded sections;
- preservation of authored rule superiority into the grounded rule surface.

## Applicability

An exception applies only when all of these hold:

- its `target_claim` is the contextual claim being evaluated;
- it is local to the target context, or an explicit `LiftingRuleSupport` licenses lifting from the exception context to the target context;
- it has at least one `justification_claim`;
- its live support is non-zero after solver nogood filtering;
- its CEL `exception_pattern` selects the concrete `ContextualClaimUse` bindings.

Missing bindings, CEL translation failures, and solver unknowns produce `ClaimApplicability.UNKNOWN` with `DecidabilityStatus.INCOMPLETE_SOUND`. They are not treated as positive exceptions.

## Support

Exceptions and exception defeats carry `SupportEvidence`, not dictionaries or source strings. Lifting multiplies support:

```text
lifted_exception_support = exception_support * lifting_rule_support
```

Solver nogoods live-filter support without deleting the exception object.

## ASPIC+ Integration

`apply_exception_defeats_to_csaf(...)` does not rebuild ASPIC+ arguments. It takes a CSAF that ASPIC+ already built, finds arguments concluding each exception justification claim, finds arguments concluding the excepted target claim, and adds Dung defeat/attack edges from justification arguments to target arguments.

If the CSAF has no argument for an applied exception's target or justification claims, integration raises. That is a malformed boundary state: CKR has produced a semantic exception result that ASPIC+ cannot represent structurally.

## Verification

The implemented contracts are pinned by:

- `tests/test_defeasibility_support_contract.py`
- `tests/test_defeasibility_satisfaction.py`
- `tests/test_defeasibility_aspic_integration.py`
- `tests/test_aspic_bridge.py::TestBridgeRationalityPostulates`
