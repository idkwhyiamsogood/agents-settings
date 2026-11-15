# Skills library

Global Claude Code skills, grouped by purpose. Claude Code only discovers skills one level deep in
`~/.claude/skills/<name>/SKILL.md`, so the real files live here and `~/.claude/skills/` holds
symlinks to them.

## Categories

| Category         | What goes here                                                        |
| :--------------- | :-------------------------------------------------------------------- |
| `mcp/<server>/`  | Skills that drive a specific MCP server's tools (useless without it)  |
| `codebase/`      | Analyzing, packing, auditing repositories                             |
| `system-design/` | Architecture, design docs, ADRs (empty for now)                       |

## Installed

| Skill                      | Category          | Purpose                                                   |
| :------------------------- | :---------------- | :-------------------------------------------------------- |
| `figma-codegen`            | `mcp/figwright`   | Figma design → framework-aware code (reuses components/tokens) |
| `figma-build`              | `mcp/figwright`   | Code / description → design in Figma (reuses file's design system) |
| `repomix-codebase-parsing` | `codebase`        | Pack a whole repo with Repomix instead of crawling files  |

## Adding a skill

```bash
mkdir -p ~/.claude/skills-library/<category>
cp -r <skill-dir> ~/.claude/skills-library/<category>/
ln -s ../skills-library/<category>/<skill-name> ~/.claude/skills/<skill-name>
```

Third-party skills: keep a `SOURCE.md` next to them (repo, commit, date).
