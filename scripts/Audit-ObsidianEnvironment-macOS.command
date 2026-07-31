#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

VAULT_PATH="$PWD"
OUTPUT_DIRECTORY=""
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

usage() {
  cat <<'USAGE'
Usage:
  bash Audit-ObsidianEnvironment-macOS.command [--vault PATH] [--output PATH] [--codex-home PATH]

This privacy-safe audit lists application/configuration state, plugin versions
and hashes, templates, snippets, and skill names. It does not read note
contents, sessions, credentials, API keys, MCP tokens, or workspace state.
USAGE
}

die() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --vault)
      [[ $# -ge 2 ]] || die "--vault requires a path."
      VAULT_PATH="$2"
      shift 2
      ;;
    --output)
      [[ $# -ge 2 ]] || die "--output requires a path."
      OUTPUT_DIRECTORY="$2"
      shift 2
      ;;
    --codex-home)
      [[ $# -ge 2 ]] || die "--codex-home requires a path."
      CODEX_HOME="$2"
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
done

case "$VAULT_PATH" in
  \~) VAULT_PATH="$HOME" ;;
  \~/*) VAULT_PATH="$HOME/${VAULT_PATH#\~/}" ;;
esac
[[ -d "$VAULT_PATH/.obsidian" ]] || die "No .obsidian directory found at: $VAULT_PATH"
VAULT_PATH="$(cd "$VAULT_PATH" && pwd -P)"

if [[ -z "$OUTPUT_DIRECTORY" ]]; then
  OUTPUT_DIRECTORY="$VAULT_PATH/90-System/Audits"
fi
mkdir -p "$OUTPUT_DIRECTORY"
OUTPUT_DIRECTORY="$(cd "$OUTPUT_DIRECTORY" && pwd -P)"

STAMP="$(date '+%Y%m%d-%H%M%S')"
REPORT="$OUTPUT_DIRECTORY/obsidian-environment-macos-$STAMP.md"

count_json_strings() {
  local file="$1"
  if [[ -f "$file" ]]; then
    /usr/bin/grep -o '"[^"]*"' "$file" | /usr/bin/wc -l | /usr/bin/tr -d ' '
  else
    printf '0\n'
  fi
}

json_value() {
  local file="$1" key="$2"
  /usr/bin/plutil -extract "$key" raw "$file" 2>/dev/null || printf 'unknown\n'
}

obsidian_version="not detected"
for app in "/Applications/Obsidian.app" "$HOME/Applications/Obsidian.app"; do
  if [[ -f "$app/Contents/Info.plist" ]]; then
    obsidian_version="$(/usr/bin/plutil -extract CFBundleShortVersionString raw "$app/Contents/Info.plist" 2>/dev/null || printf 'unknown')"
    break
  fi
done

community_count="$(count_json_strings "$VAULT_PATH/.obsidian/community-plugins.json")"
core_enabled="$(count_json_strings "$VAULT_PATH/.obsidian/core-plugins.json")"
core_disabled="$(count_json_strings "$VAULT_PATH/.obsidian/core-plugins-migration.json")"
template_count="$(find "$VAULT_PATH/99-Templates" -maxdepth 1 -type f -name '*.md' 2>/dev/null | /usr/bin/wc -l | /usr/bin/tr -d ' ')"
skill_count="$(find "$VAULT_PATH/.agents/skills" -mindepth 2 -maxdepth 2 -type f -name 'SKILL.md' 2>/dev/null | /usr/bin/wc -l | /usr/bin/tr -d ' ')"
ars_version="not installed"
if [[ -f "$CODEX_HOME/skills/academic-research-suite/manifest.json" ]]; then
  ars_version="$(json_value "$CODEX_HOME/skills/academic-research-suite/manifest.json" adapter_version)"
fi

git_state="not a Git repository"
if command -v git >/dev/null 2>&1 && [[ -d "$VAULT_PATH/.git" ]]; then
  branch="$(git -C "$VAULT_PATH" branch --show-current 2>/dev/null || true)"
  git_state="local repository on ${branch:-unknown branch}"
fi

cat > "$REPORT" <<REPORT_HEADER
# Obsidian Environment Audit for macOS

- Generated: $(date -u '+%Y-%m-%dT%H:%M:%SZ')
- Vault: \`$VAULT_PATH\`
- Obsidian: $obsidian_version
- Community plugins enabled: $community_count
- Core plugins enabled: $core_enabled
- Core plugins disabled: $core_disabled
- Templates: $template_count
- Vault-local Codex skills: $skill_count
- Academic Research Suite: $ars_version
- Git: $git_state

## Community plugins

| ID | Name | Version | main.js SHA-256 |
|---|---|---:|---|
REPORT_HEADER

if [[ -d "$VAULT_PATH/.obsidian/plugins" ]]; then
  for plugin_dir in "$VAULT_PATH/.obsidian/plugins"/*; do
    [[ -d "$plugin_dir" && -f "$plugin_dir/manifest.json" ]] || continue
    plugin_id="$(json_value "$plugin_dir/manifest.json" id)"
    plugin_name="$(json_value "$plugin_dir/manifest.json" name)"
    plugin_version="$(json_value "$plugin_dir/manifest.json" version)"
    plugin_hash="missing"
    if [[ -f "$plugin_dir/main.js" ]]; then
      plugin_hash="$(/usr/bin/shasum -a 256 "$plugin_dir/main.js" | /usr/bin/awk '{print $1}')"
    fi
    printf '| %s | %s | %s | `%s` |\n' \
      "$plugin_id" "$plugin_name" "$plugin_version" "$plugin_hash" >> "$REPORT"
  done
fi

cat >> "$REPORT" <<'REPORT_SKILLS'

## Vault-local skills

REPORT_SKILLS

if [[ -d "$VAULT_PATH/.agents/skills" ]]; then
  for skill_dir in "$VAULT_PATH/.agents/skills"/*; do
    [[ -f "$skill_dir/SKILL.md" ]] || continue
    printf -- '- `%s`\n' "$(basename "$skill_dir")" >> "$REPORT"
  done
fi

cat >> "$REPORT" <<'REPORT_PRIVACY'

## Privacy boundary

This audit does not read or output note contents, Claudian sessions, API/MCP
tokens, Git credentials, device IDs, full remote URLs, or workspace layout.
REPORT_PRIVACY

printf 'REPORT=%s\n' "$REPORT"
