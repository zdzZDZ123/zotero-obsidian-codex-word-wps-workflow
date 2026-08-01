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

## `doctor` reports Word is served by WPS

This is expected when WPS registers `Word.Application`. The formatter enables Microsoft Word only when the COM server executable is `WINWORD.EXE`. Use `editor: auto` to select WPS, or install licensed Microsoft Word separately and rerun `doctor`. Never relabel the WPS registration as genuine Word.

## LibreOffice headless conversion times out

Do not retry the same global profile. The formatter stages the DOCX under an ASCII temporary path, creates a unique `UserInstallation` URI, sets a private HOME/TEMP, invokes the explicit LibreOffice executable, captures output, enforces a timeout, and removes only its own temporary directory. Check for a modal first-run process or a damaged LibreOffice installation if this isolated path still fails.

## Pandoc was installed but the current terminal cannot find it

Open a new terminal, or run the repository wrapper. The formatter also detects winget's versioned Pandoc package directory, so a stale process PATH does not invalidate `doctor`.

## A run stays `qa_pending_visual_inspection`

That is intentional. Open every PNG listed by `run-manifest.json`, inspect it at full resolution, then use `finalize --confirm-every-page`. Structural checks and successful rasterization alone cannot release a submission.
