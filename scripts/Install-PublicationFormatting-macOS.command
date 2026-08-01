#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SOURCE_SKILL="$ROOT/codex/skills/format-submission-manuscript"
TARGET_SKILL="$CODEX_HOME/skills/format-submission-manuscript"
RUNTIME="$CODEX_HOME/runtimes/publication-formatting"

if [[ ! -d "$SOURCE_SKILL" ]]; then
  echo "Skill source is missing: $SOURCE_SKILL" >&2
  exit 2
fi
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required to install missing publication tools: https://brew.sh" >&2
  exit 2
fi

command -v pandoc >/dev/null 2>&1 || brew install pandoc
[[ -x /Applications/LibreOffice.app/Contents/MacOS/soffice ]] || brew install --cask libreoffice
if [[ ! -d /Applications/wpsoffice.app && ! -d "/Applications/WPS Office.app" ]]; then
  if brew info --cask wpsoffice >/dev/null 2>&1; then
    brew install --cask wpsoffice
  elif brew info --cask wps-office >/dev/null 2>&1; then
    brew install --cask wps-office
  else
    echo "WPS cask was not found; core DOCX/PDF generation remains available."
  fi
fi
command -v python3 >/dev/null 2>&1 || brew install python

if [[ ! -x "$RUNTIME/bin/python" ]]; then
  python3 -m venv "$RUNTIME"
fi
"$RUNTIME/bin/python" -m pip install --disable-pip-version-check --requirement "$SOURCE_SKILL/requirements.txt"
mkdir -p "$TARGET_SKILL"
cp -R "$SOURCE_SKILL/"* "$TARGET_SKILL/"
"$RUNTIME/bin/python" "$TARGET_SKILL/scripts/submission_formatter.py" doctor --self-test

echo "Installed Codex skill: $TARGET_SKILL"
echo "Microsoft Word was not installed or licensed. Restart Codex and verify the skill in /skills."
