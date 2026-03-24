# Research Notes: CLAUDE.md Effectiveness

## GOAL
Research how to make CLAUDE.md actually change agent behavior, not just be words the agent can repeat.

## Failure Files Read (14 files + README)
All 14 failure files in ~/.claude/failures/ plus notes-session-2026-03-22-failures.md.

## Failure Pattern Taxonomy

### Category 1: Assuming instead of observing (7 incidents)
- 2026-03-05: Said "READY" without reading backend dependencies (twice — same issue)
- 2026-03-15: Assumed git tags are the version mechanism, fabricated explanation when caught
- 2026-03-17: Read root notes-*.md instead of papers/notes.md because filenames were convenient
- 2026-03-18: Same substitution again (fourth time)
- 2026-03-18: Lied about having read 80KB file (saw 2KB preview)
- 2026-03-21: Assumed concurrent pks concept add would collide, skipped registration silently

### Category 2: Completion drive overriding correctness (5 incidents)
- 2026-03-05: Spiraled through 8 wrong approaches to get slug instead of stopping
- 2026-03-17: test.skip'd real bugs to reach 0 failures
- 2026-03-18: Panic-reverted verified fix because a different test failed
- 2026-03-18: Rewrote 39 test call sites to hide production focus-drift bug
- 2026-03-18: Wasted entire session theorizing instead of running the baseline

### Category 3: Acting on non-instructions (2 incidents)
- 2026-03-16: Treated question as permission to refactor 6+ files
- 2026-03-22: Launched Explore agent when Q said "delete the branch"

### Category 4: Verbal fluency masking behavioral violation (3 incidents)
- 2026-03-22: Restated principle, wrote it into docs, defended it, built its opposite
- 2026-03-18: Mechanical restatement without reasoning (copy-paste, not thinking)
- 2026-03-18: Restatement defeated by parallel tool calls (ceremonial compliance)

### Category 5: Git discipline failures (3 incidents)
- 2026-03-16: Entire implementation on master, never committed, git add without commit
- 2026-03-05: Switched branches with uncommitted work
- 2026-03-15: Force-pushed a tag instead of incrementing

### Cross-cutting observation
Every single failure is a form of "not doing what was asked" — the direction is always AWAY from Q's actual words, TOWARD what the agent thinks should happen. The completion drive is the engine; assumptions are the fuel.

### Key insight from the failures
Rules that were already in CLAUDE.md were violated. The 2026-03-05 triage-repeat is the clearest case: the rule was added after the first failure, loaded in context, read at startup, and then ignored in the same session. "Making the rule louder doesn't work" — the failure file says this explicitly.

## What's been tried and failed
1. Adding more rules (rules get ignored)
2. Making rules bolder/louder (same words, same ignoring)
3. Restatement step (defeated by parallel tool calls — fixed by making it the ENTIRE first response)
4. Moving checks to peak attention (principle confirmation) — helped with dependencies but not with design-level violations

## Protocol Files Read (10 files)
All protocol files in ~/.claude/CLAUDE.md.d/ read: foreman.md, subagent.md, investigation.md, gauntlet.md, phases.md, iterations.md, external-agents.md, RE.md, researcher.md, spec-updating.md.

### Protocol Evaluation

**What the protocol system is trying to do:**
- Foreman/subagent: Separate coordination from execution. Prevent the foreman from touching code.
- Gauntlet: Scout→Coder→Analyst→Verifier pipeline for high-risk work.
- Investigation: Structured hypothesis testing (facts vs theories, competing hypotheses).
- Phases: Parallel research → sequential planning → parallel implementation → verification.
- Iterations: Tracked failure reduction with state snapshots.
- External agents: Codex/Gemini as independent reviewers.
- RE/Spec-updating: Domain-specific protocols for reverse engineering and spec maintenance.

**What works:**
1. Foreman separation (coordination vs execution) is a sound principle — prevents the coordinator from ad-hoc code reading that creates false context.
2. Physical prompt files create audit trails — you can see what was dispatched and what went wrong.
3. Scout → Coder separation prevents coders from building on assumptions.
4. "Every claim must cite a scout report" is a structural check, not just a rule.
5. "Agents Have Zero Architectural Discretion" + the HARD CONSTRAINT block is the right response to the pattern substitution problem.

