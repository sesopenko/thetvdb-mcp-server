#!/usr/bin/env bash
set -euo pipefail

mkdir -p .cursor/rules

count=0
for src in .claude/rules/*.md; do
  filename=$(basename "$src" .md)
  dest=".cursor/rules/${filename}.mdc"
  {
    printf -- '---\ndescription: \nglobs: \nalwaysApply: true\n---\n\n'
    cat "$src"
  } > "$dest"
  echo "Written: $dest"
  ((count++))
done

echo "Done. $count rules copied to .cursor/rules/"
