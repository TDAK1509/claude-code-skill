#!/usr/bin/env python3
"""PostToolUse hook: block comments that a better name would replace.

Reads the Claude Code hook payload on stdin, looks only at the lines the edit
added, and exits 2 when it finds an explanatory comment, a docstring longer
than two sentences, or an identifier of more than ten words.

Escape hatch: put `allow-comment` on the comment line.
Disable entirely: export CLAUDE_SKIP_COMMENT_CHECK=1
"""
import difflib
import json
import os
import re
import subprocess
import sys

MAX_NAME_WORDS = int(os.environ.get("CLAUDE_MAX_NAME_WORDS", "10"))
MAX_DOCSTRING_SENTENCES = int(os.environ.get("CLAUDE_MAX_DOCSTRING_SENTENCES", "2"))
ALLOW_TODO = os.environ.get("CLAUDE_COMMENTS_ALLOW_TODO", "1") != "0"
ALLOW_MARKER = "allow-comment"

JS_SUFFIXES = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts")
PY_SUFFIXES = (".py", ".pyi")

SKIP_PATH = re.compile(
    r"(^|/)(node_modules|dist|build|vendor|\.venv|venv|__pycache__|\.next)/"
    r"|\.min\.js$"
)

TOOL_DIRECTIVE = re.compile(
    r"^\s*(?:#|//)\s*(?:"
    r"type:|noqa|pragma:|pylint:|mypy:|ruff:|fmt:|isort:|flake8:|coding[:=]|!"
    r"|@ts-|eslint|prettier|biome|c8 |istanbul|v8 |webpack|vite-|deno-|jshint|globals "
    r"|region|endregion|/ <reference"
    r")",
    re.IGNORECASE,
)
LEGAL = re.compile(r"copyright|SPDX-License|licen[cs]e", re.IGNORECASE)
TASK_MARKER = re.compile(r"^\s*(?:#|//)\s*(?:TODO|FIXME|HACK|XXX)\b")
LINE_COMMENT = re.compile(r"^\s*(?:#|//|/\*|\*\s|\*/)")

PY_DEF = re.compile(r"^\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_][\w]*)")
PY_ASSIGN = re.compile(r"^\s*([a-z_][\w]*)\s*(?::[^=]+)?=[^=]")
JS_DEF = re.compile(
    r"\b(?:function\*?|class|const|let|var|interface|type|enum)\s+([A-Za-z_$][\w$]*)"
)
JS_MEMBER = re.compile(r"^\s*(?:public|private|protected|readonly|static|async\s+)*([A-Za-z_$][\w$]*)\s*[(=:]")

