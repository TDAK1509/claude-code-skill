# claude-code-skill

Personal Claude Code skills, kept in one repo so any machine or project can pick
them up quickly.

## Layout

```
skills/<skill-name>/SKILL.md   # one directory per skill
hooks/oversized_function.py    # PostToolUse detector for long functions
hooks/install_hook.py          # registers that hook in a settings.json
install.sh                     # link or copy skills, and register hooks
```

## Install

```bash
./install.sh                      # all skills -> ~/.claude/skills (available in every project)
./install.sh oversized-function   # just one skill
./install.sh --project            # -> ./.claude/skills of the current project
./install.sh --project ~/code/app # -> that project's .claude/skills
./install.sh --copy               # copy instead of symlink
./install.sh --hooks              # also register the oversized-function hook
./install.sh --hooks --remove-hooks  # unregister it
```

Symlinks are the default. Edit a skill here and every install updates.
Restart Claude Code after installing.

## Skills

| Skill | Purpose |
| --- | --- |
| `oversized-function` | Refactor long functions by responsibility, not by line count. |

## The oversized-function hook

A skill is advice I may or may not load. The hook makes the check deterministic.

- Event: `PostToolUse` on `Edit|Write|MultiEdit`.
- It parses the file that was just written and finds functions over 20 effective
  lines (blank lines and whole-line comments do not count).
- Python uses the `ast` module. JavaScript and TypeScript use a brace counter that
  first blanks out strings and comments.
- On a hit it exits 2. That blocks the turn and feeds the finding back to Claude,
  which then applies the `oversized-function` skill.

Tuning:

| What | How |
| --- | --- |
| Change the limit | `CLAUDE_MAX_FUNCTION_LINES=30` |
| Turn it off for one session | `CLAUDE_SKIP_FUNCTION_LENGTH=1` |
| Allow one function | Put `allow-long-function` in a comment inside it |

Skipped by default: test files, `node_modules`, `dist`, `build`, `vendor`,
`.venv`, `__pycache__`, `.next`, and `*.min.js`. Test callbacks (`describe`, `it`,
`beforeEach`, …) are not treated as functions.

The JS/TS detector is a heuristic, not a parser. It can miscount exotic syntax.
Python is exact.

## Adding a skill

1. `mkdir -p skills/<name>`
2. Write `skills/<name>/SKILL.md` with YAML frontmatter: `name` and `description`.
   The `description` decides when Claude loads the skill, so state the triggers.
3. Run `./install.sh <name>`.
