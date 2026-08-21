#!/usr/bin/env bash
# Install personal Claude Code skills.
#
#   ./install.sh                      # link every skill into ~/.claude/skills (all projects)
#   ./install.sh oversized-function   # link only the named skill(s)
#   ./install.sh --project            # link into ./.claude/skills of the current directory
#   ./install.sh --project ~/code/app # link into that project's .claude/skills
#   ./install.sh --copy               # copy instead of symlink (no live updates)
#
# Symlinks are the default so editing this repo updates every install at once.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$REPO_DIR/skills"
DEST_DIR="$HOME/.claude/skills"
MODE="link"
SELECTED=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      if [[ ${2-} && ${2:0:1} != "-" ]]; then
        DEST_DIR="$(cd "$2" && pwd)/.claude/skills"; shift 2
      else
        DEST_DIR="$PWD/.claude/skills"; shift
      fi
      ;;
    --copy) MODE="copy"; shift ;;
    -h|--help) sed -n '2,12p' "${BASH_SOURCE[0]}"; exit 0 ;;
    -*) echo "unknown option: $1" >&2; exit 1 ;;
    *) SELECTED+=("$1"); shift ;;
  esac
done

if [[ ${#SELECTED[@]} -eq 0 ]]; then
  for d in "$SRC_DIR"/*/; do SELECTED+=("$(basename "$d")"); done
fi

mkdir -p "$DEST_DIR"

for name in "${SELECTED[@]}"; do
  src="$SRC_DIR/$name"
  dest="$DEST_DIR/$name"
  if [[ ! -f "$src/SKILL.md" ]]; then
    echo "skip $name: no $src/SKILL.md" >&2
    continue
  fi
  rm -rf "$dest"
  if [[ "$MODE" == "copy" ]]; then
    cp -R "$src" "$dest"
    echo "copied  $name -> $dest"
  else
    ln -s "$src" "$dest"
    echo "linked  $name -> $dest"
  fi
done

echo "Restart Claude Code, or run /doctor, to pick up new skills."
