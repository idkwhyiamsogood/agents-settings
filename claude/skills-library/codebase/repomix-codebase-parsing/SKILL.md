---
name: repomix-codebase-parsing
description: Use Repomix (via the codebase-packer skill/CLI) instead of manually crawling files with Grep/Glob/Read or spawning a broad Explore agent whenever a task requires understanding, auditing, reviewing, or summarizing a large part of a codebase or an entire repository — architecture overviews, comprehensive audits, broad code reviews, refactor planning, onboarding to an unfamiliar repo, or building context before a big change. Make sure to reach for this whenever the user asks to "parse", "pack", "audit", "get context on", or "understand" a project/repo/codebase, even if they don't name Repomix explicitly. Do NOT use for narrow, targeted lookups — finding one function, reading a single known file, grepping one symbol — standard tools remain faster and more appropriate there.
---

# Repomix for codebase-wide parsing

## Why this exists

Scattered `Grep`/`Glob` loops or a broad `Explore` subagent are slow and lossy for repo-wide understanding: each call only sees fragments, context gets rebuilt from scratch every time, and it's easy to miss files. Repomix packs the relevant directory tree into one structured snapshot in a single pass, which is both cheaper and more complete for tasks that genuinely need a wide view of the code.

## When to redirect to Repomix

Reach for Repomix when the task is about the *shape of the codebase as a whole* or a *significant slice of it*, e.g.:
- "explain the architecture of this project"
- "audit this repo for X"
- "give me context on this codebase before I refactor Y"
- "summarize what this service does end to end"
- explicit requests to parse/pack/bundle the repo or a module

## When NOT to redirect

Keep using standard tools (`Grep`, `Glob`, `Read`, or a scoped `Explore` agent) for anything narrow and targeted:
- finding a specific function/class/symbol
- reading one known file
- a single grep for a string or pattern
- quick lookups where you already know roughly where to look

Redirecting these to Repomix would be slower and wastes context on an unnecessarily large snapshot.

## How to act when this skill applies

1. Prefer invoking the existing `codebase-packer` skill (via the `Skill` tool) to run Repomix against the repository or the specific directories relevant to the task. Scope it to the smallest directory set that actually covers the task instead of always packing the entire repo.
2. If `codebase-packer` isn't available in the current session, fall back to running Repomix directly via `Bash`, e.g. `npx repomix <path>` (or the installed `repomix` CLI), then read the generated output file.
3. Reason over the packed snapshot instead of issuing many separate `Grep`/`Glob`/`Read` calls or spawning an `Explore` agent for the same broad question.
4. If the packed output is large, read it in sections rather than loading it all into context at once.
