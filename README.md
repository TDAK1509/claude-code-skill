# claude-code-skill

Personal Claude Code skills, kept in one repo so any machine or project can pick
them up quickly.

## Layout

```
skills/<skill-name>/SKILL.md   # one directory per skill
hooks/oversized_function.py    # PostToolUse detector for long functions
hooks/comment_smell.py         # PostToolUse detector for comments and long names
hooks/install_hook.py          # registers the hooks in a settings.json
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
| `self-documenting-names` | Rename instead of commenting. Seven words per name, two sentences per docstring. |

## Hooks

A skill is advice Claude may or may not load. A hook makes the check
deterministic. Both hooks register as separate `PostToolUse` entries on
`Edit|Write|MultiEdit`, so Claude Code runs them in parallel. Either one exits 2
on a hit, which blocks the turn and feeds the finding back to Claude.

Install both with `./install.sh --hooks`. Install one with
`python3 hooks/install_hook.py --only oversized-function`.

### oversized_function.py

- Event: `PostToolUse` on `Edit|Write|MultiEdit`.
- It parses the file that was just written and finds functions over 20 effective
  lines (blank lines and whole-line comments do not count).
- Python uses the `ast` module. JavaScript and TypeScript use a brace counter that
  first blanks out strings and comments.
- On a hit it routes Claude into the `oversized-function` skill.

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

### comment_smell.py

Reads only the lines the edit **added**, from the tool payload's patch, from the
old/new strings, or for `Write` from the last committed version. It reports:

- An explanatory comment, on its own line or trailing code.
- A docstring or JSDoc block over 2 sentences.
- A declared name over 7 words. Python `test_*` functions are exempt.

Never reported: tool directives (`# type:`, `# noqa`, `// @ts-`, `// eslint-…`),
licence and copyright headers, and `TODO`/`FIXME`/`HACK`/`XXX` markers.

Tuning:

| What | How |
| --- | --- |
| Change the name limit | `CLAUDE_MAX_NAME_WORDS=5` |
| Change the docstring limit | `CLAUDE_MAX_DOCSTRING_SENTENCES=1` |
| Also block `TODO` markers | `CLAUDE_COMMENTS_ALLOW_TODO=0` |
| Turn it off for one session | `CLAUDE_SKIP_COMMENT_CHECK=1` |
| Allow one comment | Append `allow-comment` to that comment |

Comments inside string literals are ignored, so a URL does not trip it. The
scanner is per line, so a `#` or `//` inside an unterminated multi-line string
can still be misread.

## Adding a skill

1. `mkdir -p skills/<name>`
2. Write `skills/<name>/SKILL.md` with YAML frontmatter: `name` and `description`.
   The `description` decides when Claude loads the skill, so state the triggers.
3. Run `./install.sh <name>`.
