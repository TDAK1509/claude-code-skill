# claude-code-skill

Personal Claude Code skills, kept in one repo so any machine or project can pick
them up quickly.

## Layout

```
skills/<skill-name>/SKILL.md   # one directory per skill
install.sh                     # link or copy skills into a Claude Code install
```

## Install

```bash
./install.sh                      # all skills -> ~/.claude/skills (available in every project)
./install.sh oversized-function   # just one skill
./install.sh --project            # -> ./.claude/skills of the current project
./install.sh --project ~/code/app # -> that project's .claude/skills
./install.sh --copy               # copy instead of symlink
```

Symlinks are the default. Edit a skill here and every install updates.
Restart Claude Code after installing.

## Skills

| Skill | Purpose |
| --- | --- |
| `oversized-function` | Refactor long functions by responsibility, not by line count. |

## Adding a skill

1. `mkdir -p skills/<name>`
2. Write `skills/<name>/SKILL.md` with YAML frontmatter: `name` and `description`.
   The `description` decides when Claude loads the skill, so state the triggers.
3. Run `./install.sh <name>`.
