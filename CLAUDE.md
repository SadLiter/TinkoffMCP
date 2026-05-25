# Project Instructions for AI Agents

This file provides instructions and context for AI coding agents working on this project.

## Git / GitHub Policy — READ FIRST

**The user pushes and commits themselves. Agents must NOT perform any write operations to git or GitHub.**

Forbidden — never run, propose, or call:

- `git commit`, `git push`, `git tag`, `git rebase --continue`, `git merge`, `git pull` (anything that mutates the working tree or refs)
- `git reset --hard`, `git restore`, `git checkout -- <path>`, `git stash drop/clear`, `git branch -D`, `git clean -f`
- `gh pr create`, `gh pr merge`, `gh pr close`, `gh pr comment`, `gh issue create/close/comment`, `gh release create`, `gh repo create`, any `gh api -X POST/PATCH/PUT/DELETE`
- GitHub MCP write tools — anything containing `create`, `update`, `push`, `merge`, `delete`, `fork`, `add_*`, `*_write` (e.g. `mcp__github__create_repository`, `mcp__github__push_files`, `mcp__github__create_or_update_file`, `mcp__github__create_pull_request`, `mcp__github__merge_pull_request`, `mcp__github__pull_request_review_write`, `mcp__github__issue_write`, `mcp__github__add_*`)
- `git remote set-url`, `git config --global ...`, `git config user.*`
- Any hook bypass: `--no-verify`, `--no-gpg-sign`, `-c commit.gpgsign=false`

Allowed:

- Read-only `git`: `git status`, `git diff`, `git log`, `git show`, `git branch --list`, `git ls-files`, `git rev-parse`, `git remote -v`
- Read-only `gh`: `gh pr view`, `gh issue view`, `gh api` with `GET` only
- GitHub MCP read tools: `mcp__github__get_*`, `mcp__github__list_*`, `mcp__github__search_*`, `mcp__github__pull_request_read`, `mcp__github__issue_read` — analysing third-party repos is fine
- Editing files in the working tree (Edit/Write tools) — the user reviews the diff and commits/pushes manually

Workflow at end of a task:

1. Finish edits and verify locally (run the app, tests, lint as appropriate)
2. Report changed files and a suggested commit message to the user as text
3. **Stop.** Do not stage, commit, or push. The user will handle it.

If the user explicitly asks for a commit/push later in the conversation, that single message overrides this section for that one action — but never assume default permission and never act preemptively.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:7510c1e2 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Session Completion

**When ending a work session**, hand off to the user — do not push yourself. The original beads integration mandated `git push`; that rule is **overridden** by the Git / GitHub Policy above for this project. Steps still relevant:

1. **File issues for remaining work** — create beads issues for anything that needs follow-up
2. **Run quality gates** (if code changed) — tests, linters, builds
3. **Update issue status** — close finished work, update in-progress items
4. **Report** — summarise changed files + suggested commit message to the user
5. **Stop** — the user commits and pushes themselves

<!-- END BEADS INTEGRATION -->


## Build & Test

```bash
uv sync --group dev               # install runtime + dev deps (ruff)
uv run ruff format src/           # format
uv run ruff check src/ scripts/   # lint — must pass before PR
uv run tinkoff-mcp                # smoke-start the MCP server (Ctrl+C to stop)
```

Smoke-test that stdio stays clean (required — JSON-RPC channel must not be polluted):

```bash
INVEST_TOKEN=t.dummy uv run tinkoff-mcp >/tmp/out.log 2>/tmp/err.log < /dev/null &
sleep 1; kill %1 2>/dev/null
wc -c /tmp/out.log   # must be 0
```

## Architecture Overview

_Add a brief overview of your project architecture_

## Conventions & Patterns

_Add your project-specific conventions here_
