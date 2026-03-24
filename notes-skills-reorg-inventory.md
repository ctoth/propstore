# Skills Reorg Inventory - Working Notes

## GOAL
Inventory all local automation artifacts across 4 locations.

## DONE
- Read all 11 protocol files in ~/.claude/CLAUDE.md.d/
- Listed slash commands in ~/.claude/commands/ (28 files)
- Listed ward rules in ~/.ward/rules/ (10 files) and ward facts (2 files)
- Found research-papers-plugin has a plugins/ directory

## STILL TODO
- Read remaining 18 slash commands (read 10 so far)
- Read each ward rule file (10 rules, 2 facts)
- Read research-papers-plugin/plugins/ contents
- Write final report

## SLASH COMMANDS READ SO FAR (10/28)
1. atomic-qa-test.md - Implement QA test items atomically with existing test infra
2. changelog-since-release.md - Generate changelog since last tagged release including deps
3. claudio.md - Control Claudio audio feedback (volume/mute/unmute/status)
4. close-if-completed.md - Check if GitHub issue was fixed elsewhere, close with explanation
5. command-template.md - Template/guide for creating new slash commands
6. commit-all.md - Commit all modified files individually with descriptive messages
7. consolidate-tests.md - Consolidate multiple test files into single comprehensive file
8. debug-conformance.md - Debug conformance test failures against reference implementation (toaststunt/MOO specific)
9. deep-grok.md - Collaborative deep library investigation with Zen/continuous-thinking tools
10. find-breaking-commit.md - Git bisect to find exact breaking commit
11. fix-e2e-test.md - Fix Playwright e2e test failures with gates and flailing detector
12. fix-github-issue.md - Analyze and fix GitHub issues with triage-first approach
13. fix-lint.md - Identify and fix linting issues (prefers oxlint)
14. fix-skipped-tests.md - Diagnose and fix skipped e2e tests
15. hg-to-git.md - Convert Mercurial repos to Git via WSL/fast-export
16. improve-command.md - Analyze slash command usage and iteratively improve
17. investigate-and-solve.md - Systematic problem-solving: explore, research, build, measure
18. make-command.md - Generate new slash command from successful workflow
19. modernize-python-project.md - Migrate Python project to pyproject.toml with ruff/pyright
20. monkeyproof-plan.md - Comprehensive atomic-commit execution plan with zero fuzzy bits

## FINDINGS SO FAR

### Protocol files (11 files, skipping CLAUDE.md itself)
1. foreman.md - Coordination protocol, no execution allowed, dispatches subagents
2. subagent.md - How to write/launch subagent prompts, template, checklist
3. gauntlet.md - Scout->Coder->Analyst->Verifier pipeline for complex work
4. investigation.md - Structured debugging with competing hypotheses (L1/L2/L3)
5. phases.md - Parallel/sequential workflow phases, filesystem artifact orchestration
6. iterations.md - Tracked iteration cycles for reducing failures
7. external-agents.md - Codex/Gemini CLI usage as external reviewers
8. RE.md - Reverse engineering projects, documentation-focused
9. adversary.md - Checks design alignment with project principles
10. researcher.md - Pre-implementation research, parallel exploration
11. spec-updating.md - Spec update workflow with external review gates
