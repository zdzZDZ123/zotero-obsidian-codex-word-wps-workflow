# Prompt 03 — Connect Codex to Zotero and Obsidian

Copy the prompt below into Codex after Zotero and Obsidian work independently.

---

Finish the three-way Zotero–Obsidian–Codex integration on this computer. Work autonomously and verify actual runtime behavior. Read `codex/README.md`, `docs/architecture.md`, `docs/security-model.md`, the target Vault's `AGENTS.md`, and all five Vault-local Skills before making changes.

1. Detect the real Codex installation and its user configuration/skills locations. Do not reuse paths or credentials from another computer.
2. Verify that LLM for Zotero's Codex App Server is enabled, native approvals are enabled, and its MCP tools are enabled. Use **Install/update Zotero MCP config** in the Zotero plugin if needed. Confirm that Codex sees the `llm_for_zotero` server, but never display or log its bearer token.
3. Restart/reload Codex after MCP configuration changes. Exercise the available Zotero tools for library search, item metadata, full-text/page reading, and child-note write/read. Use a disposable note clearly labeled as an integration test.
4. Open the Obsidian Vault as the Codex project. Confirm direct read/write access, `AGENTS.md`, templates, dashboards, and the local Skills.
5. Install or verify `academic-research-suite` from `https://github.com/Imbad0202/academic-research-skills-codex` at the pinned tag in `docs/component-lock.json`. Use the local `run-traceable-research` skill as the Zotero/Obsidian handoff layer.
6. In Claudian, set the actual local Codex CLI path and the defaults from `codex/README.md`. Start a sidebar session and verify it is scoped to the intended Vault.
7. Perform the end-to-end test: search a real Zotero item with an available PDF, read a real passage with page/location, write a source note in Obsidian with item identity and full-text evidence status, create/read back a marked Zotero child note, and link the project note to the source note.
8. Clean up only disposable test artifacts that are unambiguously yours. Report versions, deviations, successful operations, unresolved blockers, and the exact acceptance criteria passed—without exposing private titles, note bodies, credentials, or tokens unless the owner explicitly requests them.

Do not claim success from configuration files alone. The real page read and both write/readback paths are mandatory.
