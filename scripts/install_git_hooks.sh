#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
hooks_source="$repo_root/scripts/git-hooks"
hooks_target="$repo_root/.git/hooks"

if [[ ! -d "$hooks_source" ]]; then
  echo "hook template directory not found: $hooks_source" >&2
  exit 1
fi

mkdir -p "$hooks_target"

for hook in pre-commit pre-push; do
  source_file="$hooks_source/$hook"
  target_file="$hooks_target/$hook"

  if [[ ! -f "$source_file" ]]; then
    echo "missing hook template: $source_file" >&2
    exit 1
  fi

  if [[ -e "$target_file" && ! -L "$target_file" ]]; then
    backup_file="$target_file.backup.$(date +%Y%m%d%H%M%S)"
    mv "$target_file" "$backup_file"
    echo "backed up existing $hook to $backup_file"
  fi

  ln -sfn "../../scripts/git-hooks/$hook" "$target_file"
  chmod +x "$source_file"
  echo "installed $hook"
done

echo "Git hooks installed. Use git commit --no-verify or git push --no-verify only for explicit emergencies."
