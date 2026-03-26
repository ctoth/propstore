# Fix 3C: CEL Tokenizer Unescape — Session Notes

## GOAL
Fix CEL tokenizer to unescape string literals after quote stripping.

## OBSERVATIONS
- Bug is at `propstore/cel_checker.py` line 175: `val = val[1:-1]` strips quotes but doesn't unescape `\"` or `\\`
- Test file is `tests/test_cel_checker.py` — has TestTokenizer class where new tests belong
- Tokenizer regex on line 148 correctly handles escaped chars in matching: `"(?:[^"\\]|\\.)*"`

## PLAN (TDD)
1. RED: Add failing test for escaped quotes in string literals
2. GREEN: Add unescape after quote stripping
3. Verify full suite passes
4. Commit

## STATUS
Starting RED phase.
