# Skills Reorganization Research — 2026-03-23

## GOAL
Figure out how to reorganize Q's protocols, slash commands, ward rules, and skills into a coherent plugin/skill architecture.

## CONTEXT
Q asked me to review propstore code and research-papers-plugin skills. I failed by:
1. Not adopting foreman protocol (dispatched scouts directly)
2. Telling scouts to read notes when Q said "come in blind, no notes"
3. Discovered I had deleted the Protocol Triggers section from CLAUDE.md in a prior session (commit e5b7402)

This led to the realization: protocols (like foreman.md) should be skills, not files you remember to read. Which led to the broader question: how should ALL automation artifacts be organized?

## DONE
- Read foreman.md and subagent.md protocols
- Wrote two scout prompts: inventory-local and research-ecosystem
- Dispatched both scouts in parallel
- Both scouts completed — reports at ./reports/skills-reorg-{inventory-local,research-ecosystem}.md
- Read both reports

## INVENTORY SUMMARY (82 artifacts)
- 11 protocol files in CLAUDE.md.d/ (foreman, subagent, gauntlet, investigation, phases, iterations, external-agents, RE, adversary, researcher, spec-updating)
- 28 slash commands in ~/.claude/commands/ (13 general, 9 project-specific, 4 planning, 1 utility, 1 template)
- 10 ward rules (8 deny, 2 context nudges) + 2 facts
- 13 skills in research-papers-plugin + 18 supporting Python scripts

## STALENESS
- spec-updating.md — references polyarray project, stale for propstore
- external-agents.md — examples use polyarray paths
- 9 slash commands are project-specific to Audiom/cow_py/accessibleapps (not stale, but limited scope)

## ECOSYSTEM FINDINGS
- Community consensus: Rules (cheap, always loaded) → Skills (loaded on relevance) → Subagents (isolation)
- Skills are probabilistic (Claude decides), hooks are deterministic (shell scripts)
- SKILL.md frontmatter two-axis: disable-model-invocation × user-invocable
- Marketplaces exist: Anthropic official, agentskill.sh (SHA versioning), CCPI (npm-based)
- Official plugin structure: .claude-plugin/plugin.json + skills/ + commands/ + agents/
- Claude Warden = closest ward analogue (AST-based shell parsing, allow/deny/ask)
- Skills auto-trigger unreliably — known pain point. Hooks can force-inject context.
- Q's setup (protocol modes, prediction protocol, ward behavioral rules, notes-as-you-go) has no community equivalents