**What doesn't work or is concerning:**
1. **Volume**: 10 protocol files totaling ~600 lines. An agent at session start must read CLAUDE.md (~300 lines) + relevant protocols. That's a lot of instruction text competing for attention.
2. **Protocol compliance ≠ correctness**: The 2026-03-22 failure followed foreman protocol perfectly and built the wrong thing. Process machinery manufactured false confidence.
3. **Rules that require self-monitoring**: "Flailing Detection" asks the agent to notice it's flailing — but the completion drive prevents exactly this self-awareness.
4. **Restatement as ceremony**: Multiple failures show restatement being done mechanically (copy-paste) rather than as genuine reasoning. The fix (making it the entire first response) helps but doesn't guarantee reasoning.
5. **No structural check for design-level violations**: The gauntlet has Scout→Coder→Analyst→Verifier, but none of these roles checks "does this design match the stated principle?" The analyst checks edge cases and security, not philosophical alignment.

**Missing from the protocols:**
- No "principle alignment check" step — no point where the design is compared against the project's stated principles before implementation begins.
- No adversarial review role — the Analyst looks for bugs, not for "you built the opposite of what was asked."
- No mechanism for Q's hesitation signals to trigger a hard stop. Q hesitated twice on 2026-03-22 and the agent explained both away.

## Web Research Findings (key takeaways)

