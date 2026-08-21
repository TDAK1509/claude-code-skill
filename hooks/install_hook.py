#!/usr/bin/env python3
"""Register the oversized-function hook in a Claude Code settings file.

  python3 hooks/install_hook.py [--settings PATH] [--remove]

Default settings file: ~/.claude/settings.json (applies to every project).
The merge is idempotent: an existing entry for this hook is replaced.
"""
import argparse
import json
import os
import sys

HOOK_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oversized_function.py")
MATCHER = "Edit|Write|MultiEdit"
EVENT = "PostToolUse"
MARKER = "oversized_function.py"


def load(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        text = handle.read().strip()
    return json.loads(text) if text else {}


def strip_existing(entries):
    kept = []
    for entry in entries:
        hooks = [h for h in entry.get("hooks", []) if MARKER not in str(h.get("command", ""))]
        if not hooks:
            continue
        entry["hooks"] = hooks
        kept.append(entry)
    return kept


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", default=os.path.expanduser("~/.claude/settings.json"))
    parser.add_argument("--remove", action="store_true")
    args = parser.parse_args()

    path = os.path.abspath(os.path.expanduser(args.settings))
    try:
        settings = load(path)
    except json.JSONDecodeError as err:
        sys.exit(f"{path} is not valid JSON: {err}. Fix it first; nothing was written.")

    events = settings.setdefault("hooks", {})
    entries = strip_existing(events.get(EVENT, []))

    if not args.remove:
        entries.append({
            "matcher": MATCHER,
            "hooks": [{"type": "command", "command": HOOK_SCRIPT}],
        })

    if entries:
        events[EVENT] = entries
    else:
        events.pop(EVENT, None)
    if not events:
        settings.pop("hooks", None)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        backup = path + ".bak"
        with open(backup, "w", encoding="utf-8") as handle:
            handle.write(open(path, encoding="utf-8").read())
        print(f"backup written to {backup}")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")

    verb = "removed from" if args.remove else "installed in"
    print(f"oversized-function hook {verb} {path}")


if __name__ == "__main__":
    main()