WORD_SPLIT = re.compile(r"[_\-\s]+|(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
SENTENCE_END = re.compile(r"[.!?](?:\s|$)")


def word_count(name):
    return len([part for part in WORD_SPLIT.split(name) if part])


def sentence_count(text):
    body = " ".join(text.split())
    return len([piece for piece in SENTENCE_END.split(body) if piece.strip()])


# --- what the edit added -----------------------------------------------------

def added_from_patch(response):
    hunks = response.get("structuredPatch") or []
    lines = []
    for hunk in hunks:
        for line in hunk.get("lines", []):
            if line.startswith("+") and not line.startswith("+++"):
                lines.append(line[1:])
    return lines


def added_from_strings(old, new):
    diff = difflib.ndiff(old.splitlines(), new.splitlines())
    return [line[2:] for line in diff if line.startswith("+ ")]


def git_baseline(path):
    directory = os.path.dirname(os.path.abspath(path)) or "."
    try:
        result = subprocess.run(
            ["git", "-C", directory, "show", f"HEAD:./{os.path.basename(path)}"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


def added_lines(payload):
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    response = payload.get("tool_response") or {}
    path = tool_input.get("file_path")
    if not path:
        return None, []

    patched = added_from_patch(response) if isinstance(response, dict) else []
    if patched:
        return path, patched
    if tool == "Edit":
        return path, added_from_strings(tool_input.get("old_string", ""), tool_input.get("new_string", ""))
    if tool == "MultiEdit":
        lines = []
        for edit in tool_input.get("edits", []):
            lines += added_from_strings(edit.get("old_string", ""), edit.get("new_string", ""))
        return path, lines
    if tool == "Write":
        content = tool_input.get("content", "")
        baseline = git_baseline(path)
        if baseline is None:
            return path, content.splitlines()
        return path, added_from_strings(baseline, content)
    return None, []


# --- checks ------------------------------------------------------------------

def blank_strings(line):
    """Replace quoted spans with spaces so a `#` or `//` inside them is ignored."""
    out, quote, index = [], None, 0
    while index < len(line):
        char = line[index]
        if quote:
            if char == "\\":
                out.append("  ")
                index += 2
                continue
            if char == quote:
                quote = None
            out.append(" ")
        elif char in "\"'`":
            quote = char
            out.append(" ")
        else:
            out.append(char)
        index += 1
    return "".join(out)


TRAILING_COMMENT = re.compile(r"\S\s*(#|//)\s*(?P<text>.+)$")


def trailing_comment(line):
    match = TRAILING_COMMENT.search(blank_strings(line))
    if not match:
        return None
    return line[match.start(1):]


def is_explanatory(line):
    if ALLOW_MARKER in line:
        return False
    if not LINE_COMMENT.match(line):
        trailing = trailing_comment(line)
        return bool(trailing) and is_explanatory(trailing)
    if TOOL_DIRECTIVE.match(line) or LEGAL.search(line):
        return False
    if ALLOW_TODO and TASK_MARKER.match(line):
        return False
    stripped = line.strip().lstrip("#/*").strip()
    return len(stripped) > 2


def comment_findings(lines):
    return [
        {"kind": "comment", "text": (trailing_comment(line) or line).strip()}
        for line in lines
        if is_explanatory(line)
    ]


def docstring_findings(lines, path):
    opener = '"""' if path.endswith(PY_SUFFIXES) else "/**"
    closer = '"""' if path.endswith(PY_SUFFIXES) else "*/"
    blocks, current = [], None
    for line in lines:
        if current is None:
            if opener in line:
                remainder = line.split(opener, 1)[1]
                if closer in remainder:
                    blocks.append(remainder.split(closer, 1)[0])
                else:
                    current = [remainder]
            continue
        if closer in line:
            current.append(line.split(closer, 1)[0])
            blocks.append(" ".join(current))
            current = None
        else:
            current.append(line.strip().lstrip("*").strip())
    if current:
        blocks.append(" ".join(current))
    return [
        {"kind": "docstring", "text": block.strip()[:80], "sentences": sentence_count(block)}
        for block in blocks
        if sentence_count(block) > MAX_DOCSTRING_SENTENCES
    ]


def declared_names(line, path):
    if path.endswith(PY_SUFFIXES):
        for pattern in (PY_DEF, PY_ASSIGN):
            match = pattern.match(line)
            if match:
                return [match.group(1)]
        return []
    names = [match.group(1) for match in JS_DEF.finditer(line)]
    member = JS_MEMBER.match(line)
    if member:
        names.append(member.group(1))
    return names


def is_python_test(name, path):
    return path.endswith(PY_SUFFIXES) and name.startswith(("test_", "Test"))


def name_findings(lines, path):
    found = []
    for line in lines:
        for name in declared_names(line, path):
            if is_python_test(name, path):
                continue
            words = word_count(name)
            if words > MAX_NAME_WORDS:
                found.append({"kind": "name", "text": name, "words": words})
    return found


# --- reporting ---------------------------------------------------------------

def describe(finding):
    if finding["kind"] == "comment":
        return f"  comment  {finding['text'][:90]}"
    if finding["kind"] == "docstring":
        return f"  docstring ({finding['sentences']} sentences)  {finding['text']}"
    return f"  name ({finding['words']} words)  {finding['text']}"


ADVICE = {
    "comment": (
        "Rename instead of commenting. Move the comment's meaning into the",
        "variable, function or class name, or extract a function whose name is",
        "that sentence. Then delete the comment.",
    ),
    "docstring": (
        f"Keep docstrings to {MAX_DOCSTRING_SENTENCES} sentences. Cut the rest.",
    ),
    "name": (
        f"Names stop at {MAX_NAME_WORDS} words. A name that needs more is a",
        "function doing more than one thing. Split it.",
    ),
}


def report(path, findings):
    lines = [f"Comment and naming rules violated in {path}:", ""]
    lines += [describe(finding) for finding in findings]
    lines.append("")
    for kind in dict.fromkeys(finding["kind"] for finding in findings):
        lines += list(ADVICE[kind])
    lines += [
        "",
        "Use the `self-documenting-names` skill.",
        f"If a comment truly cannot become a name, append `{ALLOW_MARKER}` to it.",
    ]
    return "\n".join(lines)


def main():
    if os.environ.get("CLAUDE_SKIP_COMMENT_CHECK"):
        return 0
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    path, lines = added_lines(payload)
    if not path or SKIP_PATH.search(path):
        return 0
    if not path.endswith(PY_SUFFIXES + JS_SUFFIXES):
        return 0
    findings = comment_findings(lines) + docstring_findings(lines, path) + name_findings(lines, path)
    if not findings:
        return 0
    sys.stderr.write(report(path, findings) + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
