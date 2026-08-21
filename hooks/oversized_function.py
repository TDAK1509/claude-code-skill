#!/usr/bin/env python3
"""PostToolUse hook: block on functions longer than the threshold.

Reads the Claude Code hook payload on stdin. When the file that was just
edited contains a function over CLAUDE_MAX_FUNCTION_LINES effective lines
(default 20), it writes an explanation to stderr and exits 2, which feeds the
message back to Claude and blocks the turn.

Escape hatch: put `allow-long-function` in a comment inside the function.
Disable entirely: export CLAUDE_SKIP_FUNCTION_LENGTH=1
"""
import ast
import json
import os
import re
import sys

THRESHOLD = int(os.environ.get("CLAUDE_MAX_FUNCTION_LINES", "20"))
ALLOW_MARKER = "allow-long-function"

JS_SUFFIXES = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts")
PY_SUFFIXES = (".py", ".pyi")

SKIP_PATH = re.compile(
    r"(^|/)(node_modules|dist|build|vendor|\.venv|venv|__pycache__|\.next)/"
    r"|\.min\.js$"
    r"|(^|/)(tests?|__tests__|spec)/"
    r"|(^|/)test_[^/]*\.py$"
    r"|_test\.py$|conftest\.py$"
    r"|\.(test|spec)\.[jt]sx?$"
)

# Callbacks whose bodies are structure, not behaviour. Long ones are not this smell.
CALLBACK_HOSTS = {
    "describe", "it", "test", "suite", "context",
    "beforeEach", "afterEach", "beforeAll", "afterAll", "before", "after",
}
JS_KEYWORDS = {
    "if", "else", "for", "while", "switch", "catch", "try", "do", "return",
    "typeof", "instanceof", "new", "delete", "void", "await", "yield", "in", "of",
}


# --- shared helpers ---------------------------------------------------------

def effective_lines(lines, comment_prefixes):
    """Count lines that carry code: not blank, not a whole-line comment."""
    count = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if any(stripped.startswith(p) for p in comment_prefixes):
            continue
        count += 1
    return count


def drop_nested(violations):
    """Keep only the outermost function of each nested violating pair."""
    kept = []
    for v in sorted(violations, key=lambda v: (v["start"], -v["end"])):
        if any(k["start"] <= v["start"] and v["end"] <= k["end"] for k in kept):
            continue
        kept.append(v)
    return kept


def allowed(lines, start, end):
    return any(ALLOW_MARKER in line for line in lines[start - 1:end])


# --- Python -----------------------------------------------------------------

def python_violations(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []  # mid-edit or unsupported syntax; stay quiet
    lines = source.splitlines()
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        start, end = node.lineno, node.end_lineno
        if allowed(lines, start, end):
            continue
        size = effective_lines(lines[start - 1:end], ("#",))
        if size > THRESHOLD:
            found.append({"name": node.name, "start": start, "end": end, "size": size})
    return drop_nested(found)


# --- JavaScript / TypeScript ------------------------------------------------

def blank_out_noise(source):
    """Replace string, template and comment contents with spaces.

    Line structure and brace positions in real code are preserved, so the
    brace counter never trips over a `{` inside a string or a comment.
    """
    out = []
    i, n = 0, len(source)
    state = None  # None | "line" | "block" | quote char
    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""
        if state is None:
            if ch == "/" and nxt == "/":
                state, out, i = "line", out + ["  "], i + 2
                continue
            if ch == "/" and nxt == "*":
                state, out, i = "block", out + ["  "], i + 2
                continue
            if ch in "\"'`":
                state, out, i = ch, out + [" "], i + 1
                continue
            out.append(ch)
            i += 1
            continue
        # inside a comment or string: keep newlines, blank everything else
        if state == "line":
            if ch == "\n":
                state = None
                out.append(ch)
            else:
                out.append(" ")
            i += 1
            continue
        if state == "block":
            if ch == "*" and nxt == "/":
                state, out, i = None, out + ["  "], i + 2
                continue
            out.append(ch if ch == "\n" else " ")
            i += 1
            continue
        # inside a string
        if ch == "\\":
            out.append("  ")
            i += 2
            continue
        if ch == state:
            state = None
            out.append(" ")
            i += 1
            continue
        out.append(ch if ch == "\n" else " ")
        i += 1
    return "".join(out)


NAMED_FUNC = re.compile(r"\bfunction\s*\*?\s*([A-Za-z_$][\w$]*)?\s*\(")
ASSIGNED = re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=")
PROP_ARROW = re.compile(r"([A-Za-z_$][\w$]*)\s*:\s*(?:async\s*)?\(")
METHOD = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:public|private|protected|readonly|static|abstract\s+)*"
    r"(?:async\s+)?(?:get\s+|set\s+)?\*?\s*([A-Za-z_$][\w$]*)\s*(?:<[^>(]*>)?\s*\([^;]*\)\s*"
    r"(?::\s*[^{;=]+)?\{\s*$"
)
CALL_HOST = re.compile(r"([A-Za-z_$][\w$]*)\s*\(\s*(?:async\s*)?(?:\(|function|[A-Za-z_$][\w$]*\s*=>)")


