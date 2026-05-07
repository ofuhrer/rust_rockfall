#!/usr/bin/env bash

select_repo_python() {
  local candidates=()
  if [[ -n "${RUST_ROCKFALL_PYTHON:-}" ]]; then
    candidates+=("${RUST_ROCKFALL_PYTHON}")
  fi
  if [[ -x ".venv/bin/python" ]]; then
    candidates+=(".venv/bin/python")
  fi
  candidates+=(
    python3.13
    python3.12
    python3.11
    python3.10
    python3.9
    python3
  )

  local candidate
  for candidate in "${candidates[@]}"; do
    if ! command -v "${candidate}" >/dev/null 2>&1; then
      continue
    fi
    if "${candidate}" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
    then
      REPO_PYTHON="$(command -v "${candidate}")"
      break
    fi
  done

  if [[ -z "${REPO_PYTHON:-}" ]]; then
    echo "Python >= 3.9 is required for repository hooks." >&2
    echo "Set RUST_ROCKFALL_PYTHON=/path/to/python if needed." >&2
    return 1
  fi

  REPO_PYTHONPATH="${PYTHONPATH:-}"
  if "${REPO_PYTHON}" - <<'PY' >/dev/null 2>&1
import yaml
PY
  then
    return 0
  fi

  echo "PyYAML is required for repository hooks." >&2
  echo "Run \`uv venv --python 3.12 .venv && uv pip install -r requirements-tools.txt\` or set RUST_ROCKFALL_PYTHON." >&2
  return 1
}
