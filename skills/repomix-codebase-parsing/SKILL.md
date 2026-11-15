---
name: repomix-codebase-parsing
description: Pack a repository or substantial module with Repomix for architecture analysis, broad review or onboarding. Use for repository-wide context, not individual symbol lookups.
---

# Repository context with Repomix

1. Inspect repository instructions and select the smallest scope covering the task.
2. Use an available Repomix integration or installed CLI. If absent, consult current
   official installation instructions; do not assume a shell or package runner.
3. Exclude credentials, local state, dependencies and generated artifacts. Write
   the packed output to a temporary directory supplied by the current environment.
4. Read large output in sections. Verify important conclusions against original
   files; a packed snapshot may omit ignored or unsupported files.
5. Report scope and omissions. Keep the generated pack out of version control.
