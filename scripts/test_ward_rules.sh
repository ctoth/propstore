#!/usr/bin/env bash
# Test script for ward rules
# Tests every rule in ~/.ward/rules/ for correct firing

set -uo pipefail

CWD="C:/Users/Q/code/propstore"
PASS=0
FAIL=0
RESULTS=""

add_result() {
  local rule="$1" testcase="$2" expected="$3" actual="$4" verdict="$5"
  RESULTS="${RESULTS}| ${rule} | ${testcase} | ${expected} | ${actual} | ${verdict} |\n"
  if [ "$verdict" = "PASS" ]; then
    ((PASS++))
  else
    ((FAIL++))
  fi
}

# Helper: run ward eval on a JSON string, capture combined output
run_ward() {
  echo "$1" | ward eval 2>&1 || true
}

# Helper: check if output contains a deny/context message
has_output() {
  [ -n "$1" ]
}

echo "=== Testing ward rules ==="

# ---------------------------------------------------------------
# 1. no-python-c.yaml
# ---------------------------------------------------------------
echo "Testing no-python-c..."

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"python -c \"print(1)\""},"session_id":"test-pyc-1","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-python-c" "python -c (deny)" "deny" "deny" "PASS"
else
  add_result "no-python-c" "python -c (deny)" "deny" "allow" "FAIL"
fi

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"python3 -c \"import os\""},"session_id":"test-pyc-2","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-python-c" "python3 -c (deny)" "deny" "deny" "PASS"
else
  add_result "no-python-c" "python3 -c (deny)" "deny" "allow" "FAIL"
fi

# Use /tmp (no pyproject.toml) so uv-not-python doesn't also fire
OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"python scripts/foo.py"},"session_id":"test-pyc-3","cwd":"/tmp"}')
if has_output "$OUT"; then
  add_result "no-python-c" "python scripts/foo.py (allow)" "allow" "deny" "FAIL"
else
  add_result "no-python-c" "python scripts/foo.py (allow)" "allow" "allow" "PASS"
fi

# ---------------------------------------------------------------
# 2. uv-not-python.yaml
# ---------------------------------------------------------------
echo "Testing uv-not-python..."

# In propstore dir (has pyproject.toml) — bare python should deny
OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"python scripts/foo.py"},"session_id":"test-uv-1","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "uv-not-python" "bare python w/ pyproject (deny)" "deny" "deny" "PASS"
else
  add_result "uv-not-python" "bare python w/ pyproject (deny)" "deny" "allow" "FAIL"
fi

# uv run python should allow
OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"uv run python scripts/foo.py"},"session_id":"test-uv-2","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "uv-not-python" "uv run python (allow)" "allow" "deny" "FAIL"
else
  add_result "uv-not-python" "uv run python (allow)" "allow" "allow" "PASS"
fi

# In /tmp (no pyproject.toml) — bare python should allow
OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"python scripts/foo.py"},"session_id":"test-uv-3","cwd":"/tmp"}')
if has_output "$OUT"; then
  add_result "uv-not-python" "bare python no pyproject (allow)" "allow" "deny" "FAIL"
else
  add_result "uv-not-python" "bare python no pyproject (allow)" "allow" "allow" "PASS"
fi

# ---------------------------------------------------------------
# 3. no-git-stash.yaml
# ---------------------------------------------------------------
echo "Testing no-git-stash..."

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git stash"},"session_id":"test-stash-1","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-git-stash" "git stash (deny)" "deny" "deny" "PASS"
else
  add_result "no-git-stash" "git stash (deny)" "deny" "allow" "FAIL"
fi

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git stash pop"},"session_id":"test-stash-2","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-git-stash" "git stash pop (deny)" "deny" "deny" "PASS"
else
  add_result "no-git-stash" "git stash pop (deny)" "deny" "allow" "FAIL"
fi

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git status"},"session_id":"test-stash-3","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-git-stash" "git status (allow)" "allow" "deny" "FAIL"
else
  add_result "no-git-stash" "git status (allow)" "allow" "allow" "PASS"
fi

# ---------------------------------------------------------------
# 4. no-git-add-all.yaml
# ---------------------------------------------------------------
echo "Testing no-git-add-all..."

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git add ."},"session_id":"test-addall-1","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-git-add-all" "git add . (deny)" "deny" "deny" "PASS"
else
  add_result "no-git-add-all" "git add . (deny)" "deny" "allow" "FAIL"
fi

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git add -A"},"session_id":"test-addall-2","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-git-add-all" "git add -A (deny)" "deny" "deny" "PASS"
else
  add_result "no-git-add-all" "git add -A (deny)" "deny" "allow" "FAIL"
fi

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git add --all"},"session_id":"test-addall-3","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-git-add-all" "git add --all (deny)" "deny" "deny" "PASS"
else
  add_result "no-git-add-all" "git add --all (deny)" "deny" "allow" "FAIL"
fi

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git add specific-file.py"},"session_id":"test-addall-4","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-git-add-all" "git add specific-file.py (allow)" "allow" "deny" "FAIL"
else
  add_result "no-git-add-all" "git add specific-file.py (allow)" "allow" "allow" "PASS"
