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

hook="pre-commit"
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

pre_push_target="$hooks_target/pre-push"
repo_pre_push_target="../../scripts/git-hooks/pre-push"
if [[ -L "$pre_push_target" ]]; then
  current_target="$(readlink "$pre_push_target")"
  if [[ "$current_target" == "$repo_pre_push_target" ]]; then
    rm "$pre_push_target"
    echo "removed obsolete repository pre-push hook"
  else
    echo "leaving custom pre-push hook symlink unchanged: $current_target" >&2
  fi
elif [[ -e "$pre_push_target" ]]; then
  echo "leaving custom pre-push hook unchanged: $pre_push_target" >&2
fi

echo "Git pre-commit hook installed. Run task-specific tests before committing; no repository pre-push hook is installed."
