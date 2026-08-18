#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SOURCE_SKILL="$ROOT/codex/skills/revise-originality-with-evidence"
TARGET_SKILL="$CODEX_HOME/skills/revise-originality-with-evidence"
RUNTIME="$CODEX_HOME/runtimes/originality-revision"

if [[ ! -d "$SOURCE_SKILL" ]]; then
  echo "Skill source is missing: $SOURCE_SKILL" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    brew install python
  else
    echo "Python 3 is required. Install it from python.org or Homebrew." >&2
    exit 2
  fi
fi
if [[ ! -x "$RUNTIME/bin/python" ]]; then
  python3 -m venv "$RUNTIME"
fi
"$RUNTIME/bin/python" -m pip install --disable-pip-version-check --requirement "$SOURCE_SKILL/requirements.txt"
mkdir -p "$TARGET_SKILL"
cp -R "$SOURCE_SKILL/"* "$TARGET_SKILL/"
"$RUNTIME/bin/python" "$TARGET_SKILL/scripts/originality_revision.py" doctor --self-test

echo "Installed Codex skill: $TARGET_SKILL"
echo "Processing is local-only; no commercial similarity account or API is configured."
echo "Restart Codex and verify the skill in /skills."