fi

# ---------------------------------------------------------------
# 5. no-git-reset-hard.yaml
# ---------------------------------------------------------------
echo "Testing no-git-reset-hard..."

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git reset --hard"},"session_id":"test-reset-1","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-git-reset-hard" "git reset --hard (deny)" "deny" "deny" "PASS"
else
  add_result "no-git-reset-hard" "git reset --hard (deny)" "deny" "allow" "FAIL"
fi

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git reset --hard HEAD~1"},"session_id":"test-reset-2","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-git-reset-hard" "git reset --hard HEAD~1 (deny)" "deny" "deny" "PASS"
else
  add_result "no-git-reset-hard" "git reset --hard HEAD~1 (deny)" "deny" "allow" "FAIL"
fi

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git reset --soft HEAD~1"},"session_id":"test-reset-3","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-git-reset-hard" "git reset --soft (allow)" "allow" "deny" "FAIL"
else
  add_result "no-git-reset-hard" "git reset --soft (allow)" "allow" "allow" "PASS"
fi

# ---------------------------------------------------------------
# 6. no-force-push.yaml
# ---------------------------------------------------------------
echo "Testing no-force-push..."

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git push --force"},"session_id":"test-fpush-1","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-force-push" "git push --force (deny)" "deny" "deny" "PASS"
else
  add_result "no-force-push" "git push --force (deny)" "deny" "allow" "FAIL"
fi

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git push origin master --force"},"session_id":"test-fpush-2","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-force-push" "git push origin master --force (deny)" "deny" "deny" "PASS"
else
  add_result "no-force-push" "git push origin master --force (deny)" "deny" "allow" "FAIL"
fi

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git push"},"session_id":"test-fpush-3","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-force-push" "git push (allow)" "allow" "deny" "FAIL"
else
  add_result "no-force-push" "git push (allow)" "allow" "allow" "PASS"
fi

# ---------------------------------------------------------------
# 7. no-tskill.yaml
# ---------------------------------------------------------------
echo "Testing no-tskill..."

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"tskill node.exe"},"session_id":"test-tskill-1","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-tskill" "tskill node.exe (deny)" "deny" "deny" "PASS"
else
  add_result "no-tskill" "tskill node.exe (deny)" "deny" "allow" "FAIL"
fi

OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"ls"},"session_id":"test-tskill-2","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "no-tskill" "ls (allow)" "allow" "deny" "FAIL"
else
  add_result "no-tskill" "ls (allow)" "allow" "allow" "PASS"
fi

# ---------------------------------------------------------------
# 8. flailing-reads.yaml
# ---------------------------------------------------------------
echo "Testing flailing-reads..."

# Build up 5 Read events in session, then 6th should trigger
SID="test-flailing-1"
for i in 1 2 3 4 5; do
  run_ward '{"hook_event_name":"PreToolUse","tool_name":"Read","tool_input":{"file_path":"/tmp/file'$i'.py"},"session_id":"'"$SID"'","cwd":"'"$CWD"'"}' > /dev/null
done

# 6th Read should trigger context message
OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Read","tool_input":{"file_path":"/tmp/file6.py"},"session_id":"'"$SID"'","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "flailing-reads" "6th consecutive Read (context)" "context" "context" "PASS"
else
  add_result "flailing-reads" "6th consecutive Read (context)" "context" "allow" "FAIL"
fi

# Reset by piping a Bash event, then Read should NOT trigger
SID2="test-flailing-2"
for i in 1 2 3 4 5; do
  run_ward '{"hook_event_name":"PreToolUse","tool_name":"Read","tool_input":{"file_path":"/tmp/file'$i'.py"},"session_id":"'"$SID2"'","cwd":"'"$CWD"'"}' > /dev/null
done
# Bash event resets the streak
run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"echo hello"},"session_id":"'"$SID2"'","cwd":"'"$CWD"'"}' > /dev/null
# Next Read should NOT trigger
OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Read","tool_input":{"file_path":"/tmp/file7.py"},"session_id":"'"$SID2"'","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "flailing-reads" "Read after Bash reset (allow)" "allow" "context" "FAIL"
else
  add_result "flailing-reads" "Read after Bash reset (allow)" "allow" "allow" "PASS"
fi

# ---------------------------------------------------------------
# 9. uncommitted-edits.yaml
# ---------------------------------------------------------------
echo "Testing uncommitted-edits..."

SID3="test-uncommitted-1"
# 2 Edit events
run_ward '{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"file_path":"/tmp/a.py","old_string":"x","new_string":"y"},"session_id":"'"$SID3"'","cwd":"'"$CWD"'"}' > /dev/null
run_ward '{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"file_path":"/tmp/b.py","old_string":"x","new_string":"y"},"session_id":"'"$SID3"'","cwd":"'"$CWD"'"}' > /dev/null

