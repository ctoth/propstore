# Ward Rules Signals Update

## GOAL
Add signal escape hatches to all blocking ward rules, add missing interpreter rules.

## KEY FINDING
- `session.signals.contains("x")` does NOT work — CEL "no such overload" error because session is typed as MapType(StringType, DynType), so .signals returns DynType and .contains() can't resolve
- `"x" in session.signals` DOES work — CEL `in` operator handles DynType correctly at runtime
- Go regex `signalRefRe` needed update to also match the `"x" in session.signals` pattern (for signal consumption)
- Fixed regex in guard.go, rebuilt, tests pass

## DONE
- [x] Go regex fix in guard.go (signalRefRe + signalsReferencedByRules)
- [x] Rebuilt ward.exe, tests pass
- [x] no-force-push.yaml updated and verified (deny without signal, allow with signal)
- [x] All 11 deny rules updated with signal checks (need to re-update 10 to use `in` syntax)
- [x] no-ruby-e.yaml and no-perl-e.yaml created

## REMAINING
- Re-update 10 rules to use `"x" in session.signals` instead of `.contains()`
  (no-force-push already uses correct syntax)
- Verify end-to-end again
- Commit ward repo changes
- Write report

## FILES
- C:/Users/Q/code/ward/guard.go — regex fix for signal extraction
- C:/Users/Q/.ward/rules/*.yaml — all deny rules getting signal escape hatches