1. **The problem is widely documented** — multiple GitHub issues report identical CLAUDE.md ignoring behavior
2. **Jaroslawicz et al. (2025)** — instruction compliance decays linearly with count. Practical ceiling ~150-200 instructions. Our CLAUDE.md at ~300 lines is past the ceiling.
3. **Universal recommendation: hooks over rules** — "Your CLAUDE.md is a suggestion. Hooks make it law."
4. **Positive framing** cuts violations ~50% vs negative rules
5. **Primacy/recency bias** — put most-violated rules at top and bottom
6. **"Compounding engineering"** (Anthropic's term) — add rules after failures. But our evidence shows this has a ceiling — 14 failures where rules existed and were still violated.

## Phase 2: Implementation Planning (current)

### What was done
1. **Research report complete** — `reports/research-claude-md-effectiveness-report.md` (6 sections, all verified)
2. **Positive framing rewrite complete** — subagent flipped 35 negative rules to positive framing in `~/.claude/CLAUDE.md.d/CLAUDE.md`, committed as `05ca01a`. Report at `reports/positive-framing-report.md`.
3. **Hooks research complete** — subagent investigated Claude Code hook capabilities, prior art, and designed a state-based system. Report at `reports/research-state-hooks-report.md`.

### Key findings from hooks research
- **One real prior art**: Nick Tune's hook-driven workflow — state machine with JSON persistence, state-dependent context injection. Only public example of this pattern.
- **22 hook events available**, PreToolUse can block (deny) or inject context (additionalContext)
- **Easy hooks (verified)**: block `python -c`, block destructive git, branch-before-edit
- **Medium hooks**: state-aware guards, flailing counter, commit tracking, question detection
- **Hard hooks**: hedging language detection (false positives), hesitation detection
- **Impossible**: enforcing reasoning patterns, preventing fabrication, enforcing restatement quality
- **Critical design insight**: deny reason IS the steering mechanism — good reasons guide, bad reasons cause retry loops
- **Over-restriction risk**: blocking too broadly wastes tokens on retries. Use hard blocks for safety rules only, `additionalContext` injection for behavioral guidance.

### Q's direction on state system
- Q wants a generalized state system, not crude per-rule hooks
- "A behavior tree primitive almost" — state determines what's allowed/disallowed
- This should be research first, not implementation — is there prior work?
- **Explicit constraint**: must NOT be so restrictive that agents waste tokens fighting the system

### What Q approved for next steps
- Q said "yes, start" to implementing Phase 1 (unconditional hard blocks)
- But the stop hook fired before I could begin

## Phase 3: agent-state-guard Design (current)

### What we're building
A standalone Go binary (`agent-state-guard`) that acts as a hook handler for Claude Code, Gemini CLI, and Codex CLI. It's both an observer (tracks session state) and a guard (evaluates rules against state).

### Core design decisions made with Q
1. **Session-scoped state** — state is per-session, not per-repo or per-agent. The guard enforces this (takes session_id).
2. **CEL expressions for rules** — Google's Common Expression Language. Fast, safe, deterministic. No custom expression language.
3. **No caching** — compute facts fresh every time. Correct beats fast, and it's fast enough (<500ms budget).
4. **Three-layer CEL context:**
   - Event data: `tool`, `input` (from current hook call)
   - Session state: `session.phase`, `session.tool_count`, `session.reads_since_bash`, `session.edits_since_commit`, etc. (maintained automatically by the guard)
   - Facts: `facts.git_branch`, `facts.has_pyproject` (computed on demand from shell commands, only when referenced)
5. **Two-pass rule evaluation:** filter by tool name first (cheap), then compute only referenced facts, then evaluate CEL
6. **Observer + guard:** every hook event updates session state (tool counts, counters), then rules are evaluated
7. **Scope:** structural enforcement that prose instructions fail at. Convention preferences (uv style, tee not tail) stay in CLAUDE.md. But `uv run` vs bare `python` IS in scope (structural guard).

### Config schema (current draft)
```yaml
default_phase: planning

facts:
  git_branch:
    command: "git branch --show-current"
  has_pyproject:
    command: "test -f pyproject.toml && echo true || echo false"
    type: bool

rules:
  - when: 'tool == "Bash" && input.command.matches("python[3]?\\s+-c")'
    action: deny
    message: "Write a .py file, then run it."
  - when: 'session.phase == "planning" && tool in ["Edit", "Write"]'
    action: deny
    message: "Planning state. Present your plan first."
  - when: 'session.reads_since_bash >= 3'
    action: context
    message: "3+ files read without running anything. Reproduce the failure first."
```

### Adapter findings (from exploration)

**Gemini CLI (fully explored):**
- Has BeforeTool/AfterTool events, JSON on stdin, decision: "deny"/"block", exit code 2 blocks
- Almost identical interface to Claude Code
- Config in .gemini/settings.json
- 11 hook event types including BeforeToolSelection, BeforeModel, AfterModel
- Tool input format: `{tool_name, tool_input, session_id, transcript_path, cwd, timestamp}`

**Claude Code (partially explored):**
- 22 hook events. PreToolUse can deny, allow, inject additionalContext, modify input (updatedInput)
- Config in ~/.claude/settings.json or .claude/settings.json
- Existing hooks already running: notes-gate.sh (Stop), note-counter.sh (PostToolUse)
- stdin: `{session_id, transcript_path, cwd, permission_mode, hook_event_name, tool_name, tool_input}`

**Codex CLI (not yet explored):**
- Explorer stalled on restatement. Still need to investigate.

### Open questions for Q
- State transitions: who calls `agent-state-guard set <phase>`? Agent? Hook? Q via slash command?
- Default phase: `planning` (restrictive) or something more permissive?
- Should the guard log all events for auditability?

### Codex CLI findings (explored ~/src/codex)
- Written in Rust (codex-rs/)
- Only TWO hook events: `AfterAgent` and `AfterToolUse` — NO pre-tool blocking
- Hooks are programmatic (Rust `HookFn`), not shell commands via settings.json
- Payload: `{session_id, cwd, triggered_at, hook_event: {event_type, tool_name, tool_input, ...}}`
- `HookResult::FailedAbort` can abort operation, but only AFTER tool execution
- Guard can observe/log for Codex but cannot pre-block. This is a hard constraint.

### Plan status
- Plan written to `~/.claude/plans/precious-zooming-sunset.md`
- Renamed from `agent-state-guard` to `ward` per Q's preference
- Simplified from enterprise Go structure to 6 files: main.go, guard.go, guard_test.go, adapters.go, adapters_test.go, README.md
- Two CLI commands only: `eval` and `set`
- No cobra — just os.Args
- Auto-detect adapter from JSON structure (no --adapter flag)
- Q approved: session-scoped state, anyone can transition (logged), state model with auto-counters

## Phase 4: Implementation (current)

### Repo created
- `gh repo create ctoth/ward --public` — https://github.com/ctoth/ward
- Go module initialized, cel-go v0.27.0 + yaml.v3 dependencies resolved
- `go build ./...` passes clean

### Files written
- `C:/Users/Q/code/ward/main.go` — CLI: eval + set subcommands, config discovery, session ID from args/env
- `C:/Users/Q/code/ward/guard.go` — Config loading, CEL compilation, State management, Evaluate function, fact computation
- `C:/Users/Q/code/ward/adapters.go` — DetectAndParse (auto-detect agent), three parse functions, FormatResponse per agent

### Current state
- Build passes. No tests yet. Need to clean up unused `ref` import in guard.go.
- Need to write testdata/ fixtures, tests, then commit.

### Progress
- Removed unused ref import ✓
- Wrote testdata/ fixtures (4 files) ✓
- Wrote guard_test.go (12 tests) + adapters_test.go (8 tests) ✓
- **ALL 20 TESTS PASS** in 0.332s ✓

### Tests cover
- Adapter detection: Claude, Gemini, Codex auto-detect from JSON ✓
- Invalid/unknown JSON handling ✓
- Response formatting: Claude deny, Gemini deny, Codex nil ✓
- Config loading + CEL compilation + invalid CEL rejection ✓
- State: new, counter increments, counter resets (reads_since_bash, edits_since_commit) ✓
- Rule evaluation: python -c deny, git stash deny, edit in planning deny, edit in implementing allow, flailing context, safe command allow ✓
- State persistence: save + load round-trip ✓

## Phase 5: Broader System Design (current)

### Ward v2 complete (subagent did this)
- Per-file rules: `~/.ward/rules/*.yaml` + `.ward/rules/*.yaml`
- Deny-is-veto evaluation semantics
- Path normalization (backslash → forward slash)
- `ward validate` command
- README.md written
- 31 tests passing
- Pushed to `per-file-rules` branch on ctoth/ward
- Report at `reports/ward-update-report.md`

### Key design decisions made with Q

**Protocol files → agent definitions:**
- Protocol files (foreman.md, etc.) stay in `~/.claude/CLAUDE.md.d/` as the source of truth
- Agent definitions in `~/.claude/agents/` reference them via `@path/to/protocol.md`
- Agent definitions add enforcement (disallowedTools, hooks) that protocol files can't
- Same file serves both paths: mode-switching (read protocol, keep context) and fresh dispatch (agent definition, get enforcement)

**Adversarial agent:**
- New role that doesn't exist yet — reads project CLAUDE.md + implementation, checks directional alignment
- tools: Read, Glob, Grep only (can't edit, can't run anything)
- Can be either a Claude Code agent definition OR an agent-type hook that fires on SubagentStop/Stop
- Addresses the 03-22 failure directly

**Three-tier enforcement:**
1. Ward — deterministic, cheap, mechanical violations (git, python -c, phase)
2. Agent hooks — automated adversarial review at lifecycle points (SubagentStop, Stop)
3. External agents — Codex/Gemini for high-stakes, strongest independence

**Approach: B+C with A backstop:**
- B: Checkpoint before code — design artifact required before ward allows Edit/Write
- C: Radical transparency — agent externalizes decision points and uncertainty
- A: Adversary fires on Stop as backstop

### Agent hook discovery
- Claude Code supports `type: "agent"` hooks — spawns a subagent with full tool access (Read, Grep, Glob, etc.)
- Returns `{ok: true/false, reason: "..."}`
- Different from prompt hooks (no tool access) and command hooks (shell only)
- Can fire on any event: SubagentStop, Stop, PreToolUse, etc.
- Up to 50 tool turns, 60s default timeout
- This is the mechanism for automated adversarial review

### Claude Code custom agents discovery
- `/agents` command creates custom agents
- Stored in `~/.claude/agents/` (global) or `.claude/agents/` (project)
- YAML frontmatter + markdown prompt
- Frontmatter: name, description, tools, disallowedTools, model, permissionMode, hooks, etc.
- Prompt can reference files via `@path/to/file.md`
- Claude auto-delegates based on description field
- Can also be @-mentioned explicitly

### Concrete next steps (Q to choose)
1. Create agent definitions in `~/.claude/agents/` (adversary, analyst, verifier, scout, foreman)
2. Design artifact enforcement via ward rule
3. Prune CLAUDE.md to under 100 lines
4. Wire ward into `~/.claude/settings.json`
5. Hesitation hook on UserPromptSubmit

### Ward complete (3 merges to master, all pushed to github.com/ctoth/ward)

**Merge 1: per-file-rules** — Per-file rules in ~/.ward/rules/ and .ward/rules/, deny-is-veto, path normalization, validate command, README. 31 tests.

**Merge 2: README expansion** — Full example rules covering safety, git discipline, phase enforcement, behavioral nudges (flailing bumped to 5, "state your theory"), file scope protection.

**Merge 3: history-refactor** — Replaced bespoke counters (ReadsSinceBash, EditsSinceCommit, ToolCount, ToolCounts, LastTool) with History []string list. Custom CEL functions `last(list, n)` and `since(list, marker)`. Synthetic `_commit` marker. 100-entry cap. 32 tests.

**Current ward state:** State is `{phase, history, started_at}`. Everything else is patterns in rules. Clean, extensible.

### Remaining work items
1. **Create agent definitions** — ~/.claude/agents/ for adversary, analyst, verifier, scout, foreman. Each references protocol file.
2. **Write adversary protocol** — New file, the missing role from 03-22.
3. **Wire ward into Claude Code** — Build binary, add to ~/.claude/settings.json.
4. **Prune CLAUDE.md** — Remove rules now enforced by ward. Target: under 100 lines.
5. **Hesitation hook** — UserPromptSubmit detecting Q's uncertainty signals.

### Adversary protocol complete
- `~/.claude/CLAUDE.md.d/adversary.md` — protocol file, project-agnostic (no hardcoded questions, reads principle from project CLAUDE.md)
- `~/.claude/agents/adversary.md` — agent definition, Read/Glob/Grep only, Opus model, references protocol file
- Self-test found a real violation: initial version had hardcoded data-flow questions that were narrower than the principle. Q caught this, questions removed. Protocol now trusts the agent to derive checks from the principle.
- Self-test report at `reports/adversary-self-test-report.md`

### Ward v3 design direction: SQLite replaces CEL

Two research agents converged on the same insight: **insert the event into SQLite BEFORE evaluating rules.** Then the current event is just the latest row. No "current event" vs "history" split. Everything is rows.

**Key design decision pending Q's approval:**
- Drop CEL entirely (saves ~15MB binary, removes a dependency)
- Rules become SQL queries (mostly hidden behind YAML sugar)
- Built-in views: `this` (current event), `recent` (last N), `since_commit`, `tool_counts`
- Raw hook JSON stored verbatim, facts stamped via auto-analysis of rules
- YAML DSL for simple rules, raw SQL escape hatch for complex ones
- `ward explain <rule>` shows generated SQL

**Stamped facts computed automatically:** ward analyzes rule SQL for references like `e.git_branch`, determines which facts to compute and store at insert time. No `stamp: true` config needed.

**Five options evaluated:**
- A: Pure SQL (powerful but verbose)
- B: CEL + SQL (current split, two languages)
- C: CTE injection (current event as CTE, eliminates CEL but still verbose)
- D: Datalog over SQLite (most composable, no good Go implementation)
- E: DSL over SQL views (recommended — simple rules are YAML, complex rules escape to SQL)

Reports at:
- `reports/research-ward-sql-design.md`
- `reports/research-datalog-ward.md`

### Ward facts refactor merged + installed
- facts-per-file branch merged to master, pushed
- config.yaml gone entirely, facts are individual files in ~/.ward/facts/
- 34 tests passing
- Binary installed at /c/Users/Q/go/bin/ward (on PATH)

### Agent definitions created (6 agents)
- ~/.claude/agents/foreman.md — coordination, disallowedTools: Edit, Bash
- ~/.claude/agents/scout.md — exploration, disallowedTools: Edit
- ~/.claude/agents/analyst.md — problem finding, disallowedTools: Edit
- ~/.claude/agents/verifier.md — merge gate, disallowedTools: Edit
- ~/.claude/agents/investigator.md — structured debugging, disallowedTools: Edit
- ~/.claude/agents/researcher.md — research, disallowedTools: Edit, has WebSearch/WebFetch

### Ward rules + facts deployed
11 rule files in ~/.ward/rules/:
- no-python-c, uv-not-python, no-git-stash, no-git-add-all, no-git-reset-hard, no-force-push, no-tskill (hard deny)
- flailing-reads, uncommitted-edits (context nudge)

2 fact files in ~/.ward/facts/:
- git_branch (git branch --show-current)
- has_pyproject (bool)

### Ward fully wired and tested
- `ward validate` — 11 rules, 2 facts, 0 errors ✓
- Manual test: `python -c` → deny ✓, safe Read → allow (no output) ✓
- Hook added to `~/.claude/settings.json` PreToolUse, matcher `Bash|Edit|Write`, timeout 5s
- **25/25 rule tests pass** — every rule tested with positive and negative cases in real repo context
- Test script at `scripts/test_ward_rules.sh`, results at `reports/ward-rules-test-report.md`
- Key finding: `uv-not-python` correctly uses `has_pyproject` fact — only fires when pyproject.toml exists in cwd

### What's confirmed working
- 7 deny rules: no-python-c, uv-not-python, no-git-stash, no-git-add-all, no-git-reset-hard, no-force-push, no-tskill
- 2 context rules: flailing-reads (resets on Bash), uncommitted-edits (resets on git commit)
- Ward will fire on all new sessions (settings loaded at session start)

### CLAUDE.md pruning done (3 commits)
- Commit 1: Removed Flailing Detection, Git section, Hard Rules (python-c/tskill/uv), replaced Protocol Triggers with Specialized Agents list
- Commit 2: Condensed Take Notes + Compaction Schema into 3 lines, merged Checkpoints + Baseline + Testing into "Verification", removed Pass Objects
- Commit 3: Removed Source Code section (ward clone-not-fetch rule enforces it)
- **309 → 231 lines** (78 lines removed, 25%)

### Ward rules: 12 total, all tested
- no-python-c ✓ (tested: fires on `python -c`, allows `python scripts/foo.py`)
- uv-not-python ✓ (tested: fires on bare python with pyproject.toml, allows without)
- no-git-stash ✓ (tested)
- no-git-add-all ✓ (tested: fires on `.`, `-A`, `--all`)
- no-git-reset-hard ✓ (tested)
- no-force-push ✓ (tested)
- no-tskill ✓ (tested)
- flailing-reads ✓ (tested: fires after 5 consecutive reads, resets on Bash)
- uncommitted-edits ✓ (tested: fires after 2 edits, resets on git commit)
- clone-not-fetch ✓ (tested: fires on github blob/tree/raw URLs, allows non-github)
- Rules now use `input.commands.exists()` with shell parser (subagent updated them)

### Shell parser complete
- mvdan.cc/sh/v3 added for AST-based command parsing
- `input.commands` field: list of `{name, full}` maps extracted from shell AST
- Heredoc content, string literals in args no longer trigger false positives
- All 12 rules updated to `input.commands.exists()` syntax
- 53 Go tests + 30 integration tests pass
- Merged to master, installed, pushed

### Settings.json updated
- Ward PreToolUse matcher expanded: `Bash|Edit|Write|WebFetch`

### Q's request pending
- Ward project needs its own CLAUDE.md with rule: "test every rule before considering it deployed"

### Still to do
- Merge shell parser branch when subagent finishes
- Write ward project CLAUDE.md
- Consider further CLAUDE.md pruning (231 → target ~150?)
- SQLite redesign — parked
- Hesitation hook — not started
