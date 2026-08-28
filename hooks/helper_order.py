#!/usr/bin/env python3
"""PostToolUse hook: block when a helper is defined above the function that calls it.

Reads the Claude Code hook payload on stdin. A function that is only ever called
by functions defined below it reads backwards: you meet the detail before the
caller that gives it meaning. The fix is to move the helper under its caller.

Escape hatch: put `allow-helper-order: <reason>` inside the helper. The reason
that counts is a language that requires definition before use.
Disable entirely: export CLAUDE_SKIP_HELPER_ORDER=1
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generated import is_generated
from oversized_function import (
    JS_KEYWORDS,
    JS_SUFFIXES,
    PY_SUFFIXES,
    blank_out_noise,
    edited_paths,
    js_function_starts,
    _scan_block_end,
)

ALLOW_MARKER = "allow-helper-order"
ALLOW_WITH_REASON = re.compile(re.escape(ALLOW_MARKER) + r"\s*:\s*\S")

CALL = re.compile(r"\b([A-Za-z_$][\w$]*)\s*\(")
ANONYMOUS = ("<arrow>", "<anonymous>")


# --- the rule ---------------------------------------------------------------

def callers_of(group):
    """Map each defined name to the indexes of the siblings that call it."""
    index = {}
    for position, function in enumerate(group):
        index.setdefault(function["name"], position)
    found = {}
    for position, function in enumerate(group):
        for name in function["calls"]:
            target = index.get(name)
            if target is not None and target != position:
                found.setdefault(name, []).append(position)
    return index, found


def is_mutual(group, callee, caller):
    return group[caller]["name"] in group[callee]["calls"]


def order_violations(group, module_level, lines):
    index, callers = callers_of(group)
    found = []
    for name, positions in callers.items():
        callee, caller = index[name], min(positions)
        if callee > caller or name in module_level or name in ANONYMOUS:
            continue
        if is_mutual(group, callee, caller):
            continue
        if allowed(lines, group[callee]["start"], group[callee]["end"]):
            continue
        found.append({
            "name": name,
            "line": group[callee]["start"],
            "caller": group[caller]["name"],
            "caller_line": group[caller]["start"],
        })
    return found


def allowed(lines, start, end):
    return any(ALLOW_WITH_REASON.search(line) for line in lines[start - 1:end])


# --- Python -----------------------------------------------------------------

def called_names(node):
    names = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        target = child.func
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, ast.Attribute) and _is_self(target.value):
            names.add(target.attr)
    return names


def _is_self(node):
    return isinstance(node, ast.Name) and node.id in ("self", "cls")


def python_siblings(body):
    return [
        {"name": node.name, "start": node.lineno, "end": node.end_lineno,
         "calls": called_names(node)}
        for node in body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def python_module_level(tree):
    """Names used outside any function or class body, where order is real."""
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.update(item.id for item in _decorator_names(node))
            continue
        names.update(child.id for child in ast.walk(node) if isinstance(child, ast.Name))
    return names


def _decorator_names(node):
    for decorator in node.decorator_list:
        for child in ast.walk(decorator):
            if isinstance(child, ast.Name):
                yield child


def python_violations(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []  # mid-edit or unsupported syntax; stay quiet
    lines = source.splitlines()
    module_level = python_module_level(tree)
    groups = [tree.body] + [n.body for n in tree.body if isinstance(n, ast.ClassDef)]
    found = []
    for body in groups:
        found += order_violations(python_siblings(body), module_level, lines)
    return sorted(found, key=lambda v: v["line"])


# --- JavaScript / TypeScript ------------------------------------------------

def js_spans(code_lines):
    spans = []
    for idx, name in js_function_starts(code_lines):
        end = _scan_block_end(code_lines, idx)
        if end:
            spans.append({"name": name, "start": idx + 1, "end": end})
    return spans


def outermost(spans):
    return [
        span for span in spans
        if not any(other["start"] < span["start"] and span["end"] <= other["end"]
                   for other in spans)
    ]


def js_calls(code_lines, start, end):
    text = "\n".join(code_lines[start - 1:end])
    return {name for name in CALL.findall(text) if name not in JS_KEYWORDS}


def js_module_level(code_lines, spans):
    covered = {n for span in spans for n in range(span["start"], span["end"] + 1)}
    outside = [line for n, line in enumerate(code_lines, 1) if n not in covered]
    return set(CALL.findall("\n".join(outside)))


def js_violations(source):
    code_lines = blank_out_noise(source).splitlines()
    spans = sorted(outermost(js_spans(code_lines)), key=lambda s: s["start"])
    for span in spans:
        span["calls"] = js_calls(code_lines, span["start"], span["end"])
    module_level = js_module_level(code_lines, spans)
    return order_violations(spans, module_level, source.splitlines())


# --- hook plumbing ----------------------------------------------------------

def analyse(path):
    if is_generated(path):
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
    head = [f"Helper defined above its caller in {path}:", ""]
    for v in violations:
        head.append(
            f"  {v['name']}  line {v['line']}  is called by {v['caller']} "
            f"(line {v['caller_line']})"
        )
    head += [
        "",
        "Use the `helper-functions-ordering` skill.",
        "Move each helper directly below the function that calls it, so the file",
        "reads from the whole to the parts. The caller comes first.",
        "",
        "This rule is required. The only reason to skip it is a language that",
        "demands definition before use. Then say so on the marker:",
        f"`{ALLOW_MARKER}: C requires the prototype above the call site`.",
    ]
    return "\n".join(head)


def main():
    if os.environ.get("CLAUDE_SKIP_HELPER_ORDER"):
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