def js_function_starts(code_lines):
    """Yield (line_index, name) for lines that open a function body."""
    for idx, line in enumerate(code_lines):
        if "{" not in line:
            continue
        host = CALL_HOST.search(line)
        if host and host.group(1) in CALLBACK_HOSTS:
            continue
        named = NAMED_FUNC.search(line)
        if named:
            name = named.group(1) or _nearby_name(line) or "<anonymous>"
            yield idx, name
            continue
        if "=>" in line and line.rstrip().endswith("{"):
            yield idx, _nearby_name(line) or "<arrow>"
            continue
        method = METHOD.match(line)
        if method and method.group(1) not in JS_KEYWORDS:
            yield idx, method.group(1)


def _nearby_name(line):
    for pattern in (ASSIGNED, PROP_ARROW):
        match = pattern.search(line)
        if match:
            return match.group(1)
    return None


def js_violations(source):
    raw_lines = source.splitlines()
    code_lines = blank_out_noise(source).splitlines()
    found = []
    for idx, name in js_function_starts(code_lines):
        end = _scan_block_end(code_lines, idx)
        if end is None:
            continue
        start = idx + 1
        if allowed(raw_lines, start, end):
            continue
        size = effective_lines(raw_lines[start - 1:end], ("//", "/*", "*"))
        if size > THRESHOLD:
            found.append({"name": name, "start": start, "end": end, "size": size})
    return drop_nested(found)


def _scan_block_end(code_lines, start_idx):
    """Return the 1-based line where the block opened on start_idx closes."""
    depth = 0
    opened = False
    for idx in range(start_idx, len(code_lines)):
        for ch in code_lines[idx]:
            if ch == "{":
                depth += 1
                opened = True
            elif ch == "}":
                depth -= 1
                if opened and depth == 0:
                    return idx + 1
        if opened and depth <= 0:
            return idx + 1
    return None


# --- hook plumbing ----------------------------------------------------------

def edited_paths(payload):
    tool = payload.get("tool_name", "")
    if tool not in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        return []
    path = (payload.get("tool_input") or {}).get("file_path")
    return [path] if path else []


def analyse(path):
    if SKIP_PATH.search(path):
        return []
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            source = handle.read()
    except OSError:
        return []
    if path.endswith(PY_SUFFIXES):
        return python_violations(source)
    if path.endswith(JS_SUFFIXES):
        return js_violations(source)
    return []


def report(path, violations):
    head = [
        f"Oversized function in {path} (limit {THRESHOLD} effective lines):",
        "",
    ]
    for v in violations:
        head.append(f"  {v['name']}  lines {v['start']}-{v['end']}  ({v['size']} lines)")
    head += [
        "",
        "Use the `oversized-function` skill before you continue.",
        "Length is the signal, not the problem: name the distinct responsibilities",
        "first, then redistribute them. Do not extract helperA/helperB to get under",
        "the limit.",
        "",
        "If the function is genuinely one responsibility, say why, and add a comment",
        f"containing `{ALLOW_MARKER}` inside it.",
    ]
    return "\n".join(head)


def main():
    if os.environ.get("CLAUDE_SKIP_FUNCTION_LENGTH"):
        return 0
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    messages = []
    for path in edited_paths(payload):
        violations = analyse(path)
        if violations:
            messages.append(report(path, violations))
    if not messages:
        return 0
    sys.stderr.write("\n\n".join(messages) + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
