# Troubleshooting

## `gh` was installed but the shell cannot find it

Open a new terminal so `PATH` refreshes, or invoke the executable once by its absolute installation path. Then confirm `gh --version` and `gh auth status`.

## Obsidian lists a plugin but does not load it

`community-plugins.json` enables IDs; it does not install plugin code. Install each plugin from Obsidian's Community Plugins interface, then restart Obsidian. A compatible-latest version is acceptable only with a recorded deviation and successful runtime test.

## Claudian cannot find Codex

Run `codex --version` in the target computer's terminal. In Claudian, select the Codex provider and set the CLI path to the target computer's actual executable. Never reuse an absolute path copied from another computer.

## Zotero MCP is missing in Codex

1. Start Zotero and enable the Codex App Server in `llm-for-zotero`.
2. Use the plugin's **Install/update Zotero MCP config** action.
3. Restart Codex so it reloads MCP configuration.
4. Confirm the server exists without printing its authorization value.

The expected loopback endpoint is `http://127.0.0.1:23119/llm-for-zotero/mcp`, but the plugin-generated configuration is authoritative.

## Zotero search works but full text does not

Confirm the selected Zotero item has a locally available PDF attachment and that text extraction has completed. Metadata-only access is not page-level evidence. Record the limitation instead of inventing a page or quotation.

## macOS rejects a downloaded `.command` file

The primary workflow uses agent prompts and official installers; no replication package is required. If running the audit helper, grant execute permission only after reviewing it, then run it from Terminal. Gatekeeper warnings should be resolved through normal macOS security controls, not by disabling protection globally.

## GitHub repository creation works but `git push` is reset

Retry normal Git transport first. If `api.github.com` remains reachable while Git smart HTTP is blocked, an authenticated maintainer can run `scripts/Publish-ViaGitHubApi.ps1 -Repository owner/repository` from a clean, unpublished root commit. The fallback uploads every tracked file through GitHub's official Git Data API, canonicalizes the local root-commit serialization to match GitHub's API representation, and refuses publication unless both the tree and root-commit hashes match.
