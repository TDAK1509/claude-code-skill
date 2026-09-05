# claude-code-skill

Personal Claude Code skills, kept in one repo so any machine or project can pick
them up quickly.

## Layout

```
skills/<skill-name>/SKILL.md   # one directory per skill
hooks/oversized_function.py    # PostToolUse detector for long functions
hooks/comment_smell.py         # PostToolUse detector for comments and long names
hooks/helper_order.py          # PostToolUse detector for helpers above their caller
hooks/generated.py             # shared: is this file generated or vendored?
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
| `clean-code-implementation` | The index for the three rules that bind code you write. Start here. |
| `helper-functions-ordering` | Define a helper directly below its caller. Read a file from the whole to the parts. |
| `oversized-function` | Refactor long functions by responsibility, not by line count. |
| `self-documenting-names` | Rename instead of commenting. Ten words per name, two sentences per docstring. |
| `minimal-scope-plan` | Plan from code you read, not comments. Smallest change that reaches the goal. |
| `increments-plan` | Plan a task as small, single-responsibility PRs — each one working, testable, revertible. |
| `function-names-are-verbs` | Name every function with a verb. Nouns name things, not actions. |
| `code-review-do-what-it-claims` | Review changed files (current branch vs main) against the claim they make. |
| `code-review-leaks` | Review changed files (current branch vs main) for security and performance leaks. |
| `code-review-full` | Runs the two skills above and combines their reports. |

`oversized-function`, `self-documenting-names` and `helper-functions-ordering`
have hooks. The rest are judgement calls, so no deterministic check exists for
them.

## Hooks

A skill is advice Claude may or may not load. A hook makes the check
deterministic. Each hook registers as its own `PostToolUse` entry on
`Edit|Write|MultiEdit`, so Claude Code runs them in parallel. Either one exits 2
on a hit, which blocks the turn and feeds the finding back to Claude.

Install them all with `./install.sh --hooks`. Install one with
`python3 hooks/install_hook.py --only oversized-function`.

### oversized_function.py

- Event: `PostToolUse` on `Edit|Write|MultiEdit`.
- It parses the file that was just written and finds functions over 12 effective
  lines (blank lines and whole-line comments do not count).
- Python uses the `ast` module. JavaScript and TypeScript use a brace counter that
  first blanks out strings and comments.
- On a hit it routes Claude into the `oversized-function` skill.

Tuning:

| What | How |
| --- | --- |
| Change the limit | `CLAUDE_MAX_FUNCTION_LINES=20` |
| Turn it off for one session | `CLAUDE_SKIP_FUNCTION_LENGTH=1` |
| Allow one function | Put `allow-long-function: <reason>` in a comment inside it |

Skipped by default: test files, plus everything in *Generated files* below. Test
callbacks (`describe`, `it`, `beforeEach`, …) are not treated as functions.

The JS/TS detector is a heuristic, not a parser. It can miscount exotic syntax.
Python is exact.

### comment_smell.py

Reads only the lines the edit **added**, from the tool payload's patch, from the
old/new strings, or for `Write` from the last committed version. New code is
bound by the rule; the legacy code around it is not. It reports:

- An explanatory comment, on its own line or trailing code.
- A docstring or JSDoc block over 2 sentences.
- A declared name over 10 words. Python `test_*` functions are exempt.

Never reported: tool directives (`# type:`, `# noqa`, `// @ts-`, `// eslint-…`),
licence and copyright headers, and `TODO`/`FIXME`/`HACK`/`XXX` markers.

Tuning:

| What | How |
| --- | --- |
| Change the name limit | `CLAUDE_MAX_NAME_WORDS=7` |
| Change the docstring limit | `CLAUDE_MAX_DOCSTRING_SENTENCES=1` |
| Also block `TODO` markers | `CLAUDE_COMMENTS_ALLOW_TODO=0` |
| Turn it off for one session | `CLAUDE_SKIP_COMMENT_CHECK=1` |
| Allow one comment | Append `allow-comment: <reason>` to that comment |
| Change the bypass cap | `CLAUDE_MAX_COMMENT_BYPASS=5` |

Comments inside string literals are ignored, so a URL does not trip it. The
scanner is per line, so a `#` or `//` inside an unterminated multi-line string
can still be misread.

### helper_order.py

- Event: `PostToolUse` on `Edit|Write|MultiEdit`.
- It finds a function that every one of its callers is defined below. The file
  then reads bottom-up: detail before purpose.
- Siblings only, at the top level of a file and inside a Python class. Python
  uses `ast`; JS/TS reuses the brace scanner from `oversized_function.py`.
- On a hit it routes Claude into the `helper-functions-ordering` skill.

Tuning:

| What | How |
| --- | --- |
| Turn it off for one session | `CLAUDE_SKIP_HELPER_ORDER=1` |
| Allow one helper | Put `allow-helper-order: <reason>` inside it |

Not reported: mutual recursion, a name used at module level (moving it would
break the language's own order rule), and anonymous functions.

Unlike `comment_smell.py`, this one reads the whole file. That is deliberate:
reordering is pure movement, so a file you open is a file you may order. Commit
the move separately from the change that made you open it.

## The rules are required

All three hooks block. None is advisory, and no escape hatch is free.

- A bare `allow-comment`, `allow-long-function` or `allow-helper-order` does not
  silence a hook. The marker needs a written reason after a colon.
- More than 2 reasoned bypasses in one edit is itself reported. Raise the cap
  with `CLAUDE_MAX_COMMENT_BYPASS`.
- "It matches the file's existing style" is not a reason. That is how the file
  got this way.

The failure this guards against: reaching for the marker instead of loading the
skill, then discovering later that half the comments could have been names.

## Generated files

The hooks ignore generated and vendored code, through `hooks/generated.py`. The
rules are for code a person writes; generator output is regenerated, not
refactored.

A file is treated as generated when any of these hold:

- It sits in `node_modules`, `vendor`, `third_party`, `dist`, `build`, `out`,
  `target`, `coverage`, `.venv`, `__pycache__`, `.next`, `.nuxt`, `.turbo`, and
  similar build or dependency directories.
- It sits in `generated/`, `__generated__/`, `gen/`, `codegen/`, `autogen/`,
  `proto/`, `migrations/`, `openapi/`, or `api/generated/`.
- Its name matches `*.gen.ts`, `*.generated.*`, `*.d.ts`, `openapi*.json|yaml|ts`,
  `swagger*.*`, `schema.graphql`, `*_pb2.py`, `*_pb.ts`, `*.pb.go`, a lock file,
  or `*.min.js`.
- Its first 4 KB contain `@generated`, `generated by`, `auto-generated`, or
  `DO NOT EDIT`. This catches `openapi-typescript` output wherever it lives.

Add project-specific patterns with `CLAUDE_GENERATED_EXTRA`, a comma-separated
list of regular expressions:

```bash
export CLAUDE_GENERATED_EXTRA='src/lib/api/.*\.ts$,.*/fixtures/.*'
```

## Adding a skill

1. `mkdir -p skills/<name>`
2. Write `skills/<name>/SKILL.md` with YAML frontmatter: `name` and `description`.
   The `description` decides when Claude loads the skill, so state the triggers.
3. Run `./install.sh <name>`.
