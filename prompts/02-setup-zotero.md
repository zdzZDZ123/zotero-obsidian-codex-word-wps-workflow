# Prompt 02 — Configure Zotero on another computer

Copy the prompt below into Codex on the target computer.

---

You are deploying the Zotero evidence and citation layer of the open Zotero–Obsidian–Codex–Word/WPS research and publication workflow. Work on the actual desktop environment and validate it; do not merely write instructions.

Read `docs/component-lock.json`, `zotero/README.md`, `docs/security-model.md`, and `THIRD_PARTY_NOTICES.md` first.

Requirements:

1. Detect the OS, architecture, existing Zotero installation/profile, browser, and installed extensions. Preserve all existing libraries and preferences. Back up before any risky profile change.
2. Install Zotero and the Zotero Connector from their official sources if missing. Prefer the baseline versions where compatible; otherwise use the latest compatible official release and document the deviation.
3. Install Better BibTeX, Notero, Translate for Zotero, and LLM for Zotero from the official release sources linked by this repository. Do not use a third-party plugin pack.
4. Apply the non-secret settings in `zotero/README.md`. Never copy OAuth data, account credentials, collection/database IDs, API keys, or a bearer token from another computer.
5. Let the user authenticate to Zotero Sync through the normal Zotero interface if authentication is not already present. Do not request that a password be pasted into chat. Wait for sync to complete and report library/attachment sync status without exposing private titles if the user did not authorize them.
6. In LLM for Zotero, enable Codex App Server, model `gpt-5.6-sol`, native approvals, and MCP tools. Use its **Install/update Zotero MCP config** action so this computer generates its own bearer-protected local configuration.
7. Validate the Browser Connector with a permitted test source, stable Better BibTeX citation-key generation, plugin load status, and local MCP server availability. Do not print the bearer token.

Success means Zotero works normally, the four plugins load, Sync/Connector status is known, and the local Zotero MCP service is ready for Codex.
