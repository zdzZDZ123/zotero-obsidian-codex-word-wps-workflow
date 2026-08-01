#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
PYTHON="$CODEX_HOME/runtimes/publication-formatting/bin/python"
FORMATTER="$CODEX_HOME/skills/format-submission-manuscript/scripts/submission_formatter.py"
if [[ ! -x "$PYTHON" || ! -f "$FORMATTER" ]]; then
  echo "Publication formatter is not installed. Run Install-PublicationFormatting-macOS.command first." >&2
  exit 2
fi
exec "$PYTHON" "$FORMATTER" "$@"