# 3rd Edit should trigger context message
OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"file_path":"/tmp/c.py","old_string":"x","new_string":"y"},"session_id":"'"$SID3"'","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "uncommitted-edits" "3rd Edit no commit (context)" "context" "context" "PASS"
else
  add_result "uncommitted-edits" "3rd Edit no commit (context)" "context" "allow" "FAIL"
fi

# Now test with commit reset
SID4="test-uncommitted-2"
run_ward '{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"file_path":"/tmp/a.py","old_string":"x","new_string":"y"},"session_id":"'"$SID4"'","cwd":"'"$CWD"'"}' > /dev/null
run_ward '{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"file_path":"/tmp/b.py","old_string":"x","new_string":"y"},"session_id":"'"$SID4"'","cwd":"'"$CWD"'"}' > /dev/null
# git commit resets counter (using _commit sentinel)
run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git commit -m \"test\""},"session_id":"'"$SID4"'","cwd":"'"$CWD"'"}' > /dev/null
# Next Edit should NOT trigger
OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"file_path":"/tmp/d.py","old_string":"x","new_string":"y"},"session_id":"'"$SID4"'","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "uncommitted-edits" "Edit after commit reset (allow)" "allow" "context" "FAIL"
else
  add_result "uncommitted-edits" "Edit after commit reset (allow)" "allow" "allow" "PASS"
fi

# ---------------------------------------------------------------
# 10. Shell AST parsing: false positive prevention
# ---------------------------------------------------------------
echo "Testing shell AST parsing (false positives)..."

# Heredoc: "python -c" in commit message heredoc should NOT trigger
OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git commit -m \"python -c is forbidden\""},"session_id":"test-ast-1","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "ast-parsing" "python -c in commit msg (allow)" "allow" "deny" "FAIL"
else
  add_result "ast-parsing" "python -c in commit msg (allow)" "allow" "allow" "PASS"
fi

# echo with "git stash" in args should NOT trigger no-git-stash
OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"echo \"git stash is bad\""},"session_id":"test-ast-2","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "ast-parsing" "echo git stash in args (allow)" "allow" "deny" "FAIL"
else
  add_result "ast-parsing" "echo git stash in args (allow)" "allow" "allow" "PASS"
fi

# python -c in pipe chain SHOULD trigger
OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"echo foo | python -c \"import sys\""},"session_id":"test-ast-3","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "ast-parsing" "python -c in pipe (deny)" "deny" "deny" "PASS"
else
  add_result "ast-parsing" "python -c in pipe (deny)" "deny" "allow" "FAIL"
fi

# python -c in && chain SHOULD trigger
OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"cd /tmp && python -c \"print(1)\""},"session_id":"test-ast-4","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "ast-parsing" "python -c in && chain (deny)" "deny" "deny" "PASS"
else
  add_result "ast-parsing" "python -c in && chain (deny)" "deny" "allow" "FAIL"
fi

# git stash in && chain SHOULD trigger
OUT=$(run_ward '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"cd /tmp && git stash"},"session_id":"test-ast-5","cwd":"'"$CWD"'"}')
if has_output "$OUT"; then
  add_result "ast-parsing" "git stash in && chain (deny)" "deny" "deny" "PASS"
else
  add_result "ast-parsing" "git stash in && chain (deny)" "deny" "allow" "FAIL"
fi

# ---------------------------------------------------------------
# Cleanup session state
# ---------------------------------------------------------------
echo "Cleaning up session state..."
rm -f /tmp/ward-session-test-* 2>/dev/null || true

# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------
echo ""
echo "=== Results ==="
echo "PASS: $PASS  FAIL: $FAIL  TOTAL: $((PASS + FAIL))"
echo ""

# Write report
mkdir -p "$CWD/reports"
cat > "$CWD/reports/ward-rules-test-report.md" << REPORT_EOF
# Ward Rules Test Report

Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Summary

- **PASS:** $PASS
- **FAIL:** $FAIL
- **TOTAL:** $((PASS + FAIL))

## Results

| Rule | Test Case | Expected | Actual | PASS/FAIL |
|------|-----------|----------|--------|-----------|
$(echo -e "$RESULTS")

## Rules Tested

1. **no-python-c.yaml** - Denies \`python -c\` and \`python3 -c\`
2. **uv-not-python.yaml** - Denies bare python when pyproject.toml exists
3. **no-git-stash.yaml** - Denies \`git stash\`
4. **no-git-add-all.yaml** - Denies \`git add .\`, \`git add -A\`, \`git add --all\`
5. **no-git-reset-hard.yaml** - Denies \`git reset --hard\`
6. **no-force-push.yaml** - Denies \`git push --force\`
7. **no-tskill.yaml** - Denies \`tskill\`
8. **flailing-reads.yaml** - Context after 5+ consecutive Read/Glob/Grep calls
9. **uncommitted-edits.yaml** - Context after 2+ Edit/Write calls without commit
10. **ast-parsing** - Shell AST parsing prevents false positives (heredoc, string args, pipe/chain detection)
REPORT_EOF

echo "Report written to $CWD/reports/ward-rules-test-report.md"