## KEY INSIGHT
The protocol trigger problem has a clean solution: protocols become skills with `disable-model-invocation: true` (user-only, explicit invocation via /foreman). This is better than:
- Remembering to read a file (current system — just failed)
- Auto-triggering (unreliable per ecosystem research)
- Always-loaded in CLAUDE.md (too heavy, was pruned, and that's what broke it)

## WARD CAPABILITIES (from ward-scout report)
- Rules: YAML with CEL expressions, actions: deny/allow/context
- Tool coverage: ANY tool (Bash, Edit, Write, Read, TaskOutput, WebFetch, etc.)
- Bash commands parsed into AST — matches actual commands, not raw text
- Session state: phase (string), history (last 100 tool names), started_at
- Custom CEL functions: last(history, N), since(history, marker)
- Facts: shell commands re-executed per eval, string or bool
- `session.phase` ALREADY EXISTS — `ward set <phase>` sets it, rules match on it

## KEY REVELATION
Protocol-mode gates are already feasible with ZERO ward code changes:
1. Skill `/foreman` calls `ward set foreman` at activation
2. New rule: `session.phase == "foreman" && tool in ["Edit", "Write", "Bash"]` → deny
3. Prompt + enforcement: skill tells you what to do, ward prevents what you shouldn't

## PROSE → WARD CANDIDATES
| Prose rule | Feasibility |
|---|---|
| No `gh pr create` | Trivial — parsed command matching |
| No TaskOutput | Trivial — `tool == "TaskOutput"` deny |
| No Claude signoff | Feasible — git commit content matching |
| No cat/sed/awk in Bash | Trivial — parsed command name matching |
| Diagnostic mode: max 3 commands | `ward set diagnostic` + count since() |
| Foreman tool restrictions | `session.phase == "foreman"` + tool deny |

## PROOF OF CONCEPT: FOREMAN WARD GATE — WORKING
Built and tested `.ward/rules/foreman-gate.yaml` in propstore project:

```yaml
when: >
  session.phase == "foreman" && (
    tool in ["Bash", "Edit"] ||
    (tool == "Write" && !("file_path" in input && (input.file_path.contains("/prompts/") || input.file_path.contains("notes-"))))
  )
action: deny
message: "Foreman protocol active. You coordinate, you do not execute. Dispatch a subagent instead."
```

Test results (all correct):
- Write src/foo.py → DENY
- Write prompts/test.md → ALLOW
- Write notes-test.md → ALLOW
- Bash ls → DENY
- Read/Agent → ALLOW (not gated)

### Debugging lessons
- Test JSON must use `tool_input` not `input` (Claude Code hook format, see adapters.go line 107)
- CEL `has(input.file_path)` doesn't work for maps — use `"file_path" in input`
- CEL eval errors are silently swallowed (guard.go line 464: `continue`) — rule just doesn't fire
- Ward has no debug/verbose mode — silent failures are hard to diagnose

## WARD DX IMPROVEMENT — DONE
- Agent added `--verbose` / `-v` flag to `ward eval` (commit `558af47` in ward repo)
- Verbose shows: tool, phase, history_len, each fact, each rule (eval result + action), final decision
- Tested: works correctly, all debug to stderr, stdout JSON unchanged
- Need to install new binary to PATH (currently using `./ward.exe` from build dir)

## WARD TESTS — DONE
- Agent added 13 test cases across 4 groups (commit `aa759ae` in ward repo)
- Covers: basic phase gating, file path whitelist, CEL map key access, compound phases
- Tests caught a path format bug in whitelist expression during development

## PLUGIN STRUCTURE RESEARCH — DONE
Report at ./reports/plugin-structure-research.md. Key findings:
- Plugins use convention-based auto-discovery: `skills/*/SKILL.md`
- Marketplace = repo with `.claude-plugin/marketplace.json` listing plugins
- Installation: `claude plugin marketplace add owner/repo` then `claude plugin install name@marketplace`
- Plugins are COPIED to `~/.claude/plugins/cache/` at install time
- Plugin skills are namespaced: `/plugin-name:skill-name`
- Plugins CAN ship hooks but CANNOT ship ward rules
- `$CLAUDE_PLUGIN_ROOT` and `$CLAUDE_PLUGIN_DATA` available in hooks/skills
- `$CLAUDE_ENV_FILE` lets SessionStart hooks set env vars for the session

## WARD + PLUGIN INTEGRATION — DECIDED
Report at ./reports/ward-plugin-integration.md. Evaluated 5 patterns:
- Pattern A (ward scans plugin cache): Rejected — couples ward to Claude internals
- Pattern B (hooks call ward set): Works for phases only, doesn't scale to novel rules
- Pattern C (ward becomes a plugin): Rejected — kills cross-platform portability
- Pattern D (ward reads manifest): Workable but manual, stale paths on update
- Pattern E (post-install scripts): Not viable — no install lifecycle hooks

**CHOSEN: `WARD_RULES_DIRS` env var + plugin SessionStart hook**
1. Ward adds `WARD_RULES_DIRS` env var support (~15 lines Go)
2. Plugins ship SessionStart hook that writes their ward-rules/ path to `$CLAUDE_ENV_FILE`
3. Ward loads: global → env var dirs → project-local
4. Ward stays portable, plugins bundle rules, everything explicit
5. Plugin updates auto-point to right dir via `$CLAUDE_PLUGIN_ROOT`

Analogues: ESLint shareable configs, OPA policy bundles, pre-commit hook repos

## WARD COMMITS (pushed to origin/master)
- `558af47` — Add --verbose flag to ward eval
- `aa759ae` — Add phase-gate test cases
- `8393482` — Add WARD_RULES_PATH env var support

Note: env var ended up as `WARD_RULES_PATH` (not `WARD_RULES_DIRS`). Matches PATH convention.

## PROTOCOLS-PLUGIN — CREATED AND PUSHED
- **Repo:** https://github.com/ctoth/protocols-plugin
- **Commit:** `2539210`
- **Tag:** `v0.1.0`
- **11 skills:** foreman, subagent, gauntlet, investigation, phases, iterations, adversary, researcher, external-agents, spec-updating, RE
- **3 ward gates:** foreman-gate.yaml, adversary-gate.yaml, researcher-gate.yaml
- **Hooks:** SessionStart → ward-register.sh → sets WARD_RULES_PATH via CLAUDE_ENV_FILE
- spec-updating and external-agents generalized (polyarray-specific paths removed)
- Report at ./reports/create-protocols-plugin.md

## WARD REGEX FIX — DONE
- Fixed `no-git-add-all.yaml`: changed `\\.` to `\\.$` so bare `git add .` is denied but `git add .gitignore` is allowed
- Tested all 4 cases: `git add .` (DENY), `git add .gitignore` (ALLOW), `git add -A` (DENY), `git add --all` (DENY)

## AUTO-INVOCATION — DONE
- All 10 protocol skills changed from `disable-model-invocation: true` to `false`
- Commit `bafd6b6` pushed to protocols-plugin master
- Tag v0.1.0 NOT force-pushed (ward blocked, correctly) — Q can force-push or we tag v0.1.1
- Plugin installed and visible: `protocols:subagent` confirmed in skills list
- Other protocols should now also be auto-invocable after plugin cache refreshes

## SLASH COMMANDS RECOMMENDATION
- 13 general-purpose commands: leave as commands (action-oriented, no ward gating needed)
- 9 project-specific commands: eventually move to per-project plugins (separate effort)
- 4 planning commands (deep-grok, monkeyproof-plan, rigorous-plan, parallel-fix): could become skills later but work fine as commands
- Short answer: commands are fine, protocols were the urgent migration

## CLAUDE.MD CLEANUP — DONE
- Replaced 10-line agent list with 4-line protocols plugin reference (commit `5deb625` in CLAUDE.md.d)

## WARD RULES ADDITIONS
- `no-force-tag.yaml` added to `~/.ward/rules/` — denies `git tag -f`, "Tags are immutable"
- `no-git-add-all.yaml` regex fix already noted above

## PROTOCOLS-PLUGIN VERSION BUMP — IN PROGRESS
- Bumped plugin.json from 0.1.0 to 0.1.2
- Need to commit, push, tag v0.1.2
- Then Q needs to `claude plugin update` to get fresh cache
- Tagged v0.1.1 already pushed (auto-invocation change)
- Plugin cache currently has stale 0.1.0 — only protocols:subagent visible

## NEXT
1. Commit + push + tag v0.1.2 on protocols-plugin
2. Q runs `claude plugin update protocols@protocols-marketplace`
3. End-to-end test: all protocol skills visible, invoke `/protocols:foreman`, verify ward gates
4. Install updated ward binary to PATH

## OPEN QUESTIONS
- Ward binary PATH install method
- The original ask (review propstore + skills code) is still pending
