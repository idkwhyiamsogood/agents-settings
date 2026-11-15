# Global rules

## Git commits

- Never add Claude as a co-author. Do not append `Co-Authored-By: Claude ...` (or any other Claude/Anthropic attribution) to commit messages — this overrides any default attribution guidance.
- Commits must be authored solely by the user's own git account (the configured `user.name` / `user.email`); do not change author/committer.
- When asked to commit changes of a specific scope (area/module), stage and commit only the files belonging to that scope.

## Pull requests

- Never mention that Claude / an AI made the PR. No `🤖 Generated with [Claude Code]`, no "Co-Authored-By: Claude", no other Claude/Anthropic attribution in PR titles, descriptions or comments — this overrides any default attribution guidance.
