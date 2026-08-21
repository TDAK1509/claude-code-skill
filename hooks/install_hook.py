#!/usr/bin/env python3
"""Register this repository's hooks in a Claude Code settings file.

  python3 hooks/install_hook.py [--settings PATH] [--only NAME] [--remove]

Default settings file: ~/.claude/settings.json (applies to every project).
Each hook gets its own PostToolUse entry, so Claude Code runs them in
parallel. The merge is idempotent and backs the settings file up first.
"""
import argparse
import json
import os
import sys

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
EVENT = "PostToolUse"
MATCHER = "Edit|Write|MultiEdit"
REGISTRY = {
    "oversized-function": "oversized_function.py",
    "self-documenting-names": "comment_smell.py",
}


def load(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        text = handle.read().strip()
    return json.loads(text) if text else {}


def strip_ours(entries, scripts):
    kept = []
    for entry in entries:
        hooks = [
            hook for hook in entry.get("hooks", [])
            if not any(script in str(hook.get("command", "")) for script in scripts)
        ]
        if not hooks:
            continue
        entry["hooks"] = hooks
        kept.append(entry)
    return kept


def entry_for(script):
    return {
        "matcher": MATCHER,
        "hooks": [{"type": "command", "command": os.path.join(HOOKS_DIR, script)}],
    }


def write(path, settings):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        backup = path + ".bak"
        with open(path, encoding="utf-8") as source, open(backup, "w", encoding="utf-8") as target:
            target.write(source.read())
        print(f"backup written to {backup}")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", default=os.path.expanduser("~/.claude/settings.json"))
    parser.add_argument("--only", action="append", choices=sorted(REGISTRY), default=None)
    parser.add_argument("--remove", action="store_true")
    args = parser.parse_args()

    names = args.only or sorted(REGISTRY)
    scripts = [REGISTRY[name] for name in names]
    path = os.path.abspath(os.path.expanduser(args.settings))
    try:
        settings = load(path)
    except json.JSONDecodeError as error:
        sys.exit(f"{path} is not valid JSON: {error}. Fix it first; nothing was written.")

    events = settings.setdefault("hooks", {})
    entries = strip_ours(events.get(EVENT, []), scripts)
    if not args.remove:
        entries += [entry_for(script) for script in scripts]

    if entries:
        events[EVENT] = entries
    else:
        events.pop(EVENT, None)
    if not events:
        settings.pop("hooks", None)

    write(path, settings)
    verb = "removed from" if args.remove else "installed in"
    print(f"{', '.join(names)} {verb} {path}")


if __name__ == "__main__":
    main()
