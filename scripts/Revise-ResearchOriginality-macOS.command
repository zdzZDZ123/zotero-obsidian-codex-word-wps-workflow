#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
PYTHON="$CODEX_HOME/runtimes/originality-revision/bin/python"
HELPER="$CODEX_HOME/skills/revise-originality-with-evidence/scripts/originality_revision.py"
if [[ ! -x "$PYTHON" || ! -f "$HELPER" ]]; then
  echo "revise-originality-with-evidence is not installed. Run scripts/Install-OriginalityRevision-macOS.command first." >&2
  exit 2
fi
exec "$PYTHON" "$HELPER" "$@"
